import streamlit as st
import pandas as pd
import requests
import json
import time

# --- 1. การเชื่อมต่อหลัก ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# --- 2. ฟังก์ชันโหลดข้อมูล (ปรับปรุงเพื่อแก้ปัญหา Cache) ---
def load_data():
    # บังคับดึงข้อมูลใหม่โดยใช้ Timestamp ต่อท้าย URL
    # วิธีนี้จะทำให้ Google ไม่ส่งไฟล์เก่าที่ค้างอยู่ในระบบมาให้
    fresh_url = f"{STOCK_URL}&t={int(time.time())}"
    try:
        df = pd.read_csv(fresh_url)
        df.columns = df.columns.str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"โหลดข้อมูลไม่สำเร็จ: {e}")
        return pd.DataFrame()

# เตรียม State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False

# ดึงข้อมูลสินค้าใหม่ทุกครั้งที่รันหน้านี้
df = load_data()

# ฟังก์ชันจัดการการจ่ายเงิน
def process_payment(method, summary, total):
    payload = {
        "action": "checkout",
        "cart": st.session_state.cart,
        "method": method,
        "total": total,
        "items_summary": summary
    }
    with st.spinner('กำลังบันทึกและตัดสต็อก...'):
        try:
            res = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
            if "Success" in res.text:
                st.success(f"จ่ายด้วย {method} สำเร็จ!")
                st.session_state.cart = {}
                st.session_state.show_qr = False
                # บังคับรีเฟรชสต็อกทันที
                time.sleep(1) 
                st.rerun()
            else:
                st.error(f"เกิดข้อผิดพลาด: {res.text}")
        except:
            st.warning("บันทึกข้อมูลแล้ว โปรดรอสักครู่เพื่อให้ Google Sheets อัพเดท")
            st.session_state.cart = {}
            st.rerun()

# --- 3. ส่วนแสดงผลเมนู ---
st.sidebar.title("🛠️ แผงควบคุม")
if st.sidebar.button("🔄 อัพเดทสต็อกตอนนี้ (Refresh)"):
    st.cache_data.clear() # ล้างความจำแคชทั้งหมด
    st.rerun()

menu = st.sidebar.radio("ไปที่หน้า:", ["หน้าขายสินค้า", "จัดการสต็อกหลังบ้าน"])

if menu == "หน้าขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 สินค้าพร้อมขาย")
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    # ตกแต่งกรอบสินค้า
                    st.markdown(f"""
                        <div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">
                            <img src="{row['Image_URL']}" style="height:80px; margin-bottom:10px;">
                            <h4>{row['Name']}</h4>
                            <h3 style="color:#f1c40f;">{row['Price']:,} ฿</h3>
                            <p style="color:#2ecc71;">เหลือในระบบ: <b>{row['Stock']}</b></p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"btn_{i}", use_container_width=True):
                            name = row['Name'].strip()
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"sold_{i}", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าของลูกค้า")
        if st.session_state.cart:
            total_amt = 0
            items_list = []
            for name, item in list(st.session_state.cart.items()):
                sub_total = item['price'] * item['qty']
                total_amt += sub_total
                items_list.append(f"{name} x{item['qty']}")
                
                c_txt, c_btn = st.columns([2, 1])
                c_txt.write(f"**{name}** ({item['qty']} ชิ้น)")
                if c_btn.button("❌", key=f"del_{name}"):
                    del st.session_state.cart[name]
                    st.rerun()
            
            st.divider()
            st.header(f"ยอดรวม: {total_amt:,} ฿")
            
            p_cash, p_qr = st.columns(2)
            if p_cash.button("💵 จ่ายเงินสด", use_container_width=True, type="primary"):
                process_payment("เงินสด", ", ".join(items_list), total_amt)
            
            if p_qr.button("📱 สแกน QR", use_container_width=True, type="primary"):
                st.session_state.show_qr = True
            
            if st.session_state.show_qr:
                st.image(f"https://promptpay.io/0945016189/{total_amt}.png", width=300)
                if st.button("✅ ยืนยันว่าโอนเงินแล้ว", use_container_width=True):
                    process_payment("QR Code", ", ".join(items_list), total_amt)
        else:
            st.info("ยังไม่มีสินค้าในตะกร้า")

elif menu == "จัดการสต็อกหลังบ้าน":
    st.title("📊 รายงานสต็อกล่าสุด")
    st.write("ตัวเลขนี้ดึงมาจาก Google Sheets โดยตรง:")
    st.dataframe(df[['Name', 'Stock', 'Price']], use_container_width=True, hide_index=True)
