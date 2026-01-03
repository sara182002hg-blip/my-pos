import streamlit as st
import requests
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="Ultimate POS Premium", layout="wide")

# --- CORE FUNCTIONS: ป้องกัน KeyError 100% ---
def clean_dataframe(df):
    """ ปรับแต่ง DataFrame ให้มาตรฐาน (ลบช่องว่าง, ตัวพิมพ์เล็ก) ป้องกันสินค้าไม่ขึ้น """
    if df is not None and not df.empty:
        # ล้างหัวตาราง: จาก " ID " หรือ "id" ให้กลายเป็น "id" ทั้งหมด
        df.columns = [str(c).strip().lower() for c in df.columns]
        # ล้างข้อมูลในคอลัมน์ที่เป็น String
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].astype(str).str.strip()
    return df

@st.cache_data(ttl=2)
def fetch_pos_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData", timeout=15)
        if response.status_code == 200:
            res_json = response.json()
            return {
                "products": clean_dataframe(pd.DataFrame(res_json.get('products', []))),
                "stock": clean_dataframe(pd.DataFrame(res_json.get('stock', [])))
            }
    except Exception as e:
        st.error(f"❌ เชื่อมต่อข้อมูลไม่ได้: {e}")
    return None

def record_sale_to_sheets(payload):
    try:
        res = requests.post(API_URL, json=payload, timeout=20)
        return res.status_code == 200
    except:
        return False

# --- SESSION STATE MANAGEMENT ---
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'app_data' not in st.session_state: st.session_state.app_data = fetch_pos_data()
if 'show_receipt' not in st.session_state: st.session_state.show_receipt = False
if 'last_bill' not in st.session_state: st.session_state.last_bill = {}

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("💎 PREMIUM POS")
    st.markdown("---")
    menu = st.radio("เมนูการทำงาน", ["🛒 ระบบการขายสินค้า", "📊 รายงานสรุปยอด", "📦 เช็คสต็อกสินค้า"])
    st.markdown("---")
    if st.button("🔄 รีเฟรชสินค้า (Sync)", use_container_width=True):
        st.session_state.app_data = fetch_pos_data()
        st.rerun()

# --- MAIN INTERFACE ---
if st.session_state.app_data is None:
    st.error("🚨 ไม่พบข้อมูลสินค้าในระบบ กรุณาตรวจสอบ Google Sheets หรือกดรีเฟรช")
