import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS PROFESSIONAL", layout="wide")

# 2. ฟังก์ชันจัดการข้อมูล
@st.cache_data(ttl=600)
def load_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# 3. เตรียมตัวแปรระบบ
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

# ฟังก์ชันสำหรับปุ่มกด (เพิ่ม/ลด/ลบ) เพื่อความลื่นไหล
def update_qty(name, price, action):
    if action == "add":
        if name in st.session_state.pos_cart:
            st.session_state.pos_cart[name]['qty'] += 1
        else:
            st.session_state.pos_cart[name] = {'price': price, 'qty': 1}
    elif action == "minus":
        if name in st.session_state.pos_cart:
            st.session_state.pos_cart[name]['qty'] -= 1
            if st.session_state.pos_cart[name]['qty'] <= 0:
                del st.session_state.pos_cart[name]

def clear_cart():
    st.session_state.pos_cart = {}

# 4. หน้าตาโปรแกรม (CSS)
st.markdown("""
    <style>
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; text-align: center; height: 270px; margin-bottom: 10px;
    }
    .img-box { width: 100%; height: 120px; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .stButton > button { width: 100% !important; border-radius: 8px !important; }
    /* ปุ่มลบ/ลดสีแดง */
    button[key*="minus"], button[key*="clear"] { background-color: #ff4b4b !important; color: white !important; }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. เมนูด้านข้าง
menu = st.sidebar.radio("เมนูใช้งาน", ["🛒 ขายสินค้า (POS)", "📊 ยอดขาย & สต็อก"])
if st.sidebar.button("🔄 อัปเดตข้อมูลจาก Sheets"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# หน้า 1: POS
# ==========================================
if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col_main, col_side = st.columns([3.3, 1.7])

    df = load_products()

    with col_main:
        if not df.empty:
            grid = st.columns(4)
            for i, row in df.iterrows():
                with grid[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div style="font-weight:bold; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f;">{row['Price']:,} ฿</div>
                        </div>
                    """, unsafe_allow_html=True)
                    st.button(f"เลือก {row['Name']}", key=f"p_{i}", 
                              on_click=update_qty, args=(row['Name'], row['Price'], "add"))

    with col_side:
        st.subheader("🛒 รายการในตะกร้า")
        
        if st.session_state.pos_cart:
            grand_total = 0
            for name, data in list(st.session_state.pos_cart.items()):
                sub = data['price'] * data['qty']
                grand_total += sub
                
                # แถวสินค้า
                c_name, c_btn = st.columns([2, 1.5])
                with c_name:
                    st.write(f"**{name}**")
                    st.caption(f"{data['qty']} x {data['price']:,} ฿")
                with c_btn:
                    # ปุ่ม ➕ และ ❌ (กลับมาแล้ว!)
                    b1, b2 = st.columns(2)
                    with b1: st.button("➕", key=f"plus_{name}", on_click=update_qty, args=(name, data['price'], "add"))
                    with b2: st.button("❌", key=f"minus_{name}", on_click=update_qty, args=(name, data['price'], "minus"))
                st.divider()

            st.markdown(f"## ยอดรวม: :orange[{grand_total:,.2f}] ฿")
            
            pay_val = st.radio("วิธีชำระเงิน:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
                st.session_state.pos_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": grand_total, "วิธี": pay_val})
                st.session_state.last_bill = {"total": grand_total, "method": pay_val}
                # ยิง API ไป Sheets
                try: requests.get(f"{API_URL}?total={grand_total}&pay={pay_val}", timeout=0.1)
                except: pass
                st.session_state.pos_cart = {}
                st.rerun()

            st.button("🗑️ ล้างตะกร้า", key="clear_cart", on_click=clear_cart)

        elif st.session_state.last_bill:
            bill = st.session_state.last_bill
            st.success(f"บันทึกสำเร็จ {bill['total']:,} ฿")
            if bill['method'] == "โอนเงิน":
                st.image(f"https://promptpay.io/0945016189/{bill['total']}.png")
            if st.button("เริ่มการขายใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.info("ยังไม่มีสินค้าในตะกร้า")

# ==========================================
# หน้า 2: ยอดขาย & สต็อก
# ==========================================
else:
    st.title("📊 รายงานวันนี้")
    if st.session_state.pos_history:
        log_df = pd.DataFrame(st.session_state.pos_history)
        st.metric("ยอดรวมทั้งหมด", f"{log_df['ยอด'].sum():,.2f} ฿")
        st.dataframe(log_df, use_container_width=True)
    else:
        st.write("ไม่มีข้อมูลการขาย")
