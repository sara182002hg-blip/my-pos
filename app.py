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
# ✅ บังคับดึงข้อมูลจากหน้า Sales (gid=0)
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ✅ ปรับขนาดรูปภาพและตัวหนังสือให้ใหญ่ขึ้นกว่าเดิม
st.markdown("""
    <style>
    .stButton>button { height: 3.5em; font-size: 1.3rem !important; }
    .product-card { border: 2px solid #555; padding: 20px; border-radius: 20px; text-align: center; background-color: #1e1e1e; }
    .product-name { font-size: 1.6rem !important; font-weight: bold; margin-top: 15px; }
    .product-price { font-size: 1.8rem !important; color: #f1c40f; font-weight: bold; }
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

# ✅ ฟังก์ชัน PDF: แก้ไขการโหลดรูปภาพ QR Code ให้เสถียรขึ้น
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
            # ใช้การ download รูปมาก่อนเพื่อป้องกัน Error ในบางกรณี
            qr_img = requests.get(qr_url).content
            with open("temp_qr.png", "wb") as f: f.write(qr_img)
            pdf.image("temp_qr.png", x=15, w=50)
            
        return bytes(pdf.output(dest='S')) 
    except Exception as e:
        st.error(f"PDF Error: {str(e)}")
        return None

if 'cart' not in st.session_state: st.session_state.cart = {}
# เก็บใบเสร็จแยกตาม Bill ID เพื่อป้องกันปุ่มหาย
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

df_stock = load_data(STOCK_URL)
menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอด & กำไร", "📦 สต็อกสินค้า"])

if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])
    with col1:
        st.subheader("📦 เลือกสินค้า")
        if not df_stock.empty:
            grid = st.columns(2) # 2 คอลัมน์เพื่อให้รูปใหญ่ที่สุด
            for i, row in df_stock.iterrows():
                with grid[i % 2]:
                    st.markdown(f"""<div class="product-card">
                        <img src="{row['Image_URL']}" style="width:250px; height:250px; object-fit:contain;"><br>
                        <div class="product-name">{row['Name']}</div>
                        <div class="product-price">{row['Price']:,} ฿</div>
                        </div>""", unsafe_allow_html=True)
                    if st.button(f"➕ เพิ่ม {row['Name']}", key=f"add_{i}", use_container_width=True):
                        n = str(row['Name']).strip()
                        st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                        st.session_state.cart[n]['qty'] += 1; st.rerun()
    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = sum(v['price'] * v['qty'] for v in st.session_state.cart.values())
            for name, item in list(st.session_state.cart.items()):
                c1, c2 = st.columns([3, 1.5])
                c1.write(f"**{name}** ({item['qty']})")
                if c2.button("❌ ลบ", key=f"del_{name}"):
                    del st.session_state.cart[name]; st.rerun()
            st.divider()
            st.header(f"ยอดรวม: {total_sum:,} ฿")
            method = st.radio("วิธีชำระเงิน", ["เงินสด", "QR Code"], horizontal=True)
            if method == "QR Code":
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=250)
            
            if st.button("✅ ยืนยันการขาย", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": method}
                try:
                    res = requests.post(SCRIPT_URL, json=payload, timeout=15)
                    if res.status_code == 200:
                        st.session_state.last_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, bill_id)
                        st.session_state.cart = {}
                        st.success("บันทึกข้อมูลแล้ว!")
                        st.rerun()
                    else: st.error("บันทึกไม่สำเร็จ")
                except: st.error("เชื่อมต่อ Google Sheets ไม่ได้")
        
        # ✅ ปุ่มดาวน์โหลดใบเสร็จที่แสดงค้างไว้หลังขายเสร็จ
        if st.session_state.last_receipt:
            st.download_button("🖨️ ดาวน์โหลดใบเสร็จล่าสุด (PDF)", 
                             data=st.session_state.last_receipt, 
                             file_name=f"Receipt_{int(time.time())}.pdf", 
                             use_container_width=True)

elif menu == "📊 สรุปยอด & กำไร":
    st.title("📊 สรุปผลการขาย")
    df_sales = load_data(SALES_URL)
    if not df_sales.empty:
        try:
            # ✅ ค้นหาชื่อคอลัมน์ "Total_Amount" ที่คุณเปลี่ยนใหม่
            if 'Total_Amount' in df_sales.columns:
                total_val = pd.to_numeric(df_sales['Total_Amount'], errors='coerce').fillna(0).sum()
                st.metric("ยอดขายรวมทั้งหมด", f"{total_val:,.2f} ฿")
                st.dataframe(df_sales.iloc[::-1], use_container_width=True)
            else:
                st.error("ไม่พบคอลัมน์ 'Total_Amount' กรุณาตรวจสอบการสะกดใน Google Sheets")
                st.write("ชื่อคอลัมน์ที่พบตอนนี้:", list(df_sales.columns))
        except Exception as e: st.error(f"Error: {e}")
    else: st.info("ยังไม่มีข้อมูลในแผ่น Sales")

elif menu == "📦 สต็อกสินค้า":
    st.title("📦 สต็อกสินค้า")
    st.dataframe(df_stock, use_container_width=True)
