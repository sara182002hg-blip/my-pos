import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
# ตรวจสอบว่า SHEET_URL เชื่อมกับชีต Stock ที่ Publish เป็น CSV แล้ว
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูลสินค้าและสต็อก
@st.cache_data(ttl=60)
def load_stock_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        # ทำความสะอาดข้อมูลตัวเลข
        if 'Stock' in df.columns:
            df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        if 'Price' in df.columns:
            df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0).astype(float)
        return df
    except:
        return pd.DataFrame()

# 3. เตรียมตัวแปรระบบ
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

# ดึงข้อมูลล่าสุด
df_stock = load_stock_data()

# 4. หน้าตาโปรแกรม (CSS)
st.markdown("""
    <style>
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; text-align: center; height: 300px; margin-bottom: 10px;
    }
    .img-box { width: 100%; height: 120px; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .stButton > button { width: 100% !important; border-radius: 8px !important; }
    p, span, div, h1, h2, h3 { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 5. เมนูด้านข้าง
st.sidebar.title("📦 ระบบจัดการ")
menu = st.sidebar.radio("เลือกเมนู", ["🛒 หน้าขาย (POS)", "📊 ยอดคงเหลือ & รายงาน"])

if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# หน้า 1: POS
# ==========================================
if menu == "🛒 หน้าขาย (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col_products, col_cart = st.columns([3.3, 1.7])

    with col_products:
        if not df_stock.empty:
            grid = st.columns(4)
            for i, row in df_stock.iterrows():
                with grid[i % 4]:
                    stock_color = "red" if row['Stock'] <= 5 else "#888"
                    st.markdown(f"""
                        <div class="product-card">
                            <div class="img-box"><img src="{row['Image_URL']}"></div>
                            <div style="font-weight:bold; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f;">{row['Price']:,} ฿</div>
                            <div style="color:{stock_color}; font-size:0.9em;">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"p_{i}"):
                            name = row['Name']
                            if name in st.session_state.pos_cart:
                                st.session_state.pos_cart[name]['qty'] += 1
                            else:
                                st.session_state.pos_cart[name] = {'price': row['Price'], 'qty': 1}
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"p_{i}", disabled=True)

    with col_cart:
        st.subheader("🛒 รายการในตะกร้า")
        if st.session_state.pos_cart:
            total = 0
            for name, data in list(st.session_state.pos_cart.items()):
                total += data['price'] * data['qty']
                c_n, c_b = st.columns([3, 1])
                with c_n: st.write(f"**{name}** x{data['qty']}")
                with c_b: 
                    if st.button("❌", key=f"del_{name}"):
                        del st.session_state.pos_cart[name]
                        st.rerun()
            
            st.divider()
            st.markdown(f"## รวม: :orange[{total:,}] ฿")
            
            pay_type = st.radio("วิธีชำระ:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
                st.session_state.pos_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": total, "วิธี": pay_type})
                st.session_state.last_bill = {"total": total, "method": pay_type}
                st.session_state.pos_cart = {}
                st.rerun()
        
        elif st.session_state.last_bill:
            bill = st.session_state.last_bill
            st.success(f"ขายสำเร็จ {bill['total']:,} ฿")
            if bill['method'] == "โอนเงิน":
                st.image(f"https://promptpay.io/0945016189/{bill['total']}.png")
            if st.button("เริ่มการขายใหม่"):
                st.session_state.last_bill = None
                st.rerun()
        else:
            st.info("กรุณาเลือกสินค้า")

# ==========================================
# หน้า 2: ยอดคงเหลือ & รายงาน (แก้ไขส่วนที่ Error)
# ==========================================
else:
    st.title("📊 รายงานสต็อกสินค้า")
    
    # ตรวจสอบความถูกต้องของข้อมูลก่อนแสดงตาราง
    if not df_stock.empty:
        st.subheader("📦 จำนวนสินค้าคงเหลือปัจจุบัน")
        
        # เลือกเฉพาะคอลัมน์ที่มีในชีต Stock จริงๆ
        display_df = df_stock[['Name', 'Price', 'Stock']].copy()
        
        st.dataframe(
            display_df, 
            column_config={
                "Name": "ชื่อสินค้า",
                "Price": st.column_config.NumberColumn("ราคา (฿)", format="%.2f"),
                "Stock": st.column_config.NumberColumn("คงเหลือ", format="%d 📦")
            },
            use_container_width=True,
            hide_index=True
        )
        
        # แสดงยอดขายวันนี้
        st.divider()
        st.subheader("📝 ประวัติการขายวันนี้")
        if st.session_state.pos_history:
            st.table(pd.DataFrame(st.session_state.pos_history))
        else:
            st.write("ยังไม่มีข้อมูลการขาย")
    else:
        st.warning("ไม่สามารถโหลดข้อมูลสต็อกได้ ตรวจสอบลิงก์ Google Sheets")
