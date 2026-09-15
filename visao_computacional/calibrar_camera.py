"""
Calibração FIXA da câmera.

OBJETIVO:
    Rodar esse script UMA VEZ, com a câmera já instalada na posição
    final (mesmo ângulo/altura que vai ficar permanentemente), com o
    objeto de referência (folha A4) visível na cena.

    O script detecta a referência, calcula quantos pixels equivalem
    a 1 cm NAQUELA posição específica da câmera, e salva esse valor
    em um arquivo (calibracao.json).

    Depois disso, o script de medição (medir_grama_fixo.py) usa esse
    valor salvo para sempre — sem precisar da referência na cena de novo.

IMPORTANTE:
    Se a câmera for movida, trocar de altura, ângulo ou zoom, você
    precisa rodar essa calibração de novo.

REQUISITOS:
    pip install opencv-python numpy

COMO USAR:
    1. Posicione a câmera no local/ângulo definitivo.
    2. Coloque a folha A4 (referência) na cena, no mesmo plano do chão
       onde a grama será medida.
    3. Rode o script.
    4. Quando o retângulo azul aparecer estável na referência, aperte 's'.
    5. O valor será salvo em calibracao.json.
"""

import cv2
import numpy as np
import json
import os

# Tamanho real da referência (folha A4 vertical = 21 cm de largura)
REFERENCIA_LARGURA_CM = 21.0

# Faixa de cor HSV da referência (ajuste se mudar o objeto/cor)
HSV_REF_MIN = (116, 40, 0)
HSV_REF_MAX = (179, 255, 222)

AREA_MINIMA = 500
ARQUIVO_CALIBRACAO = "calibracao.json"


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


def salvar_calibracao(pixels_por_cm):
    dados = {"pixels_por_cm": pixels_por_cm}
    with open(ARQUIVO_CALIBRACAO, "w") as f:
        json.dump(dados, f, indent=2)
    print(f"\nCalibração salva em '{ARQUIVO_CALIBRACAO}': {dados}\n")


def main():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Erro: não consegui acessar a câmera.")
        return

    print("Posicione a referência na cena.")
    print("Pressione 's' quando o retângulo azul estiver estável na referência.")
    print("Pressione 'q' para sair sem salvar.")

    while True:
        ok, frame = cap.read()
        if not ok:
            print("Erro ao capturar frame.")
            break

        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mascara_ref = criar_mascara(frame_hsv, HSV_REF_MIN, HSV_REF_MAX)
        contorno_ref = encontrar_maior_contorno(mascara_ref)

        pixels_por_cm_atual = None

        if contorno_ref is not None:
            x, y, w, h = cv2.boundingRect(contorno_ref)
            pixels_por_cm_atual = w / REFERENCIA_LARGURA_CM

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2.putText(
                frame, f"{pixels_por_cm_atual:.2f} px/cm", (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2
            )
        else:
            cv2.putText(
                frame, "Referencia nao detectada", (20, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
            )

        cv2.imshow("Calibracao - Camera", frame)
        cv2.imshow("Mascara Referencia", mascara_ref)

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord('q'):
            print("Saindo sem salvar calibração.")
            break

        elif tecla == ord('s'):
            if pixels_por_cm_atual is not None:
                salvar_calibracao(pixels_por_cm_atual)
                break
            else:
                print("Referência não detectada no momento. Ajuste e tente de novo.")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()