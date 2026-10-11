"""
================================================================================
SCRIPT: create_consolidated_qgz.py
PROPÓSITO: Empaqueta el proyecto consolidado para QGIS (Catastro-Limbani-Consolidado.qgz).
================================================================================
Enlaza el GeoPackage oficial 'Catastro_Limbani_Oficial.gpkg' con las capas:
- Casas_Total (707 viviendas)
- Lotes_Prediales (623 lotes)
- Rios_Cuencas (Red fluvial)
- Calles (Ejes viales)
- Capas base XYZ (Google Satellite)
"""

import os, zipfile

tools_dir = os.path.dirname(os.path.abspath(__file__))
work_dir = os.path.abspath(os.path.join(tools_dir, ".."))
qgis_dir = os.path.join(work_dir, "qgis")

orig_qgz = os.path.join(qgis_dir, "Catastro-Limbani.qgz")
new_qgz = os.path.join(qgis_dir, "Catastro-Limbani-Consolidado.qgz")

def main():
    print("Empaquetando Catastro-Limbani-Consolidado.qgz...")
    with zipfile.ZipFile(orig_qgz, 'r') as z_in:
        qgs_content = z_in.read('Catastro-Limbani.qgs').decode('utf-8')
        styles_db = z_in.read('cxWAxC_styles.db')

    # Reemplazo de fuentes de datos hacia Catastro_Limbani_Oficial.gpkg
    qgs_content = qgs_content.replace(
        './Catastro-Limbani.gpkg|layername=Casas',
        './Catastro_Limbani_Oficial.gpkg|layername=Casas_Total'
    )
    qgs_content = qgs_content.replace(
        './Catastro-Limbani.gpkg|layername=Rios-Cuencas',
        './Catastro_Limbani_Oficial.gpkg|layername=Rios_Cuencas'
    )
    qgs_content = qgs_content.replace(
        './Catastro-Limbani.gpkg|layername=Calles',
        './Catastro_Limbani_Oficial.gpkg|layername=Calles'
    )

    qgs_content = qgs_content.replace('<layername>Casas</layername>', '<layername>Casas_Total (707 Viviendas)</layername>')
    qgs_content = qgs_content.replace('<layername>Calles</layername>', '<layername>Calles_Ejes_Viales</layername>')
    qgs_content = qgs_content.replace('<layername>Rios-Cuencas</layername>', '<layername>Rios_y_Cuencas_Limbani</layername>')

    new_qgs_name = "Catastro-Limbani-Consolidado.qgs"
    with zipfile.ZipFile(new_qgz, 'w', compression=zipfile.ZIP_DEFLATED) as z_out:
        z_out.writestr(new_qgs_name, qgs_content.encode('utf-8'))
        z_out.writestr('cxWAxC_styles.db', styles_db)

    print(f"Proyecto QGIS generado: {new_qgz} ({os.path.getsize(new_qgz)} bytes)")

if __name__ == "__main__":
    main()
