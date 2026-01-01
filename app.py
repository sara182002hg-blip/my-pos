import streamlit as st
import pandas as pd
import requests
import segno
import io

# 1. ลิงก์บันทึกยอดขาย (Apps Script)
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลสินค้าที่เผยแพร่สำเร็จแล้ว
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=5)
def load_products():
    try:
        # ดึงข้อมูลจากลิงก์ CSV
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

df_products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS - ร้านค้าออนไลน์")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 รายการสินค้า")
    if df_products.empty:
        st.error("❌ ไม่สามารถดึงข้อมูลได้ โปรดกด Refresh หน้าเว็บอีกครั้ง")
    else:
        # แสดงสินค้า 4 ชิ้นต่อแถว
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                name = str(row.get('Name', 'ไม่มีชื่อ'))
                price = row.get('Price', 0)
                img = str(row.get('Image_URL', 'https://via.placeholder.com/150'))
                
                # แสดงรูปและปุ่มกดซื้อ
                st.image(img, use_container_width=True)
                if st.button(f"{name}\n{price:,.0f}.-", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": name, "Price": price})
                    st.rerun()

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = df_cart['Price'].sum()
        st.write(f"### ยอดรวม: {total:,.0f} บาท")
        
        if st.button("ชำระเงิน & บันทึกยอด"):
            data = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": int(total)
            }
            try:
                res = requests.post(API_URL, json=data)
                if res.status_code == 200:
                    st.success("✅ บันทึกยอดขายสำเร็จ!")
                    # สร้าง QR Code พร้อมเพย์ (เปลี่ยนเป็นเบอร์ของคุณได้)
                    qr = segno.make_qr(f"https://promptpay.io/0812345678/{total}")
                    img_buf = io.BytesIO()
                    qr.save(img_buf, kind='png', scale=5)
                    st.image(img_buf.getvalue(), caption="สแกนจ่ายเงิน")
                    st.session_state.cart = [] 
                else:
                    st.error("บันทึกไม่สำเร็จ")
            except:
                st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ")
                
        if st.button("ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("กรุณาเลือกสินค้า")
