@echo off
echo ============================================
echo   Building PDF Merge Tool (.exe)
echo ============================================
echo.

pip install pyinstaller customtkinter PyPDF2

pyinstaller --noconfirm --onefile --windowed ^
    --name "PDFMergeTool" ^
    --collect-all customtkinter ^
    PDF_Merge.py

echo.
echo Build complete! Check the dist\ folder.
pause