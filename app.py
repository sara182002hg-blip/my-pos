import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าจอและลิงก์ข้อมูล
st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# 2. ฟังก์ชันโหลดข้อมูล (ไม่ใช้ Cache เพื่อให้เลขสต็อกเปลี่ยนทันที)
def load_data():
    try:
        df = pd.read_csv(URL)
        df.columns = df.columns.str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# 3. เตรียมตัวแปรระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'bill' not in st.session_state: st.session_state.bill = None

df = load_data()

# 4. หน้าจอหลัก
st.title("🏪 TAS POS SYSTEM")

if df.empty:
    st.error("❌ ไม่สามารถดึงข้อมูลได้ กรุณาเช็ค Google Sheets")
else:
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📦 รายการสินค้า")
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                # แสดงกล่องสินค้าสวยงาม
                st.markdown(f"""
                    <div style="background:#1a1c24; border:1px solid #444; padding:15px; border-radius:10px; text-align:center; margin-bottom:10px;">
                        <img src="{row['Image_URL']}" style="height:100px; width:100px; object-fit:contain; background:white; border-radius:8px;">
                        <div style="font-weight:bold; color:white; margin:10px 0;">{row['Name']}</div>
                        <div style="color:#f1c40f; font-size:1.3em; font-weight:bold;">{row['Price']:,} ฿</div>
                        <div style="color:{'#2ecc71' if row['Stock'] > 0 else '#e74c3c'};">คงเหลือ: {row['Stock']}</div>
                    </div>
                """, unsafe_allow_html=True)
                
                if row['Stock'] > 0:
                    if st.button(f"เลือก {row['Name']}", key=f"btn_{i}", use_container_width=True):
                        name = row['Name']
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': row['Price'], 'qty': 1}
                        st.rerun()
                else:
                    st.button("สินค้าหมด", key=f"btn_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            for n, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                c1, c2 = st.columns([4, 1])
                c1.write(f"**{n}** x {item['qty']} ({sub:,} ฿)")
                if c2.button("❌", key=f"del_{n}"):
                    del st.session_state.cart[n]
                    st.rerun()
            st.divider()
            st.markdown(f"## รวม: :orange[{total:,}] ฿")
            if st.button("✅ ยืนยันชำระเงิน", type="primary", use_container_width=True):
                st.session_state.bill = total
                st.session_state.cart = {}
                st.rerun()
        elif st.session_state.bill:
            st.success(f"ชำระเงินเรียบร้อยยอด {st.session_state.bill:,} ฿")
            if st.button("เปิดบิลใหม่"):
                st.session_state.bill = None
                st.rerun()
        else:
            st.info("กรุณาเลือกสินค้าจากด้านซ้าย")

# เมนูเสริมด้านข้าง
st.sidebar.title("⚙️ ตั้งค่า")
if st.sidebar.button("🔄 รีโหลดสต็อก"):
    st.rerun()
