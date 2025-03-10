import os
import yaml
import shutil
from pathlib import Path
import random
from tqdm import tqdm
import cv2
import numpy as np

# Konfiguracja ścieżek
DATA_ROOT = 'data/data'
OUTPUT_PATH = 'datasets/custom_yolo'
MODEL_SAVE_PATH = 'models'

"""
# Zakomentowana część przygotowania danych, ponieważ już są przygotowane
def create_dataset_structure():
    for split in ['train', 'val', 'test']:
        for subdir in ['images', 'labels']:
            path = os.path.join(OUTPUT_PATH, split, subdir)
            os.makedirs(path, exist_ok=True)

def prepare_data():
    print("Przygotowywanie danych...")
    
    create_dataset_structure()
    
    all_images = []
    for root, _, files in os.walk(DATA_ROOT):
        for file in files:
            if file.endswith('.png'):
                all_images.append(os.path.join(root, file))
    
    random.shuffle(all_images)
    total = len(all_images)
    train_size = int(total * 0.8)
    val_size = int(total * 0.1)
    
    train_images = all_images[:train_size]
    val_images = all_images[train_size:train_size+val_size]
    test_images = all_images[train_size+val_size:]
    
    def process_image(img_path, split):
        img = cv2.imread(img_path)
        if img is None:
            return
        
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        img_filename = os.path.basename(img_path)
        cv2.imwrite(os.path.join(OUTPUT_PATH, split, 'images', img_filename), img)
        
        label_filename = os.path.splitext(img_filename)[0] + '.txt'
        label_path = os.path.join(OUTPUT_PATH, split, 'labels', label_filename)
        
        with open(label_path, 'w') as f:
            for contour in contours:
                if cv2.contourArea(contour) < 100:
                    continue
                
                x, y, w_box, h_box = cv2.boundingRect(contour)
                x_center = (x + w_box/2) / w
                y_center = (y + h_box/2) / h
                width = w_box / w
                height = h_box / h
                
                f.write(f"0 {x_center} {y_center} {width} {height}\n")
    
    for images, split in [(train_images, 'train'), (val_images, 'val'), (test_images, 'test')]:
        print(f"Przetwarzanie zbioru {split}...")
        for img_path in tqdm(images):
            process_image(img_path, split)
"""

def create_dataset_yaml():
    """Tworzenie pliku konfiguracyjnego YAML dla YOLO"""
    yaml_content = {
        'path': os.path.abspath(OUTPUT_PATH),
        'train': 'train/images',
        'val': 'val/images',
        'test': 'test/images',
        'names': {
            0: 'text'
        }
    }
    
    yaml_path = os.path.join(OUTPUT_PATH, 'dataset.yaml')
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_content, f, sort_keys=False)
    
    return yaml_path

def train_model():
    """Trenowanie modelu YOLO"""
    from ultralytics import YOLO
    
    print("Rozpoczynanie treningu modelu...")
    
    os.makedirs(MODEL_SAVE_PATH, exist_ok=True)
    
    # Inicjalizacja modelu YOLO
    model = YOLO('yolov8n.pt')
    
    # Trenowanie modelu - zmniejszona liczba epok do 3
    yaml_path = create_dataset_yaml()
    results = model.train(
        data=yaml_path,
        epochs=3,  # Zmniejszono z 50 do 3
        imgsz=640,
        batch=16,
        patience=10,
        save=True,
        project=MODEL_SAVE_PATH,
        name='custom_text_detection'
    )
    
    print(f"Model zapisany w {MODEL_SAVE_PATH}/custom_text_detection")
    return results

if __name__ == '__main__':
    # prepare_data()  # Zakomentowane, bo dane są już przygotowane
    train_model()
