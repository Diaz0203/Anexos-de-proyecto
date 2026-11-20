# Simulación del sistema de cajas de una tienda Dollarcity en Sincelejo

Material de apoyo del informe final del curso **Simulación de Sistemas** (Ingeniería de Sistemas, CECAR, 2026).

**Autores:** Sofia Marcela Suancha Contreras, Andres Felipe Diaz Oviedo y Amaurys Castro de Arco.
**Docente:** Gean Pablo Mendoza.

Este repositorio contiene los datos de campo, el modelo en FlexSim, los códigos en FlexScript, los resultados del diseño factorial 2³ y los scripts de análisis en Python usados en el informe.

## Estructura

| Carpeta | Contenido |
| --- | --- |
| `datos/` | `registro_campo_30oct2026.xlsx`: registro cronometrado del 30 de octubre de 2026, de 17:00 a 20:00 (hojas Llegadas, Atención y Cajas abiertas).<br>`TablaLlegadas.csv` / `.xlsx`: los 172 clientes atendidos con hora de llegada, minuto desde las 17:00, tipo y número de productos. Es la tabla que lee el modelo. |
| `modelo/` | `Modelo_Factorial.fsm`: modelo en Autodesk FlexSim 2027 (versión educativa) con los parámetros Regla, Caja5 y Empaque.<br>`codigos/`: los códigos en FlexScript de cada desencadenante. |
| `resultados/` | `Modelo_Factorial.sqlite`: base de datos del Experimentador (8 escenarios × 72 réplicas).<br>`Reproducibilidad.sqlite`: corrida repetida de 3 réplicas por escenario.<br>`factorial_576_corridas.csv` y `Resultados_Factorial_576_corridas.xlsx`: resultados por réplica. |
| `analisis/` | `entrada.py`: análisis de los datos de entrada (descriptivo, independencia y ajuste).<br>`simtr.py`: modelo de verificación en Python con las llegadas reales.<br>`analisis_factorial.py`: ANOVA de tres factores, supuestos, plan B, Tukey, Games-Howell, Dunnett y pruebas de verificación. |

## Formato de recolección de datos

| Hoja | Responsable | Campos registrados |
| --- | --- | --- |
| Llegadas | Observador 1 | Hora de llegada a la fila, abandono (sí/no) y observaciones |
| Atención | Observadores 2 y 3 | Caja, inicio de la atención, fin del cobro, salida de la caja, número de productos y medio de pago |
| Cajas abiertas | Observador 1 | Hora de apertura o cierre de cada caja, cajas abiertas y personas en fila cada 15 minutos |

No se registraron nombres ni datos personales de los clientes.

## Tipos de cliente

| Tipo | Productos | Clientes |
| --- | --- | --- |
| 1 | 1 | 48 |
| 2 | 2 a 5 | 87 |
| 3 | 6 o más | 37 |

## Escenarios del diseño factorial 2³

| Escenario | Regla | Caja5 | Empaque |
| --- | --- | --- | --- |
| E1 (base) | 1 | 1 | 1 |
| E2 | 1 | 1 | 2 |
| E3 | 1 | 2 | 1 |
| E4 | 1 | 2 | 2 |
| E5 | 2 | 1 | 1 |
| E6 | 2 | 1 | 2 |
| E7 | 2 | 2 | 1 |
| E8 | 2 | 2 | 2 |

- **Regla:** 1 = abrir las cajas 3 y 4 con 6 y 15 personas en fila; 2 = con 3 y 8.
- **Caja5:** 1 = no se usa; 2 = abre con 20 personas en fila.
- **Empaque:** 1 = en la caja; 2 = mesa de empaque separada (0,5 min de traslado).

## Cómo reproducir

1. Abrir `modelo/Modelo_Factorial.fsm` en FlexSim 2027 o posterior.
2. Para ver un escenario, cambiar los valores en la tabla **Parámetros**, presionar **Reiniciar** y luego **Ejecutar**.
3. Para repetir el experimento, abrir el **Experimentador**, trabajo **Factorial**, y ejecutarlo (72 réplicas, de 0 a 300 min).
4. Para el análisis, desde la carpeta `analisis/`:

```bash
pip install pandas numpy scipy statsmodels openpyxl
python analisis_factorial.py
```
