import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. ตั้งค่าลิงก์ข้อมูล ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Ultra Fast V.7", layout="wide")

# --- ฟังก์ชันลดความหน่วง: โหลดข้อมูลแบบมี Cache ชั่วคราว (60 วินาที) ---
@st.cache_data(ttl=60)
def load_data_cached(url):
    try:
        response = requests.get(f"{url}&t={time.time()}", timeout=3)
        response.encoding = 'utf-8'
        df = pd.read_csv(StringIO(response.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except:
        return pd.DataFrame()

# ฟังก์ชันโหลดสต็อกแบบ Real-time (ไม่ใช้ Cache เพื่อความแม่นยำ)
def load_stock_realtime():
    try:
        response = requests.get(f"{URL_STOCK}&t={time.time()}", timeout=3)
        df = pd.read_csv(StringIO(response.text))
        return df.dropna(how='all').reset_index(drop=True)
    except:
        return pd.DataFrame()

# เตรียม Session State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    # โหลดสินค้า (ใช้ Cache เพื่อความเร็ว)
    df_p = load_data_cached(URL_PRODUCTS)
    # โหลดสต็อก (Real-time เฉพาะตอนเปิดหน้าแรก)
    if 'df_s' not in st.session_state:
        st.session_state.df_s = load_stock_realtime()
    
    col_main, col_right = st.columns([2.3, 1.7])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = str(row.iloc[0])
                p_price = float(row.iloc[1])
                p_img = row.iloc[3] if len(row) > 3 else ""
                
                # ดึงสต็อกจาก Session แทนการโหลดใหม่ทุกปุ่มคลิก (ลดหน่วง)
                s_match = st.session_state.df_s[st.session_state.df_s.iloc[:, 0] == p_name] if not st.session_state.df_s.empty else pd.DataFrame()
                stock_now = int(s_match.iloc[0, 1]) if not s_match.empty else 0
                qty_in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.image(p_img if p_img else "https://via.placeholder.com/150", use_container_width=True)
                        st.markdown(f"**{p_name}**")
                        color = "red" if stock_now <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock_now}</span>", unsafe_allow_html=True)
                        
                        # ปุ่มเพิ่มสินค้า (แก้ไขให้ตอบสนองไว)
                        if stock_now > qty_in_cart:
                            if st.button(f"➕ {p_price:,.0f} ฿", key=f"add_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun() # รีรันเฉพาะ UI ภายใน ไม่โหลดเน็ตใหม่ทั้งหมด
                        else:
                            st.button("❌ หมด", disabled=True, use_container_width=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.success("✅ บันทึกยอดเรียบร้อย")
            qr_html = f'<div style="text-align:center;"><img src="https://promptpay.io/{MY_PROMPTPAY}/{r["total"]}.png" style="width:180px;"></div>' if r['method'] == "📱 PromptPay" else ""
            
            st.markdown(f"""
            <div style="background:#fff; color:#000; padding:15px; border:2px solid #333; font-family:monospace; border-radius:5px;">
                <h3 style="text-align:center; margin:0;">RECEIPT</h3>
                <hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                <hr>
                <div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>ยอดรวม</span><span>{r['total']:,.0f} ฿</span></div>
                {qr_html}
            </div>
            """, unsafe_allow_html=True)
            
            # ปุ่มเริ่มใหม่ (แก้ไขอาการค้าง: ล้าง Cache สต็อกเพื่อให้โหลดใหม่ตอนเริ่มขายครั้งหน้า)
            if st.button("🔄 เริ่มการขายใหม่ (Reset)", type="primary", use_container_width=True):
                if 'df_s' in st.session_state: del st.session_state.df_s
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้า")
            total = sum(i['price'] * i['qty'] for i in st.session_state.cart.values())
            for n, i in list(st.session_state.cart.items()):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{n}** x{i['qty']}")
                if c2.button("🗑️", key=f"del_{n}"):
                    del st.session_state.cart[n]; st.rerun()
            
            if total > 0:
                st.divider()
                method = st.radio("วิธีชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 จ่ายเงิน", type="primary", use_container_width=True):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    # ยิงข้อมูลทิ้งไว้ ไม่ต้องรอ response นาน (Fire and Forget)
                    try: requests.post(SCRIPT_URL, json={"action":"checkout","bill_id":bill_id,"summary":summary,"total":total,"method":method}, timeout=0.1)
                    except: pass
                    st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": method}
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปรายงาน")
    # หน้าจอรายงานใช้โหลดสดเสมอ
    df_sales = load_data_cached.clear() # ล้าง cache เพื่อดูยอดล่าสุด
    df_sales = load_data_cached(URL_SALES)
    
    if not df_sales.empty:
        col_dt = df_sales.columns[0]
        col_total = df_sales.columns[3]
        df_sales[col_dt] = pd.to_datetime(df_sales[col_dt], dayfirst=True, errors='coerce')
        now = datetime.now()
        
        m1, m2, m3 = st.columns(3)
        df_today = df_sales[df_sales[col_dt].dt.date == now.date()]
        m1.metric("ยอดวันนี้", f"{df_today[col_total].sum():,.0f} ฿")
        m2.metric("รายสัปดาห์", f"{df_sales[df_sales[col_dt] >= (now - timedelta(days=7))][col_total].sum():,.0f} ฿")
        m3.metric("รายเดือน", f"{df_sales[df_sales[col_dt].dt.month == now.month][col_total].sum():,.0f} ฿")
        
        # แก้ไข: ปุ่มสรุปยอดรายวัน (ใส่ try-except ป้องกัน Error สีแดง)
        if st.button("📝 ยืนยันสรุปยอดวันนี้เข้าชีต Summary"):
            try:
                res = requests.post(SCRIPT_URL, json={
                    "action": "save_summary",
                    "date": now.strftime("%d/%m/%Y"),
                    "total": float(df_today[col_total].sum()),
                    "bills": int(len(df_today))
                }, timeout=5)
                st.success("สรุปยอดสำเร็จ!")
            except:
                st.error("ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้ แต่ข้อมูลอาจถูกบันทึกแล้ว")

        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.dataframe(load_stock_realtime(), use_container_width=True)
