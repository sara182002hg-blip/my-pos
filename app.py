import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลพื้นฐาน
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="POS TAS System", layout="wide")

# 2. ฟังก์ชันดึงข้อมูลสินค้า
@st.cache_data(ttl=1)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# 3. เริ่มหน้าจอ POS
st.title("🏪 ระบบ POS TAS (094-501-6189)")

df_products = load_products()
if 'cart' not in st.session_state:
    st.session_state.cart = []

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 สินค้าในร้าน")
    if not df_products.empty:
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                name = str(row['Name'])
                price = row['Price']
                img = row['Image_URL']
                st.image(img, use_container_width=True)
                if st.button(f"เลือก {name}\n{price}.-", key=f"p_{i}"):
                    st.session_state.cart.append({"Name": name, "Price": price})
                    st.rerun()
    else:
        st.warning("🔄 กำลังโหลดข้อมูลสินค้า... หากนานเกินไปโปรด Refresh หน้าเว็บ")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = sum(item['Price'] for item in st.session_state.cart)
        st.write(f"## ยอดรวม: {total:,.2f} บาท")
        
        if st.button("💰 ชำระเงิน", use_container_width=True):
            # บันทึกยอดไป Google Sheets
            payload = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total)
            }
            try:
                requests.post(API_URL, json=payload)
                st.success("✅ บันทึกยอดเรียบร้อย!")
                # แสดง QR Code พร้อมเพย์เบอร์คุณ
                st.image(f"https://promptpay.io/0945016189/{total}.png", caption="สแกนเพื่อจ่ายเงิน")
                st.session_state.cart = []
            except:
                st.error("❌ บันทึกไม่สำเร็จ แต่สามารถสแกนจ่ายได้ที่นี่")
                st.image(f"https://promptpay.io/0945016189/{total}.png")

        if st.button("❌ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
