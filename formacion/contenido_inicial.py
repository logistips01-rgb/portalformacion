"""Contenido de partida del portal.

IMPORTANTE: los textos y preguntas son un BORRADOR DE EJEMPLO para que el portal
funcione desde el primer día. Deben revisarse y sustituirse por el temario oficial
de Aldelis (manual del empleado, APPCC, procedimientos de almacén…) desde «Gestión».

Formato de cada pregunta: (enunciado, [opciones], índice de la correcta, explicación)
"""

AVISO = "Contenido de ejemplo: pendiente de revisar y sustituir por el temario oficial."

DEPARTAMENTOS = {
    "Logística": [
        ("Recepción de mercancías", "Descarga, control e identificación de la mercancía que entra en el almacén."),
        ("Logística interna", "Ubicación, reposición y movimientos de material entre almacén y líneas."),
        ("Registro de producción", "Declaración, etiquetado y paletizado del producto terminado."),
        ("Expediciones", "Preparación de pedidos, carga y documentación de salida."),
    ],
}

CURSOS = [
    # ------------------------------------------------------------------ ACOGIDA
    {
        "codigo": "manual-empleado",
        "titulo": "Manual del empleado",
        "categoria": "acogida",
        "audiencia": "interno",
        "duracion": 30,
        "descripcion": "Quiénes somos, cómo nos organizamos y qué necesitas saber en tu primer día.",
        "temas": [
            ("Bienvenida a Aldelis", f"""{AVISO}

## Quiénes somos
Aquí irá la presentación de la empresa: historia, actividad, centros de trabajo y valores.

## Tu primer día
- Presenta tu DNI en recepción y recoge tu equipo de trabajo.
- Tu responsable te enseñará tu puesto y te presentará al equipo.
- Completa la formación de acogida en este portal durante tu primera semana."""),
            ("Horarios, fichajes y ausencias", f"""{AVISO}

- Ficha siempre al entrar y al salir, también en los descansos si así está establecido.
- Los cambios de turno se solicitan a tu responsable con antelación.
- Comunica cualquier ausencia lo antes posible y entrega el justificante a RR. HH.
- Las vacaciones se solicitan según el calendario que publica RR. HH."""),
            ("Normas de convivencia y canales de comunicación", f"""{AVISO}

- Respeto a compañeros, clientes y proveedores.
- Prohibido fumar fuera de las zonas habilitadas.
- Uso del móvil personal restringido en zonas de producción y almacén.
- Para dudas o incidencias: tu responsable directo, RR. HH. o el canal interno de comunicación."""),
        ],
        "preguntas": [
            ("¿Qué debes hacer si vas a faltar al trabajo?", ["Nada, se justifica a la vuelta", "Avisar lo antes posible y entregar el justificante", "Decírselo a un compañero"], 1, "Avisar cuanto antes permite reorganizar el turno."),
            ("¿Cuándo debes fichar?", ["Solo al entrar", "Al entrar y al salir", "Una vez por semana"], 1, ""),
            ("¿A quién te diriges primero ante una duda sobre tu puesto?", ["A tu responsable directo", "A un cliente", "A nadie"], 0, ""),
            ("¿Dónde está permitido fumar?", ["En cualquier zona exterior", "Solo en las zonas habilitadas", "En el almacén si no hay nadie"], 1, ""),
        ],
    },
    {
        "codigo": "buenas-practicas-manipulacion",
        "titulo": "Buenas prácticas de manipulación",
        "categoria": "acogida",
        "audiencia": "interno",
        "duracion": 45,
        "descripcion": "Higiene personal, prevención de la contaminación y normas básicas en zonas de producto.",
        "temas": [
            ("Higiene personal", f"""{AVISO}

## Antes de entrar en zona de producto
- Lávate las manos con agua y jabón y sécalas con papel de un solo uso.
- Ropa de trabajo limpia y exclusiva, gorro que cubra todo el pelo.
- Sin joyas, relojes, piercings ni uñas postizas o pintadas.

## Cuándo lavarse las manos
- Al entrar en la zona y después de cada descanso.
- Después de ir al aseo, comer, sonarse o tocar residuos.
- Al cambiar de tarea."""),
            ("Prevención de la contaminación", f"""{AVISO}

- Contaminación física: plásticos, madera de palés, cristal, metales. Revisa siempre el estado de embalajes y palés.
- Contaminación química: nunca dejes productos de limpieza junto al producto.
- Contaminación biológica: respeta las temperaturas y los circuitos limpio/sucio.
- Alérgenos: mantén separadas e identificadas las materias primas con alérgenos."""),
            ("Estado de salud y comunicación de incidencias", f"""{AVISO}

- Comunica a tu responsable si tienes diarrea, vómitos, fiebre o heridas infectadas.
- Las heridas se cubren con apósito azul detectable.
- Cualquier anomalía (plagas, roturas, cuerpos extraños) se comunica de inmediato."""),
        ],
        "preguntas": [
            ("¿Cuándo debes lavarte las manos?", ["Solo al empezar el turno", "Al entrar en la zona, tras cada descanso y tras ir al aseo", "Solo si están visiblemente sucias"], 1, ""),
            ("¿Qué se debe hacer con un reloj o una pulsera antes de entrar en zona de producto?", ["Llevarlo por dentro de la manga", "Quitárselo", "Nada"], 1, "Los objetos personales son una fuente de contaminación física."),
            ("Tienes una pequeña herida en un dedo. ¿Qué haces?", ["Nada", "Cubrirla con apósito azul detectable y avisar", "Cubrirla con cinta adhesiva"], 1, ""),
            ("Un trozo de madera de un palé roto es un ejemplo de contaminación…", ["Física", "Química", "Biológica"], 0, ""),
            ("Si tienes vómitos o diarrea, debes…", ["Ir a trabajar igualmente", "Comunicarlo a tu responsable antes de entrar", "Tomar un medicamento y no decir nada"], 1, ""),
        ],
    },
    # -------------------------------------------------------- LOGÍSTICA COMÚN
    {
        "codigo": "seguridad-almacen",
        "titulo": "Seguridad y prevención en el almacén",
        "categoria": "departamento",
        "audiencia": "interno",
        "duracion": 40,
        "descripcion": "Riesgos del almacén, EPI, circulación de carretillas y manipulación manual de cargas.",
        "temas": [
            ("Riesgos principales y EPI", f"""{AVISO}

- Atropellos y golpes con carretillas y transpaletas.
- Caídas de carga desde estanterías.
- Sobreesfuerzos al manipular cajas.

## EPI obligatorios
- Calzado de seguridad.
- Chaleco de alta visibilidad.
- Guantes cuando se manipulen palés o flejes."""),
            ("Circulación y uso de equipos de manutención", f"""{AVISO}

- Circula siempre por las zonas peatonales señalizadas.
- Solo pueden usar carretillas elevadoras las personas formadas y autorizadas.
- Revisa el equipo antes de usarlo (frenos, claxon, horquillas, batería) y comunica cualquier avería.
- Nunca transportes personas ni circules con la carga elevada."""),
            ("Manipulación manual de cargas", f"""{AVISO}

- Flexiona las rodillas, espalda recta y carga pegada al cuerpo.
- No gires el tronco con la carga: mueve los pies.
- Pide ayuda o usa medios mecánicos si la carga pesa más de 25 kg o es voluminosa."""),
        ],
        "preguntas": [
            ("¿Quién puede conducir una carretilla elevadora?", ["Cualquier empleado de almacén", "Solo personal formado y autorizado", "Cualquiera con carné de coche"], 1, ""),
            ("¿Por dónde debes caminar en el almacén?", ["Por el camino más corto", "Por las zonas peatonales señalizadas", "Por los pasillos de carretillas"], 1, ""),
            ("Al levantar una caja del suelo debes…", ["Doblar la espalda con las piernas rectas", "Flexionar las rodillas y mantener la espalda recta", "Levantarla girando el tronco"], 1, ""),
            ("¿Qué EPI es obligatorio en el almacén?", ["Calzado de seguridad y chaleco de alta visibilidad", "Solo guantes", "Ninguno"], 0, ""),
            ("Detectas que los frenos de una transpaleta no funcionan bien. ¿Qué haces?", ["La sigo usando con cuidado", "No la uso y comunico la avería", "Se la dejo a otro compañero"], 1, ""),
        ],
    },
    {
        "codigo": "trazabilidad-lotes",
        "titulo": "Trazabilidad, lotes y registros",
        "categoria": "departamento",
        "audiencia": "interno",
        "duracion": 35,
        "descripcion": "Por qué es clave identificar cada palé y cómo funcionan lotes, caducidades y rotación FEFO.",
        "temas": [
            ("Qué es la trazabilidad", f"""{AVISO}

La trazabilidad permite saber, para cada producto, de dónde viene, qué materias primas lleva y a qué cliente se ha enviado.
Si hay una alerta, nos permite retirar solo los lotes afectados.

- Cada palé debe estar identificado con su etiqueta en todo momento.
- Un palé sin etiqueta se aparta y se comunica: nunca se le pone una etiqueta «a ojo»."""),
            ("Lotes, caducidades y rotación FEFO", f"""{AVISO}

- Lote: conjunto de unidades fabricadas o recibidas en las mismas condiciones.
- FEFO (First Expired, First Out): sale primero lo que caduca antes.
- FIFO (First In, First Out): sale primero lo que entró antes. Se usa cuando no hay fecha de caducidad.
- Revisa siempre la fecha antes de ubicar o preparar un palé."""),
            ("Registros y lectura de etiquetas", f"""{AVISO}

- Los movimientos se registran en el terminal (escáner) en el momento en que se hacen, nunca después.
- Lee el código de la etiqueta del palé y el de la ubicación.
- Si el sistema da un error, no lo fuerces: avisa a tu responsable."""),
        ],
        "preguntas": [
            ("¿Qué significa FEFO?", ["Lo primero que entra, primero sale", "Lo primero que caduca, primero sale", "Lo más pesado sale primero"], 1, ""),
            ("Encuentras un palé sin etiqueta. ¿Qué haces?", ["Le pongo una etiqueta parecida", "Lo aparto y lo comunico", "Lo ubico donde haya hueco"], 1, "Una identificación incorrecta rompe la trazabilidad."),
            ("¿Cuándo se registra un movimiento en el terminal?", ["Al final del turno", "En el momento en que se hace", "Solo si lo pide el responsable"], 1, ""),
            ("¿Para qué sirve la trazabilidad?", ["Para saber el origen y el destino de cada lote", "Para calcular nóminas", "Para nada en concreto"], 0, ""),
        ],
    },
    # -------------------------------------------------------- ESPECÍFICOS DE PUESTO
    {
        "codigo": "recepcion-mercancias",
        "titulo": "Recepción de mercancías",
        "categoria": "puesto",
        "audiencia": "interno",
        "duracion": 45,
        "puesto": "Recepción de mercancías",
        "descripcion": "Cómo descargar, inspeccionar, registrar y ubicar la mercancía que llega al almacén.",
        "temas": [
            ("Llegada del camión y descarga", f"""{AVISO}

- Comprueba el pedido de compra y la documentación (albarán) antes de descargar.
- Asegura el camión: calzos, freno y conexión al muelle.
- Revisa la temperatura del camión si la mercancía es refrigerada y anótala."""),
            ("Inspección en recepción", f"""{AVISO}

- Cantidad: bultos y palés coinciden con el albarán.
- Estado: embalajes sin roturas, humedad ni suciedad; palés en buen estado.
- Producto: lote y fecha de caducidad legibles y con vida útil suficiente.
- Ante cualquier no conformidad: anótala en el albarán, haz foto y avisa a Calidad."""),
            ("Registro y ubicación", f"""{AVISO}

- Da de alta la entrada en el sistema y etiqueta cada palé.
- La mercancía rechazada o pendiente de revisión se coloca en la zona de bloqueo, identificada.
- Ubica los palés según indique el terminal."""),
        ],
        "preguntas": [
            ("Antes de descargar un camión debes…", ["Comprobar la documentación y asegurar el camión", "Empezar a descargar cuanto antes", "Firmar el albarán"], 0, ""),
            ("Un palé llega con el film roto y cajas húmedas. ¿Qué haces?", ["Lo acepto igualmente", "Lo anoto en el albarán, hago foto y aviso a Calidad", "Lo devuelvo sin decir nada"], 1, ""),
            ("¿Dónde se coloca la mercancía pendiente de revisión?", ["En la zona de bloqueo, identificada", "En cualquier hueco libre", "En el muelle de expediciones"], 0, ""),
            ("En mercancía refrigerada, ¿qué hay que comprobar al llegar?", ["El color del camión", "La temperatura del camión y del producto", "Nada especial"], 1, ""),
            ("¿Qué datos del producto debes revisar en la recepción?", ["Lote y fecha de caducidad", "Solo el nombre del proveedor", "El precio"], 0, ""),
        ],
    },
    {
        "codigo": "logistica-interna",
        "titulo": "Logística interna",
        "categoria": "puesto",
        "audiencia": "interno",
        "duracion": 40,
        "puesto": "Logística interna",
        "descripcion": "Ubicaciones, reposición a línea y movimientos internos de material.",
        "temas": [
            ("Mapa del almacén y ubicaciones", f"""{AVISO}

- Cada ubicación tiene un código (pasillo, módulo, altura).
- Respeta la carga máxima de cada estantería, indicada en su placa.
- Los palés no deben sobresalir del hueco ni bloquear pasillos."""),
            ("Reposición a líneas de producción", f"""{AVISO}

- Atiende las peticiones de material de las líneas según prioridad.
- Sirve siempre el lote que indique el sistema (FEFO).
- Retira los palés vacíos y los residuos de la zona de línea."""),
            ("Inventarios y movimientos", f"""{AVISO}

- Cualquier movimiento de palé se registra con el terminal.
- Si encuentras una diferencia de stock, no la corrijas por tu cuenta: comunícala.
- Participa en los recuentos cíclicos siguiendo las instrucciones."""),
        ],
        "preguntas": [
            ("¿Dónde se indica la carga máxima de una estantería?", ["En su placa de características", "No existe límite", "En el albarán"], 0, ""),
            ("Al reponer material a línea, ¿qué lote se sirve?", ["El que esté más cerca", "El que indique el sistema (FEFO)", "El más nuevo"], 1, ""),
            ("Detectas una diferencia de stock en una ubicación. ¿Qué haces?", ["La corrijo yo en el sistema", "La comunico a mi responsable", "La ignoro"], 1, ""),
            ("¿Puede un palé sobresalir del hueco de la estantería?", ["Sí, si es poco", "No", "Solo en el nivel del suelo"], 1, ""),
        ],
    },
    {
        "codigo": "registro-produccion",
        "titulo": "Registro de producción",
        "categoria": "puesto",
        "audiencia": "interno",
        "duracion": 40,
        "puesto": "Registro de producción",
        "descripcion": "Declaración del producto terminado, etiquetado de palés y control de la producción.",
        "temas": [
            ("Declaración de la producción", f"""{AVISO}

- Cada palé de producto terminado se declara en el sistema al finalizarlo.
- Comprueba que la orden de fabricación, el producto y el lote son los correctos.
- Las cantidades declaradas deben coincidir con lo paletizado."""),
            ("Etiquetado y paletizado", f"""{AVISO}

- La etiqueta se coloca en el lugar indicado, visible y sin arrugas.
- Comprueba que la información impresa (producto, lote, caducidad, cantidad) es correcta.
- Paletiza según el esquema de carga del producto y fleja/enfilma correctamente."""),
            ("Producto no conforme", f"""{AVISO}

- Si detectas producto defectuoso o una etiqueta errónea, bloquea el palé y avisa a Calidad.
- Nunca mezcles lotes distintos en un mismo palé salvo que esté autorizado.
- Anota las incidencias en el registro del turno."""),
        ],
        "preguntas": [
            ("¿Cuándo se declara un palé de producto terminado?", ["Al finalizarlo", "Al final de la semana", "Cuando se expide"], 0, ""),
            ("La etiqueta impresa tiene un lote incorrecto. ¿Qué haces?", ["La dejo, nadie se dará cuenta", "Bloqueo el palé y aviso", "La corrijo a bolígrafo"], 1, ""),
            ("¿Se pueden mezclar lotes distintos en un palé?", ["Sí, siempre", "Solo si está autorizado", "Sí, si es el mismo producto"], 1, ""),
            ("¿Qué información debes revisar en la etiqueta?", ["Producto, lote, caducidad y cantidad", "Solo el producto", "Solo el código de barras"], 0, ""),
        ],
    },
    {
        "codigo": "expediciones",
        "titulo": "Expediciones",
        "categoria": "puesto",
        "audiencia": "interno",
        "duracion": 45,
        "puesto": "Expediciones",
        "descripcion": "Preparación de pedidos, control de carga y documentación de salida.",
        "temas": [
            ("Preparación de pedidos (picking)", f"""{AVISO}

- Prepara los pedidos siguiendo la orden del terminal.
- Respeta el lote propuesto por el sistema (FEFO) y la vida útil mínima que pide cada cliente.
- Lee cada palé o caja con el escáner: así se evitan errores de producto y cantidad."""),
            ("Control y carga del camión", f"""{AVISO}

- Antes de cargar revisa el camión: limpio, sin olores y a la temperatura correcta.
- Comprueba palé a palé que corresponde al pedido.
- Carga según el orden de descargas y asegura la carga para que no se desplace."""),
            ("Documentación de salida", f"""{AVISO}

- Imprime y revisa el albarán y, si aplica, el CMR.
- Anota la temperatura del camión y las incidencias.
- El transportista firma la recepción de la mercancía; guarda la copia según el procedimiento."""),
        ],
        "preguntas": [
            ("¿Qué lote se prepara para un pedido?", ["El que propone el sistema (FEFO)", "El más reciente", "Cualquiera"], 0, ""),
            ("El camión llega sucio y con olor. ¿Qué haces?", ["Cargo igualmente", "No cargo y aviso a mi responsable", "Lo limpio con producto de la línea"], 1, ""),
            ("¿Por qué se escanea cada palé al cargar?", ["Para evitar errores de producto y cantidad", "Porque lo pide el transportista", "No es necesario"], 0, ""),
            ("¿En qué orden se cargan los palés?", ["Al azar", "Según el orden de descargas de la ruta", "Primero los más ligeros"], 1, ""),
            ("¿Qué documento acompaña habitualmente a la mercancía?", ["El albarán", "La nómina", "El parte de horas"], 0, ""),
        ],
    },
    # -------------------------------------------------------- EXTERNOS
    {
        "codigo": "normas-personal-externo",
        "titulo": "Normas de acceso y seguridad para personal externo",
        "categoria": "externo",
        "audiencia": "externo",
        "duracion": 20,
        "descripcion": "Obligatoria para transportistas, contratas y visitas antes de acceder a las instalaciones.",
        "temas": [
            ("Acceso a las instalaciones", f"""{AVISO}

- Identifícate en recepción y lleva siempre visible la acreditación.
- Accede solo a las zonas autorizadas y acompañado si así se indica.
- Respeta la señalización y los límites de velocidad dentro del recinto."""),
            ("Higiene y seguridad", f"""{AVISO}

- Usa los EPI y la ropa que se te indique (chaleco, calzado, gorro, bata).
- Prohibido comer, beber o fumar fuera de las zonas habilitadas.
- Transportistas: permanece en la zona de espera durante la carga/descarga salvo indicación.
- En caso de emergencia, sigue las indicaciones del personal de Aldelis y dirígete al punto de reunión."""),
        ],
        "preguntas": [
            ("¿Qué debes hacer al llegar a las instalaciones?", ["Ir directamente al muelle", "Identificarte en recepción", "Esperar en el coche"], 1, ""),
            ("¿Dónde debes permanecer durante la carga si eres transportista?", ["Dentro del almacén", "En la zona de espera, salvo indicación", "Donde quiera"], 1, ""),
            ("En caso de emergencia…", ["Sigue las indicaciones del personal y ve al punto de reunión", "Sal por donde puedas", "Quédate en tu puesto"], 0, ""),
        ],
    },
]

