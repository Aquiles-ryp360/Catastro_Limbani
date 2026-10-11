"""
================================================================================
SCRIPT MAESTRO: generate_official_catastre.py
PROPÓSITO: Fusión integral del avance de digitalización con el levantamiento oficial.
================================================================================
Flujo de trabajo:
1. Lee los avances del usuario en 'qgis/Catastro-Limbani.gpkg' en modo SOLO LECTURA.
   - Casas digitalizadas por el usuario (334)
   - Ejes de calles digitalizados (19)
   - Ejes de ríos y quebradas (5)
2. Lee los 623 lotes oficiales y toponimias desde 'insumos/Lotes_Limpios.dxf'.
3. Detecta lotes residenciales vacantes y complementa las huellas usando el módulo
   morfológico andino 'footprint_generator.py'.
4. Exporta el GeoPackage oficial complementario: 'qgis/Catastro_Limbani_Oficial.gpkg'
5. Exporta el plano CAD maestro: 'catastro_limbani.dxf' con 9 capas normalizadas
   y membrete de ingeniería oficial.
"""

import os, sys, math, sqlite3, struct
import numpy as np
import shapely.geometry
import shapely.affinity
import shapely.wkb
import ezdxf
from ezdxf import colors
from ezdxf.enums import TextEntityAlignment

# Directorios de trabajo relativos
tools_dir = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(os.path.join(tools_dir, ".."))
qgis_dir = os.path.join(work_dir, "qgis")
insumos_dir = os.path.join(work_dir, "insumos")

user_gpkg = os.path.join(qgis_dir, "Catastro-Limbani.gpkg")
lotes_dxf = os.path.join(insumos_dir, "Lotes_Limpios.dxf")
if not os.path.exists(lotes_dxf):
    # Fallback to parent downloads
    lotes_dxf = os.path.abspath(os.path.join(work_dir, "..", "Lotes_Limpios.dxf"))

sys.path.append(tools_dir)
from footprint_generator import make_house_street_front

def gpkg_blob_to_shapely(blob):
    if not blob or len(blob) < 8:
        return None
    flags = blob[3]
    envelope_sizes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
    env_size = envelope_sizes.get((flags >> 1) & 0x07, 0)
    return shapely.wkb.loads(blob[8 + env_size:])

def shapely_to_gpkg_blob(geom, srs_id=32719):
    wkb = shapely.wkb.dumps(geom)
    minx, miny, maxx, maxy = geom.bounds
    header = struct.pack('<bbbbI4d', 0x47, 0x50, 0, 0x03, srs_id, minx, maxx, miny, maxy)
    return header + wkb

