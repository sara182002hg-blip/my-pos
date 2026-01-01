import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. ตั้งค่าการเชื่อมต่อ (ใช้ URL ที่คุณเพิ่ง Deploy สำเร็จ) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ฟังก์ชันดึงสต็อก (ปรับให้โหลดไว)
@st.cache_data(ttl=2)
def load_data():
    try:
        df = pd.read_csv(f"{STOCK_URL}&t={int(time.time())}")
        df.columns = df.columns.str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# เตรียมตัวแปร State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False
if 'order_success' not in st.session_state: st.session_state.order_success = None

df = load_data()

# ฟังก์ชันบันทึกยอดและตัดสต็อก
def process_checkout(method, summary, total):
    payload = {
        "bill_id": f"BILL-{int(time.time())}",
        "items": summary,
        "total": total,
        "cart": st.session_state.cart,
        "method": method
    }
    with st.spinner('กำลังตัดสต็อกและบันทึกข้อมูล...'):
        try:
            # ยิงข้อมูลไปที่ Google Apps Script
            response = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
            if response.status_code == 200:
                st.session_state.order_success = f"✅ {method} {total:,} ฿ สำเร็จ!"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.cache_data.clear() # ล้างแคชเพื่อให้เห็นสต็อกใหม่ทันที
                st.rerun()
            else:
                st.error(f"การเชื่อมต่อมีปัญหา: {response.status_code}")
        except:
            # กรณีเน็ตช้าแต่ข้อมูลส่งไปแล้ว
            st.session_state.cart = {}
            st.rerun()

# --- ส่วนหน้าจอการขาย ---
st.sidebar.title("⚙️ POS MENU")
page = st.sidebar.radio("เลือกเมนู", ["🛒 ขายสินค้า", "📊 ตารางสต็อก"])

if page == "🛒 ขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1e1e26; border:1px solid #333; padding:15px; border-radius:15px; text-align:center; margin-bottom:15px;">
                            <img src="{row['Image_URL']}" style="height:80px; margin-bottom:10px;">
                            <div style="font-weight:bold; font-size:16px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-weight:bold; font-size:18px;">{row['Price']:,} ฿</div>
                            <div style="color:#2ecc71; font-size:13px;">สต็อก: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"➕ เพิ่ม {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = row['Name'].strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("❌ สินค้าหมด", key=f"out_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            summary_list = []
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total_sum += sub
                summary_list.append(f"{name}({item['qty']})")
                
                c_name, c_act = st.columns([1.5, 1])
                c_name.write(f"**{name}**\n{sub:,} ฿")
                
                # ปุ่มบวก/ลบ
                b_minus, b_plus = c_act.columns(2)
                if b_minus.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1:
                        st.session_state.cart[name]['qty'] -= 1
                    else:
                        del st.session_state.cart[name]
                    st.rerun()
                if b_plus.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.markdown(f"### ยอดรวมทั้งหมด: :orange[{total_sum:,}] ฿")
            
            pay_cash, pay_qr = st.columns(2)
            if pay_cash.button("💵 เงินสด", use_container_width=True, type="primary"):
                process_checkout("เงินสด", ", ".join(summary_list), total_sum)
            if pay_qr.button("📱 QR Code", use_container_width=True, type="primary"):
                st.session_state.show_qr = True

            if st.session_state.show_qr:
                st.markdown("---")
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=250)
                if st.button("✅ ยืนยันการโอนเงิน", use_container_width=True):
                    process_checkout("QR Code", ", ".join(summary_list), total_sum)
            
            if st.button("🗑️ ล้างตะกร้า"):
                st.session_state.cart = {}
                st.rerun()

        elif st.session_state.order_success:
            st.success(st.session_state.order_success)
            if st.button("🔥 เริ่มบิลใหม่"):
                st.session_state.order_success = None
                st.rerun()
        else:
            st.info("ตะกร้ายังว่างอยู่ครับ")

else:
    st.title("📊 รายงานสต็อกปัจจุบัน")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
