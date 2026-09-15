import sys
from pathlib import Path
import time
import cv2
import streamlit as st

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from visao_computacional.core.measure import (
    processar_frame_referencia,
    processar_frame_fixo,
    HSV_REF_MIN_DEFAULT,
    HSV_REF_MAX_DEFAULT,
    HSV_GRAMA_MIN_DEFAULT,
    HSV_GRAMA_MAX_DEFAULT,
    AREA_MINIMA_DEFAULT,
    REFERENCIA_LARGURA_CM_DEFAULT,
)
from visao_computacional.core.io_utils import (
    garantir_pastas,
    carregar_pixels_por_cm,
    salvar_foto,
    salvar_medida_dashboard,
    PASTA_FOTOS_DASHBOARD,
)
from visao_computacional.core.vision import bgr_para_rgb

st.set_page_config(page_title="GreenSense - Monitoramento", layout="wide")
st.title("📷 GreenSense - Monitoramento")

garantir_pastas()

if "camera_ativa" not in st.session_state:
    st.session_state.camera_ativa = False
if "ultimo_frame_processado" not in st.session_state:
    st.session_state.ultimo_frame_processado = None
if "salvar_agora" not in st.session_state:
    st.session_state.salvar_agora = False
if "feedback_msg" not in st.session_state:
    st.session_state.feedback_msg = ""
if "ultimas_medidas" not in st.session_state:
    st.session_state.ultimas_medidas = {}

st.sidebar.header("Configurações")

modo = st.sidebar.radio("Modo de medição", ["Com referência", "Calibração fixa"], index=0)
area_minima = st.sidebar.slider("Área mínima (px)", 50, 5000, AREA_MINIMA_DEFAULT, 50)

st.sidebar.subheader("HSV Grama")
hmin_g = st.sidebar.slider("H min (grama)", 0, 179, HSV_GRAMA_MIN_DEFAULT[0])
smin_g = st.sidebar.slider("S min (grama)", 0, 255, HSV_GRAMA_MIN_DEFAULT[1])
vmin_g = st.sidebar.slider("V min (grama)", 0, 255, HSV_GRAMA_MIN_DEFAULT[2])
hmax_g = st.sidebar.slider("H max (grama)", 0, 179, HSV_GRAMA_MAX_DEFAULT[0])
smax_g = st.sidebar.slider("S max (grama)", 0, 255, HSV_GRAMA_MAX_DEFAULT[1])
vmax_g = st.sidebar.slider("V max (grama)", 0, 255, HSV_GRAMA_MAX_DEFAULT[2])

HSV_GRAMA_MIN = (hmin_g, smin_g, vmin_g)
HSV_GRAMA_MAX = (hmax_g, smax_g, vmax_g)

HSV_REF_MIN = HSV_REF_MIN_DEFAULT
HSV_REF_MAX = HSV_REF_MAX_DEFAULT
referencia_largura_cm = REFERENCIA_LARGURA_CM_DEFAULT

if modo == "Com referência":
    st.sidebar.subheader("Referência")
    referencia_largura_cm = st.sidebar.number_input(
        "Largura real da referência (cm)",
        min_value=0.1,
        max_value=200.0,
        value=float(REFERENCIA_LARGURA_CM_DEFAULT),
        step=0.1
    )

    st.sidebar.subheader("HSV Referência")
    hmin_r = st.sidebar.slider("H min (ref)", 0, 179, HSV_REF_MIN_DEFAULT[0])
    smin_r = st.sidebar.slider("S min (ref)", 0, 255, HSV_REF_MIN_DEFAULT[1])
    vmin_r = st.sidebar.slider("V min (ref)", 0, 255, HSV_REF_MIN_DEFAULT[2])
    hmax_r = st.sidebar.slider("H max (ref)", 0, 179, HSV_REF_MAX_DEFAULT[0])
    smax_r = st.sidebar.slider("S max (ref)", 0, 255, HSV_REF_MAX_DEFAULT[1])
    vmax_r = st.sidebar.slider("V max (ref)", 0, 255, HSV_REF_MAX_DEFAULT[2])

    HSV_REF_MIN = (hmin_r, smin_r, vmin_r)
    HSV_REF_MAX = (hmax_r, smax_r, vmax_r)

col_sb1, col_sb2 = st.sidebar.columns(2)
if col_sb1.button("▶️ Iniciar", use_container_width=True):
    st.session_state.camera_ativa = True

if col_sb2.button("⏹️ Parar", use_container_width=True):
    st.session_state.camera_ativa = False

if st.sidebar.button("📸 Salvar foto atual", use_container_width=True):
    st.session_state.salvar_agora = True

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Vídeo")
    frame_placeholder = st.empty()

with col_right:
    st.subheader("Métricas")
    m_status = st.empty()
    m_escala = st.empty()
    m_largura = st.empty()
    m_altura = st.empty()
    m_feedback = st.empty()

mask_col1, mask_col2 = st.columns(2)
mask_ref_placeholder = mask_col1.empty()
mask_grama_placeholder = mask_col2.empty()

