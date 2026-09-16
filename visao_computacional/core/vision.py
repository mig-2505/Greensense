import cv2


def desenhar_caixa(frame_bgr, coord_xyxy, cor=(0, 255, 0), espessura=2):
    """
    Desenha bounding box a partir das coordenadas exatas enviadas pelo YOLO.
    coord_xyxy é uma tupla: (x1, y1, x2, y2)
    """
    x1, y1, x2, y2 = coord_xyxy
    cv2.rectangle(frame_bgr, (x1, y1), (x2, y2), cor, espessura)

    # Retorna o canto superior esquerdo (x1, y1) e as dimensões (w, h)
    w = x2 - x1
    h = y2 - y1
    return x1, y1, w, h


def escrever_texto(frame_bgr, texto, pos, cor=(255, 255, 255), escala=0.6, espessura=2):
    """Escreve um texto na imagem com uma fonte padrão."""
    cv2.putText(
        frame_bgr,
        texto,
        pos,
        cv2.FONT_HERSHEY_SIMPLEX,
        escala,
        cor,
        espessura
    )


def bgr_para_rgb(frame_bgr):
    """Converte o frame para RGB (necessário para exibição correta no Streamlit)."""
    return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)