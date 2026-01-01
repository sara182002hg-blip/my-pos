import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. ตั้งค่าการเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS Ultimate", layout="wide")

# ฟังก์ชันสร้าง PDF (รองรับภาษาไทยเบื้องต้น)
def create_pdf(cart, total, method):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="TAS POS RECEIPT", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(200, 10, txt=f"Payment: {method}", ln=True)
    pdf.cell(200, 10, txt="---------------------------------------------------", ln=True)
    for name, item in cart.items():
        pdf.cell(200, 10, txt=f"{name} x {item['qty']} = {item['price']*item['qty']:,} Baht", ln=True)
    pdf.cell(200, 10, txt="---------------------------------------------------", ln=True)
    pdf.cell(200, 10, txt=f"TOTAL: {total:,} Baht", ln=True)
    return pdf.output(dest='S').encode('latin-1', 'ignore')

# ดึงข้อมูล (UTF-8 + No Cache)
def load_data():
    try:
        res = requests.get(f"{STOCK_URL}&t={int(time.time())}")
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# เตรียม State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False
if 'pdf_ready' not in st.session_state: st.session_state.pdf_ready = None

df = load_data()

# ฟังก์ชันจัดการการขาย
def process_checkout(method, total):
    summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
    payload = {"action": "checkout", "cart": st.session_state.cart, "method": method, "total": total, "summary": summary}
    
    with st.spinner('กำลังบันทึก...'):
        try:
            # สร้าง PDF ไว้ก่อนเผื่อเน็ตหน่วง
            st.session_state.pdf_ready = create_pdf(st.session_state.cart, total, method)
            # ส่งข้อมูลไป Google Sheets
            res = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=20)
            st.success("✅ บันทึกสำเร็จ!")
        except:
            st.warning("⚠️ ข้อมูลถูกส่งแล้ว แต่การตอบกลับช้า โปรดตรวจสอบสต็อกในชีต")
            if not st.session_state.pdf_ready:
                st.session_state.pdf_ready = create_pdf(st.session_state.cart, total, method)

# --- 2. ส่วนหน้าจอหลัก ---
menu = st.sidebar.selectbox("เมนู", ["🛒 ขายสินค้า", "📊 สรุปยอดและกำไร", "📦 จัดการสต็อก"])

if menu == "🛒 ขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 รายการสินค้า")
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f'<div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">'
                                f'<img src="{row["Image_URL"]}" style="height:70px;"><br>'
                                f'<b>{row["Name"]}</b><br><span style="color:#f1c40f;">{row["Price"]:,} ฿</span>'
                                f'<br><small>คงเหลือ: {row["Stock"]}</small></div>', unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = row['Name'].strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0, 'cost': row.get('Cost', 0)})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้า")
        if st.session_state.cart:
            total_amt = 0
            for name, item in list(st.session_state.cart.items()):
                total_amt += (item['price'] * item['qty'])
                c1, c2 = st.columns([2, 1])
                c1.write(f"**{name}**")
                # ปุ่มบวกลบ
                b1, b2 = c2.columns(2)
                if b1.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if b2.button("➕", key=f"p_{name}"):
                    st.session_state.cart
