import streamlit as st
import pandas as pd
import time

# 1. ตั้งค่าพื้นฐาน
st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# 2. ฟังก์ชันโหลดข้อมูล (ใส่ระบบกันค้าง)
@st.cache_data(ttl=2)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = df.columns.str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# 3. เตรียมระบบ (Session State)
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'bill' not in st.session_state: st.session_state.bill = None

df = load_data()

# 4. เมนูข้าง (สลับหน้าจอ)
st.sidebar.title("🚀 TAS MENU")
page = st.sidebar.radio("เลือกหน้าจอ", ["🛒 ขายสินค้า", "📊 หลังบ้าน/สต็อก"])

# --- 🛒 หน้าขายสินค้า ---
if page == "🛒 ขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1a1c24; border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">
                            <img src="{row['Image_URL']}" style="height:80px; width:80px; object-fit:contain; background:white; border-radius:5px;">
                            <div style="font-weight:bold; color:white; font-size:15px; margin:5px 0;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-size:1.2em;">{row['Price']:,} ฿</div>
                            <div style="color:#2ecc71; font-size:0.8em;">สต็อก: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = row['Name']
                            if n in st.session_state.cart:
                                st.session_state.cart[n]['qty'] += 1
                            else:
                                st.session_state.cart[n] = {'price': row['Price'], 'qty': 1}
                            st.rerun()
                    else: st.button("หมด", key=f"no_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            for n, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                with st.container():
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**{n}**\n\n{sub:,} ฿")
                    # ปุ่ม บวกลบ
                    if c2.button("➕", key=f"p_{n}"):
                        st.session_state.cart[n]['qty'] += 1
                        st.rerun()
                    if c2.button("➖", key=f"m_{n}"):
                        if st.session_state.cart[n]['qty'] > 1: st.session_state.cart[n]['qty'] -= 1
                        else: del st.session_state.cart[n]
                        st.rerun()
                    if c3.button("❌", key=f"d_{n}"):
                        del st.session_state.cart[n]
                        st.rerun()
            st.divider()
            st.subheader(f"รวม: {total:,} ฿")
            if st.button("✅ จ่ายเงิน", type="primary", use_container_width=True):
                st.session_state.bill = total
                st.session_state.cart = {}
                st.rerun()
            if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
        elif st.session_state.bill:
            st.success(f"จ่ายเงินสำเร็จ: {st.session_state.bill:,} ฿")
            if st.button("บิลใหม่"):
                st.session_state.bill = None
                st.rerun()
        else: st.info("ตะกร้าว่างเปล่า")

# --- 📊 หน้าหลังบ้าน ---
else:
    st.title("📊 จัดการหลังบ้าน")
    st.write("### ตรวจสอบสต็อกล่าสุด")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
    if st.button("🔄 อัปเดตข้อมูลจากชีต"):
        st.cache_data.clear()
        st.rerun()
