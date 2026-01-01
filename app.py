import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. CSS จัดการ Layout ให้คงที่
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24;
        border-radius: 15px;
        border: 1px solid #333;
        padding: 10px;
        margin-bottom: 5px;
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 280px; /* ปรับความสูงให้กระชับขึ้น */
    }
    .img-box {
        width: 100%; height: 150px;
        background-color: white; border-radius: 10px;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden; margin-bottom: 8px;
    }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; text-align: center; height: 2.4em; overflow: hidden; font-size: 0.95em; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: bold; transition: 0.3s; }
    /* ปรับแต่ง Scrollbar ของตะกร้า */
    .cart-container { max-height: 400px; overflow-y: auto; padding-right: 10px; }
    p, span, label, h1, h2, h3, div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. ฟังก์ชันโหลดข้อมูล (เพิ่มระบบ Cache เพื่อความเร็ว)
@st.cache_data(ttl=60)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# เตรียม Session State สำหรับตะกร้า
if 'cart' not in st.session_state:
    st.session_state.cart = {}

st.title("🏪 TAS PROFESSIONAL POS")

df_products = load_products()
col_main, col_cart = st.columns([3.6, 1.4])

# ส่วนแสดงสินค้า
with col_main:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                # แสดง Card สินค้า
                st.markdown(f"""
                    <div class="product-card">
                        <div class="img-box"><img src="{row['Image_URL']}"></div>
                        <div class="p-name">{row['Name']}</div>
                        <div class="p-price">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # ปุ่มเลือก (ใช้การอัปเดต State โดยตรงเพื่อลดการหน่วง)
                if st.button(f"➕ เลือก", key=f"add_{i}"):
                    name, price = row['Name'], row['Price']
                    if name in st.session_state.cart:
                        st.session_state.cart[name]['qty'] += 1
                    else:
                        st.session_state.cart[name] = {'price': price, 'qty': 1}
                    st.rerun() # รีรันเฉพาะเมื่อมีการเปลี่ยนแปลงจริง
    else:
        st.info("กำลังโหลดข้อมูลสินค้า...")

# ส่วนตะกร้าสินค้า
with col_cart:
    st.subheader("🛒 รายการสินค้า")
    
    if st.session_state.cart:
        total = 0
        items_summary = []
        
        # ใส่ Container เพื่อจัดการพื้นที่ตะกร้า
        with st.container():
            for name, info in list(st.session_state.cart.items()):
                item_total = info['price'] * info['qty']
                total += item_total
                items_summary.append(f"{name} (x{info['qty']})")
                
                c1, c2 = st.columns([3, 1.2])
                with c1:
                    st.markdown(f"**{name}**")
                    st.caption(f"{info['qty']} ชิ้น x {info['price']:,} ฿")
                with c2:
                    if st.button("❌", key=f"del_{name}"):
                        st.session_state.cart[name]['qty'] -= 1
                        if st.session_state.cart[name]['qty'] <= 0:
                            del st.session_state.cart[name]
                        st.rerun()
                st.divider()

        st.markdown(f"### รวม: :orange[{total:,.2f}] บาท")
        method = st.radio("ชำระเงิน:", ("เงินสด", "โอนเงิน"), horizontal=True)
        
        if st.button("💰 ยืนยันการขาย", type="primary", use_container_width=True):
            bill_id = "B" + pd.Timestamp.now().strftime("%y%m%d%H%M%S")
            params = {
                "bill_id": bill_id,
                "items": ", ".join(items_summary),
                "total": float(total),
                "payment_type": method
            }
            # ยิงข้อมูลออกไปทันที
            try: requests.get(API_URL, params=params, timeout=0.1)
            except: pass
            
            st.session_state.last_bill = {"total": total, "type": method}
            st.session_state.cart = {}
            st.rerun()

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = {}
            st.rerun()
            
    elif 'last_bill' in st.session_state and st.session_state.last_bill:
        last = st.session_state.last_bill
        st.success(f"บันทึกยอด {last['total']:,} ฿ สำเร็จ")
        if "โอน" in last['type']:
            st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
        if st.button("บิลถัดไป"):
            st.session_state.last_bill = None
            st.rerun()
    else:
        st.write("ยังไม่มีสินค้า")
