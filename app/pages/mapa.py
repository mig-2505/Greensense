import streamlit as st
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="GreenSense - Mapa", layout="wide")
st.title("🗺️ GreenSense - Mapa (KMZ/KML)")


# =========================================================
# 1) Descobrir pasta de arquivos (aceita MKZ ou KMZ)
# =========================================================
ROOT_DIR = Path(__file__).resolve().parents[2]
DIR_MKZ = ROOT_DIR / "MKZ"
DIR_KMZ = ROOT_DIR / "KMZ"

if DIR_MKZ.exists():
    MAP_DIR = DIR_MKZ
elif DIR_KMZ.exists():
    MAP_DIR = DIR_KMZ
else:
    st.error(
        "Pasta de mapas não encontrada.\n\n"
        f"Tente criar uma destas pastas na raiz do projeto:\n"
        f"- {DIR_MKZ}\n"
        f"- {DIR_KMZ}"
    )
    st.stop()

# =========================================================
# 2) Funções utilitárias
# =========================================================
def extrair_kml_de_arquivo(caminho: Path) -> bytes:
    """
    Aceita:
    - KMZ real (zip com .kml dentro)
    - KML puro renomeado para .kmz
    - KML normal (.kml)
    """
    sufixo = caminho.suffix.lower()

    # Caso .kml direto
    if sufixo == ".kml":
        raw = caminho.read_bytes()
        if b"<kml" in raw[:5000].lower() or b"http://www.opengis.net/kml/2.2" in raw:
            return raw
        raise ValueError(f"{caminho.name}: arquivo .kml inválido")

    # Caso .kmz: geralmente zip
    if sufixo == ".kmz":
        if zipfile.is_zipfile(caminho):
            with zipfile.ZipFile(caminho, "r") as zf:
                kml_files = [n for n in zf.namelist() if n.lower().endswith(".kml")]
                if not kml_files:
                    raise ValueError(f"{caminho.name}: KMZ sem .kml interno")
                return zf.read(kml_files[0])

        # Fallback: às vezes é KML com extensão errada
        raw = caminho.read_bytes()
        if b"<kml" in raw[:5000].lower() or b"http://www.opengis.net/kml/2.2" in raw:
            return raw

        raise ValueError(f"{caminho.name}: não é zip KMZ nem KML válido")

    raise ValueError(f"{caminho.name}: extensão não suportada ({sufixo})")


def parse_kml_coordinates(kml_bytes: bytes):
    """
    Extrai coordenadas de tags <coordinates> no formato KML:
      lon,lat,alt lon,lat,alt ...
    Retorna lista de dicts: [{"lat": ..., "lon": ...}, ...]
    """
    try:
        root = ET.fromstring(kml_bytes)
    except Exception as e:
        raise ValueError(f"Falha ao ler XML/KML: {e}")

    ns = {"kml": "http://www.opengis.net/kml/2.2"}
    coords_nodes = root.findall(".//kml:coordinates", ns)

    pontos = []
    for node in coords_nodes:
        if not node.text:
            continue

        raw = node.text.strip().replace("\n", " ")
        pares = raw.split()

        for p in pares:
            partes = p.split(",")
            if len(partes) < 2:
                continue

            try:
                lon = float(partes[0])
                lat = float(partes[1])
                pontos.append({"lat": lat, "lon": lon})
            except ValueError:
                continue

    return pontos


# =========================================================
# 3) Buscar arquivos disponíveis
# =========================================================
arquivos = sorted(list(MAP_DIR.glob("*.kmz")) + list(MAP_DIR.glob("*.kml")))

if not arquivos:
    st.warning(f"Nenhum arquivo .kmz/.kml encontrado em: {MAP_DIR}")
    st.stop()

nomes_arquivos = [a.name for a in arquivos]

selecionados = st.multiselect(
    "Selecione os arquivos para exibir no mapa:",
    options=nomes_arquivos,
    default=nomes_arquivos
)

if not selecionados:
    st.info("Selecione ao menos um arquivo.")
    st.stop()


# =========================================================
# 4) Processar arquivos escolhidos
# =========================================================
todos_pontos = []
erros = []

for nome in selecionados:
    caminho = MAP_DIR / nome
    try:
        kml_bytes = extrair_kml_de_arquivo(caminho)
        pontos = parse_kml_coordinates(kml_bytes)

        if not pontos:
            erros.append(f"{nome}: sem coordenadas encontradas no KML.")
            continue

        for pt in pontos:
            pt["arquivo"] = nome

        todos_pontos.extend(pontos)

    except Exception as e:
        erros.append(f"{nome}: {e}")

# Mostrar erros (se houver)
for e in erros:
    st.error(f"Erro em {e}")

if not todos_pontos:
    st.warning("Nenhuma coordenada válida para mostrar.")
    st.stop()

df = pd.DataFrame(todos_pontos).dropna(subset=["lat", "lon"])

if df.empty:
    st.warning("Coordenadas vazias após limpeza.")
    st.stop()


# =========================================================
# 5) Exibir mapa e tabelas
# =========================================================
st.success(f"Total de coordenadas carregadas: {len(df)}")
st.map(df[["lat", "lon"]])

col1, col2 = st.columns(2)

with col1:
    with st.expander("Tabela de coordenadas"):
        st.dataframe(df, use_container_width=True)

with col2:
    with st.expander("Resumo por arquivo"):
        resumo = df.groupby("arquivo").size().reset_index(name="qtd_pontos")
        st.dataframe(resumo, use_container_width=True)

