# 🤖 AGENT.md - Guía de Operación y Desarrollo para Agentes IA

> **Para cualquier Agente IA o Asistente de Código que trabaje en este repositorio:**  
> Lee este documento detenidamente antes de realizar cualquier modificación. Contiene las reglas operativas, arquitectura de datos, directrices morfológicas y el pipeline de herramientas para el Catastro Urbano de Limbani.

---

## 1. 📌 Contexto del Proyecto y Dominio

- **Ubicación:** Distrito de Limbani, Provincia de Sandia, Departamento de Puno, Perú.
- **Topografía:** Valle interandino encajonado de alta pendiente, atravesado por dos ríos principales: el **Río Limbani** (cauce central) y el **Río Chinchalamani** (afluente oeste), además de quebradas laterales.
- **Sistema Geodésico Oficial:** **WGS 84 / UTM Zona 19 Sur** (`EPSG:32719`).
- **Objetivo:** Consolidar el catastro urbano digital unificando la digitalización manual del usuario con el levantamiento oficial por lotes, garantizando 100% de coherencia morfológica para proyectos de ingeniería y electrificación.

---

## 2. ⚠️ Reglas de Oro No Negociables (Directivas Críticas)

### 🔴 Regla 1: El avance del usuario es SAGRADO (Solo Lectura)
- **NUNCA** sobreescribas, modifiques ni borres los archivos de avance original del usuario:
  - `qgis/Catastro-Limbani.gpkg`
  - `qgis/Catastro-Limbani.qgz`
- Estos archivos se leen únicamente en modo **READ-ONLY**. Todo resultado consolidado se guarda en los archivos oficiales derivados (`Catastro_Limbani_Oficial.gpkg` y `catastro_limbani.dxf`).

### 🔴 Regla 2: Hidrografía y Topografía Exacta
- *"El río no está a un canto"*: El río no es una línea decorativa al margen del pueblo. Río Limbani fluye por el corazón del casco urbano y Río Chinchalamani desemboca en él a la altura del Estadio Municipal.
- **JAMÁS** coloques huellas de casas, postes ni líneas cruzando el cauce activo ni las fajas marginales.

### 🔴 Regla 3: Morfología Urbana Andina Realista
- **NO uses generadores de cuadrícula sintética ni "radiadores/códigos de barra"**.
- En Limbani los lotes son irregulares (150 a 400 m²). Las viviendas son módulos compactos (42 a 110 m², cubriendo ~35% del lote), construidas en el **frente de calle**, dejando el fondo como patio/corral interior.
- Usa siempre el algoritmo morfológico `tools/footprint_generator.py` para complementar lotes vacantes.

### 🔴 Regla 4: Cero redes eléctricas hasta aprobación catastral
- **NO** dibujes cables, postes, acometidas ni redes de baja/media tensión hasta que la base catastral (casas, lotes, vías, ríos) esté 100% aprobada y validada por el usuario.

---

## 3. 📂 Estructura del Repositorio

```text
Catastro_Limbani/
├── AGENT.md                       # Esta guía maestra para IA
├── README.md                      # Ficha técnica para humanos
├── .gitignore                     # Filtros para evitar temporales y locks
├── catastro_limbani.dxf           # Plano maestro AutoCAD (R2010, 9 capas)
├── catastro_limbani.kml           # Modelo 3D para Google Earth Pro
├── ortofoto_limbani.jpg           # Ortofoto satelital georreferenciada
├── ortofoto_limbani.jgw/tfw/wld   # Archivos World de georreferenciación
│
├── insumos/                       # Materia prima oficial
│   └── Lotes_Limpios.dxf          # Levantamiento oficial: 623 lotes y textos
│
├── qgis/                          # Sistema de Información Geográfica
│   ├── Catastro-Limbani-Consolidado.qgz  # Proyecto consolidado listo
│   ├── Catastro_Limbani_Oficial.gpkg     # GeoPackage con 4 capas normalizadas
│   ├── Catastro-Limbani.gpkg             # [ORIGINAL USUARIO - NO TOCAR]
│   └── Catastro-Limbani.qgz              # [ORIGINAL USUARIO - NO TOCAR]
│
├── tools/                         # Herramientas y Pipeline de Python
│   ├── generate_official_catastre.py     # Script maestro de consolidación
│   ├── footprint_generator.py            # Algoritmo morfológico de huellas
│   ├── create_consolidated_qgz.py        # Generador del proyecto QGIS
│   ├── export_official_kml.py            # Exportador KML para Google Earth
│   ├── render_final_verification.py      # Motor de control visual OpenCV
│   ├── analyze_coverage.py               # Analizador de métricas y metrados
│   └── push_to_github.py                 # Sincronizador seguro de GitHub
│
└── verificacion_final/            # Control visual en alta resolución
    ├── 01_superposicion_ortofoto_completa.png
    ├── 02_modelo_autocad_completo.png
    ├── 03_zoom_sector_norte_hidroelectrica.png
    ├── 04_zoom_sector_centro_plaza_puno.png
    ├── 05_zoom_sector_confluencia_estadio.png
    └── 06_zoom_sector_sur_piscina_salida.png
```

