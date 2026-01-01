import streamlit as st
import pandas as pd
import requests
import segno
import io

# 1. URL สำหรับบันทึกยอดขาย (Apps Script)
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ตรงสำหรับดึงข้อมูลหน้า Products (ID: 1A18StFwB8KLcFUaeUSF48TZxbKSepM-MNX4suPPrFhg)
# ระบุ gid=540097780 เพื่อดึงเฉพาะชีตสินค้า
SHEET_URL = "https://docs.google.com/spreadsheets/d/1A18StFwB8KLcFUaeUSF48TZxbKSepM-MNX4suPPrFhg/export?format=csv&gid=540097780"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=5)
def load_products():
    try:
        # ดึงข้อมูลและลบช่องว่างส่วนเกินในหัวตาราง
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        return pd.DataFrame()

df_products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS (เชื่อมต่อสำเร็จ)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 รายการสินค้าจากร้าน")
    if df_products.empty:
        st.error("❌ ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบว่าเปิดแชร์ Google Sheets เป็น 'Everyone with the link' หรือยัง")
    else:
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
        
        if st.button("ชำระเงิน & บันทึกยอด"):
            data = {
                "bill_id": "BILL-" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": int(total)
            }
            try:
                res = requests.post(API_URL, json=data)
                if res.status_code == 200:
                    st.success("✅ บันทึกยอดขายลงหน้า Sales สำเร็จ!")
                    # สร้าง QR Code (เปลี่ยนเบอร์โทรเป็นของคุณ)
                    qr = segno.make_qr(f"https://promptpay.io/0812345678/{total}")
                    img_buf = io.BytesIO()
                    qr.save(img_buf, kind='png', scale=5)
                    st.image(img_buf.getvalue(), caption="สแกนจ่ายเงินที่นี่")
                    st.session_state.cart = [] 
                else:
                    st.error(f"❌ บันทึกไม่สำเร็จ (Code: {res.status_code})")
            except Exception as e:
                st.error(f"⚠️ การส่งข้อมูลขัดข้อง: {e}")
                
        if st.button("ล้างตะกร้า"):
            st.session_state.cart = []
            st.rerun()
    else:
        st.write("เลือกสินค้าเพื่อเริ่มต้นการขาย")
