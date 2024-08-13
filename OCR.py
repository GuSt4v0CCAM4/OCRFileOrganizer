import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import gc


def es_codigo(string):
    return string.isdigit() and len(string) == 5


def procesar_OCR(string):
    if not isinstance(string, str):
        return None
    palabras = string.split()
    for palabra in palabras:
        if es_codigo(palabra):
            return palabra
    return None


def detectar_area_con_texto(img, margen=10):
    """
    Detecta la primera fila y columna con píxeles oscuros y recorta la imagen
    """
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    coords = cv2.findNonZero(binary)  # Encuentra los píxeles blancos (que eran negros en el original)
    x, y, w, h = cv2.boundingRect(coords)  # Encuentra el área mínima que contiene el texto

    # Añadir un margen para evitar cortar letras
    x = max(0, x - margen)
    y = max(0, y - margen)
    w = min(img.shape[1], x + w + margen)
    h = min(img.shape[0], y + h + margen)

    # Recortar la imagen
    cropped_img = img[y:h, x:w]

    return cropped_img


def OCR_input(image_path):
    # Cargar la imagen
    img = cv2.imread(image_path)

    # Detectar el área con texto
    img = detectar_area_con_texto(img)

    # Dividir la imagen en dos partes
    height, width = img.shape[:2]
    mid_width = width // 2

    # Lado izquierdo
    left_img = img[:, :mid_width]

    # Lado derecho
    right_img = img[:, mid_width:]

    # Convertir a escala de grises
    left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)

    # Pasar a tesseract directamente en ambos lados
    left_code = pytesseract.image_to_string(left_gray, lang='spa')
    right_code = pytesseract.image_to_string(right_gray, lang='spa')

    # Procesar los textos para extraer el código
    left_code = procesar_OCR(left_code)
    right_code = procesar_OCR(right_code)

    # Retornar el código encontrado, dando prioridad al lado izquierdo
    final_code = left_code if left_code else right_code
    print(image_path)
    print(final_code)
    return final_code


def process_image(image_path, output_folder):
    code = OCR_input(image_path)
    new_image_path = os.path.join(output_folder, f'{code}_{os.path.basename(image_path)}')
    os.rename(image_path, new_image_path)


def PDF_to_image(pdf_path, output_folder, dpi=200):
    # Convertir PDF a imágenes con una resolución específica (dpi)
    images = convert_from_path(pdf_path, dpi=dpi)

    # Nos aseguramos que la carpeta existe
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Guardamos cada imagen en la carpeta
    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f'page_{i + 1}.png')
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
        image.close()
        gc.collect()

    # Procesar imágenes en paralelo
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_image, image_paths, [output_folder] * len(image_paths))


def move_file(ruta_origen, ruta_destino):
    try:
        shutil.move(ruta_origen, ruta_destino)
    except Exception as e:
        print(f"Error al mover el archivo {ruta_origen}: {e}")


def organizador(input_images, folder_path):
    # Crear un diccionario para almacenar las rutas de destino para cada código
    folder_paths = {}

    # Crear un pool de hilos
    with ThreadPoolExecutor(max_workers=4) as executor:
        # Iterar sobre los archivos en la carpeta input_images
        for name in os.listdir(input_images):
            if os.path.isfile(os.path.join(input_images, name)):
                code = name.split('_')[0]

                if code == 'None':
                    continue

                # Verificar si ya existe la ruta de la carpeta para este código
                if code not in folder_paths:
                    folder_path_code = os.path.join(folder_path, code)
                    folder_paths[code] = folder_path_code
                    os.makedirs(folder_path_code, exist_ok=True)

                # Mover el archivo a la carpeta correspondiente en un hilo separado
                ruta_origen = os.path.join(input_images, name)
                ruta_destino = os.path.join(folder_paths[code], name)
                executor.submit(move_file, ruta_origen, ruta_destino)


# Ejemplo de uso
pdf_path = '01.pdf'
output_folder = 'images'
PDF_to_image(pdf_path, output_folder)
folder_path = '/home/lorsgusty07/PycharmProjects/OCR_para_clasificacion_de_documentos/organizado'
organizador(output_folder, folder_path)
