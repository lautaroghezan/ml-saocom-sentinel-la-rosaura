# Identificación de ambientes de manejo en maíz para silo forrajero mediante Machine Learning y fusión multisensor SAOCOM–Sentinel-2

## Caso de aplicación: Establecimiento La Rosaura, Tandil, provincia de Buenos Aires

**Proyecto Final — Ciencia de Datos II**

**Nivel de madurez tecnológica objetivo: TRL 3 — Prueba de concepto experimental**

---

# 1. Formulación del problema

## 1.1 Contexto y caso de aplicación

El presente proyecto toma como caso de aplicación al **establecimiento La Rosaura**, ubicado en el partido de **Tandil, provincia de Buenos Aires, Argentina**. Se trata de un establecimiento de producción lechera en el que una parte de la superficie productiva se destina a la generación de alimento para el rodeo.

Para el desarrollo del proyecto se dispone de la delimitación geográfica de **16 potreros**, identificados como `L01` a `L16`. Dentro del sistema productivo se distinguen potreros destinados a **pasturas** y potreros utilizados para la producción de **maíz para silo forrajero**.

El uso de un potrero puede modificarse entre campañas agrícolas. Por este motivo, la unidad conceptual de análisis no se limita al potrero como unidad física permanente, sino que considera la combinación:

**Potrero + campaña agrícola + uso del suelo**

El presente trabajo se concentra específicamente en los potreros destinados a la producción de **maíz para silo forrajero**.

## 1.2 Problema productivo

Un lote agrícola no necesariamente presenta condiciones homogéneas en toda su superficie. Dentro de un mismo potrero pueden existir diferencias espaciales y temporales asociadas a múltiples factores, entre ellos las características del suelo, la disponibilidad hídrica, la topografía, la historia de manejo y el desarrollo del cultivo.

Una estrategia convencional de manejo puede representarse como:

**Lote → manejo uniforme**

La agricultura de precisión plantea, en cambio, la posibilidad de avanzar hacia:

**Lote → ambientes diferenciados → manejo diferencial**

Sin embargo, antes de establecer recomendaciones agronómicas diferenciadas resulta necesario determinar si es posible **identificar de manera consistente esa heterogeneidad espacial**.

Este proyecto aborda esa etapa inicial del problema.

## 1.3 Propuesta tecnológica

Se propone desarrollar una metodología basada en la integración de información proveniente de dos sistemas satelitales con características diferentes y potencialmente complementarias:

- **Sentinel-2:** información óptica multiespectral y multitemporal, utilizada para caracterizar la evolución de la cobertura vegetal y generar índices y atributos espectrales.
- **SAOCOM:** información obtenida mediante radar de apertura sintética (SAR) en banda L, que aporta una fuente de observación físicamente diferente de la información óptica.

La integración de ambas fuentes se plantea como una **arquitectura multisensor o constelación virtual SAOCOM–Sentinel-2**.

El proyecto no presupone que la combinación de ambos sensores produzca necesariamente mejores resultados. Uno de sus objetivos experimentales será evaluar si la integración multisensor aporta capacidad adicional de discriminación respecto de la utilización individual de cada fuente.

## 1.4 Preguntas de investigación

La pregunta principal del proyecto es:

> **¿La integración de información óptica multitemporal Sentinel-2 y radar SAR banda L SAOCOM mediante técnicas de Machine Learning permite identificar y discriminar ambientes espacialmente diferenciados dentro de lotes destinados a maíz para silo forrajero?**

De esta pregunta se deriva una segunda pregunta experimental:

> **¿La integración SAOCOM–Sentinel-2 mejora la capacidad de clasificación de dichos ambientes respecto del empleo individual de cada sensor?**

## 1.5 Objetivo general

**Desarrollar una prueba de concepto de Machine Learning que integre información óptica Sentinel-2 y radar SAR banda L SAOCOM para identificar, caracterizar y clasificar ambientes espacialmente diferenciados dentro de lotes destinados a maíz para silo forrajero del establecimiento La Rosaura, como etapa preliminar para el desarrollo futuro de estrategias de fertilización de precisión.**

