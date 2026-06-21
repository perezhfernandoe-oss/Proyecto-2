"""
Programa Principal - Proyecto Maquina Expendedora
Maneja la interfaz de usuario, validaciones, flujos de modulos y reportes.
Autores: Gustavo Lujan, George Loutfi, Fernando Perez
"""

import os
from modelos import InventarioControlador, Producto, Tarjeta

# Intentamos importar matplotlib para el modulo de bonos. 
# Si el entorno del laboratorio no lo tiene, el programa funcionara igual.
try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_DISPONIBLE = True
    # Configuracion para evitar que las ventanas bloqueen el script
    plt.ioff() 
except ImportError:
    MATPLOTLIB_DISPONIBLE = False


def inicializar_inventario_defecto(controlador):
    """
    Rellena la maquina con datos iniciales si no existe el archivo local,
    garantizando que el programa entregado tenga un inventario ya llenado.
    """
    datos_base = {
        "A1": ("CocaC", "Coca Cola", 10, "¡Disfruta tu refrescante Coca Cola!"),
        "B1": ("Pepsi", "Pepsi Cola", 8, "¡Toma Pepsi, vive hoy!"),
        "C1": ("Fanta", "Fanta Naranja", 5, "¡Siente el sabor frutal de Fanta!"),
        "D1": ("Malta", "Malta Caracas", 12, "¡Alimenta tu energia con Malta!"),
        "A2": ("Chint", "Chinito Limon", 7, "¡Frescura total con Chinito!"),
        "B2": ("SvnUp", "7 Up", 6, "¡Siete veces mas refrescante!"),
        "C2": ("Goldn", "Golden Sabores", 4, "¡La diversion tiene sabor Golden!"),
        "D2": ("Aquak", "Agua Aqua", 15, "¡Hidratacion pura y natural!"),
        "A3": ("Ruffl", "Ruffles Original", 5, "¡Sabor crujiente con Ruffles!"),
        "B3": ("Dorit", "Doritos Mega", 10, "¡Atrévete a ser un Dorito Donte!"),
        "C3": ("Cheet", "Cheetos Queso", 8, "¡El sabor mas divertido!"),
        "D3": ("Yuqts", "Yuquitas Fritas", 3, "¡El toque criollo de Yuquitas!"),
        "A4": ("Savoy", "Chocolate Savoy", 14, "¡Con sabor venezolano Savoy!"),
        "B4": ("Hrshy", "Hersheys Leche", 9, "¡Un momento dulce con Hersheys!"),
        "C4": ("Snkrs", "Snickers Barra", 11, "¡No eres tu cuando tienes hambre!"),
        "D4": ("Milky", "Milky Way", 6, "¡Viaja a las estrellas con Milky Way!"),
        "A5": ("Flips", "Flips Dulce de Leche", 20, "¡Tu mundo Flips!"),
        "B5": ("Abcts", "Agüita de Coco", 2, "¡Naturalmente saludable!"),
        "C5": ("Fruty", "Fruticos Caramelos", 15, "¡Dulces y aciditos!"),
        "Cnchf": ("Cnchf", "Conchitas Fritas", 0, "¡Crujientes conchas!") 
    }
    
    for coord, (cod, nom, cant, desp) in datos_base.items():
        controlador.matriz_productos[coord] = Producto(cod, nom, cant, desp)
        controlador.historial_stock[cod] = {'inicial': cant, 'vendidos': 0}
        
    controlador.guardar_productos_locales()


