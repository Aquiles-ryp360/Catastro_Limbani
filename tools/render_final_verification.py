"""
================================================================================
SCRIPT: render_final_verification.py
PROPÓSITO: Genera imágenes de superposición y control visual en alta resolución.
================================================================================
Superpone las entidades vectoriales del plano DXF directamente sobre la ortofoto
satelital georreferenciada (ortofoto_limbani.jpg) usando OpenCV y genera:
1. Superposición completa global
2. Modelo CAD sobre fondo negro
3. 4 zooms detallados por sectores estratégicos (Norte, Centro, Estadio, Sur)
"""

import os, cv2, numpy as np, ezdxf

tools_dir = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(os.path.join(tools_dir, ".."))
out_dir = os.path.join(work_dir, "verificacion_final")
os.makedirs(out_dir, exist_ok=True)

img_path = os.path.join(work_dir, "ortofoto_limbani.jpg")
dxf_path = os.path.join(work_dir, "catastro_limbani.dxf")

# Georreferenciación ortofoto
X_NW, Y_NW = 424744.74, 8437057.14
X_SE, Y_SE = 426234.72, 8434410.45

def main():
    if not os.path.exists(img_path):
        print(f"Ortofoto no encontrada en: {img_path}")
        return

    print("Cargando ortofoto satelital y plano DXF...")
    img = cv2.imread(img_path)
    h, w, _ = img.shape
    DX = (X_SE - X_NW) / w
    DY = (Y_NW - Y_SE) / h

    def utm2px(e, n):
        return int(round((e - X_NW) / DX)), int(round((Y_NW - n) / DY))

    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    color_table = {
        '01_RIOS_Y_CUENCAS': (240, 180, 0),         # Azure blue
        '02_CALLES_Y_VIAS': (255, 255, 255),        # White
        '03_MANZANAS_ROTULOS': (255, 0, 255),       # Magenta
        '04_LOTES_PREDIALES': (180, 180, 180),      # Light grey
        '05_HUELLAS_CASAS_USUARIO': (0, 140, 255),  # Orange (BGR)
        '06_HUELLAS_CASAS_COMPLEMENTO': (255, 220, 0), # Cyan (BGR)
        '07_EQUIPAMIENTOS': (0, 255, 0),            # Green
        '08_TOPONIMIA_ROTULOS': (200, 255, 255),    # Light Yellow
        '09_MEMBRETE_DATOS': (255, 255, 255),
    }

    overlay = img.copy()

    # Canvas CAD oscuro
    cad_w, cad_h = 2400, 3600
    CAD_X_MIN, CAD_X_MAX = 425200.0, 425750.0
    CAD_Y_MIN, CAD_Y_MAX = 8434700.0, 8436700.0
    cad_dx = (CAD_X_MAX - CAD_X_MIN) / cad_w
    cad_dy = (CAD_Y_MAX - CAD_Y_MIN) / cad_h

    def utm2cad(e, n):
        return int(round((e - CAD_X_MIN) / cad_dx)), int(round((CAD_Y_MAX - n) / cad_dy))

    cad_canvas = np.zeros((cad_h, cad_w, 3), dtype=np.uint8)
    cad_canvas[:] = (25, 25, 25)

    for e in msp:
        layer = e.dxf.layer
        c = color_table.get(layer, (200, 200, 200))
        thick = 2
        if 'RIOS' in layer: thick = 3
        elif 'LOTES' in layer: thick = 1

        if e.dxftype() == 'LWPOLYLINE':
            pts_geo = [utm2px(p[0], p[1]) for p in e.get_points()]
            pts_cad = [utm2cad(p[0], p[1]) for p in e.get_points()]
            poly_geo = np.array(pts_geo, np.int32)
            poly_cad = np.array(pts_cad, np.int32)
            
            cv2.polylines(overlay, [poly_geo], e.closed, c, thick)
            cv2.polylines(cad_canvas, [poly_cad], e.closed, c, thick)
            
            if layer == '05_HUELLAS_CASAS_USUARIO':
                cv2.fillPoly(cad_canvas, [poly_cad], (0, 70, 140))
                cv2.polylines(cad_canvas, [poly_cad], e.closed, (0, 140, 255), 2)
            elif layer == '06_HUELLAS_CASAS_COMPLEMENTO':
                cv2.fillPoly(cad_canvas, [poly_cad], (120, 100, 0))
                cv2.polylines(cad_canvas, [poly_cad], e.closed, (255, 220, 0), 2)

        elif e.dxftype() == 'LINE':
            cv2.line(overlay, utm2px(e.dxf.start[0], e.dxf.start[1]), utm2px(e.dxf.end[0], e.dxf.end[1]), c, thick)
            cv2.line(cad_canvas, utm2cad(e.dxf.start[0], e.dxf.start[1]), utm2cad(e.dxf.end[0], e.dxf.end[1]), c, thick)

        elif e.dxftype() == 'TEXT':
            text = e.dxf.text
            tp_cad = utm2cad(e.dxf.insert[0], e.dxf.insert[1])
            if 'MANZANAS' in layer:
                cv2.putText(cad_canvas, text, tp_cad, cv2.FONT_HERSHEY_SIMPLEX, 0.6, c, 1, cv2.LINE_AA)
            elif 'EQUIPAMIENTO' in layer or 'CALLES' in layer:
                cv2.putText(cad_canvas, text, tp_cad, cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1, cv2.LINE_AA)

    blended = cv2.addWeighted(img, 0.45, overlay, 0.55, 0)
    cv2.imwrite(os.path.join(out_dir, "01_superposicion_ortofoto_completa.png"), blended)
    cv2.imwrite(os.path.join(out_dir, "02_modelo_autocad_completo.png"), cad_canvas)

    sectors = [
        ("03_zoom_sector_norte_hidroelectrica.png", 425280, 8436200, 425620, 8436650),
        ("04_zoom_sector_centro_plaza_puno.png", 425300, 8435550, 425600, 8436050),
        ("05_zoom_sector_confluencia_estadio.png", 425320, 8435150, 425620, 8435600),
        ("06_zoom_sector_sur_piscina_salida.png", 425320, 8434750, 425620, 8435200)
    ]
    for name, xmin, ymin, xmax, ymax in sectors:
        px1, py2 = utm2px(xmin, ymin)
        px2, py1 = utm2px(xmax, ymax)
        x_min, x_max = min(px1, px2), max(px1, px2)
        y_min, y_max = min(py1, py2), max(py1, py2)
        crop = blended[max(0, y_min-30):min(h, y_max+30), max(0, x_min-30):min(w, x_max+30)]
        cv2.imwrite(os.path.join(out_dir, name), crop)

    print(f"Renders de verificación completados en: {out_dir}")

if __name__ == "__main__":
    main()
