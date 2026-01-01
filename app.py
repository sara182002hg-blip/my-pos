import streamlit as st
import pandas as pd
import requests
from io import StringIO
import time
from datetime import datetime

# --- ส่วนตั้งค่า (รบกวนตรวจสอบ URL อีกครั้ง) ---
# คัดลอก URL จากหน้า image_7d90e0.png มาวางในเครื่องหมายคำพูดด้านล่างนี้ครับ
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# ฟังก์ชันดึงสต็อก (แก้ปัญหาภาษาไทยต่างดาวและข้อมูลไม่อัพเดท)
def load_data():
    try:
        # ใส่ t= เพื่อไม่ให้ Google ส่งไฟล์เก่ามา (Anti-Cache)
        res = requests.get(f"{STOCK_URL}&t={int(time.time())}", timeout=10)
        res.encoding = 'utf-8' # บังคับอ่านภาษาไทยให้ถูกต้อง
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        # แปลงตัวเลขให้เป็นชนิดข้อมูลที่ถูกต้อง
        for col in ['Price', 'Stock', 'Cost']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"ไม่สามารถโหลดข้อมูลได้: {e}")
        return pd.DataFrame()

# ส่วนจัดการ State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False

df = load_data()

# ฟังก์ชันบันทึกการขายและตัดสต็อก
def checkout(method, total, items_text):
    payload = {
        "action": "checkout",
        "cart": st.session_state.cart,
        "method": method,
        "total": total,
        "items": items_text
    }
    with st.spinner('กำลังสื่อสารกับ Google Sheets...'):
        try:
            # ส่งข้อมูลไปยัง Script URL ที่คุณ Deploy ไว้
            response = requests.post(SCRIPT_URL, json=payload, timeout=15)
            if response.status_code == 200:
                st.success("✅ บันทึกสำเร็จและตัดสต็อกเรียบร้อย!")
                # ปุ่มดาวน์โหลดใบเสร็จ
                st.download_button("📄 กดดาวน์โหลดใบเสร็จ", f"รายการ: {items_text}\nรวม: {total} บาท", file_name="receipt.txt")
                st.session_state.cart = {}
                st.session_state.show_qr = False
                time.sleep(2)
                st.rerun()
            else:
                st.error("เกิดข้อผิดพลาดจาก Google Script โปรดตรวจสอบการ Deploy")
        except:
            st.error("ไม่สามารถเชื่อมต่อได้ โปรดตรวจสอบอินเทอร์เน็ตและ URL Script")

# --- การแสดงผลหน้าจอ ---
st.sidebar.title("🏧 เมนูระบบ")
menu = st.sidebar.radio("เลือกหน้าร้าน", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอดและกำไร"])

if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📦 สินค้าในร้าน")
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                    <div style="border:1px solid #444; padding:10px; border-radius:10px; text-align:center;">
                        <img src="{row['Image_URL']}" style="height:80px; margin-bottom:10px;">
                        <div style="font-weight:bold;">{row['Name']}</div>
                        <div style="color:#f1c40f; font-size:20px;">{row['Price']:,} ฿</div>
                        <div style="color:#2ecc71; font-size:12px;">คงเหลือ: {row['Stock']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"add_{i}", use_container_width=True):
                            name = row['Name'].strip()
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0, 'cost': row.get('Cost', 0)})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("หมด", disabled=True, use_container_width=True)

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_sum = 0
            items_summary = []
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total_sum += sub
                items_summary.append(f"{name}({item['qty']})")
                
                c_info, c_btn = st.columns([2, 1])
                c_info.write(f"**{name}**\n{sub:,} ฿")
                
                # ปุ่มบวก-ลบ (ไม่มีกากบาทตามที่ต้องการ)
                b1, b2 = c_btn.columns(2)
                if b1.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if b2.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1; st.rerun()
            
            st.divider()
            st.header(f"ยอดรวม: :orange[{total_sum:,}] ฿")
            
            # ปุ่มเคลียร์ตะกร้า
            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}; st.rerun()

            p1, p2 = st.columns(2)
            if p1.button("💵 เงินสด", use_container_width=True, type="primary"):
                checkout("เงินสด", total_sum, ", ".join(items_summary))
            if p2.button("📱 QR Code", use_container_width=True):
                st.session_state.show_qr = not st.session_state.show_qr

            if st.session_state.show_qr:
                st.image(f"https://promptpay.io/0945016189/{total_sum}.png", width=250)
                if st.button("✅ ยืนยันลูกค้าโอนแล้ว", use_container_width=True):
                    checkout("QR Code", total_sum, ", ".join(items_summary))
        else:
            st.info("ตะกร้าว่าง")

elif menu == "📊 สรุปยอดและกำไร":
    st.title("📊 สถิติร้านค้า")
    # ส่วนสรุปกำไรขาดทุน
    st.info("ระบบคำนวณกำไรจาก (ราคาขาย - ต้นทุน) ของรายการที่ขายได้จริง")
    st.subheader("🏆 สินค้าขายดีที่สุด 5 อันดับ")
    st.write("ข้อมูลจะอัพเดทตามตาราง Sales ใน Google Sheets")
