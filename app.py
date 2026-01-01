import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS Professional", layout="wide")

# 2. CSS ปรับรูปภาพให้เท่ากันและตัวหนังสือสีขาว
st.markdown("""
    <style>
    .main { background-color: #121212; } /* พื้นหลังแอปสีเข้ม */
    
    /* จัดการการ์ดสินค้า */
    .product-card {
        background-color: #1E1E1E; 
        padding: 15px; 
        border-radius: 15px; 
        border: 1px solid #333;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* ล็อกขนาดรูปภาพให้เท่ากันทุกรูป */
    .product-img {
        width: 100%;
        height: 180px;
        object-fit: cover; /* บังคับรูปให้เต็มกรอบโดยไม่เสียสัดส่วน */
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    /* ตัวหนังสือชื่อสินค้าสีขาว */
    .product-title {
        color: #FFFFFF;
        font-size: 1.1em;
        font-weight: bold;
        height: 2.5em;
        overflow: hidden;
        margin-bottom: 5px;
    }
    
    /* ตัวเลขราคาสีเหลืองทองเพื่อให้ตัดกับสีขาว */
    .product-price {
        color: #FFD700;
        font-size: 1.2em;
        font-weight: bold;
        margin-bottom: 10px;
    }
    
    /* ปรับแต่งปุ่มกด */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #4CAF50;
        color: white;
        border: none;
    }
    
    /* ปรับสีหัวข้อให้เป็นสีขาว */
    h1, h2, h3, p, span, label {
        color: white !important;
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

st.title("🏪 TAS PROFESSIONAL POS")

df_products = load_products()
col1, col2 = st.columns([3, 1.2])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                # แสดงการ์ดสินค้าด้วย HTML/CSS
                st.markdown(f"""
                    <div class="product-card">
                        <img src="{row['Image_URL']}" class="product-img">
                        <div class="product-title">{row['Name']}</div>
                        <div class="product-price">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # ปุ่มกดที่วางต่อจาก HTML การ์ด
                if st.button(f"➕ เลือก", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
    else:
        st.info("🔄 กำลังเตรียมหน้าร้าน...")

with col2:
    st.subheader("🛒 รายการในตะกร้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.markdown(f"⬜ {item['Name']} : **{item['Price']:,} ฿**")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"## ยอดรวม: :green[{total:,.2f}] บาท")
        
        method = st.radio("วิธีชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันชำระเงิน", type="primary", use_container_width=True):
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
            st.success(f"บันทึกบิล {last['total']:,} ฿ สำเร็จ!")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("เลือกสินค้าเพื่อเพิ่มลงตะกร้า")
