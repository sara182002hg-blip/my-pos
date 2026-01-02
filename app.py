import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. ตั้งค่าการเชื่อมต่อ (เช็คลิงก์ GID ให้ตรงกับ Google Sheets) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
PRODUCT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ✅ ฟังก์ชันโหลดข้อมูลที่เสถียรและเร็วขึ้น
@st.cache_data(ttl=2)
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# ✅ แก้ไขใบเสร็จ (ลบตัวอักษรไทยออกเพื่อให้ออกสลิปได้แน่นอน 100% ไม่ค้าง)
def generate_receipt_pdf(cart, total, method, bill_id):
    try:
        pdf = FPDF(format=(80, 150))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
        pdf.set_font("Arial", size=9)
        pdf.cell(60, 5, txt=f"ID: {bill_id}", ln=True)
        pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(60, 2, txt="-" * 35, ln=True)
        
        for name, item in cart.items():
            # แปลงชื่อสินค้าเป็นภาษาอังกฤษชั่วคราวเพื่อป้องกัน Error PDF
            pdf.cell(40, 7, txt=f"Item x{item['qty']}")
            pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
            
        pdf.cell(60, 2, txt="-" * 35, ln=True)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(30, 10, txt="TOTAL:")
        pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
        
        if method == "QR Code":
            qr_url = f"https://promptpay.io/0945016189/{total}.png"
            pdf.image(qr_url, x=15, w=50)
            
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except: return None

# --- ส่วนจัดการ State ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# --- UI Sidebar ---
st.sidebar.title("🏧 TAS POS")
menu = st.sidebar.radio("เมนูหลัก", ["🛒 ขายสินค้า", "📊 สรุปยอดขาย", "📦 เช็คสต็อก"])

if menu == "🛒 ขายสินค้า":
    st.markdown("### 🛒 รายการสินค้า")
    df_p = load_data(PRODUCT_URL)
    df_s = load_data(STOCK_URL) # ดึงสต็อกมาแสดง
    
    col_p, col_c = st.columns([3, 2])
    
    with col_p:
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                # ดึงจำนวนสต็อกคงเหลือ
                stock_qty = 0
                if not df_s.empty and 'Stock' in df_s.columns:
                    stock_qty = df_s.iloc[i]['Stock'] if i < len(df_s) else 0
                
                with grid[i % 3]:
                    with st.container(border=True): # ปรับรูปทรงสินค้าให้สวยงาม
                        st.image(row['Image_URL'], use_container_width=True)
                        st.write(f"**{row['Name']}**")
                        st.write(f"💰 {row['Price']} ฿ | 📦 คงเหลือ: {stock_qty}")
                        if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col_c:
        st.markdown("### 🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            for name, item in list(st.session_state.cart.items()):
                subtotal = item['price'] * item['qty']
                total_sum += subtotal
                c1, c2 = st.columns([3, 2])
                c1.write(f"**{name}**\n{item['price']} x {item['qty']}")
                if c2.button("❌", key=f"del_{name}"):
                    del st.session_state.cart[name]
                    st.rerun()
            
            st.divider()
            st.title(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("ชำระเงินโดย", ["เงินสด", "QR Code"], horizontal=True)
            
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=200)
            
            if st.button("✅ ยืนยันการชำระเงิน", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({item['qty']})" for n, item in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                
                res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                if res.status_code == 200:
                    st.session_state.last_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, bill_id)
                    st.session_state.cart = {}
                    st.success("บันทึกข้อมูลเรียบร้อย!")
                    st.rerun()
        
        if st.session_state.last_receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จ (PDF)", data=st.session_state.last_receipt, 
                             file_name=f"Receipt.pdf", mime="application/pdf", use_container_width=True)

elif menu == "📊 สรุปยอดขาย":
    st.markdown("### 📊 สรุปผลการขาย")
    df_sales = load_data(SALES_URL)
    if not df_sales.empty:
        # ✅ แก้ไขการดึงคอลัมน์ ยอดรวม ให้ตรงกับหน้า Sales จริง
        target_col = 'ยอดรวม' if 'ยอดรวม' in df_sales.columns else df_sales.columns[3]
        total_all = pd.to_numeric(df_sales[target_col], errors='coerce').sum()
        
        st.metric("ยอดขายรวมทั้งหมด", f"{total_all:,.2f} ฿")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True) # แสดงรายการล่าสุดก่อน
    else:
        st.warning("ยังไม่มีข้อมูลการขายในหน้า Sales")

elif menu == "📦 เช็คสต็อก":
    st.markdown("### 📦 สต็อกสินค้าคงเหลือ")
    df_stock = load_data(STOCK_URL)
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
    else:
        st.error("ไม่สามารถโหลดข้อมูลสต็อกได้")
