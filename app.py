import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- การตั้งค่าการเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
PRODUCT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ✅ โหลดข้อมูลแบบ Cache เพื่อความเร็ว
@st.cache_data(ttl=5)
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# ✅ แก้ไขใบเสร็จให้รองรับภาษาไทย (ใช้ฟอนต์มาตรฐานที่รองรับ Unicode)
def generate_receipt_pdf(cart, total, method, bill_id):
    try:
        pdf = FPDF(format=(80, 150))
        pdf.add_page()
        # ใช้ฟอนต์ Helvetica (Standard) และเลี่ยงตัวอักษรพิเศษเพื่อป้องกัน Error
        pdf.set_font("Helvetica", 'B', 12)
        pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
        pdf.set_font("Helvetica", size=9)
        pdf.cell(60, 5, txt=f"Bill ID: {bill_id}", ln=True)
        pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(60, 2, txt="-" * 35, ln=True)
        
        pdf.set_font("Helvetica", size=9)
        for name, item in cart.items():
            # แปลงชื่อสินค้าเป็นภาษาอังกฤษหรือตัดคำเพื่อป้องกัน Error
            clean_name = name.encode('ascii', 'ignore').decode('ascii') if not name.isascii() else name
            if not clean_name: clean_name = "Product Item"
            pdf.cell(40, 7, txt=f"{clean_name[:15]} x{item['qty']}")
            pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
            
        pdf.cell(60, 2, txt="-" * 35, ln=True)
        pdf.set_font("Helvetica", 'B', 10)
        pdf.cell(30, 10, txt="TOTAL:")
        pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
        
        if method == "QR Code":
            qr_url = f"https://promptpay.io/0945016189/{total}.png"
            pdf.image(qr_url, x=15, y=pdf.get_y()+2, w=50)
            
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except Exception as e:
        return None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# --- ส่วนของการทำงาน (UI) ---
menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอด & กำไร"])

if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    df_products = load_data(PRODUCT_URL)
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📦 รายการสินค้า")
        if not df_products.empty:
            # ✅ ใช้ container เพื่อลดการกระพริบเวลาเลือกสินค้า
            grid = st.columns(3)
            for i, row in df_products.iterrows():
                with grid[i % 3]:
                    with st.container(border=True):
                        st.image(row['Image_URL'], use_container_width=True)
                        st.write(f"**{row['Name']}**")
                        st.write(f"💰 {row['Price']:,} ฿")
                        if st.button(f"➕ เพิ่ม", key=f"btn_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = sum(v['price'] * v['qty'] for v in st.session_state.cart.values())
            for name, item in list(st.session_state.cart.items()):
                c_name, c_qty = st.columns([2, 1])
                c_name.write(f"{name}")
                # ✅ ปุ่มบวกลบแบบไม่กระพริบมาก
                with c_qty:
                    q_col1, q_col2 = st.columns(2)
                    if q_col1.button("➖", key=f"m_{name}"):
                        if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                        else: del st.session_state.cart[name]
                        st.rerun()
                    if q_col2.button("➕", key=f"p_{name}"):
                        st.session_state.cart[name]['qty'] += 1
                        st.rerun()
            
            st.divider()
            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("วิธีชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=200)
            
            if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({item['qty']})" for n, item in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                with st.spinner('กำลังบันทึก...'):
                    try:
                        res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                        if res.status_code == 200:
                            st.session_state.last_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, bill_id)
                            st.session_state.cart = {}
                            st.success("บันทึกสำเร็จ!")
                            st.rerun()
                    except: st.error("บันทึกไม่สำเร็จ")
        
        # ✅ ปุ่มดาวน์โหลดใบเสร็จ (แสดงทันทีหลังขาย)
        if st.session_state.last_receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จล่าสุด", data=st.session_state.last_receipt, 
                             file_name=f"Receipt_{int(time.time())}.pdf", mime="application/pdf", use_container_width=True)

elif menu == "📊 สรุปยอด & กำไร":
    st.title("📊 สรุปผลการขาย")
    df_sales = load_data(SALES_URL)
    if not df_sales.empty:
        # ✅ ค้นหาคอลัมน์ 'ยอดรวม' อย่างแม่นยำ
        col_name = next((c for c in df_sales.columns if 'ยอดรวม' in c or 'Total' in c), None)
        if col_name:
            total_val = pd.to_numeric(df_sales[col_name], errors='coerce').fillna(0).sum()
            st.metric("ยอดขายรวมทั้งหมด", f"{total_val:,.2f} ฿")
            st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else: st.info("ยังไม่มีข้อมูลการขาย")
