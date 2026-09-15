"""
Medição de grama usando CALIBRAÇÃO FIXA (já salva anteriormente).

PRÉ-REQUISITO:
    Ter rodado o 'medir_grama_fixo.py' antes, com a câmera já na
    posição definitiva. Isso gera o arquivo 'calibracao.json'.

DIFERENÇA para o medir_grama.py original:
    Esse script NÃO procura objeto de referência na cena. Ele lê a
    razão pixels/cm salva no calibracao.json e assume que a câmera
    está na MESMA posição/ângulo/altura de quando foi calibrada.

REQUISITOS:
    pip install opencv-python numpy
"""

import cv2
import numpy as np
import json
import os
from datetime import datetime

ARQUIVO_CALIBRACAO = "calibracao.json"
PASTA_FOTOS = "dados/fotos_medicoes_fixo"
os.makedirs(PASTA_FOTOS, exist_ok=True)

# Faixa de cor (HSV) da grama — mesma calibração de antes.
HSV_GRAMA_MIN = (24, 41, 28)
HSV_GRAMA_MAX = (91, 255, 255)

AREA_MINIMA = 500

contador_fotos = 0


def carregar_calibracao():
    """Lê o arquivo de calibração salvo. Retorna None se não existir."""
    if not os.path.exists(ARQUIVO_CALIBRACAO):
        return None

    with open(ARQUIVO_CALIBRACAO, "r") as f:
        dados = json.load(f)

    return dados.get("pixels_por_cm")


def encontrar_maior_contorno(mascara):
    contornos, _ = cv2.findContours(
        mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    if not contornos:
        return None
    maior = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(maior) < AREA_MINIMA:
        return None
    return maior


def criar_mascara(frame_hsv, cor_min, cor_max):
    mascara = cv2.inRange(frame_hsv, cor_min, cor_max)
    kernel = np.ones((5, 5), np.uint8)
    mascara = cv2.erode(mascara, kernel, iterations=1)
    mascara = cv2.dilate(mascara, kernel, iterations=2)
    return mascara


def formatar_medida(cm):
    if cm >= 100:
        return f"{cm / 100:.2f} m"
    return f"{cm:.1f} cm"


def main():
    global contador_fotos

    pixels_por_cm = carregar_calibracao()

    if pixels_por_cm is None:
        print("ERRO: arquivo de calibração não encontrado ou inválido.")
        print("Rode primeiro o 'medir_grama_fixo.py' com a câmera")
        print("já na posição definitiva.")
        return

    print(f"Calibração carregada: {pixels_por_cm:.2f} pixels/cm")
    print("(Se a câmera mudou de posição, recalibre antes de usar isso.)")

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: não consegui acessar a câmera.")
        return

    print("Pressione ESPAÇO para salvar uma foto do resultado.")
    print("Pressione 'q' para sair.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Erro ao capturar frame.")
            break

        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mascara_grama = criar_mascara(frame_hsv, HSV_GRAMA_MIN, HSV_GRAMA_MAX)
        contorno_grama = encontrar_maior_contorno(mascara_grama)

        if contorno_grama is not None:
            x, y, w, h = cv2.boundingRect(contorno_grama)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            largura_cm = w / pixels_por_cm
            altura_cm = h / pixels_por_cm

            cv2.putText(
                frame, f"Largura: {formatar_medida(largura_cm)}", (x, y - 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )
            cv2.putText(
                frame, f"Altura: {formatar_medida(altura_cm)}", (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2
            )

        cv2.imshow("Camera", frame)
        cv2.imshow("Mascara Grama", mascara_grama)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord('q'):
            break

        elif tecla == ord(' '):
            contador_fotos += 1
            nome_arquivo = f"foto_medicao_fixa_{contador_fotos}_{datetime.now().strftime('%d-%m-%Y_%H-%M-%S')}.png"
            caminho_completo = os.path.join(PASTA_FOTOS, nome_arquivo)
            cv2.imwrite(caminho_completo, frame)
            print(f"Foto salva: {caminho_completo}")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

