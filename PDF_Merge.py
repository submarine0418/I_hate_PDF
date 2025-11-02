"""
PDF 合併小工具 - GUI 版本（兩檔案合併版）
使用說明：
1. 選擇「檔案 1」（第一個要合併的 PDF）
2. 選擇「檔案 2」（第二個要合併的 PDF，這個檔名會被保留）
3. 點選「開始合併」
4. 合併後的檔案會存在「檔案 2」的同一資料夾，檔名格式：原檔名_merged.pdf
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import PyPDF2
from threading import Thread


class PDFMergerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF 合併小工具")
        self.root.geometry("700x500")
        self.root.resizable(False, False)
        
        # 設定變數
        self.file1_path = tk.StringVar()
        self.file2_path = tk.StringVar()
        
        self.create_widgets()
    
    def create_widgets(self):
        # 標題
        title_frame = tk.Frame(self.root, bg="#4CAF50", height=60)
        title_frame.pack(fill="x")
        title_label = tk.Label(
            title_frame, 
            text="📄 PDF 合併小工具", 
            font=("微軟正黑體", 18, "bold"),
            bg="#4CAF50",
            fg="white"
        )
        title_label.pack(pady=15)
        
        # 主要內容區
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        # 說明文字
        instruction_frame = tk.LabelFrame(main_frame, text="📌 使用說明", font=("微軟正黑體", 10, "bold"), padx=10, pady=10)
        instruction_frame.pack(fill="x", pady=(0, 15))
        
        instructions = [
            "1. 選擇「檔案 1」（第一個要合併的 PDF 檔案）",
            "2. 選擇「檔案 2」（第二個要合併的 PDF 檔案）",
            "3. 點選「開始合併」按鈕",
            "4. 合併後的檔案會存在「檔案 2」的同一資料夾",
            "   檔名格式：原檔名_merged.pdf（例：王大頭_merged.pdf）",

        ]
        
        for instruction in instructions:
            label = tk.Label(
                instruction_frame, 
                text=instruction, 
                font=("微軟正黑體", 9),
                anchor="w",
                fg="red" if "提醒" in instruction else "black"
            )
            label.pack(anchor="w")
        
        # 檔案選擇區
        file_frame = tk.LabelFrame(main_frame, text="📁 檔案設定", font=("微軟正黑體", 10, "bold"), padx=10, pady=10)
        file_frame.pack(fill="x", pady=(0, 15))
        
        # 檔案 1
        self.create_file_row(
            file_frame, 
            "檔案 1：", 
            self.file1_path, 
            0
        )
        
        # 檔案 2
        self.create_file_row(
            file_frame, 
            "檔案 2（保留此檔名）：", 
            self.file2_path, 
            1
        )
        
        # 進度條
        self.progress_frame = tk.Frame(main_frame)
        self.progress_frame.pack(fill="x", pady=(0, 10))
        
        self.progress_label = tk.Label(
            self.progress_frame, 
            text="", 
            font=("微軟正黑體", 9),
            fg="blue"
        )
        self.progress_label.pack()
        
        self.progress = ttk.Progressbar(
            self.progress_frame, 
            mode='indeterminate',
            length=400
        )
        
        # 按鈕區
        button_frame = tk.Frame(main_frame)
        button_frame.pack(pady=10)
        
        self.merge_button = tk.Button(
            button_frame,
            text="🚀 開始合併",
            font=("微軟正黑體", 12, "bold"),
            bg="#4CAF50",
            fg="white",
            width=15,
            height=5,
            command=self.start_merge,
            cursor="hand2"
        )
        self.merge_button.pack(side="left", padx=5)
        
        clear_button = tk.Button(
            button_frame,
            text="🔄 清除",
            font=("微軟正黑體", 12),
            bg="#ff9800",
            fg="white",
            width=10,
            height=5,
            command=self.clear_fields,
            cursor="hand2"
        )
        clear_button.pack(side="left", padx=5)
        
        # 訊息顯示區
        message_frame = tk.LabelFrame(main_frame, text="📋 執行訊息", font=("微軟正黑體", 10, "bold"))
        message_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        self.message_text = tk.Text(
            message_frame, 
            height=8, 
            font=("Consolas", 9),
            wrap="word",
            bg="#f5f5f5"
        )
        self.message_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        scrollbar = tk.Scrollbar(self.message_text)
        scrollbar.pack(side="right", fill="y")
        self.message_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.message_text.yview)
    
    def create_file_row(self, parent, label_text, string_var, row):
        """創建檔案選擇行"""
        label = tk.Label(
            parent, 
            text=label_text, 
            font=("微軟正黑體", 10),
            width=20,
            anchor="w"
        )
        label.grid(row=row, column=0, sticky="w", pady=8)
        
        entry = tk.Entry(
            parent, 
            textvariable=string_var, 
            font=("微軟正黑體", 9),
            width=40
        )
        entry.grid(row=row, column=1, padx=5, pady=8)
        
        button = tk.Button(
            parent,
            text="瀏覽...",
            font=("微軟正黑體", 9),
            command=lambda: self.browse_file(string_var),
            cursor="hand2",
            width=8
        )
        button.grid(row=row, column=2, pady=8)
    
    def browse_file(self, string_var):
        """開啟檔案選擇對話框"""
        file = filedialog.askopenfilename(
            title="選擇 PDF 檔案",
            filetypes=[("PDF 檔案", "*.pdf"), ("所有檔案", "*.*")]
        )
        if file:
            string_var.set(file)
    
    def clear_fields(self):
        """清除所有輸入欄位"""
        self.file1_path.set("")
        self.file2_path.set("")
        self.message_text.delete(1.0, tk.END)
        self.progress_label.config(text="")
    
    def log_message(self, message):
        """在訊息區顯示訊息"""
        self.message_text.insert(tk.END, message + "\n")
        self.message_text.see(tk.END)
        self.root.update()
    
    def merge_two_pdfs(self, file1, file2):
        """合併兩個 PDF 檔案，輸出到 file2 的位置"""
        try:
            merger = PyPDF2.PdfMerger()
            
            # 依序加入兩個 PDF
            self.log_message(f"正在讀取檔案 1：{os.path.basename(file1)}")
            merger.append(file1)
            
            self.log_message(f"正在讀取檔案 2：{os.path.basename(file2)}")
            merger.append(file2)
            
            # 輸出到 file2 的位置（取代原檔案）
            self.log_message(f"正在寫入合併後的檔案...")
            file2_dir = os.path.dirname(file2)
            file2_name = os.path.basename(file2)
            file2_name_without_ext = os.path.splitext(file2_name)[0]
            output_filename = f"{file2_name_without_ext}_merged.pdf"
            output_path = os.path.join(file2_dir, output_filename)
            merger.write(output_path)
            merger.close()
            
            self.log_message(f"✓ 合併成功！")
            self.log_message(f"📁 檔案位置：{output_path}\n")
            return True
            
        except Exception as e:
            self.log_message(f"✗ 合併失敗：{str(e)}")
            return False
    
    def start_merge(self):
        """開始合併處理"""
        # 檢查檔案是否都已選擇
        if not self.file1_path.get():
            messagebox.showwarning("警告", "請選擇「檔案 1」！")
            return
        
        if not self.file2_path.get():
            messagebox.showwarning("警告", "請選擇「檔案 2」！")
            return
        
        # 檢查檔案是否存在
        if not os.path.exists(self.file1_path.get()):
            messagebox.showerror("錯誤", "「檔案 1」不存在！")
            return
        
        if not os.path.exists(self.file2_path.get()):
            messagebox.showerror("錯誤", "「檔案 2」不存在！")
            return
        
        # 檢查是否為 PDF 檔案
        if not self.file1_path.get().lower().endswith('.pdf'):
            messagebox.showerror("錯誤", "「檔案 1」不是 PDF 檔案！")
            return
        
        if not self.file2_path.get().lower().endswith('.pdf'):
            messagebox.showerror("錯誤", "「檔案 2」不是 PDF 檔案！")
            return
        
        # 確認是否要取代檔案
        result = messagebox.askyesno(
            "確認",
            "合併後的檔案會儲存在「檔案 2」的同一資料夾，\n"
            "檔名格式為：原檔名_merged.pdf\n\n",
            icon='warning'
        )
        
        if not result:
            return
        
        # 在新執行緒中執行合併（避免凍結 GUI）
        thread = Thread(target=self.merge_process)
        thread.daemon = True
        thread.start()
    
    def merge_process(self):
        """合併處理流程"""
        try:
            # 禁用合併按鈕
            self.merge_button.config(state="disabled")
            
            # 清空訊息區
            self.message_text.delete(1.0, tk.END)
            
            # 顯示進度條
            self.progress_label.config(text="正在處理中，請稍候...")
            self.progress.pack(pady=5)
            self.progress.start(10)
            
            self.log_message("=" * 50)
            self.log_message("開始執行 PDF 合併作業")
            self.log_message("=" * 50 + "\n")
            
            # 合併 PDF
            success = self.merge_two_pdfs(
                self.file1_path.get(), 
                self.file2_path.get()
            )
            
            # 顯示結果
            self.log_message("=" * 50)
            if success:
                self.log_message("合併完成！")
                self.log_message("=" * 50)
                                
                # 顯示完成對話框
                messagebox.showinfo(
                    "完成", 
                    f"PDF 合併完成！\n\n檔案已儲存至：\n{self.file2_path.get()}\n\n"
                )
            else:
                self.log_message("合併失敗！")
                self.log_message("=" * 50)
                messagebox.showerror("失敗", "PDF 合併失敗，請檢查檔案是否正常。")
            
        except Exception as e:
            self.log_message(f"\n✗ 發生錯誤：{str(e)}")
            messagebox.showerror("錯誤", f"合併過程發生錯誤：\n{str(e)}")
        
        finally:
            # 停止進度條並重新啟用按鈕
            self.progress.stop()
            self.progress.pack_forget()
            self.progress_label.config(text="")
            self.merge_button.config(state="normal")


def main():
    root = tk.Tk()
    app = PDFMergerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()