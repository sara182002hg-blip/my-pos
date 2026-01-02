import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. ตั้งค่าการเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
# ✅ ใช้ gid=0 สำหรับหน้า Sales
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS Ultimate", layout="wide")

@st.cache_data(ttl=2) 
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8' 
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip() 
        return df
    except: return pd.DataFrame()

# ✅ ฟังก์ชัน PDF: แก้ไข Error 'bytearray' และเพิ่ม QR Code
def generate_receipt_pdf(cart, total, method, bill_id):
    try:
        pdf = FPDF(format=(80, 200))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
        pdf.set_font("Arial", size=9)
        pdf.cell(60, 5, txt=f"Bill ID: {bill_id}", ln=True)
        pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(60, 5, txt="-" * 35, ln=True)
        
        for i, (name, item) in enumerate(cart.items()):
            pdf.cell(40, 7, txt=f"Item {i+1} x{item['qty']}")
            pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
        
        pdf.cell(60, 5, txt="-" * 35, ln=True)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 10, txt="TOTAL:")
        pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
        
        if method == "QR Code":
            qr_url = f"https://promptpay.io/0945016189/{total}.png"
            pdf.ln(5)
            pdf.cell(60, 5, txt="Scan to Pay", ln=True, align='C')
            pdf.image(qr_url, x=15, w=50) 
            
        # ส่งค่าออกแบบ bytes โดยตรงเพื่อเลี่ยง Error .encode()
        return bytes(pdf.output(dest='S')) 
    except Exception as e: 
        st.error(f"PDF Error: {str(e)}")
        return None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'pdf_receipt' not in st.session_state: st.session_state.pdf_receipt = None

df_stock = load_data(STOCK_URL)
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
                    st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center; min-height:180px;">
                        <img src="{row['Image_URL']}" style="height:60px;"><br>
                        <b>{row['Name']}</b><br><span style="color:#f1c40f;">{row['Price']:,} ฿</span><br>
                        <small>สต็อก: {int(row['Stock'])}</small></div>""", unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1; st.rerun()
    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = sum(v['price'] * v['qty'] for v in st.session_state.cart.values())
            for name, item in list(st.session_state.cart.items()):
                c_info, c_btn = st.columns([2, 1.2])
                c_info.write(f"**{name}** {item['price']*item['qty']:,} ฿")
                m, p = c_btn.columns(2)
                if m.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if p.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1; st.rerun()
            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}; st.rerun()
            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("ช่องทางชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=220)
            if st.button("✅ ยืนยันการขาย (บันทึกข้อมูล)", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                try:
                    res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                    if res.status_code == 200: 
                        st.success(f"บันทึกสำเร็จ!")
                        st.session_state.pdf_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, bill_id)
                    else: st.error("บันทึกไม่สำเร็จ")
                except: st.error("ระบบขัดข้อง")
            if st.session_state.pdf_receipt:
                st.download_button("🖨️ ดาวน์โหลดใบเสร็จ", data=st.session_state.pdf_receipt, file_name=f"Bill_{bill_id}.pdf", use_container_width=True)
        else: st.info("ตะกร้าว่าง")

elif menu == "📊 สรุปยอด & กำไร":
    st.title("📊 สรุปผลการขาย")
    df_sales = load_data(SALES_URL)
    if not df_sales.empty:
        try:
            # ✅ ปรับการค้นหาคอลัมน์ให้ตรงกับ "ยอดรวม" ในชีตของคุณ
            target_cols = [c for c in df_sales.columns if 'ยอดรวม' in c or 'Total' in c]
            if target_cols:
                col_name = target_cols[0]
                total_val = pd.to_numeric(df_sales[col_name], errors='coerce').fillna(0).sum()
                st.metric("ยอดขายรวมทั้งหมด", f"{total_val:,.2f} ฿")
                st.subheader("📋 รายการล่าสุด")
                st.dataframe(df_sales.iloc[::-1], use_container_width=True)
            else:
                st.error("ไม่พบคอลัมน์ 'ยอดรวม' กรุณาตรวจสอบหัวตารางในหน้า Sales")
                st.dataframe(df_sales.head())
        except Exception as e: st.error(f"Error: {e}")
    else: st.info("ยังไม่มีข้อมูลในแผ่น Sales")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 หลังบ้าน (สต็อก)")
    st.dataframe(df_stock, use_container_width=True)
