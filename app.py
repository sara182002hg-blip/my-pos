import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS Modern POS", layout="wide", initial_sidebar_state="collapsed")

# 2. CSS ปรับแต่งให้รูปดูเหมือนปุ่มและมีเอฟเฟกต์เมื่อเอาเมาส์ไปวาง
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    /* สไตล์ Card สินค้า */
    .stButton > button {
        border: none;
        background: none;
        padding: 0;
        transition: transform 0.2s;
    }
    .stButton > button:hover {
        transform: scale(1.05); /* ขยายเล็กน้อยเมื่อเมาส์วาง */
        background: none;
        border: none;
    }
    .product-box {
        background-color: white;
        padding: 10px;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        text-align: center;
    }
    .price-text {
        color: #e67e22;
        font-weight: bold;
        font-size: 1.1em;
    }
    .cart-container {
        background-color: white;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=1)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

st.markdown("# 🏪 **TAS QUICK POS**")
st.caption("แตะที่รูปสินค้าเพื่อเพิ่มลงตะกร้า | พร้อมเพย์: 094-501-6189")

df_products = load_products()
col1, col2 = st.columns([3, 1.2])

with col1:
    if not df_products.empty:
        # จัด Grid 4 คอลัมน์
        cols = st.columns(4)
        for i, row in df_products.iterrows():
            with cols[i % 4]:
                # ใช้ปุ่มที่ครอบทั้งรูปภาพและชื่อ
                if st.button(label=f" ", key=f"img_{i}", help=f"คลิกเพื่อเพิ่ม {row['Name']}"):
                    st.session_state.cart.append({"Name": row['Name'], "Price": row['Price']})
                    st.rerun()
                
                # แสดงรายละเอียดสินค้าใต้ปุ่ม (รูปจะซ้อนอยู่บนปุ่มด้านบน)
                st.markdown(f"""
                    <div class="product-box" style="margin-top: -50px; pointer-events: none;">
                        <img src="{row['Image_URL']}" style="width:100%; border-radius:10px;">
                        <div style="margin-top:10px; font-weight:bold; color:#34495e;">{row['Name']}</div>
                        <div class="price-text">{row['Price']:,} ฿</div>
                    </div>
                """, unsafe_allow_html=True)
                st.write("") # เว้นวรรคระหว่างแถว
    else:
        st.warning("กำลังดึงข้อมูลสินค้า...")

with col2:
    st.markdown('<div class="cart-container">', unsafe_allow_html=True)
    st.subheader("🛒 ตะกร้าสินค้า")
    
    if st.session_state.cart:
        df_cart = pd.DataFrame(st.session_state.cart)
        for idx, item in df_cart.iterrows():
            st.markdown(f"✅ {item['Name']} <span style='float:right;'>{item['Price']:,} ฿</span>", unsafe_allow_html=True)
        
        total = sum(item['Price'] for item in st.session_state.cart)
        st.divider()
        st.markdown(f"### รวม: <span style='color:#27ae60'>{total:,.2f} บาท</span>", unsafe_allow_html=True)
        
        method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 โอนเงิน"], horizontal=True)
        
        if st.button("🏁 จบการขาย", type="primary", use_container_width=True):
            payload = {
                "bill_id": "B" + pd.Timestamp.now().strftime("%H%M%S"),
                "items": ", ".join(df_cart['Name'].tolist()),
                "total": float(total),
                "payment_type": method
            }
            try:
                requests.post(API_URL, json=payload)
                st.session_state.last_bill = {"total": total, "type": method}
                st.session_state.cart = []
                st.rerun()
            except: st.error("บันทึกผิดพลาด")

        if st.button("🗑️ ล้างตะกร้าทั้งหมด", use_container_width=True):
            st.session_state.cart = []
            st.rerun()
    else:
        if st.session_state.last_bill:
            last = st.session_state.last_bill
            st.success(f"บันทึกสำเร็จ! ยอดรวม {last['total']:,} ฿")
            if "โอน" in last['type']:
                st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
            else:
                st.balloons()
            if st.button("รับลูกค้าคนถัดไป"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.write("ยังไม่มีสินค้า...")
    st.markdown('</div>', unsafe_allow_html=True)
