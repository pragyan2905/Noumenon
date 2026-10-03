from PIL import Image
from rembg import remove, new_session
print("Imported successfully")
try:
    img = Image.new('RGB', (100, 100), color='red')
    session = new_session('u2netp')
    print("Session created")
    out = remove(img, session=session)
    print("Success!", out.mode, out.size)
except Exception as e:
    print("Error:", str(e))
