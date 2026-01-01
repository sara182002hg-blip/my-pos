import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. CSS ขั้นสูง: ล็อกตำแหน่งปุ่มให้ตรงกัน และตัวหนังสือขาวชัดเจน
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; margin-bottom: 5px; display: flex; flex-direction: column;
        align-items: center; height: 260px; justify-content: space-between;
    }
    .img-box {
        width: 100%; height: 140px; background-color: white; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden;
    }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; text-align: center; font-size: 0.9em; margin-top: 5px; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
    /* บังคับปุ่ม Streamlit ให้มีขนาดพอดีกล่อง */
    .stButton > button { 
        width: 100% !important; border-radius: 8px !important; 
        background-color: #28a745 !important; color: white !important;
        font-weight: bold !important; height: 35px !important;
    }
    p, span, label, h1, h2, h3, div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. ระบบจัดการตะกร้าสินค้า (เพิ่ม/ลด แบบรวดเร็ว)
if 'cart' not in st.session_state:
    st.session_state.cart = {}

def add_to_cart(name, price):
    if name in st.session_state.cart:
        st.session_state.cart[name]['qty'] += 1
    else:
        st.session_state.cart[name] = {'price': price, 'qty': 1}

# 4. โหลดข้อมูลสินค้า (ดึงข้อมูลเพียงครั้งเดียวเพื่อลดความหน่วง)
@st.cache_data(ttl=300) # จำข้อมูลไว้ 5 นาที
def get_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

df_products = get_products()

st.title("🏪 TAS PROFESSIONAL POS")
col_main, col_cart = st.columns([3.8, 1.2])

with col_main:
    if not df_products.empty:
        # สร้าง Grid 4 คอลัมน์
        rows = [df_products[i:i + 4] for i in range(0, df_products.shape[0], 4)]
        for row_data in rows:
            cols = st.columns(4)
            for idx, (i, row) in enumerate(row_data.iterrows()):
                with cols[idx]:
                    # แสดงรายละเอียดสินค้า
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div class="p-name">{row['Name']}</div>
                            <div class="p-price">{row['Price']:,} ฿</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # ปุ่มกดที่ทำงานร่วมกับ Session State โดยตรง
                    if st.button(f"➕ เลือก", key=f"add_{i}"):
                        add_to_cart(row['Name'], row['Price'])
                        st.rerun()
    else:
        st.error("ไม่สามารถโหลดข้อมูลสินค้าได้ กรุณาเช็ค Google Sheets")

with col_cart:
    st.subheader("🛒 รายการสินค้า")
    if st.session_state.cart:
        total = 0
        items_summary = []
        for name, info in list(st.session_state.cart.items()):
            subtotal = info['price'] * info['qty']
            total += subtotal
            items_summary.append(f"{name} x{info['qty']}")
            
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{name}**")
                st.caption(f"{info['qty']} x {info['price']:,} ฿")
            with c2:
                if st.button("❌", key=f"del_{name}"):
                    st.session_state.cart[name]['qty'] -= 1
                    if st.session_state.cart[name]['qty'] <= 0:
                        del st.session_state.cart[name]
                    st.rerun()
            st.divider()

        st.markdown(f"### รวม: :orange[{total:,.2f}] ฿")
        pay_type = st.radio("วิธีชำระ:", ["เงินสด", "โอนเงิน"], horizontal=True)
        
        if st.button("✅ ยืนยันการขาย", type="primary"):
            bill_id = "B" + pd.Timestamp.now().strftime("%H%M%S")
            # ส่งข้อมูลไป Google Sheets
            data_url = f"{API_URL}?bill_id={bill_id}&items={', '.join(items_summary)}&total={total}&payment_type={pay_type}"
            try: requests.get(data_url, timeout=0.1)
            except: pass
            
            st.session_state.last_bill = {"total": total, "type": pay_type}
            st.session_state.cart = {}
            st.rerun()
            
        if st.button("🗑️ ล้างตะกร้า"):
            st.session_state.cart = {}
            st.rerun()
            
    elif 'last_bill' in st.session_state and st.session_state.last_bill:
        last = st.session_state.last_bill
        st.success(f"บันทึกสำเร็จ {last['total']:,} ฿")
        if "โอน" in last['type']:
            st.image(f"https://promptpay.io/0945016189/{last['total']}.png")
        if st.button("เริ่มบิลใหม่"):
            st.session_state.last_bill = None
            st.rerun()
    else:
        st.write("กรุณาเลือกสินค้า...")
