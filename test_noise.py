import requests
import json
from PIL import Image
import os
import random

# Create a noisy image
img = Image.new('RGB', (100, 100), color='white')
pixels = img.load()
for i in range(img.size[0]):
    for j in range(img.size[1]):
        if random.random() < 0.1:
            pixels[i, j] = (0, 0, 0) # Salt and pepper noise
img.save('noisy.png')

# Call the API
url = 'http://127.0.0.1:10000/api/convert'
files = {'file': open('noisy.png', 'rb')}
data = {
    'output_format': 'png',
    'options': json.dumps({'noise_reduction': 'median'})
}
response = requests.post(url, files=files, data=data)

with open('cleaned.png', 'wb') as f:
    f.write(response.content)

print(f"Status Code: {response.status_code}")
if response.status_code == 200:
    print("Noise reduction successfully applied and saved to cleaned.png")
else:
    print(response.text)
