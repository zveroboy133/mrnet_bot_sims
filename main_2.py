import cv2 # Импортируем библиотеку OpenCV-Python
import numpy as np
import easyocr
from PIL import Image
import os
import platform
import ssl
import certifi

# Настройка SSL для решения проблем с сертификатами
ssl._create_default_https_context = ssl._create_unverified_context

# Указываем путь к исполняемому файлу Tesseract только для Windows
if platform.system() == 'Windows':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def create_output_dir():
    # Создаем директорию для сохранения результатов
    output_dir = "processing_steps"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    return output_dir

def save_image(image, filename, output_dir):
    # Сохраняем изображение
    output_path = os.path.join(output_dir, filename)
    cv2.imwrite(output_path, image)
    return output_path

def preprocess_image(image_path, output_dir):
    # Загрузка изображения
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError("Не удалось загрузить изображение")
    
    # Сохраняем оригинальное изображение
    save_image(img, "1_original.jpg", output_dir)
    
    # Конвертация в оттенки серого
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    save_image(gray, "2_gray.jpg", output_dir)
    
    # Применение размытия для уменьшения шума
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    save_image(blur, "3_blur.jpg", output_dir)
    
    # Применение адаптивной пороговой обработки
    thresh = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
    )
    save_image(thresh, "4_threshold.jpg", output_dir)
    
    # Морфологические операции для улучшения качества
    kernel = np.ones((2,2), np.uint8)
    morph = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    save_image(morph, "5_morph.jpg", output_dir)
    
    return morph, img

def find_text_regions(image, original_img, output_dir):
    # Поиск контуров
    contours, _ = cv2.findContours(
        image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Создаем копию изображения для отрисовки контуров
    contour_img = original_img.copy()
    cv2.drawContours(contour_img, contours, -1, (0, 255, 0), 2)
    save_image(contour_img, "6_all_contours.jpg", output_dir)
    
    # Фильтрация контуров по размеру
    min_area = 100  # Минимальная площадь контура
    text_regions = []
    
    # Создаем изображение для отображения отфильтрованных контуров
    filtered_contour_img = original_img.copy()
    
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > min_area:
            x, y, w, h = cv2.boundingRect(contour)
            text_regions.append((x, y, w, h))
            # Рисуем прямоугольник вокруг области с текстом
            cv2.rectangle(filtered_contour_img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    save_image(filtered_contour_img, "7_filtered_regions.jpg", output_dir)
    
    return text_regions

def extract_text(image, regions, original_img, output_dir):
    results = []
    # Создаем изображение для отображения распознанных областей
    recognition_img = original_img.copy()
    
    try:
        # Инициализируем EasyOCR с дополнительными параметрами
        reader = easyocr.Reader(
            ['en'],
            gpu=False,
            download_enabled=True,
            model_storage_directory='./easyocr_models',
            user_network_directory='./easyocr_models',
            recog_network='english_g2'
        )
        
        for i, (x, y, w, h) in enumerate(regions):
            try:
                # Вырезаем область с текстом
                roi = image[y:y+h, x:x+w]
                
                # Добавляем отступы для лучшего распознавания
                padding = 10
                roi = cv2.copyMakeBorder(roi, padding, padding, padding, padding, 
                                    cv2.BORDER_CONSTANT, value=255)
                
                # Сохраняем каждую область отдельно
                save_image(roi, f"8_region_{i+1}.jpg", output_dir)
                
                # Распознаем текст с помощью EasyOCR
                result = reader.readtext(roi)
                
                if result:  # Если текст найден
                    text = result[0][1]  # Берем только текст из результата
                    # Очищаем текст от нецифровых символов
                    text = ''.join(filter(str.isdigit, text))
                    
                    if text:  # Если остались цифры
                        results.append(text)
                        # Добавляем текст на изображение
                        cv2.putText(recognition_img, text, (x, y-10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            except Exception as e:
                print(f"Ошибка при обработке области {i+1}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Ошибка при инициализации EasyOCR: {str(e)}")
        return results
    
    save_image(recognition_img, "9_recognition_result.jpg", output_dir)
    return results

def process_image(image_path):
    # Создаем директорию для результатов
    output_dir = create_output_dir()
    
    # Предобработка изображения
    processed_img, original_img = preprocess_image(image_path, output_dir)
    
    # Поиск областей с текстом
    text_regions = find_text_regions(processed_img, original_img, output_dir)
    
    # Извлечение текста из найденных областей
    numbers = extract_text(processed_img, text_regions, original_img, output_dir)
    
    return numbers, output_dir

if __name__ == "__main__":
    # Путь к изображению
    image_path = "crop_photo_2025-05-29_17-14-39.png"  # Замените на путь к вашему изображению
    
    try:
        # Обработка изображения
        found_numbers, output_dir = process_image(image_path)
        
        # Вывод результатов
        print("Найденные номера:")
        for number in found_numbers:
            print(number)
            
        print(f"\nПромежуточные результаты сохранены в директории: {output_dir}")
        print("Порядок обработки изображений:")
        print("1. Оригинальное изображение")
        print("2. Оттенки серого")
        print("3. Размытие")
        print("4. Пороговая обработка")
        print("5. Морфологические операции")
        print("6. Все найденные контуры")
        print("7. Отфильтрованные области с текстом")
        print("8. Отдельные области с текстом")
        print("9. Финальный результат с распознанным текстом")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
