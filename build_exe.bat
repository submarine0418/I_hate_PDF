@echo off
echo ============================================
echo   Building PDF Merge Tool (.exe)
echo ============================================
echo.

pip install pyinstaller customtkinter PyPDF2 PyMuPDF Pillow

pyinstaller --noconfirm --onefile --windowed ^
    --name "PDFMergeTool" ^
    --collect-all customtkinter ^
    --hidden-import fitz ^
    --hidden-import PIL ^
    PDF_Merge.py

echo.
echo Build complete! Check the dist\ folder.
pause