def mostrar_catalogo(controlador):
    """
    Modulo 1: Catalogo
    Muestra los productos cargados organizados como una matriz de ajedrez.
    Si el stock es 0, imprime el espacio en blanco.
    """
    print("\n" + "="*45)
    print("      MÁQUINA EXPENDEDORA PREPAGADA")
    print("="*45)
    
    # Identificar todas las filas (numeros) y columnas (letras) presentes en las coordenadas
    columnas = sorted(list(set(c[0] for c in controlador.matriz_productos.keys() if len(c) > 0 and c[0].isalpha())))
    filas = sorted(list(set(c[1:] for c in controlador.matriz_productos.keys() if len(c) > 1 and c[1:].isdigit())), key=int)
    
    if not columnas or not filas:
        print("   [ Máquina vacía por completo ]")
        return

    # Imprimir encabezado de columnas (Letras)
    header = "   " + "      ".join(columnas)
    print(header)
    
    # Imprimir filas
    for f in filas:
        linea = f"{f}  "
        for c in columnas:
            coord = f"{c}{f}"
            if coord in controlador.matriz_productos:
                prod = controlador.matriz_productos[coord]
                # Si se agota, la posicion se imprime en blanco (5 espacios vacios)
                if prod.cantidad > 0:
                    linea += f"{prod.codigo:<5}  "
                else:
                    linea += "       "
            else:
                linea += "       " # Coordenada vacia sin panel asignado
        print(linea)
    print("="*45)


def ejecutar_venta(controlador, coord):
    """
    Modulo 2: Venta
    Procesa la seleccion de un producto mediante su coordenada.
    """
    if coord not in controlador.matriz_productos:
        print("[Error] Coordenada no válida o sin panel divisor asignado.")
        return

    prod = controlador.matriz_productos[coord]
    if prod.cantidad <= 0:
        print(f"[Aviso] El producto '{prod.nombre}' se encuentra agotado.")
        return

    print(f"-> Producto seleccionado: {prod.nombre}")
    print(f"-> Precio: ${prod.precio:.2f}")

    tarjeta_input = input("Introduzca su número de tarjeta (o presione Enter para cancelar): ").strip()
    if not tarjeta_input:
        print("Venta cancelada. Regresando al catálogo.")
        return

    # Encriptacion con la funcion hash integrada para seguridad
    hash_generado = str(hash(tarjeta_input))

    if hash_generado not in controlador.tarjetas:
        print("[Error] Tarjeta no válida o inexistente en el sistema.")
        return          

    tarjeta_obj = controlador.tarjetas[hash_generado]
    
    # Confirmacion final usando el nombre completo del producto
    confirmar = input(f"¿Confirmar la compra de {prod.nombre} por ${prod.precio:.2f}? (S/N): ").strip().upper()
    if confirmar != 'S':
        print("Compra cancelada.")
        return

    # Intentar transaccion con saldo
    if tarjeta_obj.descontar_saldo(prod.precio):
        # Descontar del inventario
        prod.actualizar_stock(prod.cantidad - 1)
        
        # Registrar estadisticas para reportes
        controlador.historial_stock[prod.codigo]['vendidos'] += 1
        controlador.gastos_usuarios[hash_generado] = controlador.gastos_usuarios.get(hash_generado, 0.0) + prod.precio
        
        # Sincronizar cambios inmediatamente en los archivos de texto
        controlador.guardar_productos_locales()
        controlador.guardar_tarjetas_locales()
        
        print("\n[MÁQUINA DISPENSANDO...] ¡Por favor, retire su producto!")
        print(f">>> {prod.despedida} <<<")
        print(f"Saldo restante en tarjeta: ${tarjeta_obj.saldo:.2f}")
    else:
        print(f"[Error] Saldo insuficiente. Saldo actual: ${tarjeta_obj.saldo:.2f}")


