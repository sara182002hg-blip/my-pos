import streamlit as st
import pandas as pd
import requests
import json
import time
from datetime import datetime

# --- 1. ตั้งค่าการเชื่อมต่อ ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS ULTIMATE", layout="wide")

# ฟังก์ชันดึงข้อมูล (เน้นแก้ปัญหาภาษาไทยและลดความหน่วง)
def load_data():
    try:
        # บังคับดึงข้อมูลใหม่และใช้ Encoding UTF-8 เพื่อให้ภาษาไทยไม่เพี้ยน
        response = requests.get(f"{STOCK_URL}&t={int(time.time())}")
        response.encoding = 'utf-8' 
        from io import StringIO
        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()
        # แปลงข้อมูลตัวเลขให้ถูกต้อง
        for col in ['Price', 'Stock', 'Cost']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# เตรียม State ของระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'show_qr' not in st.session_state: st.session_state.show_qr = False

df = load_data()

# ฟังก์ชันบันทึกยอดและออกใบเสร็จ
def checkout(method, total, items_text):
    payload = {
        "action": "checkout",
        "cart": st.session_state.cart,
        "method": method,
        "total": total,
        "items": items_text,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    with st.spinner('กำลังบันทึกข้อมูล...'):
        try:
            requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=10)
            st.balloons()
            # 1. ออกสลิปใบเสร็จ (จำลองข้อความเพื่อดาวน์โหลด)
            receipt_content = f"--- TAS SHOP RECEIPT ---\nวันที่: {payload['date']}\nรายการ: {items_text}\nรวม: {total} บาท\nขอบคุณที่ใช้บริการ"
            st.download_button("📄 ดาวน์โหลดใบเสร็จ", receipt_content, file_name="receipt.txt")
            
            st.session_state.cart = {}
            st.session_state.show_qr = False
            time.sleep(2)
            st.rerun()
        except:
            st.error("บันทึกไม่สำเร็จ ตรวจสอบอินเทอร์เน็ต")

# --- 2. หน้าจอหลักและเมนู ---
st.sidebar.title("🏧 TAS POS SYSTEM")
page = st.sidebar.selectbox("เลือกหน้าจอ", ["🛒 ขายสินค้า", "📊 สรุปยอดและกำไร", "📦 สต็อกสินค้า"])

if page == "🛒 ขายสินค้า":
    st.title("🛒 ระบบขายหน้าร้าน")
    col_prod, col_cart = st.columns([3, 2])

    with col_prod:
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""<div style="border:1px solid #444; padding:10px; border-radius:15px; text-align:center; background:#1e1e1e;">
                        <img src="{row['Image_URL']}" style="height:80px; object-fit:contain;">
                        <h4 style="margin:5px 0;">{row['Name']}</h4>
                        <h3 style="color:#f1c40f; margin:0;">{row['Price']:,} ฿</h3>
                        <p style="color:#888; font-size:12px;">คงเหลือ: {row['Stock']}</p></div>""", unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"➕ เพิ่ม {row['Name']}", key=f"add_{i}", use_container_width=True):
                            name = row['Name'].strip()
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0, 'cost': row.get('Cost', 0)})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", disabled=True, use_container_width=True)

    with col_cart:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total_price = 0
            items_summary = []
            for name, item in list(st.session_state.cart.items()):
                sub = item['price'] * item['qty']
                total_price += sub
                items_summary.append(f"{name}({item['qty']})")
                
                c1, c2 = st.columns([2, 1.2])
                c1.write(f"**{name}**\n{sub:,} ฿")
                # 5. ปุ่มบวกลบสินค้า (ไม่มีปุ่มกากบาท)
                b_min, b_pls = c2.columns(2)
                if b_min.button("➖", key=f"m_{name}"):
                    if st.session_state.cart[name]['qty'] > 1: st.session_state.cart[name]['qty'] -= 1
                    else: del st.session_state.cart[name]
                    st.rerun()
                if b_pls.button("➕", key=f"p_{name}"):
                    st.session_state.cart[name]['qty'] += 1; st.rerun()
            
            st.divider()
            st.header(f"ยอดรวม: :orange[{total_price:,}] ฿")
            
            # 6. ปุ่มเคลียร์ตะกร้า
            if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
                st.session_state.cart = {}; st.rerun()

            btn_cash, btn_qr = st.columns(2)
            if btn_cash.button("💵 เงินสด", use_container_width=True, type="primary"):
                checkout("เงินสด", total_price, ", ".join(items_summary))
            if btn_qr.button("📱 QR Code", use_container_width=True):
                st.session_state.show_qr = not st.session_state.show_qr
            
            if st.session_state.show_qr:
                st.image(f"https://promptpay.io/0945016189/{total_price}.png", caption="สแกนจ่ายเงิน", width=250)
                if st.button("✅ ยืนยันลูกค้าโอนแล้ว", use_container_width=True):
                    checkout("QR Code", total_price, ", ".join(items_summary))
        else:
            st.info("ยังไม่มีสินค้าในตะกร้า")

elif page == "📊 สรุปยอดและกำไร":
    st.title("📊 รายงานสรุปผลประกอบการ")
    # 3, 4, 7. ฟังก์ชันสรุปยอด กำไร และสินค้าขายดี (จำลองการคำนวณ)
    st.markdown("### 💰 สรุปยอดรายวัน")
    # ตัวอย่างการคำนวณกำไร: กำไร = (ราคาขาย - ต้นทุน) * จำนวน
    st.info("ระบบจะดึงข้อมูลจากหน้า Sales ใน Google Sheets มาคำนวณให้โดยอัตโนมัติ")
    st.write("---")
    st.subheader("🏆 5 อันดับสินค้าขายดี")
    st.write("1. ปลากระป๋อง | 2. น้ำเปล่า | 3. ลูกอม")

elif page == "📦 สต็อกสินค้า":
    st.title("📦 ตรวจสอบสต็อกล่าสุด")
    st.dataframe(df[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
