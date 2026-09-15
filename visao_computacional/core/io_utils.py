import json
import csv
from pathlib import Path
from datetime import datetime
import cv2

# Raiz do pacote visao_computacional/
BASE_DIR = Path(__file__).resolve().parents[1]

CAMINHO_CALIBRACAO = BASE_DIR / "calibracao.json"

PASTA_FOTOS_MEDICOES = BASE_DIR / "dados" / "fotos_medicoes"
PASTA_FOTOS_MEDICOES_FIXO = BASE_DIR / "dados" / "fotos_medicoes_fixo"
PASTA_FOTOS_DASHBOARD = BASE_DIR / "dados" / "fotos_dashboard"

ARQUIVO_MEDIDAS_DASHBOARD = BASE_DIR / "dados" / "medidas_dashboard.csv"


def garantir_pastas():
    PASTA_FOTOS_MEDICOES.mkdir(parents=True, exist_ok=True)
    PASTA_FOTOS_MEDICOES_FIXO.mkdir(parents=True, exist_ok=True)
    PASTA_FOTOS_DASHBOARD.mkdir(parents=True, exist_ok=True)
    ARQUIVO_MEDIDAS_DASHBOARD.parent.mkdir(parents=True, exist_ok=True)


def carregar_pixels_por_cm(caminho_calibracao=CAMINHO_CALIBRACAO):
    caminho = Path(caminho_calibracao)
    if not caminho.exists():
        return None

    try:
        with caminho.open("r", encoding="utf-8") as f:
            dados = json.load(f)
        valor = dados.get("pixels_por_cm", None)
        return float(valor) if valor is not None else None
    except Exception:
        return None


def salvar_calibracao_pixels_por_cm(pixels_por_cm, caminho_calibracao=CAMINHO_CALIBRACAO):
    caminho = Path(caminho_calibracao)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with caminho.open("w", encoding="utf-8") as f:
        json.dump({"pixels_por_cm": float(pixels_por_cm)}, f, ensure_ascii=False, indent=2)


def salvar_foto(frame_bgr, pasta_destino, prefixo="medicao"):
    """
    Salva imagem de forma robusta no Windows:
    usa cv2.imencode + write_bytes para evitar falhas com unicode em path.
    """
    pasta = Path(pasta_destino)
    pasta.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    nome_arquivo = f"{prefixo}_{timestamp}.png"
    caminho = pasta / nome_arquivo

    ok, buf = cv2.imencode(".png", frame_bgr)
    if not ok:
        raise RuntimeError("Falha no cv2.imencode('.png', frame).")

    caminho.write_bytes(buf.tobytes())
    return str(caminho.resolve())


def salvar_medida_dashboard(
    arquivo_foto: str,
    modo: str,
    largura_cm,
    altura_cm,
    pixels_por_cm,
    status_ref
):
    novo_arquivo = not ARQUIVO_MEDIDAS_DASHBOARD.exists()

    with ARQUIVO_MEDIDAS_DASHBOARD.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if novo_arquivo:
            writer.writerow([
                "timestamp",
                "arquivo_foto",
                "modo",
                "largura_cm",
                "altura_cm",
                "pixels_por_cm",
                "status_ref",
            ])

        writer.writerow([
            datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            arquivo_foto,
            modo,
            largura_cm if largura_cm is not None else "",
            altura_cm if altura_cm is not None else "",
            pixels_por_cm if pixels_por_cm is not None else "",
            status_ref if status_ref is not None else "",
        ])