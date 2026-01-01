import streamlit as st
import pandas as pd
import requests

# 1. ข้อมูลการเชื่อมต่อ
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"

st.set_page_config(page_title="TAS POS PROFESSIONAL", layout="wide")

# 2. ฟังก์ชันโหลดข้อมูล (เพิ่มระบบ Check คอลัมน์แบบเข้มงวด)
@st.cache_data(ttl=30) # ลดเวลาจำเหลือ 30 วินาทีเพื่อให้อัปเดตไวขึ้น
def load_stock_data():
    @st.cache_data(ttl=5) # ลดเวลาเหลือ 5 วินาทีเพื่อทดสอบ
def load_stock_data():
    try:
        # ดึงข้อมูลและห้ามใช้ Cache เก่า
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        
        # แสดงผลชั่วคราวเพื่อตรวจสอบ (เมื่อเลขมาแล้วค่อยลบบรรทัดนี้ออก)
        # st.write("คอลัมน์ที่พบ:", list(df.columns)) 
        
        if 'Stock' not in df.columns:
            st.error("⚠️ ไม่พบคอลัมน์ 'Stock' ในลิงก์ที่ระบุ กรุณาเช็คชื่อหัวตารางใน Sheets")
        
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce').fillna(0)
        df['Stock'] = pd.to_numeric(df['Stock'], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"❌ โหลดข้อมูลไม่ได้: {e}")
        return pd.DataFrame()
        return df
    except Exception as e:
        return pd.DataFrame(columns=['Name', 'Price', 'Stock', 'Image_URL'])

# 3. เตรียมตัวแปรระบบ
if 'pos_cart' not in st.session_state: st.session_state.pos_cart = {}
if 'pos_history' not in st.session_state: st.session_state.pos_history = []
if 'last_bill' not in st.session_state: st.session_state.last_bill = None

# ดึงข้อมูล
df_stock = load_stock_data()

# 4. เมนูด้านข้าง
st.sidebar.title("📦 ระบบจัดการ")
menu = st.sidebar.radio("เลือกเมนู", ["🛒 หน้าขาย (POS)", "📊 ยอดคงเหลือ & รายงาน"])

if st.sidebar.button("🔄 บังคับดึงข้อมูลใหม่"):
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
                    # ใช้ .get() เพื่อความปลอดภัยสูงสุด
                    name = row.get('Name', 'Unknown')
                    price = row.get('Price', 0)
                    stock = row.get('Stock', 0)
                    img = row.get('Image_URL', '')

                    stock_color = "red" if stock <= 5 else "#28a745"
                    
                    st.markdown(f"""
                        <div style="background-color:#1a1c24; border-radius:12px; border:1px solid #333; padding:10px; text-align:center; height:310px; margin-bottom:10px;">
                            <div style="width:100%; height:120px; background:white; border-radius:8px; display:flex; align-items:center; justify-content:center; overflow:hidden;">
                                <img src="{img}" style="max-width:90%; max-height:90%;">
                            </div>
                            <div style="font-weight:bold; margin-top:8px; color:white; font-size:1.1em;">{name}</div>
                            <div style="color:#f1c40f; font-weight:bold; font-size:1.2em;">{price:,.0f} ฿</div>
                            <div style="color:{stock_color}; font-size:0.9em; font-weight:bold;">คงเหลือ: {stock} ชิ้น</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    if stock > 0:
                        if st.button(f"เลือก {name}", key=f"btn_{i}"):
                            if name in st.session_state.pos_cart:
                                st.session_state.pos_cart[name]['qty'] += 1
                            else:
                                st.session_state.pos_cart[name] = {'price': price, 'qty': 1}
                            st.rerun()
                    else:
                        st.button("สินค้าหมด", key=f"btn_{i}", disabled=True)
        else:
            st.warning("กำลังโหลดข้อมูลสินค้า...")

    with col_cart:
        st.subheader("🛒 ตะกร้า")
        if st.session_state.pos_cart:
            total = 0
            for name, data in list(st.session_state.pos_cart.items()):
                subtotal = data['price'] * data['qty']
                total += subtotal
                c1, c2 = st.columns([3, 1])
                with c1: st.write(f"**{name}** x{data['qty']}")
                with c2: 
                    if st.button("❌", key=f"del_{name}"):
                        del st.session_state.pos_cart[name]
                        st.rerun()
            
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
        else:
            st.info("ยังไม่มีสินค้า")

# ==========================================
# หน้า 2: ยอดคงเหลือ & รายงาน
# ==========================================
else:
    st.title("📊 รายงานสต็อกสินค้า")
    if not df_stock.empty:
        # แสดงตารางสต็อก (ใช้คอลัมน์ที่เราดึงมา)
        st.dataframe(
            df_stock[['Name', 'Price', 'Stock']],
            column_config={
                "Name": "ชื่อสินค้า",
                "Price": st.column_config.NumberColumn("ราคา", format="%.2f"),
                "Stock": "คงเหลือ"
            },
            use_container_width=True, hide_index=True
        )
    else:
        st.warning("ไม่สามารถโหลดสต็อกได้")