## 1.6 Objetivos específicos

1. Construir un dataset analítico que integre información proveniente de Sentinel-2 y SAOCOM.
2. Explorar estadísticamente las variables disponibles y su comportamiento espacial y temporal.
3. Desarrollar atributos derivados de las observaciones ópticas y SAR mediante técnicas de ingeniería de atributos.
4. Identificar ambientes estadísticamente diferenciados mediante técnicas de aprendizaje no supervisado.
5. Generar pseudo-etiquetas experimentales que representen los ambientes identificados.
6. Entrenar modelos supervisados de clasificación multiclase utilizando dichas pseudo-etiquetas como variable objetivo.
7. Comparar el desempeño de modelos construidos con Sentinel-2, SAOCOM y la combinación de ambos sensores.
8. Optimizar los hiperparámetros de los modelos seleccionados mediante técnicas de validación cruzada.
9. Evaluar cuantitativamente el desempeño de los modelos mediante métricas de clasificación.
10. Aplicar SHAP para analizar la contribución de las variables a las predicciones.
11. Dejar desarrollado un entorno metodológico y computacional reproducible preparado para comenzar posteriormente su validación con datos reales de campo.

## 1.7 Definición del problema de Machine Learning

El proyecto combina dos etapas de aprendizaje automático.

### Etapa 1 — Aprendizaje no supervisado

En ausencia de una variable agronómica observada que permita clasificar previamente los ambientes, se utilizarán técnicas de **clustering** sobre las variables derivadas de Sentinel-2 y SAOCOM.

De manera simplificada:

**Variables satelitales → clustering → ambientes A/B/C**

Los grupos obtenidos serán considerados **ambientes candidatos o agrupamientos estadísticos**.

Las denominaciones `Ambiente A`, `Ambiente B` y `Ambiente C` no implican una clasificación de alto, medio o bajo potencial productivo.

### Etapa 2 — Aprendizaje supervisado

Los ambientes obtenidos en la etapa anterior serán utilizados como **pseudo-etiquetas experimentales** para construir un problema supervisado.

La variable objetivo será:

**Y = Ambiente {A, B, C}**

Por lo tanto, el problema supervisado principal se define como una tarea de:

**Clasificación multiclase**

## 1.8 Diseño experimental multisensor

Se compararán tres configuraciones:

- **M1 — Sentinel-2:** variables derivadas exclusivamente de información óptica Sentinel-2.
- **M2 — SAOCOM:** variables derivadas exclusivamente de información SAR SAOCOM.
- **M3 — Sentinel-2 + SAOCOM:** integración de las variables provenientes de ambos sensores.

La hipótesis experimental es:

> **H1: el modelo multisensor M3 presenta una capacidad de discriminación superior a los modelos monofuente M1 y M2.**

Esta hipótesis será evaluada experimentalmente y no se asumirá como verdadera de antemano.

## 1.9 Métricas de evaluación

La métrica principal será:

**Macro F1-score**

Como métricas complementarias se utilizarán:

- Accuracy.
- Precision por clase.
- Recall por clase.
- F1-score por clase.
- Matriz de confusión.

La contribución de la integración multisensor podrá analizarse mediante:

**ΔF1 M3-M1 = F1(M3) − F1(M1)**

**ΔF1 M3-M2 = F1(M3) − F1(M2)**

No se establece a priori un valor mínimo arbitrario de F1-score. El objetivo consiste en comparar de manera reproducible las diferentes configuraciones y analizar las diferencias observadas.

## 1.10 Usuarios potenciales

Los principales usuarios potenciales de una futura herramienta derivada de este desarrollo serían:

- productores agropecuarios;
- ingenieros agrónomos y asesores técnicos;
- responsables de planificación y manejo de cultivos.

El modelo se concibe como una futura herramienta de **apoyo a la toma de decisiones** y no como sustituto del diagnóstico agronómico.

## 1.11 Alcance y limitaciones

El presente trabajo se desarrolla íntegramente como una **prueba de concepto en entorno de laboratorio**.

