import sys
from pathlib import Path
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from visao_computacional.core.io_utils import (
    PASTA_FOTOS_DASHBOARD,
    CAMINHO_CALIBRACAO,
)

st.set_page_config(page_title="GreenSense", page_icon="🌱", layout="wide")

def contar_imagens(pasta: Path) -> int:
    if not pasta.exists():
        return 0
    total = 0
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        total += len(list(pasta.glob(ext)))
    return total

def ultimo_arquivo_imagem(pasta: Path):
    if not pasta.exists():
        return None
    arquivos = []
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        arquivos.extend(pasta.glob(ext))
    if not arquivos:
        return None
    arquivos.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return arquivos[0]

st.title("🌱 GreenSense")
st.markdown(
    "Dashboard para monitoramento da grama, visualização em mapa e histórico de imagens/medidas."
)

st.markdown("---")

total_imgs = contar_imagens(Path(PASTA_FOTOS_DASHBOARD))
ultimo_img = ultimo_arquivo_imagem(Path(PASTA_FOTOS_DASHBOARD))
calibracao_ok = Path(CAMINHO_CALIBRACAO).exists()

m1, m2, m3 = st.columns(3)
m1.metric("🖼️ Imagens salvas", total_imgs)
m2.metric("⚙️ Calibração fixa", "Disponível" if calibracao_ok else "Não encontrada")
m3.metric("📁 Pasta dashboard", "OK" if Path(PASTA_FOTOS_DASHBOARD).exists() else "Pendente")

if ultimo_img:
    st.caption(f"Última imagem: **{ultimo_img.name}**")
else:
    st.caption("Ainda não há imagens salvas.")

st.markdown("---")

c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("📷 Monitoramento")
    st.write("Câmera ao vivo, detecção e captura de foto.")
    st.info("Abra no menu lateral: monitoramento")

with c2:
    st.subheader("🗺️ Mapa")
    st.write("Leitura de arquivos KMZ/KML.")
    st.info("Abra no menu lateral: mapa")

with c3:
    st.subheader("📊 Históricos")
    st.write("Imagens salvas e métricas de medidas.")
    st.info("Abra no menu lateral: Histórico de Imagens / Histórico de Medidas")

with st.expander("📘 Como usar", expanded=True):
    st.markdown(
        """
        1. Vá em **monitoramento**  
        2. Clique em **Iniciar**  
        3. Ajuste os parâmetros se necessário  
        4. Clique em **Salvar foto atual**  
        5. Veja em **Histórico de Imagens** e **Histórico de Medidas**
        """
    )