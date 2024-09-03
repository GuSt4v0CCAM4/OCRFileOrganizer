import cv2
import pytesseract
import numpy as np
from pdf2image import convert_from_path
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
import gc
from fpdf import FPDF


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
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    coords = cv2.findNonZero(binary)
    x, y, w, h = cv2.boundingRect(coords)

    x = max(0, x - margen)
    y = max(0, y - margen)
    w = min(img.shape[1], x + w + margen)
    h = min(img.shape[0], y + h + margen)

    cropped_img = img[y:h, x:w]

    return cropped_img


def OCR_input(image_path):
    img = cv2.imread(image_path)
    img = detectar_area_con_texto(img)

    height, width = img.shape[:2]
    mid_width = width // 2

    left_img = img[:, :mid_width]
    right_img = img[:, mid_width:]

    left_gray = cv2.cvtColor(left_img, cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right_img, cv2.COLOR_BGR2GRAY)

    left_code = pytesseract.image_to_string(left_gray, lang='spa')
    right_code = pytesseract.image_to_string(right_gray, lang='spa')

    left_code = procesar_OCR(left_code)
    right_code = procesar_OCR(right_code)

    final_code = left_code if left_code else right_code
    print(image_path)
    print(final_code)
    return final_code


def process_image(image_path, output_folder):
    code = OCR_input(image_path)
    new_image_path = os.path.join(output_folder, f'{code}_{os.path.basename(image_path)}')
    os.rename(image_path, new_image_path)


def PDF_to_image(pdf_path, output_folder, dpi=200):
    images = convert_from_path(pdf_path, dpi=dpi)

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    image_paths = []
    for i, image in enumerate(images):
        image_path = os.path.join(output_folder, f'page_{i + 1}.png')
        image.save(image_path, 'PNG')
        image_paths.append(image_path)
        image.close()
        gc.collect()

    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(process_image, image_paths, [output_folder] * len(image_paths))


def move_file(ruta_origen, ruta_destino):
    try:
        shutil.move(ruta_origen, ruta_destino)
    except Exception as e:
        print(f"Error al mover el archivo {ruta_origen}: {e}")


def convert_images_to_pdf(image_folder, output_pdf_path):
    pdf = FPDF()

    images = [img for img in os.listdir(image_folder) if img.endswith(".png")]
    images.sort()

    for image in images:
        image_path = os.path.join(image_folder, image)
        pdf.add_page()
        pdf.image(image_path, x=0, y=0, w=210, h=297)  # Ajuste a tamaño A4

    pdf.output(output_pdf_path, "F")


def organizador(input_images, folder_path):
    folder_paths = {}

    with ThreadPoolExecutor(max_workers=4) as executor:
        for name in os.listdir(input_images):
            if os.path.isfile(os.path.join(input_images, name)):
                code = name.split('_')[0]

                if code == 'None':
                    continue

                if code not in folder_paths:
                    folder_path_code = os.path.join(folder_path, code)
                    folder_paths[code] = folder_path_code
                    os.makedirs(folder_path_code, exist_ok=True)

                ruta_origen = os.path.join(input_images, name)
                ruta_destino = os.path.join(folder_paths[code], name)
                executor.submit(move_file, ruta_origen, ruta_destino)

    # Convertir imágenes a PDF después de organizarlas
    print("Convirtiendo imágenes a PDF...")
    for code, path in folder_paths.items():
        output_pdf_path = os.path.join(path, f"{code}.pdf")
        convert_images_to_pdf(path, output_pdf_path)


# Ejemplo de uso
pdf_path = '01.pdf'
output_folder = 'images'
PDF_to_image(pdf_path, output_folder)
folder_path = '/home/lorsgusty07/PycharmProjects/OCR_para_clasificacion_de_documentos/organizado'
organizador(output_folder, folder_path)
