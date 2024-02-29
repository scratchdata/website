from PIL import Image, ImageDraw, ImageFont


def create_gradient_rect(size, color1, color2, mode='horizontal'):
    """
    Create a rectangular gradient between two colors.
    """
    image = Image.new("RGB", size)
    draw = ImageDraw.Draw(image)

    def interpolate(start_color, end_color, factor: float):
        recip = 1 - factor
        return (
            int(start_color[0] * recip + end_color[0] * factor),
            int(start_color[1] * recip + end_color[1] * factor),
            int(start_color[2] * recip + end_color[2] * factor)
        )

    if mode == 'horizontal':
        for x in range(size[0]):
            factor = x / size[0]
            color = interpolate(color1, color2, factor)
            draw.line([(x, 0), (x, size[1])], fill=color)
    elif mode == 'vertical':
        for y in range(size[1]):
            factor = y / size[1]
            color = interpolate(color1, color2, factor)
            draw.line([(0, y), (size[0], y)], fill=color)
    elif mode == 'diagonal':
        for x in range(size[0]):
            for y in range(size[1]):
                factor = (x + y) / (size[0] + size[1])
                color = interpolate(color1, color2, factor)
                draw.point((x, y), fill=color)
    elif mode == 'reverse_diagonal':
        for x in range(size[0]):
            for y in range(size[1]):
                factor = (size[0] - x + y) / (size[0] + size[1])
                color = interpolate(color1, color2, factor)
                draw.point((x, y), fill=color)

    return image

# def create_gradient_image(width, height, color1, color2):
#     img = Image.new('RGB', (width, height), color1)
#     draw = ImageDraw.Draw(img)
#     for i in range(height):
#         r = int(color1[0] + (color2[0] - color1[0]) * (i / height))
#         g = int(color1[1] + (color2[1] - color1[1]) * (i / height))
#         b = int(color1[2] + (color2[2] - color1[2]) * (i / height))
#         draw.line([(0, i), (width, i)], fill=(r, g, b))
#     return img


def add_rounded_corners(img, radius):
    circle = Image.new('L', (radius *  2, radius *  2),  0)
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0,  0, radius *  2, radius *  2), fill=255)
    alpha = Image.new('L', img.size,  255)
    alpha.paste(circle.crop((0,  0, radius, radius)), (0,  0))
    alpha.paste(circle.crop((0, radius, radius, radius *  2)), (0, img.height - radius))
    alpha.paste(circle.crop((radius,  0, radius *  2, radius)), (img.width - radius,  0))
    alpha.paste(circle.crop((radius, radius, radius *  2, radius *  2)), (img.width - radius, img.height - radius))
    img.putalpha(alpha)
    return img.convert('RGBA')


def add_text(img, text, font_size=30):
    font = ImageFont.truetype('Play-Regular.ttf', font_size)
    wrapped_text = get_wrapped_text(text, font, line_length=600)

    draw = ImageDraw.Draw(img)
    # font = ImageFont.truetype('arial.ttf', font_size)
    # text_width = draw.textlength(text, font=font)
    text_height = (font_size * (wrapped_text.count("\n")+1)) 
    x = 80
    y = (img.height-text_height)-font_size
    # x = (img.width - text_width) /  2
    # y = (img.height - text_height) /  2
    draw.text((x, y), wrapped_text, fill=(255,  255,  255), font=font)
    # draw.text((x, y), text, fill=(255,  255,  255), font=font)
    return img

def get_wrapped_text(text: str, font: ImageFont.ImageFont,
                     line_length: int):
        lines = ['']
        for word in text.split():
            line = f'{lines[-1]} {word}'.strip()
            if font.getlength(line) <= line_length:
                lines[-1] = line
            else:
                lines.append(word)
        return '\n'.join(lines)

def generate_social_hero(color1, color2, text, direction='horizontal',width=1200, height=630,radius=30):
    gradient_img = create_gradient_rect((width, height), color1, color2,direction)
    # gradient_img = create_gradient_image(width, height, color1, color2)
    rounded_img = add_rounded_corners(gradient_img, radius)
    final_img = add_text(rounded_img, text,60)

    logo = Image.open('static/logo_light.png', 'r')
    logo.thumbnail((500,200),Image.Resampling.LANCZOS)
    final_img.paste(logo, (80,80),logo)
    return final_img


if __name__ == "__main__":
    width, height =  1200,  630  # Example dimensions for a social hero image
    color1 = (0,  74,  173)
    color2 = (203,  108,230)  
    text = "How to use DuckDB as a REST API"
    radius =  30  # Radius for rounded corners

    # Generate and save the image
    img = generate_social_hero(width, height, color1, color2, text, radius)

    # logo = Image.open('logo.png', 'r')
    # logo.thumbnail((500,200),Image.Resampling.LANCZOS)
    # img.paste(logo, (80,80),logo)

    img.save("social_hero.png")
