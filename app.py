import cv2
from PIL import Image
import pytesseract as tess

# Set the path to the Tesseract executable if necessary
# tess.pytesseract.tesseract_cmd = r'path_to_tesseract_executable'

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

image_path = capture_image()
if image_path:
    processed_image_path = preprocess_image(image_path)
    extracted_text = extract_text_from_image(processed_image_path)
    print("Extracted Text from Processed Image:")
    print(extracted_text)
