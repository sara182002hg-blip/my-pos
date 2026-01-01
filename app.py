import streamlit as st
import pandas as pd
import requests
import segno
import io

# 1. ลิงก์บันทึกยอดขาย (Apps Script)
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลสินค้าที่ Publish แล้ว (จากหน้า Products)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=5)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

df_products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS - ร้านค้าหน้าหลัก")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 รายการสินค้า")
    if df_products.empty:
        st.error("❌ ไม่พบข้อมูลสินค้า โปรดตรวจสอบการ Publish บน Google Sheets")
    else:
        # แสดงรายการสินค้า เช่น ปลากระป๋อง, M150, เบียร์ช้าง 
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                name = str(row.get('Name', 'ไม่มีชื่อ'))
                price = row.get('Price', 0)
                img = str(row.get('Image_URL', 'https://via.placeholder.com/150'))
                
                st.image(img, use_container_width=True)
                if st.button(f"{name}\n{price:,.0f}.-", key=f"btn_{i}"):
                    st.session_state.cart.append({"Name": name, "Price": price})
                    st.rerun()

with col2:
    st.subheader("🛒 ตะกร้าสินค้า")
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        st.table(df_cart)
        total = df_cart['Price'].sum()
        st.write(f"### รวมทั้งสิ้น: {total:,.0f} บาท")
        
        # ตั้งค่าเบอร์ PromptPay เป็นเบอร์ที่คุณแจ้งมา
        pp_number = "0945016189"

        if st.button("ชำระเงิน & บันทึกยอด"):
            data = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": int(total)
            }
            try:
                res = requests.post(API_URL, json=data)
                if res.status_code == 200:
                    st.success("✅ บันทึกยอดขายลงในชีต Sales เรียบร้อย!")
                    # สร้าง QR Code PromptPay ตามเบอร์ 0945016189 และยอดรวม
                    qr = segno.make_qr(f"https://promptpay.io/{pp_number}/{total}")
                    img_buf = io.BytesIO()
                    qr.save(img_buf, kind='png', scale=5)
                    st.image(img_buf.getvalue(), caption=f"สแกนเพื่อจ่ายเงินเข้าเบอร์ {pp_number}")
                    st.session_state.cart = [] 
                else:
                    st.error("บันทึกข้อมูลไม่สำเร็จ")
            except:
                st.error("ไม่สามารถเชื่อมต่อกับระบบบันทึกข้อมูลได้")
                
        if st.button("ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.info("กรุณาเลือกสินค้าจากหน้าจอหลัก")
