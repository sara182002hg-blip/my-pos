import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (ใส่ Try-Except คลุมไว้ทั้งหมด)
def load_data_safe():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        if 'Stock' not in df.columns:
            df['Stock'] = 0
        return df
    except:
        return pd.DataFrame(columns=['Name', 'Price', 'Stock', 'Image_URL'])

# 3. ตรวจสอบและซ่อมแซม Session State ทุกครั้งที่รัน
# แก้ปัญหา AttributeError โดยการ "จองชื่อตัวแปร" ไว้ก่อน
if 'product_list' not in st.session_state:
    st.session_state.product_list = load_data_safe()
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'sales_history' not in st.session_state:
    st.session_state.sales_history = []

# 4. เมนูด้านข้าง
st.sidebar.title("⚙️ ตั้งค่า")
# ปุ่มบังคับโหลดข้อมูลใหม่ (กรณีข้อมูลในหน้าจอไม่เปลี่ยน)
if st.sidebar.button("🔄 บังคับโหลดข้อมูลใหม่"):
    st.session_state.product_list = load_data_safe()
    st.cache_data.clear()
    st.rerun()

menu = st.sidebar.selectbox("เลือกหน้า:", ["🛒 ขายสินค้า (POS)", "📊 สรุปยอด & สต็อก"])

# ดึงข้อมูลมาใส่ตัวแปรใช้งาน
df = st.session_state.product_list

# 5. ดีไซน์ (CSS)
st.markdown("""
    <style>
    .product-card {
        background-color: #1a1c24; border-radius: 10px; border: 1px solid #444;
        padding: 10px; text-align: center; margin-bottom: 10px;
    }
    .img-box { width: 100%; height: 120px; background: white; border-radius: 5px; overflow: hidden; display: flex; align-items: center; justify-content: center; }
    .img-box img { max-width: 90%; max-height: 90%; }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# หน้า 1: POS
# ==========================================
if menu == "🛒 ขายสินค้า (POS)":
    st.title("🏪 TAS PROFESSIONAL POS")
    
    col_main, col_cart = st.columns([3.5, 1.5])
    
    with col_main:
        if df.empty:
            st.error("❌ ไม่สามารถโหลดข้อมูลสินค้าได้ กรุณากดปุ่ม 'โหลดข้อมูลใหม่' ที่เมนูด้านข้าง")
        else:
            cols = st.columns(4)
            for i, row in df.iterrows():
                with cols[i % 4]:
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div style="font-weight: bold; margin-top:5px;">{row['Name']}</div>
                            <div style="color: #f1c40f !important;">{row['Price']:,} ฿</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button(f"เลือก", key=f"add_{i}"):
                        name, price = row['Name'], row['Price']
                        if name in st.session_state.cart:
                            st.session_state.cart[name]['qty'] += 1
                        else:
                            st.session_state.cart[name] = {'price': price, 'qty': 1}
                        st.rerun()

    with col_cart:
        st.subheader("🛒 รายการ")
        total = 0
        for name, info in list(st.session_state.cart.items()):
            total += info['price'] * info['qty']
            st.write(f"**{name}** x{info['qty']}")
            if st.button("ลบ", key=f"del_{name}"):
                del st.session_state.cart[name]
                st.rerun()
        
        st.divider()
        st.write(f"### รวม: {total:,} ฿")
        if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
            st.session_state.sales_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": total})
            # ส่งข้อมูลไป Sheets (Optional)
            try: requests.get(f"{API_URL}?total={total}", timeout=0.1)
            except: pass
            st.session_state.cart = {}
            st.success("บันทึกสำเร็จ!")
            st.rerun()

# ==========================================
# หน้า 2: Dashboard & Stock
# ==========================================
else:
    st.title("📊 สรุปยอด & สต็อก")
    
    # สรุปยอด
    if st.session_state.sales_history:
        sh_df = pd.DataFrame(st.session_state.sales_history)
        st.metric("ยอดขายรวมวันนี้", f"{sh_df['ยอด'].sum():,} ฿")
        st.table(sh_df)
    else:
        st.info("ยังไม่มีข้อมูลยอดขาย")
        
    st.divider()
    
    # สต็อก
    st.subheader("📦 สินค้าคงเหลือ")
    st.table(df[['Name', 'Stock']])
