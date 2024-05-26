import cv2
from PIL import Image
import pytesseract as tess
from tkinter import Tk, Label, Button, filedialog, Text
from pdf2image import convert_from_path
import os

# Set the path to the Tesseract executable
tess.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def capture_image():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        return None

    print("Press 's' to capture image and 'q' to quit.")
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture image.")
            break

        cv2.imshow('Capture Image', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('s'):
            image_path = 'captured_image.jpg'
            cv2.imwrite(image_path, frame)
            print(f"Image captured and saved as {image_path}")
            break
        elif key == ord('q'):
            print("Image capture cancelled.")
            break

    cap.release()
    cv2.destroyAllWindows()
    return image_path

def select_file():
    file_path = filedialog.askopenfilename(
        filetypes=[("Image files", "*.jpg *.jpeg *.png"), ("PDF files", "*.pdf")]
    )
    if file_path:
        ext = os.path.splitext(file_path)[1].lower()
        if ext == '.pdf':
            images = convert_from_path(file_path)
            image_path = 'temp_image.jpg'
            images[0].save(image_path, 'JPEG')
        else:
            image_path = file_path
        processed_image_path = preprocess_image(image_path)
        extracted_text = extract_text_from_image(processed_image_path)
        text_display.delete('1.0', 'end')
        text_display.insert('1.0', extracted_text)

def preprocess_image(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    processed_image_path = 'processed_image.jpg'
    cv2.imwrite(processed_image_path, binary)
    return processed_image_path

def extract_text_from_image(image_path):
    i = Image.open(image_path)
    txt = tess.image_to_string(i)
    return txt

def create_gui():
    global text_display
    root = Tk()
    root.title("OCR Image/Text Extractor")

    label = Label(root, text="Upload an Image/PDF or Capture Image from Webcam")
    label.pack(pady=10)

    capture_button = Button(root, text="Capture Image from Webcam", command=capture_and_process)
    capture_button.pack(pady=5)

    upload_button = Button(root, text="Upload File", command=select_file)
    upload_button.pack(pady=5)

    text_display = Text(root, wrap='word', height=20, width=60)
    text_display.pack(pady=10)

    root.mainloop()

def capture_and_process():
    image_path = capture_image()
    if image_path:
        processed_image_path = preprocess_image(image_path)
        extracted_text = extract_text_from_image(processed_image_path)
        text_display.delete('1.0', 'end')
        text_display.insert('1.0', extracted_text)

if __name__ == "__main__":
    create_gui()
