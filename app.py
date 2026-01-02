import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz36dYw2mJI2Nr4aqCLswtd4v4wq3AhleY_tFWfBRRSw2YwlyAzla55gclUVlHR2ulB/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Pro", layout="wide")

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
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(2) 
            for i, row in df_p.iterrows():
                with grid[i % 2]:
                    with st.container(border=True):
                        st.markdown(f"### {row['Name']}")
                        st.markdown(f"**{row['Price']:,} ฿**")
                        if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.session_state.receipt = None # ปิดใบเสร็จเก่าเมื่อเริ่มเลือกใหม่
                            st.rerun()

    with col_right:
        # กรณีที่ยังมีใบเสร็จค้างอยู่ (เพิ่งจ่ายเงินเสร็จ)
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.subheader("📄 ใบเสร็จรับเงิน")
            with st.container(border=True):
                st.markdown(f"""
                <div style="background-color: white; color: black; padding: 20px; border-radius: 5px; font-family: monospace;">
                    <h3 style="text-align: center; margin:0;">RECEIPT</h3>
                    <p style="text-align: center; font-size: 12px;">ID: {r['id']}</p>
                    <hr style="border-top: 1px dashed black;">
                    {''.join([f'<div style="display: flex; justify-content: space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,}</span></div>' for n, i in r['items'].items()])}
                    <hr style="border-top: 1px dashed black;">
                    <div style="display: flex; justify-content: space-between; font-weight: bold;">
                        <span>TOTAL</span><span>{r['total']:,} ฿</span>
                    </div>
                    <p style="font-size: 12px; margin-top: 10px;">Payment: {r['method']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if r['method'] == "📱 PromptPay":
                    st.image(f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png", caption="สแกนจ่าย 0945016189", width=200)
                
                st.info("💡 กด Ctrl+P เพื่อบันทึกเป็น PDF")
                if st.button("✅ เริ่มการขายใหม่", use_container_width=True, type="primary"):
                    st.session_state.receipt = None
                    st.rerun()
        
        # กรณีแสดงตะกร้าปกติ
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            if not st.session_state.cart:
                st.write("ยังไม่มีสินค้าในตะกร้า")
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
