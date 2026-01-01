import streamlit as st
import pandas as pd
import requests
import plotly.express as px

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwu (URL ของคุณ)"

st.set_page_config(page_title="TAS POS & ADMIN", layout="wide")

# 2. CSS จัดการหน้าจอ
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
    .metric-card { background: #1a1c24; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; }
    p, span, label, h1, h2, h3, div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. ฟังก์ชันโหลดข้อมูลแบบบังคับ Refresh
def load_data_force():
    st.cache_data.clear() # ล้าง Cache เก่าทิ้งทั้งหมด
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        if 'Stock' not in df.columns: df['Stock'] = 0 # สร้างคอลัมน์หลอกถ้าไม่มี
        st.session_state.product_list = df
        st.success("อัปเดตข้อมูลสำเร็จ!")
    except:
        st.error("เชื่อมต่อข้อมูลไม่ได้")

# เตรียม Session State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'sales_history' not in st.session_state: st.session_state.sales_history = []
if 'product_list' not in st.session_state: load_data_force()

# --- แถบเมนูด้านข้าง ---
st.sidebar.title("🛠 ตั้งค่าระบบ")
if st.sidebar.button("🔄 ล้างระบบและโหลดใหม่"):
    load_data_force()
    st.rerun()

menu = st.sidebar.selectbox("เลือกหน้าการทำงาน", ["🛒 หน้าขายสินค้า (POS)", "📊 สรุปยอด & สต็อก"])

# ==========================================
# หน้า 1: POS
# ==========================================
if menu == "🛒 หน้าขายสินค้า (POS)":
    st.title("🏪 TAS PROFESSIONAL POS")
    col1, col2 = st.columns([3.5, 1.5])
    
    df = st.session_state.product_list
    with col1:
        grid = st.columns(4)
        for i, row in df.iterrows():
            with grid[i % 4]:
                st.markdown(f"""
                    <div class="product-card">
                        <div class="img-box"><img src="{row['Image_URL']}"></div>
                        <div class="p-name">{row['Name']}</div>
                        <div class="p-price">{row['Price']:,} ฿</div>
                        <div style='color: #888; font-size: 0.8em;'>สต็อก: {row['Stock']}</div>
                    </div>
                """, unsafe_allow_html=True)
                if st.button(f"➕ เลือก", key=f"add_{i}"):
                    name, price = row['Name'], row['Price']
                    if name in st.session_state.cart:
                        st.session_state.cart[name]['qty'] += 1
                    else:
                        st.session_state.cart[name] = {'price': price, 'qty': 1}
                    st.rerun()

    with col2:
        st.subheader("🛒 ตะกร้าสินค้า")
        if st.session_state.cart:
            total = 0
            current_items = []
            for name, info in list(st.session_state.cart.items()):
                item_total = info['price'] * info['qty']
                total += item_total
                current_items.append(f"{name} x{info['qty']}")
                
                c_a, c_b = st.columns([3, 1])
                with c_a: st.write(f"**{name}** x{info['qty']}")
                with c_b:
                    if st.button("❌", key=f"del_{name}"):
                        st.session_state.cart[name]['qty'] -= 1
                        if st.session_state.cart[name]['qty'] <= 0: del st.session_state.cart[name]
                        st.rerun()
            
            st.divider()
            st.markdown(f"## รวม: {total:,.2f} ฿")
            pay = st.radio("ชำระโดย:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
                # บันทึกประวัติ
                st.session_state.sales_history.append({
                    "เวลา": pd.Timestamp.now().strftime("%H:%M"),
                    "รายการ": ", ".join(current_items),
                    "ยอดรวม": total,
                    "ประเภท": pay
                })
                # ส่งข้อมูลไป Sheets
                try:
                    requests.get(f"{API_URL}?bill_id=B{pd.Timestamp.now().strftime('%M%S')}&items={current_items}&total={total}&payment_type={pay}", timeout=0.1)
                except: pass
                
                st.session_state.last_sale = {"total": total, "pay": pay}
                st.session_state.cart = {}
                st.rerun()
        
        elif 'last_sale' in st.session_state:
            st.success(f"ขายสำเร็จ! {st.session_state.last_sale['total']:,} ฿")
            if st.button("รับบิลใหม่"):
                del st.session_state.last_sale
                st.rerun()

# ==========================================
# หน้า 2: Dashboard & Stock
# ==========================================
else:
    st.title("📊 ระบบหลังบ้าน & สต็อก")
    
    # ส่วนสรุปยอด
    if st.session_state.sales_history:
        df_h = pd.DataFrame(st.session_state.sales_history)
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"<div class='metric-card'><h3>ยอดขายรวมวันนี้</h3><h2>{df_h['ยอดรวม'].sum():,.2f} ฿</h2></div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div class='metric-card'><h3>จำนวนบิล</h3><h2>{len(df_h)} บิล</h2></div>", unsafe_allow_html=True)
        
        fig = px.bar(df_h, x="เวลา", y="ยอดรวม", color="ประเภท", title="กราฟการขายรายช่วงเวลา")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ยังไม่มีข้อมูลการขาย")

    st.divider()
    
    # ส่วนสต็อก
    st.subheader("📦 ตารางสต็อกสินค้า")
    st.dataframe(st.session_state.product_list[['Name', 'Price', 'Stock']], use_container_width=True)
