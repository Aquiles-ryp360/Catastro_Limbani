"""
================================================================================
MÓDULO: footprint_generator.py
PROPÓSITO: Generador morfológico de huellas de vivienda urbana andina.
================================================================================
Genera huellas habitacionales realistas dentro de polígonos de lote irregulares,
siguiendo los patrones urbanos del distrito de Limbani (Sandia, Puno):
1. Ubicación al frente del lote (colindante a la vía o calle más cercana).
2. Proporción rectangular/L realista (área entre 42 y 110 m2, cobertura ~35-45%).
3. Retiros limpios de linderos colindantes (0.5 a 0.8 m).
4. Preservación del patio posterior / corral tradicional andino.
"""

import numpy as np
import shapely.geometry
import shapely.affinity

def make_house_street_front(lot: shapely.geometry.Polygon, street_axes: list = None) -> shapely.geometry.Polygon:
    """
    Genera una huella construida realista en el frente de un lote hacia la calle.
    """
    lot = shapely.make_valid(lot)
    if lot.area < 40:
        b = lot.buffer(-0.5, join_style=2)
        return b if (b.is_valid and b.area >= 8.0) else None
        
    mrr = lot.minimum_rotated_rectangle
    coords = list(mrr.exterior.coords)[:-1]
    
    edge1 = np.array(coords[1]) - np.array(coords[0])
    edge2 = np.array(coords[2]) - np.array(coords[1])
    len1 = np.linalg.norm(edge1)
    len2 = np.linalg.norm(edge2)
    
    angle = np.degrees(np.arctan2(edge1[1], edge1[0])) if len1 > len2 else np.degrees(np.arctan2(edge2[1], edge2[0]))
    
    center = lot.centroid
    lot_r = shapely.affinity.rotate(lot, -angle, origin=center)
    minx, miny, maxx, maxy = lot_r.bounds
    w = maxx - minx
    h = maxy - miny
    
    # Cobertura objetivo típica en Limbani
    target_area = min(110.0, max(42.0, lot.area * 0.38))
    hw = min(w - 1.4, max(5.2, np.sqrt(target_area * 1.35)))
    hh = min(h - 1.4, max(4.8, target_area / hw))
    
    # Candidatos en esquinas y frentes del lote rotado
    candidates = [
        shapely.geometry.box(minx + 0.7, miny + 0.7, minx + 0.7 + hw, miny + 0.7 + hh),
        shapely.geometry.box(maxx - 0.7 - hw, miny + 0.7, maxx - 0.7, miny + 0.7 + hh),
        shapely.geometry.box(minx + 0.7, maxy - 0.7 - hh, minx + 0.7 + hw, maxy - 0.7),
        shapely.geometry.box(maxx - 0.7 - hw, maxy - 0.7 - hh, maxx - 0.7, maxy - 0.7),
    ]
    
    safe_lot = lot.buffer(-0.4, join_style=2)
    valid_cands = []
    for c in candidates:
        cr = shapely.affinity.rotate(c, angle, origin=center)
        try:
            inter = safe_lot.intersection(cr)
            if inter.is_valid and inter.area >= target_area * 0.55:
                d = min(cr.centroid.distance(s) for s in street_axes) if street_axes else 0
                valid_cands.append((d, -inter.area, inter))
        except Exception:
            pass
            
    if valid_cands:
        valid_cands.sort()
        best = valid_cands[0][2]
        if isinstance(best, shapely.geometry.MultiPolygon):
            best = max(best.geoms, key=lambda p: p.area)
        return best
        
    fallback = lot.buffer(-0.8, join_style=2)
    return fallback if (fallback.is_valid and fallback.area >= 10.0) else None
