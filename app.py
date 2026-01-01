import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. ตั้งค่าการเชื่อมต่อ (เช็ค URL ให้ถูกต้อง) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzPnRauhL9eU7nw8ZbowGKK8wW2D1vMpJEqr1oC8uBubN0MS2e3IfO8L4TvCR4-65Ns/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# --- 2. ฟังก์ชันโหลดข้อมูล (ปรับให้เบาลง) ---
def load_data():
    try:
        # ใส่ t= เพื่อป้องกันเครื่องจำค่าเก่า
        df = pd.read_csv(f"{STOCK_URL}&t={int(time.time())}")
        df.columns = df.columns.str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# เตรียมตัวแปรระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False
if 'order_success' not in st.session_state: st.session_state.order_success = None

df = load_data()

# --- 3. ฟังก์ชันส่งข้อมูลไป Google Sheets (ตัวที่ปรับปรุงใหม่) ---
def process_payment(method, items_summary, total):
    payload = {
        "bill_id": f"BILL-{int(time.time())}",
        "items": ", ".join(items_summary),
        "total": total,
        "cart": st.session_state.cart,
        "method": method
    }
    
    with st.spinner('กำลังบันทึกและตัดสต็อก...'):
        try:
            # เพิ่ม timeout เป็น 30 วินาที ป้องกัน Error สีแดงจากการรอนาน
            response = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=30)
            if response.status_code == 200:
                st.session_state.order_success = f"{method} {total:,} ฿"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.rerun()
            else:
                st.error("เซิร์ฟเวอร์ Google ไม่ตอบกลับ กรุณาลองใหม่")
        except Exception as e:
            st.error(f"การเชื่อมต่อล่าช้า: {e}")

# --- 4. ส่วนหน้าจอ (UI) ---
st.sidebar.title("⚙️ TAS POS MENU")
page = st.sidebar.radio("เลือกหน้าจอ", ["🛒 หน้าขายสินค้า", "📊 หลังบ้าน/สรุปรายได้"])

if page == "🛒 หน้าขายสินค้า":
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
                            <div style="font-weight:bold; color:white; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-size:1.1em; font-weight:bold;">{row['Price']:,} ฿</div>
                            <div style="color:#2ecc71; font-size:0.8em;">สต็อก: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = row['Name']
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()
                    else: st.button("หมด", key=f"no_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            items_summary = []
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                items_summary.append(f"{name}({item['qty']})")
                c1, c2, c3 = st.columns([2, 1.5, 0.5])
                c1.write(f"**{name}**\n({item['qty']} ชิ้น)")
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
            
            c_pay1, c_pay2 = st.columns(2)
            if c_pay1.button("💵 เงินสด", use_container_width=True, type="primary"):
                process_payment("เงินสด", items_summary, total)
            if c_pay2.button("📱 QR Code", use_container_width=True, type="primary"):
                st.session_state.show_qr = True

            if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

            if st.session_state.show_qr:
                st.markdown("---")
                qr_api = f"https://promptpay.io/0945016189/{total}.png"
                st.image(qr_api, caption=f"สแกนจ่าย {total} ฿", width=250)
                if st.button("✅ ยืนยันว่าลูกค้าโอนเงินแล้ว"):
                    process_payment("QR Code", items_summary, total)

        elif st.session_state.order_success:
            st.success(f"🎉 สำเร็จ: {st.session_state.order_success}")
            if st.button("เริ่มบิลใหม่"):
                st.session_state.order_success = None
                st.rerun()
        else: st.info("เลือกสินค้าได้เลยครับ")

else:
    st.title("📊 รายงานสต็อกล่าสุด")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
