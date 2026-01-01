import streamlit as st
import pandas as pd
import requests
import segno
import io

# ฟังก์ชันสร้างรหัส พร้อมเพย์ (แบบไม่ต้องลง Library เพิ่ม)
def generate_promptpay_code(phone, amount):
    target = phone.replace("-", "").[:10]
    target = "00066" + target if len(target) == 10 else target
    amount_str = f"{amount:.2f}".replace(".", "")
    amount_len = f"{len(f'{amount:.2f}'):02d}"
    
    # โครงสร้างพื้นฐานของ PromptPay
    payload = f"00020101021129370016A000000677010111011300{len(target):02d}{target}5802TH54{amount_len}{amount:.2f}5303764"
    
    # คำนวณ CRC16 (แบบง่ายเพื่อให้สแกนติด)
    # สำหรับการใช้งานจริงแนะนำการใช้ Library แต่เพื่อให้ผ่าน Error ติดตั้ง เราจะใช้ลิงก์ API แทนครับ
    return f"https://promptpay.io/{phone}/{amount}.png"

# 1. ลิงก์บันทึกยอดขาย
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลสินค้า
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=5)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

df_products = load_products()
if 'cart' not in st.session_state: st.session_state.cart = []

st.title("🏪 ระบบ POS TAS (จ่ายผ่าน 094-501-6189)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 รายการสินค้า")
    if not df_products.empty:
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                name, price = row['Name'], row['Price']
                img = row.get('Image_URL', 'https://via.placeholder.com/150')
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
        st.write(f"## รวม: {total:,.2f} บาท")
        
        if st.button("ยืนยันชำระเงิน"):
            # บันทึกยอดขาย
            data = {"bill_id": "BILL-"+pd.Timestamp.now().strftime("%H%M%S"), "items": ", ".join(df_cart['Name'].tolist()), "total": float(total)}
            try:
                res = requests.post(API_URL, json=data)
                if res.status_code == 200:
                    st.success("✅ บันทึกยอดเรียบร้อย!")
                    # แสดง QR Code พร้อมเพย์จากเบอร์ 0945016189
                    qr_url = f"https://promptpay.io/0945016189/{total}.png"
                    st.image(qr_url, caption=f"สแกนจ่ายเงินเข้าเบอร์ 094-501-6189 ยอด {total} บาท")
                    st.session_state.cart = []
                else: st.error("บันทึกไม่สำเร็จ")
            except: st.error("การเชื่อมต่อมีปัญหา")
            
        if st.button("ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
