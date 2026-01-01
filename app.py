import streamlit as st
import pandas as pd
import time

# ตั้งค่าหน้าจอ
st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# 1. รวมลิงก์จาก Google Sheets ของคุณ (เปลี่ยนเป็นแบบ CSV ทั้งหมด)
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"

# 2. ฟังก์ชันดึงข้อมูลสต็อก
@st.cache_data(ttl=5)
def load_stock():
    try:
        # ใส่ตัวแปร time เพื่อป้องกันการจำค่าเก่า (Cache)
        df = pd.read_csv(f"{STOCK_URL}&t={int(time.time())}")
        df.columns = df.columns.str.strip() # ตัดช่องว่างหัวตาราง
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"เชื่อมต่อสต็อกไม่ได้: {e}")
        return pd.DataFrame()

# 3. เตรียมระบบตะกร้า
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_total' not in st.session_state: st.session_state.last_total = 0

df_stock = load_stock()

# 4. เมนูด้านข้าง
st.sidebar.title("🏪 TAS POS")
menu = st.sidebar.radio("เมนู", ["🛒 หน้าขายสินค้า", "📊 รายงานสต็อก"])

if st.sidebar.button("🔄 รีโหลดข้อมูลใหม่"):
    st.cache_data.clear()
    st.rerun()

# --- หน้าขายสินค้า ---
if menu == "🛒 หน้าขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    
    if not df_stock.empty:
        col_list, col_cart = st.columns([3, 2])
        
        with col_list:
            st.subheader("📦 รายการสินค้า")
            grid = st.columns(3)
            for i, row in df_stock.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1a1c24; border:1px solid #444; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                            <img src="{row['Image_URL']}" style="height:100px; width:100px; object-fit:contain; background:white; border-radius:8px;">
                            <div style="font-weight:bold; color:white; margin-top:10px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-size:1.2em; font-weight:bold;">{row['Price']:,} ฿</div>
                            <div style="color:{'#2ecc71' if row['Stock'] > 0 else '#e74c3c'};">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"pos_{i}", use_container_width=True):
                            name = row['Name']
                            if name in st.session_state.cart:
                                st.session_state.cart[name]['qty'] += 1
                            else:
                                st.session_state.cart[name] = {'price': row['Price'], 'qty': 1}
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"pos_{i}", disabled=True, use_container_width=True)

        with col_cart:
            st.subheader("🛒 ตะกร้าสินค้า")
            if st.session_state.cart:
                total = 0
                for name, item in list(st.session_state.cart.items()):
                    sub = item['price'] * item['qty']
                    total += sub
                    c1, c2 = st.columns([4, 1])
                    c1.write(f"**{name}** x {item['qty']} ({sub:,} ฿)")
                    if c2.button("❌", key=f"del_{name}"):
                        del st.session_state.cart[name]
                        st.rerun()
                st.divider()
                st.markdown(f"## รวม: :orange[{total:,}] ฿")
                if st.button("✅ ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    st.session_state.last_total = total
                    st.session_state.cart = {}
                    st.rerun()
            elif st.session_state.last_total > 0:
                st.success(f"ขายสำเร็จ! ยอดเงิน: {st.session_state.last_total:,} ฿")
                if st.button("เปิดบิลใหม่"):
                    st.session_state.last_total = 0
                    st.rerun()
            else:
                st.info("กรุณาเลือกสินค้า")
    else:
        st.warning("กำลังรอข้อมูลจาก Google Sheets...")

# --- หน้าสต็อก ---
else:
    st.title("📊 รายงานสต็อกสินค้า")
    if not df_stock.empty:
        st.dataframe(df_stock[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
        st.info(f"อัปเดตล่าสุดเมื่อ: {time.strftime('%H:%M:%S')}")
