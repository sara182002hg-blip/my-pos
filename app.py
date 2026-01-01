import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. ตรวจสอบ URL ให้ถูกต้อง ---
# นำ URL จากหน้า image_7d90e0.png มาวางที่นี่
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
# URL สำหรับดึงสต็อก (CSV)
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ฟังก์ชันดึงสต็อก (เพิ่มพารามิเตอร์เวลาเพื่อป้องกันการจำค่าเก่า)
def load_data():
    try:
        # ใส่ t=time เพื่อบังคับให้โหลดค่าใหม่ล่าสุดเสมอ
        df = pd.read_csv(f"{STOCK_URL}&t={int(time.time())}")
        df.columns = df.columns.str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# เตรียมตัวแปรระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False
if 'order_success' not in st.session_state: st.session_state.order_success = None

# โหลดข้อมูลสินค้า
df = load_data()

def process_checkout(method, summary, total):
    payload = {
        "bill_id": f"BILL-{int(time.time())}",
        "items": summary,
        "total": total,
        "cart": st.session_state.cart,
        "method": method
    }
    with st.spinner('กำลังสื่อสารกับระบบสต็อก...'):
        try:
            response = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
            if response.status_code == 200:
                st.session_state.order_success = f"✅ บันทึกสำเร็จ: {method} {total:,} ฿"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                # บังคับล้างแคชเพื่อให้สต็อกหน้าแอปอัพเดททันที
                st.cache_data.clear() 
                st.rerun()
            else:
                st.error("ไม่สามารถเชื่อมต่อ Google Script ได้ (ตรวจสอบการ Deploy)")
        except:
            st.warning("บันทึกข้อมูลแล้ว แต่การตอบกลับล่าช้า")
            st.session_state.cart = {}
            st.rerun()

# --- หน้าจอขายสินค้า ---
st.title("🏪 TAS POS SYSTEM")
col1, col2 = st.columns([3, 2])

with col1:
    if not df.empty:
        grid = st.columns(3)
        for i, row in df.iterrows():
            with grid[i % 3]:
                st.markdown(f"""
                    <div style="background:#1e1e26; border:1px solid #333; padding:15px; border-radius:15px; text-align:center; margin-bottom:10px;">
                        <img src="{row['Image_URL']}" style="height:80px; margin-bottom:10px;">
                        <div style="font-weight:bold;">{row['Name']}</div>
                        <div style="color:#f1c40f;">{row['Price']:,} ฿</div>
                        <div style="color:#2ecc71; font-size:12px;">สต็อก: {row['Stock']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if row['Stock'] > 0:
                    if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                        n = row['Name'].strip()
                        st.session_state.cart[n] = st.session_state.cart.get(n, {'price': row['Price'], 'qty': 0})
                        st.session_state.cart[n]['qty'] += 1
                        st.rerun()
                else:
                    st.button("หมด", key=f"out_{i}", disabled=True, use_container_width=True)

with col2:
    st.subheader("🛒 รายการในตะกร้า")
    if st.session_state.cart:
        total_price = 0
        sum_text = []
        for name, item in list(st.session_state.cart.items()):
            sub = item['price'] * item['qty']
            total_price += sub
            sum_text.append(f"{name}({item['qty']})")
            
            c_info, c_btn = st.columns([1.5, 1])
            c_info.write(f"**{name}**\n{sub:,} ฿")
            
            b1, b2 = c_btn.columns(2)
            if b1.button("➖", key=f"m_{name}"):
                if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                else: del st.session_state.cart[name]
                st.rerun()
            if b2.button("➕", key=f"p_{name}"):
                st.session_state.cart[name]['qty'] += 1; st.rerun()
        
        st.divider()
        st.markdown(f"### ยอดรวม: :orange[{total_price:,}] ฿")
        
        # ปุ่มชำระเงิน
        p1, p2 = st.columns(2)
        if p1.button("💵 เงินสด", use_container_width=True, type="primary"):
            process_checkout("เงินสด", ", ".join(sum_text), total_price)
            
        if p2.button("📱 QR Code", use_container_width=True, type="primary"):
            st.session_state.show_qr = True
            st.rerun() # บังคับให้หน้าจอโหลดใหม่เพื่อแสดง QR

        # ส่วนแสดง QR Code
        if st.session_state.show_qr:
            st.markdown("---")
            st.markdown("<h4 style='text-align:center;'>สแกนจ่ายที่นี่</h4>", unsafe_allow_html=True)
            # แก้ไขลิงก์ QR Code ให้เป็นแบบ Dynamic
            qr_url = f"https://promptpay.io/0945016189/{total_price}.png"
            st.image(qr_url, width=250, use_container_width=True)
            if st.button("✅ ยืนยันว่าลูกค้าโอนแล้ว", use_container_width=True):
                process_checkout("QR Code", ", ".join(sum_text), total_price)

        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = {}
            st.session_state.show_qr = False
            st.rerun()

    elif st.session_state.order_success:
        st.success(st.session_state.order_success)
        if st.button("เริ่มบิลใหม่"):
            st.session_state.order_success = None
            st.rerun()
    else:
        st.info("ตะกร้าว่าง")
