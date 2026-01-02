import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- การตั้งค่าการเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycby8f3q4R9it3uGxTpcMlXR_nfsV1c9bJPXy3hJahIVZyAul1IHpY6JpsY5iGrg3_Czp/exec"
CSV_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"
CSV_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
CSV_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ✅ โหลดข้อมูล (เพิ่ม Error Handling ป้องกันหน้าหาย)
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

# ✅ ฟังก์ชันใบเสร็จ (แก้ไข Character Error ภาษาไทย)
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
        for name, item in cart.items():
            # ใช้ชื่อภาษาอังกฤษชั่วคราวหรือคำกลางๆ เพื่อไม่ให้ PDF พัง
            pdf.cell(40, 7, txt=f"Product x{item['qty']}")
            pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
        pdf.cell(60, 2, txt="-" * 35, ln=True)
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(30, 10, txt="TOTAL:")
        pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except: return None

# --- Session State ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# --- UI Layout ---
menu = st.sidebar.radio("เมนูระบบ", ["🛒 หน้าขายสินค้า", "📊 สรุปยอดขาย", "📦 สต็อกสินค้า"])

if menu == "🛒 หน้าขายสินค้า":
    df_p = load_data(CSV_PRODUCTS)
    df_stk = load_data(CSV_STOCK)
    
    col_main, col_cart = st.columns([3, 1.8])
    
    with col_main:
        st.subheader("📦 สินค้าทั้งหมด")
        if not df_p.empty:
            # ปรับให้เป็น 4 คอลัมน์เพื่อให้รูปขนาดพอดี ไม่ใหญ่เกินไป
            grid = st.columns(4)
            for i, row in df_p.iterrows():
                # ดึงสต็อกมาโชว์ (ถ้ามี)
                stk_val = df_stk.iloc[i]['Stock'] if not df_stk.empty and i < len(df_stk) else "N/A"
                with grid[i % 4]:
                    with st.container(border=True):
                        # แก้ไข Error TypeError ในการดึงรูป
                        img_url = row['Image_URL'] if 'Image_URL' in df_p.columns else ""
                        st.image(img_url, height=120, use_container_width=True)
                        st.write(f"**{row['Name']}**")
                        st.caption(f"💰 {row['Price']} ฿ | 📦 คงเหลือ: {stk_val}")
                        if st.button("➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col_cart:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            for name, item in list(st.session_state.cart.items()):
                total_sum += item['price'] * item['qty']
                c_info, c_qty = st.columns([2, 1.5])
                c_info.write(f"**{name}**\n{item['price']} ฿")
                # ✅ ปุ่มบวกลบต้องอยู่ครบ
                b1, b2 = c_qty.columns(2)
                if b1.button("➖", key=f"min_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if b2.button("➕", key=f"pls_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("วิธีชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=200)
            
            if st.button("✅ ยืนยันชำระเงิน (บันทึกข้อมูล)", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                
                with st.spinner('กำลังบันทึก...'):
                    res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                    if res.status_code == 200:
                        st.session_state.last_receipt = generate_pdf(st.session_state.cart, total_sum, method, bill_id)
                        st.session_state.cart = {}
                        st.success("บันทึกข้อมูลและอัปเดตสต็อกเรียบร้อย!")
                        st.rerun()
        
        # ✅ ใบเสร็จไม่หายหลังชำระเงิน
        if st.session_state.last_receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จ (PDF)", data=st.session_state.last_receipt, 
                             file_name=f"Receipt_{int(time.time())}.pdf", mime="application/pdf", use_container_width=True)
            if st.button("เริ่มการขายใหม่"):
                st.session_state.last_receipt = None
                st.rerun()

elif menu == "📊 สรุปยอดขาย":
    st.title("📊 สรุปผลการขาย")
    df_sales = load_data(CSV_SALES)
    if not df_sales.empty:
        # ✅ แก้ไขการหาคอลัมน์ ยอดรวม ให้ตรงกับหน้า Sales จริง
        col_total = next((c for c in df_sales.columns if 'ยอดรวม' in c or 'Total' in c), None)
        if col_total:
            total_val = pd.to_numeric(df_sales[col_total], errors='coerce').sum()
            st.metric("ยอดขายสะสม", f"{total_val:,.2f} ฿")
            st.dataframe(df_sales.iloc[::-1], use_container_width=True) # รายการล่าสุดอยู่บน
        else:
            st.error("ไม่พบชื่อคอลัมน์ 'ยอดรวม' ในหน้า Sales กรุณาตรวจสอบหัวตาราง")
            st.write("คอลัมน์ที่พบ:", list(df_sales.columns))
    else: st.warning("ยังไม่มีข้อมูลการขาย")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 สต็อกคงเหลือปัจจุบัน")
    st.dataframe(load_data(CSV_STOCK), use_container_width=True)
