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
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Final V.8", layout="wide")

# ฟังก์ชันโหลดข้อมูลแบบบังคับภาษาไทย (UTF-8)
def load_data_utf8(url):
    try:
        response = requests.get(f"{url}&t={time.time()}", timeout=5)
        response.encoding = 'utf-8' # บังคับภาษาไทย
        data = response.text
        df = pd.read_csv(StringIO(data))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except:
        return pd.DataFrame()

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data_utf8(URL_PRODUCTS)
    df_s = load_data_utf8(URL_STOCK)
    
    col_main, col_right = st.columns([2.3, 1.7])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                # ดึงข้อมูลตามลำดับคอลัมน์ที่ถูกต้อง
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[3]).strip() if len(row) > 3 else ""
                
                # Matching สต็อกด้วยชื่อที่ Strip ช่องว่างออกแล้ว
                s_match = df_s[df_s.iloc[:, 0].str.strip() == p_name] if not df_s.empty else pd.DataFrame()
                stock_now = int(s_match.iloc[0, 1]) if not s_match.empty else 0
                qty_in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        # แสดงรูปภาพ (ถ้าไม่มีให้ใช้ Placeholder)
                        if p_img and p_img.startswith("http"):
                            st.image(p_img, use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/150?text=No+Image", use_container_width=True)
                            
                        st.markdown(f"**{p_name}**")
                        color = "red" if stock_now <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock_now}</span>", unsafe_allow_html=True)
                        
                        if stock_now > qty_in_cart:
                            if st.button(f"➕ {p_price:,.0f} ฿", key=f"add_{i}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ หมด", disabled=True, use_container_width=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            r = st.session_state.receipt
            qr_html = f'<div style="text-align:center;"><img src="https://promptpay.io/{MY_PROMPTPAY}/{r["total"]}.png" style="width:180px;"></div>' if r['method'] == "📱 PromptPay" else ""
            st.markdown(f"""
            <div style="background:#fff; color:#000; padding:15px; border:2px solid #333; font-family:monospace; border-radius:5px;">
                <h3 style="text-align:center; margin:0;">RECEIPT</h3><hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-size:18px;font-weight:bold;"><span>ยอดรวม</span><span>{r['total']:,.0f} ฿</span></div>
                <p style="text-align:center; font-size:12px;">ชำระโดย: {r['method']}</p>{qr_html}
            </div>""", unsafe_allow_html=True)
            if st.button("🔄 เริ่มการขายใหม่", type="primary", use_container_width=True):
                st.session_state.receipt = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้า")
            total = sum(i['price'] * i['qty'] for i in st.session_state.cart.values())
            for n, i in list(st.session_state.cart.items()):
                c1, c2 = st.columns([3, 1])
                c1.write(f"**{n}** x{i['qty']}")
                if c2.button("🗑️", key=f"del_{n}"): del st.session_state.cart[n]; st.rerun()
            if total > 0:
                method = st.radio("วิธีชำระ", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                if st.button("🚀 ยืนยันจ่ายเงิน", type="primary", use_container_width=True):
                    requests.post(SCRIPT_URL, json={"action":"checkout","bill_id":f"B{int(time.time())}","summary":", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()]),"total":total,"method":method}, timeout=5)
                    st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": method}
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 รายงานยอดขาย")
    df_sales = load_data_utf8(URL_SALES)
    df_sum = load_data_utf8(URL_SUMMARY)
    
    if not df_sales.empty:
        df_sales.iloc[:, 0] = pd.to_datetime(df_sales.iloc[:, 0], dayfirst=True, errors='coerce')
        today = datetime.now().date()
        today_str = datetime.now().strftime("%d/%m/%Y")
        
        # เช็คว่าตัดยอดไปหรือยัง
        is_cut = not df_sum[df_sum.iloc[:, 0] == today_str].empty if not df_sum.empty else False
        
        # คำนวณยอดขายวันนี้
        sales_today = df_sales[df_sales.iloc[:, 0].dt.date == today]
        total_raw = sales_today.iloc[:, 3].sum()
        
        # ยอดที่จะแสดง (ถ้าตัดยอดแล้วให้เป็น 0)
        display_today = 0 if is_cut else total_raw
        display_bills = 0 if is_cut else len(sales_today)

        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{display_today:,.0f} ฿")
        m2.metric("จำนวนบิลวันนี้", f"{display_bills} บิล")
        m3.metric("ยอดขายเดือนนี้", f"{df_sales[df_sales.iloc[:, 0].dt.month == today.month].iloc[:, 3].sum():,.0f} ฿")
        
        if st.button("📝 กดบันทึกตัดยอดรายวัน (ยอดจะรีเซ็ตเป็น 0)", type="primary", disabled=is_cut):
            requests.post(SCRIPT_URL, json={"action":"save_summary","date":today_str,"total":float(total_raw),"bills":int(len(sales_today))})
            st.success("บันทึกตัดยอดเรียบร้อยแล้ว!")
            time.sleep(1)
            st.rerun()

        st.divider()
        st.subheader("📋 ประวัติการขายทั้งหมด")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อกสินค้าปัจจุบัน")
    st.dataframe(load_data_utf8(URL_STOCK), use_container_width=True)
