import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from visao_computacional.core.io_utils import ARQUIVO_MEDIDAS_DASHBOARD

st.set_page_config(page_title="GreenSense - Histórico de Medidas", layout="wide")
st.title("📏 GreenSense - Histórico de Medidas")
st.caption("Resumo das medidas salvas junto com as fotos do dashboard.")

csv_path = Path(ARQUIVO_MEDIDAS_DASHBOARD)

if not csv_path.exists():
    st.info("Ainda não existem medidas salvas. Tire fotos no monitoramento para gerar dados.")
    st.stop()

df = pd.read_csv(csv_path)

if df.empty:
    st.info("Arquivo de medidas está vazio.")
    st.stop()

# -------------------------------------------------
# Pré-processamento
# -------------------------------------------------
for col in ["largura_cm", "altura_cm", "pixels_por_cm"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# tenta converter timestamp
if "timestamp" in df.columns:
    df["timestamp_dt"] = pd.to_datetime(df["timestamp"], dayfirst=True, errors="coerce")
else:
    df["timestamp_dt"] = pd.NaT

# -------------------------------------------------
# Filtros
# -------------------------------------------------
modos = sorted(df["modo"].dropna().unique().tolist()) if "modo" in df.columns else []
modo_filtro = st.selectbox("Filtrar modo", ["Todos"] + modos)

df_filtrado = df.copy()
if modo_filtro != "Todos":
    df_filtrado = df_filtrado[df_filtrado["modo"] == modo_filtro]

if df_filtrado.empty:
    st.warning("Sem dados para o filtro selecionado.")
    st.stop()

# ordena cronologicamente para calcular comparação com foto anterior
df_filtrado = df_filtrado.sort_values("timestamp_dt", ascending=True).reset_index(drop=True)

total_registros = len(df_filtrado)
if total_registros <= 10:
    limite = total_registros
    st.caption(f"Quantidade de registros disponível: {limite}")
else:
    limite = st.slider(
        "Quantidade de registros",
        min_value=10,
        max_value=total_registros,
        value=min(200, total_registros),
        step=10
    )

df_view = df_filtrado.tail(limite).copy().reset_index(drop=True)

# -------------------------------------------------
# Limiares de alerta
# -------------------------------------------------
st.subheader("⚙️ Sensibilidade dos alertas por foto")
a1, a2, a3 = st.columns(3)
queda_largura_pct = a1.slider("Queda largura (%)", 5, 80, 20, 1)
queda_altura_pct = a2.slider("Queda altura (%)", 5, 80, 20, 1)
instabilidade_px_pct = a3.slider("Variação escala px/cm (%)", 1, 50, 10, 1)

# -------------------------------------------------
# Alertas por foto (comparando com foto anterior)
# -------------------------------------------------
df_view["largura_ant"] = df_view["largura_cm"].shift(1)
df_view["altura_ant"] = df_view["altura_cm"].shift(1)
df_view["px_ant"] = df_view["pixels_por_cm"].shift(1)

def calc_queda_pct(atual, anterior):
    if pd.isna(atual) or pd.isna(anterior) or anterior <= 0:
        return np.nan
    return ((anterior - atual) / anterior) * 100

def calc_var_pct(atual, anterior):
    if pd.isna(atual) or pd.isna(anterior) or anterior == 0:
        return np.nan
    return abs((atual - anterior) / anterior) * 100

df_view["queda_largura_pct"] = df_view.apply(
    lambda r: calc_queda_pct(r["largura_cm"], r["largura_ant"]), axis=1
)
df_view["queda_altura_pct"] = df_view.apply(
    lambda r: calc_queda_pct(r["altura_cm"], r["altura_ant"]), axis=1
)
df_view["var_px_pct"] = df_view.apply(
    lambda r: calc_var_pct(r["pixels_por_cm"], r["px_ant"]), axis=1
)

def classificar_alerta(row):
    motivos = []
    nivel = "🟢 OK"

    ql = row["queda_largura_pct"]
    qa = row["queda_altura_pct"]
    vp = row["var_px_pct"]

    critico = False
    atencao = False

    if pd.notna(ql):
        if ql >= queda_largura_pct:
            critico = True
            motivos.append(f"queda largura {ql:.1f}%")
        elif ql >= (queda_largura_pct * 0.6):
            atencao = True
            motivos.append(f"queda largura moderada {ql:.1f}%")

    if pd.notna(qa):
        if qa >= queda_altura_pct:
            critico = True
            motivos.append(f"queda altura {qa:.1f}%")
        elif qa >= (queda_altura_pct * 0.6):
            atencao = True
            motivos.append(f"queda altura moderada {qa:.1f}%")

    if pd.notna(vp):
        if vp >= instabilidade_px_pct:
            atencao = True
            motivos.append(f"escala variou {vp:.1f}%")

    if critico:
        nivel = "🔴 Crítico"
    elif atencao:
        nivel = "🟠 Atenção"

    detalhe = " | ".join(motivos) if motivos else "sem alterações relevantes"
    return pd.Series([nivel, detalhe])

df_view[["alerta", "detalhe_alerta"]] = df_view.apply(classificar_alerta, axis=1)

# -------------------------------------------------
# KPIs gerais
# -------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    "Média Largura (cm)",
    f"{df_view['largura_cm'].mean():.2f}" if df_view["largura_cm"].notna().any() else "-"
)
c2.metric(
    "Média Altura (cm)",
    f"{df_view['altura_cm'].mean():.2f}" if df_view["altura_cm"].notna().any() else "-"
)
c3.metric("Fotos Críticas", int((df_view["alerta"] == "🔴 Crítico").sum()))
c4.metric("Fotos Atenção", int((df_view["alerta"] == "🟠 Atenção").sum()))

st.markdown("---")

# -------------------------------------------------
# Lista de alertas por foto
# -------------------------------------------------
st.subheader("🚨 Alertas por Foto")

df_alertas = df_view.copy()

# mais recente primeiro para leitura humana
df_alertas = df_alertas.sort_values("timestamp_dt", ascending=False)

# tabela amigável
cols_show = [
    "timestamp",
    "arquivo_foto",
    "modo",
    "largura_cm",
    "altura_cm",
    "pixels_por_cm",
    "alerta",
    "detalhe_alerta",
]
cols_show = [c for c in cols_show if c in df_alertas.columns]

st.dataframe(df_alertas[cols_show], use_container_width=True)

# cards só com críticos
criticos = df_alertas[df_alertas["alerta"] == "🔴 Crítico"]
if not criticos.empty:
    st.error(f"Foram encontrados {len(criticos)} registros críticos.")
else:
    st.success("Nenhum registro crítico no recorte atual.")

st.markdown("---")

# -------------------------------------------------
# Gráficos
# -------------------------------------------------
g1, g2 = st.columns(2)

with g1:
    st.subheader("Evolução da Largura")
    plot_larg = df_view[["timestamp_dt", "largura_cm"]].dropna().set_index("timestamp_dt")
    if not plot_larg.empty:
        st.line_chart(plot_larg)
    else:
        st.info("Sem dados de largura.")

with g2:
    st.subheader("Evolução da Altura")
    plot_alt = df_view[["timestamp_dt", "altura_cm"]].dropna().set_index("timestamp_dt")
    if not plot_alt.empty:
        st.line_chart(plot_alt)
    else:
        st.info("Sem dados de altura.")

st.markdown("---")
st.subheader("Tabela Completa de Medições")
st.dataframe(df_alertas, use_container_width=True)