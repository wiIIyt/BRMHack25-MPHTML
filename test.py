import pytesseract

text = pytesseract.image_to_string('uploads/processed/receipt-ocr-original.webp', lang='eng')
print(text)