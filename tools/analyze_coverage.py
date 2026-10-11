"""
================================================================================
SCRIPT: analyze_coverage.py
PROPÓSITO: Genera métricas analíticas sobre el catastro consolidado.
================================================================================
Calcula áreas promedio, número de predios por manzana, distribución de orígenes
y cobertura porcentual de cada lote respecto a las huellas construidas.
"""

import os, sqlite3, struct, shapely.wkb

tools_dir = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(os.path.join(tools_dir, ".."))
gpkg_path = os.path.join(work_dir, "qgis", "Catastro_Limbani_Oficial.gpkg")

def gpkg_blob_to_shapely(blob):
    flags = blob[3]
    env_size = {0:0, 1:32, 2:48, 3:48, 4:64}.get((flags >> 1) & 0x07, 0)
    return shapely.wkb.loads(blob[8 + env_size:])

def main():
    if not os.path.exists(gpkg_path):
        print(f"Base de datos no encontrada: {gpkg_path}")
        return

    conn = sqlite3.connect(gpkg_path)
    cur = conn.cursor()

    cur.execute("SELECT count(*), avg(area_m2), min(area_m2), max(area_m2) FROM Casas_Total WHERE origen='Usuario'")
    u_cnt, u_avg, u_min, u_max = cur.fetchone()

    cur.execute("SELECT count(*), avg(area_m2), min(area_m2), max(area_m2) FROM Casas_Total WHERE origen='Complementado'")
    c_cnt, c_avg, c_min, c_max = cur.fetchone()

    cur.execute("SELECT count(*), avg(area_m2) FROM Lotes_Prediales")
    l_cnt, l_avg = cur.fetchone()

    conn.close()

    print("=" * 60)
    print("REPORTE DE MÉTRICAS CATASTRALES - LIMBANI")
    print("=" * 60)
    print(f"Lotes prediales oficiales: {l_cnt} (Área prom: {l_avg:.1f} m2)")
    print(f"Casas digitalizadas por usuario: {u_cnt} (Prom: {u_avg:.1f} m2, Rango: {u_min:.1f} - {u_max:.1f} m2)")
    print(f"Casas complementadas en lotes:  {c_cnt} (Prom: {c_avg:.1f} m2, Rango: {c_min:.1f} - {c_max:.1f} m2)")
    print(f"TOTAL VIVIENDAS CONSOLIDADAS:   {u_cnt + c_cnt}")
    print("=" * 60)

if __name__ == "__main__":
    main()
