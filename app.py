import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. การเชื่อมต่อข้อมูล ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
PRODUCT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

@st.cache_data(ttl=1)
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# ✅ ฟังก์ชัน PDF: แก้ไข Error ภาษาไทยและ Bytearray
def generate_receipt_pdf(cart, total, method, bill_id):
    try:
        pdf = FPDF(format=(80, 150))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 10, txt="TAS POS SYSTEM", ln=True, align='C')
        pdf.set_font("Arial", size=9)
        pdf.cell(60, 5, txt=f"Bill ID: {bill_id}", ln=True)
        pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
        pdf.cell(60, 5, txt="-" * 35, ln=True)
        
        # ใช้ชื่อภาษาอังกฤษชั่วคราวเพื่อเลี่ยง Error ฟอนต์ภาษาไทย
        i = 1
        for name, item in cart.items():
            pdf.cell(40, 7, txt=f"Item {i} x{item['qty']}")
            pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
            i += 1
            
        pdf.cell(60, 5, txt="-" * 35, ln=True)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 10, txt="TOTAL:")
        pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
        pdf.set_font("Arial", size=8)
        pdf.cell(60, 5, txt=f"Payment: {method}", ln=True)

        # ✅ ส่งออกเป็น Bytes โดยตรงเพื่อแก้ปัญหา 'bytearray' error
        return pdf.output(dest='S')
    except Exception as e:
        return None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอด & กำไร", "📦 สต็อกสินค้า"])

if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    df_products = load_data(PRODUCT_URL)
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("📦 รายการสินค้า")
        if not df_products.empty:
            grid = st.columns(3)
            for i, row in df_products.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                        <img src="{row['Image_URL']}" style="width:100px; height:100px; object-fit:contain;"><br>
                        <b>{row['Name']}</b><br>
                        <span style="color:#f1c40f;">{row['Price']:,} ฿</span></div>""", unsafe_allow_html=True)
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
            
            st.divider()
            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("วิธีชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            
            # ✅ แสดง QR PromptPay ทันทีเพื่อให้สแกนง่าย
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=250, caption="สแกนเพื่อชำระเงิน")
            
            if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({item['qty']})" for n, item in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                try:
                    res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                    if res.status_code == 200:
                        st.session_state.last_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, bill_id)
                        st.success("บันทึกข้อมูลเรียบร้อย!")
                        st.session_state.cart = {}
                        st.rerun()
                except: st.error("บันทึกไม่สำเร็จ")
        
        # ✅ ปุ่มดาวน์โหลดใบเสร็จ (แสดงเมื่อขายสำเร็จ)
        if st.session_state.last_receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จล่าสุด", data=st.session_state.last_receipt, 
                             file_name=f"Receipt_{int(time.time())}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("ยังไม่มีรายการขายล่าสุด")

elif menu == "📊 สรุปยอด & กำไร":
    st.title("📊 สรุปผลการขาย")
    df_sales = load_data(SALES_URL)
    if not df_sales.empty:
        # ตรวจสอบคอลัมน์จาก Google Sheets จริง
        col_name = 'ยอดรวม' if 'ยอดรวม' in df_sales.columns else df_sales.columns[3] if len(df_sales.columns) > 3 else None
        if col_name:
            total_val = pd.to_numeric(df_sales[col_name], errors='coerce').fillna(0).sum()
            st.metric("ยอดขายรวมทั้งหมด", f"{total_val:,.2f} ฿")
            st.dataframe(df_sales.iloc[::-1], use_container_width=True)
        else:
            st.warning("ไม่พบคอลัมน์คำนวณยอด")
    else: st.info("ยังไม่มีข้อมูลการขาย")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 สต็อกสินค้า")
    st.dataframe(load_data(STOCK_URL), use_container_width=True)