def ejecutar_restock(controlador):
    """
    Modulo 3: Restock
    Permite reabastecer inventarios o reasignar paneles divisores de la maquina.
    """
    print("\n--- MENÚ DE RESTOCK ---")
    print("1. Actualizar existencia de inventario")
    print("2. Cambiar producto de posición (Modificar Código)")
    
    opcion = input("Seleccione una opción (1 o 2): ").strip()
    if opcion not in ["1", "2"]:
        print("[Error] Opción inválida.")
        return

    coord = input("Introduzca la coordenada objetivo (ej. A1, E3): ").strip().upper()
    if not coord:
        print("[Error] Coordenada vacía.")
        return

    if opcion == "1":
        # Validacion de entrada numerica segura
        try:
            nueva_cant = int(input("Introduzca la nueva cantidad en existencia: "))
            if nueva_cant < 0:
                print("[Error] La cantidad no puede ser negativa.")
                return
        except ValueError:
            print("[Error] Debe ingresar un número entero válido.")
            return

        if coord in controlador.matriz_productos:
            prod = controlador.matriz_productos[coord]
            prod.actualizar_stock(nueva_cant)
            controlador.historial_stock[prod.codigo]['inicial'] = nueva_cant
            print(f"¡Éxito! Stock de {prod.nombre} actualizado a {nueva_cant}.")
        else:
            print("[Aviso] Esa coordenada no existía. Se interpretará como adición de un nuevo panel divisor.")
            print("Para añadirlo por completo complete los datos usando la opción 2.")
            return

    elif opcion == "2":
        nuevo_cod = input("Introduzca el nuevo código de 5 letras: ").strip()
        if len(nuevo_cod) != 5:
            print("[Error] El código del producto debe contener exactamente 5 letras.")
            return

        nombre_completo = input("Introduzca el nombre completo del producto: ").strip()
        despedida = input("Introduzca el mensaje de despedida: ").strip()
        
        try:
            cantidad_inicial = int(input("Introduzca la cantidad en existencia inicial: "))
            if cantidad_inicial < 0:
                print("[Error] La cantidad no puede ser negativa.")
                return
        except ValueError:
            print("[Error] Debe ingresar un número entero válido.")
            return

        # Creamos o sobreescribimos el producto en esa coordenada (soporta agregar nuevos paneles divisores)
        nuevo_prod = Producto(nuevo_cod, nombre_completo, cantidad_inicial, despedida, precio=1.5)
        controlador.matriz_productos[coord] = nuevo_prod
        controlador.historial_stock[nuevo_cod] = {'inicial': cantidad_inicial, 'vendidos': 0}
        print(f"¡Éxito! Producto {nombre_completo} asignado a la coordenada {coord}.")

    # Guardamos los cambios inmediatamente en el archivo plano local
    controlador.guardar_productos_locales()


