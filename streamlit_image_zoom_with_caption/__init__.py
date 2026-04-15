import base64
import io
import json
import os.path
import textwrap
from typing import Optional, Tuple, Union, Final
from urllib.parse import urlparse

import numpy as np
import streamlit
import streamlit.components.v1 as components
from google.protobuf.json_format import ParseDict

from streamlit.logger import get_logger
from streamlit.proto.NewSession_pb2 import FontFace

from PIL import Image

__version__ = "0.0.4"

_LOGGER: Final = get_logger(__name__)


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


def collect_font_faces_css() -> str:
    """
    Collects font faces definitions from the config and create @font-face and @import rules for each of them.

    Returns:
        str: A string representing the font faces definitions in CSS.
    """
    font_faces = streamlit.get_option("theme.fontFaces")

    style = ""

    # see streamlit.runtime.app_session._populate_theme_msg()
    if isinstance(font_faces, str):
        try:
            font_faces = json.loads(font_faces)
        except Exception as e:
            _LOGGER.warning(
                "Failed to parse the theme.fontFaces config option with json.loads: %s.",
                font_faces,
                exc_info=e,
            )
            font_faces = None

    if font_faces is not None:
        for font_face in font_faces:
            try:
                if "weight" in font_face:
                    font_face["weight_range"] = str(font_face["weight"])
                    del font_face["weight"]

                face = ParseDict(font_face, FontFace())
                css_fields = {}
                import_url = None

                for field, value in face.ListFields():
                    if field.name == "url":
                        parsed_url = urlparse(value)
                        # check if url is for a file or a stylesheet
                        if os.path.splitext(parsed_url.path)[1] in [".woff", ".woff2", ".ttf", ".otf", ".eot", ".svg"]:
                            css_fields["src"] = f"url('{value}')"
                        else:   # else will use @import later to import the stylesheet
                            import_url = value
                    elif field.name in ["weight", "weight_range"]:
                        css_fields["font-weight"] = value
                    elif field.name == "unicode-range":
                        css_fields["unicode-range"] = value
                    else:
                        css_fields[f"font-{field.name}"] = f'"{value}", sans-serif'

                if import_url:
                    style += f"@import url('{import_url}');"

                style += textwrap.dedent("""
                @font-face {
                    %s
                }""") % "\n    ".join([f"{k}: {v};" for k, v in css_fields.items()])
            except Exception as e:  # noqa: PERF203
                _LOGGER.warning(
                    "Failed to parse the theme.fontFaces config option: %s.",
                    font_face,
                    exc_info=e,
                )

    return style


