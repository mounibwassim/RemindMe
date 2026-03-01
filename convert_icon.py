from PIL import Image

img = Image.open('assets/logo.png')
icon_sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]
img.save('app.ico', format='ICO', sizes=icon_sizes)
print("Successfully generated app.ico with multiple resolutions.")
