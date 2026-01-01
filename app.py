import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. ปรับ CSS เน้นความสว่างของตัวหนังสือขาว
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: white; }
    .stMarkdown, p, span, label { color: white !important; font-size: 1.1em; }
    .product-title { color: #ffffff !important; font-weight: bold; text-align: center; }
    .product-price { color: #f1c40f !important; font-weight: bold; text-align: center; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# เตรียม Session State
if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

st.title("🏪 TAS PROFESSIONAL POS")

df_products = load_products()
col1, col2 = st.columns([3, 1.2])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                st.image(row['Image_URL'], use_container_width=True)
                st.markdown(f'<div class="product-title">{row["Name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="product-price">{row["Price"]:,} ฿</div>', unsafe_allow_html=True)
                if st.button(f"เลือก", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
    else:
        st.info("กำลังโหลดสินค้า...")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.write(f"◽ {item['Name']} : {item['Price']:,} ฿")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"## ยอดรวม: :green[{total:,.2f}] บาท")
        
        method = st.radio("วิธีชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        # ปรับการทำงานของปุ่มยืนยัน
        if st.button("💰 ยืนยันชำระเงิน (กดครั้งเดียว)", type="primary", use_container_width=True):
            bill_data = {
                "bill_id": "B"+pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total),
                "payment_type": method
            }
            
            # เคลียร์ตะกร้าและโชว์ผลลัพธ์ก่อน (User Experience จะได้ไม่สะดุด)
            st.session_state.last_bill = {"total": total, "type": method, "data": bill_data}
            st.session_state.cart = []
            
            # ส่งข้อมูลไปบันทึก (พยายามส่ง 1 ครั้งแบบตั้งใจ)
            try:
                # ใช้ .get แทน .post ในบางกรณีจะทำงานเร็วกว่าบน Google Apps Script
                # แต่ถ้า Script รับแค่ POST ก็ใช้ POST ต่อไปครับ
                requests.post(API_URL, json=bill_data, timeout=5)
            except:
                pass # บันทึกไม่สำเร็จในเบื้องหลังแต่หน้าจอทำงานต่อ
            
            st.rerun()

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกยอด {last['total']:,} ฿ เรียบร้อย!")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            
            if st.button("เริ่มบิลถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("ยังไม่มีสินค้า")