En esta etapa no se dispone de información de campo suficiente para validar agronómicamente los ambientes identificados, particularmente datos georreferenciados de rendimiento, biomasa, análisis de suelo y respuesta del cultivo a diferentes dosis de fertilización.

Por este motivo:

**Ambiente A/B/C ≠ nivel de productividad**

y:

**Ambiente A/B/C ≠ recomendación de dosis de fertilizante**

Los ambientes identificados deben interpretarse como agrupamientos estadísticos obtenidos a partir de las variables utilizadas por el modelo.

**El trabajo presentado finaliza antes de la validación con datos reales de campo.**

La campaña agrícola **2026/27** constituye una etapa posterior al alcance de esta entrega. Durante dicha campaña se prevé comenzar a relevar información agronómica georreferenciada que permita contrastar los ambientes identificados por el modelo con observaciones reales.

## 1.12 Madurez tecnológica

El desarrollo utiliza como referencia conceptual la escala **Technology Readiness Level (TRL)**.

El objetivo de la presente entrega es alcanzar un nivel equivalente a:

### TRL 3 — Prueba de concepto experimental

Para ello se desarrollará el entorno completo de laboratorio:

**Datos satelitales → procesamiento → EDA → ingeniería de atributos → clustering → pseudo-etiquetas → clasificación supervisada → comparación de sensores → optimización → evaluación → explicabilidad**

**El alcance de la presente entrega finaliza en este punto.**

La posterior incorporación de observaciones agronómicas obtenidas durante la campaña 2026/27 permitirá comenzar una nueva etapa de validación con datos reales.

Dicha validación no forma parte de los resultados presentados en este trabajo y será necesaria antes de atribuir significado productivo a los ambientes o utilizar el modelo para realizar recomendaciones de fertilización.

## 1.13 Criterio de éxito

El criterio de éxito de esta etapa no consiste en demostrar una reducción del uso de fertilizante ni un incremento del rendimiento, dado que ambas afirmaciones requerirían evidencia agronómica que actualmente no se encuentra disponible.

El éxito de la prueba de concepto consistirá en desarrollar un pipeline reproducible capaz de:

**observar → integrar → caracterizar → segmentar → clasificar → explicar**

la heterogeneidad espacial detectada mediante información satelital y evaluar cuantitativamente si la integración **SAOCOM + Sentinel-2** mejora la capacidad de discriminación de ambientes respecto del uso individual de cada sensor.

El producto final será, por lo tanto, un **prototipo metodológico y computacional TRL 3**, preparado para iniciar posteriormente su proceso de validación en condiciones reales de campo.

---

## Estado del proyecto

**En desarrollo — Proyecto Final de Ciencia de Datos II**

La presente versión corresponde a la construcción de la prueba de concepto en entorno de laboratorio.

## Estado de los datos — Campaña 2024/25

El proyecto utiliza información satelital real correspondiente a la campaña agrícola 2024/25 del establecimiento La Rosaura, Tandil, provincia de Buenos Aires. La unidad espacial de referencia está constituida por 16 lotes (L01–L16), cuya geometría fue validada y totaliza aproximadamente 165,36 ha.

### SAOCOM

Se identificaron 13 adquisiciones SAOCOM únicas correspondientes al período comprendido entre el 06/08/2024 y el 18/03/2025.

Los productos utilizados corresponden a nivel de procesamiento L1D y polarización cuádruple:

- HH
- HV
- VH
- VV

La auditoría de los productos confirmó la disponibilidad de las cuatro polarizaciones para las 13 adquisiciones y un sistema de referencia espacial homogéneo (EPSG:32721).

Los productos declaran `Sigma0Type = AMPLITUDE`. Para el análisis radiométrico, los valores válidos de amplitud se transformaron a sigma cero en decibeles mediante:

`σ0_dB = 20 × log10(A)`

El dataset SAOCOM agregado a escala de lote contiene 832 registros. Adicionalmente, se construyó un dataset intralote de 11.658 registros:

