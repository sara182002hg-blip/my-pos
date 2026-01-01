import streamlit as st
import pandas as pd

# 1. ตั้งค่าหน้าจอ
st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ลิงก์ดึงข้อมูลจาก Google Sheets
URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# 2. ฟังก์ชันดึงข้อมูล
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

# 3. ตัวแปรระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False
if 'payment_msg' not in st.session_state: st.session_state.payment_msg = None

df = load_data()

# 4. เมนูแถบข้าง (หลังบ้าน)
st.sidebar.title("⚙️ TAS POS MENU")
menu = st.sidebar.radio("เลือกหน้าจอ", ["🛒 หน้าขายสินค้า", "📊 รายงานหลังบ้าน/สต็อก"])

# --- 🛒 หน้าขายสินค้า ---
if menu == "🛒 หน้าขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 รายการสินค้า")
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1e1e26; border:1px solid #333; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                            <img src="{row['Image_URL']}" style="height:80px; object-fit:contain; background:white; border-radius:5px; padding:5px;">
                            <div style="font-weight:bold; color:white; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-size:1.1em; font-weight:bold;">{row['Price']:,} ฿</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = row['Name']
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()
                    else: st.button("หมด", key=f"off_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                c1, c2, c3 = st.columns([2, 1.5, 0.5])
                c1.write(f"**{name}**\n{sub:,} ฿")
                if c2.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
                if c2.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if c3.button("❌", key=f"d_{name}"):
                    del st.session_state.cart[name]
                    st.rerun()
            
            st.divider()
            st.markdown(f"## ยอดรวม: :orange[{total:,}] ฿")
            
            # ปุ่มชำระเงิน
            pay_c1, pay_c2 = st.columns(2)
            if pay_c1.button("💵 เงินสด", use_container_width=True, type="primary"):
                st.session_state.payment_msg = f"เงินสด {total:,} ฿"
                st.session_state.cart = {}
                st.rerun()
            
            if pay_c2.button("📱 QR Code", use_container_width=True, type="primary"):
                st.session_state.show_qr = True # สั่งให้โชว์ QR

            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

        # --- ส่วนแสดง QR Code เมื่อกดปุ่ม ---
        if st.session_state.show_qr:
            st.markdown("---")
            st.subheader("📸 สแกนเพื่อชำระเงิน")
            # ใส่ลิงก์รูป QR Code ของคุณที่นี่
            qr_url = "https://via.placeholder.com/300?text=QR+PROMPTPAY" 
            st.image(qr_url, caption="สแกนจ่ายที่นี่", width=300)
            if st.button("ชำระเงินสำเร็จแล้ว"):
                st.session_state.payment_msg = "QR Code (สำเร็จ)"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.rerun()

        elif st.session_state.payment_msg:
            st.success(f"🎉 ชำระเรียบร้อย: {st.session_state.payment_msg}")
            if st.button("เริ่มบิลใหม่"):
                st.session_state.payment_msg = None
                st.rerun()
        else: st.info("กรุณาเลือกสินค้า")

# --- 📊 หน้าหลังบ้าน ---
else:
    st.title("📊 หลังบ้าน (สต็อกสินค้า)")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
