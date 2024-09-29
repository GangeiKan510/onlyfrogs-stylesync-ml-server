import cv2
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import numpy as np
import requests
from rembg import remove
from PIL import Image
from io import BytesIO
import pyrebase
import os
from datetime import datetime

from sklearn.cluster import KMeans

firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
}

firebase = pyrebase.initialize_app(firebase_config)
storage = firebase.storage()


def home(request):
    return HttpResponse("StyleSync Django Server")


@csrf_exempt
def remove_background_view(request):
    if request.method == 'POST':
        image_url = request.POST.get('image_url', '')

        if not image_url:
            return JsonResponse({'error': 'No image URL provided.'}, status=400)

        try:
            response = requests.get(image_url)
            if response.status_code != 200:
                return JsonResponse({'error': 'Failed to download the image.'}, status=400)

            input_image = Image.open(BytesIO(response.content))

            output_image = remove(input_image)

            output_image_io = BytesIO()
            output_image.save(output_image_io, format='PNG')
            output_image_io.seek(0)

            # Firebase upload
            filename = f"output_images/{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            storage.child(filename).put(output_image_io)

            file_url = storage.child(filename).get_url()

            return JsonResponse({
                'message': 'Image processed and uploaded successfully.',
                'file_url': file_url
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)


def get_skin_tone(image_url):
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img = np.array(img)

    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    elif len(img.shape) == 2 or img.shape[2] == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) == 0:
        return {"error": "No faces detected"}

    x, y, w, h = faces[0]
    face_roi = img[y:y+h, x:x+w]
    h_roi, w_roi = face_roi.shape[:2]
    skin_sample_region = face_roi[int(
        0.4*h_roi):int(0.6*h_roi), int(0.3*w_roi):int(0.7*w_roi)]
    pixels = skin_sample_region.reshape(-1, 3)

    kmeans = KMeans(n_clusters=1)
    kmeans.fit(pixels)
    dominant_color = kmeans.cluster_centers_[0]

    skin_tone_hex = "#{:02x}{:02x}{:02x}".format(
        int(dominant_color[2]), int(dominant_color[1]), int(dominant_color[0]))

    skin_tone_rgb = [int(dominant_color[2]), int(
        dominant_color[1]), int(dominant_color[0])]
    season, sub_season = classify_season_and_sub_season(skin_tone_rgb)

    complement_colors = []
    for i in range(12):
        complementary_hue = (cv2.cvtColor(
            np.uint8([[skin_tone_rgb]]), cv2.COLOR_BGR2HSV)[0][0][0] + (i * 15)) % 180

        saturation = np.random.randint(70, 180)
        value = np.random.randint(100, 250)

        complement_color = cv2.cvtColor(np.uint8(
            [[[complementary_hue, saturation, value]]]), cv2.COLOR_HSV2BGR)[0][0]
        complement_color_hex = "#{:02x}{:02x}{:02x}".format(
            int(complement_color[2]), int(complement_color[1]), int(complement_color[0]))
        complement_colors.append(complement_color_hex)

    neutral_colors = ['#000000', '#808080', '#A9A9A9', '#D3D3D3']
    complement_colors.extend(neutral_colors)

    return {
        "skin_tone": skin_tone_hex,
        "season": season,
        "sub_season": sub_season,
        "complements": complement_colors
    }


def classify_season_and_sub_season(skin_tone_rgb):
    hsv = cv2.cvtColor(np.uint8([[skin_tone_rgb]]), cv2.COLOR_BGR2HSV)[0][0]
    hue, saturation, value = hsv
    warm_undertone = (hue < 30 or hue > 150)

    if value > 200:
        depth = "light"
    elif value < 85:
        depth = "deep"
    else:
        depth = "medium"

    if saturation > 150:
        chroma = "bright"
    else:
        chroma = "soft"

    if warm_undertone:
        if depth == "light":
            if chroma == "bright":
                return ("spring", "light spring")
            else:
                return ("autumn", "soft autumn")
        elif depth == "deep":
            return ("autumn", "deep autumn")
        else:
            if chroma == "bright":
                return ("spring", "warm spring")
            else:
                return ("autumn", "warm autumn")
    else:
        if depth == "light":
            if chroma == "soft":
                return ("summer", "light summer")
            else:
                return ("winter", "bright winter")
        elif depth == "deep":
            return ("winter", "deep winter")
        else:
            if chroma == "soft":
                return ("summer", "cool summer")
            else:
                return ("winter", "cool winter")


@csrf_exempt
def analyze_skin_tone_view(request):
    if request.method == 'POST':
        try:
            data = request.POST
            image_url = data.get('image_url')
            if not image_url:
                return JsonResponse({'error': 'No image URL provided.'}, status=400)

            result = get_skin_tone(image_url)
            return JsonResponse(result)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)
