import pytesseract as tess
from PIL import Image
import cv2
from tkinter import Tk, Label, Button, filedialog, Text
from pdf2image import convert_from_path
import os
import re

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
        visitor_info = extract_visitor_information(extracted_text)
        validated_info = validate_visitor_information(visitor_info)
        display_extracted_info(validated_info)

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
    print("OCR Output:\n", txt)  # Debugging statement
    return txt

def extract_visitor_information(text):
    # Improved regex patterns for extraction
    visitor_info = {
        "name": re.search(r"Name[:\s]*(.*)", text, re.IGNORECASE),
        "date_of_visit": re.search(r"Date of Visit[:\s]*(.*)", text, re.IGNORECASE),
        "purpose": re.search(r"Purpose[:\s]*(.*)", text, re.IGNORECASE),
        "dob": re.search(r"Date of Birth[:\s]*(.*)", text, re.IGNORECASE)
    }
    # Extract and clean data
    for key in visitor_info:
        if visitor_info[key]:
            visitor_info[key] = visitor_info[key].group(1).strip()
        else:
            visitor_info[key] = None
    return visitor_info

def validate_visitor_information(info):
    errors = []
    if not info["name"]:
        errors.append("Name is missing.")
    if not info["date_of_visit"]:
        errors.append("Date of Visit is missing.")
    elif not re.match(r"\d{4}-\d{2}-\d{2}", info["date_of_visit"]):
        errors.append("Date of Visit format should be YYYY-MM-DD.")
    if not info["purpose"]:
        errors.append("Purpose is missing.")
    if not info["dob"]:
        errors.append("Date of Birth is missing.")
    elif not re.match(r"\d{4}-\d{2}-\d{2}", info["dob"]):
        errors.append("Date of Birth format should be YYYY-MM-DD.")
    
    info["errors"] = errors
    return info

def display_extracted_info(info):
    text_display.delete('1.0', 'end')
    if info["errors"]:
        text_display.insert('1.0', "Errors:\n" + "\n".join(info["errors"]) + "\n\n")
    text_display.insert('1.0', "Extracted Information:\n")
    for key, value in info.items():
        if key != "errors":
            text_display.insert('end', f"{key.capitalize()}: {value}\n")

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
        visitor_info = extract_visitor_information(extracted_text)
        validated_info = validate_visitor_information(visitor_info)
        display_extracted_info(validated_info)

if __name__ == "__main__":
    create_gui()
