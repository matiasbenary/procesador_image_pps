# Proyecto: Procesamiento de Archivos DICOM

Este repositorio contiene scripts para la conversión automatizada de archivos DICOM a formatos compatibles con herramientas como Gmsh, permitiendo generar mallas y realizar análisis adicionales.

## Descripción General

El proyecto incluye un flujo de trabajo completo que abarca:

1. **Procesamiento de archivos DICOM**: Lectura y análisis de archivos médicos en formato DICOM.
2. **Detección de contornos**: Identificación de estructuras como huesos y piel mediante umbrales ajustables.
3. **Filtrado y ordenamiento**: Mejora de los datos detectados para una mejor representación geométrica.
4. **Generación de archivos GEO**: Creación de archivos compatibles con Gmsh.
5. **Conversión adicional**:
   - Transformación de archivos GEO a MSH.
   - Conversión de modelos de Elementos Finitos (FEM) a FDTD.
   - Generación de imágenes visuales a partir de archivos FDTD.

## Scripts Principales

### `procimage2gmsh_vdb.py`

Este es el script principal del proyecto. Utiliza bibliotecas como:

- `numpy`
- `matplotlib`
- `pydicom`

#### Funcionalidades:

- Procesamiento por lotes de archivos DICOM.
- Detección de contornos mediante algoritmos personalizados.
- Exportación a archivos GEO listos para ser utilizados en Gmsh.

### `convert_geo_to_msh.py`

Este script convierte archivos GEO generados a formato MSH, compatible con herramientas de simulación basadas en elementos finitos.

#### Funcionalidades:

- Lee archivos GEO.
- Genera archivos MSH optimizados para su uso en simulaciones FEM.

### `procimage2h5.py`

Script para convertir datos procesados a formato propietario

#### Funcionalidades:

- Conversión de datos procesados a propietario.

### `convertToPng.py`

Este script convierte los resultados procesados a imágenes en formato PNG para una visualización rápida y clara.

#### Funcionalidades:

- Lectura de archivos procesados.
- Generación de imágenes PNG de alta calidad.

## Requisitos

### Dependencias

Instala las bibliotecas requeridas mediante `pip`:

```bash
pip install -r requirements.txt
```

### Software Adicional

- [Gmsh](https://gmsh.info/) para manejar archivos GEO y MSH.

## Uso

1. Coloca los archivos DICOM en la carpeta `input/`.
2. Ejecuta los scripts:
   - Convertir Dicom a geo:
  
   ```bash
   python3 procimage2gmsh_vdb.py -i input -o output
   ```

   - Convertir GEO a MSH:

   ```bash
   ./convert_geo_to_msh.sh
   ```

   - Convertir datos a personalizado:

   ```bash
   python3 procimage2h5.py
   ```

   - Generar imágenes PNG:

   ```bash
   python3 convertToPng.py
   ```

3. Los resultados se guardarán en la carpeta `output/` con los formatos correspondientes.
