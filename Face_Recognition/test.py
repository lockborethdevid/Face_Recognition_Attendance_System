from PIL import Image

img = Image.open("img810.png")

img.save("image_test1.jpg", quality = 200)