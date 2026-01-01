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

# ฟังก์ชันดึงสต็อก (แก้ปัญหาภาษาต่างดาว)
@st.cache_data(ttl=5)
def load_data():
    try:
        res = requests.get(f"{STOCK_URL}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8' 
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# ฟังก์ชันสร้าง PDF
def generate_receipt_pdf(cart, total, method):
    pdf = FPDF(format=(80, 150))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, txt="TAS POS RECEIPT", ln=True, align='C')
    pdf.set_font("Arial", size=8)
    pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(60, 5, txt="-" * 35, ln=True)
    for name, item in cart.items():
        pdf.cell(40, 7, txt=f"Item x{item['qty']}")
        pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
    pdf.cell(60, 5, txt="-" * 35, ln=True)
    pdf.cell(30, 10, txt="TOTAL:")
    pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
    return pdf.output()

# --- State Management ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'pay_method' not in st.session_state: st.session_state.pay_method = None
if 'pdf_ready' not in st.session_state: st.session_state.pdf_ready = None

df = load_data()

# --- ส่วนแสดงผล ---
st.title("🏪 TAS POS SYSTEM")
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📦 สินค้า")
    if not df.empty:
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:15px; text-align:center;">
                    <img src="{row['Image_URL']}" style="height:70px; object-fit:contain;"><br>
                    <b>{row['Name']}</b><br><span style="color:#f1c40f;">{row['Price']:,} ฿</span><br>
                    <small>สต็อก: {int(row['Stock'])}</small></div>""", unsafe_allow_html=True)
                if row['Stock'] > 0:
                    if st.button(f"เลือก {row['Name']}", key=f"btn_{i}", use_container_width=True):
                        n = str(row['Name']).strip()
                        st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                        st.session_state.cart[n]['qty'] += 1
                        st.rerun()

with col2:
    st.subheader("🛒 ตะกร้า")
    if st.session_state.cart:
        total_sum = sum(v['price'] * v['qty'] for v in st.session_state.cart.values())
        for name, item in list(st.session_state.cart.items()):
            c1, c2 = st.columns([2, 1.2])
            c1.write(f"**{name}**\n{item['price']*item['qty']:,} ฿")
            m, p = c2.columns(2)
            if m.button("➖", key=f"m_{name}"):
                if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                else: del st.session_state.cart[name]
                st.rerun()
            if p.button("➕", key=f"p_{name}"):
                st.session_state.cart[name]['qty'] += 1; st.rerun()
        
        st.divider()
        if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
            st.session_state.cart = {}; st.session_state.pay_method = None; st.rerun()

        st.header(f"ยอดรวม: :orange[{total_sum:,}] ฿")
        
        # เลือกช่องทางชำระเงิน
        c_pay1, c_pay2 = st.columns(2)
        if c_pay1.button("💵 เงินสด", use_container_width=True):
            st.session_state.pay_method = "Cash"
        if c_pay2.button("📱 QR Code", use_container_width=True):
            st.session_state.pay_method = "QR"

        # แสดง QR Code ทันทีเมื่อเลือก
        if st.session_state.pay_method == "QR":
            st.write("---")
            st.image(f"https://promptpay.io/0945016189/{total_sum}.png", caption="สแกนเพื่อจ่ายเงิน", width=250)
            
        if st.session_state.pay_method:
            if st.button("✅ ยืนยันการขาย (ตัดสต็อก)", use_container_width=True, type="primary"):
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "cart": st.session_state.cart, "method": st.session_state.pay_method, "total": total_sum, "summary": summary}
                try:
                    # สร้าง PDF เก็บไว้
                    st.session_state.pdf_ready = generate_receipt_pdf(st.session_state.cart, total_sum, st.session_state.pay_method)
                    # ส่งข้อมูล
                    res = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
                    if res.status_code == 200:
                        st.success("บันทึกสำเร็จ!")
                    else:
                        st.error("บันทึกไม่สำเร็จ ตรวจสอบ Google Script")
                except:
                    st.error("บันทึกไม่สำเร็จ ตรวจสอบอินเทอร์เน็ต")

        if st.session_state.pdf_ready:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จ (PDF)", data=bytes(st.session_state.pdf_ready), file_name="receipt.pdf", use_container_width=True)
            if st.button("🔄 เริ่มการขายใหม่"):
                st.session_state.cart = {}; st.session_state.pdf_ready = None; st.session_state.pay_method = None; st.rerun()
    else:
        st.info("ตะกร้าว่าง")
