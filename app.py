import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime

# --- 1. ตั้งค่าลิงก์ข้อมูล (คงเดิม) ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189" 

st.set_page_config(page_title="TAS POS Professional", layout="wide")

# ฟังก์ชันโหลดข้อมูลแบบ Real-time (บังคับ No-Cache)
def load_data_live(url):
    try:
        res = requests.get(f"{url}&t={time.time()}", timeout=10)
        res.encoding = 'utf-8'
        df = pd.read_csv(StringIO(res.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

def find_col(df, keywords):
    for c in df.columns:
        if any(k.lower() in c.lower() for k in keywords): return c
    return df.columns[0] if not df.empty else None

if 'cart' not in st.session_state: st.session_state.cart = {}
if 'receipt' not in st.session_state: st.session_state.receipt = None

menu = st.sidebar.radio("🏬 เมนูระบบ", ["🛒 ขายสินค้า", "📊 รายงานยอดขาย", "📦 ตรวจสอบสต็อก"])

if menu == "🛒 ขายสินค้า":
    df_p = load_data_live(URL_PRODUCTS)
    df_s = load_data_live(URL_STOCK) # โหลดสต็อกใหม่ทุกครั้งที่เข้าหน้านี้
    
    col_main, col_right = st.columns([2.5, 1.5])
    
    with col_main:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            c_name = find_col(df_p, ['Name', 'สินค้า'])
            c_price = find_col(df_p, ['Price', 'ราคา'])
            c_img = find_col(df_p, ['Image', 'รูป'])
            
            grid = st.columns(3)
            for i, row in df_p.iterrows():
                p_name = row[c_name]
                s_match = df_s[df_s[find_col(df_s, ['Name'])] == p_name] if not df_s.empty else pd.DataFrame()
                stock = int(s_match.iloc[0][find_col(df_s, ['Stock', 'คงเหลือ'])] ) if not s_match.empty else 0
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.markdown(f'<img src="{row[c_img]}" style="width:100%; height:180px; object-fit:contain;">', unsafe_allow_html=True)
                        st.write(f"**{p_name}**")
                        color = "red" if stock <= 5 else "#00ff00"
                        st.markdown(f"คงเหลือ: <span style='color:{color}; font-weight:bold;'>{stock}</span>", unsafe_allow_html=True)
                        
                        if stock > st.session_state.cart.get(p_name, {}).get('qty', 0):
                            if st.button(f"➕ เพิ่ม ({p_name})", key=f"add_{i}"):
                                st.session_state.cart[p_name] = st.session_state.cart.get(p_name, {'price':row[c_price], 'qty':0})
                                st.session_state.cart[p_name]['qty'] += 1
                                st.rerun() # Refresh เพื่อให้สต็อกในตะกร้าอัปเดต
                        else: st.button("❌ หมด", disabled=True, key=f"sold_{i}")

    with col_right:
        if st.session_state.receipt:
            st.success("ชำระเงินสำเร็จ!")
            if st.button("🔄 ขายรายการต่อไป"):
                st.session_state.receipt = None
                st.rerun()
        else:
            total = sum(i['price'] * i['qty'] for i in st.session_state.cart.values())
            if total > 0:
                st.title(f"รวม {total:,} ฿")
                if st.button("🚀 ยืนยันการขาย", type="primary", use_container_width=True):
                    summary = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    requests.post(SCRIPT_URL, json={"action":"checkout", "summary":summary, "total":total, "method":"POS"})
                    st.session_state.receipt = {"total":total}
                    st.session_state.cart = {}
                    st.rerun()

elif menu == "📊 รายงานยอดขาย":
    st.title("📊 รายงานสรุปยอด")
    df_sales = load_data_live(URL_SALES)
    df_sum = load_data_live(URL_SUMMARY)
    
    today = datetime.now().strftime("%d/%m/%Y")
    this_month = datetime.now().strftime("%m/%Y")

    # ตรวจสอบว่าวันนี้ตัดยอดไปหรือยัง
    is_cut_today = not df_sum[df_sum.iloc[:, 0] == today].empty if not df_sum.empty else False

    # คำนวณยอดขายวันนี้ (ถ้าตัดยอดแล้วให้โชว์ 0)
    c_dt = find_col(df_sales, ['วันที่', 'Time'])
    df_sales['Date_Only'] = pd.to_datetime(df_sales[c_dt], dayfirst=True, errors='coerce').dt.strftime("%d/%m/%Y")
    sales_today = df_sales[df_sales['Date_Only'] == today]
    
    display_total = 0 if is_cut_today else pd.to_numeric(sales_today[find_col(df_sales, ['ยอดรวม'])], errors='coerce').sum()
    display_bills = 0 if is_cut_today else len(sales_today)

    c1, c2, c3 = st.columns(3)
    c1.metric("ยอดขายวันนี้", f"{display_total:,} ฿")
    c2.metric("จำนวนบิลวันนี้", f"{display_bills} บิล")
    
    # สรุปรายเดือน
    month_sales = 0
    if not df_sum.empty:
        df_sum['Month'] = pd.to_datetime(df_sum.iloc[:, 0], dayfirst=True, errors='coerce').dt.strftime("%m/%Y")
        month_sales = df_sum[df_sum['Month'] == this_month].iloc[:, 1].sum()
    c3.metric(f"ยอดรวมเดือน {this_month}", f"{month_sales + display_total:,} ฿")

    if st.button("📅 กดตัดยอดรายวัน", type="primary", disabled=is_cut_today):
        if display_total > 0:
            requests.post(SCRIPT_URL, json={"action":"save_summary", "date":today, "total":float(display_total), "bills":int(display_bills)})
            st.success("ตัดยอดเรียบร้อย! ยอดวันนี้ถูกรีเซ็ตเป็น 0")
            time.sleep(1)
            st.rerun()
        else: st.warning("ยังไม่มีมียอดขายให้ตัด")

    st.divider()
    st.subheader("📝 ประวัติการตัดยอดรายวัน (Daily Summary)")
    st.dataframe(df_sum.iloc[::-1], use_container_width=True)

elif menu == "📦 ตรวจสอบสต็อก":
    st.title("📦 สต็อก")
    st.dataframe(load_data_live(URL_STOCK), use_container_width=True)
