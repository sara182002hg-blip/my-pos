import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS Modern POS", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS ขั้นสูง: สร้างปุ่มล่องหนทับรูปภาพ
st.markdown("""
    <style>
    /* บังคับให้คอลัมน์สินค้าเป็นตำแหน่งอ้างอิง */
    [data-testid="column"] {
        position: relative;
    }
    
    /* สไตล์ปุ่มกดที่ทำให้มองไม่เห็นแต่กดได้ (Invisible Button) */
    .stButton > button {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 250px; /* ความสูงโดยประมาณให้คลุมรูป */
        background-color: transparent !important;
        border: none !important;
        color: transparent !important;
        z-index: 10;
        cursor: pointer;
    }

    /* สไตล์การ์ดสินค้าที่โชว์ด้านล่างปุ่ม */
    .product-display {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        transition: transform 0.2s;
    }
    
    .product-display:hover {
        transform: scale(1.02);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }

    .price-text {
        color: #ff4b4b;
        font-weight: bold;
        font-size: 1.2em;
        margin-top: 5px;
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

st.markdown("# 🏪 **TAS TOUCH POS**")
st.caption("แตะที่รูปสินค้าเพื่อเพิ่มลงตะกร้า | พร้อมเพย์: 094-501-6189")

df_products = load_products()
col1, col2 = st.columns([3, 1.2])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                # 1. แสดงรูปภาพและชื่อก่อน (อยู่ด้านล่าง)
                st.markdown(f"""
                    <div class="product-display">
                        <img src="{row['Image_URL']}" style="width:100%; height:160px; object-fit:contain; border-radius:10px;">
                        <div style="margin-top:10px; font-weight:bold; height:40px; overflow:hidden;">{row['Name']}</div>
                        <div class="price-text">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # 2. วางปุ่มล่องหนไว้ด้านบน (Overlay)
                # เมื่อกดปุ่มล่องหนนี้ สินค้าจะเข้าตะกร้า
                if st.button("", key=f"overlay_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
    else:
        st.warning("กำลังโหลดข้อมูลสินค้า...")

with col2:
    st.subheader("🛒 รายการที่เลือก")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.markdown(f"**{item['Name']}** <span style='float:right;'>{item['Price']:,} ฿</span>", unsafe_allow_html=True)
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"### รวม: <span style='color:#27ae60'>{total:,.2f} บาท</span>", unsafe_allow_html=True)
        
        method = st.segmented_control("วิธีชำระเงิน", ["เงินสด", "โอนเงิน"], default="เงินสด")
        
        if st.button("🏁 ยืนยันชำระเงิน", type="primary", use_container_width=True):
            payload = {"bill_id": "B"+pd.Timestamp.now().strftime("%H%M%S"), "items": ", ".join(df_cart['Name'].tolist()), "total": float(total), "payment_type": method}
            try:
                requests.post(API_URL, json=payload)
                st.session_state.last_bill = {"total": total, "type": method}
                st.session_state.cart = []
                st.rerun()
            except: st.error("บันทึกผิดพลาด")

        if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"จ่ายสำเร็จ! {last['total']:,} ฿")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.info("แตะสินค้าด้านซ้ายได้เลย")
