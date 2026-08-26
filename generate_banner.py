from PIL import Image, ImageDraw, ImageFont
import random
import os


def generate_banner(output_path: str = "data/banner.png"):
    """Генерирует баннер SPAXRIZESAVE в кровавом стиле."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Размер баннера
    width, height = 1080, 720
    
    # Создаем изображение с тёмно-красным градиентом
    img = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(img)
    
    # Градиент от тёмно-красного к чёрному
    for y in range(height):
        r = int(80 - (y / height) * 60)
        g = int(10 - (y / height) * 10)
        b = int(10 - (y / height) * 10)
        draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Добавляем "кровавые" потёки и брызги
    for _ in range(50):
        x = random.randint(0, width)
        y = random.randint(0, height)
        length = random.randint(20, 150)
        thickness = random.randint(2, 8)
        
        # Потёк вниз
        for i in range(length):
            if y + i < height:
                alpha = max(0, 255 - i * 2)
                color = (min(255, 150 + random.randint(0, 50)), 
                        random.randint(0, 20), 
                        random.randint(0, 20))
                draw.ellipse([x - thickness//2, y + i, 
                            x + thickness//2, y + i + thickness], 
                           fill=color)
    
    # Брызги
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        size = random.randint(2, 10)
        color = (min(255, 180 + random.randint(0, 50)), 
                random.randint(0, 30), 
                random.randint(0, 30))
        draw.ellipse([x, y, x + size, y + size], fill=color)
    
    # Текст SPAXRIZESAVE
    try:
        # Пытаемся использовать системный шрифт Arial Bold
        font_large = ImageFont.truetype("arialbd.ttf", 80)
        font_small = ImageFont.truetype("arial.ttf", 30)
    except:
        # Если Arial недоступен, используем дефолтный
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    text = "SPAXRIZESAVE"
    
    # Вычисляем позицию текста (по центру)
    bbox = draw.textbbox((0, 0), text, font=font_large)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2 - 30
    
    # Тень для текста
    shadow_offset = 4
    draw.text((x + shadow_offset, y + shadow_offset), text, 
              fill=(50, 0, 0), font=font_large)
    
    # Основной текст (белый)
    draw.text((x, y), text, fill=(255, 255, 255), font=font_large)
    
    # Подпись
    subtitle = "· вотчер личных чатов ·"
    bbox_sub = draw.textbbox((0, 0), subtitle, font=font_small)
    sub_width = bbox_sub[2] - bbox_sub[0]
    sub_x = (width - sub_width) // 2
    sub_y = y + text_height + 20
    
    draw.text((sub_x, sub_y), subtitle, fill=(200, 200, 200), font=font_small)
    
    # Сохраняем
    img.save(output_path, "PNG")
    print(f"Баннер сохранён: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_banner()
