import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS PRO", layout="wide")

# 2. โหลดข้อมูลสินค้าแบบใช้ Cache เพื่อความเร็ว (ลดการกระตุกตอนโหลด)
@st.cache_data(ttl=600) # จำข้อมูลไว้ 10 นาที
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# 3. เตรียมตัวแปรระบบ
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'checkout_info' not in st.session_state: st.session_state.checkout_info = None

# ดึงข้อมูลสินค้า
df = load_data()

# 4. ปรับแต่ง UI
st.markdown("""
    <style>
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; text-align: center; height: 260px; transition: 0.3s;
    }
    .product-card:hover { border-color: #28a745; }
    .img-box { width: 100%; height: 120px; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. ฟังก์ชันเพิ่มสินค้า (ลดการใช้ rerun พร่ำเพรื่อ)
def add_to_cart(name, price):
    if name in st.session_state.pos_cart:
        st.session_state.pos_cart[name]['qty'] += 1
    else:
        st.session_state.pos_cart[name] = {'price': price, 'qty': 1}

# 6. เมนูด้านข้าง
menu = st.sidebar.radio("เมนู", ["🛒 POS", "📊 รายงาน"])
if st.sidebar.button("🔄 อัปเดตสต็อกสด"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# หน้า POS
# ==========================================
if menu == "🛒 POS":
    st.title("🏪 TAS POS SYSTEM")
    c1, c2 = st.columns([3.3, 1.7])

    with c1:
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
                    # ใช้ on_click เพื่อความลื่นไหล
                    st.button(f"เลือก {row['Name']}", key=f"add_{i}", 
                              on_click=add_to_cart, args=(row['Name'], row['Price']))
        else:
            st.warning("กำลังเชื่อมต่อข้อมูล...")

    with c2:
        st.subheader("🛒 รายการสินค้า")
        if st.session_state.pos_cart:
            total = 0
            for name, item in list(st.session_state.pos_cart.items()):
                total += item['price'] * item['qty']
                col_i, col_b = st.columns([3, 1.5])
                with col_i:
                    st.write(f"**{name}**")
                    st.caption(f"{item['qty']} x {item['price']:,} ฿")
                with col_b:
                    if st.button("❌", key=f"del_{name}"):
                        st.session_state.pos_cart[name]['qty'] -= 1
                        if st.session_state.pos_cart[name]['qty'] <= 0:
                            del st.session_state.pos_cart[name]
                        st.rerun()
            
            st.divider()
            st.markdown(f"## รวม: :orange[{total:,.2f}] ฿")
            
            method = st.radio("ชำระโดย:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
                st.session_state.pos_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": total, "วิธี": method})
                st.session_state.checkout_info = {"total": total, "method": method}
                try: requests.get(f"{API_URL}?total={total}&type={method}", timeout=0.1)
                except: pass
                st.session_state.pos_cart = {}
                st.rerun()

            if st.button("🗑️ ล้างตะกร้า"):
                st.session_state.pos_cart = {}
                st.rerun()

        elif st.session_state.checkout_info:
            info = st.session_state.checkout_info
            st.success(f"บันทึกสำเร็จ {info['total']:,} ฿")
            if info['method'] == "โอนเงิน":
                st.image(f"https://promptpay.io/0945016189/{info['total']}.png")
            if st.button("รับลูกค้าคนใหม่"):
                st.session_state.checkout_info = None
                st.rerun()
        else:
            st.info("ยังไม่มีสินค้า")

else:
    st.title("📊 รายงานยอดขาย")
    if st.session_state.pos_history:
        st.table(pd.DataFrame(st.session_state.pos_history))
    else:
        st.write("ไม่มีข้อมูล")
