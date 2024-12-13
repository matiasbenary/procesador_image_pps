#!/bin/bash

# Carpeta donde están los archivos .geo
input_folder="./"
output_folder="./msh"

# Crear carpeta de salida si no existe
mkdir -p "$output_folder"

# Iterar sobre cada archivo .geo
for geo_file in "$input_folder"/*.geo; do
    # Obtener el nombre base del archivo sin extensión
    base_name=$(basename "$geo_file" .geo)
    # Convertir a .msh usando Gmsh
    gmsh "$geo_file" -2 -o "$output_folder/$base_name.msh"
done

echo "Conversión completada. Archivos guardados en $output_folder"