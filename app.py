import streamlit as st
import pandas as pd
import requests
import time
import json
from io import StringIO
from datetime import datetime, timedelta

# ==========================================
# 1. CORE SYSTEM CONFIGURATION
# ==========================================
CSV_URLS = {
    "stock": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv",
    "sales": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv",
    "products": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv",
    "summary": "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
}
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
PROMPTPAY_ID = "0945016189"

st.set_page_config(page_title="TAS POS ULTIMATE V21", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 2. PREMIUM UI (คงเดิมตาม V21)
# ==========================================
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Kanit:wght@200;400;600&display=swap');
    * {{ font-family: 'Kanit', sans-serif; }}
    .stApp {{ background-color: #050505; color: #E0E0E0; }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg, #111, #000); border-right: 1px solid #333; }}
    .product-box {{
        background: rgba(28, 33, 40, 0.8); border: 1px solid #30363D; border-radius: 18px;
        padding: 15px; text-align: center; backdrop-filter: blur(10px);
    }}
    .img-container img {{ width: 100%; height: 180px; object-fit: cover; border-radius: 12px; }}
    .price-tag {{ font-size: 24px; color: #D4AF37; font-weight: 600; margin: 10px 0; }}
    .receipt-container {{
        background: #FFF; color: #000; padding: 30px; border-radius: 10px;
        font-family: 'Courier New', monospace;
    }}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. ROBUST DATA ENGINE (ปรับปรุง Encoding)
# ==========================================
class POSDataEngine:
    @staticmethod
    def fetch(key):
        try:
            url = CSV_URLS[key]
            response = requests.get(f"{url}&nocache={time.time()}", timeout=15)
            response.encoding = 'utf-8-sig' 
            if response.status_code == 200:
                df = pd.read_csv(StringIO(response.text))
                df.columns = df.columns.str.strip()
                return df.dropna(how='all')
        except Exception as e:
            st.error(f"Data Fetch Error ({key}): {e}")
        return pd.DataFrame()

    @staticmethod
    def post_to_gsheet(payload):
        try:
            res = requests.post(SCRIPT_URL, json=payload, timeout=20)
            return res.status_code == 200
        except: return False

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'last_receipt' not in st.session_state: st.session_state.last_receipt = None

# ==========================================
# 4. NAVIGATION
# ==========================================
with st.sidebar:
    st.markdown("<h1 style='color:#D4AF37; text-align:center;'>PLATINUM POS</h1>", unsafe_allow_html=True)
    choice = st.radio("MAIN MENU", ["🛒 หน้าขายสินค้า", "📊 รายงานวิเคราะห์", "📦 สต็อก & คลัง"], label_visibility="collapsed")
    st.divider()
    if st.button("🔄 Sync Data (Force)"):
        st.cache_data.clear()
        st.rerun()

# ==========================================
# 5. PAGE: POS SYSTEM
# ==========================================
if choice == "🛒 หน้าขายสินค้า":
    df_p = POSDataEngine.fetch("products")
    df_s = POSDataEngine.fetch("stock")
    stock_map = pd.Series(df_s.iloc[:, 1].values, index=df_s.iloc[:, 0].astype(str).str.strip()).to_dict() if not df_s.empty else {}

    col_l, col_r = st.columns([2.3, 1.4])

    with col_l:
        st.markdown("<h2 style='color:#D4AF37;'>📋 รายการเมนู</h2>", unsafe_allow_html=True)
        if not df_p.empty:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[2]) if len(row) > 2 else ""
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                available = int(stock_map.get(p_name, 0)) - in_cart

                with grid[idx % 3]:
                    st.markdown(f'<div class="product-box"><div class="img-container"><img src="{p_img}"></div>'
                                f'<div style="margin-top:10px; font-weight:600; height:30px;">{p_name}</div>'
                                f'<div class="price-tag">{p_price:,.0f} ฿</div>'
                                f'<div class="stock-label">คงเหลือ: {available} ชิ้น</div></div>', unsafe_allow_html=True)
                    if available > 0:
                        if st.button(f"เลือก {p_name}", key=f"p_{idx}"):
                            st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                            st.session_state.cart[p_name]['qty'] += 1
                            st.rerun()
                    else: st.button("สินค้าหมด", key=f"out_{idx}", disabled=True)

    with col_r:
        if st.session_state.last_receipt:
            res = st.session_state.last_receipt
            receipt_html = f"""
            <div class="receipt-container"><center><h2>TAS PREMIUM SHOP</h2><small>บิล: {res['bill_id']}</small><hr></center>
            <table style="width:100%;">{''.join([f'<tr><td>{k} x{v["qty"]}</td><td style="text-align:right;">{v["price"]*v["qty"]:,.0f}</td></tr>' for k,v in res['items'].items()])}</table>
            <hr><div style="display:flex; justify-content:space-between; font-size:20px; font-weight:bold;"><span>ยอดรวม</span><span>{res['total']:,.0f} ฿</span></div>
            <div style="margin-top:10px;">วิธีชำระ: {res['method']}<br>
            {f"รับเงิน: {res['cash']:,.2f} / ทอน: {res['change']:,.2f}" if res['method'] == "เงินสด" else ""}</div>
            {f'<center><img src="https://promptpay.io/{PROMPTPAY_ID}/{res["total"]}.png" width="180"></center>' if res['method'] == "พร้อมเพย์" else ""}
            <hr><center><small>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</small></center></div>"""
            st.markdown(receipt_html, unsafe_allow_html=True)
            if st.button("➕ เปิดบิลใหม่", type="primary", use_container_width=True):
                st.session_state.last_receipt = None
                st.rerun()
        else:
            st.markdown("<h3 style='color:#D4AF37;'>🛒 ตะกร้าของฉัน</h3>", unsafe_allow_html=True)
            if not st.session_state.cart: st.info("ตะกร้าว่างเปล่า...")
            else:
                total_val = 0
                for name, data in list(st.session_state.cart.items()):
                    total_val += data['price'] * data['qty']
                    with st.container(border=True):
                        c1, c2, c3 = st.columns([3, 1, 1])
                        c1.markdown(f"**{name}**\n\n{data['price']:,.0f} x {data['qty']}")
                        if c2.button("➕", key=f"plus_{name}"):
                            st.session_state.cart[name]['qty'] += 1; st.rerun()
                        if c3.button("🗑️", key=f"rem_{name}"):
                            del st.session_state.cart[name]; st.rerun()
                st.markdown(f"<h1 style='text-align:right; color:#D4AF37;'>{total_val:,.0f} ฿</h1>", unsafe_allow_html=True)
                pay_method = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                cash_received = 0.0
                if pay_method == "เงินสด":
                    cash_received = st.number_input("รับเงิน", min_value=float(total_val), step=20.0)
                # ประมาณบรรทัดที่ 150 ใน app.py ของพี่ครับ
        if st.button("🚀 ยืนยันการขาย", use_container_width=True):
            if not st.session_state.cart:
                st.warning("กรุณาเลือกสินค้าก่อนครับ")
            else:
                # สร้างวันที่และเวลาปัจจุบัน (เพื่อให้ลงคอลัมน์ A และ B ใน Google Sheets)
                now = datetime.now()
                current_date = now.strftime("%d/%m/%Y")
                current_time = now.strftime("%H:%M:%S")
                bill_id = f"POS{int(time.time())}"
                
                summary_text = ", ".join([f"{k}({v['qty']})" for k, v in st.session_state.cart.items()])
                total_val = sum(v['price'] * v['qty'] for v in st.session_state.cart.values())

                with st.spinner("กำลังบันทึกข้อมูล..."):
                    # ส่งค่า date และ time ไปให้ Apps Script
                    payload = {
                        "action": "checkout",
                        "date": current_date,
                        "time": current_time,
                        "bill_id": bill_id,
                        "total": float(total_val),
                        "method": pay_method,
                        "summary": summary_text
                    }
                    
                    # เรียกใช้ URL จาก SCRIPT_URL (บรรทัดที่ 18 ของพี่)
                    try:
                        response = requests.post(SCRIPT_URL, json=payload)
                        if response.status_code == 200:
                            st.session_state.last_receipt = {
                                "bill_id": bill_id,
                                "date": current_date,
                                "time": current_time,
                                "items": dict(st.session_state.cart),
                                "total": total_val,
                                "method": pay_method,
                                "cash": cash_received,
                                "change": cash_received - total_val
                            }
                            st.session_state.cart = {}
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error("บันทึกไม่สำเร็จ (Server Error)")
                    except Exception as e:
                        st.error(f"การเชื่อมต่อผิดพลาด: {e}")
                        
# ==========================================
# 6. PAGE: ANALYTICS (ปรับการดึงข้อมูลตามลำดับ A-F)
# ==========================================
elif choice == "📊 รายงานวิเคราะห์":
    st.markdown("<h2 style='color:#D4AF37;'>📊 วิเคราะห์ผลประกอบการ</h2>", unsafe_allow_html=True)
    df_sales = POSDataEngine.fetch("sales")
    df_sum = POSDataEngine.fetch("summary")
    
    if df_sales.empty:
        st.info("ไม่พบข้อมูลการขาย")
    else:
        try:
            # ตั้งชื่อคอลัมน์ใหม่ตามโครงสร้าง A-F ของพี่
            df_sales.columns = ['วันที่', 'เวลา', 'เลขบิล', 'ยอดเงิน', 'วิธีชำระเงิน', 'รายการสินค้า']
            
            # แปลงวันที่และยอดเงิน
            df_sales['วันที่'] = pd.to_datetime(df_sales['วันที่'], dayfirst=True, errors='coerce')
            df_sales['ยอดเงิน'] = pd.to_numeric(df_sales['ยอดเงิน'], errors='coerce').fillna(0)
            
            now = datetime.now()
            today_str = now.strftime("%d/%m/%Y")
            
            # ตรวจสอบการปิดวัน
            is_closed = not df_sum[df_sum.iloc[:,0].astype(str).str.contains(today_str)].empty if not df_sum.empty else False
            
            # คำนวณยอด
            today_val = df_sales[df_sales['วันที่'].dt.date == now.date()]['ยอดเงิน'].sum()
            week_val = df_sales[df_sales['วันที่'] >= (now - timedelta(days=7))]['ยอดเงิน'].sum()
            month_val = df_sales[df_sales['วันที่'].dt.month == now.month]['ยอดเงิน'].sum()

            m1, m2, m3 = st.columns(3)
            m1.metric("ยอดขายวันนี้", f"{today_val:,.2f} ฿", delta="CLOSED" if is_closed else "ACTIVE")
            m2.metric("ยอดรวม 7 วัน", f"{week_val:,.2f} ฿")
            m3.metric("ยอดรวมเดือนนี้", f"{month_val:,.2f} ฿")
            
            st.divider()
            tab1, tab2 = st.tabs(["📉 ประวัติรายการขาย", "📝 สรุปยอดปิดวัน"])
            with tab1:
                st.dataframe(df_sales.sort_values(by='วันที่', ascending=False), use_container_width=True)
            with tab2:
                if is_closed: st.success(f"✅ ปิดยอดวันเรียบร้อยแล้ว ({today_str})")
                elif st.button("Confirm: บันทึกปิดยอดวันนี้"):
                    if POSDataEngine.post_to_gsheet({"action": "save_summary", "date": today_str, "total": float(today_val), "bills": len(df_sales[df_sales['วันที่'].dt.date == now.date()])}):
                        st.success("บันทึกสำเร็จ!"); st.cache_data.clear(); time.sleep(1); st.rerun()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการประมวลผลข้อมูล: {e}")

# ==========================================
# 7. PAGE: STOCK MANAGEMENT (RESTORED & IMPROVED)
# ==========================================
elif choice == "📦 สต็อก & คลัง":
    st.markdown("<h2 style='color:#D4AF37;'>📦 คลังสินค้าออนไลน์</h2>", unsafe_allow_html=True)
    
    with st.spinner("กำลังดึงข้อมูลสต็อกล่าสุด..."):
        df_stock = POSDataEngine.fetch("stock")
    
    if not df_stock.empty:
        # ฟังก์ชันสำหรับไฮไลต์สีแดงเมื่อสต็อกต่ำกว่า 10
        def highlight_low_stock(row):
            # สมมติว่าคอลัมน์จำนวนคงเหลืออยู่ที่ Index 1 (คอลัมน์ B)
            target_col = df_stock.columns[1]
            if row[target_col] < 10:
                return ['background-color: #5b2121; color: white'] * len(row)
            return [''] * len(row)

        st.write("📋 รายการสินค้าในระบบทั้งหมด (Sync กับ Google Sheets แล้ว)")
        
        # แสดงตารางพร้อมการตกแต่ง (Styling)
        styled_df = df_stock.style.apply(highlight_low_stock, axis=1)
        
        st.dataframe(
            styled_df, 
            use_container_width=True, 
            height=600
        )
        
        # สรุปข้อมูลเบื้องต้น
        c1, c2 = st.columns(2)
        with c1:
            low_items = df_stock[df_stock.iloc[:, 1] < 10]
            if not low_items.empty:
                st.warning(f"⚠️ มีสินค้าใกล้หมด {len(low_items)} รายการ")
        with c2:
            st.info(f"💡 อัปเดตล่าสุด: {datetime.now().strftime('%H:%M:%S')}")
            
    else:
        st.error("❌ ไม่สามารถเชื่อมต่อข้อมูลสต็อกได้ กรุณากด Sync Data ที่แถบด้านข้าง")