---

## 4. 🛠️ Pipeline de Ejecución (Flujo de Trabajo para la IA)

Si necesitas re-procesar, actualizar o extender los datos catastrales, ejecuta los scripts en este orden exacto:

### Paso 1: Regenerar el Catastro Consolidado
```bash
python tools/generate_official_catastre.py
```
- Lee `qgis/Catastro-Limbani.gpkg` (avance usuario) y `insumos/Lotes_Limpios.dxf`.
- Conserva las 334 casas del usuario intactas.
- Genera huellas morfológicas para los lotes vacantes mediante `footprint_generator.py`.
- Produce `qgis/Catastro_Limbani_Oficial.gpkg` y `catastro_limbani.dxf`.

### Paso 2: Empaquetar el Proyecto QGIS
```bash
python tools/create_consolidated_qgz.py
```
- Ensambla `Catastro-Limbani-Consolidado.qgz` enlazando las capas del GeoPackage oficial y el mapa base satelital XYZ de Google.

### Paso 3: Exportar el Modelo KML para Google Earth
```bash
python tools/export_official_kml.py
```
- Convierte de `EPSG:32719` a `EPSG:4326` y actualiza `catastro_limbani.kml`.

### Paso 4: Generar y Revisar el Control Visual
```bash
python tools/render_final_verification.py
```
- Superpone el dibujo CAD sobre `ortofoto_limbani.jpg` y genera las capturas en `verificacion_final/`.
- **IMPORTANTE:** Inspecciona visualmente siempre las imágenes resultantes antes de dar por terminado cualquier cambio.

### Paso 5: Verificar Métricas
```bash
python tools/analyze_coverage.py
```
- Muestra el resumen cuantitativo de viviendas, lotes y áreas construidas.

### Paso 6: Sincronizar Cambios a GitHub
```bash
python tools/push_to_github.py
```
- Sube las modificaciones automáticamente a la rama `main` en GitHub.

---

## 5. 🎨 Especificación de Capas CAD (AutoCAD DXF)

Todo plano DXF exportado debe seguir rigurosamente esta jerarquía de capas:

| Nombre de Capa | Color ACI | Lineweight | Descripción |
| :--- | :---: | :---: | :--- |
| `01_RIOS_Y_CUENCAS` | 140 (Cian/Azul) | 0.35 mm | Cauce del Río Limbani, Río Chinchalamani y quebradas |
| `02_CALLES_Y_VIAS` | 7 (Blanco) | 0.25 mm | Ejes viales urbanos |
| `03_MANZANAS_ROTULOS` | 6 (Magenta) | 0.35 mm | Identificadores oficiales de manzana (A, B, C...) |
| `04_LOTES_PREDIALES` | 7 (Blanco/Gris) | 0.15 mm | Linderos de propiedad de los 623 lotes oficiales |
| `05_HUELLAS_CASAS_USUARIO` | 30 (Naranja) | 0.30 mm | Viviendas digitalizadas manualmente por el usuario |
| `06_HUELLAS_CASAS_COMPLEMENTO` | 4 (Cyan) | 0.25 mm | Huellas residenciales generadas morfológicamente |
| `07_EQUIPAMIENTOS` | 3 (Verde) | 0.40 mm | Áreas públicas (Plaza, Estadio, Parques, Educación, Salud) |
| `08_TOPONIMIA_ROTULOS` | 7 (Blanco) | Normal | Nombres oficiales de jirones, pasajes y avenidas |
| `09_MEMBRETE_DATOS` | 7 (Blanco) | 0.35 mm | Recuadro técnico y metrados en esquina superior derecha |

---

## 6. 💡 Consejos de Buenas Prácticas para el Agente
1. Si agregas nuevas funcionalidades, crea módulos independientes dentro de `tools/`.
2. Mantén todas las rutas relativas basadas en `os.path.dirname(os.path.abspath(__file__))`.
3. Nunca agregues dependencias pesadas que no estén instaladas en el entorno (el entorno cuenta con `shapely`, `ezdxf`, `pyproj`, `opencv-python`, `numpy`).
4. Recuerda que la satisfacción del usuario se basa en el **acabado visual limpio, sin sobreposiciones de texto ni desbordes geométricos**.
