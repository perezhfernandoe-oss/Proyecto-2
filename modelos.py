"""
Modulo de Modelos y Datos - Proyecto Maquina Expendedora
Contiene las clases fundamentales del sistema y las funciones de persistencia.
Autores: Gustavo Lujan, George Loutfi, Fernando Perez
"""
import json
import urllib.request
import os

class Producto:
    """
    Clase que representa un producto individual en la maquina expendedora.
    """
    def __init__(self, codigo, nombre, cantidad, despedida, precio=0.0):
        self.codigo = codigo          # Codigo de 5 letras (ej. CocaC)
        self.nombre = nombre          # Nombre completo para confirmacion
        self.cantidad = int(cantidad)  # Cantidad disponible en stock
        self.despedida = despedida    # Mensaje de despedida personalizado
        self.precio = float(precio)    # Precio, se actualizara con la API

    def actualizar_stock(self, nueva_cantidad):
        """Actualiza la cantidad disponible del producto."""
        self.cantidad = int(nueva_cantidad)


class Tarjeta:
    """
    Clase que representa una tarjeta prepagada registrada en el sistema.
    """
    def __init__(self, hashed_numero, saldo):
        self.hashed_numero = hashed_numero  # El hash de Python del numero
        self.saldo = float(saldo)

    def descontar_saldo(self, monto):
        """Descuenta el monto del saldo si es suficiente. Retorna True si se logro."""
        if self.saldo >= monto:
            self.saldo -= monto
            return True
        return False


class InventarioControlador:
    """
    Controlador encargado de la lectura/escritura de archivos y conexion a la API.
    """
    def __init__(self, archivo_productos="productos.txt", archivo_tarjetas="tarjetas.txt"):
        self.archivo_productos = archivo_productos
        self.archivo_tarjetas = archivo_tarjetas
        self.matriz_productos = {}  # Coordenada -> Objeto Producto
        self.tarjetas = {}          # Hash -> Objeto Tarjeta
        
        # Historial para el modulo de Reportes (Estructura: {codigo: {'inicial': x, 'vendidos': y}})
        self.historial_stock = {}
        # Historial de gastos por usuario (Estructura: {hash_tarjeta: total_gastado})
        self.gastos_usuarios = {}

    def cargar_datos_locales(self):
        """
        Lee los archivos de texto locales. Si no existen, asume valores vacios
        o por defecto segun los requerimientos.
        """
        # Cargar Productos
        if os.path.exists(self.archivo_productos):
            with open(self.archivo_productos, "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if linea:
                        # Formato esperado: coordenada,codigo,nombre,cantidad,despedida
                        partes = linea.split(",")
                        if len(partes) == 5:
                            coord, cod, nom, cant, desp = partes
                            prod = Producto(cod, nom, cant, desp)
                            self.matriz_productos[coord] = prod
                            # Guardamos la cantidad inicial para el reporte
                            self.historial_stock[cod] = {'inicial': int(cant), 'vendidos': 0}
        else:
            print("[Aviso] Archivo local de productos no encontrado. Maquina vacia.")

        # Cargar Tarjetas Locales por si acaso, aunque el enunciado pide contrastar con el repositorio
        # Inicializamos los hashes conocidos con saldos base si no existe archivo
        if not os.path.exists(self.archivo_tarjetas):
            # Creamos un archivo base simulado con hashes de las tarjetas validas
            # Usamos hashes fijos simulados correspondientes a los numeros de la prueba
            tarjetas_base = {
                str(hash("1234567890")): 50.0,
                str(hash("9876543210")): 100.0,
                str(hash("1223334444")): 20.0,
                str(hash("4444333221")): 15.5,
                str(hash("1010101010")): 200.0
            }
            self.guardar_tarjetas_locales(tarjetas_base)
            
        self._cargar_tarjetas_desde_archivo()

    def _cargar_tarjetas_desde_archivo(self):
        """Metodo interno para rellenar el diccionario de tarjetas desde el archivo local."""
        if os.path.exists(self.archivo_tarjetas):
            with open(self.archivo_tarjetas, "r", encoding="utf-8") as f:
                for linea in f:
                    linea = linea.strip()
                    if linea:
                        h_num, saldo = linea.split(",")
                        self.tarjetas[h_num] = Tarjeta(h_num, saldo)

    def guardar_productos_locales(self):
        """Guarda el estado actual del inventario en el archivo de texto local."""
        with open(self.archivo_productos, "w", encoding="utf-8") as f:
            for coord, prod in self.matriz_productos.items():
                f.write(f"{coord},{prod.codigo},{prod.nombre},{prod.cantidad},{prod.despedida}\n")

    def guardar_tarjetas_locales(self, diccionario_datos=None):
        """Guarda el estado de las tarjetas en el archivo local."""
        with open(self.archivo_tarjetas, "w", encoding="utf-8") as f:
            if diccionario_datos:
                for h_num, saldo in diccionario_datos.items():
                    f.write(f"{h_num},{saldo}\n")
            else:
                for h_num, t_obj in self.tarjetas.items():
                    f.write(f"{h_num},{t_obj.saldo}\n")

    def sincronizar_con_repositorio(self):
        """
        Se conecta a la API de GitHub (simulado mediante URL del repositorio o mock de JSON)
        para actualizar los precios y validar tarjetas prepagadas.
        """
        # El repositorio definitivo deberia proveer un archivo JSON estructurado.
        url_json = "https://raw.githubusercontent.com/FernandoSapient/BPTSP05/2526-3/datos.json"
        
        print("Sincronizando precios y tarjetas con GitHub...")
        try:
            # Peticion HTTP con la libreria estandar de Python
            req = urllib.request.Request(url_json, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as response:
                datos = json.loads(response.read().decode())
                
                # Suponiendo estructura JSON: {"precios": {"CocaC": 2.5, ...}, "tarjetas": {"hash_1": 100, ...}}
                if "precios" in datos:
                    for coord, prod in self.matriz_productos.items():
                        if prod.codigo in datos["precios"]:
                            prod.precio = float(datos["precios"][prod.codigo])
                
                if "tarjetas" in datos:
                    for h_num, saldo in datos["tarjetas"].items():
                        if h_num in self.tarjetas:
                            self.tarjetas[h_num].saldo = float(saldo)
                        else:
                            self.tarjetas[h_num] = Tarjeta(h_num, saldo)
            print("¡Sincronizacion exitosa!")
        except Exception as e:
            print(f"[Aviso] No se pudo conectar al repositorio ({e}). Se mantendran los precios actuales.")
            # Asignamos precios base por defecto si la maquina inicio en 0 y la red fallo
            precios_defecto = {"CocaC": 1.5, "Pepsi": 1.5, "Fanta": 1.2, "Malta": 1.8, "Ruffl": 2.0, "Dorit": 2.2}
            for coord, prod in self.matriz_productos.items():
                if prod.precio == 0.0:
                    prod.precio = precios_defecto.get(prod.codigo, 1.0)
