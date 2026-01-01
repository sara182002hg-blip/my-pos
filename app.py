import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. CSS ขั้นสูง: บังคับทุกกล่องให้สูงเท่ากันเป๊ะ
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    
    /* กล่องสินค้าครอบทั้งหมด */
    .product-card {
        background-color: #1a1c24;
        border-radius: 15px;
        border: 1px solid #333;
        padding: 10px;
        margin-bottom: 15px;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 320px; /* บังคับความสูงกล่องรวม */
    }

    /* กล่องรูปภาพ: หัวใจสำคัญที่ทำให้เท่ากัน */
    .img-box {
        width: 100%;
        height: 160px; /* ล็อกความสูงรูปภาพ */
        background-color: white;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin-bottom: 10px;
    }

    .img-box img {
        max-width: 95%;
        max-height: 95%;
        object-fit: contain; /* รูปไม่เบี้ยวแน่นอน */
    }

    .p-name {
        color: white !important;
        font-weight: bold;
        font-size: 1.1em;
        text-align: center;
        height: 2.5em; /* ล็อกความสูงชื่อ 2 บรรทัด */
        overflow: hidden;
        margin-top: 5px;
    }

    .p-price {
        color: #f1c40f !important;
        font-weight: bold;
        font-size: 1.2em;
        margin-bottom: 10px;
    }

    /* ปรับปุ่มเลือกให้ติดขอบล่าง */
    .stButton > button {
        width: 100%;
        border-radius: 8px;
        background-color: #28a745;
        color: white;
    }
    
    h1, h2, h3, p, span, label { color: white !important; }
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
col1, col2 = st.columns([3.5, 1.2])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                # ใช้ HTML สร้างโครงสร้าง Card ทั้งหมดยกเว้นปุ่ม
                st.markdown(f"""
                    <div class="product-card">
                        <div class="img-box">
                            <img src="{row['Image_URL']}">
                        </div>
                        <div class="p-name">{row['Name']}</div>
                        <div class="p-price">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # วางปุ่มแยกออกมาแต่อยู่ใต้ Card พอดี
                if st.button(f"เลือก {row['Name']}", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
    else:
        st.info("กำลังโหลดสินค้า...")

with col2:
    st.subheader("🛒 รายการสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.write(f"⬜ {item['Name']} : {item['Price']:,} ฿")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"## ยอดรวม: :green[{total:,.2f}] บาท")
        method = st.radio("วิธีชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันชำระเงิน", type="primary", use_container_width=True):
            bill_id = "B" + pd.Timestamp.now().strftime("%y%m%d%H%M%S")
            items_str = ", ".join(df_cart['Name'].tolist())
            final_url = f"{API_URL}?bill_id={bill_id}&items={items_str}&total={total}&payment_type={method}"
            try:
                requests.get(final_url, timeout=0.001)
            except: pass 
            st.session_state.last_bill = {"total": total, "type": method}
            st.session_state.cart = []
            st.rerun()

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกสำเร็จ! ยอด {last['total']:,} ฿")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("กรุณาเลือกสินค้า")
