import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- 1. ตั้งค่าลิงก์ข้อมูล (CSV) ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# ลิงก์ Apps Script ของคุณ
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz36dYw2mJI2Nr4aqCLswtd4v4wq3AhleY_tFWfBRRSw2YwlyAzla55gclUVlHR2ulB/exec"
MY_PROMPTPAY = "0945016189"

st.set_page_config(page_title="TAS POS v2", layout="wide")

def load_data(url):
    try:
        # บังคับรีเฟรชข้อมูลด้วย timestamp
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        # กรองเฉพาะแถวที่มีข้อมูลสินค้าจริง
        return df.dropna(subset=['Name']).reset_index(drop=True)
    except:
        return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("ระบบจัดการ", ["🛒 ขายสินค้า", "📊 ยอดขาย", "📦 สต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data(URL_PRODUCTS)
    col_main, col_cart = st.columns([2.5, 1.5])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3) 
            for i, row in df_p.iterrows():
                with grid[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"### {row['Name']}")
                        st.markdown(f"**ราคา: {row['Price']:,} ฿**")
                        if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
        else:
            st.info("💡 กำลังดึงข้อมูลสินค้า...")

    with col_cart:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.button("🗑️ เคลียร์ตะกร้า", key="clear_all", use_container_width=True):
            st.session_state.cart = {}
            st.rerun()
            
        total_sum = 0
        for name, item in list(st.session_state.cart.items()):
            subtotal = item['price'] * item['qty']
            total_sum += subtotal
            c1, c2, c3 = st.columns([2, 1, 1])
            c1.write(f"**{name}**\n{subtotal:,} ฿")
            if c2.button("➖", key=f"min_{name}"):
                st.session_state.cart[name]['qty'] -= 1
                if st.session_state.cart[name]['qty'] <= 0: del st.session_state.cart[name]
                st.rerun()
            if c3.button("➕", key=f"plus_{name}"):
                st.session_state.cart[name]['qty'] += 1
                st.rerun()

        if st.session_state.cart:
            st.divider()
            st.title(f"รวม: {total_sum:,} ฿")
            pay_method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
            
            if st.button("✅ ยืนยันและออกใบเสร็จ", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                
                payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": pay_method}
                
                try:
                    # ส่งข้อมูลไปบันทึก
                    response = requests.post(SCRIPT_URL, json=payload, timeout=20)
                    if response.status_code == 200:
                        st.session_state.receipt = {"id": bill_id, "items": dict(st.session_state.cart), "total": total_sum, "method": pay_method}
                        st.session_state.cart = {}
                        st.success("บันทึกยอดขายสำเร็จ!")
                        st.rerun()
                    else:
                        st.error("⚠️ บันทึกข้อมูลไม่สำเร็จ กรุณาลองอีกครั้ง")
                except:
                    st.error("❌ การเชื่อมต่อล้มเหลว (ตรวจสอบลิงก์ Apps Script)")

    if st.session_state.receipt:
        with st.expander("📄 ใบเสร็จรับเงิน", expanded=True):
            r = st.session_state.receipt
            st.markdown(f"<div style='text-align: center;'><h3>ใบเสร็จ #{r['id']}</h3></div>", unsafe_allow_html=True)
            for n, i in r['items'].items():
                st.write(f"• {n} x{i['qty']} : {i['price']*i['qty']:,} ฿")
            st.divider()
            st.subheader(f"รวมทั้งสิ้น: {r['total']:,} ฿")
            
            if r['method'] == "📱 PromptPay":
                # สร้าง QR Code อัตโนมัติจากยอดเงิน
                st.image(f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png", width=250)
                st.caption(f"เบอร์พร้อมเพย์: {MY_PROMPTPAY}")
            
            if st.button("ปิดใบเสร็จ"): 
                st.session_state.receipt = None
                st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        # แสดงรายการล่าสุดขึ้นก่อน
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.warning("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อก":
    st.title("📦 สต็อกสินค้าคงเหลือ")
    df_stock = load_data(URL_STOCK)
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
