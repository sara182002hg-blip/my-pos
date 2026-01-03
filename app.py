import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURATION (ตั้งค่าเบอร์และ URL) ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="Ultimate POS Premium", layout="wide", initial_sidebar_state="expanded")

# --- CORE FUNCTIONS ---
def normalize_columns(df):
    """ ป้องกัน KeyError โดยการล้างชื่อคอลัมน์ให้เป็นตัวเล็กและไม่มีช่องว่างอัตโนมัติ """
    if df is not None and not df.empty:
        df.columns = [str(c).strip().lower() for c in df.columns]
    return df

@st.cache_data(ttl=2) # รีเฟรชข้อมูลทุก 2 วินาทีเพื่อให้สต็อกสดใหม่เสมอ
def fetch_all_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData", timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            # ดึงและล้างคอลัมน์ทันที
            prods = normalize_columns(pd.DataFrame(res_json.get('products', [])))
            stock = normalize_columns(pd.DataFrame(res_json.get('stock', [])))
            return {"products": prods, "stock": stock}
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
    return None

def send_transaction(payload):
    """ ส่งข้อมูลการขายไปที่ Google Sheets """
    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        return res.status_code == 200
    except:
        return False

# --- INITIALIZE SESSION STATE ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'app_data' not in st.session_state: st.session_state.app_data = fetch_all_data()
if 'show_receipt' not in st.session_state: st.session_state.show_receipt = False
if 'last_bill' not in st.session_state: st.session_state.last_bill = {}

# --- SIDEBAR (เมนูหลัก) ---
with st.sidebar:
    st.title("💎 PREMIUM POS")
    st.markdown("---")
    menu = st.radio("เลือกเมนูการใช้งาน", ["🛒 ระบบการขายสินค้า", "📊 รายงานสรุปยอดขาย", "📦 ตรวจสอบสต็อกออนไลน์"])
    st.markdown("---")
    if st.button("🔄 อัปเดตข้อมูล (Sync)", use_container_width=True):
        st.session_state.app_data = fetch_all_data()
        st.rerun()

# --- MAIN LOGIC ---
if st.session_state.app_data is None:
    st.warning("⚠️ ไม่สามารถโหลดสินค้าได้ กรุณากดปุ่ม Sync ข้อมูลอีกครั้ง")
