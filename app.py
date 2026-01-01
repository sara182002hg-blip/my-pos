import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime
from io import StringIO
from fpdf import FPDF

# --- 1. ตั้งค่าการเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
SALES_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv" # เปลี่ยน GID ให้ตรงกับหน้า Sales

st.set_page_config(page_title="TAS POS Ultimate", layout="wide")

# ฟังก์ชันดึงข้อมูล (ปรับปรุงให้เร็วขึ้นด้วย Cache)
@st.cache_data(ttl=5) # โหลดใหม่ทุก 5 วินาที ลดความหน่วงหน้าเว็บ
def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=5)
        res.encoding = 'utf-8' # แก้ภาษาต่างดาว
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# ฟังก์ชันสร้าง PDF (สำหรับข้อ 10)
def generate_receipt_pdf(cart, total, method, order_id):
    pdf = FPDF(format=(80, 150))
    pdf.add_page()
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(60, 10, txt="TAS SHOP RECEIPT", ln=True, align='C')
    pdf.set_font("Arial", size=8)
    pdf.cell(60, 5, txt=f"Order: {order_id}", ln=True)
    pdf.cell(60, 5, txt=f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    pdf.cell(60, 5, txt="-" * 35, ln=True)
    for name, item in cart.items():
        pdf.cell(40, 7, txt=f"{name[:15]} x{item['qty']}")
        pdf.cell(20, 7, txt=f"{item['price']*item['qty']:,}", ln=True, align='R')
    pdf.cell(60, 5, txt="-" * 35, ln=True)
    pdf.cell(30, 10, txt="TOTAL:")
    pdf.cell(30, 10, txt=f"{total:,} THB", ln=True, align='R')
    return pdf.output()

# --- State Management ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'pdf_receipt' not in st.session_state: st.session_state.pdf_receipt = None

df_stock = load_data(STOCK_URL)

# --- เมนูระบบ ---
menu = st.sidebar.radio("เมนูหลัก", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอดรายวัน & กำไร", "📦 จัดการสต็อก"])

if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 รายการสินค้า")
        if not df_stock.empty:
            grid = st.columns(3)
            for i, row in df_stock.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">
                        <img src="{row['Image_URL']}" style="height:60px;"><br>
                        <b>{row['Name']}</b><br><span style="color:#f1c40f;">{row['Price']:,} ฿</span><br>
                        <small>สต็อก: {int(row['Stock'])}</small></div>""", unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            n = str(row['Name']).strip()
                            st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0, 'cost': row.get('Cost', 0)})
                            st.session_state.cart[n]['qty'] += 1
                            st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            for name, item in list(st.session_state.cart.items()):
                total_sum += (item['price'] * item['qty'])
                c_info, c_btn = st.columns([2, 1.2])
                c_info.write(f"**{name}**\n{item['price']*item['qty']:,} ฿")
                m, p = c_btn.columns(2)
                if m.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if p.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1; st.rerun()
            
            st.divider()
            # 6. เพิ่มปุ่มเคลียร์ตะกร้า (กลับมาแล้ว)
            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True, type="secondary"):
                st.session_state.cart = {}; st.rerun()

            st.header(f"รวม: {total_sum:,} ฿")
            
            method = st.radio("ช่องทางชำระเงิน", ["เงินสด", "โอนเงิน"], horizontal=True)
            if st.button("✅ ยืนยันการขาย (ตัดสต็อก & บันทึกชีต)", use_container_width=True, type="primary"):
                order_id = f"TX{int(time.time())}"
                summary = ", ".join([f"{n}({i['qty']})" for n, i in st.session_state.cart.items()])
                payload = {
                    "action": "checkout",
                    "order_id": order_id, # 8. เพิ่มเลขที่ออเดอร์
                    "cart": st.session_state.cart,
                    "method": method,
                    "total": total_sum,
                    "summary": summary # 8. เพิ่มรายชื่อสินค้าลงในชีต
                }
                try:
                    # สร้าง PDF
                    st.session_state.pdf_receipt = generate_receipt_pdf(st.session_state.cart, total_sum, method, order_id)
                    # ส่งข้อมูล
                    requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=10)
                    st.success(f"บันทึกสำเร็จ! ออเดอร์: {order_id}")
                except:
                    st.error("บันทึกไม่สำเร็จ ตรวจสอบอินเทอร์เน็ต")

            if st.session_state.pdf_receipt:
                st.download_button("🖨️ ดาวน์โหลดใบเสร็จ (PDF)", data=bytes(st.session_state.pdf_receipt), file_name="receipt.pdf", use_container_width=True)

elif menu == "📊 สรุปยอดรายวัน & กำไร":
    st.title("📈 สรุปผลประกอบการ")
    df_sales = load_data(SALES_URL)
    
    if not df_sales.empty:
        # 3. สรุปยอดรายวัน
        daily_total = df_sales['Total'].sum() if 'Total' in df_sales.columns else 0
        st.metric("ยอดขายรวมทั้งหมด", f"{daily_total:,} ฿")

        # 7. สรุปยอดกำไรขาดทุนสำหรับร้านของชำ
        if 'Cost' in df_sales.columns and 'Total' in df_sales.columns:
            total_cost = df_sales['Cost'].sum()
            profit = daily_total - total_cost
            st.metric("กำไรสุทธิ", f"{profit:,} ฿", delta=f"{profit:,}")

        # 4. สถิติสินค้าขายดี
        st.subheader("🏆 5 อันดับสินค้าขายดี")
        if 'Summary' in df_sales.columns:
            st.write("วิเคราะห์จากรายการออเดอร์ล่าสุดในระบบ")
            st.dataframe(df_sales.tail(10), use_container_width=True) # แสดงรายการล่าสุด
    else:
        st.info("ยังไม่มีข้อมูลการขายในวันนี้")

elif menu == "📦 จัดการสต็อก":
    st.title("📦 ระบบจัดการสต็อก")
    # 1. หลังบ้าน (กลับมาแล้ว)
    st.dataframe(df_stock, use_container_width=True, hide_index=True)
