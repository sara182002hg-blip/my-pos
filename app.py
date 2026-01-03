import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="Ultimate POS Premium", layout="wide")

# --- CORE FUNCTIONS ---
def clean_df(df):
    """ ล้างชื่อคอลัมน์ให้เป็นมาตรฐาน (ตัวเล็กและไม่มีช่องว่าง) """
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

@st.cache_data(ttl=2)
def fetch_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData", timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            # ดึงข้อมูลแผ่น Stock และ Products มาทำความสะอาด
            stock_data = clean_df(pd.DataFrame(res_json.get('stock', [])))
            return {"stock": stock_data}
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
    return None

def send_to_sheets(payload):
    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        return res.status_code == 200
    except:
        return False

# --- SESSION STATE ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'app_data' not in st.session_state: st.session_state.app_data = fetch_data()
if 'show_receipt' not in st.session_state: st.session_state.show_receipt = False
if 'last_bill' not in st.session_state: st.session_state.last_bill = {}

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 PREMIUM POS")
    menu = st.radio("เมนูหลัก", ["🛒 ระบบขายสินค้า", "📊 รายงานยอดขาย", "📦 คลังสินค้าคงเหลือ"])
    if st.button("🔄 อัปเดตข้อมูล (Sync)", use_container_width=True):
        st.session_state.app_data = fetch_data()
        st.rerun()

# --- MAIN LOGIC ---
if st.session_state.app_data:
    df_s = st.session_state.app_data['stock']

    if menu == "🛒 ระบบขายสินค้า":
        col_main, col_cart = st.columns([2, 1])
        
        with col_main:
            st.subheader("📦 รายการสินค้าพร้อมขาย")
            search = st.text_input("🔍 ค้นหาสินค้า...", placeholder="พิมพ์ชื่อสินค้าที่นี่")
            
            # กรองสินค้า (อ้างอิงคอลัมน์ 'name' จากชีตของคุณ)
            display_df = df_s
            if search:
                display_df = df_s[df_s['name'].astype(str).str.contains(search, case=False)]

            if display_df.empty:
                st.info("ไม่พบรายการสินค้า")
            else:
                grid = st.columns(3)
                for i, (idx, row) in enumerate(display_df.iterrows()):
                    with grid[i % 3]:
                        with st.container(border=True):
                            # ดึงข้อมูลจากคอลัมน์ที่มีอยู่จริงในชีตของคุณ (name, price, stock)
                            p_name = str(row['name'])
                            p_price = float(row['price']) if 'price' in row else 0.0
                            p_stock = int(row['stock']) if 'stock' in row else 0
                            p_img = row['image_url'] if 'image_url' in row else ""

                            if p_img: st.image(p_img, use_container_width=True)
                            st.markdown(f"**{p_name}**")
                            st.markdown(f"## ฿{p_price:,.2f}")
                            st.caption(f"คงเหลือ: {p_stock} ชิ้น")

                            if st.button("➕ เพิ่มลงตะกร้า", key=f"add_{p_name}", disabled=(p_stock <= 0), use_container_width=True):
                                if p_name in st.session_state.cart:
                                    st.session_state.cart[p_name]['qty'] += 1
                                else:
                                    st.session_state.cart[p_name] = {'price': p_price, 'qty': 1}
                                st.rerun()

        with col_cart:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            for name, item in list(st.session_state.cart.items()):
                with st.container(border=True):
                    sub = item['price'] * item['qty']
                    total += sub
                    st.write(f"**{name}**")
                    c1, c2, c3 = st.columns([1,1,1])
                    if c1.button("➖", key=f"m_{name}"):
                        st.session_state.cart[name]['qty'] -= 1
                        if st.session_state.cart[name]['qty'] <= 0: del st.session_state.cart[name]
                        st.rerun()
                    c2.write(f"x{item['qty']}")
                    if c3.button("➕", key=f"p_{name}"):
                        st.session_state.cart[name]['qty'] += 1
                        st.rerun()
            
            st.divider()
            st.metric("ยอดรวมทั้งหมด", f"฿{total:,.2f}")
            method = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
                if total > 0:
                    now = datetime.now()
                    items_txt = ", ".join([f"{k}({v['qty']})" for k, v in st.session_state.cart.items()])
                    
                    # ข้อมูลลงแผ่น Sales: วันที่ | เวลา | เลขบิล | ยอดเงิน | วิธีชำระ | รายการ
                    payload = {
                        "action": "recordSale",
                        "data": [
                            now.strftime("%d/%m/%Y"),
                            now.strftime("%H:%M:%S"),
                            f"POS{int(now.timestamp())}",
                            total,
                            method,
                            items_txt
                        ],
                        # ส่งชื่อสินค้าไปตัดสต็อก (ใช้ชื่อแทน ID)
                        "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in st.session_state.cart.items()]
                    }
                    
                    if send_to_sheets(payload):
                        st.session_state.last_bill = {"total": total, "method": method, "items": st.session_state.cart.copy()}
                        st.session_state.show_receipt = True
                        st.session_state.cart = {}
                        st.session_state.app_data = fetch_data()
                        st.rerun()

    # --- RECEIPT DIALOG ---
    if st.session_state.show_receipt:
        @st.dialog("🧾 ใบเสร็จรับเงิน")
        def show_receipt():
            b = st.session_state.last_bill
            st.write(f"**ยอดรวม: ฿{b['total']:,.2f}**")
            st.write(f"ช่องทาง: {b['method']}")
            if b['method'] == "พร้อมเพย์":
                qr = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://promptpay.io/{PROMPTPAY_ID}/{b['total']}"
                st.image(qr, width=200)
            if st.button("ปิดใบเสร็จ"):
                st.session_state.show_receipt = False
                st.rerun()
        show_receipt()

    elif menu == "📊 รายงานยอดขาย":
        st.subheader("📊 ข้อมูลการขายล่าสุด")
        st.info("ระบบบันทึกข้อมูลเข้าแผ่น 'Sales' เรียบร้อยแล้ว")

    elif menu == "📦 คลังสินค้าคงเหลือ":
        st.subheader("📦 ตรวจสอบสต็อกสินค้า")
        st.dataframe(df_s, use_container_width=True, hide_index=True)
