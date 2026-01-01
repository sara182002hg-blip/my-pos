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

# เพิ่มสถานะการแสดง QR Code หลังชำระเงิน
if 'last_bill' not in st.session_state:
    st.session_state.last_bill = None

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

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = sum(item['Price'] for item in st.session_state.cart)
        st.write(f"## ยอดรวม: {total:,.2f} บาท")
        
        payment_method = st.radio("เลือกวิธีชำระเงิน:", ("เงินสด", "โอนเงิน (พร้อมเพย์)"), horizontal=True)
        
        if st.button("💰 ยืนยันการชำระเงิน", use_container_width=True, type="primary"):
            # เตรียมข้อมูลส่ง
            payload = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total),
                "payment_type": payment_method
            }
            
            try:
                # ส่งข้อมูลไปบันทึก
                requests.post(API_URL, json=payload)
                
                # เก็บค่าเพื่อแสดงผลหลังรีเซ็ตตะกร้า
                st.session_state.last_bill = {
                    "total": total,
                    "method": payment_method
                }
                
                # ✅ รีเซ็ตตะกร้าทันที
                st.session_state.cart = []
                st.rerun() 
            except:
                st.error("❌ บันทึกไม่สำเร็จ")

        if st.button("❌ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        # แสดงผลหลังจากรีเซ็ตตะกร้าแล้ว (เช่น โชว์ QR Code หรือข้อความสำเร็จ)
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"✅ ชำระเงิน ({last['method']}) เรียบร้อยแล้ว!")
            
            if last['method'] == "โอนเงิน (พร้อมเพย์)":
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png", caption=f"สแกนจ่าย {last['total']} บาท")
            else:
                st.balloons()
            
            if st.button("เริ่มบิลใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.info("ตะกร้าว่างเปล่า เลือกสินค้าได้เลยครับ")
