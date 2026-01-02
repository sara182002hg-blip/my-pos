import streamlit as st
import pandas as pd
import requests
import time
from io import StringIO
from datetime import datetime, timedelta

# --- 1. CONFIG & LINKS ---
URL_STOCK = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=228640428&single=true&output=csv"
URL_SALES = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=952949333&single=true&output=csv"
URL_PRODUCTS = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=1258507712&single=true&output=csv"
URL_SUMMARY = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQh2Zc7U-GRR9SRp0ElOMhsfdJmgKAPBGsHwTicoVTrutHdZCLSA5hwuQymluTlvNM5OLd5wY_95LCe/pub?gid=668209785&single=true&output=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbySel8Dxd6abzj7-JbYtaAgH3saKHBkeGsl47fpfUe293MmVwZM_Bx2K4CthYKUI4Ks/exec"
MY_PROMPTPAY = "0945016189"

st.set_page_config(page_title="TAS POS STABLE V13", layout="wide")

# --- 2. CSS & PRINT SCRIPT ---
st.markdown("""
<style>
    .img-box { width: 100%; height: 160px; object-fit: cover; border-radius: 8px; background: #f8f9fa; }
    .stButton>button { border-radius: 6px; font-weight: bold; }
    /* ซ่อนส่วนที่ไม่เกี่ยวข้องเวลาสั่งปริ้น */
    @media print {
        .no-print { display: none !important; }
        body { background: white; }
    }
</style>
""", unsafe_allow_html=True)

# ฟังก์ชันดึงข้อมูล (Optimized)
def fetch_now(url):
    try:
        r = requests.get(f"{url}&t={time.time()}", timeout=10)
        r.encoding = 'utf-8'
        df = pd.read_csv(StringIO(r.text))
        df.columns = df.columns.str.strip()
        return df.dropna(how='all').reset_index(drop=True)
    except: return pd.DataFrame()

def find_c(df, keys):
    for k in keys:
        for c in df.columns:
            if k.lower() in c.lower(): return c
    return df.columns[0] if not df.empty else None

# State Management
if 'cart' not in st.session_state: st.session_state.cart = {}
if 'order_res' not in st.session_state: st.session_state.order_res = None

# --- 3. SIDEBAR ---
menu = st.sidebar.radio("เมนูใช้งาน", ["🛒 ขายสินค้า (POS)", "📊 รายงานยอดขาย", "📦 สต็อกสินค้า"])

