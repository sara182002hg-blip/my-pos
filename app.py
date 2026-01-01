import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. CSS จัดการ Layout (ล็อกความสูง ไม่ให้หน้าจอกระตุกตอนโหลด)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 8px; margin-bottom: 5px; display: flex; flex-direction: column;
        align-items: center; height: 260px;
    }
    .img-box {
        width: 100%; height: 140px; background-color: white; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden; margin-bottom: 5px;
    }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; text-align: center; height: 2em; overflow: hidden; font-size: 0.9em; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.1em; }
    .stButton > button { width: 100%; border-radius: 6px; font-weight: bold; height: 2.5em; }
    p, span, label, h1, h2, h3, div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. ระบบจัดการข้อมูล (โหลดครั้งเดียวเก็บยาว)
if 'product_list' not in st.session_state:
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        st.session_state.product_list = df
    except:
        st.session_state.product_list = pd.DataFrame()

if 'cart' not in st.session_state:
    st.session_state.cart = {}

# ฟังก์ชันเพิ่มสินค้า (ทำงานใน Memory ทันที)
def add_item(name, price):
    if name in st.session_state.cart:
        st.session_state.cart[name]['qty'] += 1
    else:
        st.session_state.cart[name] = {'price': price, 'qty': 1}

# 4. หน้าจอหลัก
st.title("🏪 TAS PROFESSIONAL POS")

col_left, col_right = st.columns([3.8, 1.2])

with col_left:
    df = st.session_state.product_list
    if not df.empty:
        grid = st.columns(4)
        for i, row in df.iterrows():
            with grid[i % 4]:
                st.markdown(f"""
                    <div class="product-card">
                        <div class="img-box"><img src="{row['Image_URL']}"></div>
                        <div class="p-name">{row['Name']}</div>
                        <div class="p-price">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                
                # ใช้ปุ่ม Streamlit แบบปกติแต่สั่ง rerun เมื่อกด
                if st.button(f"เลือก {row['Name']}", key=f"btn_{i}"):
                    add_item(row['Name'], row['Price'])
                    st.rerun()
    else:
        if st.button("🔄 โหลดข้อมูลสินค้าใหม่"):
            del st.session_state.product_list
            st.rerun()

with col_right:
    st.subheader("🛒 ตะกร้า")
    
    if st.session_state.cart:
        total = 0
        summary_text = []
        for name, info in list(st.session_state.cart.items()):
            item_total = info['price'] * info['qty']
            total += item_total
            summary_text.append(f"{name} x{info['qty']}")
            
            c1, c2 = st.columns([3, 1])
            with c1: st.write(f"**{name}** x{info['qty']}")
            with c2:
                if st.button("❌", key=f"rem_{name}"):
                    st.session_state.cart[name]['qty'] -= 1
                    if st.session_state.cart[name]['qty'] <= 0:
                        del st.session_state.cart[name]
                    st.rerun()
        
        st.divider()
        st.markdown(f"### รวม: :orange[{total:,.2f}] ฿")
        pay_type = st.radio("ชำระโดย:", ["เงินสด", "โอนเงิน"], horizontal=True)
        
        if st.button("✅ ยืนยันชำระเงิน", type="primary", use_container_width=True):
            # ยิงข้อมูลแบบ Get พ่วงท้าย (เร็วที่สุด)
            bill_id = "B" + pd.Timestamp.now().strftime("%H%M%S")
            data_url = f"{API_URL}?bill_id={bill_id}&items={', '.join(summary_text)}&total={total}&payment_type={pay_type}"
            try: requests.get(data_url, timeout=0.1)
            except: pass
            
            st.session_state.last_bill = {"total": total, "type": pay_type}
            st.session_state.cart = {}
            st.rerun()
            
        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = {}
            st.rerun()

    elif 'last_bill' in st.session_state and st.session_state.last_bill:
        last = st.session_state.last_bill
        st.success(f"บันทึกยอด {last['total']:,} ฿ สำเร็จ!")
        if "โอน" in last['type']:
            st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
        if st.button("บิลใหม่"):
            st.session_state.last_bill = None
            st.rerun()
