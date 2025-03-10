import cv2
import numpy as np

def preprocess_image_for_ocr(image):
    """
    Przygotowanie obrazu do OCR
    """
    # Resize obrazu
    image = cv2.resize(image, None, fx=2, fy=2)
    
    # Konwersja do skali szarości
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Gaussian blur
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Binaryzacja z metodą Otsu
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    # Odwrócenie kolorów (czarny tekst na białym tle) dla Tesseract
    thresh = cv2.bitwise_not(thresh)
    
    # Operacje morfologiczne dla lepszej jakości
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.dilate(thresh, kernel, iterations=1)
    processed = cv2.erode(processed, kernel, iterations=1)
    
    return processed
