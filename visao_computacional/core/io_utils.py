import os
import json
import csv
from pathlib import Path
from datetime import datetime
import cv2

# ==========================================
# CAMINHOS E DIRETÓRIOS
# ==========================================
# Resolve para a raiz do projeto (supondo que este arquivo esteja em visao_computacional/core)
ROOT_DIR = Path(__file__).resolve().parents[2]

# Pastas de saída
PASTA_FOTOS_DASHBOARD = ROOT_DIR / "dados" / "fotos_dashboard"
ARQUIVO_MEDIDAS_DASHBOARD = ROOT_DIR / "dados" / "medidas_dashboard.csv"

# O caminho EXATO do seu JSON de calibração
CAMINHO_CALIBRACAO = ROOT_DIR / "visao_computacional" / "calibracao.json"


# ==========================================
# FUNÇÕES DE SISTEMA
# ==========================================
def garantir_pastas():
    """Garante que as pastas de dados existam antes de salvar os arquivos."""
    PASTA_FOTOS_DASHBOARD.mkdir(parents=True, exist_ok=True)
    ARQUIVO_MEDIDAS_DASHBOARD.parent.mkdir(parents=True, exist_ok=True)


def carregar_pixels_por_cm():
    """Lê o arquivo de calibração JSON com a escala da referência fixa."""
    try:
        if CAMINHO_CALIBRACAO.exists():
            with open(CAMINHO_CALIBRACAO, "r") as f:
                dados = json.load(f)
                return dados.get("pixels_por_cm_fixo")
        else:
            print(f"[Aviso] Arquivo de calibração não encontrado em: {CAMINHO_CALIBRACAO}")
    except Exception as e:
        print(f"[Erro] Falha ao ler calibração: {e}")
    return None


def salvar_foto(frame_bgr, pasta_destino, prefixo="foto"):
    """Salva a imagem capturada e retorna APENAS O NOME do arquivo para o CSV."""
    agora = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    nome = f"{prefixo}_{agora}.png"
    caminho = Path(pasta_destino) / nome
    cv2.imwrite(str(caminho), frame_bgr)

    # Retorna apenas o nome da foto para cruzar corretamente com o histórico do dashboard
    return nome


def salvar_medida_dashboard(arquivo_foto, modo, largura_cm, altura_cm, pixels_por_cm, status_ref):
    """Salva os dados da medição atrelados à foto em um arquivo CSV."""
    existe = ARQUIVO_MEDIDAS_DASHBOARD.exists()

    with open(ARQUIVO_MEDIDAS_DASHBOARD, mode='a', newline='', encoding='utf-8') as csvfile:
        colunas = ["timestamp", "arquivo_foto", "modo", "largura_cm", "altura_cm", "pixels_por_cm", "status_ref"]
        writer = csv.DictWriter(csvfile, fieldnames=colunas)

        # Cria o cabeçalho se o arquivo estiver sendo criado pela primeira vez
        if not existe:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "arquivo_foto": arquivo_foto,
            "modo": modo,
            "largura_cm": f"{largura_cm:.2f}" if largura_cm else "",
            "altura_cm": f"{altura_cm:.2f}" if altura_cm else "",
            "pixels_por_cm": f"{pixels_por_cm:.2f}" if pixels_por_cm else "",
            "status_ref": status_ref or ""
        })