else:
    df_prods = st.session_state.app_data['products']
    df_stock = st.session_state.app_data['stock']

    # --- PAGE: SALES SYSTEM ---
    if menu == "🛒 ระบบการขายสินค้า":
        col_main, col_cart = st.columns([2, 1])

        with col_main:
            st.subheader("📦 เลือกรายการสินค้า")
            search = st.text_input("🔍 ค้นหา...", placeholder="พิมพ์ชื่อสินค้าที่ต้องการ")
            
            # กรองสินค้า
            display_df = df_prods
            if search:
                display_df = df_prods[df_prods['name'].str.contains(search, case=False)]

            if display_df.empty:
                st.info("ไม่พบรายการสินค้า")
            else:
                p_grid = st.columns(3)
                for i, (idx, row) in enumerate(display_df.iterrows()):
                    with p_grid[i % 3]:
                        with st.container(border=True):
                            # ดึง ID และเช็คสต็อกแบบปลอดภัย
                            try:
                                pid = str(row['id'])
                                p_name = row['name']
                                p_price = float(row['price'])
                                
                                # หาสต็อกที่ตรงกัน
                                s_match = df_stock[df_stock['id'] == pid]
                                current_stock = int(s_match['qty'].values[0]) if not s_match.empty else 0
                                
                                st.markdown(f"**{p_name}**")
                                st.markdown(f"## ฿{p_price:,.2f}")
                                
                                if current_stock <= 0:
                                    st.error("สินค้าหมด")
                                    btn_status = True
                                else:
                                    st.caption(f"คงเหลือ: {current_stock}")
                                    btn_status = False

                                if st.button("➕ เพิ่ม", key=f"add_{pid}", disabled=btn_status, use_container_width=True):
                                    if pid in st.session_state.cart:
                                        st.session_state.cart[pid]['qty'] += 1
                                    else:
                                        st.session_state.cart[pid] = {'name': p_name, 'price': p_price, 'qty': 1}
                                    st.rerun()
                            except KeyError as e:
                                st.warning(f"ข้อมูลคอลัมน์ {e} ไม่สมบูรณ์")

        with col_cart:
            st.subheader("🛒 ตะกร้าสินค้า")
            total_amt = 0
            if not st.session_state.cart:
                st.write("ยังไม่มีสินค้า")
            else:
                for pid, item in list(st.session_state.cart.items()):
                    with st.container(border=True):
                        sub = item['price'] * item['qty']
                        total_amt += sub
                        st.write(f"**{item['name']}**")
                        c1, c2, c3 = st.columns([1,1,1])
                        if c1.button("➖", key=f"m_{pid}"):
                            st.session_state.cart[pid]['qty'] -= 1
                            if st.session_state.cart[pid]['qty'] <= 0: del st.session_state.cart[pid]
                            st.rerun()
                        c2.write(f"x{item['qty']}")
                        if c3.button("➕", key=f"p_{pid}"):
                            st.session_state.cart[pid]['qty'] += 1
                            st.rerun()
                
                st.divider()
                st.metric("ยอดชำระ", f"฿{total_amt:,.2f}")
                pay_type = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if st.button("✅ ยืนยันการสั่งซื้อ", type="primary", use_container_width=True):
                    if total_amt > 0:
                        now = datetime.now()
                        # สรุปสินค้าให้เป็นบรรทัดเดียวป้องกันการเลื่อนคอลัมน์ใน Sheet
                        summary = ", ".join([f"{v['name']}({v['qty']})" for v in st.session_state.cart.values()])
                        
                        # ลำดับข้อมูล: วันที่ | เวลา | เลขบิล | ยอดเงิน | วิธีชำระเงิน | รายการสินค้า
                        sale_payload = [
                            now.strftime("%d/%m/%Y"),
                            now.strftime("%H:%M:%S"),
                            f"POS{int(now.timestamp())}",
                            total_amt,
                            pay_type,
                            summary
                        ]

                        final_data = {
                            "action": "recordSale",
                            "data": sale_payload,
                            "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in st.session_state.cart.items()]
                        }

                        if record_sale_to_sheets(final_data):
                            st.session_state.last_bill = {
                                "no": sale_payload[2], "date": sale_payload[0], "time": sale_payload[1],
                                "total": total_amt, "type": pay_type, "items": st.session_state.cart.copy()
                            }
                            st.session_state.show_receipt = True
                            st.session_state.cart = {}
                            st.session_state.app_data = fetch_pos_data()
                            st.rerun()

    # --- 📄 RECEIPT DIALOG (ใบเสร็จ & QR Code) ---
    if st.session_state.show_receipt:
        @st.dialog("🧾 รายละเอียดใบเสร็จ")
        def show_receipt():
            b = st.session_state.last_bill
            st.write(f"**เลขที่:** {b['no']} | **วันที่:** {b['date']} {b['time']}")
            st.divider()
            for pid, item in b['items'].items():
                st.write(f"{item['name']} x{item['qty']} = ฿{item['price']*item['qty']:,.2f}")
            st.divider()
            st.subheader(f"รวมทั้งสิ้น: ฿{b['total']:,.2f}")
            st.write(f"การชำระเงิน: {b['type']}")

            if b['type'] == "พร้อมเพย์":
                qr = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=https://promptpay.io/{PROMPTPAY_ID}/{b['total']}"
                st.image(qr, caption="สแกนเพื่อชำระเงิน", width=200)

            if st.button("🖨️ ปริ้นใบเสร็จ", use_container_width=True):
                st.markdown("<script>window.print();</script>", unsafe_allow_html=True)
            if st.button("ปิดหน้าต่าง", use_container_width=True):
                st.session_state.show_receipt = False
                st.rerun()
        show_receipt()

    # --- PAGE: REPORT & STOCK ---
    elif menu == "📊 รายงานสรุปยอด":
        st.subheader("📊 ข้อมูลยอดขายล่าสุด")
        st.info("ระบบจะบันทึกข้อมูลเรียงคอลัมน์: วันที่, เวลา, เลขบิล, ยอดเงิน, วิธีชำระ, รายการสินค้า")
        st.write("ตรวจสอบข้อมูลเพิ่มเติมได้ที่ Google Sheets แผ่น 'Sales'")

    elif menu == "📦 เช็คสต็อกสินค้า":
        st.subheader("📦 รายการสต็อกสินค้าคงเหลือปัจจุบัน")
        st.dataframe(df_stock, use_container_width=True, hide_index=True)
