from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
import requests
from rembg import remove
from PIL import Image
from io import BytesIO


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

            return HttpResponse(output_image_io, content_type='image/png')

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method. Use POST.'}, status=405)
