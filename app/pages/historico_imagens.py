import sys
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from visao_computacional.core.io_utils import (
    PASTA_FOTOS_DASHBOARD,
    ARQUIVO_MEDIDAS_DASHBOARD,
)

st.set_page_config(page_title="GreenSense - Histórico de Imagens", layout="wide")
st.title("🖼️ GreenSense - Histórico de Imagens")
st.caption("Exibe imagens salvas pelo dashboard com status de alerta por foto.")

pasta = Path(PASTA_FOTOS_DASHBOARD)
pasta.mkdir(parents=True, exist_ok=True)

# ---------------------------
# Controles
# ---------------------------
qtd = st.slider("Quantidade máxima de imagens", 10, 500, 60, 10)
ordem = st.radio("Ordem", ["Mais recentes primeiro", "Mais antigas primeiro"], index=0)

st.subheader("⚙️ Sensibilidade dos alertas")
a1, a2, a3 = st.columns(3)
queda_largura_pct = a1.slider("Queda largura (%)", 5, 80, 20, 1, key="img_alert_ql")
queda_altura_pct = a2.slider("Queda altura (%)", 5, 80, 20, 1, key="img_alert_qa")
instabilidade_px_pct = a3.slider("Variação escala px/cm (%)", 1, 50, 10, 1, key="img_alert_px")

# ---------------------------
# Coleta imagens
# ---------------------------
arquivos = []
for ext in ("*.png", "*.jpg", "*.jpeg"):
    arquivos.extend(pasta.glob(ext))

if not arquivos:
    st.info(f"Nenhuma imagem encontrada em: {pasta}")
    st.stop()

reverse_sort = ordem == "Mais recentes primeiro"
arquivos = sorted(arquivos, key=lambda f: f.stat().st_mtime, reverse=reverse_sort)
arquivos = arquivos[:qtd]

dados = []
for f in arquivos:
    dt_local = datetime.fromtimestamp(f.stat().st_mtime)
    dados.append({
        "arquivo": f.name,
        "modificado_em": dt_local.strftime("%d/%m/%Y %H:%M:%S"),
        "timestamp_dt": dt_local,
        "caminho": str(f.resolve()),
    })

df_imgs = pd.DataFrame(dados)

# ---------------------------
# Carrega medidas e calcula alerta por foto
# ---------------------------
alerta_por_arquivo = {}

csv_path = Path(ARQUIVO_MEDIDAS_DASHBOARD)
if csv_path.exists():
    df_med = pd.read_csv(csv_path)

    if not df_med.empty and "arquivo_foto" in df_med.columns:
        for col in ["largura_cm", "altura_cm", "pixels_por_cm"]:
            if col in df_med.columns:
                df_med[col] = pd.to_numeric(df_med[col], errors="coerce")

        if "timestamp" in df_med.columns:
            df_med["timestamp_dt"] = pd.to_datetime(df_med["timestamp"], dayfirst=True, errors="coerce")
        else:
            df_med["timestamp_dt"] = pd.NaT

        # Ordena cronologicamente para comparar com anterior
        df_med = df_med.sort_values("timestamp_dt", ascending=True).reset_index(drop=True)

        df_med["largura_ant"] = df_med["largura_cm"].shift(1)
        df_med["altura_ant"] = df_med["altura_cm"].shift(1)
        df_med["px_ant"] = df_med["pixels_por_cm"].shift(1)

        def calc_queda_pct(atual, anterior):
            if pd.isna(atual) or pd.isna(anterior) or anterior <= 0:
                return np.nan
            return ((anterior - atual) / anterior) * 100

        def calc_var_pct(atual, anterior):
            if pd.isna(atual) or pd.isna(anterior) or anterior == 0:
                return np.nan
            return abs((atual - anterior) / anterior) * 100

        df_med["queda_largura_pct"] = df_med.apply(
            lambda r: calc_queda_pct(r.get("largura_cm"), r.get("largura_ant")), axis=1
        )
        df_med["queda_altura_pct"] = df_med.apply(
            lambda r: calc_queda_pct(r.get("altura_cm"), r.get("altura_ant")), axis=1
        )
        df_med["var_px_pct"] = df_med.apply(
            lambda r: calc_var_pct(r.get("pixels_por_cm"), r.get("px_ant")), axis=1
        )

        def classificar(row):
            ql = row["queda_largura_pct"]
            qa = row["queda_altura_pct"]
            vp = row["var_px_pct"]

            critico = False
            atencao = False
            motivos = []

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

            if pd.notna(vp) and vp >= instabilidade_px_pct:
                atencao = True
                motivos.append(f"escala variou {vp:.1f}%")

            if critico:
                nivel = "🔴 Crítico"
            elif atencao:
                nivel = "🟠 Atenção"
            else:
                nivel = "🟢 OK"

            detalhe = " | ".join(motivos) if motivos else "sem alterações relevantes"
            return pd.Series([nivel, detalhe])

        df_med[["alerta", "detalhe_alerta"]] = df_med.apply(classificar, axis=1)

        # Se houver arquivo repetido, mantém o registro mais recente
        df_med = df_med.sort_values("timestamp_dt", ascending=True)
        ultimos = df_med.dropna(subset=["arquivo_foto"]).drop_duplicates(subset=["arquivo_foto"], keep="last")

        for _, r in ultimos.iterrows():
            alerta_por_arquivo[str(r["arquivo_foto"])] = {
                "alerta": r.get("alerta", "🟢 OK"),
                "detalhe": r.get("detalhe_alerta", "sem alterações relevantes")
            }

# Mapeia alerta nas imagens
df_imgs["alerta"] = df_imgs["arquivo"].map(
    lambda nome: alerta_por_arquivo.get(nome, {}).get("alerta", "⚪ Sem dados")
)
df_imgs["detalhe_alerta"] = df_imgs["arquivo"].map(
    lambda nome: alerta_por_arquivo.get(nome, {}).get("detalhe", "sem registro no CSV de medidas")
)

# ---------------------------
# Tabela
# ---------------------------
st.write(f"Total exibido: **{len(df_imgs)}**")
st.dataframe(
    df_imgs[["arquivo", "modificado_em", "alerta", "detalhe_alerta", "caminho"]],
    use_container_width=True
)

st.markdown("---")
st.subheader("Pré-visualização")

# Resumo rápido
c1, c2, c3, c4 = st.columns(4)
c1.metric("🔴 Crítico", int((df_imgs["alerta"] == "🔴 Crítico").sum()))
c2.metric("🟠 Atenção", int((df_imgs["alerta"] == "🟠 Atenção").sum()))
c3.metric("🟢 OK", int((df_imgs["alerta"] == "🟢 OK").sum()))
c4.metric("⚪ Sem dados", int((df_imgs["alerta"] == "⚪ Sem dados").sum()))

# Galeria
cols = st.columns(3)
for i, row in df_imgs.iterrows():
    col = cols[i % 3]
    try:
        img = Image.open(row["caminho"])
        col.image(img, caption=f"{row['arquivo']} • {row['alerta']}", use_container_width=True)

        if row["alerta"] == "🔴 Crítico":
            col.error(row["detalhe_alerta"])
        elif row["alerta"] == "🟠 Atenção":
            col.warning(row["detalhe_alerta"])
        elif row["alerta"] == "🟢 OK":
            col.success(row["detalhe_alerta"])
        else:
            col.info(row["detalhe_alerta"])
    except Exception:
        col.warning(f"Não foi possível abrir: {row['arquivo']}")