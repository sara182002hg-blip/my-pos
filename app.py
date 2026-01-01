import streamlit as st
import pandas as pd
import time

# 1. ตั้งค่าหน้าจอ
st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ลิงก์ดึงข้อมูลจาก Google Sheets ของคุณ (แบบ CSV)
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# 2. ฟังก์ชันดึงข้อมูล (ลด Cache ลงเหลือ 1 วินาทีกันค้าง)
@st.cache_data(ttl=1)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = df.columns.str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# 3. เตรียมตัวแปร (Session State)
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'bill_done' not in st.session_state: st.session_state.bill_done = None

df = load_data()

# 4. เมนูแถบข้าง (หน้าหลังบ้าน)
st.sidebar.title("⚙️ TAS POS MENU")
menu = st.sidebar.radio("เลือกหน้าจอ", ["🛒 หน้าขายสินค้า", "📊 หลังบ้าน/สต็อก"])

if st.sidebar.button("🔄 อัปเดตสต็อก"):
    st.cache_data.clear()
    st.rerun()

# --- 🛒 ส่วนที่ 1: หน้าขายสินค้า ---
if menu == "🛒 หน้าขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 เลือกสินค้า")
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1e1e26; border:1px solid #333; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                            <img src="{row['Image_URL']}" style="height:80px; object-fit:contain; background:white; border-radius:5px; padding:5px;">
                            <div style="font-weight:bold; color:white; margin-top:5px; font-size:14px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-size:1.1em; font-weight:bold;">{row['Price']:,} ฿</div>
                            <div style="color:#2ecc71; font-size:0.8em;">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            if name in st.session_state.cart:
                                st.session_state.cart[name]['qty'] += 1
                            else:
                                st.session_state.cart[name] = {'price': row['Price'], 'qty': 1}
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"off_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            # แสดงรายการในตะกร้า
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                with st.container():
                    c1, c2, c3 = st.columns([2, 2, 1])
                    c1.write(f"**{name}**\n\n{sub:,} ฿")
                    # ปุ่มบวก/ลบ
                    if c2.button("➕", key=f"p_{name}"):
                        st.session_state.cart[name]['qty'] += 1
                        st.rerun()
                    if c2.button("➖", key=f"m_{name}"):
                        if st.session_state.cart[name]['qty'] > 1:
                            st.session_state.cart[name]['qty'] -= 1
                        else:
                            del st.session_state.cart[name]
                        st.rerun()
                    # ปุ่มลบ
                    if c3.button("❌", key=f"d_{name}"):
                        del st.session_state.cart[name]
                        st.rerun()
            
            st.divider()
            st.markdown(f"## รวมทั้งสิ้น: :orange[{total:,}] ฿")
            
            # --- ปุ่มที่หายไป: จ่ายเงิน และ เคลียร์ตะกร้า ---
            if st.button("✅ ยืนยันชำระเงิน", type="primary", use_container_width=True):
                st.session_state.bill_done = total
                st.session_state.cart = {}
                st.rerun()
            
            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

        elif st.session_state.bill_done:
            st.success(f"🎉 ชำระเงินสำเร็จ! ยอด {st.session_state.bill_done:,} ฿")
            if st.button("เปิดบิลใหม่"):
                st.session_state.bill_done = None
                st.rerun()
        else:
            st.info("กรุณาเลือกสินค้าจากด้านซ้าย")

# --- 📊 ส่วนที่ 2: หน้าหลังบ้าน ---
else:
    st.title("📊 ระบบหลังบ้าน (Stock Report)")
    st.write("สถานะสินค้าล่าสุดจาก Google Sheets")
    if not df.empty:
        st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
    else:
        st.error("ไม่สามารถดึงข้อมูลสต็อกได้")
