import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลพื้นฐาน
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=1)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

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
        st.warning("🔄 กำลังโหลดข้อมูลสินค้า...")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = sum(item['Price'] for item in st.session_state.cart)
        st.write(f"## ยอดรวม: {total:,.2f} บาท")
        
        # --- เพิ่มส่วนเลือกวิธีชำระเงิน ---
        payment_method = st.radio("เลือกวิธีชำระเงิน:", ("เงินสด", "โอนเงิน (พร้อมเพย์)"), horizontal=True)
        
        if st.button("💰 ยืนยันการชำระเงิน", use_container_width=True, type="primary"):
            payload = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total),
                "payment_type": payment_method # ส่งประเภทการจ่ายเงินไปด้วย
            }
            
            try:
                requests.post(API_URL, json=payload)
                st.success(f"✅ บันทึกยอดขาย ({payment_method}) สำเร็จ!")
                
                # ถ้าเลือก "โอนเงิน" ให้โชว์ QR Code
                if payment_method == "โอนเงิน (พร้อมเพย์)":
                    st.image(f"https://promptpay.io/0945016189/{total}.png", caption=f"สแกนจ่าย {total} บาท")
                else:
                    st.balloons() # ถ้าจ่ายเงินสดให้ขึ้นเอฟเฟกต์ฉลอง
                
                st.session_state.cart = []
            except:
                st.error("❌ บันทึกไม่สำเร็จ")
        
        if st.button("❌ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("กรุณาเลือกสินค้า")
