import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS PROFESSIONAL", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (เพิ่มระบบป้องกัน KeyError)
@st.cache_data(ttl=60)
def load_stock_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip() # ลบช่องว่างหัวตาราง
        
        # ตรวจสอบคอลัมน์: ถ้าหาไม่เจอ ให้สร้างคอลัมน์ว่างขึ้นมาป้องกัน Error
        if 'Name' not in df.columns: df['Name'] = "ไม่มีชื่อสินค้า"
        if 'Price' not in df.columns: df['Price'] = 0
        if 'Stock' not in df.columns: df['Stock'] = 0
        if 'Image_URL' not in df.columns: df['Image_URL'] = ""
        
        # แปลงข้อมูลเป็นตัวเลข
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        
        return df
    except Exception as e:
        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
        return pd.DataFrame()

# 3. เตรียมตัวแปรระบบ
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

# ดึงข้อมูลล่าสุดมาเก็บไว้
df_stock = load_stock_data()

# 4. เมนูด้านข้าง
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
                    # ใช้ .get() เพื่อป้องกัน KeyError ซ้อน
                    stock_val = row.get('Stock', 0)
                    price_val = row.get('Price', 0)
                    name_val = row.get('Name', "Unknown")
                    img_url = row.get('Image_URL', "")
                    
                    stock_color = "red" if stock_val <= 5 else "#888"
                    
                    st.markdown(f"""
                        <div style="background-color:#1a1c24; border-radius:12px; border:1px solid #333; padding:10px; text-align:center; height:300px; margin-bottom:10px;">
                            <div style="width:100%; height:120px; background:white; border-radius:8px; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                                <img src="{img_url}" style="max-width:90%; max-height:90%;">
                            </div>
                            <div style="font-weight:bold; margin-top:5px; color:white;">{name_val}</div>
                            <div style="color:#f1c40f; font-weight:bold;">{price_val:,.2f} ฿</div>
                            <div style="color:{stock_color}; font-size:0.9em;">คงเหลือ: {stock_val}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if stock_val > 0:
                        if st.button(f"เลือก {name_val}", key=f"btn_{i}"):
                            if name_val in st.session_state.pos_cart:
                                st.session_state.pos_cart[name_val]['qty'] += 1
                            else:
                                st.session_state.pos_cart[name_val] = {'price': price_val, 'qty': 1}
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"btn_{i}", disabled=True)

    with col_cart:
        st.subheader("🛒 ตะกร้า")
        if st.session_state.pos_cart:
            total = 0
            for name, data in list(st.session_state.pos_cart.items()):
                total += data['price'] * data['qty']
                st.write(f"**{name}** x{data['qty']}")
            
            st.divider()
            st.markdown(f"## รวม: :orange[{total:,.2f}] ฿")
            
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
            if st.button("ลูกค้าใหม่"):
                st.session_state.last_bill = None
                st.rerun()

# ==========================================
# หน้า 2: ยอดคงเหลือ & รายงาน
# ==========================================
else:
    st.title("📊 รายงานสรุปสต็อก")
    if not df_stock.empty:
        st.dataframe(
            df_stock[['Name', 'Price', 'Stock']],
            column_config={
                "Name": "ชื่อสินค้า",
                "Price": st.column_config.NumberColumn("ราคา", format="%.2f"),
                "Stock": "จำนวนคงเหลือ"
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.warning("ไม่มีข้อมูลสต็อก")
