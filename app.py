import streamlit as st
import pandas as pd

# 1. เชื่อมต่อผ่าน Public CSV Link (ตัวที่ข้อมูลสต็อกคุณโชว์แน่นอน)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (ตัดความซับซ้อนออกทั้งหมดเพื่อให้ข้อมูลมาให้ได้ก่อน)
def load_data():
    try:
        # ดึงข้อมูลจากลิงก์ตรงๆ
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip() # ลบช่องว่างหัวตาราง
        
        # บังคับสร้างคอลัมน์ถ้าหาไม่เจอ
        cols = ['Name', 'Price', 'Stock', 'Image_URL']
        for c in cols:
            if c not in df.columns:
                df[c] = 0 if c in ['Price', 'Stock'] else ""
        
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"การเชื่อมต่อมีปัญหา: {e}")
        return pd.DataFrame()

# 3. เริ่มระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'bill' not in st.session_state: st.session_state.bill = None

df = load_data()

# 4. เมนูข้าง
menu = st.sidebar.radio("เมนู", ["🛒 หน้าขาย", "📊 สต็อก"])

# --- หน้าขาย ---
if menu == "🛒 หน้าขาย":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])
    
    with col1:
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1a1c24; border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">
                            <img src="{row['Image_URL']}" style="height:100px; width:100px; object-fit:contain; background:white; border-radius:5px;">
                            <div style="font-weight:bold; color:white; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-size:1.2em;">{row['Price']:,} ฿</div>
                            <div style="color:#2ecc71;">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"เลือก {row['Name']}", key=f"b{i}"):
                        name = row['Name']
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': row['Price'], 'qty': 1}
                        st.rerun()
        else:
            st.warning("ไม่มีข้อมูลสินค้า ลองรีเฟรชหน้าเว็บอีกครั้ง")

    with col2:
        st.subheader("🛒 ตะกร้า")
        if st.session_state.cart:
            total = 0
            for n, item in list(st.session_state.cart.items()):
                total += item['price'] * item['qty']
                st.write(f"{n} x{item['qty']}")
            st.divider()
            st.subheader(f"รวม: {total:,} ฿")
            if st.button("ยืนยัน", type="primary", use_container_width=True):
                st.session_state.bill = total
                st.session_state.cart = {}
                st.rerun()
        elif st.session_state.bill:
            st.success(f"จ่ายเงินแล้ว: {st.session_state.bill:,} ฿")
            if st.button("บิลใหม่"):
                st.session_state.bill = None
                st.rerun()

# --- หน้าสต็อก ---
else:
    st.title("📊 สต็อกสินค้า")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