def main():
    print("=" * 70)
    print("EJECUTANDO PIPELINE CATASTRAL LIMBANI (WGS84 UTM 19S)")
    print("=" * 70)

    # 1. LEER AVANCE DE USUARIO (READ-ONLY)
    print("\n[1/5] Leyendo avance del usuario desde Catastro-Limbani.gpkg...")
    conn_u = sqlite3.connect(user_gpkg)
    cur_u = conn_u.cursor()

    cur_u.execute('SELECT fid, geometry FROM "Casas"')
    user_casas = []
    for fid, blob in cur_u.fetchall():
        g = gpkg_blob_to_shapely(blob)
        if g and g.is_valid:
            user_casas.append({"fid": fid, "geom": g, "origen": "Usuario"})

    cur_u.execute('SELECT fid, Calles, geometry FROM "Calles"')
    user_calles = []
    for fid, name, blob in cur_u.fetchall():
        g = gpkg_blob_to_shapely(blob)
        if g and g.is_valid:
            user_calles.append({"fid": fid, "name": name if name else f"Calle_{fid}", "geom": g})

    cur_u.execute('SELECT fid, rio, geometry FROM "Rios-Cuencas"')
    user_rios = []
    for fid, name, blob in cur_u.fetchall():
        g = gpkg_blob_to_shapely(blob)
        if g and g.is_valid:
            user_rios.append({"fid": fid, "name": name if name else f"Rio_{fid}", "geom": g})

    conn_u.close()
    print(f" -> Preservadas: {len(user_casas)} casas de usuario, {len(user_calles)} vías, {len(user_rios)} ríos.")

    # 2. LEER LEVANTAMIENTO OFICIAL (LOTES LIMPIOS)
    print("\n[2/5] Leyendo linderos oficiales y textos desde Lotes_Limpios.dxf...")
    doc_ll = ezdxf.readfile(lotes_dxf)
    msp_ll = doc_ll.modelspace()

    lots = []
    texts = []
    for e in msp_ll:
        if e.dxftype() == 'POLYLINE' and e.is_closed:
            pts = [(v.dxf.location.x, v.dxf.location.y) for v in e.vertices]
            if len(pts) >= 3:
                poly = shapely.geometry.Polygon(pts)
                if poly.is_valid and poly.area > 5.0:
                    lots.append(poly)
        elif e.dxftype() == 'TEXT':
            txt = e.dxf.text.strip()
            texts.append({
                "text": txt,
                "pt": shapely.geometry.Point(e.dxf.insert.x, e.dxf.insert.y),
                "x": e.dxf.insert.x,
                "y": e.dxf.insert.y,
                "height": e.dxf.height,
                "rotation": e.dxf.rotation
            })

    manzana_texts = [t for t in texts if len(t["text"]) <= 3 and t["text"].isalnum()]
    street_texts = [t for t in texts if any(v in t["text"].upper() for v in ['JR.', 'AV.', 'PJE.', 'PASAJE', 'CALLE'])]
    river_texts = [t for t in texts if any(r in t["text"].upper() for r in ['RIO LIMBANI', 'CHINCHALAMANI', 'RIACHUELO', 'FAJA MARGINAL', 'CANAL'])]
    equip_texts = [t for t in texts if any(eq in t["text"].upper() for eq in ['PLAZA', 'PARQUE', 'EDUCACI', 'SALUD', 'DEPORTIVA', 'RECREACI', 'COMUNAL', 'VERDE', 'TERCEROS', 'OTROS FINES'])]

    print(f" -> Lotes oficiales: {len(lots)} | Manzanas: {len(manzana_texts)} | Vías: {len(street_texts)} | Equipamientos: {len(equip_texts)}")

    # 3. COMPLEMENTAR HUELLAS HABITACIONALES
    print("\n[3/5] Generando huellas habitacionales para lotes vacantes...")
    complemented_casas = []
    lot_data = []
    street_geoms = [uc["geom"] for uc in user_calles]

    for idx, lot in enumerate(lots):
        lot_valid = shapely.make_valid(lot)
        equip_type = None
        for eq in equip_texts:
            if lot_valid.contains(eq["pt"]) or lot_valid.distance(eq["pt"]) < 1.0:
                equip_type = eq["text"]
                break
                
        is_river_buffer = any(lot_valid.contains(rt["pt"]) or lot_valid.distance(rt["pt"]) < 1.0 for rt in river_texts)
        mz_name = next((mt["text"] for mt in manzana_texts if lot_valid.contains(mt["pt"]) or lot_valid.distance(mt["pt"]) < 5.0), "")
        
        lot_data.append({
            "fid": idx + 1,
            "geom": lot_valid,
            "area": round(lot_valid.area, 2),
            "manzana": mz_name,
            "equip": equip_type,
            "is_river": is_river_buffer
        })
        
        has_user_house = False
        for uc in user_casas:
            uc_geom = shapely.make_valid(uc["geom"])
            if lot_valid.intersects(uc_geom):
                try:
                    if lot_valid.intersection(uc_geom).area > 2.0:
                        has_user_house = True
                        break
                except Exception:
                    has_user_house = True
                    break
                
        if has_user_house or equip_type or is_river_buffer:
            continue
            
        inner = make_house_street_front(lot_valid, street_geoms)
        if inner and inner.is_valid and inner.area >= 10.0:
            complemented_casas.append({
                "fid": len(user_casas) + len(complemented_casas) + 1,
                "geom": inner,
                "origen": "Complementado",
                "manzana": mz_name
            })

    total_casas = user_casas + complemented_casas
    print(f" -> Total consolidado: {len(user_casas)} casas usuario + {len(complemented_casas)} complementadas = {len(total_casas)} viviendas.")

    # 4. GUARDAR GEOPACKAGE OFICIAL
    out_gpkg = os.path.join(qgis_dir, "Catastro_Limbani_Oficial.gpkg")
    if os.path.exists(out_gpkg):
        os.remove(out_gpkg)

    print(f"\n[4/5] Escribiendo GeoPackage oficial: {out_gpkg}...")
    conn_out = sqlite3.connect(out_gpkg)
    cur_out = conn_out.cursor()

    cur_out.execute("""
    CREATE TABLE gpkg_spatial_ref_sys (
        srs_name TEXT NOT NULL, srs_id INTEGER NOT NULL PRIMARY KEY,
        organization TEXT NOT NULL, organization_coordsys_id INTEGER NOT NULL,
        definition TEXT NOT NULL, description TEXT
    );
    """)
    cur_out.execute("""
    INSERT INTO gpkg_spatial_ref_sys VALUES 
    ('WGS 84 / UTM zone 19S', 32719, 'EPSG', 32719, 
     'PROJCS["WGS 84 / UTM zone 19S",GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",-69],PARAMETER["scale_factor",0.9996],PARAMETER["false_easting",500000],PARAMETER["false_northing",10000000],UNIT["metre",1]]',
     'WGS 84 UTM Zone 19S');
    """)
    cur_out.execute("""
    CREATE TABLE gpkg_contents (
        table_name TEXT NOT NULL PRIMARY KEY, data_type TEXT NOT NULL,
        identifier TEXT UNIQUE, description TEXT DEFAULT '',
        last_change DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
        min_x DOUBLE, min_y DOUBLE, max_x DOUBLE, max_y DOUBLE, srs_id INTEGER
    );
    """)
    cur_out.execute("""
    CREATE TABLE gpkg_geometry_columns (
        table_name TEXT NOT NULL, column_name TEXT NOT NULL,
        geometry_type_name TEXT NOT NULL, srs_id INTEGER NOT NULL,
        z TINYINT NOT NULL, m TINYINT NOT NULL,
        CONSTRAINT pk_geom_cols PRIMARY KEY (table_name, column_name)
    );
    """)

    # Tabla 1: Casas_Total
    cur_out.execute("CREATE TABLE Casas_Total (fid INTEGER PRIMARY KEY AUTOINCREMENT, geom BLOB, origen TEXT, manzana TEXT, area_m2 REAL);")
    cur_out.execute("INSERT INTO gpkg_geometry_columns VALUES ('Casas_Total', 'geom', 'POLYGON', 32719, 0, 0)")
    c_minx, c_miny, c_maxx, c_maxy = 1e9, 1e9, -1e9, -1e9
    for c in total_casas:
        g = c["geom"]
        bx = g.bounds
        c_minx, c_miny = min(c_minx, bx[0]), min(c_miny, bx[1])
        c_maxx, c_maxy = max(c_maxx, bx[2]), max(c_maxy, bx[3])
        cur_out.execute("INSERT INTO Casas_Total (geom, origen, manzana, area_m2) VALUES (?, ?, ?, ?)",
                        (shapely_to_gpkg_blob(g, 32719), c.get("origen", "Usuario"), c.get("manzana", ""), round(g.area, 2)))
    cur_out.execute("INSERT INTO gpkg_contents VALUES ('Casas_Total', 'features', 'Casas_Total', 'Huellas consolidadas', strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?, ?, ?, ?, 32719)",
                    (c_minx, c_miny, c_maxx, c_maxy))

    # Tabla 2: Lotes_Prediales
    cur_out.execute("CREATE TABLE Lotes_Prediales (fid INTEGER PRIMARY KEY AUTOINCREMENT, geom BLOB, manzana TEXT, equipamiento TEXT, area_m2 REAL);")
    cur_out.execute("INSERT INTO gpkg_geometry_columns VALUES ('Lotes_Prediales', 'geom', 'POLYGON', 32719, 0, 0)")
    l_minx, l_miny, l_maxx, l_maxy = 1e9, 1e9, -1e9, -1e9
    for ld in lot_data:
        g = ld["geom"]
        bx = g.bounds
        l_minx, l_miny = min(l_minx, bx[0]), min(l_miny, bx[1])
        l_maxx, l_maxy = max(l_maxx, bx[2]), max(l_maxy, bx[3])
        cur_out.execute("INSERT INTO Lotes_Prediales (geom, manzana, equipamiento, area_m2) VALUES (?, ?, ?, ?)",
                        (shapely_to_gpkg_blob(g, 32719), ld["manzana"], ld["equip"], ld["area"]))
    cur_out.execute("INSERT INTO gpkg_contents VALUES ('Lotes_Prediales', 'features', 'Lotes_Prediales', 'Lotes prediales', strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?, ?, ?, ?, 32719)",
                    (l_minx, l_miny, l_maxx, l_maxy))

    # Tabla 3: Rios_Cuencas
    cur_out.execute("CREATE TABLE Rios_Cuencas (fid INTEGER PRIMARY KEY AUTOINCREMENT, geom BLOB, nombre TEXT);")
    cur_out.execute("INSERT INTO gpkg_geometry_columns VALUES ('Rios_Cuencas', 'geom', 'LINESTRING', 32719, 0, 0)")
    r_minx, r_miny, r_maxx, r_maxy = 1e9, 1e9, -1e9, -1e9
    for ur in user_rios:
        g = ur["geom"]
        bx = g.bounds
        r_minx, r_miny = min(r_minx, bx[0]), min(r_miny, bx[1])
        r_maxx, r_maxy = max(r_maxx, bx[2]), max(r_maxy, bx[3])
        cur_out.execute("INSERT INTO Rios_Cuencas (geom, nombre) VALUES (?, ?)", (shapely_to_gpkg_blob(g, 32719), ur["name"]))
    cur_out.execute("INSERT INTO gpkg_contents VALUES ('Rios_Cuencas', 'features', 'Rios_Cuencas', 'Rios y quebradas', strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?, ?, ?, ?, 32719)",
                    (r_minx, r_miny, r_maxx, r_maxy))

    # Tabla 4: Calles
    cur_out.execute("CREATE TABLE Calles (fid INTEGER PRIMARY KEY AUTOINCREMENT, geom BLOB, nombre TEXT);")
    cur_out.execute("INSERT INTO gpkg_geometry_columns VALUES ('Calles', 'geom', 'LINESTRING', 32719, 0, 0)")
    v_minx, v_miny, v_maxx, v_maxy = 1e9, 1e9, -1e9, -1e9
    for uc in user_calles:
        g = uc["geom"]
        bx = g.bounds
        v_minx, v_miny = min(v_minx, bx[0]), min(v_miny, bx[1])
        v_maxx, v_maxy = max(v_maxx, bx[2]), max(v_maxy, bx[3])
        cur_out.execute("INSERT INTO Calles (geom, nombre) VALUES (?, ?)", (shapely_to_gpkg_blob(g, 32719), uc["name"]))
    cur_out.execute("INSERT INTO gpkg_contents VALUES ('Calles', 'features', 'Calles', 'Ejes viales', strftime('%Y-%m-%dT%H:%M:%fZ','now'), ?, ?, ?, ?, 32719)",
                    (v_minx, v_miny, v_maxx, v_maxy))

    conn_out.commit()
    conn_out.close()
    print(" -> GeoPackage oficial guardado exitosamente.")

    # 5. GENERAR PLANO MAESTRO AUTOCAD DXF
    print("\n[5/5] Generando planos maestros de AutoCAD DXF...")
    doc_dxf = ezdxf.new('R2010', setup=True)
    msp = doc_dxf.modelspace()

    doc_dxf.layers.add('01_RIOS_Y_CUENCAS', color=140, lineweight=35)
    doc_dxf.layers.add('02_CALLES_Y_VIAS', color=7, lineweight=25)
    doc_dxf.layers.add('03_MANZANAS_ROTULOS', color=6, lineweight=35)
    doc_dxf.layers.add('04_LOTES_PREDIALES', color=7, lineweight=15)
    doc_dxf.layers.add('05_HUELLAS_CASAS_USUARIO', color=30, lineweight=30)
    doc_dxf.layers.add('06_HUELLAS_CASAS_COMPLEMENTO', color=4, lineweight=25)
    doc_dxf.layers.add('07_EQUIPAMIENTOS', color=3, lineweight=40)
    doc_dxf.layers.add('08_TOPONIMIA_ROTULOS', color=7)
    doc_dxf.layers.add('09_MEMBRETE_DATOS', color=7, lineweight=35)

    for ur in user_rios:
        pts = list(ur["geom"].coords)
        msp.add_lwpolyline([(round(p[0], 2), round(p[1], 2)) for p in pts], dxfattribs={'layer': '01_RIOS_Y_CUENCAS'})
        mid_idx = len(pts) // 2
        msp.add_text(ur["name"], height=3.5, dxfattribs={'layer': '01_RIOS_Y_CUENCAS'}).set_placement(
            (round(pts[mid_idx][0], 2), round(pts[mid_idx][1], 2)), align=TextEntityAlignment.MIDDLE_CENTER)

    for uc in user_calles:
        pts = list(uc["geom"].coords)
        msp.add_lwpolyline([(round(p[0], 2), round(p[1], 2)) for p in pts], dxfattribs={'layer': '02_CALLES_Y_VIAS'})
        if uc["name"] and not uc["name"].startswith("Calle_"):
            mid_idx = len(pts) // 2
            msp.add_text(uc["name"], height=2.8, dxfattribs={'layer': '08_TOPONIMIA_ROTULOS'}).set_placement(
                (round(pts[mid_idx][0], 2), round(pts[mid_idx][1], 2) + 2.0), align=TextEntityAlignment.BOTTOM_CENTER)

    for ld in lot_data:
        pts = list(ld["geom"].exterior.coords)
        layer = '07_EQUIPAMIENTOS' if ld["equip"] else '04_LOTES_PREDIALES'
        msp.add_lwpolyline([(round(p[0], 2), round(p[1], 2)) for p in pts], close=True, dxfattribs={'layer': layer})
        if ld["equip"]:
            c = ld["geom"].centroid
            msp.add_text(ld["equip"], height=3.0, dxfattribs={'layer': '07_EQUIPAMIENTOS'}).set_placement(
                (round(c.x, 2), round(c.y, 2)), align=TextEntityAlignment.MIDDLE_CENTER)

    for uc in user_casas:
        pts = list(uc["geom"].exterior.coords)
        msp.add_lwpolyline([(round(p[0], 2), round(p[1], 2)) for p in pts], close=True, dxfattribs={'layer': '05_HUELLAS_CASAS_USUARIO'})

    for cc in complemented_casas:
        pts = list(cc["geom"].exterior.coords)
        msp.add_lwpolyline([(round(p[0], 2), round(p[1], 2)) for p in pts], close=True, dxfattribs={'layer': '06_HUELLAS_CASAS_COMPLEMENTO'})

    for mt in manzana_texts:
        msp.add_text(mt["text"], height=mt["height"] if mt["height"] > 0 else 3.5, dxfattribs={'layer': '03_MANZANAS_ROTULOS'}).set_placement(
            (round(mt["x"], 2), round(mt["y"], 2)), align=TextEntityAlignment.MIDDLE_CENTER)

    for st in street_texts:
        msp.add_text(st["text"], height=st["height"] if st["height"] > 0 else 2.8, dxfattribs={'layer': '08_TOPONIMIA_ROTULOS'}).set_placement(
            (round(st["x"], 2), round(st["y"], 2)), align=TextEntityAlignment.MIDDLE_CENTER)

    # Membrete
    tb_x, tb_y = 425680.0, 8436600.0
    tb_w, tb_h = 320.0, 420.0
    frame = [(tb_x, tb_y), (tb_x + tb_w, tb_y), (tb_x + tb_w, tb_y - tb_h), (tb_x, tb_y - tb_h)]
    msp.add_lwpolyline(frame, close=True, dxfattribs={'layer': '09_MEMBRETE_DATOS', 'lineweight': 50})
    msp.add_line((tb_x, tb_y - 65), (tb_x + tb_w, tb_y - 65), dxfattribs={'layer': '09_MEMBRETE_DATOS', 'lineweight': 35})
    msp.add_text("PLANO CATASTRAL URBANO OFICIAL", height=5.5, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + tb_w/2, tb_y - 20), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text("DISTRITO DE LIMBANI - SANDIA - PUNO", height=4.2, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + tb_w/2, tb_y - 38), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text("SISTEMA DE COORDENADAS: WGS84 UTM ZONA 19 SUR", height=3.2, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + tb_w/2, tb_y - 54), align=TextEntityAlignment.MIDDLE_CENTER)

    cur_y = tb_y - 85
    msp.add_text("RESUMEN CATASTRAL Y METRADOS:", height=3.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 15, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 16
    msp.add_text(f"- LOTES PREDIALES REGISTRADOS: {len(lot_data)} lotes oficiales", height=2.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 20, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 14
    msp.add_text(f"- HUELLAS DE CASAS (AVANCE USUARIO): {len(user_casas)} viviendas digitalizadas", height=2.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 20, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 14
    msp.add_text(f"- HUELLAS DE CASAS (COMPLEMENTO): {len(complemented_casas)} viviendas en lotes vacantes", height=2.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 20, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 14
    msp.add_text(f"- TOTAL VIVIENDAS CONSOLIDADAS: {len(total_casas)} predios construidos", height=2.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 20, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 14
    msp.add_text(f"- MANZANAS CATASTRALES: {len(manzana_texts)} manzanas oficiales (A, B, C...)", height=2.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 20, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 14
    msp.add_text(f"- RED HIDROGRAFICA: Rio Limbani, Rio Chinchalamani y quebradas", height=2.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 20, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)
    cur_y -= 14
    msp.add_text(f"- EQUIPAMIENTOS URBANOS: Plaza, Parques, Deporte, Educacion y Salud", height=2.8, dxfattribs={'layer': '09_MEMBRETE_DATOS'}).set_placement((tb_x + 20, cur_y), align=TextEntityAlignment.MIDDLE_LEFT)

    all_x = [ld["geom"].bounds[0] for ld in lot_data] + [ld["geom"].bounds[2] for ld in lot_data]
    all_y = [ld["geom"].bounds[1] for ld in lot_data] + [ld["geom"].bounds[3] for ld in lot_data]
    doc_dxf.header['$EXTMIN'] = (min(all_x) - 50.0, min(all_y) - 50.0, 0.0)
    doc_dxf.header['$EXTMAX'] = (max(all_x) + 50.0, max(all_y) + 50.0, 0.0)

    out_dxf = os.path.join(work_dir, "catastro_limbani.dxf")
    doc_dxf.saveas(out_dxf)
    print(f" -> Guardado plano DXF: {out_dxf}")
    print("\nPROCESO COMPLETADO EXITOSAMENTE.")

if __name__ == "__main__":
    main()
