"""
PDF 合併工具 - 現代化 GUI 版本
功能：
- 多檔案合併（不限數量）
- 頁面預覽＋點選選擇要合併的頁面
- 排序檔案順序
- 深色主題介面
"""

import os
import io
import customtkinter as ctk
from tkinter import filedialog, messagebox, Canvas
from PIL import Image, ImageTk
import fitz  # PyMuPDF
from PyPDF2 import PdfReader, PdfWriter
from threading import Thread

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── 顏色常數 ──────────────────────────────────────────────
ACCENT = "#3B82F6"
ACCENT_HOVER = "#2563EB"
DANGER = "#EF4444"
DANGER_HOVER = "#DC2626"
SUCCESS = "#22C55E"
SURFACE = "#1E293B"
CARD = "#334155"
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"
SELECTED_BORDER = "#3B82F6"
UNSELECTED_BG = "#1E293B"

# 縮圖尺寸
THUMB_W = 120
THUMB_H = 160


def render_page_thumbnail(pdf_path, page_idx, width=THUMB_W, height=THUMB_H):
    """用 PyMuPDF 渲染單頁為 PIL Image 縮圖"""
    doc = fitz.open(pdf_path)
    page = doc[page_idx]
    # 計算縮放比例讓頁面適合 width x height
    rect = page.rect
    zoom = min(width / rect.width, height / rect.height)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.open(io.BytesIO(pix.tobytes("png")))
    doc.close()
    return img