`13 fechas × 16 lotes × 4 polarizaciones = 832 observaciones`

Para cada combinación fecha–lote–polarización se calcularon estadísticas descriptivas y robustas, incluyendo mediana, media, percentiles 25 y 75, rango intercuartílico, desviación estándar y porcentaje de píxeles válidos.

El control de calidad mostró cobertura válida elevada en toda la serie. Los menores porcentajes se observaron en algunas combinaciones HV/VH, con un mínimo cercano al 88 %, por lo que estas observaciones fueron conservadas sin imputación de valores faltantes.

### Sentinel-2

Para Sentinel-2 se utiliza la colección Level-2A (reflectancia de superficie).

El catálogo correspondiente al período 01/08/2024–30/06/2025 contiene:

- 73 productos Sentinel-2 L2A.
- 69 fechas únicas.
- Primera observación: 05/08/2024.
- Última observación: 26/06/2025.

La diferencia entre productos y fechas se debe a que cuatro fechas presentan dos productos disponibles.

El porcentaje global de nubosidad informado por cada producto se considera únicamente un indicador preliminar. El filtrado local de observaciones ya fue implementado mediante la Scene Classification Layer (SCL) y dataMask, sobre las celdas correspondientes a los 16 lotes de La Rosaura.

### Estado actual del procesamiento

**SAOCOM:** catálogo, geometría, auditoría radiométrica, control de calidad y construcción del dataset multitemporal por lote completados.

**Sentinel-2:** catálogo temporal, filtrado sistemático mediante SCL y dataMask, extracción de índices espectrales y construcción del dataset intralote completados. El dataset contiene 285.177 registros, de los cuales 132.206 presentan índices válidos.

El procesamiento intralote independiente de ambos sensores se encuentra completado. La armonización espacial y temporal entre SAOCOM y Sentinel-2, y la construcción del dataset multisensor integrado, constituyen las siguientes etapas pendientes.

La estrategia experimental comparará:

- **M1:** Sentinel-2.
- **M2:** SAOCOM.
- **M3:** Sentinel-2 + SAOCOM.

La identificación de ambientes mediante clustering tendrá carácter exploratorio. Los grupos obtenidos serán tratados como pseudo-etiquetas (por ejemplo, Ambiente A, B y C) y no como categorías de potencial productivo hasta contar con validación agronómica independiente.

El alcance actual corresponde a una prueba de concepto experimental (TRL 3). La validación con datos de campo constituye una etapa posterior del proyecto.

---

## Actualización metodológica — análisis intralote 2024–2025

### Alcance temporal y espacial

La prueba de concepto correspondiente a Ciencia de Datos II utiliza
exclusivamente observaciones históricas SAOCOM y Sentinel-2 de 2024–2025.

El área de estudio comprende 16 lotes (L01–L16) del establecimiento
La Rosaura, Tandil, provincia de Buenos Aires.

La unidad principal de análisis para la identificación de patrones
espaciales es la celda georreferenciada dentro de cada lote.

Los análisis agregados por lote se conservan como referencia descriptiva
y como estrategia alternativa de análisis.

La campaña 2026–2027 no integra los datos ni la validación de esta entrega.

### Dataset SAOCOM intralote

Se construyó el archivo:

`data/processed/dataset_saocom_intralote.csv`

Contiene 11.658 registros correspondientes a 13 adquisiciones
históricas, 16 lotes y observaciones espaciales intralote.

Incluye coordenadas UTM y retrodispersión expresada en decibeles
para las polarizaciones HH, HV, VH y VV.

La transformación radiométrica aplicada a los valores de amplitud
válidos es `20 * log10(A)`, conforme a la interpretación provisional
de los metadatos disponibles. La calibración radiométrica definitiva
requiere corroboración adicional con la documentación del producto.

El espaciamiento observado de los píxeles SAOCOM es aproximadamente
43–44 metros. Este valor no debe confundirse con la resolución
espacial efectiva del instrumento, que no se considera verificada.

Las adquisiciones SAOCOM de diferentes fechas no necesariamente
comparten la misma grilla espacial. Las comparaciones por celda
requieren procedimientos explícitos de alineación espacial.

