import sys
from PIL import Image
import os

def create_icns():
    # Create a simple wallet icon
    img = Image.open('icon.png')
    
    # Create iconset directory
    if not os.path.exists('icon.iconset'):
        os.makedirs('icon.iconset')
    
    # Generate different sizes
    sizes = [(16,16), (32,32), (64,64), (128,128), (256,256), (512,512)]
    for size in sizes:
        resized = img.resize(size)
        resized.save(f'icon.iconset/icon_{size[0]}x{size[0]}.png')
        if size[0] <= 256:  # Also create @2x versions for smaller sizes
            resized = img.resize((size[0]*2, size[0]*2))
            resized.save(f'icon.iconset/icon_{size[0]}x{size[0]}@2x.png')
    
    # Convert to icns using iconutil
    os.system('iconutil -c icns icon.iconset')
    
    # Clean up
    for size in sizes:
        os.remove(f'icon.iconset/icon_{size[0]}x{size[0]}.png')
        if size[0] <= 256:
            os.remove(f'icon.iconset/icon_{size[0]}x{size[0]}@2x.png')
    os.rmdir('icon.iconset')

if __name__ == '__main__':
    create_icns()