# --- 4. PAGE: CASHIER ---
if menu == "🛒 ขายสินค้า (POS)":
    df_p = fetch_now(URL_PRODUCTS)
    df_s = fetch_now(URL_STOCK)
    
    col_l, col_r = st.columns([2.2, 1.8])
    
    with col_l:
        st.subheader("📦 รายการสินค้า")
        if not df_p.empty:
            c_n, c_p, c_i = find_c(df_p, ["สินค้า"]), find_c(df_p, ["ราคา"]), find_c(df_p, ["รูป"])
            s_n, s_q = find_c(df_s, ["สินค้า"]), find_c(df_s, ["คงเหลือ"])
            stock_db = pd.Series(df_s[s_q].values, index=df_s[s_n].astype(str).str.strip()).to_dict()

            grid = st.columns(3)
            for i, row in df_p.iterrows():
                name = str(row[c_n]).strip()
                price = float(row[c_p])
                img = str(row[c_i]) if c_i and pd.notna(row[c_i]) else ""
                
                avail = int(stock_db.get(name, 0)) - st.session_state.cart.get(name, {}).get('qty', 0)
                
                with grid[i % 3]:
                    with st.container(border=True):
                        st.markdown(f'<img src="{img if img.startswith("http") else ""}" class="img-box">', unsafe_allow_html=True)
                        st.write(f"**{name}**")
                        st.markdown(f"### {price:,.0f} ฿")
                        st.caption(f"คงเหลือ: {avail}")
                        if avail > 0:
                            if st.button(f"➕ เพิ่ม", key=f"add_{i}", use_container_width=True):
                                st.session_state.cart[name] = st.session_state.cart.get(name, {'price': price, 'qty': 0})
                                st.session_state.cart[name]['qty'] += 1
                                st.rerun()
                        else: st.button("❌ หมด", disabled=True, use_container_width=True)

    with col_r:
        if st.session_state.order_res:
            data = st.session_state.order_res
            qr_tag = f'<center><img src="https://promptpay.io/{MY_PROMPTPAY}/{data["total"]}.png" width="180"></center>' if data['method'] == "พร้อมเพย์" else ''
            
            cash_info = ""
            if data['method'] == "เงินสด":
                cash_info = f"""
                <div style="display:flex;justify-content:space-between;"><span>รับเงินมา:</span><span>{data['received']:,.2f}</span></div>
                <div style="display:flex;justify-content:space-between;font-weight:bold;border-top:1px solid #eee;"><span>เงินทอน:</span><span>{data['change']:,.2f}</span></div>
                """

            receipt_html = f"""
            <div id="receipt-area" style="background:white; color:black; padding:20px; border:1px solid #333; font-family:monospace; width:300px; margin:auto; border-radius:10px;">
                <center><h2 style="margin:0;">TAS POS</h2><small>ใบเสร็จรับเงิน/ใบกำกับภาษีอย่างย่อ</small></center>
                <hr style="border-top:1px dashed #000">
                {''.join([f'<div style="display:flex;justify-content:space-between;"><span>{n} x{v["qty"]}</span><span>{v["price"]*v["qty"]:,.0f}</span></div>' for n,v in data['items'].items()])}
                <hr style="border-top:1px dashed #000">
                <div style="display:flex;justify-content:space-between;font-size:20px;font-weight:bold;"><span>รวมสุทธิ</span><span>{data['total']:,.0f} ฿</span></div>
                <p style="text-align:center;margin:10px 0;">ชำระโดย: {data['method']}</p>
                {cash_info}
                {qr_tag}
                <center style="font-size:10px;margin-top:10px;">ขอบคุณที่ใช้บริการ<br>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</center>
            </div>
            """
            st.markdown(receipt_html, unsafe_allow_html=True)
            
            # --- แก้ไขปุ่มปริ้นให้เสถียร ---
            if st.button("🖨️ คลิกเพื่อสั่งพิมพ์ใบเสร็จ", type="primary", use_container_width=True):
                st.components.v1.html(f"""
                <script>
                function printReceipt() {{
                    var content = document.getElementById('receipt-area').innerHTML;
                    var frame = document.createElement('iframe');
                    frame.name = "print_frame";
                    frame.style.position = "absolute";
                    frame.style.top = "-1000000px";
                    document.body.appendChild(frame);
                    var frameDoc = frame.contentWindow ? frame.contentWindow : frame.contentDocument.document ? frame.contentDocument.document : frame.contentDocument;
                    frameDoc.document.open();
                    frameDoc.document.write('<html><head><title>Print</title>');
                    frameDoc.document.write('<style>body{{font-family:monospace;width:300px;padding:10px;}}</style></head><body>');
                    frameDoc.document.write(content);
                    frameDoc.document.write('</body></html>');
                    frameDoc.document.close();
                    setTimeout(function() {{
                        window.frames["print_frame"].focus();
                        window.frames["print_frame"].print();
                        document.body.removeChild(frame);
                    }}, 500);
                }}
                printReceipt();
                </script>
                """, height=0)

            if st.button("🔄 เริ่มการขายใหม่ (Reset)", use_container_width=True):
                st.session_state.order_res = None
                st.rerun()
        else:
            st.subheader("🛒 ตะกร้าสินค้า")
            if not st.session_state.cart: st.info("ยังไม่มีสินค้า")
            else:
                total = sum(v['price']*v['qty'] for v in st.session_state.cart.values())
                for n, v in list(st.session_state.cart.items()):
                    c1, c2, c3 = st.columns([2,1,1])
                    c1.write(f"**{n}**")
                    c2.write(f"x{v['qty']}")
                    if c3.button("🗑️", key=f"del_{n}"): del st.session_state.cart[n]; st.rerun()
                
                st.divider()
                st.title(f"ยอดรวม: {total:,.0f} ฿")
                p_method = st.radio("วิธีชำระเงิน", ["เงินสด", "พร้อมเพย์"], horizontal=True)
                
                received = 0.0
                if p_method == "เงินสด":
                    received = st.number_input("เงินที่รับมา:", min_value=float(total), step=20.0)
                    st.write(f"เงินทอน: **{received - float(total):,.2f} ฿**")

                if st.button("🚀 ยืนยันชำระเงิน", type="primary", use_container_width=True):
                    bill_id = f"B{int(time.time())}"
                    items_txt = ", ".join([f"{k}({v['qty']})" for k,v in st.session_state.cart.items()])
                    try:
                        requests.post(SCRIPT_URL, json={
                            "action": "checkout", "bill_id": bill_id, 
                            "summary": items_txt, "total": total, "method": p_method
                        }, timeout=5)
                        st.session_state.order_res = {
                            "items": dict(st.session_state.cart), "total": total, 
                            "method": p_method, "received": received, "change": received - float(total)
                        }
                        st.session_state.cart = {}
                        st.rerun()
                    except: st.error("บันทึกไม่สำเร็จ แต่สามารถออกใบเสร็จได้")

