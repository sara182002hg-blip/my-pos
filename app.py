import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS PROFESSIONAL", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (บังคับโหลดใหม่เสมอเพื่อแก้ Error)
def get_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        if 'Stock' not in df.columns: df['Stock'] = 0
        return df
    except:
        return pd.DataFrame()

# 3. จัดการ Session State (จองชื่อตัวแปรให้ครบเพื่อกัน Error)
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'sales_history' not in st.session_state: st.session_state.sales_history = []
if 'product_list' not in st.session_state: st.session_state.product_list = get_data()

# 4. CSS จัดหน้าจอให้สวยและปุ่มชัดเจน
st.markdown("""
    <style>
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; text-align: center; height: 280px; margin-bottom: 5px;
    }
    .img-box { width: 100%; height: 130px; background: white; border-radius: 8px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; margin-top: 5px; height: 2.5em; overflow: hidden; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.1em; }
    .stButton > button { width: 100% !important; border-radius: 8px !important; }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. เมนูด้านข้าง
st.sidebar.title("🛠 เมนู")
menu = st.sidebar.selectbox("เลือกหน้า:", ["🛒 หน้าขาย (POS)", "📊 สรุปยอด & สต็อก"])
if st.sidebar.button("🔄 โหลดสินค้าใหม่"):
    st.session_state.product_list = get_data()
    st.rerun()

# ดึงข้อมูลจาก Session มาใช้ (กัน Error AttributeError)
df_products = st.session_state.product_list

# ==========================================
# หน้า 1: POS (หน้าขาย)
# ==========================================
if menu == "🛒 หน้าขาย (POS)":
    st.title("🏪 TAS PROFESSIONAL POS")
    col1, col2 = st.columns([3.5, 1.5])

    with col1:
        if not df_products.empty:
            grid = st.columns(4)
            for i, row in df_products.iterrows():
                with grid[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div class="p-name">{row['Name']}</div>
                            <div class="p-price">{row['Price']:,} ฿</div>
                            <div style="color:#888; font-size:0.8em;">สต็อก: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"➕ เลือก", key=f"add_{i}"):
                        name, price = row['Name'], row['Price']
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': price, 'qty': 1}
                        st.rerun()
        else: st.warning("ไม่พบข้อมูลสินค้า")

    with col2:
        st.subheader("🛒 รายการในตะกร้า")
        if st.session_state.cart:
            total = 0
            items_summary = []
            for name, info in list(st.session_state.cart.items()):
                sub_total = info['price'] * info['qty']
                total += sub_total
                items_summary.append(f"{name} x{info['qty']}")
                
                # ปุ่ม เพิ่ม/ลด/ลบ รายชิ้น
                c_item, c_btn = st.columns([2.5, 1.5])
                with c_item:
                    st.write(f"**{name}**")
                    st.caption(f"{info['qty']} x {info['price']:,} ฿")
                with c_btn:
                    b1, b2 = st.columns(2)
                    with b1:
                        if st.button("➕", key=f"inc_{name}"):
                            st.session_state.cart[name]['qty'] += 1
                            st.rerun()
                    with b2:
                        if st.button("❌", key=f"dec_{name}"):
                            st.session_state.cart[name]['qty'] -= 1
                            if st.session_state.cart[name]['qty'] <= 0: del st.session_state.cart[name]
                            st.rerun()
                st.divider()

            st.markdown(f"## รวม: :orange[{total:,.2f}] ฿")
            
            # วิธีชำระเงิน
            pay_type = st.radio("วิธีชำระ:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            if st.button("✅ ยืนยันชำระเงิน", type="primary"):
                # ส่งข้อมูลไป Sheets
                try: requests.get(f"{API_URL}?total={total}&type={pay_type}", timeout=0.1)
                except: pass
                
                # เก็บลงประวัติ
                st.session_state.sales_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": total, "ประเภท": pay_type})
                st.session_state.last_bill = {"total": total, "type": pay_type}
                st.session_state.cart = {}
                st.rerun()
            
            if st.button("🗑️ ล้างตะกร้าทั้งหมด"):
                st.session_state.cart = {}
                st.rerun()

        elif 'last_bill' in st.session_state:
            lb = st.session_state.last_bill
            st.success(f"บันทึกสำเร็จ {lb['total']:,} ฿")
            if lb['type'] == "โอนเงิน":
                st.image(f"https://promptpay.io/0945016189/{lb['total']}.png")
            if st.button("รับลูกค้าท่านต่อไป"):
                del st.session_state.last_bill
                st.rerun()
        else:
            st.write("เลือกสินค้าเพื่อเริ่มการขาย")

# ==========================================
# หน้า 2: สรุปยอด & สต็อก
# ==========================================
else:
    st.title("📊 ระบบหลังบ้าน")
    if st.session_state.sales_history:
        df_h = pd.DataFrame(st.session_state.sales_history)
        c1, c2 = st.columns(2)
        c1.metric("ยอดรวมวันนี้", f"{df_h['ยอด'].sum():,.2f} ฿")
        c2.metric("จำนวนบิล", f"{len(df_h)} รายการ")
        st.dataframe(df_h, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")
    
    st.divider()
    st.subheader("📦 ตรวจสอบสต็อก")
    st.dataframe(df_products[['Name', 'Price', 'Stock']], use_container_width=True)
