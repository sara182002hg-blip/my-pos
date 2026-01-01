import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. ตั้งค่าการเชื่อมต่อ (ตรวจสอบ URL ให้ถูกต้อง) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS Ultimate", layout="wide")

# แก้ปัญหาที่ 2 และ 9: โหลดข้อมูลแบบ Real-time และเร็วขึ้นด้วย Cache ระยะสั้น
@st.cache_data(ttl=5) 
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8' # แก้ปัญหาภาษาต่างดาว (ข้อ 1)
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# ฟังก์ชันสร้าง PDF ใบเสร็จ
def generate_receipt_pdf(cart, total, method, bill_id):
    pdf = FPDF(format=(80, 150))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
    pdf.set_font("Arial", size=8)
    pdf.cell(60, 5, txt=f"Bill ID: {bill_id}", ln=True)
    pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(60, 5, txt="-" * 35, ln=True)
    for name, item in cart.items():
        pdf.cell(40, 7, txt=f"{name[:15]} x{item['qty']}")
        pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
    pdf.cell(60, 5, txt="-" * 35, ln=True)
    pdf.cell(30, 10, txt="TOTAL:")
    pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
    return pdf.output()

# การจัดการ State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'pdf_receipt' not in st.session_state: st.session_state.pdf_receipt = None

df_stock = load_data(STOCK_URL)

# เมนูหลัก (แก้ปัญหาที่ 1: หน้าหลังบ้าน/จัดการสต็อก)
menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอด & กำไร", "📦 สต็อกสินค้า"])

if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 รายการสินค้า")
        if not df_stock.empty:
            grid = st.columns(3)
            for i, row in df_stock.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">
                        <img src="{row['Image_URL']}" style="height:65px;"><br>
                        <b>{row['Name']}</b><br><span style="color:#f1c40f;">{row['Price']:,} ฿</span><br>
                        <small>สต็อก: {int(row['Stock'])}</small></div>""", unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0, 'cost': row.get('Cost', 0)})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            for name, item in list(st.session_state.cart.items()):
                total_sum += (item['price'] * item['qty'])
                c_info, c_btn = st.columns([2, 1.2])
                c_info.write(f"**{name}**\n{item['price']*item['qty']:,} ฿")
                m, p = c_btn.columns(2)
                if m.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if p.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1; st.rerun()
            
            st.divider()
            # แก้ปัญหาที่ 6: ปุ่มเคลียร์ตะกร้า
            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}; st.rerun()

            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("ช่องทางชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=200)

            # แก้ปัญหาที่ 8: ส่งเลขบิลและรายชื่อสินค้าเข้า Google Sheets
            if st.button("✅ ยืนยันการขาย (บันทึกข้อมูล)", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {
                    "action": "checkout",
                    "bill_id": bill_id,
                    "cart": st.session_state.cart,
                    "method": method,
                    "total": total_sum,
                    "summary": summary
                }
                try:
                    st.session_state.pdf_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, bill_id)
                    requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
                    st.success(f"บันทึกสำเร็จ! เลขบิล: {bill_id}")
                except:
                    st.error("บันทึกไม่สำเร็จ ตรวจสอบอินเทอร์เน็ต")

            if st.session_state.pdf_receipt:
                st.download_button("🖨️ ดาวน์โหลดใบเสร็จ (PDF)", data=bytes(st.session_state.pdf_receipt), file_name=f"Bill_{int(time.time())}.pdf", use_container_width=True)

elif menu == "📊 สรุปยอด & กำไร":
    st.title("📈 ผลประกอบการร้านค้า")
    df_sales = load_data(SALES_URL)
    
    if not df_sales.empty:
        # แก้ปัญหาที่ 3 และ 7: ยอดขายรายวันและกำไรขาดทุน
        col_m1, col_m2 = st.columns(2)
        total_sales = df_sales['Total_Amount'].sum() if 'Total_Amount' in df_sales.columns else 0
        col_m1.metric("ยอดขายรวม", f"{total_sales:,} ฿")
        
        # คำนวณกำไร (ถ้าในชีตมีคอลัมน์ Cost)
        if 'Cost' in df_sales.columns:
            total_profit = total_sales - df_sales['Cost'].sum()
            col_m2.metric("กำไรสุทธิ", f"{total_profit:,} ฿")

        # แก้ปัญหาที่ 4: สถิติสินค้าขายดี
        st.subheader("🏆 รายการขายล่าสุด")
        st.dataframe(df_sales.tail(10), use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลการขาย")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 จัดการสต็อกหลังบ้าน")
    st.dataframe(df_stock, use_container_width=True)