def image_zoom(
        image: Union[Image.Image, np.ndarray],
        mode: Optional[str] = "default",
        size: Optional[Union[int, Tuple[int, int]]] = 512,
        keep_aspect_ratio: Optional[bool] = True,
        keep_resolution: Optional[bool] = False,
        zoom_factor: Optional[Union[float, int]] = 2.0,
        increment: Optional[float] = 0.2,
        caption: Optional[str] = None,
        stretch: bool = False,
) -> components.html:
    """
    Display an image with interactive zoom functionality.

    Args:
        image (Union[Image.Image, np.ndarray]): The image to be displayed. It can be a PIL Image or a NumPy array.
        mode (Optional[str]): The mode of interaction for zooming. Valid options are "default" (zoom on mousemove),
            "mousemove" (zoom on mousemove), "scroll" (zoom on scroll), "both" (zoom on both mousemove and scroll)
            or "dragmove" (drag and move zoom: Single-click to zoom in, click and drag to move the zoomed image,
            and double-click to zoom out).
            Default is "default".
        size (Optional[Union[int, Tuple[int, int]]]): The desired size of the displayed image.
            If an integer is provided, the image will be resized to have that size (width = height).
            If a tuple of integers (width, height) is provided, the image will be resized to fit within
            the specified dimensions while maintaining its aspect ratio. Default is 512.
        keep_aspect_ratio (Optional[bool]): Whether to maintain the aspect ratio of the image during resizing.
            If True, the image will be resized while preserving its aspect ratio.
            If False, the image will be resized to exactly match the provided size without preserving aspect ratio.
            Default is True.
        keep_resolution (Optional[bool]): Whether to keep the original resolution for zooming.
            If True, use the original resolution for zooming. If False, use the resized image for zooming.
            Default is False.
            Note: Setting this parameter to True may result in slower performance, especially for images with large sizes.
        zoom_factor (Optional[Union[float, int]]): The zoom factor applied to the image when zooming in.
            Default is 2.0.
        increment (Optional[float]): The increment value for adjusting the zoom level when scrolling.
            Should be between 0 and 1. Default is 0.2.
        caption (Optional[str]): The caption for the displayed image.
            Default is None.
        stretch: (bool): Whether to adjust the component's size to the width and height of the parent container.
            Default is False.

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
            mode in ["default", "mousemove", "scroll", "both", "dragmove"]
    ), "Only valid event mode are default, mousemove, scroll and both. Default work with mousemove."
    zoom_factor = float(zoom_factor) if isinstance(zoom_factor, int) else zoom_factor
    assert increment <= 1.0 or increment > 0.0, "Increment should be between 0 and 1."

    # Check and convert to PIL image.
    image = check_image(image)
    # Resize image and convert to base64.
    if keep_resolution:
        img_orig_base64, orig_size = prepare_image(image, image.size, keep_aspect_ratio)
        img_resized_base64, resized_size = prepare_image(image, size, keep_aspect_ratio)
        params_keep_res = f"""
                                data-original-src="{img_orig_base64}" 
                                data-original-width="{orig_size[0]}" 
                                data-original-height="{orig_size[1]}"
                        """
    else:
        img_resized_base64, resized_size = prepare_image(image, size, keep_aspect_ratio)
        params_keep_res = ""

    theme = streamlit.context.theme.type
    caption_color = "#ffffff" if theme == "dark" else "#31333f"

    theme_font = streamlit.get_option("theme.font") or "inherit"

    # collect font faces and insert them in the style as iframes don't inherit styles from the parent document
    font_faces = collect_font_faces_css()

    css_code = f"""
        <style>
            {font_faces}
            #container {{
                position: relative;
                overflow: hidden;
                cursor: zoom-in;
            }}
            #image {{
                {"position: absolute;" if not stretch else ""}
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border-radius: 0.5rem;
            }}
            body {{
                margin: 0;
            }}
            
            p {{
                margin:0; 
                font-family: {theme_font}; 
                font-size: 0.875rem; 
                color: {caption_color}; 
                line-height: 1.4;
                opacity: 0.6;
            }}
            
        </style>
    """
    js_code = """
        <script>
            function calculateTransformOrigin(offsetX, offsetY, image, boundingRect, keep_resolution) {
                let originX, originY;
                if (keep_resolution) {
                    const original_width = parseInt(image.getAttribute('data-original-width'));
                    const original_height = parseInt(image.getAttribute('data-original-height'));
                    const originX_original = (offsetX / boundingRect.width) * original_width;
                    const originY_original = (offsetY / boundingRect.height) * original_height;
                    originX = (originX_original / original_width) * 100 + '%';
                    originY = (originY_original / original_height) * 100 + '%';
                } else {
                    originX = (offsetX / boundingRect.width) * 100 + '%';
                    originY = (offsetY / boundingRect.height) * 100 + '%';
                }
                return { originX, originY };
            }

            function ImageZoomMouseMove(selector, scale_factor, keep_resolution) {
                const image = document.getElementById(selector);
                image.addEventListener('mousemove', function(event) {
                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = (event.clientX - boundingRect.left);
                    const offsetY = (event.clientY - boundingRect.top);
                    const { originX, originY } = calculateTransformOrigin(offsetX, offsetY, image, boundingRect, keep_resolution);
                    if (keep_resolution) {
                        image.src = image.getAttribute('data-original-src');
                    }
                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale_factor})`;
                });
                
                image.addEventListener('mouseout', function(event) {
                    if (keep_resolution) {
                        image.src = image.getAttribute('src');
                    }
                    image.style.transformOrigin = 'center center';
                    image.style.transform = 'scale(1)';
                });
            };

            function ImageZoomScroll(selector, scale_factor, increment, keep_resolution) {
                const image = document.getElementById(selector);
                let scale = 1

                image.addEventListener('wheel', function(event) {
                    event.preventDefault();
                    // Get the delta of the scroll event
                    var delta = event.deltaY || -event.detail;
                    if (delta === undefined) {
                        //we are on firefox
                        delta = event.originalEvent.detail;
                    }
                    const sign = Math.sign(delta);
                    scale += sign > 0 ? -increment : increment;
                    scale = Math.max(1, Math.min(scale_factor, scale));

                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = event.clientX - boundingRect.left;
                    const offsetY = event.clientY - boundingRect.top;
                    const { originX, originY } = calculateTransformOrigin(offsetX, offsetY, image, boundingRect, keep_resolution);
                    if (keep_resolution) {
                        image.src = image.getAttribute('data-original-src');
                    }
                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale})`;
                });

                image.addEventListener('mouseout', function(event) {
                    if (keep_resolution) {
                        image.src = image.getAttribute('src');
                    }
                    image.style.transformOrigin = 'center center';
                    image.style.transform = 'scale(1)';
                    scale = 1
                });
            };

            function ImageZoomBoth(selector, scale_factor, increment, keep_resolution) {
                const image = document.getElementById(selector);
                let scale = 1;

                image.addEventListener('mousemove', function(event) {
                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = event.clientX - boundingRect.left;
                    const offsetY = event.clientY - boundingRect.top;
                    const { originX, originY } = calculateTransformOrigin(offsetX, offsetY, image, boundingRect, keep_resolution);
                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale})`;
                });

                image.addEventListener('wheel', function(event) {
                    event.preventDefault();
                    // Get the delta of the scroll event
                    var delta = event.deltaY || -event.detail;
                    if (delta === undefined) {
                        //we are on firefox
                        delta = event.originalEvent.detail;
                    }
                    const sign = Math.sign(delta);
                    scale += sign > 0 ? -increment : increment;
                    scale = Math.max(1, Math.min(scale_factor, scale));

                    const boundingRect = image.getBoundingClientRect();
                    const offsetX = event.clientX - boundingRect.left;
                    const offsetY = event.clientY - boundingRect.top;
                    const { originX, originY } = calculateTransformOrigin(offsetX, offsetY, boundingRect, keep_resolution);
                    if (keep_resolution) {
                        image.src = image.getAttribute('data-original-src');
                    }
                    image.style.transformOrigin = `${originX} ${originY}`;
                    image.style.transform = `scale(${scale})`;
                });

                image.addEventListener('mouseout', function(event) {
                    if (keep_resolution) {
                        image.src = image.getAttribute('src');
                    }
                    image.style.transformOrigin = 'center center';
                    image.style.transform = 'scale(1)';
                    scale = 1;
                });
            };

            function ImageDragMove(selector, scale_factor, keep_resolution) {
                const image = document.getElementById(selector);
                let scale = 1;
                let startX, startY, clickX, clickY;
                let initialX = 0, initialY = 0;
                let isDragging = false;
                let zoomed = false; 
                
                image.style.transition = 'transform 0.2s ease, left 0s, top 0s';

                let originalSrc, resizedSrc;
                if (keep_resolution) {
                    originalSrc = image.getAttribute('data-original-src');
                    resizedSrc = image.getAttribute('src');
                    if (!originalSrc) {
                        image.setAttribute('data-original-src', resizedSrc);
                        originalSrc = resizedSrc;
                    }
                }

                image.addEventListener('mousedown', (event) => {
                    if (zoomed) {
                        // Start dragging
                        startX = event.clientX;
                        startY = event.clientY;
                        initialX = image.offsetLeft;
                        initialY = image.offsetTop;
                        image.style.cursor = 'grabbing';
                        isDragging = true;
                        event.preventDefault();
                    } else {
                        // Record click position for zooming in
                        clickX = event.clientX;
                        clickY = event.clientY;
                    }
                });

                document.addEventListener('mouseup', (event) => {
                    if (zoomed && isDragging) {
                        // Stop dragging
                        isDragging = false;
                        image.style.cursor = 'grab';
                    } else if (!zoomed && !isDragging && Math.abs(event.clientX - clickX) < 5 && Math.abs(event.clientY - clickY) < 5) {
                        // Zoom in on click
                        const rect = image.getBoundingClientRect();
                        const offsetX = event.clientX - rect.left;
                        const offsetY = event.clientY - rect.top;
                        const originX = `${offsetX}px`;
                        const originY = `${offsetY}px`;

                        if (keep_resolution && originalSrc !== resizedSrc) {
                            image.src = originalSrc;
                        }

                        scale = scale_factor;
                        image.style.transformOrigin = `${originX} ${originY}`;
                        image.style.transform = `scale(${scale})`;
                        image.style.cursor = 'grab';
                        zoomed = true;
                    }
                });

                image.addEventListener('dblclick', (event) => {
                    if (zoomed) {
                        // Zoom out
                        image.style.transform = `scale(1)`;
                        image.style.left = '0';
                        image.style.top = '0';
                        image.style.cursor = 'zoom-in';
                        zoomed = false;
                        isDragging = false;
                        scale = 1;

                        if (keep_resolution && resizedSrc) {
                            image.src = resizedSrc;
                        }
                    }
                });

                document.addEventListener('mousemove', (event) => {
                    if (zoomed && isDragging) {
                        // Move the zoomed image
                        const dx = (event.clientX - startX);
                        const dy = (event.clientY - startY);
                        image.style.left = `${initialX + dx}px`;
                        image.style.top = `${initialY + dy}px`;
                    }
                });
            };
        </script>
    """

    # Assemble the HTML code with CSS and JS.
    script = f"""<script>
            var mode = "{mode}";
            if (mode == "mousemove" || mode == "default") {{
                ImageZoomMouseMove('image', {zoom_factor}, {str(keep_resolution).lower()});
            }} else if (mode == "scroll") {{
                ImageZoomScroll('image', {zoom_factor}, {increment},  {str(keep_resolution).lower()});
            }} else if (mode == "both") {{
                ImageZoomBoth('image', {zoom_factor}, {increment}, {str(keep_resolution).lower()});
            }} else if (mode == "dragmove") {{
                ImageDragMove('image', {zoom_factor}, {str(keep_resolution).lower()});
            }}
            </script>
            """

    if stretch:
        image_container_style = "width: 100%; height: 100%;"
    else:
        image_container_style = f"width: {resized_size[0]}px; height: {resized_size[1]}px;"

    caption_height = 0

    if not caption:
        html_code = f"""
            {css_code}
    
            <div id="container" style="{image_container_style}">
                <img id="image" src="{img_resized_base64}" {params_keep_res}>
            </div>
    
            {js_code}
            {script}
        """

    else:
        caption_height = 40
        html_code = f"""
            {css_code}
            <div id="container" style="{image_container_style}">
                <img id="image" src="{img_resized_base64}" {params_keep_res}>
               

            </div>
            <div data-testid="stImageCaption" class="st-emotion-cache-r8fbmg e1mq0gaz2" style="width: 100%; max-width: 100%; text-align: center; margin-top: 0.375rem; overflow-wrap: break-word; padding: 0.125rem;">
                <div data-testid="stCaptionContainer" class="st-emotion-cache-1jbidbm et2rgd20">
                    <p>
                        {caption}
                    </p>
                </div>
            </div>

            {js_code}
            {script}
            
        """

    if stretch:
        width = "stretch"
        height = "stretch"
    else:
        width = resized_size[0]
        height = resized_size[1] + caption_height

    return components.html(html_code, width=width, height=height)
