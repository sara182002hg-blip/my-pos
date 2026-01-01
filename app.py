import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. CSS เดิมที่สวยอยู่แล้ว ล็อกขนาดรูปและตัวหนังสือขาว
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24;
        border-radius: 15px;
        border: 1px solid #333;
        padding: 10px;
        margin-bottom: 15px;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 320px;
    }
    .img-box {
        width: 100%; height: 160px;
        background-color: white; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden; margin-bottom: 10px;
    }
    .img-box img { max-width: 95%; max-height: 95%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; text-align: center; height: 2.5em; overflow: hidden; margin-top: 5px; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.2em; margin-bottom: 10px; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
    p, span, label, h1, h2, h3, div { color: white !important; }
    /* สไตล์ปุ่มลบเล็กๆ ในตะกร้า */
    .btn-remove { background-color: #ff4b4b !important; color: white !important; padding: 2px 5px !important; }
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
if 'cart' not in st.session_state: st.session_state.cart = {} # เปลี่ยนเป็น dict เพื่อเก็บจำนวน
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

# ฟังก์ชันจัดการตะกร้า
def add_to_cart(name, price):
    if name in st.session_state.cart:
        st.session_state.cart[name]['qty'] += 1
    else:
        st.session_state.cart[name] = {'price': price, 'qty': 1}

def remove_one(name):
    if name in st.session_state.cart:
        st.session_state.cart[name]['qty'] -= 1
        if st.session_state.cart[name]['qty'] <= 0:
            del st.session_state.cart[name]

st.title("🏪 TAS PROFESSIONAL POS")

df_products = load_products()
col1, col2 = st.columns([3.5, 1.3])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                st.markdown(f"""
                    <div class="product-card">
                        <div class="img-box"><img src="{row['Image_URL']}"></div>
                        <div class="p-name">{row['Name']}</div>
                        <div class="p-price">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"➕ เลือก", key=f"btn_{i}"):
                    add_to_cart(row['Name'], row['Price'])
                    st.rerun()
    else:
        st.info("กำลังโหลดสินค้า...")

with col2:
    st.subheader("🛒 รายการสินค้า")
    if st.session_state.cart:
        total = 0
        items_list = []
        
        for name, info in list(st.session_state.cart.items()):
            item_total = info['price'] * info['qty']
            total += item_total
            items_list.append(f"{name} x{info['qty']}")
            
            c_name, c_qty = st.columns([2, 1])
            with c_name:
                st.write(f"**{name}**\n({info['price']:,} ฿)")
            with c_qty:
                if st.button("❌", key=f"del_{name}"):
                    remove_one(name)
                    st.rerun()
                st.write(f"จำนวน: {info['qty']}")
            st.divider()
        
        st.markdown(f"## ยอดรวม: :green[{total:,.2f}] บาท")
        method = st.radio("วิธีชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันชำระเงิน", type="primary", use_container_width=True):
            bill_id = "B" + pd.Timestamp.now().strftime("%y%m%d%H%M%S")
            final_url = f"{API_URL}?bill_id={bill_id}&items={', '.join(items_list)}&total={total}&payment_type={method}"
            try:
                requests.get(final_url, timeout=0.001)
            except: pass 
            st.session_state.last_bill = {"total": total, "type": method}
            st.session_state.cart = {}
            st.rerun()

        if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
            st.session_state.cart = {}
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกสำเร็จ! ยอด {last['total']:,} ฿")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("กรุณาเลือกสินค้าด้านซ้าย")
