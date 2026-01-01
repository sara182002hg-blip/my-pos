import streamlit as st
import pandas as pd
import requests
import segno
import io

# 1. ลิงก์ Apps Script ล่าสุดของคุณ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลจากหน้า Products (ระบุ gid=540097780)
SHEET_URL = "https://docs.google.com/spreadsheets/d/1A18StFwB8KLcFUaeUSF48TZxbKSepM-MNX4suPPrFhg/export?format=csv&gid=540097780"

st.set_page_config(page_title="POS TAS System", layout="wide")

# ฟังก์ชันดึงรายการสินค้า
@st.cache_data(ttl=10)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        return df.to_dict('records')
    except:
        return []

products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS (ข้อมูลสดจาก Google Sheets)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("รายการสินค้า")
    if not products:
        st.error("❌ ไม่พบข้อมูลในหน้า Products (ตรวจสอบการแชร์หรือลิงก์ SHEET_URL)")
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
        st.write(f"### รวมทั้งสิ้น: {total} บาท")
        
        if st.button("ชำระเงิน & บันทึกยอด"):
            data = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": int(total)
            }
            try:
                res = requests.post(API_URL, json=data)
                if res.status_code == 200:
                    st.success("✅ บันทึกยอดสำเร็จ!")
                    # สร้าง QR Code พร้อมเพย์
                    qr = segno.make_qr(f"https://promptpay.io/0812345678/{total}")
                    img_buf = io.BytesIO()
                    qr.save(img_buf, kind='png', scale=5)
                    st.image(img_buf.getvalue(), caption="สแกนเพื่อชำระเงิน")
                    st.session_state.cart = [] 
                else: st.error("❌ บันทึกไม่สำเร็จ")
            except Exception as e: st.error(f"⚠️ เกิดข้อผิดพลาด: {e}")
                
        if st.button("ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else: st.write("ตะกร้าว่างเปล่า")
