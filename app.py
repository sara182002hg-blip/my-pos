import streamlit as st
import pandas as pd
import requests
import segno

# ใส่ URL ที่ก๊อปปี้มาจาก Apps Script ตรงนี้
API_URL = "https://script.google.com/macros/s/AKfycbyMUkHtPHjusc714sbBJ9j1IZsYAOT9bB2geHRyA_KqqE-xXjpxXfKv7HJvb9TSmOav/exec"

st.set_page_config(page_title="My POS with Images", layout="wide")

# ข้อมูลสินค้าพร้อมรูปภาพ (คุณสามารถเปลี่ยนลิงก์รูปได้ตามใจชอบ)
products = [
    {"Name": "กาแฟดำ", "Price": 50, "Image": "https://cdn-icons-png.flaticon.com/512/1047/1047503.png"},
    {"Name": "ชาเขียว", "Price": 55, "Image": "https://cdn-icons-png.flaticon.com/512/3504/3504827.png"},
    {"Name": "ขนมปัง", "Price": 25, "Image": "https://cdn-icons-png.flaticon.com/512/3014/3014535.png"}
]

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS หน้าร้าน")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("เมนูสินค้า")
    cols = st.columns(3)
    for i, item in enumerate(products):
        with cols[i % 3]:
            st.image(item['Image'], width=100)
            if st.button(f"เพิ่ม {item['Name']}\n({item['Price']}.-)"):
                st.session_state.cart.append(item)
                st.rerun()

with col2:
    st.subheader("ยอดชำระ")
    if st.session_state.cart:
        df = pd.DataFrame(st.session_state.cart)
        st.table(df[['Name', 'Price']])
        total = df['Price'].sum()
        st.write(f"## รวม: {total} บาท")
        
        if st.button("ชำระเงิน & บันทึกยอด"):
            # 1. ส่งข้อมูลไป Google Sheets
            data = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df['Name'].tolist()),
                "total": int(total)
            }
            res = requests.post(API_URL, json=data)
            
            if res.status_code == 200:
                st.success("บันทึกยอดขายลง Google Sheets สำเร็จ!")
                # 2. สร้าง QR Code
                qr = segno.make_qr(f"PromptPay_Logic_For_{total}")
                st.image(qr.png_as_base64(scale=5), caption="สแกนจ่ายตรงนี้")
                st.session_state.cart = [] # ล้างตะกร้า
            else:
                st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ")




