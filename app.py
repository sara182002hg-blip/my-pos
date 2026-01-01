import streamlit as st
import pandas as pd
import requests
from promptpay import qrcode # เพิ่มตัวสร้าง QR พร้อมเพย์
import io

# 1. ลิงก์บันทึกยอดขาย (Apps Script)
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลสินค้า (จาก Google Sheets)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=5)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

df_products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS (จ่ายผ่านพร้อมเพย์)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 เลือกสินค้า")
    if df_products.empty:
        st.error("❌ ไม่พบข้อมูลสินค้า")
    else:
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                name = str(row.get('Name', 'ไม่มีชื่อ'))
                price = row.get('Price', 0)
                img = str(row.get('Image_URL', 'https://via.placeholder.com/150'))
                st.image(img, use_container_width=True)
                if st.button(f"{name}\n{price:,.0f}.-", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": name, "Price": price})
                    st.rerun()

with col2:
    st.subheader("🛒 รายการที่สั่ง")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = df_cart['Price'].sum()
        st.write(f"### รวมทั้งสิ้น: {total:,.2f} บาท")
        
        # เบอร์พร้อมเพย์ของคุณ
        pp_number = "0945016189"

        if st.button("ชำระเงิน & บันทึกยอด"):
            data = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total)
            }
            try:
                res = requests.post(API_URL, json=data)
                if res.status_code == 200:
                    st.success(f"✅ บันทึกยอด {total} บาท สำเร็จ!")
                    
                    # --- ส่วนสร้าง QR Code พร้อมเพย์ของจริง ---
                    payload = qrcode.generate_payload(pp_number, total)
                    img = qrcode.to_image(payload)
                    
                    buf = io.BytesIO()
                    img.save(buf, format="PNG")
                    st.image(buf.getvalue(), caption=f"สแกนจ่าย {total} บาท (เบอร์ {pp_number})")
                    # ---------------------------------------
                    
                    st.session_state.cart = [] 
                else:
                    st.error("บันทึกไม่สำเร็จ")
            except Exception as e:
                st.error(f"เกิดข้อผิดพลาด: {e}")
                
        if st.button("ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("ยังไม่มีสินค้าในตะกร้า")
