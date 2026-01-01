import streamlit as st
import pandas as pd
import time

# 1. ตั้งค่าหน้าจอ
st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

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

# 3. ตัวแปรระบบ (Session State)
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False
if 'payment_msg' not in st.session_state: st.session_state.payment_msg = None
if 'sales_history' not in st.session_state: st.session_state.sales_history = [] # เก็บรายได้ต่อวัน

df = load_data()

# 4. เมนูแถบข้าง
st.sidebar.title("⚙️ TAS POS MENU")
menu = st.sidebar.radio("เลือกหน้าจอ", ["🛒 หน้าขายสินค้า", "📊 รายงานหลังบ้าน/รายได้"])

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
                            if n in st.session_state.cart:
                                st.session_state.cart[n]['qty'] += 1
                            else:
                                st.session_state.cart[n] = {'price': row['Price'], 'qty': 1}
                            st.rerun()
                    else: st.button("หมด", key=f"off_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                c1, c2, c3 = st.columns([2, 2, 1])
                # แสดง ชื่อ - จำนวน - ราคารวมย่อย
                c1.write(f"**{name}**\n({item['qty']} ชิ้น)")
                c2.write(f"{sub:,} ฿")
                if c3.button("❌", key=f"d_{name}"):
                    del st.session_state.cart[name]
                    st.rerun()
            
            st.divider()
            st.markdown(f"## ยอดรวม: :orange[{total:,}] ฿")
            
            pay_c1, pay_c2 = st.columns(2)
            if pay_c1.button("💵 เงินสด", use_container_width=True, type="primary"):
                st.session_state.sales_history.append({'เวลา': time.strftime("%H:%M"), 'ยอด': total, 'วิธี': 'เงินสด'})
                st.session_state.payment_msg = f"เงินสด {total:,} ฿"
                st.session_state.cart = {}
                st.rerun()
            
            if pay_c2.button("📱 QR Code", use_container_width=True, type="primary"):
                st.session_state.show_qr = True

            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

        if st.session_state.show_qr:
            st.markdown("---")
            st.subheader("📸 สแกน PromptPay")
            # สร้าง QR Code อัตโนมัติจากเบอร์โทรและยอดเงิน
            total_price = sum(item['price'] * item['qty'] for item in st.session_state.cart.values())
            qr_api = f"https://promptpay.io/0945016189/{total_price}.png"
            st.image(qr_api, caption=f"เบอร์: 0945016189 | ยอด: {total_price} ฿", width=250)
            if st.button("ชำระเงินสำเร็จแล้ว"):
                st.session_state.sales_history.append({'เวลา': time.strftime("%H:%M"), 'ยอด': total_price, 'วิธี': 'QR Code'})
                st.session_state.payment_msg = f"QR Code {total_price:,} ฿"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.rerun()

        elif st.session_state.payment_msg:
            st.success(f"🎉 ชำระเรียบร้อย: {st.session_state.payment_msg}")
            if st.button("เริ่มบิลใหม่"):
                st.session_state.payment_msg = None
                st.rerun()
        else: st.info("ยังไม่มีสินค้าในตะกร้า")

# --- 📊 หน้าหลังบ้าน ---
else:
    st.title("📊 รายงานหลังบ้านและรายได้")
    
    # คำนวณรายได้รวม
    if st.session_state.sales_history:
        history_df = pd.DataFrame(st.session_state.sales_history)
        total_income = history_df['ยอด'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("💰 รายได้รวมวันนี้", f"{total_income:,} ฿")
        c2.metric("🧾 จำนวนบิลวันนี้", f"{len(history_df)} บิล")
        
        st.write("### ประวัติการขาย")
        st.table(history_df)
    else:
        st.info("ยังไม่มีข้อมูลการขายในวันนี้")
    
    st.divider()
    st.write("### 📦 สต็อกสินค้าปัจจุบัน")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
