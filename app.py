import customtkinter as ctk
import requests
import threading
import json
import qrcode
from PIL import Image, ImageTk
from datetime import datetime
from tkinter import messagebox

# --- CONFIGURATION ---
API_URL = "https://script.google.com/macros/s/AKfycbys8_oaky-j7tINfXAq1-B69KS_GlhO3hQd-D5JsstbC4koXEhxY7tUcuVHMHYPnUkT/exec"
PROMPTPAY_ID = "0812345678" # เปลี่ยนเป็นเบอร์ของคุณ

# --- 1. API & DATA MANAGER ---
class DataManager:
    def __init__(self, url):
        self.url = url
        self.session = requests.Session()

    def call_api(self, action, method="GET", payload=None, callback=None):
        def task():
            try:
                if method == "GET":
                    response = self.session.get(f"{self.url}?action={action}", timeout=15)
                else:
                    response = self.session.post(self.url, json=payload, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    if callback: callback(data)
                else:
                    messagebox.showerror("API Error", f"Error Code: {response.status_code}")
            except Exception as e:
                messagebox.showerror("Connection Error", f"ติดต่อ Server ไม่ได้: {e}")
        
        threading.Thread(target=task, daemon=True).start()

# --- 2. RECEIPT DESIGNER ---
class ReceiptUtils:
    @staticmethod
    def create_text(cart, total, method, received=0, change=0):
        now = datetime.now().strftime("%d/%m/%Y %H:%M")
        line = "-" * 30
        text = f"      PREMIUM STORE POS\n{line}\nDate: {now}\nPay: {method}\n{line}\n"
        for p_id, item in cart.items():
            name = item['name'][:15].ljust(16)
            sub = f"{item['price']*item['qty']:>10.2f}"
            text += f"{name} x{item['qty']}{sub}\n"
        text += f"{line}\nTOTAL:         ฿{total:>10.2f}\n"
        if method == "Cash":
            text += f"Received:      ฿{received:>10.2f}\nChange:        ฿{change:>10.2f}\n"
        text += f"{line}\n   THANK YOU & COME AGAIN\n"
        return text

# --- 3. MAIN APPLICATION ---
class PremiumPOS(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ULTIMATE POS DASHBOARD")
        self.geometry("1280x800")
        ctk.set_appearance_mode("dark")
        
        # State
        self.api = DataManager(API_URL)
        self.products = []
        self.stock = []
        self.cart = {}
        
        self.setup_ui()
        self.refresh_data()

    def setup_ui(self):
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        ctk.CTkLabel(self.sidebar, text="POS SYSTEM", font=("Inter", 22, "bold")).pack(pady=30)
        
        self.btn_sales = ctk.CTkButton(self.sidebar, text="🛒 รายการขาย", command=lambda: self.show_page("sales")).pack(pady=10, padx=20)
        self.btn_stock = ctk.CTkButton(self.sidebar, text="📦 สต็อก", command=lambda: self.show_page("stock")).pack(pady=10, padx=20)
        self.btn_report = ctk.CTkButton(self.sidebar, text="📊 รายงาน", command=lambda: self.show_page("report")).pack(pady=10, padx=20)
        
        self.status_lbl = ctk.CTkLabel(self.sidebar, text="Ready", text_color="gray")
        self.status_lbl.pack(side="bottom", pady=20)

        # Main Area
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self.pages = {}
        for p in ["sales", "stock", "report"]:
            self.pages[p] = ctk.CTkFrame(self.main_frame, fg_color="transparent")
            self.pages[p].grid(row=0, column=0, sticky="nsew")
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        
        self.init_sales_page()
        self.init_stock_page()
        self.show_page("sales")

    def init_sales_page(self):
        f = self.pages["sales"]
        f.columnconfigure(0, weight=3)
        f.columnconfigure(1, weight=1)
        
        # Product Grid
        self.prod_scroll = ctk.CTkScrollableFrame(f, label_text="เมนูสินค้า", corner_radius=15)
        self.prod_scroll.grid(row=0, column=0, sticky="nsew", padx=(0,10))
        
        # Cart Area
        cart_f = ctk.CTkFrame(f, corner_radius=15)
        cart_f.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(cart_f, text="ตะกร้าสินค้า", font=("Inter", 18, "bold")).pack(pady=10)
        self.cart_box = ctk.CTkTextbox(cart_f, height=350, font=("Courier New", 13))
        self.cart_box.pack(fill="x", padx=10)
        
        self.total_lbl = ctk.CTkLabel(cart_f, text="ยอดรวม: ฿0.00", font=("Inter", 24, "bold"), text_color="#2ECC71")
        self.total_lbl.pack(pady=20)
        
        ctk.CTkButton(cart_f, text="ชำระเงิน (F10)", height=50, fg_color="#3B8ED0", command=self.open_pay_modal).pack(fill="x", padx=15, pady=5)
        ctk.CTkButton(cart_f, text="ยกเลิกบิล", fg_color="#E74C3C", command=self.clear_cart).pack(fill="x", padx=15, pady=5)

    def init_stock_page(self):
        f = self.pages["stock"]
        ctk.CTkLabel(f, text="สต็อกออนไลน์ (Real-time)", font=("Inter", 20, "bold")).pack(pady=10)
        self.stock_list = ctk.CTkScrollableFrame(f)
        self.stock_list.pack(fill="both", expand=True, padx=20, pady=10)

    # --- LOGIC ---
    def refresh_data(self):
        self.status_lbl.configure(text="กำลังซิงค์...", text_color="orange")
        self.api.call_api("getInitialData", callback=self.on_data_loaded)

    def on_data_loaded(self, data):
        self.products = data['products']
        self.stock = data['stock']
        self.render_products()
        self.render_stock()
        self.status_lbl.configure(text=f"อัปเดต: {datetime.now().strftime('%H:%M')}", text_color="gray")

    def render_products(self):
        for child in self.prod_scroll.winfo_children(): child.destroy()
        for i, p in enumerate(self.products):
            # หาสต็อกของสินค้านี้
            qty = next((s['qty'] for s in self.stock if str(s['id']) == str(p['id'])), 0)
            btn = ctk.CTkButton(self.prod_scroll, text=f"{p['name']}\n฿{p['price']}\nคงเหลือ: {qty}",
                                 width=160, height=120, corner_radius=10, 
                                 fg_color="#2D2D2D", hover_color="#3D3D3D",
                                 command=lambda x=p: self.add_to_cart(x))
            btn.grid(row=i//3, column=i%3, padx=10, pady=10)

    def add_to_cart(self, p):
        p_id = str(p['id'])
        if p_id in self.cart:
            self.cart[p_id]['qty'] += 1
        else:
            self.cart[p_id] = {'name': p['name'], 'price': float(p['price']), 'qty': 1}
        self.update_cart_ui()

    def update_cart_ui(self):
        self.cart_box.configure(state="normal")
        self.cart_box.delete("1.0", "end")
        total = 0
        for item in self.cart.values():
            sub = item['price'] * item['qty']
            total += sub
            self.cart_box.insert("end", f"{item['name'][:12].ljust(13)} x{item['qty']} {sub:>8.2f}\n")
        self.cart_box.configure(state="disabled")
        self.total_lbl.configure(text=f"ยอดรวม: ฿{total:,.2f}")

    def open_pay_modal(self):
        if not self.cart: return
        total = sum(v['price']*v['qty'] for v in self.cart.values())
        
        modal = ctk.CTkToplevel(self)
        modal.title("Payment")
        modal.geometry("400x550")
        modal.attributes("-topmost", True)
        
        ctk.CTkLabel(modal, text="ยอดชำระ", font=("Inter", 16)).pack(pady=10)
        ctk.CTkLabel(modal, text=f"฿{total:,.2f}", font=("Inter", 32, "bold"), text_color="#2ECC71").pack()
        
        # Cash Input
        cash_in = ctk.CTkEntry(modal, placeholder_text="เงินสดที่รับมา...", height=45, font=("Inter", 18))
        cash_in.pack(pady=20, padx=30, fill="x")
        
        change_lbl = ctk.CTkLabel(modal, text="เงินทอน: ฿0.00", font=("Inter", 16))
        change_lbl.pack()

        def update_change(e):
            try:
                val = float(cash_in.get())
                change_lbl.configure(text=f"เงินทอน: ฿{max(0, val-total):,.2f}")
            except: pass
        cash_in.bind("<KeyRelease>", update_change)

        ctk.CTkButton(modal, text="ยืนยัน (Cash)", height=45, command=lambda: self.finish_sale("Cash", modal)).pack(pady=10, padx=30, fill="x")
        
        # QR Button
        ctk.CTkButton(modal, text="พร้อมเพย์ (QR)", fg_color="#555", command=lambda: self.show_qr(total)).pack(pady=5)

    def finish_sale(self, method, modal):
        # บันทึกข้อมูล
        payload = {
            "action": "recordSale",
            "data": {
                "items": json.dumps(self.cart),
                "total": sum(v['price']*v['qty'] for v in self.cart.values()),
                "method": method
            },
            "stock_updates": [{"id": k, "qty_sold": v['qty']} for k,v in self.cart.items()]
        }
        self.api.call_api("recordSale", method="POST", payload=payload)
        
        # แสดงใบเสร็จจำลอง
        receipt_text = ReceiptUtils.create_text(self.cart, payload['data']['total'], method)
        messagebox.showinfo("ใบเสร็จ", receipt_text)
        
        modal.destroy()
        self.clear_cart()
        self.refresh_data()

    def show_qr(self, amount):
        qr_win = ctk.CTkToplevel(self)
        qr_win.geometry("300x400")
        qr_data = f"https://promptpay.io/{PROMPTPAY_ID}/{amount}"
        img = qrcode.make(qr_data).resize((250, 250))
        self.qr_tk = ImageTk.PhotoImage(img)
        ctk.CTkLabel(qr_win, image=self.qr_tk, text="").pack(pady=20)
        ctk.CTkLabel(qr_win, text="สแกนเพื่อจ่ายเงิน").pack()

    def render_stock(self):
        for child in self.stock_list.winfo_children(): child.destroy()
        for s in self.stock:
            row = ctk.CTkFrame(self.stock_list, fg_color="transparent")
            row.pack(fill="x", pady=2)
            color = "#E74C3C" if int(s['qty']) < 5 else "white"
            ctk.CTkLabel(row, text=s['name'], width=200, anchor="w", text_color=color).pack(side="left", padx=10)
            ctk.CTkLabel(row, text=f"จำนวน: {s['qty']}", width=100, text_color=color).pack(side="left")
            if int(s['qty']) < 5:
                ctk.CTkLabel(row, text="⚠️ Low Stock", text_color="#E74C3C").pack(side="left")

    def clear_cart(self):
        self.cart = {}
        self.update_cart_ui()

    def show_page(self, p):
        for page in self.pages.values(): page.grid_remove()
        self.pages[p].grid()

if __name__ == "__main__":
    app = PremiumPOS()
    app.mainloop()
