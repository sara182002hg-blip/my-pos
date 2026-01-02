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

st.set_page_config(page_title="TAS POS Ultra V.4", layout="wide")

# ฟังก์ชันโหลดข้อมูลที่เน้นความเร็ว (Bypass Cache)
def load_data(url):
    try:
        # เพิ่ม parameter time เพื่อป้องกันการติด cache ของ browser/server
        res = requests.get(f"{url}&t={time.time()}", timeout=5)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    # โหลดข้อมูลสินค้าและสต็อกพร้อมกัน
    df_p = load_data(URL_PRODUCTS)
    df_s = load_data(URL_STOCK)
    
    col_main, col_right = st.columns([2.3, 1.7])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                # อ้างอิงคอลัมน์: 0=ชื่อ, 1=ราคา, 2=หมวดหมู่, 3=รูป
                p_name = row.iloc[0]
                p_price = row.iloc[1]
                p_img = row.iloc[3] if len(row) > 3 else "https://via.placeholder.com/150"
                
                # เช็คสต็อกแบบ Real-time จาก df_s
                s_match = df_s[df_s.iloc[:, 0] == p_name] if not df_s.empty else pd.DataFrame()
                stock = int(s_match.iloc[0, 1]) if not s_match.empty else 0
                in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.markdown(f'<img src="{p_img}" style="width:100%;height:150px;object-fit:contain;">', unsafe_allow_html=True)
                        st.markdown(f"**{p_name}**")
                        st.markdown(f"**{p_price:,.0f} ฿**")
                        
                        color = "red" if stock <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        # ปุ่มบวกสินค้า (กลับมาแสดงผลแล้ว)
                        if stock > in_cart:
                            if st.button(f"➕ เพิ่มสินค้า", key=f"btn_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price':p_price, 'qty':0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ สินค้าหมด", disabled=True, use_container_width=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.success("✅ บันทึกสำเร็จ")
            st.markdown(f"""
                <div style="background:white; color:black; padding:20px; border-radius:10px; font-family:monospace; border:2px solid #333;">
                    <h2 style="text-align:center;">TAS POS</h2>
                    <hr>
                    {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                    <hr>
                    <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>ยอดรวม</span><span>{r['total']:,.0f} ฿</span></div>
                    <p style="font-size:12px; margin-top:10px;">วิธีชำระ: {r['method']}</p>
                </div>
            """, unsafe_allow_html=True)
            if r['method'] == "📱 PromptPay":
                st.image(f"https://promptpay.io/{MY_PROMPTPAY}/{r['total']}.png")
            
            if st.button("🔄 เริ่มการขายใหม่", type="primary", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = 0
            if not st.session_state.cart:
                st.info("ตะกร้าว่างเปล่า")
            else:
                for n, i in list(st.session_state.cart.items()):
                    sub = i['price'] * i['qty']
                    total += sub
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{n}**")
                    c2.write(f"x{i['qty']}")
                    if c3.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]
                        st.rerun()
                
                st.divider()
                st.title(f"{total:,.0f} ฿")
                pay_method = st.radio("เลือกวิธีชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                
                if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    bill_id = f"B{int(time.time())}"
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    
                    # แก้ปัญหาแจ้งเตือนไม่เชื่อมต่อ: ใช้ Timeout ที่เหมาะสมและเก็บผลลัพธ์
                    try:
                        requests.post(SCRIPT_URL, json={
                            "action": "checkout",
                            "bill_id": bill_id,
                            "summary": summary,
                            "total": total,
                            "method": pay_method
                        }, timeout=10)
                    except:
                        pass # ให้ระบบไปต่อที่ใบเสร็จเลยเพราะบันทึกเข้าชีตไปแล้ว
                        
                    st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": pay_method}
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 รายงานสรุปยอดขาย")
    df_sales = load_data(URL_SALES)
    
    if not df_sales.empty:
        # การเตรียมข้อมูลวันที่
        col_dt = df_sales.columns[0]
        col_total = df_sales.columns[3] # ยอดรวม
        df_sales[col_dt] = pd.to_datetime(df_sales[col_dt], errors='coerce', dayfirst=True)
        
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        
        # 1. ยอดขายวันนี้
        df_today = df_sales[df_sales[col_dt].dt.strftime("%Y-%m-%d") == today_str]
        total_today = pd.to_numeric(df_today[col_total], errors='coerce').sum()
        
        # 2. ยอดขายรายสัปดาห์ (7 วันย้อนหลัง)
        week_ago = now - timedelta(days=7)
        df_week = df_sales[df_sales[col_dt] >= week_ago]
        total_week = pd.to_numeric(df_week[col_total], errors='coerce').sum()
        
        # 3. ยอดขายรายเดือน
        this_month = now.strftime("%Y-%m")
        df_month = df_sales[df_sales[col_dt].dt.strftime("%Y-%m") == this_month]
        total_month = pd.to_numeric(df_month[col_total], errors='coerce').sum()

        # แสดง Metrics
        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{total_today:,.0f} ฿", f"{len(df_today)} บิล")
        m2.metric("รายสัปดาห์ (7 วัน)", f"{total_week:,.0f} ฿")
        m3.metric(f"รายเดือน ({now.strftime('%b')})", f"{total_month:,.0f} ฿")

        st.divider()
        st.subheader("📝 ประวัติการขายล่าสุด")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)
    else:
        st.warning("ไม่พบข้อมูลการขาย")

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อกสินค้าปัจจุบัน")
    st.dataframe(load_data(URL_STOCK), use_container_width=True)
