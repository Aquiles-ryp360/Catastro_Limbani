"""
================================================================================
SCRIPT: export_official_kml.py
PROPÓSITO: Exporta el catastro oficial a formato KML 3D para Google Earth Pro.
================================================================================
Transforma las coordenadas proyectadas EPSG:32719 (WGS84 UTM 19S) a geográficas
EPSG:4326 (Lat/Lon) con estilos poligonales, alturas y carpetas temáticas.
"""

import os, sqlite3, struct, shapely.wkb, shapely.geometry
from pyproj import Transformer

tools_dir = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(os.path.join(tools_dir, ".."))
gpkg_path = os.path.join(work_dir, "qgis", "Catastro_Limbani_Oficial.gpkg")
out_kml = os.path.join(work_dir, "catastro_limbani.kml")

transformer = Transformer.from_crs("EPSG:32719", "EPSG:4326", always_xy=True)

def gpkg_blob_to_shapely(blob):
    flags = blob[3]
    env_size = {0:0, 1:32, 2:48, 3:48, 4:64}.get((flags >> 1) & 0x07, 0)
    return shapely.wkb.loads(blob[8 + env_size:])

def coords_to_kml_polygon(geom):
    coords = geom.exterior.coords
    pts_str = " ".join([f"{transformer.transform(x, y)[0]:.7f},{transformer.transform(x, y)[1]:.7f},0" for x, y in coords])
    return f"""        <Polygon>
          <tessellate>1</tessellate>
          <outerBoundaryIs>
            <LinearRing>
              <coordinates>{pts_str}</coordinates>
            </LinearRing>
          </outerBoundaryIs>
        </Polygon>"""

def coords_to_kml_linestring(geom):
    coords = geom.coords
    pts_str = " ".join([f"{transformer.transform(x, y)[0]:.7f},{transformer.transform(x, y)[1]:.7f},0" for x, y in coords])
    return f"""        <LineString>
          <tessellate>1</tessellate>
          <coordinates>{pts_str}</coordinates>
        </LineString>"""

def main():
    print(f"Exportando KML desde: {gpkg_path}...")
    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()

    cur.execute('SELECT fid, geom, origen, manzana, area_m2 FROM Casas_Total')
    casas_rows = cur.fetchall()

    cur.execute('SELECT fid, geom, manzana, equipamiento, area_m2 FROM Lotes_Prediales')
    lotes_rows = cur.fetchall()

    cur.execute('SELECT fid, geom, nombre FROM Rios_Cuencas')
    rios_rows = cur.fetchall()

    cur.execute('SELECT fid, geom, nombre FROM Calles')
    calles_rows = cur.fetchall()
    conn.close()

    kml_header = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>Catastro Urbano Oficial de Limbani (Sandia - Puno)</name>
    <open>1</open>
    <description>Catastro consolidado de Limbani: Huellas de viviendas, lotes prediales oficiales, ríos y vías.</description>
    
    <Style id="userHouseStyle">
      <LineStyle><color>ff00a5ff</color><width>1.8</width></LineStyle>
      <PolyStyle><color>7f0080ff</color><fill>1</fill><outline>1</outline></PolyStyle>
    </Style>
    <Style id="compHouseStyle">
      <LineStyle><color>ffe0d000</color><width>1.5</width></LineStyle>
      <PolyStyle><color>7fb6c42e</color><fill>1</fill><outline>1</outline></PolyStyle>
    </Style>
    <Style id="lotStyle">
      <LineStyle><color>ff888888</color><width>1.0</width></LineStyle>
      <PolyStyle><fill>0</fill><outline>1</outline></PolyStyle>
    </Style>
    <Style id="riverStyle">
      <LineStyle><color>ffd8b400</color><width>3.5</width></LineStyle>
    </Style>
    <Style id="streetStyle">
      <LineStyle><color>ffffffff</color><width>2.0</width></LineStyle>
    </Style>
"""

    kml_body = []
    # 1. Casas Usuario
    kml_body.append('    <Folder><name>1. Casas - Avance Usuario (334 viviendas)</name>')
    for fid, blob, origen, mz, area in casas_rows:
        if origen == 'Usuario':
            g = gpkg_blob_to_shapely(blob)
            if g and g.is_valid:
                kml_body.append(f"""      <Placemark>
        <name>Casa {fid}</name>
        <description>Mz: {mz or '-'} | Area: {area:.1f} m2 | Origen: Avance Usuario</description>
        <styleUrl>#userHouseStyle</styleUrl>
{coords_to_kml_polygon(g)}
      </Placemark>""")
    kml_body.append('    </Folder>')

    # 2. Casas Complementadas
    kml_body.append('    <Folder><name>2. Casas - Complemento (373 viviendas)</name>')
    for fid, blob, origen, mz, area in casas_rows:
        if origen != 'Usuario':
            g = gpkg_blob_to_shapely(blob)
            if g and g.is_valid:
                kml_body.append(f"""      <Placemark>
        <name>Casa {fid}</name>
        <description>Mz: {mz or '-'} | Area: {area:.1f} m2 | Origen: Complementado Oficial</description>
        <styleUrl>#compHouseStyle</styleUrl>
{coords_to_kml_polygon(g)}
      </Placemark>""")
    kml_body.append('    </Folder>')

    # 3. Rios
    kml_body.append('    <Folder><name>3. Rios y Cuencas</name>')
    for fid, blob, nombre in rios_rows:
        g = gpkg_blob_to_shapely(blob)
        if g and g.is_valid:
            kml_body.append(f"""      <Placemark>
        <name>{nombre}</name>
        <styleUrl>#riverStyle</styleUrl>
{coords_to_kml_linestring(g)}
      </Placemark>""")
    kml_body.append('    </Folder>')

    # 4. Calles
    kml_body.append('    <Folder><name>4. Vias y Calles</name>')
    for fid, blob, nombre in calles_rows:
        g = gpkg_blob_to_shapely(blob)
        if g and g.is_valid:
            kml_body.append(f"""      <Placemark>
        <name>{nombre}</name>
        <styleUrl>#streetStyle</styleUrl>
{coords_to_kml_linestring(g)}
      </Placemark>""")
    kml_body.append('    </Folder>')

    # 5. Lotes
    kml_body.append('    <Folder><name>5. Lotes Prediales Oficiales (623 lotes)</name>')
    for fid, blob, mz, eq, area in lotes_rows:
        g = gpkg_blob_to_shapely(blob)
        if g and g.is_valid:
            label = f"Lote {fid}" + (f" - Mz {mz}" if mz else "") + (f" ({eq})" if eq else "")
            kml_body.append(f"""      <Placemark>
        <name>{label}</name>
        <description>Mz: {mz or '-'} | Equipamiento: {eq or '-'} | Area: {area:.1f} m2</description>
        <styleUrl>#lotStyle</styleUrl>
{coords_to_kml_polygon(g)}
      </Placemark>""")
    kml_body.append('    </Folder>')

    kml_content = kml_header + "\n".join(kml_body) + "\n  </Document>\n</kml>"
    with open(out_kml, 'w', encoding='utf-8') as f:
        f.write(kml_content)
    print(f"KML generado exitosamente: {out_kml} ({len(kml_content)} caracteres)")

if __name__ == "__main__":
    main()
