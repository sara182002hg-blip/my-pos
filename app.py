import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล
def get_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        if 'Stock' not in df.columns: df['Stock'] = 0
        return df
    except:
        return pd.DataFrame()

# --- [หัวใจสำคัญ] ล้างค่าเก่าที่ทำให้ปุ่มหาย ---
# หากยังใช้ชื่อเดิม ระบบจะไม่ยอมอัปเดต UI ผมจึงเปลี่ยนชื่อตัวแปรใหม่หมดครับ
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'checkout_step' not in st.session_state: st.session_state.checkout_step = None

# ดึงข้อมูลสินค้ามาเตรียมไว้
product_data = get_products()

# 3. จัดการความสวยงาม (CSS)
st.markdown("""
    <style>
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; text-align: center; height: 280px; margin-bottom: 5px;
    }
    .img-box { width: 100%; height: 130px; background: white; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .stButton > button { width: 100% !important; border-radius: 8px !important; font-weight: bold !important; }
    /* ปุ่มลบสีแดง */
    div.stButton > button:contains("❌") { background-color: #ff4b4b !important; color: white !important; }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 4. เมนูด้านข้าง
page = st.sidebar.radio("เมนูหลัก", ["🛒 ขายสินค้า (POS)", "📊 ยอดขาย & สต็อก"])

# ==========================================
# หน้า 1: POS (กู้คืนทุกปุ่ม)
# ==========================================
if page == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col_products, col_cart = st.columns([3.3, 1.7])

    with col_products:
        if not product_data.empty:
            grid = st.columns(4)
            for i, row in product_data.iterrows():
                with grid[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div style="font-weight:bold; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f;">{row['Price']:,} ฿</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"เลือก", key=f"btn_add_{i}"):
                        name = row['Name']
                        if name in st.session_state.pos_cart:
                            st.session_state.pos_cart[name]['qty'] += 1
                        else:
                            st.session_state.pos_cart[name] = {'price': row['Price'], 'qty': 1}
                        st.rerun()

    with col_cart:
        st.subheader("🛒 รายการสินค้า")
        
        if st.session_state.pos_cart:
            total_price = 0
            for name, item in list(st.session_state.pos_cart.items()):
                sub = item['price'] * item['qty']
                total_price += sub
                
                # แสดงแถวสินค้า + ปุ่มเพิ่ม/ลด
                c_info, c_btns = st.columns([2.5, 1.5])
                with c_info:
                    st.write(f"**{name}**")
                    st.caption(f"{item['qty']} x {item['price']:,} ฿")
                with c_btns:
                    b_inc, b_dec = st.columns(2)
                    with b_inc: 
                        if st.button("➕", key=f"inc_{name}"):
                            st.session_state.pos_cart[name]['qty'] += 1
                            st.rerun()
                    with b_dec:
                        if st.button("❌", key=f"dec_{name}"):
                            st.session_state.pos_cart[name]['qty'] -= 1
                            if st.session_state.pos_cart[name]['qty'] <= 0: del st.session_state.pos_cart[name]
                            st.rerun()
                st.divider()

            st.markdown(f"## ยอดรวม: :orange[{total_price:,.2f}] ฿")
            
            # --- วิธีชำระเงิน (กลับมาแล้ว) ---
            st.write("### 💳 วิธีชำระเงิน")
            pay_type = st.radio("เลือก:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            # --- ปุ่มยืนยันการขาย ---
            if st.button("✅ ยืนยันชำระเงิน", type="primary", use_container_width=True):
                st.session_state.pos_history.append({
                    "เวลา": pd.Timestamp.now().strftime("%H:%M"),
                    "ยอด": total_price,
                    "วิธี": pay_type
                })
                st.session_state.checkout_step = {"total": total_price, "type": pay_type}
                
                # ส่งข้อมูลไป Sheets
                try: requests.get(f"{API_URL}?total={total_price}&pay={pay_type}", timeout=0.1)
                except: pass
                
                st.session_state.pos_cart = {} # ล้างตะกร้า
                st.rerun()
            
            # --- ปุ่มล้างตะกร้า ---
            if st.button("🗑️ ล้างตะกร้าทั้งหมด"):
                st.session_state.pos_cart = {}
                st.rerun()

        # --- แสดง QR Code หลังกดชำระเงิน ---
        elif st.session_state.checkout_step:
            res = st.session_state.checkout_step
            st.success(f"ชำระเงินสำเร็จ {res['total']:,} ฿")
            if res['type'] == "โอนเงิน":
                st.write("📸 **สแกนเพื่อจ่ายเงิน:**")
                # สร้าง QR PromptPay อัตโนมัติ (เปลี่ยนเลขบัญชีได้ที่นี่)
                st.image(f"https://promptpay.io/0945016189/{res['total']}.png")
            
            if st.button("รับลูกค้าคนใหม่"):
                st.session_state.checkout_step = None
                st.rerun()
        else:
            st.info("กรุณาเลือกสินค้าจากด้านซ้าย...")

# ==========================================
# หน้า 2: สรุปยอด & สต็อก
# ==========================================
else:
    st.title("📊 สรุปยอดขาย & สต็อก")
    if st.session_state.pos_history:
        log_df = pd.DataFrame(st.session_state.pos_history)
        st.metric("ยอดขายรวมวันนี้", f"{log_df['ยอด'].sum():,.2f} ฿")
        st.table(log_df)
    else:
        st.write("ยังไม่มีข้อมูลขาย")
    
    st.divider()
    st.subheader("📦 สต็อกสินค้าปัจจุบัน")
    st.dataframe(product_data[['Name', 'Price', 'Stock']], use_container_width=True)
