import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS Modern POS", layout="wide", initial_sidebar_state="collapsed")

# 2. ปรับแต่ง CSS เพื่อความสวยงาม
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; font-weight: bold; }
    .product-card {
        background-color: white; padding: 15px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); text-align: center; margin-bottom: 20px;
    }
    .price-tag { color: #ff4b4b; font-size: 1.2em; font-weight: bold; }
    .cart-section { background-color: #ffffff; padding: 20px; border-radius: 20px; border: 1px solid #e0e0e0; }
    h1, h2, h3 { color: #2c3e50; }
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

# ส่วนหัวของโปรแกรม
st.markdown("# 🏪 **TAS MODERN POS**")
st.caption("ระบบจัดการร้านค้าอัจฉริยะ | เบอร์พร้อมเพย์: 094-501-6189")
st.divider()

df_products = load_products()
col1, col2 = st.columns([2.5, 1])

with col1:
    st.subheader("🛍️ รายการสินค้า")
    if not df_products.empty:
        # แสดงสินค้าเป็น Grid
        items_per_row = 4
        for i in range(0, len(df_products), items_per_row):
            cols = st.columns(items_per_row)
            for j in range(items_per_row):
                if i + j < len(df_products):
                    row = df_products.iloc[i + j]
                    with cols[j]:
                        st.markdown(f'<div class="product-card">', unsafe_allow_html=True)
                        st.image(row['Image_URL'], use_container_width=True)
                        st.markdown(f"**{row['Name']}**")
                        st.markdown(f'<p class="price-tag">{row["Price"]:,} ฿</p>', unsafe_allow_html=True)
                        if st.button(f"➕ เพิ่ม", key=f"add_{i+j}"):
                            st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                            st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("กำลังโหลดข้อมูลสินค้า...")

with col2:
    st.markdown('<div class="cart-section">', unsafe_allow_html=True)
    st.subheader("🛒 ตะกร้าสินค้า")
    
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        # แสดงตารางแบบย่อ
        for idx, item in df_cart.iterrows():
            st.write(f"🔹 {item['Name']} : **{item['Price']:,} ฿**")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"### ยอดรวม: <span style='color:red'>{total:,.2f} บาท</span>", unsafe_allow_html=True)
        
        pay_type = st.segmented_control("วิธีชำระเงิน", ["💵 เงินสด", "📱 โอนเงิน"], default="💵 เงินสด")
        
        if st.button("🔥 ยืนยันชำระเงิน", type="primary"):
            try:
                payload = {
                    "bill_id": "B" + pd.Timestamp.now().strftime("%y%m%d%H%M"),
                    "items": ", ".join(df_cart['Name'].tolist()),
                    "total": float(total),
                    "payment_type": pay_type
                }
                requests.post(API_URL, json=payload)
                st.session_state.last_bill = {"total": total, "type": pay_type}
                st.session_state.cart = []
                st.rerun()
            except: st.error("ระบบบันทึกมีปัญหา")

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"ชำระสำเร็จ: {last['total']:,} ฿")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            else:
                st.balloons()
            if st.button("บิลถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("ยังไม่มีสินค้าในตะกร้า")
    st.markdown('</div>', unsafe_allow_html=True)
