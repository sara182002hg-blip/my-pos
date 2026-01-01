import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS System", layout="wide")

# ปรับแต่งให้ปุ่มดูเด่นและกดง่าย
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        font-weight: bold;
        background-color: #ffffff;
        border: 2px solid #f0f2f6;
    }
    .stButton>button:hover {
        border: 2px solid #ff4b4b;
        color: #ff4b4b;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

st.title("🏪 TAS POS System")
st.write(f"ผู้ใช้งาน: แอดมิน | พร้อมเพย์: **094-501-6189**")

df_products = load_products()
col1, col2 = st.columns([2.5, 1])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                st.image(row['Image_URL'], use_container_width=True)
                # ปุ่มกดขนาดใหญ่ใต้รูป
                if st.button(f"➕ {row['Name']}\n{row['Price']:,} ฿", key=f"item_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
    else:
        st.info("🔄 กำลังดึงข้อมูลสินค้า...")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.markdown(f"• {item['Name']} : **{item['Price']:,} ฿**")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"### ยอดรวม: :red[{total:,.2f}] บาท")
        
        method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 โอนเงิน"], horizontal=True)
        
        if st.button("✅ ยืนยันชำระเงิน", type="primary", use_container_width=True):
            payload = {
                "bill_id": "B"+pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total),
                "payment_type": method
            }
            try:
                requests.post(API_URL, json=payload)
                st.session_state.last_bill = {"total": total, "type": method}
                st.session_state.cart = []
                st.rerun()
            except: st.error("บันทึกข้อมูลไม่สำเร็จ")

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกบิลล่าสุด {last['total']:,} ฿ เรียบร้อย!")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("เริ่มบิลใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("กรุณาเลือกสินค้าด้านซ้าย")
