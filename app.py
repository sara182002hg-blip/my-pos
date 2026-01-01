import streamlit as st
import pandas as pd
import random

# 1. ลิงก์สาธารณะที่คุณส่งมา ( gid=228640428 คือชีต Stock)
# ใส่ random เลขท้ายลิงก์เพื่อป้องกันการจำค่าเก่า (Cache)
base_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
SHEET_URL = f"{base_url}&cachebuster={random.randint(1, 100000)}"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# 2. โหลดข้อมูลแบบไม่ใช้ระบบจำ (No Cache)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        # ตรวจสอบคอลัมน์สำคัญ
        for c in ['Name', 'Price', 'Stock', 'Image_URL']:
            if c not in df.columns:
                df[c] = 0 if c in ['Price', 'Stock'] else "https://via.placeholder.com/150"
        
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        return pd.DataFrame()

# 3. เริ่มระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'bill' not in st.session_state: st.session_state.bill = None

df = load_data()

# 4. หน้าจอหลัก
st.title("🏪 TAS POS SYSTEM")

if df.empty:
    st.error("❌ ยังดึงข้อมูลไม่ได้ กรุณากดปุ่ม 'รีโหลดข้อมูล' ด้านล่าง")
    if st.button("🔄 รีโหลดข้อมูล"):
        st.rerun()
else:
    col1, col2 = st.columns([3, 2])
    
    with col1:
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                st.markdown(f"""
                    <div style="background:#1a1c24; border:1px solid #444; padding:15px; border-radius:10px; text-align:center; margin-bottom:10px;">
                        <img src="{row['Image_URL']}" style="height:100px; width:100px; object-fit:contain; background:white; border-radius:8px;">
                        <div style="font-weight:bold; color:white; margin:10px 0;">{row['Name']}</div>
                        <div style="color:#f1c40f; font-size:1.3em; font-weight:bold;">{row['Price']:,} ฿</div>
                        <div style="color:#2ecc71; font-size:0.9em;">คงเหลือ: {row['Stock']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"เลือก {row['Name']}", key=f"btn_{i}", use_container_width=True):
                    name = row['Name']
                    if name in st.session_state.cart:
                        st.session_state.cart[name]['qty'] += 1
                    else:
                        st.session_state.cart[name] = {'price': row['Price'], 'qty': 1}
                    st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            for n, item in list(st.session_state.cart.items()):
                total += item['price'] * item['qty']
                st.write(f"✅ {n} x {item['qty']} = {item['price']*item['qty']:,} ฿")
            st.divider()
            st.markdown(f"## รวม: :orange[{total:,}] ฿")
            if st.button("✅ ยืนยันชำระเงิน", type="primary", use_container_width=True):
                st.session_state.bill = total
                st.session_state.cart = {}
                st.rerun()
            if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()
        elif st.session_state.bill:
            st.success(f"ชำระเงินเรียบร้อย: {st.session_state.bill:,} ฿")
            if st.button("เปิดบิลใหม่"):
                st.session_state.bill = None
                st.rerun()
        else:
            st.info("เลือกสินค้าเพื่อเริ่มการขาย")