### Dataset Sentinel-2 intralote

Se construyó el archivo:

`data/processed/dataset_sentinel2_intralote.csv`

Contiene 285.177 registros, correspondientes a 4.133 celdas
espaciales y 69 fechas.

Se utilizaron observaciones ópticas con grilla de 20 metros y
máscaras de calidad basadas en SCL y dataMask.

Los índices analizados incluyen NDVI, NDRE y NDMI.

Se registraron 132.206 observaciones válidas de índices,
equivalentes aproximadamente al 46,36 % de los registros.

La disponibilidad temporal es heterogénea debido principalmente
a las condiciones de observación óptica y al filtrado de calidad.

El dataset intralote fue contrastado con los resultados agregados
por lote y con los índices calculados previamente.

### Análisis exploratorio de cambios temporales

Se examinaron cambios espaciales y temporales en los lotes
L15 y L16 durante enero y febrero de 2025.

Entre el 29 de enero y el 14 de febrero de 2025,
la polarización HH de SAOCOM registró cambios medianos de:

- L15: -6,431 dB.
- L16: -6,093 dB.

Las proporciones de celdas comparables con descenso fueron:

- L15: 92,31 %.
- L16: 89,09 %.

Las polarizaciones HV, VH y VV también mostraron descensos
predominantes, aunque de diferente magnitud.

Estos cambios son compatibles con modificaciones importantes
de las condiciones observadas por el radar, pero no constituyen
evidencia suficiente para identificar una cosecha, un cultivo
específico o una causa agronómica determinada.

Las disminuciones del NDVI observadas en fechas próximas
constituyen evidencia óptica complementaria, no validación
independiente de una intervención agrícola.

### Estrategia de Machine Learning

Se mantiene el diseño experimental:

- M1: atributos Sentinel-2.
- M2: atributos SAOCOM.
- M3: atributos combinados Sentinel-2 y SAOCOM.

La identificación inicial de ambientes se realizará mediante
aprendizaje no supervisado.

Los grupos obtenidos serán tratados como agrupamientos
estadísticos o ambientes candidatos, sin atribuirles
automáticamente niveles de productividad.

Las pseudo-etiquetas derivadas del clustering podrán utilizarse
para experimentos supervisados de clasificación multiclase.

Las métricas de clasificación, incluido Macro F1-score,
evaluarán la capacidad de reproducir dichas pseudo-etiquetas,
no la exactitud agronómica de los ambientes.

Se deberán controlar las dependencias espaciales y temporales
en el diseño de las particiones de entrenamiento y evaluación,
así como evitar filtraciones de información al generar
pseudo-etiquetas y seleccionar atributos.

La comparación entre modelos monofuente y multisensor
deberá realizarse sobre unidades y particiones comparables.

### Reproducibilidad y limitaciones

Los datasets procesados, scripts, tablas, figuras y metadatos
constituyen los principales productos reproducibles del proyecto.

Los archivos satelitales originales de gran tamaño se mantienen
fuera del repositorio Git convencional.

La reproducción integral desde los productos originales requiere
disponer de esos archivos, sus metadatos y las dependencias
computacionales correspondientes.

No se dispone en esta etapa de etiquetas de cultivo verificadas
en campo, rendimientos georreferenciados ni mediciones agronómicas
independientes que permitan validar el significado productivo
de los agrupamientos.

La cantidad de celdas y fechas no equivale a una cantidad
idéntica de observaciones estadísticamente independientes.

### Trabajo futuro

Una vez concluida la prueba de concepto histórica,
se prevé aplicar el procedimiento desarrollado a imágenes
de la campaña 2026–2027 y contrastar los ambientes candidatos
con observaciones agronómicas georreferenciadas.

También podrá evaluarse la disponibilidad y pertinencia
de productos SAOCOM con otras modalidades de adquisición,
incluida Stripmap, sujeto a su disponibilidad y características
técnicas verificadas.

Estas actividades no forman parte de los resultados
de la entrega actual.
