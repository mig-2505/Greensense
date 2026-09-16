import cv2
import json
from pathlib import Path

# Configuração de caminhos
ROOT_DIR = Path(__file__).resolve().parent
# Força o salvamento na pasta visao_computacional para o io_utils conseguir encontrar
CAMINHO_CALIBRACAO = ROOT_DIR / "visao_computacional" / "calibracao.json"

# Tamanho do objeto real que você usará SÓ UMA VEZ para calibrar
LARGURA_REAL_CM = 21.0  # Exemplo: 21cm para uma folha A4 na horizontal

# Variáveis globais para o mouse
pontos = []
frame_atual = None


def selecionar_pontos(event, x, y, flags, param):
    global pontos, frame_atual

    # Se clicou com o botão esquerdo
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(pontos) < 2:
            pontos.append((x, y))
            # Desenha uma bolinha vermelha onde clicou
            cv2.circle(frame_atual, (x, y), 5, (0, 0, 255), -1)
            cv2.imshow("Calibracao Manual", frame_atual)


print("\n--- MODO DE CALIBRAÇÃO MANUAL ---")
print("1. Coloque a câmera na sua posição FINAL E FIXA.")
print(f"2. Coloque o objeto de {LARGURA_REAL_CM} cm no chão/mesa.")
print("3. Pressione a barra de 'ESPAÇO' para tirar a foto.")

cap = cv2.VideoCapture(0)
while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Calibracao Manual", frame)

    # Se apertar espaço, tira a foto e avança
    if cv2.waitKey(1) & 0xFF == ord(' '):
        frame_atual = frame.copy()
        break

cap.release()
cv2.destroyAllWindows()

# Agora a parte do mouse
cv2.namedWindow("Calibracao Manual")
cv2.setMouseCallback("Calibracao Manual", selecionar_pontos)

print("\n--- FOTO TIRADA! ---")
print("1. Clique na PONTA ESQUERDA do objeto de referencia.")
print("2. Clique na PONTA DIREITA do objeto de referencia.")
print("3. Pressione 'ENTER' para salvar, ou 'Q' para sair.")

while True:
    cv2.imshow("Calibracao Manual", frame_atual)
    key = cv2.waitKey(1) & 0xFF

    if key == 13:  # Tecla ENTER
        if len(pontos) == 2:
            # Calcula a distância em pixels entre os dois cliques
            x1, _ = pontos[0]
            x2, _ = pontos[1]
            largura_pixels = abs(x2 - x1)

            pixels_por_cm = largura_pixels / LARGURA_REAL_CM

            # Salva no JSON
            dados = {"pixels_por_cm_fixo": pixels_por_cm}
            with open(CAMINHO_CALIBRACAO, 'w') as f:
                json.dump(dados, f)

            print(f"\n[SUCESSO] Calibração salva com sucesso!")
            print(f"Arquivo salvo em: {CAMINHO_CALIBRACAO}")
            print(f"Resultado: {pixels_por_cm:.2f} pixels equivalem a 1 cm.")
        else:
            print("Erro: Você precisa clicar em exatamente 2 pontos (esquerda e direita).")
        break

    elif key == ord('q'):
        break

cv2.destroyAllWindows()