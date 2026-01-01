import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS & ADMIN", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (ปรับให้เสถียรขึ้น)
def fetch_data():
    try:
        # ดึงข้อมูลจาก Google Sheets
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        # ถ้าไม่มีคอลัมน์ Stock ให้สร้างขึ้นมากัน Error
        if 'Stock' not in df.columns:
            df['Stock'] = 0
        return df
    except Exception as e:
        st.error(f"เชื่อมต่อ Google Sheets ไม่ได้: {e}")
        return pd.DataFrame()

# 3. เตรียมตัวแปรในระบบ (Session State)
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

# --- โหลดข้อมูลสินค้าเข้ามาใช้งานเสมอ ---
df_products = fetch_data()

# 4. CSS ปรับแต่งหน้าจอ (เหมือนเดิมเพื่อให้สวยงาม)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; margin-bottom: 5px; text-align: center; height: 260px;
    }
    .img-box {
        width: 100%; height: 130px; background-color: white; border-radius: 8px;
        display: flex; align-items: center; justify-content: center; overflow: hidden;
    }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; margin-top: 5px; height: 2.4em; overflow: hidden; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.1em; }
    .stButton > button { width: 100% !important; border-radius: 8px !important; }
    .metric-card { background: #1a1c24; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745; margin-bottom: 10px;}
    p, span, label, h1, h2, h3, div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. เมนูด้านข้าง
st.sidebar.title("🛠 เมนูระบบ")
menu = st.sidebar.selectbox("เลือกหน้าการทำงาน", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอด & สต็อก"])

# ==========================================
# หน้า 1: POS (หน้าขาย)
# ==========================================
if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS PROFESSIONAL POS")
    
    if df_products.empty:
        st.warning("⚠️ ไม่พบข้อมูลสินค้า กรุณาตรวจสอบลิงก์ Google Sheets")
    else:
        col_main, col_cart = st.columns([3.5, 1.5])
        
        with col_main:
            grid = st.columns(4)
            for i, row in df_products.iterrows():
                with grid[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div class="p-name">{row['Name']}</div>
                            <div class="p-price">{row['Price']:,} ฿</div>
                            <div style='color: #888; font-size: 0.8em;'>สต็อก: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"➕ เลือก", key=f"pos_btn_{i}"):
                        name, price = row['Name'], row['Price']
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': price, 'qty': 1}
                        st.rerun()

        with col_cart:
            st.subheader("🛒 ตะกร้า")
            if st.session_state.cart:
                total_sum = 0
                summary_list = []
                for name, info in list(st.session_state.cart.items()):
                    amt = info['price'] * info['qty']
                    total_sum += amt
                    summary_list.append(f"{name} x{info['qty']}")
                    
                    ca, cb = st.columns([3, 1])
                    with ca: st.write(f"**{name}** x{info['qty']}")
                    with cb:
                        if st.button("❌", key=f"del_cart_{name}"):
                            st.session_state.cart[name]['qty'] -= 1
                            if st.session_state.cart[name]['qty'] <= 0:
                                del st.session_state.cart[name]
                            st.rerun()
                
                st.divider()
                st.markdown(f"## รวม: {total_sum:,.2f} ฿")
                p_type = st.radio("วิธีชำระ:", ["เงินสด", "โอนเงิน"], horizontal=True)
                
                if st.button("✅ ยืนยันชำระเงิน", type="primary"):
                    # ส่งข้อมูลไป Sheets
                    try:
                        requests.get(f"{API_URL}?bill_id=B{pd.Timestamp.now().strftime('%M%S')}&items={summary_list}&total={total_sum}&payment_type={p_type}", timeout=0.1)
                    except:
                        pass
                    
                    # เก็บประวัติในแอป
                    st.session_state.sales_history.append({
                        "เวลา": pd.Timestamp.now().strftime("%H:%M"),
                        "ยอด": total_sum,
                        "ประเภท": p_type
                    })
                    st.session_state.cart = {}
                    st.success("บันทึกสำเร็จ!")
                    st.rerun()
            else:
                st.write("ยังไม่มีสินค้าในตะกร้า")

# ==========================================
# หน้า 2: Dashboard & Stock (หน้าสรุปยอด)
# ==========================================
else:
    st.title("📊 สรุปยอดขาย & สต็อก")
    
    # ส่วนยอดขาย
    if st.session_state.sales_history:
        df_h = pd.DataFrame(st.session_state.sales_history)
        h1, h2 = st.columns(2)
        with h1:
            st.markdown(f"<div class='metric-card'><h3>ยอดขายวันนี้</h3><h2>{df_h['ยอด'].sum():,.2f} ฿</h2></div>", unsafe_allow_html=True)
        with h2:
            st.markdown(f"<div class='metric-card'><h3>จำนวนบิล</h3><h2>{len(df_h)} รายการ</h2></div>", unsafe_allow_html=True)
        st.dataframe(df_h, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลการขายในขณะนี้")

    st.divider()
    
    # ส่วนสต็อก
    st.subheader("📦 ตรวจสอบสต็อก")
    if not df_products.empty:
        # ใช้ df_products โดยตรง ไม่เรียกจาก session_state เพื่อป้องกัน Error
        st.dataframe(df_products[['Name', 'Price', 'Stock']], use_container_width=True)
    else:
        st.write("ไม่พบข้อมูลสต็อกสินค้า")
