
import os
from telegram import InputMediaPhoto

IMAGE_FOLDER = "assets/images/"

def get_price_media():
    if not os.path.exists(IMAGE_FOLDER):
        raise FileNotFoundError(f"Папка {IMAGE_FOLDER} не существует.")

    image_files = [f for f in os.listdir(IMAGE_FOLDER) if f.endswith((".jpg", ".png"))]
    if not image_files:
        return "Нет изображений для загрузки."

    images = []
    for image_name in image_files:
        image_path = os.path.join(IMAGE_FOLDER, image_name)
        with open(image_path, "rb") as image_file:
            media = InputMediaPhoto(image_file)  # Файл будет автоматически закрыт
            images.append(media)

    return images