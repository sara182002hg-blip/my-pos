import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS Modern POS", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS แบบใหม่: บังคับให้รูปภาพและปุ่มรวมเป็นเนื้อเดียวกัน
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        height: auto;
        padding: 10px;
        border-radius: 15px;
        border: 1px solid #eee;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        border: 1px solid #ff4b4b;
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    .stButton > button p {
        font-size: 1.1em;
        font-weight: bold;
        color: #2c3e50;
    }
    .product-img {
        width: 100%;
        border-radius: 10px;
        margin-bottom: 8px;
    }
    .price-tag {
        color: #e67e22;
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

if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

st.markdown("# 🏪 **TAS CLICK POS**")
st.caption("คลิกที่รูปสินค้าเพื่อเลือกรายการ | พร้อมเพย์: 094-501-6189")

df_products = load_products()
col1, col2 = st.columns([3, 1.2])

with col1:
    if not df_products.empty:
        # จัด Grid 4 คอลัมน์
        grid_cols = st.columns(4)
        for i, row in df_products.iterrows():
            with grid_cols[i % 4]:
                # สร้างเนื้อหาที่จะโชว์ในปุ่ม (รูป + ชื่อ + ราคา)
                content = f"{row['Name']} \n\n {row['Price']:,} ฿"
                
                # โชว์รูปภาพก่อน (เพื่อให้ดูเหมือนกดที่รูป)
                st.image(row['Image_URL'], use_container_width=True)
                
                # ปุ่มที่กดแล้วจะเพิ่มสินค้า
                if st.button(f"เลือก {row['Name']}", key=f"btn_{i}", use_container_width=True):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
                st.write("---") 
    else:
        st.warning("กำลังดึงข้อมูลสินค้า...")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.write(f"✅ {item['Name']} : **{item['Price']:,} ฿**")
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"### รวม: {total:,.2f} บาท")
        
        method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 โอนเงิน"], horizontal=True)
        
        if st.button("🏁 ยืนยันการขาย", type="primary", use_container_width=True):
            payload = {
                "bill_id": "B" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total),
                "payment_type": method
            }
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
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            if st.button("รับลูกค้าคนถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.info("ยังไม่มีสินค้า")
