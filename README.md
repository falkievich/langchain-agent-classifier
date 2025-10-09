# Documentación del Sistema
## Contenido de los Archivos
# Arquitectura General del Sistema

El sistema está diseñado con una arquitectura modular que permite la separación de responsabilidades y la reutilización de componentes. A continuación se describen los módulos principales y su comunicación:

## Módulos Principales

- **Entrada de Usuario:** Captura las solicitudes del usuario.
- **Planificador:** Se encarga de planificar las tareas a realizar.
- **Ejecutor:** Ejecuta las tareas planificadas.
- **Finalizador:** Maneja la finalización de las tareas y la generación de respuestas.
- **Herramientas (Tools):** Proporciona funciones auxiliares que son utilizadas por otros módulos.
- **Wrappers:** Facilitan la interacción con APIs externas o servicios.

## Comunicación entre Módulos
- El **Entrada de Usuario** envía solicitudes al **Planificador**.
- El **Planificador** llama al **Ejecutor** para llevar a cabo las tareas.
- El **Ejecutor** puede utilizar funciones de **Tools** y **Wrappers** según sea necesario.
- Una vez completadas las tareas, el **Ejecutor** notifica al **Finalizador** para que procese los resultados.

---
# Flujo de Ejecución Completo

El flujo de ejecución del sistema se puede desglosar en los siguientes pasos:

1. **Entrada del Usuario:**  
   El usuario realiza una solicitud a través de la interfaz.

2. **Planificación:**  
   La solicitud es recibida por el módulo de **Planificador**.  
   Se determina el conjunto de tareas a realizar.

3. **Ejecución:**  
   El **Planificador** envía las tareas al **Ejecutor**.  
   El **Ejecutor** ejecuta las tareas, utilizando funciones de **Tools** y **Wrappers** según sea necesario.

4. **Finalización:**  
   Una vez completadas las tareas, el **Ejecutor** llama al **Finalizador**.  
   El **Finalizador** procesa los resultados y genera una respuesta.

5. **Respuesta al Usuario:**  
   La respuesta final se envía de vuelta al usuario.

---
# Interacción entre Funciones
Las funciones dentro del sistema interactúan de la siguiente manera:

- **Planificación:**  
  `run_planner` inicia el proceso de planificación.  
  Llama a `execute_plan_parallel` para ejecutar las tareas en paralelo.

- **Ejecución:**  
  `execute_plan_parallel` ejecuta las tareas planificadas.  
  Puede invocar funciones de **Tools** para realizar operaciones específicas.  
  Llama a `run_finalizer` al completar la ejecución.

- **Finalización:**  
  `run_finalizer` procesa los resultados de la ejecución.  
  Genera la respuesta final que será enviada al usuario.

## Diagrama de Flujo de Interacción
```
run_planner
   └──> generate_plan
         └──> execute_plan_parallel
               └──> run_task
                     └──> run_finalizer
                           └──> generate_response
```

---
# Relaciones entre Funciones Principales

A continuación se describen las relaciones entre las funciones principales del sistema:

- `run_planner`:  
  Llama a `execute_plan_parallel` para ejecutar las tareas planificadas.

- `execute_plan_parallel`:  
  Ejecuta las tareas y puede invocar funciones de **Tools**.  
  Al finalizar, llama a `run_finalizer`.

- `run_finalizer`:  
  Procesa los resultados de la ejecución y genera la respuesta final.

## Diagrama de Flujo
```
Entrada de Usuario
       |
       v
   run_planner
       |
       v
execute_plan_parallel
       |
       v
   run_finalizer
       |
       v
Respuesta al Usuario
```