ITINERARIOS = [
    {
        "nombre": "Acogida Aldelis",
        "descripcion": "Obligatorio para todas las nuevas incorporaciones durante la primera semana.",
        "orden": 1,
        "para_todo_interno": True,
        "cursos": [("manual-empleado", 7), ("buenas-practicas-manipulacion", 7)],
    },
    {
        "nombre": "Logística · formación común",
        "descripcion": "Común a todos los puestos de logística.",
        "orden": 2,
        "departamentos": ["Logística"],
        "cursos": [("seguridad-almacen", 14), ("trazabilidad-lotes", 14)],
    },
    {"nombre": "Puesto · Recepción de mercancías", "orden": 3, "puestos": ["Recepción de mercancías"], "cursos": [("recepcion-mercancias", 30)]},
    {"nombre": "Puesto · Logística interna", "orden": 3, "puestos": ["Logística interna"], "cursos": [("logistica-interna", 30)]},
    {"nombre": "Puesto · Registro de producción", "orden": 3, "puestos": ["Registro de producción"], "cursos": [("registro-produccion", 30)]},
    {"nombre": "Puesto · Expediciones", "orden": 3, "puestos": ["Expediciones"], "cursos": [("expediciones", 30)]},
    {
        "nombre": "Personal externo",
        "descripcion": "Obligatorio antes de acceder a las instalaciones.",
        "orden": 1,
        "para_externos": True,
        "cursos": [("normas-personal-externo", 0)],
    },
]
