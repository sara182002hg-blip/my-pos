import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS & ADMIN", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูลแบบสด (ป้องกันข้อมูลหาย)
def get_fresh_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        if 'Stock' not in df.columns:
            df['Stock'] = 0
        return df
    except:
        return pd.DataFrame()

# 3. เคลียร์ Session State เก่าที่มีปัญหาทิ้งไปให้หมด
# บรรทัดนี้จะบังคับลบตัวแปร product_list ที่ทำให้เครื่องค้างครับ
if 'product_list' in st.session_state:
    del st.session_state['product_list']

if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

# 4. ดีไซน์หน้าจอ
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
    p, span, label, h1, h2, h3, div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. โหลดข้อมูลใหม่เข้าตัวแปรท้องถิ่น (ไม่เก็บใน session_state เพื่อเลี่ยง error)
products_df = get_fresh_data()

# 6. เมนู
menu = st.sidebar.radio("เลือกหน้า:", ["หน้าขาย (POS)", "สรุปยอด & สต็อก"])

if menu == "หน้าขาย (POS)":
    st.title("🏪 TAS POS")
    c1, c2 = st.columns([3.5, 1.5])
    
    with c1:
        if not products_df.empty:
            grid = st.columns(4)
            for i, row in products_df.iterrows():
                with grid[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div class="p-name">{row['Name']}</div>
                            <div class="p-price">{row['Price']:,} ฿</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"เลือก", key=f"btn_{i}"):
                        name, price = row['Name'], row['Price']
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': price, 'qty': 1}
                        st.rerun()
    
    with c2:
        st.subheader("🛒 ตะกร้า")
        total = 0
        for name, info in list(st.session_state.cart.items()):
            total += info['price'] * info['qty']
            st.write(f"{name} x{info['qty']}")
        st.markdown(f"### รวม: {total:,} ฿")
        if st.button("บันทึกการขาย", type="primary"):
            st.session_state.sales_history.append({"เวลา": pd.Timestamp.now(), "ยอด": total})
            st.session_state.cart = {}
            st.success("บันทึกแล้ว!")
            st.rerun()

else:
    st.title("📊 สรุปยอด & สต็อก")
    if st.session_state.sales_history:
        st.table(pd.DataFrame(st.session_state.sales_history))
    else:
        st.write("ยังไม่มีข้อมูลขาย")
    
    st.divider()
    st.subheader("📦 สต็อกสินค้า")
    st.dataframe(products_df[['Name', 'Price', 'Stock']], use_container_width=True)
