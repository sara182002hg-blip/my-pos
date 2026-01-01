import streamlit as st
import pandas as pd
import requests
import segno
import io

# 1. URL สำหรับบันทึกยอดขาย (Apps Script)
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"

# 2. ลิงก์ดึงข้อมูลสินค้าจากหน้า Products โดยตรง
# ผมปรับ URL ให้ดึงเฉพาะหน้า Products (gid=540097780) และบังคับเป็น CSV
SHEET_ID = "1A18StFwB8KLcFUaeUSF48TZxbKSepM-MNX4suPPrFhg"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=540097780"

st.set_page_config(page_title="POS TAS System", layout="wide")

@st.cache_data(ttl=5) # ตั้งค่าให้อัปเดตทุก 5 วินาทีเพื่อความสดใหม่
def load_products():
    try:
        # ดึงข้อมูลและตัดช่องว่างที่อาจเกิดขึ้นในชื่อหัวตาราง
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการเชื่อมต่อ: {e}")
        return pd.DataFrame()

df_products = load_products()

if 'cart' not in st.session_state:
    st.session_state.cart = []

st.title("🏪 ระบบ POS TAS (เชื่อมต่อสำเร็จ)")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📦 รายการสินค้าจากร้าน")
    if df_products.empty:
        st.warning("⚠️ กำลังพยายามดึงข้อมูล... หากนานเกินไป โปรดตรวจสอบว่าหน้าชีตแรกสุดคือหน้า Products หรือไม่")
    else:
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                # ดึงข้อมูลจากคอลัมน์ Name, Price, และ Image_URL ตามในชีต 
                name = str(row.get('Name', 'ไม่มีชื่อ'))
                try:
                    price = float(row.get('Price', 0))
                except:
                    price = 0
                img = str(row.get('Image_URL', 'https://via.placeholder.com/150'))
                
                # แสดงรูปสินค้า
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
                    # สร้าง QR Code พร้อมเพย์ (ระบุเบอร์ของคุณแทนที่เบอร์ตัวอย่าง)
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
