import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- การตั้งค่า (เช็ค GID ให้ถูกต้อง) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
CSV_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"
CSV_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
CSV_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS", layout="wide")

def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# ✅ PDF Safe Mode (กันตัวอักษรไทยพัง)
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
    except: return None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

menu = st.sidebar.radio("เมนูระบบ", ["🛒 หน้าขายสินค้า", "📊 ยอดขาย", "📦 สต็อก"])

if menu == "🛒 หน้าขายสินค้า":
    df_p = load_data(CSV_PRODUCTS)
    df_s = load_data(CSV_STOCK)
    
    col_l, col_r = st.columns([3, 1.8])
    
    with col_l:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(4) # ปรับขนาดรูปให้พอดี
            for i, row in df_p.iterrows():
                with grid[i % 4]:
                    with st.container(border=True):
                        # ✅ แก้ไขจุดที่ทำให้เกิด TypeError
                        img = row.get('Image_URL')
                        if pd.notnull(img) and isinstance(img, str) and img.startswith('http'):
                            st.image(img, height=100, use_container_width=True)
                        else:
                            st.info("ไม่มีรูปภาพ") # ถ้าไม่มีรูปให้โชว์ข้อความแทน แอปจะได้ไม่พัง
                        
                        st.write(f"**{row.get('Name', 'N/A')}**")
                        st.write(f"฿{row.get('Price', 0)}")
                        
                        if st.button("➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            n = str(row.get('Name', 'Item')).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row.get('Price', 0), 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col_r:
        st.subheader("🛒 ตะกร้า")
        if st.session_state.cart:
            total_sum = 0
            for name, item in list(st.session_state.cart.items()):
                total_sum += item['price'] * item['qty']
                c1, c2 = st.columns([2, 1.5])
                c1.write(f"{name}\n{item['price']}฿")
                # ✅ ปุ่มบวกลบอยู่ครบ
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
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=150)
            
            if st.button("✅ ยืนยันชำระเงิน", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                
                if requests.post(SCRIPT_URL, json=payload, timeout=10).status_code == 200:
                    st.session_state.last_receipt = generate_pdf(st.session_state.cart, total_sum, method, bill_id)
                    st.session_state.cart = {}
                    st.success("สำเร็จ!")
                    st.rerun()

        if st.session_state.last_receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จ", data=st.session_state.last_receipt, file_name="bill.pdf", use_container_width=True)
            if st.button("เริ่มการขายใหม่"):
                st.session_state.last_receipt = None
                st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 สรุปยอดขาย")
    df = load_data(CSV_SALES)
    if not df.empty:
        col = next((c for c in df.columns if 'ยอดรวม' in c or 'Total' in c), df.columns[-1])
        st.metric("ยอดรวม", f"{pd.to_numeric(df[col], errors='coerce').sum():,.2f} ฿")
        st.dataframe(df.iloc[::-1], use_container_width=True)

elif menu == "📦 สต็อก":
    st.title("📦 เช็คสต็อก")
    st.dataframe(load_data(CSV_STOCK), use_container_width=True)
