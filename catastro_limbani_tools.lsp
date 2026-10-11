;;; ==========================================================================
;;; RUTINAS AUTOLISP PARA CATASTRO Y ELECTRIFICACION - DISTRITO DE LIMBANI
;;; Creado para: AutoCAD 2020 - 2027
;;; Sistema de Coordenadas: WGS84 UTM Zona 19 Sur
;;; ==========================================================================

;;; 1. Comando: INFO-CATASTRO
(defun c:INFO-CATASTRO ()
  (alert 
    (strcat
      "=== CATASTRO BASE Y RED ELECTRICA - LIMBANI ===\n\n"
      "Ubicacion: Distrito de Limbani, Sandia, Puno\n"
      "Datum / Proyeccion: WGS84 UTM Zona 19 Sur (EPSG 32719)\n"
      "Proyecto: Minihidroelectrica Aislada\n\n"
      "Comandos disponibles:\n"
      "  - CREAR-POSTE   : Coloca postes numerados consecutivamente.\n"
      "  - AISLAR-RED    : Apaga todo y deja solo la red electrica y postes.\n"
      "  - AISLAR-MZ     : Deja solo las manzanas y equipamientos.\n"
      "  - VER-TODO      : Enciende todas las capas del plano.\n"
      "  - AREA-LOTE     : Mide un lote y coloca su rotulo con area m2."
    )
  )
  (princ)
)

;;; 2. Comando: CREAR-POSTE (Inserta poste numerado secuencialmente)
(defun c:CREAR-POSTE (/ pt pnum txt)
  (if (not *num-poste*) (setq *num-poste* 1))
  (setq pt (getpoint "\nSeleccione la ubicacion del Poste proyectado: "))
  (while pt
    ;; Asegurar capa de postes
    (if (not (tblsearch "LAYER" "15_POSTES_PROYECTADOS"))
      (command "_.-LAYER" "_M" "15_POSTES_PROYECTADOS" "_C" "2" "" "")
      (setvar "CLAYER" "15_POSTES_PROYECTADOS")
    )
    ;; Dibujar circulo del poste (radio 1.2m)
    (command "_.CIRCLE" pt 1.2)
    ;; Rotular numero de poste
    (setq txt (strcat "P-" (if (< *num-poste* 10) "0" "") (itoa *num-poste*)))
    (command "_.TEXT" "_J" "_ML" (list (+ (car pt) 2.5) (+ (cadr pt) 1.0)) 2.2 0 txt)
    (princ (strcat "\nPoste " txt " creado."))
    (setq *num-poste* (1+ *num-poste*))
    (setq pt (getpoint "\nSiguiente poste (o Enter para terminar): "))
  )
  (princ)
)

;;; 3. Comando: AISLAR-RED (Apaga otras capas)
(defun c:AISLAR-RED ()
  (command "_.-LAYER" "_OFF" "*" "_Y" "_ON" "12_RED_PRIMARIA_MT,13_RED_SECUNDARIA_BT,14_SUBESTACIONES_SED,15_POSTES_PROYECTADOS,08_VIAS_EJES" "")
  (princ "\n[OK] Capas de red electrica aisladas.")
  (princ)
)

;;; 4. Comando: AISLAR-MZ (Apaga otras capas)
(defun c:AISLAR-MZ ()
  (command "_.-LAYER" "_OFF" "*" "_Y" "_ON" "02_MANZANAS,02_LOTES_INTERNOS,03_EQUIPAMIENTO_PLAZA,04_EQUIPAMIENTO_MERCADO,05_EQUIPAMIENTO_ESTADIO,06_EQUIPAMIENTO_PISCINA,07_EQUIPAMIENTO_CIVICO,16_TEXTOS_ROTULOS" "")
  (princ "\n[OK] Capas de manzanas y catastro aisladas.")
  (princ)
)

;;; 5. Comando: VER-TODO (Enciende todas las capas)
(defun c:VER-TODO ()
  (command "_.-LAYER" "_ON" "*" "")
  (princ "\n[OK] Todas las capas activadas.")
  (princ)
)

;;; 6. Comando: AREA-LOTE (Calcula el area de una polilinea y escribe el texto en el centro)
(defun c:AREA-LOTE (/ ent area pt txt)
  (setq ent (car (entsel "\nSeleccione la polilinea cerrada del lote: ")))
  (if ent
    (progn
      (command "_.AREA" "_O" ent)
      (setq area (getvar "AREA"))
      (setq pt (getpoint "\nPunto donde colocar el texto del Area: "))
      (if pt
        (progn
          (if (not (tblsearch "LAYER" "16_TEXTOS_ROTULOS"))
            (command "_.-LAYER" "_M" "16_TEXTOS_ROTULOS" "_C" "7" "" "")
            (setvar "CLAYER" "16_TEXTOS_ROTULOS")
          )
          (setq txt (strcat (rtos area 2 1) " m2"))
          (command "_.TEXT" "_J" "_MC" pt 2.5 0 txt)
          (princ (strcat "\nArea anotada: " txt))
        )
      )
    )
    (princ "\nNo se selecciono ningun objeto valido.")
  )
  (princ)
)

(princ "\n=======================================================")
(princ "\n Rutinas de Catastro Limbani cargadas con exito.")
(princ "\n Escriba INFO-CATASTRO para ver los comandos disponibles.")
(princ "\n=======================================================\n")
(princ)
