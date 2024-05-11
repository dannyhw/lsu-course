import os

from cairosvg import svg2png
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # take environment variables from .env.


openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

functions = [
    {
        "type": "function",
        "function": {
            "name": "svg_to_png_bytes",
            "description": "Generate a PNG from an SVG",
            "parameters": {
                "type": "object",
                "properties": {
                    "svg_string": {
                        "type": "string",
                        "description": "A fully formed SVG element in the form of a string",
                    },
                },
                "required": ["svg_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "python_math_execution",
            "description": "Solve a math problem using python code",
            "parameters": {
                "type": "object",
                "properties": {
                    "math_string": {
                        "type": "string",
                        "description": "A string that solves a math problem that conforms with python syntax that could be passed directly to an eval() function",
                    },
                },
                "required": ["math_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "text_to_image",
            "description": "Convert text to image",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_description": {
                        "type": "string",
                        "description": "The text description of an image that will be generated. The function returns a url to the image",
                    },
                },
                "required": ["image_description"],
            }
        }
    }
]


def svg_to_png_bytes(svg_string: str):
    # Convert SVG string to PNG bytes
    png_bytes = svg2png(bytestring=svg_string.encode('utf-8'))
    return png_bytes


def python_math_execution(math_string: str):
    try:
        answer = eval(math_string)
        if answer:
            return str(answer)
    except:
        return 'invalid code generated'


def text_to_image(image_description: str):
    response = openai.images.generate(prompt=image_description,
                                      model="dall-e-3",
                                      n=1,
                                      size="1024x1024")
    image_url = response.data[0].url

    return image_url


def run_function(name: str, args: dict):
    if name == "svg_to_png_bytes":
        return svg_to_png_bytes(args["svg_string"])
    elif name == "python_math_execution":
        return python_math_execution(args["math_string"])
    elif name == "text_to_image":
        return text_to_image(args["image_description"])
    else:
        return None
