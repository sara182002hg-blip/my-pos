import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# 2. CSS บังคับสีปุ่ม (ปุ่มลบแดง ปุ่มยืนยันเขียว)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; text-align: center; height: 280px;
    }
    .img-box { width: 100%; height: 130px; background: white; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .stButton > button { width: 100% !important; border-radius: 8px !important; font-weight: bold !important; }
    /* ปรับแต่งปุ่มลบและล้างตะกร้าให้เป็นสีแดง */
    div[data-testid="stVerticalBlock"] > div:nth-child(2) button {  }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. ระบบจัดการข้อมูล (แบบไม่เก็บ Cache เพื่อให้ UI อัปเดตทันที)
def get_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        return df
    except:
        return pd.DataFrame()

# 4. บังคับสร้างตัวแปร Session (ถ้าไม่มีให้สร้างทันที)
if 'my_cart' not in st.session_state: st.session_state.my_cart = {}
if 'sales_log' not in st.session_state: st.session_state.sales_log = []
if 'order_finish' not in st.session_state: st.session_state.order_finish = None

# --- โหลดข้อมูลสินค้า ---
items_df = get_products()

# 5. เมนูด้านข้าง
st.sidebar.title("MENU")
page = st.sidebar.radio("เลือกหน้า:", ["หน้าขายสินค้า", "หลังบ้าน/สต็อก"])

# ==========================================
# หน้า 1: POS (คืนชีพปุ่มและวิธีชำระเงิน)
# ==========================================
if page == "หน้าขายสินค้า":
    st.title("🏪 TAS POS (v2.0)")
    c1, c2 = st.columns([3.2, 1.8])

    with c1:
        if not items_df.empty:
            grid = st.columns(4)
            for i, row in items_df.iterrows():
                with grid[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div style="font-weight:bold; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f;">{row['Price']:,} ฿</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"เลือกสินค้า", key=f"add_{i}_{row['Name']}"):
                        name = row['Name']
                        if name in st.session_state.my_cart:
                            st.session_state.my_cart[name]['qty'] += 1
                        else:
                            st.session_state.my_cart[name] = {'price': row['Price'], 'qty': 1}
                        st.rerun()

    with c2:
        st.subheader("🛒 รายการที่เลือก")
        
        # แสดงตะกร้าสินค้า
        if st.session_state.my_cart:
            total_amount = 0
            for name, data in list(st.session_state.my_cart.items()):
                subtotal = data['price'] * data['qty']
                total_amount += subtotal
                
                # แสดงแถวสินค้า: ชื่อ | ราคา | ปุ่มลด
                col_n, col_p, col_b = st.columns([2, 1, 1])
                with col_n: st.write(f"**{name}**")
                with col_p: st.write(f"x{data['qty']}")
                with col_b:
                    if st.button("❌ ลบ", key=f"del_{name}"):
                        st.session_state.my_cart[name]['qty'] -= 1
                        if st.session_state.my_cart[name]['qty'] <= 0:
                            del st.session_state.my_cart[name]
                        st.rerun()
            
            st.divider()
            st.markdown(f"## ยอดรวม: :orange[{total_amount:,.2f}] ฿")
            
            # --- ฟีเจอร์ที่หายไป: วิธีชำระเงิน ---
            st.write("### 💳 วิธีชำระเงิน")
            pay_method = st.radio("เลือกการชำระ:", ["เงินสด", "โอนเงินผ่าน QR"], horizontal=True)
            
            # --- ปุ่มยืนยันการขาย ---
            if st.button("✅ ยืนยันและพิมพ์บิล", type="primary", use_container_width=True):
                st.session_state.sales_log.append({
                    "เวลา": pd.Timestamp.now().strftime("%H:%M"),
                    "ยอด": total_amount,
                    "วิธี": pay_method
                })
                st.session_state.order_finish = {"total": total_amount, "method": pay_method}
                st.session_state.my_cart = {} # ล้างตะกร้า
                st.rerun()
                
            # --- ปุ่มล้างตะกร้า ---
            if st.button("🗑️ ล้างตะกร้าทั้งหมด"):
                st.session_state.my_cart = {}
                st.rerun()

        # --- ฟีเจอร์ที่หายไป: QR Code หลังชำระเงิน ---
        elif st.session_state.order_finish:
            res = st.session_state.order_finish
            st.success(f"บันทึกยอดขาย {res['total']:,} ฿ เรียบร้อย!")
            if "QR" in res['method']:
                st.write("📸 **สแกนเพื่อจ่ายเงิน:**")
                st.image(f"https://promptpay.io/0945016189/{res['total']}.png")
            
            if st.button("🔄 รับลูกค้าใหม่"):
                st.session_state.order_finish = None
                st.rerun()
        else:
            st.info("ยังไม่มีสินค้าในตะกร้า")

# ==========================================
# หน้า 2: สรุปยอด & สต็อก
# ==========================================
else:
    st.title("📊 สรุปยอดวันนี้ & สต็อก")
    if st.session_state.sales_log:
        df_log = pd.DataFrame(st.session_state.sales_log)
        st.metric("ยอดขายรวม", f"{df_log['ยอด'].sum():,.2f} ฿")
        st.dataframe(df_log, use_container_width=True)
    else:
        st.write("ไม่มีข้อมูลยอดขาย")
    
    st.divider()
    st.subheader("📦 สต็อกสินค้า")
    st.dataframe(items_df[['Name', 'Price']], use_container_width=True)