else:
    df_p = st.session_state.app_data['products']
    df_s = st.session_state.app_data['stock']

    # --- 🛒 PAGE: SALES SYSTEM ---
    if menu == "🛒 ระบบการขายสินค้า":
        col_list, col_cart = st.columns([2, 1])

        with col_list:
            st.subheader("📦 รายการสินค้า")
            search = st.text_input("🔍 ค้นหาชื่อสินค้า...", placeholder="พิมพ์เพื่อค้นหา")
            
            # กรองสินค้า
            filtered = df_p[df_p['name'].str.contains(search, case=False)] if search else df_p
            
            if filtered.empty:
                st.info("ไม่พบรายการสินค้าที่ค้นหา")
            else:
                # แสดงผลแบบ Grid 3 คอลัมน์
                grid_cols = st.columns(3)
                for i, (idx, row) in enumerate(filtered.iterrows()):
                    with grid_cols[i % 3]:
                        with st.container(border=True):
                            p_id = str(row['id']).strip()
                            # ค้นหาสต็อกปัจจุบัน
                            s_row = df_s[df_s['id'].astype(str).str.strip() == p_id]
                            qty_left = int(s_row['qty'].values[0]) if not s_row.empty else 0
                            
                            st.markdown(f"**{row['name']}**")
                            st.markdown(f"### ฿{float(row['price']):,.2f}")
                            
                            if qty_left <= 0:
                                st.error("❌ สินค้าหมด")
                            elif qty_left <= 5:
                                st.warning(f"⚠️ เหลือเพียง {qty_left}")
                            else:
                                st.caption(f"คงเหลือ: {qty_left}")

                            if st.button("➕ เพิ่มสินค้า", key=f"add_{p_id}", disabled=(qty_left <= 0), use_container_width=True):
                                if p_id in st.session_state.cart:
                                    st.session_state.cart[p_id]['qty'] += 1
                                else:
                                    st.session_state.cart[p_id] = {'name': row['name'], 'price': float(row['price']), 'qty': 1}
                                st.rerun()

        with col_cart:
            st.subheader("🛒 ตะกร้าสินค้า")
            total_price = 0
            if not st.session_state.cart:
                st.write("ยังไม่มีสินค้าในตะกร้า")
            else:
                for p_id, item in list(st.session_state.cart.items()):
                    with st.container(border=True):
                        sub = item['price'] * item['qty']
                        total_price += sub
                        st.write(f"**{item['name']}**")
                        c1, c2, c3 = st.columns([1,1,2])
                        if c1.button("➖", key=f"sub_{p_id}"):
                            st.session_state.cart[p_id]['qty'] -= 1
                            if st.session_state.cart[p_id]['qty'] <= 0: del st.session_state.cart[p_id]
                            st.rerun()
                        c2.write(f"x{item['qty']}")
                        if c3.button("➕", key=f"plus_{p_id}"):
                            st.session_state.cart[p_id]['qty'] += 1
                            st.rerun()
                
                st.divider()
                st.metric("ยอดรวมทั้งสิ้น", f"฿{total_price:,.2f}")
                method = st.radio("เลือกวิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("🔥 ยืนยันการขาย & ตัดสต็อก", type="primary", use_container_width=True):
                    if total_price > 0:
                        now = datetime.now()
                        # สรุปรายการสินค้าเป็นข้อความเดียว (กันลงผิดคอลัมน์)
                        items_str = ", ".join([f"{v['name']}({v['qty']})" for v in st.session_state.cart.values()])
                        
                        # ข้อมูลที่จะลงใน Sheet (เรียงตามหัวตาราง: วันที่, เวลา, เลขบิล, ยอดเงิน, วิธีชำระเงิน, รายการสินค้า)
                        sale_data = [
                            now.strftime("%d/%m/%Y"), # วันที่
                            now.strftime("%H:%M:%S"), # เวลา
                            f"POS{int(now.timestamp())}", # เลขบิล
                            total_price, # ยอดเงิน
                            method, # วิธีชำระเงิน
                            items_str # รายการสินค้า
                        ]

                        payload = {
                            "action": "recordSale",
                            "data": sale_data,
                            "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in st.session_state.cart.items()]
                        }

                        if send_transaction(payload):
                            st.session_state.last_bill = {
                                "bill_no": sale_data[2],
                                "date": sale_data[0],
                                "total": total_price,
                                "method": method,
                                "items": st.session_state.cart.copy()
                            }
                            st.session_state.show_receipt = True
                            st.session_state.cart = {} # ล้างตะกร้า
                            st.session_state.app_data = fetch_all_data() # รีเฟรชสต็อกทันที
                            st.rerun()

    # --- 📄 POP-UP RECEIPT (ระบบใบเสร็จ) ---
    if st.session_state.show_receipt:
        @st.dialog("🧾 ใบเสร็จรับเงิน (Electronic Receipt)")
        def show_receipt_dialog():
            b = st.session_state.last_bill
            st.markdown(f"**เลขที่บิล:** {b['bill_no']} | **วันที่:** {b['date']}")
            st.write("---")
            for k, v in b['items'].items():
                st.write(f"{v['name']} x{v['qty']} : ฿{v['price']*v['qty']:,.2f}")
            st.write("---")
            st.subheader(f"รวมสุทธิ: ฿{b['total']:,.2f}")
            st.write(f"การชำระ: {b['method']}")

            if b['method'] == "พร้อมเพย์":
                # สร้าง QR Code พร้อมเพย์ตามยอดเงินจริง
                qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://promptpay.io/{PROMPTPAY_ID}/{b['total']}"
                st.image(qr_url, caption=f"สแกนจ่ายเบอร์ {PROMPTPAY_ID}", width=200)

            st.markdown("---")
            if st.button("🖨️ สั่งปริ้นใบเสร็จ (Print)", use_container_width=True):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if st.button("ปิดหน้าต่าง (Close)", use_container_width=True):
                st.session_state.show_receipt = False
                st.rerun()
        show_receipt_dialog()

    # --- 📊 PAGE: REPORT ---
    elif menu == "📊 รายงานสรุปยอดขาย":
        st.subheader("📊 วิเคราะห์ข้อมูลการขาย")
        st.info("ข้อมูลถูกบันทึกเรียงตามคอลัมน์: วันที่ | เวลา | เลขที่บิล | ยอดเงิน | วิธีชำระเงิน | รายการสินค้า")
        # ตรงนี้สามารถดึงข้อมูลแผ่น Sales มาแสดงเป็นตารางสรุปได้
        st.write("ระบบซิงค์ข้อมูลล่าสุดจาก Google Sheets เรียบร้อยแล้ว")

    # --- 📦 PAGE: STOCK ---
    elif menu == "📦 ตรวจสอบสต็อกออนไลน์":
        st.subheader("📦 รายการสต็อกสินค้าคงเหลือ")
        st.dataframe(df_s, use_container_width=True, hide_index=True)
