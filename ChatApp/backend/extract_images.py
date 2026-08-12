import fitz  # PyMuPDF
import os

# Open the PDF file
pdf_document = fitz.open("Cell_Organelles_Guide.pdf")

# Create an images folder inside your frontend public folder if it doesn't exist
output_dir = "../frontend/public/organelle_images"
os.makedirs(output_dir, exist_ok=True)

image_count = 0

# Loop through every page in the PDF
for page_index in range(len(pdf_document)):
    page = pdf_document[page_index]
    image_list = page.get_images(full=True)

    # Loop through all images found on the page
    for img_index, img in enumerate(image_list):
        xref = img[0]
        base_image = pdf_document.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]  # e.g., png, jpeg

        image_filename = f"organelle_{page_index}_{img_index}.{image_ext}"
        image_path = os.path.join(output_dir, image_filename)

        # Save the image file
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        
        image_count += 1

print(f"Successfully extracted {image_count} images!")