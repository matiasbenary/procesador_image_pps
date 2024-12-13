import numpy as np
import meshio
from scipy.spatial import KDTree

mesh = meshio.read("munieca2dnewer.msh")

nodes = np.array(mesh.points)[:, :2] 
print(nodes)
elements = mesh.cells_dict['triangle']

output_file = "output.5h"

physical_surfaces = mesh.cell_data_dict['gmsh:physical']['triangle']

x_min, y_min = np.min(nodes, axis=0)
x_max, y_max = np.max(nodes, axis=0)

delta = 0.005
dx = delta
dy = delta

print(f"Generando grilla con paso max{x_max} , y max {y_max} y paso {dx} y {dy}")

x_vals = np.arange(x_min, x_max + dx, dx)
y_vals = np.arange(y_min, y_max + dy, dy)
X, Y = np.meshgrid(x_vals, y_vals)

tree = KDTree(nodes)

def find_containing_element(point):
    distance, idx = tree.query(point, k=5)
    for elem in elements:
        if any(i in elem for i in idx):
            return elem
    return None

with open(output_file, 'w') as f:
    # f.write(f"{len(x_vals)} {len(y_vals)}\n")
    # f.write(f"{x_min:.6f} {x_max:.6f} {y_min:.6f} {y_max:.6f}\n")
    last_elem = 100
    for j, y in enumerate(Y):
        for i, x in enumerate(X):
            point = [x[i], y[j]] 
            elem = find_containing_element(point)
            
            if elem is not None:
                surface_id = physical_surfaces[np.where((elements == elem).all(axis=1))[0][0]]
                f.write(f"{i+1} {j+1} {surface_id}\n")
                last_elem = surface_id
            else:
                f.write(f"{i+1} {j+1} {last_elem}\n")

print(f"Grilla generada y guardada en {output_file}")