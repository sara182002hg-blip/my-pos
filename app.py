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

st.set_page_config(page_title="TAS POS Final Pro", layout="wide")

# ฟังก์ชันโหลดข้อมูลที่เน้นความเร็วและภาษาไทย
def get_data(url):
    try:
        res = requests.get(f"{url}&t={time.time()}", timeout=5)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

# Session State
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    # โหลดสินค้าเพียงครั้งเดียวต่อการ Refresh เพื่อลดความหน่วง
    df_p = get_data(URL_PRODUCTS)
    df_s = get_data(URL_STOCK)
    
    col_products, col_cart = st.columns([2.2, 1.8])
    
    with col_products:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            grid = st.columns(3)
            for idx, row in df_p.iterrows():
                p_name = str(row.iloc[0]).strip()
                p_price = float(row.iloc[1])
                p_img = str(row.iloc[3]).strip() if len(row) > 3 else ""
                
                # ดึงสต็อกจริง
                s_match = df_s[df_s.iloc[:, 0].str.strip() == p_name] if not df_s.empty else pd.DataFrame()
                stock = int(s_match.iloc[0, 1]) if not s_match.empty else 0
                qty_in_cart = st.session_state.cart.get(p_name, {}).get('qty', 0)
                
                with grid[idx % 3]:
                    with st.container(border=True):
                        if p_img.startswith("http"):
                            st.image(p_img, use_container_width=True)
                        else:
                            st.image("https://via.placeholder.com/150?text=Product", use_container_width=True)
                        
                        st.markdown(f"**{p_name}**")
                        st.markdown(f"### {p_price:,.0f} ฿")
                        color = "red" if stock <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        if stock > qty_in_cart:
                            if st.button(f"➕ เพิ่ม", key=f"add_{idx}", use_container_width=True):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price': p_price, 'qty': 0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun()
                        else:
                            st.button("❌ หมด", disabled=True, use_container_width=True)

    with col_cart:
        if st.session_state.receipt:
            r = st.session_state.receipt
            st.success("✅ บันทึกสำเร็จ!")
            qr_code = f'<div style="text-align:center;"><img src="https://promptpay.io/{MY_PROMPTPAY}/{r["total"]}.png" width="180"></div>' if r['method'] == "📱 PromptPay" else ""
            
            st.markdown(f"""
            <div style="background:#fff; color:#000; padding:20px; border:2px solid #333; font-family:monospace; border-radius:10px;">
                <h2 style="text-align:center;">TAS POS RECEIPT</h2><hr>
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{i["qty"]}</span><span>{i["price"]*i["qty"]:,.0f}</span></div>' for n,i in r['items'].items()])}
                <hr><div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>รวมสุทธิ</span><span>{r['total']:,.0f} ฿</span></div>
                <p style="text-align:center; margin-top:10px;">ชำระโดย: {r['method']}</p>
                {qr_code}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 เริ่มการขายใหม่ (Reset)", type="primary", use_container_width=True):
                st.session_state.receipt = None
                st.session_state.cart = {}
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            total = sum(i['price'] * i['qty'] for i in st.session_state.cart.values())
            if not st.session_state.cart:
                st.info("ยังไม่มีสินค้าในตะกร้า")
            else:
                for n, i in list(st.session_state.cart.items()):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{n}**")
                    c2.write(f"x{i['qty']}")
                    if c3.button("🗑️", key=f"del_{n}"):
                        del st.session_state.cart[n]; st.rerun()
                
                st.divider()
                st.title(f"รวม: {total:,.0f} ฿")
                method = st.radio("วิธีชำระเงิน", ["💵 เงินสด", "📱 PromptPay"], horizontal=True)
                
                if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    bill_id = f"B{int(time.time())}"
                    summary_text = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    # บันทึกลงใบเสร็จก่อนส่งเน็ต เพื่อให้ใบเสร็จขึ้นทันที
                    st.session_state.receipt = {"items": dict(st.session_state.cart), "total": total, "method": method}
                    try:
                        requests.post(SCRIPT_URL, json={"action":"checkout","bill_id":bill_id,"summary":summary_text,"total":total,"method":method}, timeout=1)
                    except: pass
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปรายงานยอดขาย")
    df_sales = get_data(URL_SALES)
    df_sum = get_data(URL_SUMMARY)
    
    if not df_sales.empty:
        df_sales.iloc[:, 0] = pd.to_datetime(df_sales.iloc[:, 0], dayfirst=True, errors='coerce')
        now = datetime.now()
        today_str = now.strftime("%d/%m/%Y")
        
        # ตรวจสอบการตัดยอด
        is_cut = not df_sum[df_sum.iloc[:, 0] == today_str].empty if not df_sum.empty else False
        
        # คำนวณยอดต่างๆ
        df_today = df_sales[df_sales.iloc[:, 0].dt.date == now.date()]
        total_today = df_today.iloc[:, 3].sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("ยอดขายวันนี้", f"{0 if is_cut else total_today:,.0f} ฿", f"{0 if is_cut else len(df_today)} บิล")
        m2.metric("รายสัปดาห์", f"{df_sales[df_sales.iloc[:, 0] >= (now - timedelta(days=7))].iloc[:, 3].sum():,.0f} ฿")
        m3.metric("รายเดือน", f"{df_sales[df_sales.iloc[:, 0].dt.month == now.month].iloc[:, 3].sum():,.0f} ฿")
        
        if st.button("📅 บันทึกตัดยอดรายวัน (Reset ยอดวันนี้)", type="primary", disabled=is_cut):
            try:
                requests.post(SCRIPT_URL, json={"action":"save_summary","date":today_str,"total":float(total_today),"bills":int(len(df_today))}, timeout=5)
                st.success("บันทึกสำเร็จ!")
                time.sleep(1); st.rerun()
            except: st.error("เกิดข้อผิดพลาดในการเชื่อมต่อ")

        st.divider()
        st.subheader("📋 ประวัติการขายล่าสุด")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อกสินค้าปัจจุบัน")
    st.dataframe(get_data(URL_STOCK), use_container_width=True)
