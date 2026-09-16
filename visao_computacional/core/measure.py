from pathlib import Path
from ultralytics import YOLO
from .vision import desenhar_caixa, escrever_texto

# ==========================================
# 1. CARREGAMENTO ROBUSTO DO MODELO YOLO
# ==========================================
BASE_DIR = Path(__file__).resolve().parents[1]
CAMINHO_MODELO = BASE_DIR / "modelos" / "best.pt"

print(f"\n[SISTEMA] Tentando carregar modelo YOLO em: {CAMINHO_MODELO}")

modelo_ia = None
try:
    if not CAMINHO_MODELO.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {CAMINHO_MODELO}")

    modelo_ia = YOLO(str(CAMINHO_MODELO))
    print("[SISTEMA] Modelo YOLO carregado com sucesso!\n")

except Exception as e:
    print(f"\n[ERRO CRÍTICO] Falha ao carregar o modelo YOLO. Motivo: {e}")

# Configurações padrão
REFERENCIA_LARGURA_CM_DEFAULT = 21.0


# ==========================================
# 2. FUNÇÕES UTILITÁRIAS
# ==========================================
def formatar_medida(cm):
    if cm is None:
        return "-"
    if cm >= 100:
        return f"{cm / 100:.2f} m"
    return f"{cm:.1f} cm"


# ==========================================
# 3. LÓGICA DE MEDIÇÃO (COM REFERÊNCIA NA CENA)
# ==========================================
def processar_frame_referencia(frame_bgr, referencia_largura_cm=REFERENCIA_LARGURA_CM_DEFAULT):
    frame_out = frame_bgr.copy()

    if modelo_ia is None:
        escrever_texto(frame_out, "ERRO: Modelo IA nao carregado!", (20, 50), cor=(0, 0, 255), escala=0.8)
        return frame_out, None, None, {"status_ref": "erro modelo"}

    # Inferência com 50% de confiança
    resultados = modelo_ia.predict(frame_bgr, conf=0.5, verbose=False)

    coord_ref = None
    coord_planta = None

    for caixa in resultados[0].boxes:
        classe_id = int(caixa.cls[0].item())
        nome_classe = modelo_ia.names[classe_id].lower()
        x1, y1, x2, y2 = caixa.xyxy[0].cpu().numpy().astype(int)

        # PROCURA PELOS NOMES ATUALIZADOS DO SEU NOVO DATASET
        if nome_classe == 'planta':
            coord_planta = (x1, y1, x2, y2)
        elif nome_classe == 'referencia':
            coord_ref = (x1, y1, x2, y2)

    pixels_por_cm = None
    largura_cm = None
    altura_cm = None
    status_ref = "referencia nao encontrada"

    if coord_ref is not None:
        xr, yr, wr, hr = desenhar_caixa(frame_out, coord_ref, cor=(255, 0, 0), espessura=2)
        if referencia_largura_cm > 0:
            pixels_por_cm = wr / referencia_largura_cm
            status_ref = "referencia encontrada"
        escrever_texto(frame_out, "Referencia", (xr, yr - 10), cor=(255, 0, 0), escala=0.6)

    if coord_planta is not None:
        xg, yg, wg, hg = desenhar_caixa(frame_out, coord_planta, cor=(0, 255, 0), espessura=2)
        if pixels_por_cm and pixels_por_cm > 0:
            largura_cm = wg / pixels_por_cm
            altura_cm = hg / pixels_por_cm
            texto_largura = formatar_medida(largura_cm)
            texto_altura = formatar_medida(altura_cm)
        else:
            texto_largura = "sem escala"
            texto_altura = "sem escala"
        escrever_texto(frame_out, f"Largura: {texto_largura}", (xg, yg - 30), cor=(0, 255, 0), escala=0.6)
        escrever_texto(frame_out, f"Altura: {texto_altura}", (xg, yg - 10), cor=(0, 255, 0), escala=0.6)

    if pixels_por_cm is None:
        escrever_texto(frame_out, "REFERENCIA NAO ENCONTRADA", (10, 30), cor=(0, 0, 255), escala=0.7)
    else:
        escrever_texto(frame_out, f"Escala: {pixels_por_cm:.1f} px/cm", (10, 30), cor=(255, 255, 255), escala=0.6)

    medidas = {
        "pixels_por_cm": pixels_por_cm,
        "largura_cm": largura_cm,
        "altura_cm": altura_cm,
        "status_ref": status_ref
    }
    return frame_out, None, None, medidas


# ==========================================
# 4. LÓGICA DE MEDIÇÃO (CALIBRAÇÃO FIXA)
# ==========================================
def processar_frame_fixo(frame_bgr, pixels_por_cm_fixo):
    frame_out = frame_bgr.copy()

    if modelo_ia is None:
        escrever_texto(frame_out, "ERRO: Modelo IA nao carregado!", (20, 50), cor=(0, 0, 255), escala=0.8)
        return frame_out, None, {"status_ref": "erro modelo"}

    # Inferência com 50% de confiança
    resultados = modelo_ia.predict(frame_bgr, conf=0.5, verbose=False)
    coord_planta = None

    for caixa in resultados[0].boxes:
        classe_id = int(caixa.cls[0].item())
        nome_classe = modelo_ia.names[classe_id].lower()

        # BUSCA PELA PLANTA
        if nome_classe == 'planta':
            coord_planta = tuple(caixa.xyxy[0].cpu().numpy().astype(int))
            break

    largura_cm = None
    altura_cm = None

    if coord_planta is not None:
        x, y, w, h = desenhar_caixa(frame_out, coord_planta, cor=(0, 255, 0), espessura=2)

        if pixels_por_cm_fixo and pixels_por_cm_fixo > 0:
            largura_cm = w / pixels_por_cm_fixo
            altura_cm = h / pixels_por_cm_fixo

            escrever_texto(frame_out, f"Largura: {formatar_medida(largura_cm)}", (x, y - 30), cor=(0, 255, 0),
                           escala=0.6)
            escrever_texto(frame_out, f"Altura: {formatar_medida(altura_cm)}", (x, y - 10), cor=(0, 255, 0), escala=0.6)

    escrever_texto(frame_out, f"Escala fixa: {pixels_por_cm_fixo:.1f} px/cm", (10, 30), cor=(255, 255, 255), escala=0.6)

    medidas = {
        "pixels_por_cm": pixels_por_cm_fixo,
        "largura_cm": largura_cm,
        "altura_cm": altura_cm,
        "status_ref": "calibracao fixa"
    }
    return frame_out, None, medidas