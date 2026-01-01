import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. การเชื่อมต่อ (ใช้ URL ที่คุณ Deploy ล่าสุด) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS Ultimate", layout="wide")

def load_data():
    try:
        # บังคับใช้ t=time เพื่อป้องกันข้อมูลเก่าค้าง (Cache)
        res = requests.get(f"{STOCK_URL}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8' # แก้ปัญหาภาษาไทยต่างดาว
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        # แปลงราคาและสต็อกให้เป็นตัวเลขเสมอ
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
        return pd.DataFrame()

def generate_receipt_pdf(cart, total, method):
    pdf = FPDF(format=(80, 150))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=9)
    pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True, align='C')
    pdf.cell(60, 5, txt="-" * 35, ln=True, align='C')
    for name, item in cart.items():
        # ใน PDF ใช้ชื่อภาษาอังกฤษชั่วคราวเพื่อกัน Font Error
        pdf.cell(40, 7, txt=f"Item x{item['qty']}")
        pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
    pdf.cell(60, 5, txt="-" * 35, ln=True, align='C')
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(30, 10, txt="TOTAL:")
    pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
    return pdf.output()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False
if 'pdf_receipt' not in st.session_state: st.session_state.pdf_receipt = None

df = load_data()

def process_checkout(method, total):
    summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
    payload = {"action": "checkout", "cart": st.session_state.cart, "method": method, "total": total, "summary": summary}
    try:
        st.session_state.pdf_receipt = generate_receipt_pdf(st.session_state.cart, total, method)
        response = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
        if response.status_code == 200:
            st.success("✅ บันทึกสำเร็จ!")
        else:
            st.error(f"❌ บันทึกไม่สำเร็จ: {response.text[:50]}") #
    except Exception as e:
        st.error(f"⚠️ เกิดข้อผิดพลาดการเชื่อมต่อ: {e}")

# --- UI แสดงผล ---
st.title("🏪 TAS POS SYSTEM")
col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("📦 สินค้า")
    if not df.empty:
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                # แสดงสต็อกแบบ Real-time
                st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:15px; text-align:center;">
                    <img src="{row['Image_URL']}" style="height:70px; object-fit:contain;"><br>
                    <b>{row['Name']}</b><br><span style="color:#f1c40f;">{row['Price']:,} ฿</span><br>
                    <small>คงเหลือ: {int(row['Stock'])}</small></div>""", unsafe_allow_html=True)
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
            # ปุ่มบวกลบที่ใช้งานได้จริง
            m, p = c2.columns(2)
            if m.button("➖", key=f"m_{name}"):
                if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                else: del st.session_state.cart[name]
                st.rerun()
            if p.button("➕", key=f"p_{name}"):
                st.session_state.cart[name]['qty'] += 1; st.rerun()
        
        st.divider()
        st.header(f"รวม: :orange[{total_sum:,}] ฿")
        
        # ส่วนชำระเงินและออกใบเสร็จ
        p1, p2 = st.columns(2)
        if p1.button("💵 เงินสด", use_container_width=True, type="primary"):
            process_checkout("Cash", total_sum)
        if p2.button("📱 QR Code", use_container_width=True):
            st.session_state.show_qr = not st.session_state.show_qr

        if st.session_state.show_qr:
            st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=200)
            if st.button("✅ ยืนยันชำระแล้ว", use_container_width=True):
                process_checkout("QR Code", total_sum)

        if st.session_state.pdf_receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จ", data=bytes(st.session_state.pdf_receipt), 
                               file_name="receipt.pdf", use_container_width=True)
            if st.button("🔄 เริ่มบิลใหม่", use_container_width=True):
                st.session_state.cart = {}; st.session_state.pdf_receipt = None; st.rerun()
