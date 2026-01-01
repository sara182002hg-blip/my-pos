import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. ตั้งค่าการเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzPnRauhL9eU7nw8ZbowGKK8wW2D1vMpJEqr1oC8uBubN0MS2e3IfO8L4TvCR4-65Ns/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# --- 2. ฟังก์ชันโหลดข้อมูล (ปรับให้โหลดเฉพาะที่จำเป็น) ---
@st.cache_data(ttl=5) # เก็บแคชไว้ 5 วินาทีเพื่อลดการดึงข้อมูลบ่อยเกินไป
def load_data():
    try:
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

# --- 3. ฟังก์ชันส่งข้อมูล ---
def process_payment(method, items_summary, total):
    payload = {
        "bill_id": f"BILL-{int(time.time())}",
        "items": ", ".join(items_summary),
        "total": total,
        "cart": st.session_state.cart,
        "method": method
    }
    with st.spinner('กำลังบันทึก...'):
        try:
            response = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=20)
            if response.status_code == 200:
                st.session_state.order_success = f"{method} {total:,} ฿"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.cache_data.clear() # ล้างแคชเพื่อให้สต็อกอัปเดต
                st.rerun()
        except:
            st.error("การบันทึกล่าช้า แต่ข้อมูลอาจเข้าแล้ว กรุณาเช็คใน Sheet")

# --- 4. หน้าจอหลัก ---
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
                            <img src="{row['Image_URL']}" style="height:80px; object-fit:contain; background:white; border-radius:5px;">
                            <div style="font-weight:bold; color:white; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-weight:bold;">{row['Price']:,} ฿</div>
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
        st.subheader("🛒 รายการในตะกร้า")
        if st.session_state.cart:
            total = 0
            items_summary = []
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                items_summary.append(f"{name}({item['qty']})")
                
                # แสดงแถวสินค้า: ชื่อ | [ - ] จำนวน [ + ]
                c1, c2 = st.columns([1, 1])
                c1.write(f"**{name}**\n{sub:,} ฿")
                
                # ปุ่มบวก/ลบ แบบไม่มีปุ่มกากบาท
                btn_col1, btn_col2 = c2.columns(2)
                if btn_col1.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1:
                        st.session_state.cart[name]['qty'] -= 1
                    else:
                        del st.session_state.cart[name]
                    st.rerun()
                if btn_col2.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.markdown(f"### ยอดรวม: :orange[{total:,}] ฿")
            
            pay1, pay2 = st.columns(2)
            if pay1.button("💵 เงินสด", use_container_width=True, type="primary"):
                process_payment("เงินสด", items_summary, total)
            if pay2.button("📱 QR Code", use_container_width=True, type="primary"):
                st.session_state.show_qr = True

            if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

            if st.session_state.show_qr:
                qr_api = f"https://promptpay.io/0945016189/{total}.png"
                st.image(qr_api, width=250)
                if st.button("✅ ยืนยันโอนเงินแล้ว", use_container_width=True):
                    process_payment("QR Code", items_summary, total)

        elif st.session_state.order_success:
            st.success(f"บันทึกสำเร็จ: {st.session_state.order_success}")
            if st.button("เริ่มบิลใหม่"):
                st.session_state.order_success = None
                st.rerun()
        else: st.info("ยังไม่มีสินค้า")

else:
    st.title("📊 สต็อกสินค้า")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
