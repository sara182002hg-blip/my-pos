import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS Modern POS", layout="wide", initial_sidebar_state="collapsed")

# 2. ปรับแต่ง CSS นิดหน่อยให้การ์ดดูสวย
st.markdown("""
    <style>
    .product-box {
        background-color: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        margin-bottom: 20px;
        cursor: pointer;
    }
    .price-text {
        color: #ff4b4b;
        font-weight: bold;
        font-size: 1.2em;
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

# ฟังก์ชันสำหรับเพิ่มสินค้าลงตะกร้า
def add_to_cart(name, price):
    st.session_state.cart.append({"Name": name, "Price": price})

if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

st.markdown("# 🏪 **TAS EASY TOUCH**")
st.caption("จิ้มที่รูปสินค้าได้เลยครับ | พร้อมเพย์: 094-501-6189")

df_products = load_products()
col1, col2 = st.columns([3, 1.2])

with col1:
    if not df_products.empty:
        grid = st.columns(4)
        for i, row in df_products.iterrows():
            with grid[i % 4]:
                # --- ส่วนสำคัญ: ปุ่มรูปภาพที่กดได้ ---
                # เราใช้ st.button ที่มีรูปภาพอยู่ข้างใน หรือใช้สไตล์ปุ่มแบบคลุมรูป
                with st.container():
                    st.image(row['Image_URL'], use_container_width=True)
                    # สร้างปุ่มที่ชื่อเดียวกับสินค้า วางไว้ใต้รูปเป๊ะๆ
                    if st.button(f"เลือก {row['Name']}\n\n{row['Price']:,} ฿", key=f"btn_{i}", use_container_width=True):
                        add_to_cart(row['Name'], row['Price'])
                        st.rerun()
    else:
        st.warning("กำลังโหลดข้อมูลสินค้า...")

with col2:
    st.subheader("🛒 รายการสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.markdown(f"**{item['Name']}** <span style='float:right;'>{item['Price']:,} ฿</span>", unsafe_allow_html=True)
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"### รวม: <span style='color:#27ae60'>{total:,.2f} บาท</span>", unsafe_allow_html=True)
        
        method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 โอนเงิน"], horizontal=True)
        
        if st.button("🏁 ยืนยันการขาย", type="primary", use_container_width=True):
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
            st.success(f"บันทึกสำเร็จ! {last['total']:,} ฿")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png", caption="สแกนเพื่อโอนเงิน")
            if st.button("รับลูกค้าใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.info("แตะปุ่มใต้รูปสินค้าเพื่อเลือกรายการ")