# --- 5. PAGE: REPORT ---
elif menu == "📊 รายงานยอดขาย":
    st.title("📊 สรุปยอดขาย")
    df_sales = fetch_now(URL_SALES)
    df_sum = fetch_now(URL_SUMMARY)
    
    if not df_sales.empty:
        c_d = find_c(df_sales, ["วัน", "date"])
        c_t = find_c(df_sales, ["ยอด", "total"])
        df_sales[c_d] = pd.to_datetime(df_sales[c_d], dayfirst=True, errors='coerce')
        
        today = datetime.now().strftime("%d/%m/%Y")
        # เช็คว่าตัดยอดหรือยังจาก DailySummary
        is_done = not df_sum[df_sum.iloc[:,0].astype(str).str.contains(today)].empty if not df_sum.empty else False
        
        raw_today = df_sales[df_sales[c_d].dt.date == datetime.now().date()][c_t].sum()
        
        m1, m2 = st.columns(2)
        m1.metric("ยอดขายวันนี้", f"{0 if is_done else raw_today:,.0f} ฿", delta="ตัดยอดแล้ว" if is_done else "กำลังเปิดร้าน")
        m2.metric("บิลทั้งหมดวันนี้", f"{0 if is_done else len(df_sales[df_sales[c_d].dt.date == datetime.now().date()])} รายการ")
        
        if not is_done:
            if st.button("📝 บันทึกตัดยอดรายวันตอนนี้", type="primary", use_container_width=True):
                requests.post(SCRIPT_URL, json={
                    "action": "save_summary", "date": today, 
                    "total": float(raw_today), "bills": int(len(df_sales[df_sales[c_d].dt.date == datetime.now().date()]))
                })
                st.success("ตัดยอดสำเร็จ!"); time.sleep(1); st.rerun()
        else:
            st.info(f"✅ วันที่ {today} ตัดยอดเรียบร้อยแล้ว")
        
        st.divider()
        st.subheader("ประวัติการขายล่าสุด")
        st.dataframe(df_sales.iloc[::-1], use_container_width=True)

# --- 6. PAGE: STOCK ---
elif menu == "📦 สต็อกสินค้า":
    st.title("📦 เช็คสต็อกสินค้า")
    st.dataframe(fetch_now(URL_STOCK), use_container_width=True, height=500)
