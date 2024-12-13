import os
import numpy as np
import matplotlib.pyplot as plt
import pydicom
from skimage import measure
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon
import argparse;

def calculate_perimeter(contour):
    return np.sum(np.sqrt(np.sum(np.diff(contour, axis=0) ** 2, axis=1)))

def remove_duplicate_vectors(vectors):
    unique_vectors = set(tuple(vector) for vector in vectors)
    
    return [list(vector) for vector in unique_vectors]

class BoneImageProcessor:
    def __init__(self, dicom_file):
        self.dicom_file = dicom_file
        self.slice = None
        self.pixel_spacing = None
        self.slice_thickness = None
        self.img2d = None
        self.normalized_image = None
        self.contours = {"bone": [], "skin": []}
        self.composition = {"skin": [], "bone": []}
        self.processed_contours = []
        self.box_size = 0.25
        self.z = 0

    def load_dicom(self):
        self.slice = pydicom.dcmread(self.dicom_file)
        self.pixel_spacing = self.slice.PixelSpacing
        self.slice_thickness = self.slice.SliceThickness
        x, y, self.z = self.slice.ImagePositionPatient
        self.img2d = self.slice.pixel_array
        self.normalized_image = self.img2d / np.amax(self.img2d)

    def find_contours(self, threshold, contour_type):
        contours = measure.find_contours(self.normalized_image, threshold)
        self.contours[contour_type] = [
            c for c in contours if len(c) > 30 and not self.is_rectangle(c)
        ]

    def plot_contour(self, contour):
        fig, ax = plt.subplots(1, 1, figsize=(8, 8))
        ax.imshow(self.normalized_image, cmap=plt.cm.gray, interpolation="nearest")
        ax.plot(contour[:, 1], contour[:, 0], linewidth=2)
        plt.show()

    def is_circle(self, contour):
        hull = ConvexHull(contour)
        area = hull.volume

        perimeter = calculate_perimeter(contour)
        if perimeter == 0:
            return False
        circularity = (4 * np.pi * area) / (perimeter**2)
        return 0.7 <= circularity <= 1.3

    def is_rectangle(self, contour):
        xmax, ymax = np.max(contour * self.pixel_spacing[0] * 1.0e-3, axis=0)
        xmin, ymin = np.min(contour * self.pixel_spacing[0] * 1.0e-3, axis=0)
        ratio = (xmax - xmin) / (ymax - ymin)
        return ratio > 5 or ratio < 0.2

    def filter_body(self):
        containers = [
            {
                "container": skin,
                "items": [
                    bone
                    for bone in self.contours["bone"]
                    if self.is_contained(skin, bone)
                ],
            }
            for skin in self.contours["skin"]
        ]

        for container in containers:
            if len(container["items"]) == 4:
                self.composition["skin"].append(container["container"])
                self.composition["bone"].extend(container["items"])
                return True
        return False

    def is_contained(self, container, item):
        container_bounds = np.min(container, axis=0), np.max(container, axis=0)
        item_bounds = np.min(item, axis=0), np.max(item, axis=0)
        return (
            container_bounds[0][0] <= item_bounds[0][0]
            and container_bounds[0][1] <= item_bounds[0][1]
            and container_bounds[1][0] >= item_bounds[1][0]
            and container_bounds[1][1] >= item_bounds[1][1]
            and not np.array_equal(container_bounds, item_bounds)
        )

    def plot_final_contours(self):
        fig, ax = plt.subplots(figsize=(8, 8))
        extent = [
            0,
            self.img2d.shape[1] * self.pixel_spacing[0] * 1.0e-3,
            0,
            self.img2d.shape[0] * self.pixel_spacing[0] * 1.0e-3,
        ]
        ax.imshow(
            self.normalized_image,
            cmap=plt.cm.gray,
            interpolation="nearest",
            extent=extent,
            origin="lower",
        )

        for contour_type, contours in self.composition.items():
            for contour in contours:
                ax.plot(
                    contour[:, 1] * self.pixel_spacing[0] * 1.0e-3,
                    contour[:, 0] * self.pixel_spacing[0] * 1.0e-3,
                    linewidth=2,
                )

        ax.set_title("Final Contours")
        ax.set_xlabel("x (m)")
        ax.set_ylabel("y (m)")
        plt.show()

    def generate_gmsh_geo(self, output_file):
        with open(output_file, "w") as f:
            f.write("//Meshing bone.\n")
            f.write("//Inputs;\n")
            f.write("gridsize = 1;\n\n")

            point_index = 1
            line_index = 1
            surface_index = 1
            loop_index = 1
            max_perimeter = 0
            coords = ((0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0))
            centroid = Polygon(coords)

            for contour in self.processed_contours:
                perimeter = Polygon(
                    contour["item"] * self.pixel_spacing[0] * 1.0e-3
                ).length
                if max_perimeter < perimeter:
                    max_perimeter = perimeter
                    centroid = Polygon(
                        contour["item"] * self.pixel_spacing[0] * 1.0e-3
                    ).centroid
            for contour in self.processed_contours:
                point_index, line_index, loop_index = self.write_contour_to_geo(
                    f, contour["item"], point_index, line_index, loop_index, centroid
                )
                f.write(
                    f'Plane Surface({surface_index}) = {{{contour["surface"]}}};\n\n'
                )
                surface_index += 1

            point_index, line_index, loop_index = self.add_box_to_geo(
                f,
                point_index,
                line_index,
                loop_index,
            )
            self.add_physical_entities_to_geo(f, surface_index)

    def order_contours(self):
        aux = []
        counter = 1
        skin = ""
        for container in self.composition["bone"]:
            for item in self.composition["bone"]:
                if max(container[:, 1]) != max(item[:, 1]) and self.is_contained(
                    container, item
                ):
                    self.processed_contours.append(
                        {
                            "item": item,
                            "surface": str(counter),
                            "type": "internal",
                            "id": counter,
                        }
                    )
                    counter += 1
                    aux.append(counter)
                    self.processed_contours.append(
                        {
                            "item": container,
                            "surface": str(counter) + "," + str(counter - 1),
                            "type": "internal",
                            "id": counter,
                        }
                    )
                    skin = "," + str(counter)+skin
                    counter += 1
        for contour in self.composition["skin"]:
            self.processed_contours.append(
                {
                    "item": contour,
                    "surface": str(counter) + skin,
                    "type": "external",
                    "id": counter,
                }
            )

    def write_contour_to_geo(
        self, file, contour, point_index, line_index, loop_index, centroid
    ):
        centered_contour = contour * self.pixel_spacing[0] * 1.0e-3 - np.array(
            [centroid.x, centroid.y]
        )

        # points = remove_duplicate_vectors(centered_contour[::10])  # Use every 10th point to reduce complexity
        points = (centered_contour[::7])  
        for point in points:
            file.write(
                f"Point({point_index}) = {{{point[1]},{point[0]},0,gridsize}};\n"
            )
            point_index += 1

        file.write("\n")

        lines = []
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            file.write(
                f"Line({line_index}) = {{{point_index-len(points)+i},{point_index-len(points)+next_i}}};\n"
            )
            lines.append(line_index)
            line_index += 1

        file.write("\n")

        file.write(f'Line Loop({loop_index}) = {{{",".join(map(str, lines))}}};\n')
        loop_index += 1

        return point_index, line_index, loop_index

    def add_box_to_geo(self, file, point_index, line_index, loop_index):
        L = self.box_size / 2
        box_points = [(-L, -L), (-L, L), (L, L), (L, -L)]

        for x, y in box_points:
            file.write(f"Point({point_index}) = {{{x},{y},0,gridsize}};\n")
            point_index += 1

        box_lines = []
        for i in range(4):
            next_i = (i + 1) % 4
            file.write(
                f"Line({line_index}) = {{{point_index-4+i},{point_index-4+next_i}}};\n"
            )
            box_lines.append(line_index)
            line_index += 1

        file.write(f'Line Loop({loop_index}) = {{{",".join(map(str, box_lines))}}};\n')
        file.write(
            f"Plane Surface({loop_index+1}) = {{{loop_index},{loop_index-1}}};\n\n"
        )

        return point_index, line_index, loop_index + 2

    def add_physical_entities_to_geo(self, file, surface_index):
        file.write(
            f'Physical Surface(100) = {{{surface_index+1}}}; // "Medio de acoplamiento"\n'
        )
        file.write(f'Physical Surface(200) = {{{surface_index-1}}}; // "Musculo"\n')
        file.write(
            f'Physical Surface(300) = {{{surface_index-2},{surface_index-4}}}; // "Calcaneo"\n'
        )
        file.write(
            f'Physical Surface(400) = {{{surface_index-3},{surface_index-5}}}; // "Trabecular"\n'
        )
        file.write(f'Physical Line(10) = {{1,2,3,4}}; // "borde externo"\n')
        file.write("Mesh.CharacteristicLengthMax = 1.0e-2;\n")



def main():
    parser = argparse.ArgumentParser(description="Procesa imágenes DICOM para generar archivos .geo")
    parser.add_argument('-i', '--input', required=True, 
                        help='Directorio de entrada que contiene archivos DICOM')
    parser.add_argument('-o', '--output', default='output', 
                        help='Directorio de salida para los archivos procesados')
    
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)
    
    filename = os.listdir(args.input)
    only_files = [f for f in filename if os.path.isfile(os.path.join(args.input, f))]
    
    for filename in only_files:
        processor = BoneImageProcessor(os.path.join(args.input, filename))
        
        processor.load_dicom()
        
        processor.find_contours(0.5, 'bone')
        processor.find_contours(0.2, 'skin')
        
        if processor.filter_body():
            # Descomentar para ver las imagenes con los contornos
            processor.plot_final_contours()
            processor.order_contours()
            processor.generate_gmsh_geo(os.path.join(args.output, f'munieca-{filename[:-4]}.geo'))

if __name__ == "__main__":
    main()