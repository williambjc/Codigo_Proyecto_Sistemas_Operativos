import threading

# Clase que guarda los ingredientes del restaurante.
class Inventario:
    def __init__(self, tipo):
        self.tipo = tipo
        self.lock = threading.Lock()

        if tipo == "basico":
            # Tipo basico: cantidades separadas con variables enteras.
            self.pollo = 1
            self.carne = 8
            self.arroz = 10
            self.papas = 12
        else:
            # Tipo complejo: todos los ingredientes en un diccionario.
            self.ingredientes = {
                "pollo": 5,
                "arroz": 10,
                "carne": 8,
                "papas": 12
            }
            # Tambien tenemos platos que ya estan preparados en masa.
            self.platos_preparados = {"lasana": 1}

    def consultar_ingredientes(self, nombre):
        if self.tipo == "basico":
            return getattr(self, nombre, 0)
        return self.ingredientes.get(nombre, 0)

    def verificar_ingredientes(self, nombre, cantidad):
        return self.consultar_ingredientes(nombre) >= cantidad

    def reservar_ingredientes(self, nombre, cantidad, usar_lock, barrera=None):
        if usar_lock:
            # El Lock se adquiere aqui y se libera al salir del with.
            with self.lock:
                return self._descontar_ingrediente(nombre, cantidad)
        return self._descontar_ingrediente(nombre, cantidad, barrera)

    def _descontar_ingrediente(self, nombre, cantidad, barrera=None):
        # SECCION CRITICA: consultar, validar y actualizar el inventario.
        disponible = self.consultar_ingredientes(nombre)  # 1. Consultar
        alcanza = disponible >= cantidad                 # 2. Validar
        if barrera is not None:
            barrera.wait()  # Solo para provocar el conflicto en la demostracion.
        if alcanza:
            if self.tipo == "basico":
                setattr(self, nombre, disponible - cantidad)  # 3. Actualizar
            else:
                self.ingredientes[nombre] = disponible - cantidad
            return True
        return False

    def reservar_plato_preparado(self, nombre, usar_lock, barrera=None):
        if usar_lock:
            with self.lock:
                return self._descontar_plato(nombre)
        return self._descontar_plato(nombre, barrera)

    def _descontar_plato(self, nombre, barrera=None):
        # SECCION CRITICA: consultar, validar y descontar un plato ya hecho.
        disponible = self.platos_preparados.get(nombre, 0)  # 1. Consultar
        alcanza = disponible >= 1                          # 2. Validar
        if barrera is not None:
            barrera.wait()
        if alcanza:
            self.platos_preparados[nombre] = disponible - 1  # 3. Actualizar
            return True
        return False


# Clase que representa un pedido de un cliente.
class Pedido:
    def __init__(self, id_pedido, plato, cantidad=1, receta=None):
        self.id_pedido = id_pedido
        self.plato = plato
        self.cantidad = cantidad
        self.receta = receta or {}
        self.estado = "pendiente"

    def consultar_estado(self):
        return self.estado

    def cambiar_estado(self, nuevo_estado):
        self.estado = nuevo_estado


# Clase que administra los pedidos pendientes.
class GestorPedidos:
    def __init__(self, pedidos):
        self.pedidos = pedidos
        self.lock = threading.Lock()

    def agregar_pedido(self, pedido):
        with self.lock:
            self.pedidos.append(pedido)

    def obtener_pedido(self):
        # Se protege la lista para no entregar el mismo pedido dos veces.
        with self.lock:
            if self.pedidos:
                return self.pedidos.pop(0)
        return None

    def consultar_pedidos(self):
        with self.lock:
            return len(self.pedidos)


# Cada cocinero es un hilo que atiende un pedido.
class Cocinero(threading.Thread):
    def __init__(self, nombre, inventario, gestor_pedidos, usar_lock, barrera=None):
        super().__init__()
        self.nombre = nombre
        self.inventario = inventario
        self.gestor_pedidos = gestor_pedidos
        self.usar_lock = usar_lock
        self.barrera = barrera
        self.resultado = False

    def run(self):
        print(f"[INICIO] {self.nombre}")
        pedido = self.gestor_pedidos.obtener_pedido()
        if pedido is not None:
            self.preparar_pedido(pedido)
        print(f"[FIN] {self.nombre}")

    def preparar_pedido(self, pedido):
        if pedido.plato == "lasana":
            # La lasana ya estaba preparada en masa.
            self.resultado = self.inventario.reservar_plato_preparado(
                "lasana", self.usar_lock, self.barrera
            )
        else:
            # En la prueba basica se necesita una porcion de pollo.
            self.resultado = self.inventario.reservar_ingredientes(
                "pollo", 1, self.usar_lock, self.barrera
            )

        if self.resultado:
            pedido.cambiar_estado("completado")
            print(f"{self.nombre}: pedido {pedido.id_pedido} atendido")
        else:
            pedido.cambiar_estado("sin ingredientes")
            print(f"{self.nombre}: pedido {pedido.id_pedido} sin disponibilidad")


def probar(tipo, usar_lock):
    print(f"\n--- {tipo.upper()} / {'CON LOCK' if usar_lock else 'SIN LOCK'} ---")

    # Los dos cocineros reciben EL MISMO inventario y el mismo gestor.
    inventario = Inventario(tipo)
    nombre_plato = "pollo" if tipo == "basico" else "lasana"
    pedidos = [Pedido(1, nombre_plato), Pedido(2, nombre_plato)]
    gestor = GestorPedidos(pedidos)

    # Sin Lock, ambos hilos leen antes de descontar para mostrar el problema.
    barrera = None if usar_lock else threading.Barrier(2)
    cocineros = [
        Cocinero("Cocinero 1", inventario, gestor, usar_lock, barrera),
        Cocinero("Cocinero 2", inventario, gestor, usar_lock, barrera)
    ]

    for cocinero in cocineros:
        cocinero.start()
    for cocinero in cocineros:
        cocinero.join()

    reservas = sum(cocinero.resultado for cocinero in cocineros)
    if tipo == "basico":
        stock = inventario.consultar_ingredientes("pollo")
    else:
        stock = inventario.platos_preparados["lasana"]

    print(f"Reservas confirmadas: {reservas}")
    print(f"Cantidad final: {stock}")
    if reservas > 1:
        print("PROBLEMA: dos cocineros reservaron la misma ultima unidad")
    else:
        print("CORRECTO: no hubo reserva duplicada")


if __name__ == "__main__":
    probar("basico", False)
    probar("basico", True)
    probar("complejo", False)
    probar("complejo", True)
