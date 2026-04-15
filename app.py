import numpy as np
import streamlit as st
from PIL import Image

from streamlit_image_zoom import image_zoom


def init_variables():
    if "img_ref" not in st.session_state:
        st.session_state.img_ref = np.array(Image.open("images/building.jpg"))
    if "show_img" not in st.session_state:
        st.session_state.show_img = st.session_state.img_ref
    if "size_image" not in st.session_state:
        st.session_state.size_image = 1024


def load_image(file):
    # Function to read and convert to np.array.
    image = np.array(Image.open(file).convert("RGB"))

    return image


def plot_images(img):
    st.session_state.show_img = img

    if all(dim < 512 for dim in img.shape[:2]):
        st.session_state.size_image = 512
    else:
        st.session_state.size_image = 768


# INTRO ###############################################################################################
def main():
    # Cached parameters
    if "loaded" not in st.session_state:
        init_variables()
        st.session_state.loaded = True
        hide_img_fs = """<style>
            button[title="View fullscreen"]{
            visibility: hidden;}
            </style>
        """
        st.markdown(hide_img_fs, unsafe_allow_html=True)

    #######################################################################################################
    # --- Side bar ---
    st.sidebar.subheader("Options menu")
    st.sidebar.subheader("⏏️ Upload image")
    # Allow the user to upload a files
    st.session_state.uploaded = st.sidebar.file_uploader(
        "Choose an image file",
        accept_multiple_files=False,
        type=["png", "jpg", "jpeg", "tiff", "bmp"],
        key="file_uploader1",
    )
    
    if st.session_state.uploaded is not None:
        img = load_image(st.session_state.uploaded)
        st.session_state.image_name = st.session_state.uploaded.name
        st.sidebar.button("Process", on_click=plot_images, args=(img,))
    else:
        st.session_state.show_img = st.session_state.img_ref
        st.session_state.image_name = "no-image.jpg"
    st.sidebar.divider()

    mode = st.sidebar.radio("Select mode:", ["mousemove", "scroll", "both", "dragmove"], index=0)
    zoom_factor = st.sidebar.slider(
        "Select zoom factor:", min_value=1, max_value=5, value=2, step=1
    )
    if mode not in ["mousemove", "dragmove"]:
        increase_factor = st.sidebar.slider(
            "Select increase factor:", min_value=0.0, max_value=1.0, value=0.2, step=0.1
        )
    else:
        increase_factor = 0.0

    keep_res = st.sidebar.checkbox("Keep resolution")

    st.sidebar.divider()

    ####################################################################
    # --- Main space ---
    # Header
    st.title("Streamlit Image Zoom")
    image_zoom(
        image=st.session_state.show_img,
        mode=mode,
        size=st.session_state.size_image,
        zoom_factor=zoom_factor,
        increment=increase_factor,
        keep_resolution=keep_res,
        caption='Image zoom'
    )


if __name__ == "__main__":
    try:
        # Browser tab configuration
        st.set_page_config(
            page_title="Image Zoom",
            layout="wide",
        )
        main()

    except Exception as e:
        st.error(
            "⚠️ Something went wrong! Please contact with administrator and share the error message below ⚠️"
        )
        raise e
