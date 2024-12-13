from PIL import Image, ImageDraw

# Leer el archivo y cargar los datos
def leer_datos(archivo):
    datos = []
    with open(archivo, 'r') as f:
        for linea in f:
            # Dividir la línea en tres columnas (x, y, color)
            x, y, color = map(int, linea.split())
            datos.append((x, y, color))
    return datos

# Crear la imagen a partir de los datos
def crear_imagen(datos, ancho_celda=20, alto_celda=20):
    # Obtener las dimensiones máximas del eje x e y
    max_x = max(d[0] for d in datos)
    max_y = max(d[1] for d in datos)
    
    # Crear una imagen con el tamaño adecuado
    ancho = max_x * ancho_celda
    alto = max_y * alto_celda
    imagen = Image.new("RGB", (ancho, alto), "white")
    draw = ImageDraw.Draw(imagen)
    
    # Dibujar cada celda basada en los datos
    for x, y, color in datos:
        # Determinar el color basado en el valor de la tercera columna
        color_celda = (255, 255, 255) if color == 0 else (0, 0, 0)  # blanco para 0, negro para 100
        color_celda = (255, 0, 255) if color == 200 else color_celda
        color_celda = (255, 0, 0) if color == 300 else color_celda
        color_celda = (255, 255, 0) if color == 400 else color_celda
        # Calcular las coordenadas de la celda
        esquina_superior_izq = ((x - 1) * ancho_celda, (y - 1) * alto_celda)
        esquina_inferior_der = (x * ancho_celda, y * alto_celda)
        
        # Dibujar el rectángulo (cuadrado)
        draw.rectangle([esquina_superior_izq, esquina_inferior_der], fill=color_celda)
    
    return imagen

# Ruta del archivo con los datos
ruta_archivo = "output.5h"

# Leer los datos del archivo
datos = leer_datos(ruta_archivo)

# Crear la imagen
imagen = crear_imagen(datos)

# Guardar o mostrar la imagen
imagen.show()  # Muestra la imagen
# imagen.save("imagen_resultante.png")  # O para guardar la imagen