import streamlit as st
import pandas as pd
import requests
import segno
import io

# 1. ลิงก์ Apps Script ล่าสุดของคุณ (สำหรับการบันทึกยอดขาย)
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลสินค้าจากชีตใหม่ (หน้า Products)
# ใช้ ID: 1A18StFwB8KLcFUaeUSF48TZxbKSepM-MNX4suPPrFhg
SHEET_URL = "https://docs.google.com/spreadsheets/d/1A18StFwB8KLcFUaeUSF48TZxbKSepM-MNX4suPPrFhg/export?format=csv&gid=540097780"

st.set_page_config(page_title="POS TAS System", layout="wide")

# ฟังก์ชันดึงรายการสินค้า
@st.cache_data(ttl=30)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.to_dict('records')
    except Exception as e:
        st.error(f"ไม่สามารถดึงข้อมูลได้: {e}")
        return []

products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS (ข้อมูลจาก Google Sheets)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("รายการสินค้า")
    if not products:
        st.warning("⚠️ กำลังรอข้อมูลจาก Google Sheets... (ตรวจสอบการแชร์ลิงก์)")
    else:
        cols = st.columns(4)
        for i, item in enumerate(products):
            with cols[i % 4]:
                name = item.get('Name', 'ไม่มีชื่อ')
                price = item.get('Price', 0)
                img = item.get('Image_URL', 'https://via.placeholder.com/150')
                
                st.image(img, use_container_width=True)
                if st.button(f"{name}\n{price}.-", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": name, "Price": price})
                    st.rerun()

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = df_cart['Price'].sum()
        st.write
