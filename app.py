import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS PROFESSIONAL", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (ไม่ใช้ Cache เพื่อความสดใหม่)
def load_products_fresh():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        if 'Stock' not in df.columns: df['Stock'] = 0
        return df
    except:
        return pd.DataFrame(columns=['Name', 'Price', 'Stock', 'Image_URL'])

# 3. ล้างชื่อตัวแปรเก่าที่มีปัญหา และตั้งชื่อใหม่ทั้งหมด
if 'main_cart' not in st.session_state: st.session_state.main_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'last_order' not in st.session_state: st.session_state.last_order = None

# โหลดข้อมูลสินค้าเข้าตัวแปรใหม่ทุกรอบที่รันเพื่อกัน Error
all_items = load_products_fresh()

# 4. CSS จัดรูปแบบปุ่มและหน้าตาให้ครบถ้วน
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
    .stButton > button[key^="dec_"], .stButton > button[key^="clear_"] { background-color: #ff4b4b !important; color: white !important; }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. แถบเมนูด้านข้าง
menu = st.sidebar.radio("เมนูใช้งาน", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอด & สต็อก"])
if st.sidebar.button("🔄 อัปเดตข้อมูลสินค้า"):
    st.rerun()

# ==========================================
# หน้า 1: POS (หน้าขาย)
# ==========================================
if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col1, col2 = st.columns([3.5, 1.5])

    with col1:
        if not all_items.empty:
            grid = st.columns(4)
            for i, row in all_items.iterrows():
                with grid[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div style="font-weight:bold; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f;">{row['Price']:,} ฿</div>
                            <div style="color:#888; font-size:0.8em;">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"➕ เลือก", key=f"add_p_{i}"):
                        name, price = row['Name'], row['Price']
                        if name in st.session_state.main_cart:
                            st.session_state.main_cart[name]['qty'] += 1
                        else:
                            st.session_state.main_cart[name] = {'price': price, 'qty': 1}
                        st.rerun()

    with col2:
        st.subheader("🛒 รายการสั่งซื้อ")
        if st.session_state.main_cart:
            total_price = 0
            for name, info in list(st.session_state.main_cart.items()):
                sub = info['price'] * info['qty']
                total_price += sub
                
                # แสดงรายการพร้อมปุ่ม ➕ และ ❌
                c_txt, c_btn = st.columns([2, 1.5])
                with c_txt:
                    st.write(f"**{name}**")
                    st.caption(f"{info['qty']} x {info['price']:,} ฿")
                with c_btn:
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("➕", key=f"inc_q_{name}"):
                            st.session_state.main_cart[name]['qty'] += 1
                            st.rerun()
                    with b2:
                        if st.button("❌", key=f"dec_q_{name}"):
                            st.session_state.main_cart[name]['qty'] -= 1
                            if st.session_state.main_cart[name]['qty'] <= 0: del st.session_state.main_cart[name]
                            st.rerun()
                st.divider()

            st.markdown(f"## รวมยอด: :orange[{total_price:,.2f}] ฿")
            
            # --- วิธีชำระเงิน ---
            payment_choice = st.radio("วิธีชำระเงิน:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย", type="primary"):
                # เก็บลงประวัติ
                st.session_state.pos_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": total_price, "ประเภท": payment_choice})
                st.session_state.last_order = {"total": total_price, "type": payment_choice}
                # ยิงข้อมูล (ถ้ามี)
                try: requests.get(f"{API_URL}?total={total_price}&pay={payment_choice}", timeout=0.1)
                except: pass
                
                st.session_state.main_cart = {}
                st.rerun()
            
            # --- ปุ่มล้างตะกร้า ---
            if st.button("🗑️ ล้างตะกร้าทั้งหมด", key="clear_all_items"):
                st.session_state.main_cart = {}
                st.rerun()

        elif st.session_state.last_order:
            order = st.session_state.last_order
            st.success(f"ชำระเงินสำเร็จ {order['total']:,} ฿")
            # --- QR Code ---
            if order['type'] == "โอนเงิน":
                st.image(f"https://promptpay.io/0945016189/{order['total']}.png")
            if st.button("รับบิลถัดไป"):
                st.session_state.last_order = None
                st.rerun()
        else:
            st.write("ยังไม่มีสินค้าในตะกร้า")

# ==========================================
# หน้า 2: สรุปยอด & สต็อก
# ==========================================
else:
    st.title("📊 สรุปยอดขาย & สต็อก")
    if st.session_state.pos_history:
        h_df = pd.DataFrame(st.session_state.pos_history)
        st.metric("ยอดรวมวันนี้", f"{h_df['ยอด'].sum():,.2f} ฿")
        st.dataframe(h_df, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลขาย")
    
    st.divider()
    st.subheader("📦 สต็อกสินค้าปัจจุบัน")
    st.dataframe(all_items[['Name', 'Price', 'Stock']], use_container_width=True)
