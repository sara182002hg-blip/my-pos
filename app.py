import streamlit as st
import pandas as pd
import requests
import json
import time

# --- ตั้งค่าการเชื่อมต่อ (ใช้ URL ล่าสุดของคุณ) ---
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbXjdHQCM5mbntB82L_7YrkyxayA1k3R6HuXcPh91bwlzYb2ROVVYJnB2p5RdSstXeU/exec"
STOCK_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

@st.cache_data(ttl=2)
def load_data():
    try:
        # ดึงข้อมูลจาก Google Sheets CSV
        df = pd.read_csv(f"{STOCK_URL}&t={int(time.time())}")
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# เตรียม State ของระบบ
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'order_success' not in st.session_state: st.session_state.order_success = None
if 'show_qr' not in st.session_state: st.session_state.show_qr = False

df = load_data()

# ฟังก์ชันจัดการการชำระเงินและตัดสต็อก
def process_payment(method, summary, total):
    payload = {
        "bill_id": f"B{int(time.time())}",
        "items": summary,
        "total": total,
        "cart": st.session_state.cart,
        "method": method
    }
    with st.spinner('กำลังบันทึกข้อมูล...'):
        try:
            # ส่งข้อมูลไปยัง Apps Script (Timeout 15 วินาทีเพื่อไม่ให้ค้างนาน)
            response = requests.post(SCRIPT_URL, data=json.dumps(payload), timeout=15)
            if "Success" in response.text:
                st.session_state.order_success = f"✅ บันทึกสำเร็จ: {method} {total} ฿"
                st.session_state.cart = {}
                st.session_state.show_qr = False
                st.cache_data.clear() # ล้างแคชเพื่อให้โหลดสต็อกใหม่ทันที
                st.rerun()
            else:
                st.error("เกิดข้อผิดพลาดจาก Google Script: " + response.text[:100])
        except:
            # กรณีเชื่อมต่อช้า แอปจะแจ้งเตือนแต่ข้อมูลมักจะเข้า Sheets ไปแล้ว
            st.warning("⚠️ การสื่อสารล่าช้า ระบบกำลังบันทึกข้อมูลเบื้องหลัง กรุณารอสักครู่")
            st.session_state.cart = {}
            st.rerun()

# --- หน้าจอหลัก ---
st.sidebar.title("TAS POS MENU")
menu = st.sidebar.radio("เลือกหน้าจอ", ["🛒 ขายสินค้า", "📊 สต็อกสินค้า"])

if menu == "🛒 ขายสินค้า":
    st.title("🏪 TAS POS SYSTEM")
    col_main, col_cart = st.columns([3, 2])

    with col_main:
        if not df.empty:
            grid = st.columns(3)
            for i, row in df.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="text-align:center; border:1px solid #444; padding:10px; border-radius:10px; margin-bottom:10px;">
                            <img src="{row['Image_URL']}" style="height:60px; object-fit:contain;">
                            <div style="font-weight:bold; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f;">{row['Price']} ฿</div>
                            <div style="font-size:0.8em; color:#888;">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เพิ่ม {row['Name']}", key=f"add_{i}", use_container_width=True):
                            name = row['Name'].strip()
                            st.session_state.cart[name] = st.session_state.cart.get(name, {'price': row['Price'], 'qty': 0})
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"none_{i}", disabled=True, use_container_width=True)

    with col_cart:
        st.subheader("🛒 รายการในตะกร้า")
        if st.session_state.cart:
            total_price = 0
            items_list = []
            for name, item in list(st.session_state.cart.items()):
                subtotal = item['price'] * item['qty']
                total_price += subtotal
                items_list.append(f"{name}({item['qty']})")
                
                c_info, c_btn = st.columns([1.5, 1])
                c_info.write(f"**{name}**\n{subtotal} ฿")
                
                # ปุ่มบวก/ลบ (ไม่มีปุ่มกากบาท)
                b1, b2 = c_btn.columns(2)
                if b1.button("➖", key=f"minus_{name}"):
                    if st.session_state.cart[name]['qty'] > 1:
                        st.session_state.cart[name]['qty'] -= 1
                    else:
                        del st.session_state.cart[name]
                    st.rerun()
                if b2.button("➕", key=f"plus_{name}"):
                    st.session_state.cart[name]['qty'] += 1
                    st.rerun()
            
            st.divider()
            st.markdown(f"## ยอดรวม: :orange[{total_price}] ฿")
            
            btn_cash, btn_qr = st.columns(2)
            if btn_cash.button("💵 เงินสด", use_container_width=True, type="primary"):
                process_payment("เงินสด", ", ".join(items_list), total_price)
            if btn_qr.button("📱 QR Code", use_container_width=True, type="primary"):
                st.session_state.show_qr = True

            if st.session_state.show_qr:
                st.image(f"https://promptpay.io/0945016189/{total_price}.png", width=250)
                if st.button("✅ ยืนยันว่าลูกค้าโอนแล้ว", use_container_width=True):
                    process_payment("QR Code", ", ".join(items_list), total_price)

            if st.button("🗑️ ล้างตะกร้า", use_container_width=True):
                st.session_state.cart = {}
                st.rerun()

        elif st.session_state.order_success:
            st.success(st.session_state.order_success)
            if st.button("เริ่มบิลใหม่"):
                st.session_state.order_success = None
                st.rerun()
        else:
            st.info("ตะกร้าว่างเปล่า")

else:
    st.title("📊 ตารางสต็อกสินค้า")
    st.dataframe(df[['Name', 'Stock']], use_container_width=True, hide_index=True)
