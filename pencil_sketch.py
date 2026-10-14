import cv2
import os
import tkinter as tk
from tkinter import filedialog


def photo_to_pencil_sketch(input_path, output_path):
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Image file not found: {input_path}")

    image = cv2.imread(input_path)
    if image is None:
        raise ValueError(f"Unable to open image: {input_path}")

    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    inverted_image = 255 - gray_image
    blurred_image = cv2.GaussianBlur(inverted_image, (21, 21), 0)
    inverted_blur = 255 - blurred_image
    sketch = cv2.divide(gray_image, inverted_blur, scale=256.0)

    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    saved = cv2.imwrite(output_path, sketch)
    if not saved:
        raise OSError(f"Could not save sketch to: {output_path}")

    return output_path


def select_input_image():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select an image",
        filetypes=[
            ("Image files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif;*.tif;*.tiff"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    return file_path


def select_output_path(original_name):
    base_name = os.path.splitext(os.path.basename(original_name))[0]
    default_name = f"{base_name}_sketch.png"

    root = tk.Tk()
    root.withdraw()
    save_path = filedialog.asksaveasfilename(
        title="Save sketch as",
        defaultextension=".png",
        initialfile=default_name,
        filetypes=[
            ("PNG files", "*.png"),
            ("JPEG files", "*.jpg"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    return save_path


def main():
    input_image = select_input_image()
    if not input_image:
        print("No image selected. Exiting.")
        return

    output_image = select_output_path(input_image)
    if not output_image:
        print("No output path selected. Exiting.")
        return

    try:
        result = photo_to_pencil_sketch(input_image, output_image)
        print(f"Pencil sketch saved to: {result}")
    except Exception as exc:
        print(f"Error: {exc}")


if __name__ == "__main__":
    main()