import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- 1. ตั้งค่าลิงก์ข้อมูล (ดึงจาก Google Sheets ของคุณ) ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

# ✅ ลิงก์ Apps Script ล่าสุดที่คุณส่งมา
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzFd4Q3VTiqyhFhiI0Atu6Hu-ZZQ_0tP3PgE6jej9Q3igT2LtBV4g9te0Fw-hV0F9M/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Professional", layout="wide")

def load_data(url):
    try:
        res = requests.get(f"{url}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(subset=['Name']).reset_index(drop=True)
    except:
        return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า", "📊 ยอดขาย", "📦 สต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data(URL_PRODUCTS)
    col_main, col_right = st.columns([2.2, 1.8])
    
    with col_main:
        st.subheader("📦 เลือกรายการสินค้า")
        if not df_p.empty:
            grid = st.columns(2) 
            for i, row in df_p.iterrows():
                with grid[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"### {row['Name']}")
                        st.markdown(f"**ราคา {row['Price']:,} ฿**")
                        if st.button(f"➕ เพิ่มลงตะกร้า", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.session_state.receipt = None 
                            st.rerun()

    with col_right:
        # --- ส่วนแสดงใบเสร็จดีไซน์ใหม่ ---
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จรับเงิน")
            with st.container(border=True):
                st.markdown(f"""
                <div style="background-color: white; color: black; padding: 25px; border-radius: 10px; font-family: 'Courier New', Courier, monospace; border: 1px solid #eee;">
                    <div style="text-align: center; margin-bottom: 15px;">
                        <h2 style="margin: 0;">TAS POS</h2>
                        <p style="font-size: 12px; color: #555;">ID: {r['id']}</p>
                    </div>
                    <div style="border-top: 2px dashed #000; padding: 10px 0;">
                        {''.join([f'<div style="display: flex; justify-content: space-between; margin-bottom: 5px;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n, i in r['items'].items()])}
                    </div>
                    <div style="border-top: 2px dashed #000; padding-top: 10px; display: flex; justify-content: space-between; font-size: 22px; font-weight: bold;">
                        <span>รวมทั้งสิ้น</span><span>{r['total']:,} ฿</span>
                    </div>
                    <p style="font-size: 12px; margin-top: 10px;">วิธีชำระ: {r['method']}</p>
                    <div style="text-align: center; margin-top: 20px;">
                        {"<img src='https://promptpay.io/" + MY_PROMPTPAY + "/" + str(r['total']) + ".png' width='220' style='border: 1px solid #ddd;'/>" if r['method'] == "📱 PromptPay" else ""}
                        <p style="font-size: 11px; margin-top: 8px; color: #888;">0945016189</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.info("💡 เคล็ดลับ: กด Ctrl + P เพื่อบันทึกเป็น PDF")
                if st.button("✅ เสร็จสิ้น / เริ่มการขายใหม่", use_container_width=True, type="primary"):
                    st.session_state.receipt = None
                    st.rerun()
        
        # --- ส่วนแสดงตะกร้าสินค้า ---
        else:
            st.subheader("🛒 รายการในตะกร้า")
            if not st.session_state.cart:
                st.write("ยังไม่มีสินค้า...")
            else:
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

                st.divider()
                st.title(f"ยอดรวม: {total_sum:,} ฿")
                pay_method = st.radio("ช่องทางการชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                
                if st.button("🚀 ยืนยันชำระเงินและออกใบเสร็จ", use_container_width=True, type="primary"):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    
                    # บันทึกสถานะใบเสร็จ
                    st.session_state.receipt = {"id": bill_id, "items": dict(st.session_state.cart), "total": total_sum, "method": pay_method}
                    
                    # ส่งข้อมูลไปบันทึกยอดและตัดสต็อก
                    try:
                        payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": pay_method}
                        requests.post(SCRIPT_URL, json=payload, timeout=5)
                    except: pass
                    
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 สรุปยอดขายประจำวัน")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.info("รอข้อมูลยอดขายใหม่...")

elif menu == "📦 สต็อก":
    st.title("📦 เช็คสต็อกสินค้าคงเหลือ")
    df_stock = load_data(URL_STOCK)
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
    else:
        st.error("ไม่สามารถดึงสต็อกได้")
