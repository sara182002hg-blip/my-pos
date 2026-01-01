import streamlit as st
import pandas as pd
import requests
import time

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. ปรับปรุง CSS เน้นตัวหนังสือขาวและรูปภาพเท่ากัน
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="column"] {
        background-color: #1a1c24;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #333;
    }
    .product-title {
        color: #ffffff !important;
        font-size: 1.2em;
        font-weight: bold;
        text-align: center;
        margin: 10px 0;
        height: 1.5em;
        overflow: hidden;
    }
    .product-price {
        color: #f1c40f !important;
        font-size: 1.3em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        background-color: #28a745;
        color: white;
        border: none;
        height: 3em;
    }
    /* แก้ไขตัวหนังสือในส่วนต่างๆ ให้เป็นสีขาว */
    h1, h2, h3, p, span, label, div {
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
                # บังคับรูปให้เท่ากันเป๊ะ
                st.image(row['Image_URL'], use_container_width=True)
                st.markdown(f'<div class="product-title">{row["Name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="product-price">{row["Price"]:,} ฿</div>', unsafe_allow_html=True)
                
                if st.button(f"เลือก {row['Name']}", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
    else:
        st.info("🔄 กำลังโหลดข้อมูลสินค้า...")

with col2:
    st.subheader("🛒 รายการในตะกร้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.write(f"⬜ {item['Name']} : {item['Price']:,} ฿")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"## ยอดรวม: :green[{total:,.2f}] บาท")
        
        method = st.radio("วิธีชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันชำระเงิน", type="primary", use_container_width=True):
            payload = {
                "bill_id": "B"+pd.Timestamp.now().strftime("%y%m%d%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total),
                "payment_type": method
            }
            
            # --- ระบบส่งข้อมูลแบบ Retry (พยายามส่ง 3 ครั้งถ้าพลาด) ---
            success = False
            with st.spinner('กำลังบันทึกข้อมูล...'):
                for attempt in range(3):
                    try:
                        res = requests.post(API_URL, json=payload, timeout=10)
                        if res.status_code == 200:
                            success = True
                            break
                    except:
                        time.sleep(1) # รอ 1 วินาทีก่อนลองใหม่
            
            if success:
                st.session_state.last_bill = {"total": total, "type": method}
                st.session_state.cart = []
                st.rerun()
            else:
                st.error("❌ บันทึกข้อมูลไม่สำเร็จหลังจากพยายามหลายครั้ง โปรดลองกดอีกรอบ")

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกบิล {last['total']:,} ฿ สำเร็จ!")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("เลือกสินค้าเพื่อเริ่มการขาย")
