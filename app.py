import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ (ตรวจสอบให้แน่ใจว่า SHEET_URL เชื่อมกับชีต Stock)
# หากคุณใช้การ Publish to web ให้เลือกชีต 'Stock' ก่อนคัดลอกลิงก์ CSV มานะครับ
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS POS PROFESSIONAL", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูลสินค้าและสต็อก
@st.cache_data(ttl=60) # อัปเดตข้อมูลทุก 1 นาที
def load_stock_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        # ตรวจสอบคอลัมน์สำคัญ
        for col in ['Name', 'Price', 'Stock']:
            if col not in df.columns:
                df[col] = 0 if col != 'Name' else "Unknown"
        return df
    except:
        return pd.DataFrame()

# 3. จัดการ Session State
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []

# ดึงข้อมูลล่าสุด
df_stock = load_stock_data()

# 4. เมนูด้านข้าง
st.sidebar.title("📦 ระบบจัดการ")
menu = st.sidebar.radio("เลือกเมนู", ["🛒 หน้าขาย (POS)", "📊 ยอดคงเหลือ & รายงาน"])

if st.sidebar.button("🔄 ดึงข้อมูลสต็อกล่าสุด"):
    st.cache_data.clear()
    st.rerun()

# ==========================================
# หน้า 1: POS (แสดงสต็อกใต้รูปสินค้า)
# ==========================================
if menu == "🛒 หน้าขาย (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col_products, col_cart = st.columns([3.3, 1.7])

    with col_products:
        if not df_stock.empty:
            grid = st.columns(4)
            for i, row in df_stock.iterrows():
                with grid[i % 4]:
                    # แสดงแจ้งเตือนถ้าสต็อกต่ำกว่า 5
                    stock_color = "red" if row['Stock'] <= 5 else "#888"
                    st.markdown(f"""
                        <div style="background-color: #1a1c24; border-radius: 12px; border: 1px solid #333; padding: 10px; text-align: center; height: 300px; margin-bottom: 10px;">
                            <div style="width: 100%; height: 120px; background: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden;">
                                <img src="{row['Image_URL']}" style="max-width: 90%; max-height: 90%;">
                            </div>
                            <div style="font-weight:bold; margin-top:5px; color:white;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-weight:bold;">{row['Price']:,} ฿</div>
                            <div style="color:{stock_color}; font-size:0.9em;">คงเหลือ: {row['Stock']}</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # ปุ่มเลือกซื้อ (ปิดปุ่มถ้าสต็อกหมด)
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
        else:
            st.error("ไม่สามารถโหลดข้อมูลได้ ตรวจสอบคอลัมน์ใน Sheets")

    # (ส่วนตะกร้าสินค้าเหมือนเดิม...)
    with col_cart:
        st.subheader("🛒 ตะกร้า")
        total = 0
        for name, item in list(st.session_state.pos_cart.items()):
            total += item['price'] * item['qty']
            st.write(f"**{name}** x{item['qty']} ({item['price'] * item['qty']:,} ฿)")
        st.divider()
        st.markdown(f"### รวม: :orange[{total:,}] ฿")
        if st.button("✅ ยืนยันการขาย", type="primary"):
            st.session_state.pos_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": total})
            st.session_state.pos_cart = {}
            st.success("บันทึกสำเร็จ!")
            st.rerun()

# ... (โค้ดส่วนบน หน้า POS ทั้งหมด) ...

# ==========================================
# หน้า 2: ยอดคงเหลือ & รายงาน
# ==========================================
else:
   else:
    st.title("📊 รายงานสต็อกสินค้า")
    
    # แก้ไขจาก load_products() เป็น load_stock_data() ให้ตรงกับชื่อฟังก์ชันด้านบน
    stock_df = load_stock_data()
    
    if not stock_df.empty:
        stock_df['Stock'] = pd.to_numeric(stock_df['Stock'], errors='coerce').fillna(0).astype(int)
        stock_df['Price'] = pd.to_numeric(stock_df['Price'], errors='coerce').fillna(0).astype(float)
            
        display_df = stock_df[['Name', 'Price', 'Stock']].copy()
        
        st.dataframe(
            display_df, 
            column_config={
                "Name": st.column_config.TextColumn("ชื่อสินค้า"),
                "Price": st.column_config.NumberColumn("ราคา (฿)", format="%.2f"),
                "Stock": st.column_config.NumberColumn(
                    "จำนวนสต็อกคงเหลือ",
                    help="จำนวนสินค้าที่เหลืออยู่ในชีต Stock",
                    format="%d 📦"
                ),
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("ไม่สามารถดึงข้อมูลสต็อกได้ กรุณาตรวจสอบลิงก์ Google Sheets")

