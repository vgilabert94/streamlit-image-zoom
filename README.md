# Image Zoom - Streamlit Component

This repository presents a Python Streamlit component that wraps HTML, CSS, and JS code, enabling the creation of an interactive image zoom application.

<p align="center">
    <img src="images/mousemove.gif" width="512"/>
</p>


## Installation
- Install via pip:

```bash
pip install streamlit
pip install streamlit-image-zoom
```

- Install via git clone:
```bash
git clone https://github.com/vgilabert94/streamlit-image-zoom
```

## Documentation
### Main function

```python
def image_zoom(image: Union[Image.Image, np.ndarray],
                mode: Optional[str] = "default",
                size: Optional[Union[int, Tuple[int, int]]] = 512,
                keep_aspect_ratio: Optional[bool] = True,
                zoom_factor: Optional[Union[float, int]] = 2.0,
                increment: Optional[float] = 0.2,
            ) -> HTML:

    return component
```

### Parameters

- `image`: The image to be displayed. It can be either a PIL Image or a NumPy array.
- `mode`: The mode of interaction for zooming. Valid options are "default" (zoom on mousemove), "mousemove" (zoom on mousemove), "scroll" (zoom on scroll), or "both" (zoom on both mousemove and scroll). Default is "default".
- `size`: The desired size of the displayed image. If an integer is provided, the image will be resized to have that size (width = height). If a tuple of integers (width, height) is provided, the image will be resized to fit within the specified dimensions while maintaining its aspect ratio. Default is 512.
- `keep_aspect_ratio`: Whether to maintain the aspect ratio of the image during resizing. If True, the image will be resized while preserving its aspect ratio. If False, the image will be resized to exactly match the provided size without preserving aspect ratio. Default is True.
- `keep_resolution`: Whether to keep the original resolution for zooming. If True, use the original resolution for zooming. If False, use the resized image for zooming. Default is False.  
Note: Setting this parameter to True may result in slower performance, especially for images with large sizes.
- `zoom_factor`: The zoom factor applied to the image when zooming in. Default is 2.0.
- `increment`: The increment value for adjusting the zoom level when scrolling. Should be between 0 and 1. Default is 0.2.


## Modes

Here's a list explaining the operation of each mode in the app:

### mousemove or default
As you move the mouse, the zoom level adjusts accordingly, providing a dynamic zoom experience.
<p align="center">
    <img src="images/mousemove.gif" width="512"/>
</p>

### scroll
Zooming is activated exclusively by scrolling (wheel).  
<p align="center">
    <img src="images/scroll.gif" width="512"/>
</p>

### both
This mode combines the functionalities of both "mousemove" and "scroll" modes, allowing users to navigate the image with a fixed zoom level.
Zooming is activated by scrolling (using the mouse wheel) and moving the mouse cursor, offering flexibility in how users interact with the zoom feature.
<p align="center">
    <img src="images/both.gif" width="512"/>
</p>

## Examples

```python
import streamlit as st
from streamlit_image_zoom import image_zoom
from PIL import Image
import cv2

# Supported Image Formats
# PIL image
from PIL import Image
image = Image.open("images/building.jpg")

# Numpy array (opencv, scikit-image, etc)
import cv2
image = cv2.cvtColor(cv2.imread("image.jpg"), cv2.COLOR_BGR2RGB)

# Display image with default settings
image_zoom(image)

# Display image with custom settings
image_zoom(image, mode="scroll", size=(800, 600), keep_aspect_ratio=False, zoom_factor=4.0, increment=0.2)
```

## License
Distributed under the MIT License. See LICENSE.txt for more information.

## Contact

[Vicent Gilabert](mailto:gilabert_vicent@hotmail.com)

[Linkedin](https://www.linkedin.com/in/vgilabert/)


## References
- https://github.com/fcakyon/streamlit-image-comparison
- https://codepen.io/parvezlm/pen/qBNrrwg
- https://jsfiddle.net/xta2ccdt/13/
- https://www.w3schools.com/howto/tryit.asp?filename=tryhow_js_image_zoom
