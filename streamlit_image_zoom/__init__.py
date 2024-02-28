import base64
import io
from typing import Optional, Tuple, Union

import numpy as np
import streamlit.components.v1 as components
from PIL import Image

__version__ = "0.0.1"


def check_image(image: Union[Image.Image, np.ndarray]) -> Image.Image:
    """
    Check and convert the input image to a PIL Image.

    Args:
        image (Union[Image.Image, np.ndarray]): The input image to be checked and converted.

    Returns:
        Image.Image: The input image as a PIL Image.

    Raises:
        TypeError: If the input image format is not supported. Supported formats are PIL Image and NumPy Array.

    """
    Image.MAX_IMAGE_PIXELS = None

    if isinstance(image, Image.Image):
        image_pil = image.convert("RGB")

    elif isinstance(image, np.ndarray):
        image_pil = Image.fromarray(image).convert("RGB")
    else:
        raise TypeError("Only supported format are Pillow Image and Numpy Array.")

    return image_pil


def pillow_to_base64(image: Image.Image) -> str:
    """
    Convert a PIL Image to a base64-encoded string.

    Args:
        image (Image.Image): The PIL Image to be converted.

    Returns:
        str: A base64-encoded string representing the image.

    """
    in_mem_file = io.BytesIO()
    image.save(in_mem_file, format="JPEG", subsampling=0, quality=100)
    image_str = base64.b64encode(in_mem_file.getvalue()).decode()
    base64_src = f"data:image/jpeg;base64, {image_str}"
    return base64_src


def prepare_image(image, size, keep_aspect_ratio):
    """
    Resize the image and convert it to a base64 string.

    Args:
        image: The image to be resized.
        size: The desired size of the image. It can be an integer or a tuple of integers (width, height).
        keep_aspect_ratio: Whether to maintain the aspect ratio of the image during resizing.
            If True, the image will be resized while preserving its aspect ratio.
            If False, the image will be resized to exactly match the provided size without preserving aspect ratio.

    Returns:
        Tuple[str, Tuple[int, int]]: A tuple containing the base64 string representation of the resized image
            and the new size of the image.

    """

    # new_size=(width, height)
    if isinstance(size, int) and keep_aspect_ratio:
        if keep_aspect_ratio:
            width, height = image.size
            # Calculate the aspect ratio. Width / Height
            aspect_ratio = width / height
            if aspect_ratio > 1:  # Fixed Width
                new_size = (size, int(size / aspect_ratio))
            elif aspect_ratio < 1:  # Fixed Height
                new_size = (int(size * aspect_ratio), size)
            else:
                new_size = (size, size)
        else:
            new_size = (size, size)
    else:
        new_size = size

    # Convert images to base64 strings.
    return pillow_to_base64(image.resize(new_size)), new_size


