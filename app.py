import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"
PROMPTPAY_ID = "0945016189" # เบอร์พร้อมเพย์ที่คุณระบุ

st.set_page_config(page_title="Premium POS System", layout="wide")

# --- CORE FUNCTIONS ---
def fix_columns(df):
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

@st.cache_data(ttl=5)
def fetch_all_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData", timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            return {
                "products": fix_columns(pd.DataFrame(res_json.get('products', []))),
                "stock": fix_columns(pd.DataFrame(res_json.get('stock', [])))
            }
    except Exception as e:
        st.error(f"Error fetching data: {e}")
    return None

def send_to_sheet(payload):
    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        return res.status_code == 200
    except:
        return False

# --- SESSION STATE ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'app_data' not in st.session_state: st.session_state.app_data = fetch_all_data()
if 'show_receipt' not in st.session_state: st.session_state.show_receipt = False
if 'last_bill' not in st.session_state: st.session_state.last_bill = {}

# --- SIDEBAR ---
with st.sidebar:
    st.title("💎 PREMIUM POS")
    menu = st.radio("เมนูหลัก", ["🛒 รายการขาย", "📊 รายงานยอดขาย", "📦 สต็อกออนไลน์"])
    if st.button("🔄 Sync ข้อมูลใหม่"):
        st.session_state.app_data = fetch_all_data()
        st.rerun()

# --- MAIN CONTENT ---
if st.session_state.app_data:
    df_prods = st.session_state.app_data['products']
    df_stock = st.session_state.app_data['stock']

    if menu == "🛒 รายการขาย":
        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader("📦 สินค้า")
            search = st.text_input("ค้นหาสินค้า...", placeholder="พิมพ์ชื่อสินค้า")
            filtered_prods = df_prods[df_prods['name'].str.contains(search, case=False)] if search else df_prods
            
            p_cols = st.columns(3)
            for i, (idx, row) in enumerate(filtered_prods.iterrows()):
                with p_cols[i % 3]:
                    with st.container(border=True):
                        p_id = str(row['id'])
                        s_row = df_stock[df_stock['id'].astype(str) == p_id]
                        qty = int(s_row['qty'].values[0]) if not s_row.empty else 0
                        
                        st.write(f"**{row['name']}**")
                        st.write(f"### ฿{float(row['price']):,.2f}")
                        st.caption(f"คงเหลือ: {qty}")
                        
                        if st.button("➕ เพิ่ม", key=f"add_{p_id}", disabled=(qty <= 0)):
                            if p_id in st.session_state.cart:
                                st.session_state.cart[p_id]['qty'] += 1
                            else:
                                st.session_state.cart[p_id] = {'name': row['name'], 'price': float(row['price']), 'qty': 1}
                            st.rerun()

        with col2:
            st.subheader("🛒 ตะกร้า")
            total = 0
            for p_id, item in list(st.session_state.cart.items()):
                with st.container(border=True):
                    sub = item['price'] * item['qty']
                    total += sub
                    st.write(f"**{item['name']}**")
                    c1, c2, c3 = st.columns([1,1,1])
                    if c1.button("➖", key=f"m_{p_id}"):
                        st.session_state.cart[p_id]['qty'] -= 1
                        if st.session_state.cart[p_id]['qty'] <= 0: del st.session_state.cart[p_id]
                        st.rerun()
                    c2.write(f"x{item['qty']}")
                    if c3.button("➕", key=f"p_{p_id}"):
                        st.session_state.cart[p_id]['qty'] += 1
                        st.rerun()
            
            st.divider()
            st.metric("รวมทั้งสิ้น", f"฿{total:,.2f}")
            method = st.radio("ช่องทางชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย & ออกใบเสร็จ", type="primary", use_container_width=True):
                if total > 0:
                    bill_data = {
                        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                        "items": json.dumps(st.session_state.cart, ensure_ascii=False),
                        "total": total,
                        "method": method
                    }
                    payload = {
                        "action": "recordSale",
                        "data": bill_data,
                        "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in st.session_state.cart.items()]
                    }
                    if send_to_sheet(payload):
                        st.session_state.last_bill = bill_data
                        st.session_state.show_receipt = True
                        st.session_state.cart = {}
                        st.session_state.app_data = fetch_all_data()
                        st.rerun()

    # --- 📄 RECEIPT DIALOG WITH AUTO-PRINT & QR ---
    if st.session_state.show_receipt:
        @st.dialog("🧾 ใบเสร็จรับเงิน")
        def show_receipt_dialog():
            bill = st.session_state.last_bill
            items = json.loads(bill['items'])
            
            # ส่วนการแสดงผลในหน้าจอ
            st.markdown(f"**วันที่:** {bill['timestamp']}")
            st.markdown(f"**ช่องทางชำระ:** {bill['method']}")
            st.write("---")
            for k, v in items.items():
                st.write(f"{v['name']} x{v['qty']} : ฿{v['price']*v['qty']:,.2f}")
            st.write("---")
            st.subheader(f"ยอดรวม: ฿{bill['total']:,.2f}")

            # แสดง QR Code เฉพาะเมื่อจ่ายแบบ "พร้อมเพย์"
            if bill['method'] == "พร้อมเพย์":
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=https://promptpay.io/{PROMPTPAY_ID}/{bill['total']}"
                st.image(qr_url, caption=f"สแกนจ่ายเบอร์ {PROMPTPAY_ID}")

            # ปุ่มสั่งปริ้นใบเสร็จ
            if st.button("🖨️ สั่งปริ้นใบเสร็จ (Print)", use_container_width=True):
                st.markdown("""<script>window.print();</script>""", unsafe_allow_html=True)
            
            if st.button("เสร็จสิ้น (Close)", use_container_width=True):
                st.session_state.show_receipt = False
                st.rerun()
        
        show_receipt_dialog()

    elif menu == "📊 รายงานยอดขาย":
        st.subheader("📊 วิเคราะห์ยอดขาย")
        st.info("บันทึกข้อมูลเข้าแผ่น Sales เรียบร้อยตามลำดับคอลัมน์")

    elif menu == "📦 สต็อกออนไลน์":
        st.subheader("📦 ตรวจสอบสต็อกสินค้า")
        st.dataframe(df_stock, use_container_width=True, hide_index=True)
