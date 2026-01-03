import streamlit as st
import requests
import pandas as pd
import qrcode
from io import BytesIO
from datetime import datetime

# --- CONFIGURATION ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"

st.set_page_config(page_title="Premium POS Dashboard", layout="wide")

# --- CUSTOM CSS FOR PREMIUM LOOK ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #262730; color: white; border: 1px solid #444; }
    .stButton>button:hover { border-color: #3B8ED0; color: #3B8ED0; }
    .cart-box { background-color: #1e1e1e; padding: 20px; border-radius: 15px; border: 1px solid #333; }
    .price-tag { color: #2ecc71; font-weight: bold; font-size: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- API FUNCTIONS ---
def get_data():
    try:
        response = requests.get(f"{API_URL}?action=getInitialData")
        return response.json()
    except:
        return None

def post_sale(data):
    try:
        response = requests.post(API_URL, json=data)
        return response.ok
    except:
        return False

# --- SESSION STATE ---
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'data' not in st.session_state:
    st.session_state.data = get_data()

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("💎 PREMIUM POS")
menu = st.sidebar.radio("เมนูหลัก", ["🛒 รายการขาย", "📊 รายงานข้อมูล", "📦 สต็อกออนไลน์"])

if st.sidebar.button("🔄 รีเฟรชข้อมูล"):
    st.session_state.data = get_data()
    st.rerun()

# --- PAGE: SALES ---
if menu == "🛒 รายการขาย":
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("รายการสินค้า")
        if st.session_state.data:
            prods = st.session_state.data['products']
            stocks = {str(s['id']): s['qty'] for s in st.session_state.data['stock']}
            
            # Search Bar
            search = st.text_input("🔍 ค้นหาสินค้า...")
            
            # Grid Layout for Products
            p_cols = st.columns(3)
            for idx, p in enumerate(prods):
                if search.lower() in p['name'].lower():
                    with p_cols[idx % 3]:
                        current_stock = stocks.get(str(p['id']), 0)
                        st.markdown(f"**{p['name']}**")
                        st.markdown(f"<p class='price-tag'>฿{p['price']}</p>", unsafe_allow_html=True)
                        st.caption(f"คงเหลือ: {current_stock}")
                        
                        if st.button(f"เพิ่มลงตะกร้า", key=f"add_{p['id']}"):
                            p_id = str(p['id'])
                            if p_id in st.session_state.cart:
                                st.session_state.cart[p_id]['qty'] += 1
                            else:
                                st.session_state.cart[p_id] = {'name': p['name'], 'price': p['price'], 'qty': 1}
                            st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        total = 0
        with st.container(border=True):
            if not st.session_state.cart:
                st.write("ไม่มีสินค้าในตะกร้า")
            else:
                for p_id, item in list(st.session_state.cart.items()):
                    subtotal = item['price'] * item['qty']
                    total += subtotal
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"{item['name']}")
                    if c2.button("➖", key=f"min_{p_id}"):
                        st.session_state.cart[p_id]['qty'] -= 1
                        if st.session_state.cart[p_id]['qty'] <= 0: del st.session_state.cart[p_id]
                        st.rerun()
                    if c3.button("➕", key=f"pls_{p_id}"):
                        st.session_state.cart[p_id]['qty'] += 1
                        st.rerun()
                
                st.divider()
                st.markdown(f"### รวมทั้งสิ้น: <span style='color:#2ecc71'>฿{total:,.2f}</span>", unsafe_allow_html=True)
                
                method = st.radio("ช่องทางชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                if method == "เงินสด":
                    received = st.number_input("รับเงินมา", min_value=float(total))
                    st.success(f"เงินทอน: ฿{received - total:,.2f}")
                else:
                    qr_url = f"https://promptpay.io/0812345678/{total}" # ใส่เบอร์คุณตรงนี้
                    st.image(f"https://api.qrserver.com/v1/create-qr-code/?size=150x150&data={qr_url}", caption="สแกนจ่ายที่นี่")

                if st.button("✅ ยืนยันการขาย & ตัดสต็อก", type="primary"):
                    payload = {
                        "action": "recordSale",
                        "data": {"items": str(st.session_state.cart), "total": total, "method": method},
                        "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in st.session_state.cart.items()]
                    }
                    if post_sale(payload):
                        st.balloons()
                        st.session_state.cart = {}
                        st.session_state.data = get_data() # Update stock
                        st.success("บันทึกสำเร็จ!")
                        st.rerun()

# --- PAGE: STOCK ---
elif menu == "📦 สต็อกออนไลน์":
    st.subheader("คลังสินค้าคงเหลือ")
    if st.session_state.data:
        df_stock = pd.DataFrame(st.session_state.data['stock'])
        
        # แสดง Alert
        low_stock = df_stock[df_stock['qty'].astype(int) < 5]
        if not low_stock.empty:
            st.warning(f"⚠️ มีสินค้าใกล้หมด {len(low_stock)} รายการ!")
            
        st.dataframe(df_stock, use_container_width=True)

# --- PAGE: REPORT ---
elif menu == "📊 รายงานข้อมูล":
    st.subheader("สรุปยอดขาย")
    # ส่วนนี้คุณสามารถดึงข้อมูลจาก Sheet Sales มาสร้างกราฟด้วย st.line_chart() ได้
    st.info("ระบบรายงานกำลังเชื่อมต่อข้อมูลจาก DailySummary...")
