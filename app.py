import streamlit as st
import pandas as pd
import requests
import plotly.express as px # สำหรับวาดกราฟ

# 1. ข้อมูลการเชื่อมต่อ
API_URL = "https://script.google.com/macros/s/AKfycbxwm0SVcvcm327H-zdEIa7RCM6I5HwWst9UtXqRU_gvoiBXeZkVrxczLUDIFHVvrw_z/exec"
# *หมายเหตุ: ในระบบสต็อกจริง ควรมีคอลัมน์ 'Stock' ใน Google Sheets ของคุณด้วยครับ
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="TAS PROFESSIONAL POS & ADMIN", layout="wide")

# 2. CSS เดิม + เพิ่มสไตล์ Dashboard
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .product-card {
        background-color: #1a1c24; border-radius: 12px; border: 1px solid #333;
        padding: 10px; margin-bottom: 5px; display: flex; flex-direction: column;
        align-items: center; height: 260px; justify-content: space-between;
    }
    .img-box {
        width: 100%; height: 140px; background-color: white; border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        overflow: hidden;
    }
    .img-box img { max-width: 90%; max-height: 90%; object-fit: contain; }
    .p-name { color: white !important; font-weight: bold; text-align: center; font-size: 0.9em; }
    .p-price { color: #f1c40f !important; font-weight: bold; font-size: 1.1em; }
    .stButton > button { width: 100% !important; border-radius: 8px !important; font-weight: bold !important; }
    /* Dashboard Style */
    .metric-box {
        background-color: #1a1c24; padding: 20px; border-radius: 10px; 
        border-left: 5px solid #28a745; margin-bottom: 10px;
    }
    p, span, label, h1, h2, h3, div { color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 3. ฟังก์ชันโหลดข้อมูลและจัดการ Session
@st.cache_data(ttl=60)
def get_products():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        # ถ้าไม่มีคอลัมน์ Stock ให้จำลองขึ้นมา (ในการใช้งานจริงให้เพิ่มใน Google Sheets ครับ)
        if 'Stock' not in df.columns:
            df['Stock'] = 50 
        return df
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'sales_history' not in st.session_state: st.session_state.sales_history = []

# --- ส่วนเมนูหลัก ---
menu = st.sidebar.radio("เมนูหลัก", ["🛒 หน้าขายสินค้า (POS)", "📊 สรุปยอดขาย & สต็อก"], index=0)

# ==========================================
# 🛒 ส่วนที่ 1: หน้าขายสินค้า (POS)
# ==========================================
if menu == "🛒 หน้าขายสินค้า (POS)":
    df_products = get_products()
    st.title("🏪 TAS PROFESSIONAL POS")
    
    col_main, col_cart = st.columns([3.8, 1.2])

    with col_main:
        if not df_products.empty:
            rows = [df_products[i:i + 4] for i in range(0, df_products.shape[0], 4)]
            for row_data in rows:
                cols = st.columns(4)
                for idx, (i, row) in enumerate(row_data.iterrows()):
                    with cols[idx]:
                        st.markdown(f"""
                            <div class="product-card">
                                <div class="img-box"><img src="{row['Image_URL']}"></div>
                                <div class="p-name">{row['Name']}</div>
                                <div class="p-price">{row['Price']:,} ฿</div>
                                <div style='color: #aaa; font-size: 0.8em;'>คงเหลือ: {row['Stock']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        if st.button(f"➕ เลือก", key=f"add_{i}"):
                            name, price = row['Name'], row['Price']
                            if name in st.session_state.cart:
                                st.session_state.cart[name]['qty'] += 1
                            else:
                                st.session_state.cart[name] = {'price': price, 'qty': 1}
                            st.rerun()
        else: st.error("ไม่สามารถดึงข้อมูลสินค้าได้")

    with col_cart:
        st.subheader("🛒 ตะกร้า")
        if st.session_state.cart:
            total = 0
            items_summary = []
            for name, info in list(st.session_state.cart.items()):
                subtotal = info['price'] * info['qty']
                total += subtotal
                items_summary.append(f"{name} x{info['qty']}")
                
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.write(f"**{name}**")
                    st.caption(f"{info['qty']} x {info['price']:,} ฿")
                with c2:
                    if st.button("❌", key=f"del_{name}"):
                        st.session_state.cart[name]['qty'] -= 1
                        if st.session_state.cart[name]['qty'] <= 0: del st.session_state.cart[name]
                        st.rerun()
            
            st.divider()
            st.markdown(f"### รวม: :orange[{total:,.2f}] ฿")
            pay_type = st.radio("วิธีชำระ:", ["เงินสด", "โอนเงิน"], horizontal=True)
            
            if st.button("✅ ยืนยันการขาย", type="primary", use_container_width=True):
                bill_id = "B" + pd.Timestamp.now().strftime("%H%M%S")
                # บันทึกลงหน่วยความจำจำลอง (สำหรับสรุปยอดวันนี้)
                st.session_state.sales_history.append({
                    "Time": pd.Timestamp.now().strftime("%H:%M"),
                    "Items": ", ".join(items_summary),
                    "Total": total,
                    "Type": pay_type
                })
                
                # ส่งข้อมูลไป Google Sheets
                data_url = f"{API_URL}?bill_id={bill_id}&items={', '.join(items_summary)}&total={total}&payment_type={pay_type}"
                try: requests.get(data_url, timeout=0.1)
                except: pass
                
                st.session_state.last_bill = {"total": total, "type": pay_type}
                st.session_state.cart = {}
                st.rerun()
        else:
            if 'last_bill' in st.session_state and st.session_state.last_bill:
                st.success(f"บันทึกยอด {st.session_state.last_bill['total']:,} ฿ สำเร็จ!")
                if st.button("เริ่มบิลใหม่"):
                    st.session_state.last_bill = None
                    st.rerun()
            else: st.write("กรุณาเลือกสินค้า...")

# ==========================================
# 📊 ส่วนที่ 2: สรุปยอดขาย & สต็อก
# ==========================================
else:
    st.title("📊 ระบบหลังบ้าน (Dashboard & Stock)")
    
    # --- ส่วนสรุปยอดขาย ---
    st.subheader("📈 สรุปยอดขายวันนี้")
    if st.session_state.sales_history:
        df_sales = pd.DataFrame(st.session_state.sales_history)
        
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"<div class='metric-box'><h3>ยอดขายรวม</h3><h2>{df_sales['Total'].sum():,.2f} ฿</h2></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-box'><h3>จำนวนบิล</h3><h2>{len(df_sales)} รายการ</h2></div>", unsafe_allow_html=True)
        with m3:
            cash = df_sales[df_sales['Type'] == 'เงินสด']['Total'].sum()
            transfer = df_sales[df_sales['Type'] == 'โอนเงิน']['Total'].sum()
            st.markdown(f"<div class='metric-box'><h3>แยกตามประเภท</h3><p>เงินสด: {cash:,} | โอน: {transfer:,}</p></div>", unsafe_allow_html=True)

        # กราฟยอดขายรายช่วงเวลา
        fig = px.line(df_sales, x="Time", y="Total", title="แนวโน้มยอดขายในช่วงเวลาต่างๆ", markers=True)
        st.plotly_chart(fig, use_container_width=True)
        
        # ตารางรายการขายล่าสุด
        with st.expander("📝 ดูประวัติการขายรายบิล"):
            st.table(df_sales)
    else:
        st.info("ยังไม่มีข้อมูลการขายในเซสชั่นนี้")

    st.divider()

    # --- ส่วนจัดการสต็อก ---
    st.subheader("📦 ตรวจสอบสต็อกสินค้า")
    df_stock = get_products()
    if not df_stock.empty:
        # ไฮไลต์สินค้าที่สต็อกต่ำ (เช่น น้อยกว่า 10 ชิ้น)
        def highlight_low_stock(val):
            color = '#ff4b4b' if val < 10 else 'none'
            return f'background-color: {color}'

        st.dataframe(df_stock[['Name', 'Price', 'Stock']].style.applymap(highlight_low_stock, subset=['Stock']), use_container_width=True)
        
        st.caption("⚠️ แถบสีแดงหมายถึงสินค้าใกล้หมด (Stock < 10)")
    else:
        st.error("ไม่พบข้อมูลสต็อก")

    if st.button("🔄 อัปเดตข้อมูลจาก Sheets"):
        st.cache_data.clear()
        st.rerun()
