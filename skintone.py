import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from sklearn.cluster import KMeans


def classify_season_and_sub_season(skin_tone_rgb):
    # Convert RGB to HSV
    hsv = cv2.cvtColor(np.uint8([[skin_tone_rgb]]), cv2.COLOR_BGR2HSV)[0][0]

    # Extract hue, saturation, and value
    hue, saturation, value = hsv

    # Determine undertone: warm or cool
    warm_undertone = (hue < 30 or hue > 150)

    # Determine depth (light vs deep) using brightness (value)
    if value > 200:
        depth = "light"
    elif value < 85:
        depth = "deep"
    else:
        depth = "medium"

    # Determine chroma (bright vs soft) using saturation
    if saturation > 150:
        chroma = "bright"
    else:
        chroma = "soft"

    # Classification logic based on undertone, depth, and chroma
    if warm_undertone:
        # Spring or Autumn
        if depth == "light":
            if chroma == "bright":
                return ("spring", "light spring")
            else:
                return ("autumn", "soft autumn")
        elif depth == "deep":
            return ("autumn", "deep autumn")
        else:  # Medium
            if chroma == "bright":
                return ("spring", "warm spring")
            else:
                return ("autumn", "warm autumn")
    else:
        # Summer or Winter
        if depth == "light":
            if chroma == "soft":
                return ("summer", "light summer")
            else:
                return ("winter", "bright winter")
        elif depth == "deep":
            return ("winter", "deep winter")
        else:  # Medium
            if chroma == "soft":
                return ("summer", "cool summer")
            else:
                return ("winter", "cool winter")


def get_skin_tone(image_url):
    # Download the image
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    img = np.array(img)

    # Convert the image to RGB if it's not
    if img.shape[2] == 4:  # If the image has an alpha channel, remove it
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    # If grayscale, convert to RGB
    elif len(img.shape) == 2 or img.shape[2] == 1:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)

    # Convert to OpenCV format
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Load OpenCV's pre-trained face detector model
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    # Detect faces in the image
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    if len(faces) == 0:
        return {"error": "No faces detected"}

    # Assuming the first detected face is the one we want to analyze
    x, y, w, h = faces[0]

    # Extract the face region (We focus on the center of the face for skin tone)
    face_roi = img[y:y+h, x:x+w]

    # Sample skin region (center of the face, avoiding eyes, mouth)
    h_roi, w_roi = face_roi.shape[:2]
    skin_sample_region = face_roi[int(
        0.4*h_roi):int(0.6*h_roi), int(0.3*w_roi):int(0.7*w_roi)]

    # Reshape the image to be a list of pixels
    pixels = skin_sample_region.reshape(-1, 3)

    # Apply KMeans clustering to find the most dominant color
    kmeans = KMeans(n_clusters=1)
    kmeans.fit(pixels)
    dominant_color = kmeans.cluster_centers_[0]

    # Convert the dominant color to hexadecimal
    skin_tone_hex = "#{:02x}{:02x}{:02x}".format(
        int(dominant_color[2]), int(dominant_color[1]), int(dominant_color[0]))

    # Classify season and sub-season based on the dominant skin tone
    skin_tone_rgb = [int(dominant_color[2]), int(
        dominant_color[1]), int(dominant_color[0])]
    season, sub_season = classify_season_and_sub_season(skin_tone_rgb)

    # Generate 7 complementary colors by rotating the hue
    complement_colors = []
    for i in range(7):
        # Rotate the hue
        complementary_hue = (cv2.cvtColor(
            np.uint8([[skin_tone_rgb]]), cv2.COLOR_BGR2HSV)[0][0][0] + (i * 30)) % 180
        complement_color = cv2.cvtColor(np.uint8(
            [[[complementary_hue, 255, 255]]]), cv2.COLOR_HSV2BGR)[0][0]
        # Convert to hexadecimal
        complement_color_hex = "#{:02x}{:02x}{:02x}".format(
            int(complement_color[2]), int(complement_color[1]), int(complement_color[0]))
        complement_colors.append(complement_color_hex)

    # Return the skin tone, season, sub-season, and complementary colors
    return {
        "skin_tone": skin_tone_hex,
        "season": season,
        "sub_season": sub_season,
        "complements": complement_colors
    }


# Example usage
image_url = 'https://scontent.xx.fbcdn.net/v/t1.15752-9/415655256_1224558035170419_8091966756749466797_n.jpg?_nc_cat=109&ccb=1-7&_nc_sid=0024fc&_nc_eui2=AeEl1hYEnP_AMRb8TkBs9vd69IXB9w4VhxH0hcH3DhWHESfZsphdctELDbZIkbt4IzXiqVcFFHT8lXeKMqca18TC&_nc_ohc=OLrNTNlsv9wQ7kNvgGcH8Ro&_nc_ad=z-m&_nc_cid=0&_nc_ht=scontent.xx&oh=03_Q7cD1QH0PnRcQE8fAoglhr6103gdVlWchBW7Vj0ULQ2dSgqGYg&oe=670E8765'
result = get_skin_tone(image_url)
print(result)
