import streamlit as st
import pandas as pd
import time

# 1. ข้อมูลการเชื่อมต่อ
FILE_ID = "1XqL_8rB3vUa6I6N6_uLz7G_7fPjG0r_D-uB4fP5Y6X0"
GID = "228640428"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{FILE_ID}/export?format=csv&gid={GID}"

st.set_page_config(page_title="TAS POS SYSTEM", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล
@st.cache_data(ttl=5)
def load_stock_data():
    try:
        fresh_url = f"{SHEET_URL}&t={int(time.time())}"
        df = pd.read_csv(fresh_url)
        df.columns = df.columns.str.strip()
        for col in ['Name', 'Price', 'Stock', 'Image_URL']:
            if col not in df.columns:
                df[col] = 0 if col in ['Price', 'Stock'] else ""
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except:
        return pd.DataFrame()

# 3. เตรียมตัวแปร
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

df_stock = load_stock_data()

# 4. เมนูด้านข้าง
st.sidebar.title("📦 ระบบจัดการ")
menu = st.sidebar.radio("เลือกเมนู", ["🛒 หน้าขาย (POS)", "📊 รายงานสต็อก"])

if st.sidebar.button("🔄 ดึงข้อมูลล่าสุด"):
    st.cache_data.clear()
    st.rerun()

# 5. หน้าขาย (POS)
if menu == "🛒 หน้าขาย (POS)":
    st.title("🏪 TAS POS SYSTEM")
    col_p, col_c = st.columns([3, 2])
    with col_p:
        if not df_stock.empty:
            grid = st.columns(3)
            for i, row in df_stock.iterrows():
                with grid[i % 3]:
                    st.markdown(f"""
                        <div style="background:#1a1c24; border:1px solid #333; padding:10px; border-radius:10px; text-align:center; margin-bottom:10px;">
                            <img src="{row['Image_URL']}" style="height:100px; object-fit:contain; background:white; border-radius:5px; padding:5px;">
                            <div style="font-weight:bold; color:white; margin-top:5px;">{row['Name']}</div>
                            <div style="color:#f1c40f; font-size:1.2em;">{row['Price']:,.0f} ฿</div>
                            <div style="color:{'#2ecc71' if row['Stock'] > 0 else '#e74c3c'}; font-size:0.9em;">คงเหลือ: {row['Stock']} ชิ้น</div>
                        </div>
                    """, unsafe_allow_html=True)
                    if row['Stock'] > 0:
                        if st.button(f"เลือก {row['Name']}", key=f"sel_{i}"):
                            name = row['Name']
                            if name in st.session_state.pos_cart:
                                st.session_state.pos_cart[name]['qty'] += 1
                            else:
                                st.session_state.pos_cart[name] = {'price': row['Price'], 'qty': 1}
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"sel_{i}", disabled=True)
    with col_c:
        st.subheader("🛒 รายการซื้อ")
        if st.session_state.pos_cart:
            total = 0
            for name, item in list(st.session_state.pos_cart.items()):
                total += item['price'] * item['qty']
                c1, c2 = st.columns([3, 1])
                with c1: st.write(f"**{name}** x{item['qty']}")
                with c2: 
                    if st.button("❌", key=f"del_{name}"):
                        del st.session_state.pos_cart[name]
                        st.rerun()
            st.divider()
            st.markdown(f"### รวม: :orange[{total:,.2f}] ฿")
            if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
                st.session_state.pos_history.append({"เวลา": pd.Timestamp.now().strftime("%H:%M"), "ยอด": total})
                st.session_state.last_bill = {"total": total}
                st.session_state.pos_cart = {}
                st.rerun()
        elif st.session_state.last_bill:
            st.success(f"ขายสำเร็จยอด {st.session_state.last_bill['total']:,} ฿")
            if st.button("เริ่มการขายใหม่"):
                st.session_state.last_bill = None
                st.rerun()

# 6. หน้าแสดงสต็อก
else:
    st.title("📊 รายงานสต็อกสินค้า")
    if not df_stock.empty:
        st.dataframe(df_stock[['Name', 'Price', 'Stock']], use_container_width=True, hide_index=True)
