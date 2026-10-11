# Catastro Urbano Oficial de Limbani (Sandia - Puno, Perú)

Levantamiento, vectorización y consolidación catastral del casco urbano del distrito de Limbani, provincia de Sandia, departamento de Puno.

## 📌 Sistema de Referencia Geográfica
- **Datum:** WGS 84
- **Proyección:** Universal Transverse Mercator (UTM)
- **Zona:** 19 Sur (EPSG: 32719)

---

## 📂 Contenido del Repositorio

### 1. Sistema de Información Geográfica (QGIS)
- `qgis/Catastro-Limbani-Consolidado.qgz`: Proyecto listo para abrir en QGIS con simbología estilizada y ortofoto satelital.
- `qgis/Catastro_Limbani_Oficial.gpkg`: GeoPackage con todas las capas vectoriales:
  - `Casas_Total`: 707 viviendas clasificadas por origen (Avance de usuario y complemento).
  - `Lotes_Prediales`: 623 lotes de propiedad oficial con datos de manzana y equipamientos.
  - `Rios_Cuencas`: Río Limbani, Río Chinchalamani y quebradas naturales.
  - `Calles`: Red de ejes viales urbanos.
- `qgis/Catastro-Limbani.qgz` y `qgis/Catastro-Limbani.gpkg`: Archivos de avance original de digitalización.

### 2. Planos CAD (AutoCAD)
- `catastro_limbani.dxf`: Plano catastral general compatible con AutoCAD (versión R2010), organizado en capas:
  - `01_RIOS_Y_CUENCAS`
  - `02_CALLES_Y_VIAS`
  - `03_MANZANAS_ROTULOS`
  - `04_LOTES_PREDIALES`
  - `05_HUELLAS_CASAS_USUARIO`
  - `06_HUELLAS_CASAS_COMPLEMENTO`
  - `07_EQUIPAMIENTOS`
  - `08_TOPONIMIA_ROTULOS`
  - `09_MEMBRETE_DATOS`

### 3. Visualización 3D y Control Visual
- `catastro_limbani.kml`: Archivo compatible con Google Earth Pro.
- `verificacion_final/`: Imágenes de control y superposición en alta resolución por sectores.

---

## 📊 Metrados y Estadísticas Catastrales
- **Total Lotes Prediales:** 623
- **Total Viviendas Consolidadas:** 707
- **Manzanas Registradas:** 86
- **Red Hidrográfica:** Río Limbani y afluentes
- **Equipamientos Urbanos:** Plaza de Armas, Estadio, Piscina, Parques, Educación, Salud
