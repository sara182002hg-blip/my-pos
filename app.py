import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. ตั้งค่าการเชื่อมต่อ (ใช้ URL ล่าสุดที่คุณส่งมา) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx33rffhKc8q7JThCECJ1cO6f9fywve490dCYJBZ7MGrOJUgO3nmuExvAXVcMxscoNd/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ฟังก์ชันดึงข้อมูลสต็อก
@st.cache_data(ttl=2) # ลดเวลาแคชเพื่อให้เห็นสต็อกที่ตัดแล้วเร็วขึ้น
def load_data():
    try:
        # ใส่ t= เพื่อให้ดึงข้อมูลใหม่จาก Google เสมอ
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

# ฟังก์ชันส่งข้อมูลชำระเงิน
def process_payment(method, items_summary, total):
    payload = {
        "bill_id": f"BILL-{int(time.time())}",
        "items": ", ".join(items_summary),
        "total": total,
        "cart": st.session_state.cart,
        "method": method
    }
    with st.spinner('กำลังบันทึกข้อมูล...'):
        try:
            # ส่งข้อมูลไปยัง Apps Script
            response = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
            if "Success" in response.text:
                st.session_state.order_success = f"{method} {total:,} ฿"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.cache_data.clear() # ล้างแคชเพื่อให้สต็อกหน้าจอเปลี่ยนทันที
                st.rerun()
            else:
                st.error(f"Error: {response.text}")
        except:
            # กรณี Timeout แต่ข้อมูลมักจะเข้า Sheets ไปแล้ว
            st.warning("การเชื่อมต่อช้า แต่ข้อมูลกำลังถูกบันทึก กรุณารอสักครู่แล้วตรวจสอบสต็อกครับ")

# --- ส่วนแสดงผลหน้าจอ ---
st.sidebar.title("⚙️ TAS POS")
page = st.sidebar.radio("เมนู", ["🛒 ขายสินค้า", "📊 หลังบ้าน"])

if page == "🛒 ขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1e1e26; border:1px solid #333; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                            <img src="{row['Image_URL']}" style="height:70px; object-fit:contain; background:white; border-radius:5px;">
                            <div style="font-weight:bold; color:white; margin-top:5px; font-size:14px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-weight:bold;">{row['Price']:,} ฿</div>
                            <div style="color:#2ecc71; font-size:12px;">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = row['Name'].strip() # ล้างช่องว่าง
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
                
                c1, c2 = st.columns([1, 1])
                c1.write(f"**{name}**\n{sub:,} ฿")
                
                # ปุ่มบวก/ลบ
                b_col1, b_col2 = c2.columns(2)
                if b_col1.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1:
                        st.session_state.cart[name]['qty'] -= 1
                    else:
                        del st.session_state.cart[name]
                    st.rerun()
                if b_col2.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.markdown(f"### ยอดรวม: :orange[{total:,}] ฿")
            
            p1, p2 = st.columns(2)
            if p1.button("💵 เงินสด", use_container_width=True, type="primary"):
                process_payment("เงินสด", items_summary, total)
            if p2.button("📱 QR Code", use_container_width=True, type="primary"):
                st.session_state.show_qr = True

            if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

            if st.session_state.show_qr:
                st.image(f"https://promptpay.io/0945016189/{total}.png", width=250)
                if st.button("✅ ยืนยันว่าลูกค้าโอนแล้ว", use_container_width=True):
                    process_payment("QR Code", items_summary, total)

        elif st.session_state.order_success:
            st.success(f"บันทึกสำเร็จ: {st.session_state.order_success}")
            if st.button("เริ่มบิลใหม่"):
                st.session_state.order_success = None
                st.rerun()
        else: st.info("เลือกสินค้าได้เลยครับ")
else:
    st.title("📊 รายงานสต็อก")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
