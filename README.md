# PDF Merge Tool

A modern desktop application for merging multiple PDF files with per-file page selection.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## Features

- **Multiple file merge** — add unlimited PDF files, not just two
- **Page selection** — choose specific pages per file (e.g. `1-3, 5, 8-10`)
- **Reorder files** — move files up/down to control merge order
- **Modern UI** — dark/light theme with clean card-based layout (customtkinter)
- **Progress indicator** — real-time progress bar during merge
- **Custom output path** — choose where to save the merged PDF

## Screenshot

> _Run the app to see the modern dark-themed interface._

## Download

Pre-built executable available in the `dist/` folder:
- Windows: `PDFMergeTool.exe`

## Usage

1. Click **＋ 新增檔案** to add PDF files (multi-select supported)
2. _(Optional)_ Enter page ranges for each file, e.g. `1-3, 5, 8-10`. Leave blank for all pages.
3. Use **▲ ▼** buttons to reorder files
4. Click **瀏覽** to choose an output file location
5. Click **開始合併**

### Page Range Syntax

| Input | Meaning |
|-------|---------|
| _(empty)_ | All pages |
| `1-5` | Pages 1 through 5 |
| `3, 7, 10` | Pages 3, 7, and 10 |
| `1-3, 5, 8-10` | Pages 1–3, 5, and 8–10 |

## Installation

### From Source

```bash
pip install -r requirements.txt
python PDF_Merge.py
```

### Build Executable

```bash
# Windows
build_exe.bat
```

## Requirements

- Python 3.8+
- [customtkinter](https://github.com/TomSchimansky/CustomTkinter)
- [PyPDF2](https://pypi.org/project/PyPDF2/)

## License

[MIT](LICENSE)






