import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- การตั้งค่า (ตรวจสอบ GID และ URL ให้ถูกต้อง) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
CSV_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"
CSV_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
CSV_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ✅ ฟังก์ชันโหลดข้อมูลพร้อมล้างค่าว่างป้องกัน Error
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.fillna("") 
    except:
        return pd.DataFrame()

# ✅ ฟังก์ชันสร้างใบเสร็จ PDF (รองรับเฉพาะภาษาอังกฤษเพื่อความเสถียร)
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
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except:
        return None

# --- เตรียมระบบตะกร้า ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("เมนูระบบ", ["🛒 หน้าขายสินค้า", "📊 ยอดขาย", "📦 สต็อก"])

if menu == "🛒 หน้าขายสินค้า":
    df_p = load_data(CSV_PRODUCTS)
    col_l, col_r = st.columns([3, 1.8])
    
    with col_l:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ✅ ปรับเป็น 3 คอลัมน์ตามคำขอ
            grid = st.columns(3) 
            for i, row in df_p.iterrows():
                with grid[i % 3]:
                    with st.container(border=True):
                        # ✅ แก้ TypeError โดยตรวจสอบลิงก์รูปภาพ
                        img = row.get('Image_URL', "")
                        if isinstance(img, str) and img.startswith('http'):
                            # ✅ ปรับความสูงเป็น 200px ตามคำขอ
                            st.image(img, height=200, use_container_width=True)
                        else:
                            st.info("ไม่มีรูปภาพ")
                        
                        st.write(f"**{row.get('Name', 'N/A')}**")
                        st.write(f"฿{row.get('Price', 0)}")
                        
                        if st.button("➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            n = str(row.get('Name', 'Item')).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row.get('Price', 0), 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col_r:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            for name, item in list(st.session_state.cart.items()):
                total_sum += item['price'] * item['qty']
                c1, c2 = st.columns([2, 1.5])
                c1.write(f"{name}\n{item['price']}฿")
                # ✅ ปุ่มบวกลบสินค้า
                b1, b2 = c2.columns(2)
                if b1.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if b2.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.title(f"{total_sum:,} ฿")
            method = st.radio("ชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            
            if st.button("✅ ยืนยันชำระเงิน", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                
                if requests.post(SCRIPT_URL, json=payload, timeout=10).status_code == 200:
                    st.session_state.receipt = generate_pdf(st.session_state.cart, total_sum, method, bill_id)
                    st.session_state.cart = {}
                    st.success("บันทึกข้อมูลเรียบร้อย!")
                    st.rerun()

        if st.session_state.receipt:
            st.download_button("🖨️ พิมพ์ใบเสร็จ (PDF)", data=st.session_state.receipt, file_name="receipt.pdf", use_container_width=True)
            if st.button("เริ่มการขายใหม่"):
                st.session_state.receipt = None
                st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 สรุปยอดขาย")
    df = load_data(CSV_SALES)
    if not df.empty:
        st.dataframe(df.iloc[::-1], use_container_width=True)

elif menu == "📦 สต็อก":
    st.title("📦 เช็คสต็อกสินค้า")
    st.dataframe(load_data(CSV_STOCK), use_container_width=True)
