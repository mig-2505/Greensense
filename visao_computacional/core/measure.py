#regras de medição: referência e fixo
from .vision import (
    criar_mascara,
    encontrar_maior_contorno,
    desenhar_caixa,
    escrever_texto,
    bgr_para_hsv
)

# Defaults (você pode sobrescrever no app/script)
HSV_REF_MIN_DEFAULT = (156, 56, 127)
HSV_REF_MAX_DEFAULT = (179, 255, 189)

HSV_GRAMA_MIN_DEFAULT = (24, 41, 28)
HSV_GRAMA_MAX_DEFAULT = (91, 255, 255)

AREA_MINIMA_DEFAULT = 500
REFERENCIA_LARGURA_CM_DEFAULT = 21.0


def formatar_medida(cm):
    if cm is None:
        return "-"
    if cm >= 100:
        return f"{cm / 100:.2f} m"
    return f"{cm:.1f} cm"


def processar_frame_referencia(
    frame_bgr,
    hsv_ref_min=HSV_REF_MIN_DEFAULT,
    hsv_ref_max=HSV_REF_MAX_DEFAULT,
    hsv_grama_min=HSV_GRAMA_MIN_DEFAULT,
    hsv_grama_max=HSV_GRAMA_MAX_DEFAULT,
    area_minima=AREA_MINIMA_DEFAULT,
    referencia_largura_cm=REFERENCIA_LARGURA_CM_DEFAULT
):
    """
    Modo com objeto de referência na cena.
    Retorna:
      frame_out, mascara_ref, mascara_grama, medidas(dict)
    """
    frame_out = frame_bgr.copy()
    frame_hsv = bgr_para_hsv(frame_bgr)

    mascara_ref = criar_mascara(frame_hsv, hsv_ref_min, hsv_ref_max)
    mascara_grama = criar_mascara(frame_hsv, hsv_grama_min, hsv_grama_max)

    contorno_ref = encontrar_maior_contorno(mascara_ref, area_minima=area_minima)
    contorno_grama = encontrar_maior_contorno(mascara_grama, area_minima=area_minima)

    pixels_por_cm = None
    largura_cm = None
    altura_cm = None
    status_ref = "referencia nao encontrada"

    # Referência
    if contorno_ref is not None:
        xr, yr, wr, hr = desenhar_caixa(frame_out, contorno_ref, cor=(255, 0, 0), espessura=2)
        if referencia_largura_cm > 0:
            pixels_por_cm = wr / referencia_largura_cm
            status_ref = "referencia encontrada"

        escrever_texto(frame_out, "Referencia", (xr, yr - 10), cor=(255, 0, 0), escala=0.6)

    # Grama
    if contorno_grama is not None:
        xg, yg, wg, hg = desenhar_caixa(frame_out, contorno_grama, cor=(0, 255, 0), espessura=2)

        if pixels_por_cm and pixels_por_cm > 0:
            largura_cm = wg / pixels_por_cm
            altura_cm = hg / pixels_por_cm
            texto_largura = formatar_medida(largura_cm)
            texto_altura = formatar_medida(altura_cm)
        else:
            texto_largura = "sem referencia"
            texto_altura = "sem referencia"

        escrever_texto(frame_out, f"Largura: {texto_largura}", (xg, yg - 30), cor=(0, 255, 0), escala=0.6)
        escrever_texto(frame_out, f"Altura: {texto_altura}", (xg, yg - 10), cor=(0, 255, 0), escala=0.6)

    # Status
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

    return frame_out, mascara_ref, mascara_grama, medidas


def processar_frame_fixo(
    frame_bgr,
    pixels_por_cm_fixo,
    hsv_grama_min=HSV_GRAMA_MIN_DEFAULT,
    hsv_grama_max=HSV_GRAMA_MAX_DEFAULT,
    area_minima=AREA_MINIMA_DEFAULT
):
    """
    Modo com calibração fixa já salva.
    Retorna:
      frame_out, mascara_grama, medidas(dict)
    """
    frame_out = frame_bgr.copy()
    frame_hsv = bgr_para_hsv(frame_bgr)

    mascara_grama = criar_mascara(frame_hsv, hsv_grama_min, hsv_grama_max)
    contorno_grama = encontrar_maior_contorno(mascara_grama, area_minima=area_minima)

    largura_cm = None
    altura_cm = None

    if contorno_grama is not None:
        x, y, w, h = desenhar_caixa(frame_out, contorno_grama, cor=(0, 255, 0), espessura=2)

        if pixels_por_cm_fixo and pixels_por_cm_fixo > 0:
            largura_cm = w / pixels_por_cm_fixo
            altura_cm = h / pixels_por_cm_fixo

            escrever_texto(frame_out, f"Largura: {formatar_medida(largura_cm)}", (x, y - 30), cor=(0, 255, 0), escala=0.6)
            escrever_texto(frame_out, f"Altura: {formatar_medida(altura_cm)}", (x, y - 10), cor=(0, 255, 0), escala=0.6)

    escrever_texto(frame_out, f"Escala fixa: {pixels_por_cm_fixo:.1f} px/cm", (10, 30), cor=(255, 255, 255), escala=0.6)

    medidas = {
        "pixels_por_cm": pixels_por_cm_fixo,
        "largura_cm": largura_cm,
        "altura_cm": altura_cm,
        "status_ref": "calibracao fixa"
    }

    return frame_out, mascara_grama, medidas