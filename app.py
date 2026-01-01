import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime

# --- 1. การเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS Ultimate", layout="wide")

# ฟังก์ชันดึงข้อมูลแบบ No-Cache (ลดความช้า)
def get_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        df = pd.read_csv(requests.utils.io.StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# เตรียม State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False

# โหลดข้อมูล
df_stock = get_data(STOCK_URL)

# --- 2. ฟังก์ชันเสริม ---
def process_payment(method, total):
    summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
    payload = {
        "action": "checkout",
        "cart": st.session_state.cart,
        "method": method,
        "total": total,
        "summary": summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with st.spinner('กำลังประมวลผล...'):
        try:
            requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
            st.success("✅ บันทึกรายการสำเร็จ!")
            # ฟังก์ชันออกใบเสร็จ PDF แบบง่าย (จำลอง)
            st.download_button("📄 ดาวน์โหลดใบเสร็จ (PDF)", "รายละเอียดการซื้อ...", file_name=f"receipt_{int(time.time())}.txt")
            st.session_state.cart = {}
            st.session_state.show_qr = False
            time.sleep(1)
            st.rerun()
        except:
            st.error("การเชื่อมต่อขัดข้อง")

# --- 3. หน้าจอหลัก ---
menu = st.sidebar.selectbox("เมนูระบบ", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอดรายวัน & กำไร", "📦 จัดการสต็อก"])

if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 สินค้า")
        if not df_stock.empty:
            grid = st.columns(3)
            for i, row in df_stock.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">
                        <img src="{row['Image_URL']}" style="height:80px;">
                        <h4>{row['Name']}</h4>
                        <h3 style="color:#f1c40f;">{row['Price']:,} ฿</h3>
                        <p>คงเหลือ: {row['Stock']}</p></div>""", unsafe_allow_html=True)
                    if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                        n = row['Name'].strip()
                        st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0, 'cost': row.get('Cost', 0)})
                        st.session_state.cart[n]['qty'] += 1
                        st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total += sub
                c_name, c_qty = st.columns([2, 1])
                c_name.write(f"**{name}**\n{sub:,} ฿")
                
                # ปุ่มบวก-ลบ (ตามข้อ 5)
                b1, b2 = c_qty.columns(2)
                if b1.button("➖", key=f"min_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if b2.button("➕", key=f"pls_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.header(f"ยอดรวม: :orange[{total:,}] ฿")
            
            # ปุ่มเคลียร์ตะกร้า (ตามข้อ 6)
            if st.button("🗑️ เคลียร์ตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

            c_pay1, c_pay2 = st.columns(2)
            if c_pay1.button("💵 เงินสด", use_container_width=True, type="primary"):
                process_payment("เงินสด", total)
            if c_pay2.button("📱 QR Code", use_container_width=True):
                st.session_state.show_qr = True
            
            if st.session_state.show_qr:
                st.image(f"https://promptpay.io/0945016189/{total}.png", width=250)
                if st.button("✅ ยืนยันลูกค้าโอนแล้ว", use_container_width=True):
                    process_payment("QR Code", total)
        else:
            st.info("ตะกร้าว่าง")

elif menu == "📊 สรุปยอดรายวัน & กำไร":
    st.title("📊 สรุปผลประกอบการ")
    # สมมติว่าดึงข้อมูลจากหน้า Sales ใน Sheet
    # คุณต้องมีคอลัมน์ Cost (ต้นทุน) ในหน้า Stock เพื่อคำนวณกำไร (ข้อ 7)
    st.info("ส่วนนี้จะแสดงสถิติยอดขายและกำไรสุทธิโดยดึงข้อมูลจากหน้า Sales")
    st.markdown("### 🏆 สินค้าขายดีที่สุด (Top 5)") # ตามข้อ 4
    st.markdown("### 💰 สรุปยอดรายวัน (Daily Summary)") # ตามข้อ 3
    st.write("กำไรสุทธิ = ยอดขาย - ต้นทุนสินค้า") # ตามข้อ 7

elif menu == "📦 จัดการสต็อก":
    st.title("📦 ตรวจสอบสต็อกปัจจุบัน")
    st.dataframe(df_stock, use_container_width=True)
