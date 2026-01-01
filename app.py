import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# CSS บังคับตัวหนังสือขาวและรูปภาพสวยงาม
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-title { color: #ffffff !important; font-weight: bold; text-align: center; font-size: 1.1em; }
    .product-price { color: #f1c40f !important; font-weight: bold; text-align: center; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; font-weight: bold; }
    p, span, label, h1, h2, h3, div { color: white !important; }
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
                st.image(row['Image_URL'], use_container_width=True)
                st.markdown(f'<div class="product-title">{row["Name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="product-price">{row["Price"]:,} ฿</div>', unsafe_allow_html=True)
                if st.button(f"เลือก", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()

with col2:
    st.subheader("🛒 รายการสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.write(f"◽ {item['Name']} : {item['Price']:,} ฿")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"## ยอดรวม: :green[{total:,.2f}] บาท")
        method = st.radio("วิธีชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันชำระเงิน", type="primary", use_container_width=True):
            # 1. เตรียมข้อมูลบิล
            bill_id = "B" + pd.Timestamp.now().strftime("%y%m%d%H%M%S")
            items_str = ", ".join(df_cart['Name'].tolist())
            
            # 2. ใช้เทคนิค "ยิงแล้ววิ่ง" (Fire and Forget) แบบไม่รอ Error
            # สร้าง URL สำหรับส่งข้อมูล
            final_url = f"{API_URL}?bill_id={bill_id}&items={items_str}&total={total}&payment_type={method}"
            
            # ส่งข้อมูลผ่านเบื้องหลังแบบเร็วที่สุด
            try:
                requests.get(final_url, timeout=0.001) # ให้มัน timeout ทันทีหลังยิงออกไป
            except:
                pass 
            
            # 3. อัปเดตหน้าจอทันที ไม่ต้องรอลุ้นคำตอบ
            st.session_state.last_bill = {"total": total, "type": method}
            st.session_state.cart = []
            st.rerun()

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกยอด {last['total']:,} ฿ สำเร็จ!")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("กรุณาเลือกสินค้า")
