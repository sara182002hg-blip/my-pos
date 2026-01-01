import streamlit as st
import pandas as pd
import requests

# 1. ลิงก์บันทึกยอดขาย (Apps Script)
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลสินค้าที่คุณส่งมา (แบบ CSV)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=5)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

df_products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS (พร้อมใช้งาน)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 เลือกสินค้า")
    if df_products.empty:
        st.error("❌ ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบอินเทอร์เน็ต")
    else:
        # แสดงสินค้า เช่น ปลากระป๋อง, ลูกอม, น้ำเปล่า 
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                name = str(row.get('Name', 'ไม่มีชื่อ'))
                price = row.get('Price', 0)
                img = str(row.get('Image_URL', 'https://via.placeholder.com/150'))
                
                st.image(img, use_container_width=True)
                if st.button(f"เพิ่ม {name}\n{price}.-", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": name, "Price": price})
                    st.rerun()

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = sum(item['Price'] for item in st.session_state.cart)
        st.write(f"### รวม: {total:,.2f} บาท")
        
        if st.button("💰 ชำระเงิน & บันทึกยอด"):
            data = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total)
            }
            try:
                res = requests.post(API_URL, json=data)
                if res.status_code == 200:
                    st.success("✅ บันทึกยอดขายสำเร็จ!")
                    # ดึง QR Code สำเร็จรูปจาก promptpay.io (เบอร์ของคุณ)
                    qr_link = f"https://promptpay.io/0945016189/{total}.png"
                    st.image(qr_link, caption=f"สแกนจ่ายเงินเบอร์ 0945016189 จำนวน {total} บาท")
                    st.session_state.cart = [] 
                else:
                    st.error("บันทึกไม่สำเร็จ")
            except:
                st.error("เชื่อมต่อระบบบันทึกไม่ได้")
                
        if st.button("ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("ยังไม่มีสินค้าในตะกร้า")
