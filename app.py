import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. ตั้งค่าการเชื่อมต่อ (ตรวจสอบความถูกต้อง) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
# ✅ บังคับดึงข้อมูลจากหน้า Sales (gid=0) เพื่อแก้ปัญหาหา 'ยอดรวม' ไม่เจอ
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# CSS สำหรับขยายขนาดตัวหนังสือและปรับแต่ง UI
st.markdown("""
    <style>
    .stButton>button { height: 3em; font-size: 1.2rem !important; font-weight: bold; }
    .product-card { border: 2px solid #444; padding: 15px; border-radius: 15px; text-align: center; background-color: #1e1e1e; }
    .product-name { font-size: 1.4rem !important; font-weight: bold; color: #ffffff; margin-top: 10px; }
    .product-price { font-size: 1.6rem !important; color: #f1c40f; font-weight: bold; }
    .product-stock { font-size: 1rem; color: #bbb; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1) 
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8' 
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip() 
        return df
    except: return pd.DataFrame()

# ✅ ฟังก์ชัน PDF: เพิ่ม QR Code และปรับตำแหน่งให้แสดงผลได้จริง
def generate_receipt_pdf(cart, total, method, bill_id):
    try:
        pdf = FPDF(format=(80, 200)) 
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
        pdf.set_font("Arial", size=10)
        pdf.cell(60, 5, txt=f"Bill ID: {bill_id}", ln=True)
        pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(60, 5, txt="-" * 30, ln=True)
        for name, item in cart.items():
            pdf.cell(40, 8, txt=f"{name[:15]} x{item['qty']}")
            pdf.cell(20, 8, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
        pdf.cell(60, 5, txt="-" * 30, ln=True)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(30, 10, txt="TOTAL:")
        pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
        if method == "QR Code":
            pdf.ln(5)
            pdf.set_font("Arial", size=9)
            pdf.cell(60, 5, txt="SCAN TO PAY", ln=True, align='C')
            qr_url = f"https://promptpay.io/0945016189/{total}.png"
            pdf.image(qr_url, x=15, w=50) 
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
        st.subheader("📦 รายการสินค้า (กดเลือกเพื่อเพิ่มในตะกร้า)")
        if not df_stock.empty:
            grid = st.columns(2) # ปรับเป็น 2 คอลัมน์เพื่อให้รูปใหญ่ขึ้น
            for i, row in df_stock.iterrows():
                with grid[i % 2]:
                    st.markdown(f"""<div class="product-card">
                        <img src="{row['Image_URL']}" style="width:180px; height:180px; object-fit:contain;"><br>
                        <div class="product-name">{row['Name']}</div>
                        <div class="product-price">{row['Price']:,} ฿</div>
                        <div class="product-stock">คงเหลือ: {int(row['Stock'])}</div>
                        </div>""", unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"➕ เพิ่ม {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1; st.rerun()
    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = sum(v['price'] * v['qty'] for v in st.session_state.cart.values())
            for name, item in list(st.session_state.cart.items()):
                c1, c2 = st.columns([3, 2])
                c1.markdown(f"**{name}**<br>{item['price']:,} x {item['qty']}", unsafe_allow_html=True)
                if c2.button("❌ ลบ", key=f"del_{name}"):
                    del st.session_state.cart[name]; st.rerun()
            st.divider()
            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("วิธีชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=250)
            if st.button("✅ ยืนยันการชำระเงิน", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                try:
                    res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                    if res.status_code == 200:
                        st.session_state.pdf_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, bill_id)
                        st.success("บันทึกข้อมูลเรียบร้อย!")
                        st.session_state.cart = {} # ล้างตะกร้าหลังขายสำเร็จ
                    else: st.error("บันทึกไม่สำเร็จ")
                except: st.error("การเชื่อมต่อล้มเหลว")
            if st.session_state.pdf_receipt:
                st.download_button("🖨️ ดาวน์โหลดใบเสร็จ (PDF)", data=st.session_state.pdf_receipt, file_name=f"Receipt_{int(time.time())}.pdf", use_container_width=True)
        else: st.info("ยังไม่มีสินค้าในตะกร้า")

elif menu == "📊 สรุปยอด & กำไร":
    st.title("📊 สรุปผลการขาย")
    df_sales = load_data(SALES_URL)
    if not df_sales.empty:
        try:
            # ✅ ค้นหาคอลัมน์ "ยอดรวม" โดยตรงจากหน้า Sales
            target_cols = [c for c in df_sales.columns if 'ยอดรวม' in c or 'Total' in c]
            if target_cols:
                col_name = target_cols[0]
                total_val = pd.to_numeric(df_sales[col_name], errors='coerce').fillna(0).sum()
                st.metric("ยอดขายรวมทั้งหมด", f"{total_val:,.2f} ฿")
                st.subheader("📋 รายการล่าสุด")
                st.dataframe(df_sales.iloc[::-1], use_container_width=True)
            else:
                st.error("ไม่พบคอลัมน์ 'ยอดรวม' ในหน้าชีต Sales")
                st.write("คอลัมน์ที่มีปัจจุบัน:", list(df_sales.columns))
        except Exception as e: st.error(f"Error: {e}")
    else: st.info("ยังไม่มีข้อมูลการขาย")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 จัดการสต็อกสินค้า")
    st.dataframe(df_stock, use_container_width=True)
