import cv2
import pytesseract
import numpy as np
from utils.preprocessing import preprocess_image_for_ocr

def detect_and_recognize_text(image_bytes, model, conf_threshold=0.25):
    """
    Detekcja regionów tekstu za pomocą YOLO i rozpoznawanie za pomocą Tesseract
    """
    # Konwersja bajtów na obraz
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_height, img_width = img.shape[:2]
    
    # Detekcja regionów tekstu za pomocą YOLO
    results = model(img, conf=conf_threshold)
    
    # Przechowywanie wyników
    detected_texts = []
    
    if len(results) > 0 and len(results[0].boxes) > 0:
        # Pobierz wszystkie bounding boxy
        boxes = []
        for box in results[0].boxes:
            try:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                confidence = float(box.conf[0])
                # Filtruj małe boxy i te z niską pewnością
                if (x2 - x1) > 20 and (y2 - y1) > 10 and confidence > 0.3:
                    boxes.append([x1, y1, x2, y2, confidence])
            except Exception as e:
                print(f"Błąd podczas przetwarzania boxa: {str(e)}")
                continue
        
        # Sortuj boxy według pozycji y (od góry do dołu)
        boxes.sort(key=lambda x: x[1])
        
        # Łącz boxy w linie tekstu
        merged_boxes = []
        current_line = []
        
        for box in boxes:
            if not current_line:
                current_line.append(box)
            else:
                # Sprawdź czy box należy do tej samej linii
                prev_box = current_line[-1]
                y_diff = abs(box[1] - prev_box[1])
                
                if y_diff < 20:  # Jeśli różnica y jest mała, to ta sama linia
                    current_line.append(box)
                else:
                    # Połącz boxy w linii
                    if len(current_line) > 0:
                        x1 = min(b[0] for b in current_line)
                        y1 = min(b[1] for b in current_line)
                        x2 = max(b[2] for b in current_line)
                        y2 = max(b[3] for b in current_line)
                        conf = sum(b[4] for b in current_line) / len(current_line)
                        merged_boxes.append([x1, y1, x2, y2, conf])
                    current_line = [box]
        
        # Dodaj ostatnią linię
        if current_line:
            x1 = min(b[0] for b in current_line)
            y1 = min(b[1] for b in current_line)
            x2 = max(b[2] for b in current_line)
            y2 = max(b[3] for b in current_line)
            conf = sum(b[4] for b in current_line) / len(current_line)
            merged_boxes.append([x1, y1, x2, y2, conf])
        
        # Przetwórz połączone boxy
        for box in merged_boxes:
            x1, y1, x2, y2, confidence = box
            
            # Dodaj margines
            padding = 5
            x1 = max(0, x1 - padding)
            y1 = max(0, y1 - padding)
            x2 = min(img_width, x2 + padding)
            y2 = min(img_height, y2 + padding)
            
            # Wytnij region
            roi = img[y1:y2, x1:x2]
            
            # Preprocessing
            processed_roi = preprocess_image_for_ocr(roi)
            
            # Konfiguracja Tesseract
            custom_config = r'--oem 3 --psm 6'  # Używamy domyślnego języka
            
            # Rozpoznawanie tekstu
            text = pytesseract.image_to_string(processed_roi, config=custom_config)
            text = text.strip()
            
            # Dodaj tylko jeśli tekst nie jest pusty i ma więcej niż 1 znak
            if text and len(text) > 1:
                detected_texts.append({
                    'region': [x1, y1, x2, y2],
                    'text': text,
                    'confidence': confidence
                })
    
    return detected_texts, img_width, img_height

def preprocess_image_for_ocr(image):
    """
    Ulepszone przetwarzanie obrazu dla OCR
    """
    # Konwersja do skali szarości
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Powiększenie obrazu
    gray = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    
    # Redukcja szumu
    denoised = cv2.fastNlMeansDenoising(gray)
    
    # Normalizacja kontrastu
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    normalized = clahe.apply(denoised)
    
    # Binaryzacja adaptacyjna
    binary = cv2.adaptiveThreshold(
        normalized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2
    )
    
    # Operacje morfologiczne
    kernel = np.ones((1,1), np.uint8)
    binary = cv2.dilate(binary, kernel, iterations=1)
    binary = cv2.erode(binary, kernel, iterations=1)
    
    return binary