if st.session_state.feedback_msg:
    if "✅" in st.session_state.feedback_msg:
        m_feedback.success(st.session_state.feedback_msg)
    elif "⚠️" in st.session_state.feedback_msg:
        m_feedback.warning(st.session_state.feedback_msg)
    else:
        m_feedback.error(st.session_state.feedback_msg)

if st.session_state.camera_ativa:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Não foi possível abrir a câmera.")
        st.session_state.camera_ativa = False
    else:
        while st.session_state.camera_ativa:
            ok, frame = cap.read()
            if not ok:
                st.warning("Falha ao capturar frame.")
                break

            if modo == "Com referência":
                frame_out, mascara_ref, mascara_grama, medidas = processar_frame_referencia(
                    frame_bgr=frame,
                    hsv_ref_min=HSV_REF_MIN,
                    hsv_ref_max=HSV_REF_MAX,
                    hsv_grama_min=HSV_GRAMA_MIN,
                    hsv_grama_max=HSV_GRAMA_MAX,
                    area_minima=area_minima,
                    referencia_largura_cm=referencia_largura_cm
                )
            else:
                px_cm = carregar_pixels_por_cm()
                if px_cm is None:
                    frame_out = frame.copy()
                    cv2.putText(frame_out, "Calibracao fixa nao encontrada", (20, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    mascara_ref = None
                    mascara_grama = None
                    medidas = {}
                else:
                    frame_out, mascara_grama, medidas = processar_frame_fixo(
                        frame_bgr=frame,
                        pixels_por_cm_fixo=px_cm,
                        hsv_grama_min=HSV_GRAMA_MIN,
                        hsv_grama_max=HSV_GRAMA_MAX,
                        area_minima=area_minima
                    )
                    mascara_ref = None

            st.session_state.ultimo_frame_processado = frame_out.copy()
            st.session_state.ultimas_medidas = medidas.copy() if isinstance(medidas, dict) else {}

            frame_placeholder.image(bgr_para_rgb(frame_out), channels="RGB", caption=f"Modo: {modo}")

            if mascara_ref is not None:
                mask_ref_placeholder.image(mascara_ref, caption="Máscara Referência", clamp=True)
            else:
                mask_ref_placeholder.info("Máscara Referência: não usada neste modo")

            if mascara_grama is not None:
                mask_grama_placeholder.image(mascara_grama, caption="Máscara Grama", clamp=True)
            else:
                mask_grama_placeholder.info("Máscara Grama indisponível")

            status_ref = medidas.get("status_ref", "-") if isinstance(medidas, dict) else "-"
            px = medidas.get("pixels_por_cm") if isinstance(medidas, dict) else None
            lg = medidas.get("largura_cm") if isinstance(medidas, dict) else None
            al = medidas.get("altura_cm") if isinstance(medidas, dict) else None

            m_status.write(f"Status: {status_ref}")
            m_escala.write(f"Escala: {px:.2f} px/cm" if px is not None else "Escala: -")
            m_largura.write(f"Largura: {lg:.1f} cm" if lg is not None else "Largura: -")
            m_altura.write(f"Altura: {al:.1f} cm" if al is not None else "Altura: -")

            if st.session_state.salvar_agora:
                try:
                    frame_salvar = st.session_state.ultimo_frame_processado
                    medidas_salvar = st.session_state.ultimas_medidas

                    if frame_salvar is None:
                        st.session_state.feedback_msg = "⚠️ Ainda não há frame para salvar."
                    else:
                        prefixo = "dashboard_referencia" if modo == "Com referência" else "dashboard_fixo"
                        caminho = salvar_foto(frame_salvar, PASTA_FOTOS_DASHBOARD, prefixo)

                        salvar_medida_dashboard(
                            arquivo_foto=Path(caminho).name,
                            modo=modo,
                            largura_cm=medidas_salvar.get("largura_cm"),
                            altura_cm=medidas_salvar.get("altura_cm"),
                            pixels_por_cm=medidas_salvar.get("pixels_por_cm"),
                            status_ref=medidas_salvar.get("status_ref"),
                        )

                        st.session_state.feedback_msg = "✅ Foto salva com sucesso."
                except Exception:
                    st.session_state.feedback_msg = "❌ Erro ao salvar foto."
                finally:
                    st.session_state.salvar_agora = False

                if "✅" in st.session_state.feedback_msg:
                    m_feedback.success(st.session_state.feedback_msg)
                elif "⚠️" in st.session_state.feedback_msg:
                    m_feedback.warning(st.session_state.feedback_msg)
                else:
                    m_feedback.error(st.session_state.feedback_msg)

            time.sleep(0.03)

        cap.release()
else:
    st.info("Clique em **Iniciar** para ligar a câmera.")
    if st.session_state.ultimo_frame_processado is not None:
        frame_placeholder.image(
            bgr_para_rgb(st.session_state.ultimo_frame_processado),
            channels="RGB",
            caption="Último frame processado"
        )