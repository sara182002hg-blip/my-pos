import streamlit as st
import pandas as pd
import time

# 1. ตั้งค่าการเชื่อมต่อ (ใช้ลิงก์ Export โดยตรง)
FILE_ID = "1XqL_8rB3vUa6I6N6_uLz7G_7fPjG0r_D-uB4fP5Y6X0"
GID = "228640428"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv&gid={GID}"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (เขียนแบบชิดขอบซ้ายเพื่อป้องกัน IndentationError)
@st.cache_data(ttl=5)
def load_stock_data():
    try:
        # บังคับดึงข้อมูลใหม่เสมอ
        url = f"{SHEET_URL}&t={int(time.time())}"
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        # เติมคอลัมน์ที่ขาดให้ครบ
        for c in ['Name', 'Price', 'Stock', 'Image_URL']:
            if c not in df.columns:
                df[c] = 0 if c in ['Price', 'Stock'] else ""
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# 3. เริ่มต้นระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'bill' not in st.session_state: st.session_state.bill = None

df = load_stock_data()

# 4. ส่วนหน้าจอ POS
st.title("🏪 TAS POS SYSTEM")
col1, col2 = st.columns([3, 2])

with col1:
    if not df.empty:
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                st.image(row['Image_URL'] if row['Image_URL'] else "https://via.placeholder.com/150", width=150)
                st.write(f"**{row['Name']}**")
                st.write(f"ราคา: {row['Price']:,} ฿")
                st.write(f"คงเหลือ: {row['Stock']} ชิ้น")
                if row['Stock'] > 0:
                    if st.button(f"เลือก {row['Name']}", key=f"btn_{i}"):
                        name = row['Name']
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': row['Price'], 'qty': 1}
                        st.rerun()
                else:
                    st.button("สินค้าหมด", key=f"btn_{i}", disabled=True)
    else:
        st.error("ไม่สามารถเชื่อมต่อข้อมูลจาก Google Sheets ได้")

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        total = 0
        for name, item in list(st.session_state.cart.items()):
            sub = item['price'] * item['qty']
            total += sub
            c1, c2 = st.columns([3, 1])
            c1.write(f"{name} x{item['qty']}")
            if c2.button("❌", key=f"del_{name}"):
                del st.session_state.cart[name]
                st.rerun()
        st.divider()
        st.subheader(f"รวมทั้งสิ้น: {total:,.2f} ฿")
        if st.button("✅ ยืนยันการชำระเงิน", type="primary", use_container_width=True):
            st.session_state.bill = total
            st.session_state.cart = {}
            st.rerun()
    elif st.session_state.bill:
        st.success(f"ชำระเงินเรียบร้อย: {st.session_state.bill:,.2f} ฿")
        if st.button("เปิดบิลใหม่"):
            st.session_state.bill = None
            st.rerun()
    else:
        st.info("ยังไม่มีสินค้าในตะกร้า")

if st.sidebar.button("🔄 ดึงสต็อกล่าสุด"):
    st.cache_data.clear()
    st.rerun()
