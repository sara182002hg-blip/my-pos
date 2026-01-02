import streamlit as st
import pandas as pd
import requests
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- การตั้งค่าลิงก์เชื่อมต่อ ---
# ดึงจากหน้า "เมนู" (GID: 1258507712)
CSV_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
# ดึงจากหน้า "Sales" (GID: 952949333)
CSV_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
# URL Apps Script ใหม่ล่าสุดที่คุณส่งมา
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz36dYw2mJI2Nr4aqCLswtd4v4wq3AhleY_tFWfBRRSw2YwlyAzla55gclUVlHR2ulB/exec"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        # กรองแถวที่ไม่มีชื่อสินค้าออก (ป้องกัน TypeError)
        df = df.dropna(subset=['Name']).reset_index(drop=True)
        return df
    except:
        return pd.DataFrame()

def generate_pdf(cart, total, bill_id):
    try:
        pdf = FPDF(format=(80, 150))
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(60, 8, "TAS POS RECEIPT", ln=True, align='C')
        pdf.set_font("Arial", size=8)
        pdf.cell(60, 4, f"ID: {bill_id}", ln=True)
        pdf.cell(60, 4, f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True)
        pdf.cell(60, 2, "-"*40, ln=True)
        for i, (name, item) in enumerate(cart.items()):
            pdf.cell(40, 5, f"Item {i+1} x{item['qty']}")
            pdf.cell(20, 5, f"{item['price']*item['qty']:,}", ln=True, align='R')
        pdf.cell(60, 2, "-"*40, ln=True)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 8, "TOTAL:", ln=0)
        pdf.cell(30, 8, f"{total:,} THB", ln=True, align='R')
        return pdf.output(dest='S').encode('latin-1', errors='ignore')
    except: return None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("เลือกเมนู", ["🛒 หน้าขายสินค้า", "📊 รายงานยอดขาย"])

if menu == "🛒 หน้าขายสินค้า":
    df_p = load_data(CSV_PRODUCTS)
    col_main, col_cart = st.columns([3, 1.8])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ✅ จัดเรียง 3 คอลัมน์
            grid = st.columns(3) 
            for i, row in df_p.iterrows():
                with grid[i % 3]:
                    with st.container(border=True):
                        # ✅ แสดงรูปภาพสูง 200px และเช็คความปลอดภัย
                        img = str(row.get('Image_URL', ""))
                        if img.startswith('http'):
                            st.image(img, height=200, use_container_width=True)
                        else:
                            st.info("🖼️ No Image")
                        
                        st.write(f"**{row['Name']}**")
                        st.write(f"💰 {row['Price']:,} ฿")
                        
                        if st.button("➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
        else:
            st.warning("⚠️ ไม่พบข้อมูลสินค้า")

    with col_cart:
        st.subheader("🛒 ตะกร้า")
        total_sum = 0
        for name, item in list(st.session_state.cart.items()):
            total_sum += item['price'] * item['qty']
            c1, c2 = st.columns([2, 1.5])
            c1.write(f"**{name}**\n{item['price']}฿")
            b1, b2 = c2.columns(2)
            if b1.button("➖", key=f"m_{name}"):
                if item['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                else: del st.session_state.cart[name]
                st.rerun()
            if b2.button("➕", key=f"p_{name}"):
                st.session_state.cart[name]['qty'] += 1
                st.rerun()
        
        if st.session_state.cart:
            st.divider()
            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("วิธีชำระ", ["เงินสด", "QR Code"], horizontal=True)
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=150)
            
            if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                
                try:
                    res = requests.post(SCRIPT_URL, json=payload)
                    if res.status_code == 200:
                        st.session_state.receipt = generate_pdf(st.session_state.cart, total_sum, bill_id)
                        st.session_state.cart = {}
                        st.success("บันทึกสำเร็จ!")
                        st.rerun()
                except:
                    st.error("การเชื่อมต่อ Apps Script ล้มเหลว")

        if st.session_state.receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จ (PDF)", data=st.session_state.receipt, file_name="receipt.pdf", use_container_width=True)
            if st.button("เริ่มขายรายการใหม่"):
                st.session_state.receipt = None
                st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปยอดขาย")
    df_sales = load_data(CSV_SALES)
    if not df_sales.empty:
        # พยายามหาคอลัมน์ยอดรวมอัตโนมัติ
        col = next((c for c in df_sales.columns if any(x in c for x in ['Total', 'รวม'])), df_sales.columns[-1])
        st.metric("ยอดรวมสะสม", f"{pd.to_numeric(df_sales[col], errors='coerce').sum():,.2f} ฿")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")
