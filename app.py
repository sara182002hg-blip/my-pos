import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import qrcode
from io import BytesIO
from PIL import Image

# --- CONFIGURATION & STYLING ---
st.set_page_config(page_title="Premium POS System", layout="wide", initial_sidebar_state="expanded")

def local_css():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Sarabun:wght@300;400;700&display=swap');
        html, body, [class*="css"] { font-family: 'Sarabun', sans-serif; }
        .main { background-color: #f8f9fa; }
        .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #1E1E1E; color: white; transition: 0.3s; }
        .stButton>button:hover { background-color: #FF4B4B; border: none; }
        .product-card { border: 1px solid #ddd; padding: 10px; border-radius: 15px; background: white; text-align: center; margin-bottom: 20px; transition: 0.3s; }
        .product-card:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.1); transform: translateY(-5px); }
        .sidebar .sidebar-content { background-image: linear-gradient(#2e7bcf,#2e7bcf); color: white; }
        .receipt-box { border: 2px dashed #000; padding: 20px; background: #fff; font-family: 'Courier New', Courier, monospace; }
        </style>
    """, unsafe_allow_html=True)

# --- MOCK DATA ENGINE (แทนการเชื่อมต่อ Sheet จริงเพื่อความรวดเร็วในการ Test) ---
# ในการใช้งานจริง ให้ใช้ gspread เชื่อมต่อกับ URL ที่คุณส่งมา
@st.cache_data(ttl=60)
def load_data(sheet_name):
    # นี่คือตัวอย่างการดึงข้อมูลตามโครงสร้างคอลัมน์ที่คุณให้มา
    if sheet_name == "Products":
        return pd.DataFrame({
            'Name': ['Premium Coffee', 'Green Tea Latte', 'Croissant', 'Chocolate Cake'],
            'Price': [75, 80, 55, 120],
            'Image_URL': ['https://via.placeholder.com/150']*4
        })
    elif sheet_name == "Stock":
        return pd.DataFrame({
            'Name': ['Premium Coffee', 'Green Tea Latte', 'Croissant', 'Chocolate Cake'],
            'Stock': [10, 4, 15, 8],
            'Price': [75, 80, 55, 120],
            'Image_URL': ['https://via.placeholder.com/150']*4,
            'Cost': [30, 35, 20, 50]
        })
    return pd.DataFrame()

# --- FUNCTIONS ---
def generate_promptpay_qr(amount):
    # จำลองการสร้าง QR Code (ต้องใช้เลข PromptPay ของคุณ)
    pp_id = "0812345678" 
    # ในโปรเจกต์จริง แนะนำให้ใช้ lib 'promptpay' เพื่อสร้าง payload ที่ถูกต้อง
    qr_data = f"PromptPay:{pp_id}, Amount:{amount}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- SESSION STATE INITIALIZATION ---
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'page' not in st.session_state:
    st.session_state.page = "ขายสินค้า"

# --- SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🌟 PREMIUM POS")
    st.markdown("---")
    menu = st.radio("เมนูการใช้งาน", ["🛒 รายการขาย", "📊 รายงานข้อมูล", "📦 สต็อกออนไลน์"])
    st.markdown("---")
    st.info(f"ผู้ใช้งาน: Admin\nวันที่: {datetime.now().strftime('%d/%m/%Y')}")

# --- PAGE 1: SALES INTERFACE ---
if menu == "🛒 รายการขาย":
    local_css()
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("รายการสินค้า")
        products = load_data("Products")
        stock_info = load_data("Stock")
        
        # ค้นหาสินค้า
        search = st.text_input("🔍 ค้นหาสินค้า...", "")
        
        # Grid แสดงสินค้า
        rows = len(products) // 3 + 1
        for i in range(rows):
            cols = st.columns(3)
            for j in range(3):
                idx = i * 3 + j
                if idx < len(products):
                    prod = products.iloc[idx]
                    stk = stock_info[stock_info['Name'] == prod['Name']]['Stock'].values[0]
                    
                    with cols[j]:
                        st.markdown(f"""
                            <div class="product-card">
                                <img src="{prod['Image_URL']}" width="100%">
                                <h4>{prod['Name']}</h4>
                                <p style="color:red; font-weight:bold;">{prod['Price']} ฿</p>
                                <p style="font-size:0.8em;">คงเหลือ: {stk}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"เพิ่ม {prod['Name']}", key=f"btn_{idx}"):
                            if stk > 0:
                                if prod['Name'] in st.session_state.cart:
                                    st.session_state.cart[prod['Name']]['qty'] += 1
                                else:
                                    st.session_state.cart[prod['Name']] = {'price': prod['Price'], 'qty': 1}
                            else:
                                st.error("สินค้าหมด!")

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        total_amount = 0
        if not st.session_state.cart:
            st.write("ไม่มีสินค้าในตะกร้า")
        else:
            for item, details in list(st.session_state.cart.items()):
                c1, c2, c3 = st.columns([2, 1, 1])
                c1.write(f"**{item}**")
                c2.write(f"{details['price'] * details['qty']}฿")
                
                # ปุ่มบวกลบ
                bc1, bc2, bc3 = c3.columns(3)
                if bc1.button("-", key=f"minus_{item}"):
                    st.session_state.cart[item]['qty'] -= 1
                    if st.session_state.cart[item]['qty'] <= 0:
                        del st.session_state.cart[item]
                    st.rerun()
                bc2.write(details['qty'])
                if bc3.button("+", key=f"plus_{item}"):
                    st.session_state.cart[item]['qty'] += 1
                    st.rerun()
                
                total_amount += details['price'] * details['qty']
        
        st.markdown("---")
        st.title(f"รวม: {total_amount:,.2f} ฿")
        
        pay_method = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"])
        
        if pay_method == "เงินสด":
            cash_received = st.number_input("รับเงินมา", min_value=0.0)
            if cash_received >= total_amount and total_amount > 0:
                change = cash_received - total_amount
                st.success(f"เงินทอน: {change:,.2f} ฿")
        
        if st.button("🧧 ยืนยันการชำระเงิน / ออกใบเสร็จ"):
            if total_amount > 0:
                st.balloons()
                # แสดงใบเสร็จ
                st.markdown('<div class="receipt-box">', unsafe_allow_html=True)
                st.write("### RECEIPT")
                st.write(f"วันที่: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                st.write("--------------------------------")
                for item, d in st.session_state.cart.items():
                    st.write(f"{item} x{d['qty']} : {d['price']*d['qty']}฿")
                st.write("--------------------------------")
                st.write(f"**ยอดรวมทั้งสิ้น: {total_amount}฿**")
                
                if pay_method == "พร้อมเพย์":
                    st.image(generate_promptpay_qr(total_amount), width=200)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                if st.button("พิมพ์ใบเสร็จ"):
                    st.info("กำลังส่งข้อมูลไปที่เครื่องพิมพ์...")
                
                # Reset ตะกร้า
                if st.button("เริ่มการขายใหม่"):
                    st.session_state.cart = {}
                    st.rerun()
            else:
                st.warning("กรุณาเลือกสินค้า")

        if st.button("❌ ยกเลิกบิล"):
            st.session_state.cart = {}
            st.rerun()

# --- PAGE 2: DASHBOARD ---
elif menu == "📊 รายงานข้อมูล":
    st.title("📊 รายงานวิเคราะห์ยอดขาย")
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("ยอดขายวันนี้", "4,500 ฿", "+12%")
    m2.metric("ยอดขายสัปดาห์นี้", "28,000 ฿", "+5%")
    m3.metric("ยอดขายเดือนนี้", "120,000 ฿", "+18%")
    m4.metric("จำนวนบิลวันนี้", "42 บิล")

    # กราฟสถิติ
    c1, c2 = st.columns(2)
    with c1:
        st.write("### สถิติยอดขาย 7 วันล่าสุด")
        df_chart = pd.DataFrame({
            'Date': pd.date_range(start='2024-01-01', periods=7),
            'Sales': [3000, 4500, 3800, 5200, 4800, 6000, 4500]
        })
        fig = px.line(df_chart, x='Date', y='Sales', markers=True)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.write("### อันดับสินค้าขายดี")
        best_sell = pd.DataFrame({
            'Product': ['Coffee', 'Tea', 'Cake'],
            'Qty': [120, 85, 40]
        })
        fig2 = px.bar(best_sell, x='Qty', y='Product', orientation='h', color='Qty')
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    if st.button("📝 สรุปยอดรายวัน และเริ่มใหม่ (Reset Daily)"):
        st.warning("ระบบกำลังบันทึกข้อมูลลง DailySummary และทำการล้างยอดรายวัน...")
        # ตรงนี้ต้องใส่ Logic การอัปเดต Google Sheet คอลัมน์ DailySummary

# --- PAGE 3: STOCK ONLINE ---
elif menu == "📦 สต็อกออนไลน์":
    st.title("📦 ระบบจัดการสต็อก")
    stock_df = load_data("Stock")
    
    # แจ้งเตือนสต็อกต่ำ
    low_stock = stock_df[stock_df['Stock'] < 5]
    for _, row in low_stock.iterrows():
        st.error(f"⚠️ สินค้าใกล้หมด: {row['Name']} เหลือเพียง {row['Stock']} ชิ้น")
    
    st.write("### ตารางสต็อกปัจจุบัน")
    st.dataframe(stock_df.style.highlight_max(axis=0), use_container_width=True)
    
    st.info(f"อัปเดตสต็อกล่าสุด: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
