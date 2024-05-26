import pytesseract as tess
from PIL import Image

tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

i = Image.open('aadhar 1.jpeg')
txt = tess.image_to_string(i)
print(txt)
