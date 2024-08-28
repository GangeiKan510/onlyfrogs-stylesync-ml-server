from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from rembg import remove
from PIL import Image
from io import BytesIO
import pyrebase
import os
from datetime import datetime

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

            file_url = storage.child(filename).get_url(None)

            return JsonResponse({
                'message': 'Image processed and uploaded successfully.',
                'file_url': file_url
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)
