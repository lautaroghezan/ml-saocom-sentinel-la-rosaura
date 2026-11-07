# Identificación exploratoria de ambientes de manejo en maíz para silo

## Fusión multisensor SAOCOM–Sentinel-2

**Establecimiento La Rosaura — Tandil, Buenos Aires, Argentina**

Trabajo final de Ciencia de Datos II.

## 1. Resumen

Este proyecto desarrolla una prueba de concepto de integración
de imágenes ópticas Sentinel-2 y radar SAOCOM para explorar
patrones espaciales y temporales en los lotes L15 y L16 del
establecimiento La Rosaura.

Se utilizan observaciones históricas de la campaña 2024–2025.
El cultivo de maíz para silo y una cosecha durante febrero
de 2025 son supuestos agronómicos aportados al estudio,
no hechos verificados mediante registros de campo.

Los agrupamientos identificados representan diferencias
espectrales y radar. No constituyen zonas de rendimiento
ni recomendaciones de fertilización validadas.

## 2. Objetivos

- Integrar información óptica y radar sobre una grilla espacial común.
- Explorar agrupamientos intralote mediante KMeans.
- Comparar configuraciones ópticas, radar y multisensor.
- Analizar robustez frente a semillas, variables y fechas.
- Entrenar clasificadores supervisados de pseudoetiquetas.
- Evaluar la sensibilidad a particiones espaciales.
- Interpretar modelos mediante SHAP.
- Cuantificar la complementariedad temporal entre sensores.

## 3. Datos y procesamiento

### Sentinel-2

Se procesaron índices NDVI, NDRE y NDMI con filtrado
de observaciones válidas mediante SCL y dataMask.

### SAOCOM

Se procesaron las polarizaciones HH, HV, VH y VV.

Las amplitudes originales se reproyectaron a una grilla
común antes de transformarse provisionalmente mediante
20 log10(amplitud). No se verificó la calibración
radiométrica absoluta.

### Integración

- Sistema de referencia: EPSG:32721.
- Tamaño nominal de celda: 44 × 44 metros.
- L15: 52 celdas.
- L16: 55 celdas.
- Total: 107 celdas.
- Ventana de emparejamiento: ±5 días.
- Cobertura óptica mínima: 50 %.

La grilla es una unidad analítica y no representa
necesariamente la resolución espacial efectiva de SAOCOM.

## 4. Aprendizaje no supervisado

Se aplicó KMeans por lote, utilizando variables
temporales resumidas mediante mediana y desviación
estándar.

Se compararon configuraciones ópticas y multisensor,
con estandarización de atributos y balance entre
bloques óptico y radar.

Resultados intralote:

| Lote | k | Silueta óptica | Silueta multisensor | ARI |
|---|---:|---:|---:|---:|
| L15 | 2 | 0.443 | 0.253 | 0.921 |
| L16 | 2 | 0.580 | 0.423 | 1.000 |

La coincidencia global fue de 106 de 107 celdas
entre los agrupamientos óptico y multisensor.

La incorporación de radar no produjo una modificación
sustancial de los agrupamientos intralote.

## 5. Robustez

Se evaluaron:

- Variaciones de inicialización de KMeans.
- Exclusión individual de variables.
- Exclusión individual de fechas de adquisición.

Los resultados muestran sensibilidad a determinadas
variables y fechas, especialmente en L15.

No se evaluó estabilidad entre campañas agrícolas
independientes.

## 6. Clasificación supervisada

Se entrenaron modelos para reproducir las pseudoetiquetas
obtenidas mediante clustering.

Se aplicaron validación cruzada, optimización anidada
de hiperparámetros y pruebas con particiones espaciales.

En la comparación espacial con el mismo objetivo,
la regresión logística multisensor no superó a
la configuración óptica.

Las pseudoetiquetas se construyeron con las mismas
familias de variables utilizadas posteriormente
en clasificación. Por tanto, las métricas no
representan validación predictiva agronómica
independiente.

La concentración espacial de las clases y el
número reducido de celdas limitan las inferencias.

## 7. Complementariedad temporal

| Indicador | L15 | L16 |
|---|---:|---:|
| Fechas con datos ópticos válidos | 33 | 34 |
| Fechas con datos radar válidos | 13 | 13 |
| Fechas de observación en la unión | 45 | 46 |
| Fechas adicionales radar | 12 | 12 |

Se identificaron **294 observaciones celda-fecha
radar sin pareja óptica válida dentro de ±5 días**,
equivalentes al 21,1 % de las 1.391 observaciones
radar consideradas.

Las fechas adicionales representan oportunidades
de observación, no cobertura diaria continua.
La ausencia de datos ópticos no implica
necesariamente nubosidad.

## 8. Explicabilidad SHAP

Se utilizó SHAP para interpretar modelos de
regresión logística entrenados con pseudoetiquetas
ópticas.

En L15 predominan NDRE y NDVI medianos.
En L16 adquieren importancia la variabilidad
temporal y la mediana de NDMI.

Las variables radar participan en el modelo
multisensor, pero su importancia SHAP no
demuestra una mejora predictiva.

## 9. Hipótesis y conclusiones

**H1 — Complementariedad observacional:**
respaldada descriptivamente por fechas y
observaciones radar adicionales.

**H2 — Complementariedad informacional:**
se identificaron diferencias entre las señales
ópticas y radar, sin demostrar utilidad
agronómica adicional.

**H3 — Mejora de delimitación de ambientes:**
no demostrada con los resultados disponibles.

**H4 — Estabilidad interanual:**
pendiente de evaluación futura.

La principal contribución comprobada de la
constelación virtual es ampliar las oportunidades
de observación disponibles, sin demostrar
una mejora de clasificación en los experimentos
espaciales realizados.

## 10. Limitaciones

- Dos lotes y 107 celdas analíticas.
- Ausencia de etiquetas agronómicas independientes.
- Dependencia espacial y temporal entre muestras.
- Clases minoritarias con pocos ejemplos.
- Calibración radar absoluta no verificada.
- Ausencia de datos de rendimiento, suelo y manejo.
- Sin validación interanual.
- Las observaciones radar no sustituyen índices ópticos.

## 11. Reproducibilidad

Notebook principal:

`notebooks/analisis_final_L15_L16.ipynb`

Resultados:

- `data/processed/`
- `reports/tables/`
- `reports/figures/`

El notebook reúne la metodología, los resultados
tabulados y las figuras. Las etapas completas
de procesamiento y entrenamiento se conservan
en los scripts Python del repositorio.

Para ejecutar el notebook se requiere un entorno
Python con pandas, numpy, matplotlib, scikit-learn,
SHAP, Jupyter y sus dependencias.

Los archivos originales SAOCOM de gran tamaño
se almacenan fuera del repositorio y deben
obtenerse por separado para reproducir
íntegramente el procesamiento desde los datos
brutos.

## 12. Alcance del proyecto

Este trabajo constituye una prueba de concepto
metodológica de integración multisensor.

No produce mapas validados de productividad,
prescripciones de fertilización ni estimaciones
de rendimiento.

Una aplicación operativa futura requerirá
calibración, datos de campo, nuevas campañas
y evaluación independiente.
