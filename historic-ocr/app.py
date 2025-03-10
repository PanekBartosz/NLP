import os
import io
import base64
import time
import uuid
from flask import Flask, request, jsonify, render_template, send_file, url_for
from flask_cors import CORS
from ultralytics import YOLO
from utils.ocr import detect_and_recognize_text
from utils.database import initialize_supabase, insert_result, get_result, get_all_results
import json
import pytesseract
from dotenv import load_dotenv
import logging

# Dodaj tę linię na początku pliku, przed inicjalizacją innych komponentów
load_dotenv()

# Dodaj tę linię na początku pliku
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Inicjalizacja aplikacji Flask
app = Flask(__name__)
CORS(app)

# Dodaj logowanie błędów
logging.basicConfig(level=logging.DEBUG)

# Konfiguracja
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/custom_text_detection2/weights/best.pt')
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Upewnij się, że katalogi istnieją
os.makedirs('static/css', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Sprawdź czy pliki CSS i JS istnieją
css_file = 'static/css/style.css'
js_file = 'static/js/main.js'

if not os.path.exists(css_file):
    app.logger.warning(f'Brak pliku CSS: {css_file}')
if not os.path.exists(js_file):
    app.logger.warning(f'Brak pliku JS: {js_file}')

# Inicjalizacja modelu YOLO
print(f"Ładowanie modelu YOLO z {MODEL_PATH}...")
model = YOLO(MODEL_PATH)

# Inicjalizacja Supabase
supabase = initialize_supabase()

# Dodaj obsługę błędów
@app.errorhandler(404)
def not_found_error(error):
    app.logger.error('Page not found: %s', (request.path))
    return jsonify(error=str(error)), 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error('Server Error: %s', (error))
    return jsonify(error=str(error)), 500

# Główna strona - interfejs użytkownika
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# REST API endpoint dla OCR
@app.route('/api/ocr', methods=['POST'])
def ocr_endpoint():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nie znaleziono pliku'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nie wybrano pliku'}), 400
        
        # Odczyt pliku obrazu
        image_bytes = file.read()
        
        app.logger.info(f'Rozpoczęto przetwarzanie pliku: {file.filename}')
        
        # Dodajemy pomiar czasu
        start_time = time.time()
        
        try:
            detected_texts, img_width, img_height = detect_and_recognize_text(image_bytes, model)
            
            # Obliczamy czas przetwarzania
            processing_time = time.time() - start_time
            
            app.logger.info(f'Wykryto {len(detected_texts)} obszarów tekstu w czasie {processing_time:.2f} sekund')
            
            if not detected_texts:
                app.logger.warning('Nie wykryto żadnego tekstu na obrazie')
                return jsonify({
                    'warning': 'Nie wykryto żadnego tekstu na obrazie',
                    'detected_texts': []
                })
                
        except Exception as e:
            app.logger.error(f'Błąd podczas przetwarzania obrazu: {str(e)}')
            return jsonify({'error': f'Błąd przetwarzania obrazu: {str(e)}'}), 500
        
        # Generowanie unikalnego ID
        result_id = str(uuid.uuid4())
        
        # Konwersja obrazu do base64
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        
        # Przygotowanie wyniku z dodanym czasem przetwarzania
        result_data = {
            'id': result_id,
            'image': encoded_image,
            'results': detected_texts,
            'image_width': img_width,
            'image_height': img_height,
            'processing_time': processing_time,  # Dodajemy czas przetwarzania
            'filename': file.filename,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Zapis do bazy danych
        try:
            insert_result(supabase, result_data)
        except Exception as e:
            app.logger.error(f'Błąd zapisu do bazy: {str(e)}')
            return jsonify({'error': f'Błąd zapisu do bazy: {str(e)}'}), 500
        
        return jsonify({
            'result_id': result_id,
            'detected_texts': detected_texts,
            'processing_time': processing_time
        })
    
    except Exception as e:
        app.logger.error(f'Nieoczekiwany błąd: {str(e)}')
        return jsonify({'error': f'Nieoczekiwany błąd: {str(e)}'}), 500

# Endpoint do pobierania wyników OCR
@app.route('/api/results/<result_id>', methods=['GET'])
def get_result_endpoint(result_id):
    try:
        result = get_result(supabase, result_id)
        
        if not result:
            return jsonify({'error': 'Nie znaleziono wyniku'}), 404
        
        return jsonify({'result': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Endpoint do wyświetlania historii
@app.route('/history', methods=['GET'])
def history():
    try:
        results = get_all_results(supabase)
        return render_template('history.html', results=results)
    except Exception as e:
        return render_template('error.html', error=str(e))

# Endpoint do wyświetlania szczegółów wyniku
@app.route('/view/<result_id>', methods=['GET'])
def view_result(result_id):
    try:
        result = get_result(supabase, result_id)
        
        if not result:
            return render_template('error.html', error='Nie znaleziono wyniku')
        
        return render_template('view.html', result=result)
    
    except Exception as e:
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
