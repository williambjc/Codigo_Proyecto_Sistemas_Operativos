import threading
import time
import random

inventario = {
    "tomate": 15,
    "queso": 10,
    "pan": 25,
    "carne": 12
}

lock_inventario = threading.Lock()

class Chef(threading.Thread):
    def __init__(self, id_chef, pedidos_asignados):
        super().__init__()
        self.id_chef = id_chef
        self.pedidos_asignados = pedidos_asignados

    def run(self):
        for plato, receta in self.pedidos_asignados:
            print(f"[Chef {self.id_chef}] Intentando preparar: {plato} (Requiere: {receta})")
            time.sleep(random.uniform(1.0, 2.0))
            
            with lock_inventario:
                puede_preparar = True
                for ingrediente, cantidad_necesaria in receta.items():
                    if inventario.get(ingrediente, 0) < cantidad_necesaria:
                        puede_preparar = False
                        break
                
                if puede_preparar:
                    for ingrediente, cantidad_necesaria in receta.items():
                        inventario[ingrediente] -= cantidad_necesaria
                    print(f"-> [ÉXITO] Chef {self.id_chef} preparó: {plato}. Inventario actual: {inventario}")
                else:
                    print(f"-> [ESPERA/CANCELADO] Chef {self.id_chef} no pudo preparar {plato} por falta de stock. Inventario: {inventario}")
            
            time.sleep(random.uniform(0.5, 1.5))

def main():
    print("=== INICIO DE LA SIMULACIÓN: RESTAURANTE CON GESTIÓN DE PEDIDOS ===")
    print(f"Inventario inicial compartido: {inventario}\n")
    
    recetas_menu = {
        "Hamburguesa Clásica": {"pan": 2, "carne": 1, "tomate": 1, "queso": 1},
        "Pizza Mediana": {"queso": 3, "tomate": 2, "pan": 1},
        "Sandwich Especial": {"pan": 2, "queso": 1, "tomate": 1}
    }
    
    pedidos_chef_1 = [
        ("Hamburguesa Clásica", recetas_menu["Hamburguesa Clásica"]),
        ("Sandwich Especial", recetas_menu["Sandwich Especial"])
    ]
    pedidos_chef_2 = [
        ("Pizza Mediana", recetas_menu["Pizza Mediana"]),
        ("Hamburguesa Clásica", recetas_menu["Hamburguesa Clásica"])
    ]
    pedidos_chef_3 = [
        ("Sandwich Especial", recetas_menu["Sandwich Especial"]),
        ("Pizza Mediana", recetas_menu["Pizza Mediana"])
    ]
    
    chef1 = Chef(id_chef=1, pedidos_asignados=pedidos_chef_1)
    chef2 = Chef(id_chef=2, pedidos_asignados=pedidos_chef_2)
    chef3 = Chef(id_chef=3, pedidos_asignados=pedidos_chef_3)
    
    chef1.start()
    chef2.start()
    chef3.start()
    
    chef1.join()
    chef2.join()
    chef3.join()
    
    print(f"\n=== FIN DE LA SIMULACIÓN ===\nInventario final resultante: {inventario}")

if __name__ == "__main__":
    main()