def generar_reporte(controlador):
    """
    Modulo 4: Reporte & Bono Opcional
    Crea archivos con informacion de ventas y genera graficos con matplotlib.
    """
    nombre_archivo_rep = "reporte_ventas.txt"
    
    total_unidades_vendidas = sum(datos['vendidos'] for datos in controlador.historial_stock.values())
    dinero_total_cobrado = sum(controlador.tarjetas[h].saldo for h in controlador.tarjetas) # O usar acumulación directa
    
    # Recalculamos el dinero total cobrado basándonos en los gastos registrados por los usuarios
    dinero_total_cobrado = sum(controlador.gastos_usuarios.values())
    total_usuarios_activos = len(controlador.gastos_usuarios)

    with open(nombre_archivo_rep, "w", encoding="utf-8") as f:
        f.write("==================================================\n")
        f.write("         REPORTE DE VENTAS Y AUDITORÍA\n")
        f.write("==================================================\n\n")
        
        f.write("--- Desglose de Productos ---\n")
        for coord, prod in controlador.matriz_productos.items():
            hist = controlador.historial_stock.get(prod.codigo, {'inicial': prod.cantidad, 'vendidos': 0})
            f.write(f"Coordenada {coord} | Código: {prod.codigo} | Nombre: {prod.nombre}\n")
            f.write(f"  -> Unidades cargadas en último stock: {hist['inicial']}\n")
            f.write(f"  -> Unidades vendidas en este ciclo: {hist['vendidos']}\n\n")
            
        f.write("--------------------------------------------------\n")
        f.write(f"Número total de productos vendidos de forma general: {total_unidades_vendidas}\n")
        f.write(f"Cantidad total de dinero cobrado: ${dinero_total_cobrado:.2f}\n")
        f.write("--------------------------------------------------\n\n")
        
        f.write("--- Consumo de Usuarios ---\n")
        for hash_usr, gasto in controlador.gastos_usuarios.items():
            f.write(f"Usuario (Hashed ID: {hash_usr[:10]}...) gastó: ${gasto:.2f}\n")
        f.write(f"\nNúmero total de usuarios únicos que compraron: {total_usuarios_activos}\n")

    print(f"\n[Éxito] Reporte de texto generado con éxito en '{nombre_archivo_rep}'.")

    # --- SECCIÓN BONO (Matplotlib) ---
    if MATPLOTLIB_DISPONIBLE:
        print("Generando archivos gráficos solicitados (Bono)...")
        try:
            # Gráfico de barras: Cargado vs Vendido por producto
            codigos = [p.codigo for p in controlador.matriz_productos.values()]
            cargados = [controlador.historial_stock.get(p.codigo, {'inicial': 0})['inicial'] for p in controlador.matriz_productos.values()]
            vendidos = [controlador.historial_stock.get(p.codigo, {'vendidos': 0})['vendidos'] for p in controlador.matriz_productos.values()]
            
            x = range(len(codigos))
            plt.figure(figsize=(10, 5))
            plt.bar([i - 0.2 for i in x], cargados, width=0.4, label='Cargados', color='blue')
            plt.bar([i + 0.2 for i in x], vendidos, width=0.4, label='Vendidos', color='orange')
            plt.xticks(x, codigos, rotation=45)
            plt.xlabel('Productos')
            plt.ylabel('Cantidad')
            plt.title('Inventario Cargado vs Vendido')
            plt.legend()
            plt.tight_layout()
            plt.savefig('grafico_inventario_barras.png')
            plt.close()

            # Gráfico circular: Gasto por usuario
            if controlador.gastos_usuarios:
                plt.figure(figsize=(6, 6))
                labels = [f"User {h[:5]}" for h in controlador.gastos_usuarios.keys()]
                plt.pie(controlador.gastos_usuarios.values(), labels=labels, autopct='%1.1f%%', startangle=140)
                plt.title('Distribución de Gastos por Usuario')
                plt.savefig('grafico_gastos_circular.png')
                plt.close()
            
            print("¡Gráficas guardadas localmente en formato PNG!")
        except Exception as e:
            print(f"[Aviso] No se pudieron generar las gráficas debido a un error de dibujo ({e}).")
    else:
        print("[Información] La librería matplotlib no está instalada. Se omite la generación de gráficos.")


def main():
    """Función principal que orquesta el ciclo de vida de la aplicación."""
    controlador = InventarioControlador()
    
    # Intentar cargar localmente. Si no existe, creamos la base pre-llenada requerida
    if not os.path.exists(controlador.archivo_productos):
        inicializar_inventario_defecto(controlador)
    else:
        controlador.cargar_datos_locales()
        
    # Sincronización automática con repositorio al arrancar
    controlador.sincronizar_con_repositorio()

    while True:
        mostrar_catalogo(controlador)
        prompt = input("Introduzca código/coordenada de producto, 'RS' para Restock, 'RP' para Reporte (o 'SALIR'): ").strip()
        
        if not prompt:
            continue
            
        opcion_alta = prompt.upper()
        
        if opcion_alta == "SALIR":
            print("Apagando el sistema de la máquina expendedora. ¡Hasta luego!")
            break
        elif opcion_alta == "RS":
            ejecutar_restock(controlador)
        elif opcion_alta == "RP":
            generar_reporte(controlador)
        else:
            # Se asume que ingresó una coordenada de producto (ej: A1)
            ejecutar_venta(controlador, opcion_alta)


if __name__ == "__main__":
    main()
