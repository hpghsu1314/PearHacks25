import streamlit as st
from Utils import user, utils  # Import user.py from the Utils folder

# Set page config
st.set_page_config(page_title="Add Restaurant", layout="centered")

if "restaurants" not in st.session_state:
    st.session_state.restaurants = []

    # Initialize session state if it doesn't exist
if "restrictions_to_add" not in st.session_state:
    st.session_state.restrictions_to_add = []

if "user" not in st.session_state:
    st.session_state.user = user.User("Test User", {})  # <-- Now creating User object


st.title("Add a New Restaurant")

# Set restaurant's name
active_restaurant_name = st.text_input("Restaurant Name")

upload_c = st.container(border=True)
upload_c.markdown("**Upload a PDF or image of your menu.**")

# Upload restaurant's menu
menu_pdf = upload_c.file_uploader("Upload Menu PDF", type="pdf")

# Upload a picture instead
picture = upload_c.file_uploader("Upload Menu Picture", type=["png", "jpg", "jpeg"])
if picture:
    menu_pdf = utils.process_uploaded_image(picture)

# Confirm button
ready = active_restaurant_name != "" and menu_pdf is not None
if st.button("Add Restaurant", disabled = not ready) and active_restaurant_name is not None and menu_pdf is not None:
    restaurant_object = utils.from_pdf_to_restaurant(menu_pdf, active_restaurant_name)
    st.header(f"Dishes for {restaurant_object.get_restaurant()}")

    for dish in restaurant_object.get_menu():
        c = st.container(border=True)
        with c:
            col0, col1, col2 = st.columns([2, 1, 4])
            col0.badge(dish.get_dish(), color="gray")
            # TODO Let people edit ingredients in their dish
            col1.text(f"${'{0:.2f}'.format(dish.get_price())}")
            col2.write(", ".join([item.capitalize() for item in dish.get_ingredients()]))

    st.session_state.restaurants.append(restaurant_object)