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