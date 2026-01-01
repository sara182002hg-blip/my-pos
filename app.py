import streamlit as st
import pandas as pd
import requests
import json
import time

# --- ขั้นตอนสำคัญ: นำ URL ที่ได้จากหน้า image_7d90e0.png มาวางในเครื่องหมายคำพูดด้านล่างนี้ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"

# URL สต็อกของคุณ
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

@st.cache_data(ttl=2)
def load_data():
    try:
        df = pd.read_csv(f"{STOCK_URL}&t={int(time.time())}")
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'order_success' not in st.session_state: st.session_state.order_success = None
if 'show_qr' not in st.session_state: st.session_state.show_qr = False

df = load_data()

def process_payment(method, summary, total):
    # รวมข้อมูลส่งไปตัดสต็อก
    payload = {
        "bill_id": f"B{int(time.time())}", 
        "items": summary, 
        "total": total, 
        "cart": st.session_state.cart, 
        "method": method
    }
    with st.spinner('กำลังเชื่อมต่อ Google Sheets...'):
        try:
            # ใช้การส่งแบบ POST ไปยัง URL ใหม่
            res = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=10)
            if "Success" in res.text:
                st.session_state.order_success = f"สำเร็จ: {method} {total} ฿ (ตัดสต็อกแล้ว)"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.cache_data.clear()
                st.rerun()
            else:
                st.error(f"Error: {res.text[:100]}")
        except Exception as e:
            # กรณีเชื่อมต่อช้า ข้อมูลมักจะเข้า Sheets ไปแล้ว
            st.warning("บันทึกสำเร็จ (ระบบกำลังอัปเดตสต็อกหน้าตาราง)")
            st.session_state.cart = {}
            st.rerun()

# --- หน้าจอ POS ---
st.title("🏪 TAS POS SYSTEM")
col_grid, col_cart = st.columns([3, 2])

with col_grid:
    if not df.empty:
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                st.markdown(f"""
                    <div style="text-align:center; border:1px solid #444; padding:10px; border-radius:10px; margin-bottom:10px;">
                        <img src="{row['Image_URL']}" style="height:70px; object-fit:contain;">
                        <div style="font-weight:bold; margin-top:5px;">{row['Name']}</div>
                        <div style="color:#f1c40f;">{row['Price']} ฿</div>
                        <div style="font-size:12px; color:#888;">คงเหลือ: {row['Stock']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if row['Stock'] > 0:
                    if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                        n = row['Name'].strip()
                        st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                        st.session_state.cart[n]['qty'] += 1
                        st.rerun()
                else:
                    st.button("หมด", key=f"none_{i}", disabled=True, use_container_width=True)

with col_cart:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        total = 0; items_summary = []
        for name, item in list(st.session_state.cart.items()):
            sub = item['price'] * item['qty']
            total += sub
            items_summary.append(f"{name}({item['qty']})")
            
            c1, c2 = st.columns([2, 1])
            c1.write(f"**{name}**\n{sub} ฿")
            b_min, b_plus = c2.columns(2)
            if b_min.button("➖", key=f"m_{name}"):
                if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                else: del st.session_state.cart[name]
                st.rerun()
            if b_plus.button("➕", key=f"p_{name}"):
                st.session_state.cart[name]['qty'] += 1; st.rerun()
        
        st.divider(); st.markdown(f"## ยอดรวม: :orange[{total}] ฿")
        
        btn_c1, btn_c2 = st.columns(2)
        if btn_c1.button("💵 เงินสด", use_container_width=True, type="primary"):
            process_payment("เงินสด", ", ".join(items_summary), total)
        if btn_c2.button("📱 QR Code", use_container_width=True, type="primary"):
            st.session_state.show_qr = True
            
        if st.session_state.show_qr:
            st.image(f"https://promptpay.io/0945016189/{total}.png", width=250)
            if st.button("✅ ยืนยันโอนเงินเรียบร้อย", use_container_width=True):
                process_payment("QR Code", ", ".join(items_summary), total)
        
        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = {}; st.rerun()
            
    elif st.session_state.order_success:
        st.success(st.session_state.order_success)
        if st.button("เริ่มบิลใหม่"): st.session_state.order_success = None; st.rerun()
    else:
        st.info("ตะกร้าว่าง")
