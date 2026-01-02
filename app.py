import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. ตั้งค่าลิงก์ข้อมูล (คงเดิม) ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Stable V9", layout="wide")

# ฟังก์ชันโหลดข้อมูลแบบเร็ว (มี Cache 2 นาทีเพื่อความลื่นไหล)
@st.cache_data(ttl=120)
def fetch_data(url):
    try:
        res = requests.get(f"{url}&cache_bus={time.time()}", timeout=5)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all')
    except:
        return pd.DataFrame()

# ค้นหาชื่อคอลัมน์อัตโนมัติ
def get_col(df, names):
    for c in df.columns:
        if any(n.lower() in c.lower() for n in names): return c
    return df.columns[0] if not df.empty else None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = fetch_data(URL_PRODUCTS)
    df_s = fetch_data(URL_STOCK)
    
    col_main, col_right = st.columns([2.2, 1.8])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            # ค้นหาคอลัมน์อัตโนมัติเพื่อป้องกัน Error
            c_name = get_col(df_p, ["สินค้า", "name", "รายการ"])
            c_price = get_col(df_p, ["ราคา", "price"])
            c_img = get_col(df_p, ["รูป", "image", "url", "img"])
            
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = str(row[c_name])
                p_price = float(row[c_price])
                p_img = str(row[c_img]) if c_img and pd.notna(row[c_img]) else ""
                
                # เช็คสต็อก
                s_name_col = get_col(df_s, ["สินค้า", "name"])
                s_qty_col = get_col(df_s, ["คงเหลือ", "stock", "qty"])
                s_match = df_s[df_s[s_name_col] == p_name] if not df_s.empty else pd.DataFrame()
                stock = int(s_match.iloc[0][s_qty_col]) if not s_match.empty else 0
                
                with grid[i % 3]:
                    with st.container(border=True):
                        # แสดงรูปภาพแบบเสถียร
                        if p_img.startswith("http"): st.image(p_img, use_container_width=True)
                        else: st.write("📷 ไม่มีรูป")
                        
                        st.write(f"**{p_name}**")
                        st.write(f"### {p_price:,.0f} ฿")
                        
                        qty_in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                        if stock > qty_in_cart:
                            if st.button(f"➕ เพิ่มสินค้า", key=f"add_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ สินค้าหมด", disabled=True, use_container_width=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.success("ชำระเงินเรียบร้อย")
            qr_html = f'<div style="text-align:center;"><img src="https://promptpay.io/{MY_PROMPTPAY}/{r["total"]}.png" width="180"></div>' if r['method'] == "📱 PromptPay" else ""
            st.markdown(f"""<div style="background:white; color:black; padding:15px; border:2px solid #333; font-family:monospace; border-radius:5px;">
                <h3 style="text-align:center;">TAS POS</h3><hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>ยอดรวม</span><span>{r['total']:,.0f} ฿</span></div>
                <p style="text-align:center; margin-top:10px;">วิธีชำระ: {r['method']}</p>{qr_html}</div>""", unsafe_allow_html=True)
            if st.button("🔄 เริ่มการขายใหม่", type="primary", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = sum(i['price'] * i['qty'] for i in st.session_state.cart.values())
            for n, i in list(st.session_state.cart.items()):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{n}** x{i['qty']}")
                if c2.button("🗑️", key=f"del_{n}"): del st.session_state.cart[n]; st.rerun()
            
            if total > 0:
                st.divider()
                method = st.radio("เลือกการชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    # ส่งข้อมูลไป Apps Script
                    try:
                        requests.post(SCRIPT_URL, json={"action":"checkout","bill_id":f"B{int(time.time())}","summary":", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()]),"total":total,"method":method}, timeout=1)
                    except: pass
                    st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": method}
                    st.session_state.cart = {}
                    st.cache_data.clear() # ล้าง Cache สต็อกเพื่อให้อัปเดตหลังขาย
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = fetch_data(URL_SALES)
    df_sum = fetch_data(URL_SUMMARY)
    
    if not df_sales.empty:
        # ระบบป้องกันการค้างหน้าจอ (Safe Date Parsing)
        c_date = get_col(df_sales, ["วัน", "time", "date"])
        c_total = get_col(df_sales, ["ยอด", "total", "ราคา"])
        df_sales[c_date] = pd.to_datetime(df_sales[c_date], dayfirst=True, errors='coerce')
        
        now = datetime.now()
        df_today = df_sales[df_sales[c_date].dt.date == now.date()]
        
        # ตรวจสอบการตัดยอด
        today_str = now.strftime("%d/%m/%Y")
        is_cut = not df_sum[df_sum.iloc[:, 0] == today_str].empty if not df_sum.empty else False
        
        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_cut else df_today[c_total].sum():,.0f} ฿")
        m2.metric("รายสัปดาห์", f"{df_sales[df_sales[c_date] >= (now - timedelta(days=7))][c_total].sum():,.0f} ฿")
        m3.metric("รายเดือน", f"{df_sales[df_sales[c_date].dt.month == now.month][c_total].sum():,.0f} ฿")
        
        if st.button("📝 บันทึกสรุปยอดรายวัน", type="primary", disabled=is_cut):
            try:
                requests.post(SCRIPT_URL, json={"action":"save_summary","date":today_str,"total":float(df_today[c_total].sum()),"bills":int(len(df_today))}, timeout=5)
                st.success("บันทึกสำเร็จ!")
                st.cache_data.clear()
                time.sleep(1); st.rerun()
            except: st.error("บันทึกไม่สำเร็จ")
            
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 เช็คสต็อกสินค้า")
    st.dataframe(fetch_data(URL_STOCK), use_container_width=True)
