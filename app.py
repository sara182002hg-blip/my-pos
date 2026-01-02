import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

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
    # โหลดทั้งข้อมูลสินค้าและสต็อกเพื่อเช็คจำนวนคงเหลือ
    df_p = load_data(URL_PRODUCTS)
    df_s = load_data(URL_STOCK)
    
    col_main, col_right = st.columns([2.2, 1.8])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(2) 
            for i, row in df_p.iterrows():
                # ดึงจำนวนสต็อกล่าสุดของสินค้านั้นๆ
                stock_qty = 0
                if not df_s.empty:
                    match = df_s[df_s['Name'] == row['Name']]
                    if not match.empty:
                        stock_qty = match.iloc[0]['Stock']

                with grid[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"### {row['Name']}")
                        st.markdown(f"**ราคา {row['Price']:,} ฿**")
                        st.caption(f"คงเหลือในสต็อก: {stock_qty} ชิ้น")
                        
                        # เงื่อนไขเช็คสต็อกก่อนกด (ป้องกันติดลบ)
                        cart_qty = st.session_state.cart.get(row['Name'], {}).get('qty', 0)
                        can_add = stock_qty > cart_qty
                        
                        if can_add:
                            if st.button(f"➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                                name = row['Name']
                                st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                                st.session_state.cart[name]['qty'] += 1
                                st.session_state.receipt = None 
                                st.rerun()
                        else:
                            st.button("❌ สินค้าหมด / ไม่พอ", key=f"out_{i}", use_container_width=True, disabled=True)

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จรับเงิน")
            with st.container(border=True):
                # ดีไซน์ใบเสร็จพร้อม QR Code ในตัว
                qr_html = ""
                if r['method'] == "📱 PromptPay":
                    qr_html = f"""
                    <div style="text-align: center; margin-top: 15px; border-top: 1px solid #eee; padding-top: 15px;">
                        <img src="https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png" width="250" style="border: 1px solid #ddd;"/>
                        <p style="font-size: 12px; color: #666; margin-top: 5px;">สแกนจ่ายเบอร์ {MY_PROMPTPAY}</p>
                    </div>
                    """
                
                st.markdown(f"""
                <div style="background-color: white; color: black; padding: 30px; border-radius: 10px; font-family: 'Courier New', Courier, monospace; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <h2 style="margin: 0;">TAS POS</h2>
                        <p style="font-size: 12px; color: #666;">ID: {r['id']}</p>
                    </div>
                    <div style="border-top: 2px dashed #000; border-bottom: 2px dashed #000; padding: 15px 0; margin-bottom: 15px;">
                        {''.join([f'<div style="display: flex; justify-content: space-between; margin-bottom: 5px;"><span>{n} x{i["qty"]}</span><span style="font-weight: bold;">{i["price"]*i["qty"]:,} ฿</span></div>' for n, i in r['items'].items()])}
                    </div>
                    <div style="display: flex; justify-content: space-between; font-size: 24px; font-weight: bold;">
                        <span>รวมทั้งสิ้น</span><span>{r['total']:,} ฿</span>
                    </div>
                    <p style="font-size: 14px; margin-top: 10px;">วิธีชำระ: {r['method']}</p>
                    {qr_html}
                </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                if st.button("✅ เริ่มการขายใหม่", use_container_width=True, type="primary"):
                    st.session_state.receipt = None
                    st.rerun()
        
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
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
                        # เช็คสต็อกอีกรอบก่อนเพิ่มจำนวนในตะกร้า
                        current_stock = df_s[df_s['Name'] == name].iloc[0]['Stock'] if not df_s.empty else 0
                        if item['qty'] < current_stock:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.toast(f"ขออภัย {name} ในสต็อกไม่พอแล้ว", icon="⚠️")
                        st.rerun()

                st.divider()
                st.title(f"รวม: {total_sum:,} ฿")
                pay_method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                
                if st.button("✅ ยืนยันชำระเงิน", use_container_width=True, type="primary"):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    st.session_state.receipt = {"id": bill_id, "items": dict(st.session_state.cart), "total": total_sum, "method": pay_method}
                    
                    try:
                        payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": pay_method}
                        requests.post(SCRIPT_URL, json=payload, timeout=2)
                    except: pass
                    
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.warning("ยังไม่มีข้อมูลยอดขาย")

elif menu == "📦 สต็อก":
    st.title("📦 สต็อกสินค้าคงเหลือ")
    df_stock = load_data(URL_STOCK)
    if not df_stock.empty:
        st.dataframe(df_stock, use_container_width=True)
    else:
        st.error("ไม่สามารถโหลดข้อมูลสต็อกได้")
