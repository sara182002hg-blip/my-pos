import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. ตั้งค่าการเชื่อมต่อ (ลิงก์ GID ทั้งหมดของคุณ) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
PRODUCT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwu (gid=0)"
# บังคับใช้ URL CSV เพื่อความเสถียรในการดึงข้อมูล
CSV_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"
CSV_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
CSV_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ✅ โหลดข้อมูลแบบไม่กระพริบ
@st.cache_data(ttl=1)
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        return pd.read_csv(StringIO(res.text))
    except: return pd.DataFrame()

# ✅ ฟังก์ชันใบเสร็จ PDF (รองรับทั้งเงินสดและ QR)
def generate_pdf(cart, total, method, bill_id):
    try:
        pdf = FPDF(format=(80, 150))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
        pdf.set_font("Arial", size=9)
        pdf.cell(60, 5, txt=f"Bill ID: {bill_id}", ln=True)
        pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(60, 2, txt="-" * 35, ln=True)
        for i, (name, item) in enumerate(cart.items()):
            pdf.cell(40, 7, txt=f"Item {i+1} x{item['qty']}")
            pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
        pdf.cell(60, 2, txt="-" * 35, ln=True)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(30, 10, txt="TOTAL:")
        pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
        if method == "QR Code":
            pdf.image(f"https://promptpay.io/0945016189/{total}.png", x=15, w=50)
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except: return None

# --- เก็บค่าในตัวแปรระบบ (Session State) ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

# --- UI ---
menu = st.sidebar.radio("เมนูระบบ", ["🛒 หน้าขายสินค้า", "📊 สรุปยอดขาย", "📦 สต็อกสินค้า"])

if menu == "🛒 หน้าขายสินค้า":
    df_p = load_data(CSV_PRODUCTS)
    df_s = load_data(CSV_STOCK)
    
    col1, col2 = st.columns([3, 1.8])
    
    with col1:
        st.subheader("📦 สินค้าทั้งหมด")
        if not df_p.empty:
            grid = st.columns(4) # ปรับรูปขนาดกลาง (4 คอลัมน์)
            for i, row in df_p.iterrows():
                with grid[i % 4]:
                    with st.container(border=True):
                        st.image(row['Image_URL'], height=120)
                        st.write(f"**{row['Name']}**")
                        st.write(f"💰 {row['Price']} ฿")
                        if st.button("➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            for name, item in list(st.session_state.cart.items()):
                total_sum += item['price'] * item['qty']
                c_name, c_btn = st.columns([2, 1.5])
                c_name.write(f"**{name}**\n{item['price']} ฿")
                # ✅ ปุ่มบวกลบ (อยู่ครบถ้วน)
                b1, b2 = c_btn.columns(2)
                if b1.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if b2.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.title(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("ชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=180)
            
            if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                
                res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                if res.status_code == 200:
                    # สร้างใบเสร็จเก็บไว้ก่อนล้างตะกร้า
                    st.session_state.last_bill = generate_pdf(st.session_state.cart, total_sum, method, bill_id)
                    st.session_state.cart = {}
                    st.success("ชำระเงินสำเร็จ!")
                    st.rerun()
        
        # ✅ ใบเสร็จและ QR จะไม่หายไปจนกว่าจะเริ่มการขายใหม่
        if st.session_state.last_bill:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จล่าสุด", data=st.session_state.last_bill, 
                             file_name="receipt.pdf", use_container_width=True)
            if st.button("เริ่มการขายใหม่ (ล้างใบเสร็จ)"):
                st.session_state.last_bill = None
                st.rerun()

elif menu == "📊 สรุปยอดขาย":
    st.title("📊 สรุปยอดขายจากหน้า Sales")
    df_sales = load_data(CSV_SALES)
    if not df_sales.empty:
        # ระบบค้นหาคอลัมน์ 'ยอดรวม' หรือ 'Total_Amount' แบบอัตโนมัติ
        col_name = next((c for c in df_sales.columns if 'ยอดรวม' in c or 'Total' in c), df_sales.columns[-1])
        total_all = pd.to_numeric(df_sales[col_name], errors='coerce').sum()
        st.metric("ยอดขายสะสมทั้งหมด", f"{total_all:,.2f} ฿")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else: st.warning("ไม่สามารถดึงข้อมูลจากหน้า Sales ได้")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 จำนวนสินค้าคงเหลือ")
    st.dataframe(load_data(CSV_STOCK), use_container_width=True)
