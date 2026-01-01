import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS System", layout="wide")

# 2. ปรับแต่ง CSS ให้ตัวหนังสือชื่อสินค้าเด่นชัด
st.markdown("""
    <style>
    .product-title {
        font-size: 1.2em;
        font-weight: bold;
        color: #1E1E1E;
        margin-top: 10px;
        line-height: 1.2;
        height: 2.4em; /* ล็อกความสูงไว้ 2 บรรทัด */
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
    }
    .product-price {
        font-size: 1.3em;
        font-weight: bold;
        color: #FF4B4B;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        background-color: #007BFF;
        color: white;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #0056b3;
        color: white;
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

df_products = load_products()
col1, col2 = st.columns([2.8, 1.2])

with col1:
    if not df_products.empty:
        # จัด Grid 4 คอลัมน์
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                # แสดงรูปภาพ
                st.image(row['Image_URL'], use_container_width=True)
                
                # แสดงชื่อสินค้า (ตัวหนา ชัดเจน)
                st.markdown(f'<div class="product-title">{row["Name"]}</div>', unsafe_allow_html=True)
                
                # แสดงราคา (ตัวหนา สีแดง)
                st.markdown(f'<div class="product-price">{row["Price"]:,} ฿</div>', unsafe_allow_html=True)
                
                # ปุ่มกดเพิ่มลงตะกร้า
                if st.button(f"เพิ่มรายการ", key=f"item_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
                st.write("") # เพิ่มช่องว่างระหว่างแถว
    else:
        st.info("🔄 กำลังดึงข้อมูลสินค้า...")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.markdown(f"**{item['Name']}** <span style='float:right;'>{item['Price']:,} ฿</span>", unsafe_allow_html=True)
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"### รวมทั้งหมด: :red[{total:,.2f}] บาท")
        
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
            except: st.error("บันทึกไม่สำเร็จ")

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"ชำระเรียบร้อย {last['total']:,} ฿")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับบิลถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.info("ยังไม่มีสินค้าในตะกร้า")
