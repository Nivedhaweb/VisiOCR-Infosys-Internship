import pytesseract as tess
from PIL import Image

i=Image.open('image_path')
txt=tess.image_to_string(i)
print(txt)