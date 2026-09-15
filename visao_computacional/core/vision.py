import cv2
import numpy as np
#máscara, contorno, desenho

def criar_mascara(frame_hsv, cor_min, cor_max, kernel_size=5, erode_iter=1, dilate_iter=2):
    """
    Cria máscara binária para a faixa HSV informada.
    """
    mascara = cv2.inRange(frame_hsv, cor_min, cor_max)
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    mascara = cv2.erode(mascara, kernel, iterations=erode_iter)
    mascara = cv2.dilate(mascara, kernel, iterations=dilate_iter)
    return mascara


def encontrar_maior_contorno(mascara, area_minima=500):
    """
    Retorna o maior contorno válido da máscara (ou None).
    """
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return None

    maior = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(maior) < area_minima:
        return None
    return maior


def desenhar_caixa(frame_bgr, contorno, cor=(0, 255, 0), espessura=2):
    """
    Desenha bounding box do contorno e retorna (x, y, w, h).
    """
    x, y, w, h = cv2.boundingRect(contorno)
    cv2.rectangle(frame_bgr, (x, y), (x + w, y + h), cor, espessura)
    return x, y, w, h


def escrever_texto(frame_bgr, texto, pos, cor=(255, 255, 255), escala=0.6, espessura=2):
    cv2.putText(
        frame_bgr,
        texto,
        pos,
        cv2.FONT_HERSHEY_SIMPLEX,
        escala,
        cor,
        espessura
    )


def bgr_para_hsv(frame_bgr):
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)


def bgr_para_rgb(frame_bgr):
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)