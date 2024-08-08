import cv2
import pytesseract
from pdf2image import convert_from_path
import os

def OCR_input(image_path):
    #Area del crop de la imagen
    crop_region = (10, 10, 1500, 150)

    #Cargar la imagen
    img = cv2.imread(image_path)

    img = img[crop_region[1]:crop_region[3], crop_region[0]:crop_region[2]]
    # Redimensionar la imagen para aumentar el tamaño
    scale_percent = 100  # Porcentaje de aumento
    width = int(img.shape[1] * scale_percent / 100)
    height = int(img.shape[0] * scale_percent / 100)
    dim = (width, height)
    resized = cv2.resize(img, dim, interpolation=cv2.INTER_LINEAR)

    # Convertir a escala de grises
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # Aplicar desenfoque gaussiano para suavizar la imagen
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Aumentar el contraste
    alpha = 1.88  # Contraste
    beta = 0  # Brillo
    contrasted = cv2.convertScaleAbs(blurred, alpha=alpha, beta=beta)

    # Aplicar umbral para convertir a imagen binaria
    _, threshold_img = cv2.threshold(contrasted, 128, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Pasar a tesseract
    text = pytesseract.image_to_string(contrasted, lang='spa')

    #cv2.imshow('resized', resized)
    #cv2.imshow('gray', gray)
    #cv2.imshow('blurred', blurred)
    #cv2.imshow('contrasted', contrasted)
    #cv2.imshow('threshold', threshold_img)

    print(text)
    return text
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

def PDF_to_image(pdf_path, output_folder):
    #Convertir pdf a imagen

