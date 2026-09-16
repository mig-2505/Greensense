import streamlit as st
import cv2
import sys
from pathlib import Path

# Garante que o Streamlit encontre a pasta raiz do projeto
ROOT_DIR = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT_DIR))

# Importa as funções do nosso núcleo (agora atualizado para YOLO)
from visao_computacional.core import measure, io_utils
from visao_computacional.core.vision import bgr_para_rgb


def main():
    st.set_page_config(page_title="Monitoramento - GreenSense", layout="wide")
    st.title("📷 GreenSense - Monitoramento (I.A. YOLOv8)")

    # Garante que as pastas para salvar fotos e o CSV existam
    io_utils.garantir_pastas()

    # CARREGA A CALIBRAÇÃO (Escala fixa gerada pelo mouse)
    pixels_por_cm_fixo = io_utils.carregar_pixels_por_cm()

    # Layout Principal: Coluna para o Vídeo e Coluna para os Dados
    col_video, col_metricas = st.columns([7, 3])

    with col_metricas:
        st.subheader("Métricas em Tempo Real")
        placeholder_status = st.empty()
        placeholder_escala = st.empty()
        placeholder_largura = st.empty()
        placeholder_altura = st.empty()

        if pixels_por_cm_fixo is None:
            st.error("⚠️ Calibração não encontrada! Rode o script gerar_calibracao_fixa.py")

    # BARRA LATERAL (Controles limpos)
    st.sidebar.title("Configurações")

    # Botões de controle da câmera
    col1, col2 = st.sidebar.columns(2)
    iniciar = col1.button("▶️ Iniciar")
    parar = col2.button("⏹️ Parar")

    st.sidebar.markdown("---")
    salvar = st.sidebar.button("📸 Salvar foto atual")

    # Gerencia o estado da câmera no Streamlit
    if "rodando" not in st.session_state:
        st.session_state.rodando = False

    if iniciar:
        st.session_state.rodando = True
    if parar:
        st.session_state.rodando = False

    # LOOP DA CÂMERA E PROCESSAMENTO DA I.A.
    with col_video:
        placeholder_video = st.empty()

        if st.session_state.rodando:
            cap = cv2.VideoCapture(0)  # 0 é a webcam padrão. Mude para 1 ou 2 se usar câmera externa

            while st.session_state.rodando:
                ret, frame = cap.read()
                if not ret:
                    st.error("Erro ao acessar a câmera. Verifique a conexão.")
                    break

                # A Mágica Acontece Aqui: Passa a imagem e a calibração para a I.A.
                frame_processado, _, medidas = measure.processar_frame_fixo(
                    frame_bgr=frame,
                    pixels_por_cm_fixo=pixels_por_cm_fixo
                )

                # Exibe o vídeo com os retângulos na tela do Dashboard
                frame_rgb = bgr_para_rgb(frame_processado)
                placeholder_video.image(frame_rgb, channels="RGB", use_container_width=True)

                # Atualiza as métricas de texto na direita
                placeholder_status.text(f"Status: {medidas.get('status_ref', 'N/A')}")

                if medidas.get('pixels_por_cm'):
                    placeholder_escala.text(f"Escala: {medidas['pixels_por_cm']:.2f} px/cm")
                else:
                    placeholder_escala.text("Escala: N/A")

                if medidas.get('largura_cm'):
                    placeholder_largura.text(f"Largura: {measure.formatar_medida(medidas['largura_cm'])}")
                else:
                    placeholder_largura.text("Largura: N/A")

                if medidas.get('altura_cm'):
                    placeholder_altura.text(f"Altura: {measure.formatar_medida(medidas['altura_cm'])}")
                else:
                    placeholder_altura.text("Altura: N/A")

                # Salva a foto e os dados no banco/histórico (Com a trava de segurança)
                if salvar:
                    if medidas.get('largura_cm') is not None:
                        caminho_foto = io_utils.salvar_foto(frame_processado, io_utils.PASTA_FOTOS_DASHBOARD)
                        io_utils.salvar_medida_dashboard(
                            arquivo_foto=caminho_foto,
                            modo="calibracao fixa",
                            largura_cm=medidas.get('largura_cm'),
                            altura_cm=medidas.get('altura_cm'),
                            pixels_por_cm=medidas.get('pixels_por_cm'),
                            status_ref=medidas.get('status_ref')
                        )
                        st.sidebar.success("✅ Foto e medidas salvas com sucesso!")
                    else:
                        st.sidebar.warning(
                            "⚠️ Nenhuma planta detectada! Aguarde o retângulo verde aparecer para salvar.")

                    salvar = False  # Reseta o botão para não salvar infinitamente

            cap.release()  # Libera a câmera quando apertar 'Parar'
        else:
            placeholder_video.info("Câmera desativada. Clique em '▶️ Iniciar' na barra lateral para começar a medição.")


if __name__ == "__main__":
    main()