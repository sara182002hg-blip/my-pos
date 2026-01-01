import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. CSS จัดการรูปภาพและตัวหนังสือ
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24;
        border-radius: 15px;
        border: 1px solid #333;
        padding: 10px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 300px;
    }
    .img-box {
        width: 100%; height: 160px;
        background-color: white; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden; margin-bottom: 10px;
    }
    .img-box img { max-width: 95%; max-height: 95%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; text-align: center; height: 2.5em; overflow: hidden; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.2em; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; }
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

# เตรียมระบบตะกร้าสินค้า
if 'cart' not in st.session_state:
    st.session_state.cart = {} # ใช้ชื่อสินค้าเป็น Key

st.title("🏪 TAS PROFESSIONAL POS")

df_products = load_products()
col1, col2 = st.columns([3.5, 1.5])

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
                
                # ปุ่มกดเพิ่มสินค้า (แก้ไขให้ทำงานร่วมกับ Dictionary)
                if st.button(f"➕ เลือก", key=f"add_{i}"):
                    name = row['Name']
                    price = row['Price']
                    if name in st.session_state.cart:
                        st.session_state.cart[name]['qty'] += 1
                    else:
                        st.session_state.cart[name] = {'price': price, 'qty': 1}
                    st.rerun()
    else:
        st.info("กำลังโหลดสินค้า...")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        total = 0
        items_summary = []
        
        # วนลูปแสดงรายการในตะกร้า
        for name, info in list(st.session_state.cart.items()):
            item_price_total = info['price'] * info['qty']
            total += item_price_total
            items_summary.append(f"{name} (x{info['qty']})")
            
            # แสดงแถวสินค้าและปุ่มลบ
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{name}** x {info['qty']}")
                st.caption(f"{item_price_total:,} ฿")
            with c2:
                if st.button("❌", key=f"remove_{name}"):
                    st.session_state.cart[name]['qty'] -= 1
                    if st.session_state.cart[name]['qty'] <= 0:
                        del st.session_state.cart[name]
                    st.rerun()
            st.divider()
            
        st.markdown(f"### รวมทั้งหมด: :green[{total:,.2f}] บาท")
        method = st.radio("การชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันการขาย", type="primary", use_container_width=True):
            bill_id = "B" + pd.Timestamp.now().strftime("%y%m%d%H%M%S")
            # ยิงข้อมูลไป Google Sheets
            params = {
                "bill_id": bill_id,
                "items": ", ".join(items_summary),
                "total": float(total),
                "payment_type": method
            }
            try:
                requests.get(API_URL, params=params, timeout=0.1)
            except: pass
            
            # บันทึกสถานะบิลล่าสุดและล้างตะกร้า
            st.session_state.last_bill = {"total": total, "type": method}
            st.session_state.cart = {}
            st.rerun()

        if st.button("🗑️ ล้างตะกร้าทั้งหมด"):
            st.session_state.cart = {}
            st.rerun()
    else:
        if 'last_bill' in st.session_state and st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกยอด {last['total']:,} ฿ เรียบร้อย!")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับบิลใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("ยังไม่มีสินค้าในตะกร้า")