class PagePreviewWindow(ctk.CTkToplevel):
    """頁面預覽視窗 — 顯示縮圖格狀版面，點擊切換選取"""

    def __init__(self, master, filepath, selected_pages, on_confirm):
        super().__init__(master)
        self.title(f"頁面預覽 — {os.path.basename(filepath)}")
        self.geometry("860x640")
        self.minsize(640, 480)
        self.filepath = filepath
        self.on_confirm = on_confirm
        self.grab_set()

        doc = fitz.open(filepath)
        self.total_pages = len(doc)
        doc.close()

        # 已選頁面 set（0-based）
        if selected_pages is None:
            self.selected = set(range(self.total_pages))
        else:
            self.selected = set(selected_pages)

        self.thumb_images = []  # keep references
        self.thumb_labels = []

        self._build_ui()
        self._load_thumbnails()

    def _build_ui(self):
        # 頂部工具列
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(12, 6))

        ctk.CTkLabel(
            top, text=f"共 {self.total_pages} 頁  —  點擊縮圖切換選取",
            font=ctk.CTkFont(size=16), text_color=TEXT_SECONDARY
        ).pack(side="left")

        ctk.CTkButton(
            top, text="全選", width=80, height=34,
            font=ctk.CTkFont(size=14),
            fg_color="#475569", hover_color="#64748B",
            command=self._select_all
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            top, text="取消全選", width=100, height=34,
            font=ctk.CTkFont(size=14),
            fg_color="#475569", hover_color="#64748B",
            command=self._deselect_all
        ).pack(side="right", padx=(6, 0))

        ctk.CTkButton(
            top, text="反選", width=80, height=34,
            font=ctk.CTkFont(size=14),
            fg_color="#475569", hover_color="#64748B",
            command=self._invert_selection
        ).pack(side="right")

        # 可捲動的縮圖區
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#0F172A")
        self.scroll.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        # 底部確認
        bot = ctk.CTkFrame(self, fg_color="transparent")
        bot.pack(fill="x", padx=16, pady=(0, 12))

        self.info_label = ctk.CTkLabel(
            bot, text="", font=ctk.CTkFont(size=15), text_color=TEXT_SECONDARY
        )
        self.info_label.pack(side="left")

        ctk.CTkButton(
            bot, text="確認選取", width=140, height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=SUCCESS, hover_color="#16A34A",
            command=self._confirm
        ).pack(side="right")

        self._update_info()

    def _load_thumbnails(self):
        """載入所有頁面縮圖"""
        # 計算每行可放幾張
        cols = max(1, 860 // (THUMB_W + 24))
        for idx in range(self.total_pages):
            row, col = divmod(idx, cols)
            frame = ctk.CTkFrame(
                self.scroll, width=THUMB_W + 16, height=THUMB_H + 44,
                corner_radius=8, fg_color=CARD, border_width=3,
                border_color=SELECTED_BORDER if idx in self.selected else CARD
            )
            frame.grid(row=row, column=col, padx=8, pady=8)
            frame.grid_propagate(False)

            try:
                img = render_page_thumbnail(self.filepath, idx)
                photo = ImageTk.PhotoImage(img)
                self.thumb_images.append(photo)
            except Exception:
                photo = None
                self.thumb_images.append(None)

            canvas = Canvas(
                frame, width=THUMB_W, height=THUMB_H,
                bg="#0F172A", highlightthickness=0, cursor="hand2"
            )
            canvas.pack(padx=8, pady=(6, 2))
            if photo:
                canvas.create_image(THUMB_W // 2, THUMB_H // 2, image=photo, anchor="center")

            lbl = ctk.CTkLabel(
                frame, text=f"第 {idx + 1} 頁",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=TEXT_PRIMARY
            )
            lbl.pack(pady=(0, 4))

            # 點擊事件
            canvas.bind("<Button-1>", lambda e, i=idx, f=frame: self._toggle(i, f))
            lbl.bind("<Button-1>", lambda e, i=idx, f=frame: self._toggle(i, f))

            self.thumb_labels.append(frame)

    def _toggle(self, idx, frame):
        if idx in self.selected:
            self.selected.discard(idx)
            frame.configure(border_color=CARD)
        else:
            self.selected.add(idx)
            frame.configure(border_color=SELECTED_BORDER)
        self._update_info()

    def _select_all(self):
        self.selected = set(range(self.total_pages))
        for i, f in enumerate(self.thumb_labels):
            f.configure(border_color=SELECTED_BORDER)
        self._update_info()

    def _deselect_all(self):
        self.selected.clear()
        for f in self.thumb_labels:
            f.configure(border_color=CARD)
        self._update_info()

    def _invert_selection(self):
        self.selected = set(range(self.total_pages)) - self.selected
        for i, f in enumerate(self.thumb_labels):
            f.configure(border_color=SELECTED_BORDER if i in self.selected else CARD)
        self._update_info()

    def _update_info(self):
        n = len(self.selected)
        self.info_label.configure(text=f"已選 {n} / {self.total_pages} 頁")

    def _confirm(self):
        if not self.selected:
            messagebox.showwarning("提示", "請至少選擇一頁。", parent=self)
            return
        self.on_confirm(sorted(self.selected))
        self.destroy()


class FileCard(ctk.CTkFrame):
    """單一 PDF 檔案的卡片元件"""

    def __init__(self, master, filepath, index, on_remove, on_move_up, on_move_down, app_ref, **kw):
        super().__init__(master, corner_radius=10, fg_color=CARD, **kw)
        self.filepath = filepath
        self.index = index
        self.app_ref = app_ref

        try:
            reader = PdfReader(filepath)
            self.total_pages = len(reader.pages)
        except Exception:
            self.total_pages = 0

        # 預設全選
        self.selected_pages = list(range(self.total_pages))

        # ── 第一列：序號 + 檔名 + 按鈕 ──
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=14, pady=(12, 4))

        ctk.CTkLabel(
            top, text=f"#{index + 1}", width=36,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=ACCENT
        ).pack(side="left")

        name = os.path.basename(filepath)
        ctk.CTkLabel(
            top, text=name,
            font=ctk.CTkFont(size=15),
            text_color=TEXT_PRIMARY, anchor="w"
        ).pack(side="left", padx=(8, 0), fill="x", expand=True)

        self.page_info = ctk.CTkLabel(
            top, text=f"{self.total_pages}/{self.total_pages} 頁",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_SECONDARY
        )
        self.page_info.pack(side="left", padx=(8, 6))

        btn_size = 34
        ctk.CTkButton(
            top, text="預覽", width=70, height=btn_size,
            font=ctk.CTkFont(size=14), fg_color=ACCENT,
            hover_color=ACCENT_HOVER, command=self._open_preview
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            top, text="▲", width=btn_size, height=btn_size,
            font=ctk.CTkFont(size=14), fg_color="transparent",
            hover_color="#475569", command=lambda: on_move_up(self.index)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            top, text="▼", width=btn_size, height=btn_size,
            font=ctk.CTkFont(size=14), fg_color="transparent",
            hover_color="#475569", command=lambda: on_move_down(self.index)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            top, text="✕", width=btn_size, height=btn_size,
            font=ctk.CTkFont(size=14), fg_color=DANGER,
            hover_color=DANGER_HOVER, command=lambda: on_remove(self.index)
        ).pack(side="left", padx=(2, 0))

    def _open_preview(self):
        PagePreviewWindow(
            self.app_ref, self.filepath,
            self.selected_pages, self._on_pages_confirmed
        )

    def _on_pages_confirmed(self, pages):
        self.selected_pages = pages
        self.page_info.configure(text=f"{len(pages)}/{self.total_pages} 頁")

    def get_selected_pages(self):
        return self.selected_pages


class PDFMergerApp(ctk.CTk):
    """主視窗"""

    def __init__(self):
        super().__init__()
        self.title("PDF Merge Tool")
        self.geometry("800x720")
        self.minsize(680, 520)

        self.files: list[str] = []
        self.cards: list[FileCard] = []

        self._build_ui()

    # ── UI 建構 ─────────────────────────────────────────
    def _build_ui(self):
        # 標題列
        header = ctk.CTkFrame(self, fg_color=ACCENT, corner_radius=0, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header, text="  PDF Merge Tool",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=20)

        # 工具列
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(14, 6))

        ctk.CTkButton(
            toolbar, text="＋ 新增檔案",
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=ACCENT, hover_color=ACCENT_HOVER, height=42,
            command=self._add_files
        ).pack(side="left")

        ctk.CTkButton(
            toolbar, text="清空全部",
            font=ctk.CTkFont(size=15),
            fg_color="transparent", hover_color="#475569",
            border_width=1, border_color="#475569", height=42,
            command=self._clear_all
        ).pack(side="left", padx=(10, 0))

        self.file_count_label = ctk.CTkLabel(
            toolbar, text="0 個檔案",
            font=ctk.CTkFont(size=15), text_color=TEXT_SECONDARY
        )
        self.file_count_label.pack(side="right")

        # 檔案列表
        self.scroll_frame = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(6, 10))

        self.empty_label = ctk.CTkLabel(
            self.scroll_frame,
            text="點擊「＋ 新增檔案」加入 PDF\n可多選，再按「預覽」選取要合併的頁面",
            font=ctk.CTkFont(size=17), text_color=TEXT_SECONDARY,
            justify="center"
        )
        self.empty_label.pack(pady=100)

        # 底部
        bottom = ctk.CTkFrame(self, fg_color=SURFACE, corner_radius=0)
        bottom.pack(fill="x", side="bottom")

        row1 = ctk.CTkFrame(bottom, fg_color="transparent")
        row1.pack(fill="x", padx=20, pady=(14, 6))

        ctk.CTkLabel(
            row1, text="輸出資料夾：",
            font=ctk.CTkFont(size=15), text_color=TEXT_SECONDARY
        ).pack(side="left")

        self.output_entry = ctk.CTkEntry(
            row1, placeholder_text="選擇輸出資料夾...",
            font=ctk.CTkFont(size=14), height=36
        )
        self.output_entry.pack(side="left", fill="x", expand=True, padx=(6, 10))

        ctk.CTkButton(
            row1, text="瀏覽", width=80, height=36,
            font=ctk.CTkFont(size=14),
            fg_color="#475569", hover_color="#64748B",
            command=self._browse_output
        ).pack(side="left")

        row2 = ctk.CTkFrame(bottom, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(0, 8))

        self.progress = ctk.CTkProgressBar(row2, height=8, progress_color=ACCENT)
        self.progress.pack(fill="x", pady=(0, 6))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(
            row2, text="就緒",
            font=ctk.CTkFont(size=15), text_color=TEXT_SECONDARY
        )
        self.status_label.pack(side="left")

        self.merge_btn = ctk.CTkButton(
            row2, text="開始合併", width=160, height=46,
            font=ctk.CTkFont(size=18, weight="bold"),
            fg_color=SUCCESS, hover_color="#16A34A",
            command=self._start_merge
        )
        self.merge_btn.pack(side="right")

    # ── 新增檔案 ─────────────────────────────────────────
    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="選擇 PDF 檔案（可多選）",
            filetypes=[("PDF 檔案", "*.pdf")]
        )
        if not paths:
            return
        for p in paths:
            if p not in self.files:
                self.files.append(p)
        self._refresh_cards()

    # ── 清空 ─────────────────────────────────────────────
    def _clear_all(self):
        self.files.clear()
        self._refresh_cards()
        self.output_entry.delete(0, "end")

    # ── 移除單一檔案 ─────────────────────────────────────
    def _remove_file(self, idx):
        if 0 <= idx < len(self.files):
            self.files.pop(idx)
            self._refresh_cards()

    # ── 上移 / 下移 ──────────────────────────────────────
    def _move_up(self, idx):
        if idx > 0:
            sel = self._collect_selections()
            self.files[idx], self.files[idx - 1] = self.files[idx - 1], self.files[idx]
            sel[idx], sel[idx - 1] = sel[idx - 1], sel[idx]
            self._refresh_cards(sel)

    def _move_down(self, idx):
        if idx < len(self.files) - 1:
            sel = self._collect_selections()
            self.files[idx], self.files[idx + 1] = self.files[idx + 1], self.files[idx]
            sel[idx], sel[idx + 1] = sel[idx + 1], sel[idx]
            self._refresh_cards(sel)

    def _collect_selections(self):
        return [c.get_selected_pages() for c in self.cards]

    # ── 重建卡片 ─────────────────────────────────────────
    def _refresh_cards(self, selections=None):
        for c in self.cards:
            c.destroy()
        self.cards.clear()

        if not self.files:
            self.empty_label.pack(pady=100)
        else:
            self.empty_label.pack_forget()
            for i, fp in enumerate(self.files):
                card = FileCard(
                    self.scroll_frame, fp, i,
                    on_remove=self._remove_file,
                    on_move_up=self._move_up,
                    on_move_down=self._move_down,
                    app_ref=self
                )
                card.pack(fill="x", pady=4)
                if selections and i < len(selections):
                    card.selected_pages = selections[i]
                    card.page_info.configure(
                        text=f"{len(selections[i])}/{card.total_pages} 頁"
                    )
                self.cards.append(card)

        self.file_count_label.configure(text=f"{len(self.files)} 個檔案")

    # ── 輸出路徑（選資料夾）───────────────────────────────
    def _browse_output(self):
        folder = filedialog.askdirectory(title="選擇輸出資料夾")
        if folder:
            self.output_entry.delete(0, "end")
            self.output_entry.insert(0, folder)

    # ── 檔名輸入彈窗 ─────────────────────────────────────
    def _ask_filename(self, default_name):
        """彈出自訂視窗讓使用者輸入/修改檔名，預填 default_name"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("輸出檔名")
        dialog.geometry("460x180")
        dialog.resizable(False, False)
        dialog.grab_set()

        result = [None]

        ctk.CTkLabel(
            dialog, text="請輸入合併後的檔案名稱：",
            font=ctk.CTkFont(size=15)
        ).pack(padx=20, pady=(20, 8))

        entry = ctk.CTkEntry(
            dialog, font=ctk.CTkFont(size=14), height=36, width=400
        )
        entry.pack(padx=20)
        entry.insert(0, default_name)
        entry.select_range(0, len(default_name) - 4)  # 選取檔名部分，不含 .pdf
        entry.focus()

        def on_ok(event=None):
            result[0] = entry.get()
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        entry.bind("<Return>", on_ok)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=(14, 10))

        ctk.CTkButton(
            btn_frame, text="確認", width=100, height=36,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=SUCCESS, hover_color="#16A34A",
            command=on_ok
        ).pack(side="left", padx=6)

        ctk.CTkButton(
            btn_frame, text="取消", width=100, height=36,
            font=ctk.CTkFont(size=15),
            fg_color="#475569", hover_color="#64748B",
            command=on_cancel
        ).pack(side="left", padx=6)

        dialog.wait_window()
        return result[0]

    # ── 合併流程 ─────────────────────────────────────────
    def _start_merge(self):
        if len(self.files) < 2:
            messagebox.showwarning("提示", "請至少新增 2 個 PDF 檔案。")
            return

        output_dir = self.output_entry.get().strip()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showwarning("提示", "請選擇有效的輸出資料夾。")
            return

        for fp in self.files:
            if not os.path.exists(fp):
                messagebox.showerror("錯誤", f"檔案不存在：\n{fp}")
                return

        # 預設檔名 = 第二個檔案名_merge.pdf
        second_name = os.path.splitext(os.path.basename(self.files[1]))[0]
        default_name = f"{second_name}_merge.pdf"

        # 彈出命名視窗
        filename = self._ask_filename(default_name)
        if not filename or not filename.strip():
            return

        filename = filename.strip()
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        output_path = os.path.join(output_dir, filename)

        if os.path.exists(output_path):
            overwrite = messagebox.askyesno(
                "檔案已存在",
                f"「{filename}」已存在，是否覆蓋？"
            )
            if not overwrite:
                return

        self.merge_btn.configure(state="disabled")
        self.status_label.configure(text="合併中…", text_color=ACCENT)
        self.progress.set(0)

        Thread(target=self._do_merge, args=(output_path,), daemon=True).start()

    def _do_merge(self, output_path):
        try:
            writer = PdfWriter()
            total = len(self.files)

            for i, fp in enumerate(self.files):
                reader = PdfReader(fp)
                pages = self.cards[i].get_selected_pages()

                for p in pages:
                    writer.add_page(reader.pages[p])

                self.progress.set((i + 1) / total)
                self.status_label.configure(
                    text=f"處理中 ({i + 1}/{total})：{os.path.basename(fp)}"
                )

            with open(output_path, "wb") as f:
                writer.write(f)

            self.progress.set(1)
            self.status_label.configure(text="合併完成！", text_color=SUCCESS)
            messagebox.showinfo("完成", f"PDF 合併完成！\n\n儲存於：\n{output_path}")

        except Exception as e:
            self.status_label.configure(text="合併失敗", text_color=DANGER)
            messagebox.showerror("錯誤", f"合併過程發生錯誤：\n{e}")
        finally:
            self.merge_btn.configure(state="normal")


def main():
    app = PDFMergerApp()
    app.mainloop()


if __name__ == "__main__":
    main()