def image_zoom(
    image: Union[Image.Image, np.ndarray],
    mode: Optional[str] = "default",
    size: Optional[Union[int, Tuple[int, int]]] = 512,
    keep_aspect_ratio: Optional[bool] = True,
    zoom_factor: Optional[Union[float, int]] = 2.0,
    increment: Optional[float] = 0.2,
) -> components.html:
    """
    Display an image with interactive zoom functionality.

    Args:
        image (Union[Image.Image, np.ndarray]): The image to be displayed. It can be a PIL Image or a NumPy array.
        mode (Optional[str]): The mode of interaction for zooming. Valid options are "default" (zoom on mousemove),
            "mousemove" (zoom on mousemove), "scroll" (zoom on scroll), or "both" (zoom on both mousemove and scroll).
            Default is "default".
        size (Optional[Union[int, Tuple[int, int]]]): The desired size of the displayed image.
            If an integer is provided, the image will be resized to have that size (width = height).
            If a tuple of integers (width, height) is provided, the image will be resized to fit within
            the specified dimensions while maintaining its aspect ratio. Default is 512.
        keep_aspect_ratio (Optional[bool]): Whether to maintain the aspect ratio of the image during resizing.
            If True, the image will be resized while preserving its aspect ratio.
            If False, the image will be resized to exactly match the provided size without preserving aspect ratio.
            Default is True.
        zoom_factor (Optional[Union[float, int]]): The zoom factor applied to the image when zooming in.
            Default is 2.0.
        increment (Optional[float]): The increment value for adjusting the zoom level when scrolling.
            Should be between 0 and 1. Default is 0.2.

    Returns:
        HTML: An HTML component displaying the image with interactive zoom functionality.

    Raises:
        AssertionError: If the specified mode is not one of "default", "mousemove", "scroll", or "both".
        AssertionError: If the increment value is not within the range of 0 to 1.

    Example:
        image_zoom(image)
        image_zoom(image, mode="scroll", size=(800, 600), keep_aspect_ratio=False, zoom_factor=3.0, increment=0.05)
    """
    mode = mode.lower()
    assert (
        mode in ["default", "mousemove", "scroll", "both"]
    ), "Only valid event mode are default, mousemove, scroll and both. Default work with mousemove."
    zoom_factor = float(zoom_factor) if isinstance(zoom_factor, int) else zoom_factor
    assert increment <= 1.0 or increment > 0.0, "Increment should be between 0 and 1."

    # Check and convert to PIL image.
    image = check_image(image)
    # Resize image and convert to base64.
    img_base64, new_size = prepare_image(image, size, keep_aspect_ratio)

    css_code = """
        <style>
            #container {
                position: relative;
                overflow: hidden;
                cursor: zoom-in;
            }
            #image {
                position: absolute;
                top: 0;
                left: 0;
            }
        </style>
    """
    js_code = """
        <script>
            function ImageZoomMouseMove(selector, scale_factor) {
                const image = document.getElementById(selector);
                image.addEventListener('mousemove', function(event) {
                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = event.clientX - boundingRect.left;
                    const offsetY = event.clientY - boundingRect.top;
                    const originX = (offsetX / boundingRect.width) * 100 + '%';
                    const originY = (offsetY / boundingRect.height) * 100 + '%';
                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale_factor})`;
                });
                image.addEventListener('mouseout', function(event) {
                    image.style.transformOrigin = 'center center';
                    image.style.transform = 'scale(1)';
                });
            };

            function ImageZoomScroll(selector, scale_factor, increment) {
                const image = document.getElementById(selector);
                let scale = 1

                image.addEventListener('wheel', function(event) {
                    console.log(event)
                    event.preventDefault();
                    // Get the delta of the scroll event
                    var delta = event.deltaY || -event.detail;
                    if (delta === undefined) {
                        //we are on firefox
                        delta = e.originalEvent.detail;
                    }
                    const sign = Math.sign(delta);
                    scale += sign > 0 ? -increment : increment;
                    scale = Math.max(1, Math.min(scale_factor, scale));

                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = event.clientX - boundingRect.left;
                    const offsetY = event.clientY - boundingRect.top;
                    const originX = (offsetX / boundingRect.width) * 100 + '%';
                    const originY = (offsetY / boundingRect.height) * 100 + '%';
                    
                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale})`;
                });
                image.addEventListener('mouseout', function(event) {
                    image.style.transformOrigin = 'center center';
                    image.style.transform = 'scale(1)';
                    scale = 1
                });
            };
        
            function ImageZoomBoth(selector, scale_factor, increment) {
                const image = document.getElementById(selector);
                let scale = 1;

                image.addEventListener('mousemove', function(event) {
                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = event.clientX - boundingRect.left;
                    const offsetY = event.clientY - boundingRect.top;
                    const originX = (offsetX / boundingRect.width) * 100 + '%';
                    const originY = (offsetY / boundingRect.height) * 100 + '%';
                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale})`;
                });

                image.addEventListener('wheel', function(event) {
                    console.log(event);
                    event.preventDefault();
                    // Get the delta of the scroll event
                    var delta = event.deltaY || -event.detail;
                    if (delta === undefined) {
                        //we are on firefox
                        delta = e.originalEvent.detail;
                    }
                    const sign = Math.sign(delta);
                    scale += sign > 0 ? -increment : increment;
                    scale = Math.max(1, Math.min(scale_factor, scale));

                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = event.clientX - boundingRect.left;
                    const offsetY = event.clientY - boundingRect.top;
                    const originX = (offsetX / boundingRect.width) * 100 + '%';
                    const originY = (offsetY / boundingRect.height) * 100 + '%';

                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale})`;
                });

                image.addEventListener('mouseout', function(event) {
                    image.style.transformOrigin = 'center center';
                    image.style.transform = 'scale(1)';
                    scale = 1;
                });
            };
        </script>
    """

    # Assemble the HTML code with CSS and JS.
    html_code = f"""
    {css_code}
    <div id="container" style="width: {new_size[0]}px; height: {new_size[1]}px;">
        <img id="image" src="{img_base64}">
    </div>
    {js_code}
    <script>
    var mode = "{mode}";
    if (mode == "mousemove" || mode == "default") {{
        ImageZoomMouseMove('image', {zoom_factor});
    }} else if (mode == "scroll") {{
        ImageZoomScroll('image', {zoom_factor}, {increment});
    }} else if (mode == "both") {{
        ImageZoomBoth('image', {zoom_factor}, {increment});
    }}
    </script>
    """

    return components.html(html_code, width=new_size[0], height=new_size[1])
