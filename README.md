# Redes

Sistema de monitoreo con un servidor central y dos tipos de agentes: el **cliente** (agente monitoreado) y el **admin** (consola de administración). Ambos descubren al servidor por broadcast UDP y luego se conectan por TCP.

## Cómo levantar todo

```bash
python servidor.py    # en la máquina que actúa de servidor
python cliente_comun.py    # en cada máquina a monitorear
python cliente_admin.py     # en la consola de administración
```

## Agente cliente (`cliente_comun.py`)

El cliente trabaja solo: cada 5 segundos manda métricas de CPU y memoria, cada 1 segundo revisa si superan el umbral que le dio el servidor y manda alertas, y responde con la lista de procesos cuando el servidor se la pide.

La terminal del cliente acepta un único comando:

| Comando | Qué hace |
|---|---|
| `END` | Cierra la conexión con el servidor y termina el proceso. |

Cualquier otro texto se envía tal cual al servidor, que responde `ERROR 400 [BAD REQUEST]`.

Mensajes que el cliente envía por sí solo:

| Mensaje | Cuándo |
|---|---|
| `METRIC CPU <valor>` / `METRIC MEM <valor>` | Cada 5 segundos. |
| `ALERT CPU <valor>` / `ALERT MEM <valor>` | Cada 1 segundo, solo si el valor supera el umbral. |
| `PROC <pid>:<nombre> <pid>:<nombre> ...` | En respuesta a un `GET_PROC` del servidor. |

## Agente admin (`cliente_admin.py`)

La terminal del admin traduce comandos cortos al protocolo del servidor.

| Comando | Se envía como | Respuesta del servidor |
|---|---|---|
| `L` | `LIST_AGENTS` | `AGENTS <cantidad> <id> <id> ...` |
| `P <id>` | `GET_PROC <id>` | `PROC <id> <pid>:<nombre> ...` o `ERROR 504 [AGENT TIMEOUT]` |
| `M <id> CPU` | `GET_METRIC <id> CPU` | `MEASURMENTS <id> CPU <v1> ... <v10>` |
| `M <id> MEM` | `GET_METRIC <id> MEM` | `MEASURMENTS <id> MEM <v1> ... <v10>` |
| `END` | `END` | Cierra la conexión y termina el proceso. |

Las métricas devuelven las últimas 10 mediciones, la más reciente primero.

Errores posibles:

| Respuesta | Motivo |
|---|---|
| `ERROR 400 [BAD REQUEST]` | Comando desconocido o parámetros inválidos. |
| `ERROR 404 [NOT FOUND]` | El `<id>` no corresponde a ningún cliente conectado. |
| `ERROR 504 [AGENT TIMEOUT]` | El cliente no respondió la lista de procesos a tiempo. |
