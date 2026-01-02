import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbz36dYw2mJI2Nr4aqCLswtd4v4wq3AhleY_tFWfBRRSw2YwlyAzla55gclUVlHR2ulB/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Receipt System", layout="wide")

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

menu = st.sidebar.radio("เมนูระบบ", ["🛒 ขายสินค้า", "📊 ยอดขาย"])

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
                        st.markdown(f"**{row['Price']:,} ฿**")
                        if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                            name = row['Name']
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()

    with col_cart:
        st.subheader("🛒 ตะกร้าสินค้า")
        total_sum = 0
        for name, item in list(st.session_state.cart.items()):
            subtotal = item['price'] * item['qty']
            total_sum += subtotal
            st.write(f"**{name}** x{item['qty']} = {subtotal:,} ฿")
        
        if st.session_state.cart:
            st.divider()
            st.title(f"รวม: {total_sum:,} ฿")
            pay_method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
            
            if st.button("✅ ยืนยันและออกใบเสร็จ", use_container_width=True, type="primary"):
                bill_id = f"B{int(time.time())}"
                summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                
                # เก็บข้อมูลลง Receipt State ทันทีเพื่อให้ QR ขึ้นแน่นอน
                st.session_state.receipt = {
                    "id": bill_id, "items": dict(st.session_state.cart), 
                    "total": total_sum, "method": pay_method, "time": time.ctime()
                }
                
                # พยายามส่งข้อมูลไป Sheets (เบื้องหลัง)
                try:
                    payload = {"action": "checkout", "bill_id": bill_id, "summary": summary, "total": total_sum, "method": pay_method}
                    requests.post(SCRIPT_URL, json=payload, timeout=2)
                except: pass 
                
                st.session_state.cart = {}
                st.rerun()

    # --- ส่วนใบเสร็จสำหรับสั่ง Print ---
    if st.session_state.receipt:
        r = st.session_state.receipt
        st.divider()
        # ใช้สไตล์ CSS เพื่อให้หน้าใบเสร็จดูเหมือนกระดาษ
        st.markdown(f"""
        <div style="background-color: white; color: black; padding: 30px; border: 1px solid #ddd; border-radius: 10px; font-family: 'Courier New', Courier, monospace; max-width: 500px; margin: auto;">
            <h2 style="text-align: center;">ใบเสร็จรับเงิน</h2>
            <p style="text-align: center;">ID: {r['id']}<br>วันที่: {r['time']}</p>
            <hr>
            {''.join([f'<p>{n} x{i["qty"]} <span style="float: right;">{i["price"]*i["qty"]:,} ฿</span></p>' for n, i in r['items'].items()])}
            <hr>
            <h3 style="text-align: right;">ยอดรวมสุทธิ: {r['total']:,} ฿</h3>
            <p>ชำระด้วย: {r['method']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # แสดง QR Code ทันทีถ้าเลือก PromptPay
        if r['method'] == "📱 PromptPay":
            qr_url = f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png"
            st.image(qr_url, caption="สแกนเพื่อชำระเงิน (0945016189)", width=250)

        c1, c2 = st.columns(2)
        with c1:
            st.info("💡 เคล็ดลับ: กด Ctrl + P เพื่อบันทึกเป็น PDF หรือสั่งปริ้น")
        with c2:
            if st.button("❌ ปิดและเริ่มการขายใหม่", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()

elif menu == "📊 ยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data(URL_SALES)
    if not df_sales.empty:
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")
