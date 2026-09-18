import customtkinter as ctk
from tkinter import messagebox
import requests
import secrets
from datetime import datetime, timedelta

ctk.set_appearance_mode("dark")

FIREBASE_URL = "https://punin-mobile-unlock-default-rtdb.asia-southeast1.firebasedatabase.app"

def db_get(path):
    try:
        res = requests.get(f"{FIREBASE_URL}/{path}.json", timeout=5)
        return res.json() or {}
    except Exception:
        return {}

def db_put(path, data):
    try:
        res = requests.put(f"{FIREBASE_URL}/{path}.json", json=data, timeout=5)
        return res.ok
    except Exception:
        return False

def db_delete(path):
    try:
        res = requests.delete(f"{FIREBASE_URL}/{path}.json", timeout=5)
        return res.ok
    except Exception:
        return False

def generate_random_key(duration_label="1Y"):
    p1, p2 = secrets.token_hex(2).upper(), secrets.token_hex(2).upper()
    return f"PUNIN-{duration_label}-{p1}-{p2}"

def calculate_expiry(duration_choice):
    now = datetime.now()
    if duration_choice == "3 ខែ (3 Months)":
        return (now + timedelta(days=90)).strftime("%Y-%m-%d"), "3M"
    elif duration_choice == "6 ខែ (6 Months)":
        return (now + timedelta(days=180)).strftime("%Y-%m-%d"), "6M"
    elif duration_choice == "1 ឆ្នាំ (1 Year)":
        return (now + timedelta(days=365)).strftime("%Y-%m-%d"), "1Y"
    elif duration_choice == "Lifetime (អាយុកាល)":
        return "2099-12-31", "LIFE"
    else:
        return (now + timedelta(days=365)).strftime("%Y-%m-%d"), "1Y"

class AdminApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🛠️ ONLINE ADMIN MANAGEMENT V2.6")
        
        # កែសម្រួលទំហំ Window ឱ្យតូចល្មមសមរម្យ
        self.geometry("720x520")
        self.resizable(False, False)

        ctk.CTkLabel(
            self, 
            text="🔑 ONLINE ADMIN ACTIVATION & CONTROL CENTER", 
            font=("Khmer OS Battambang", 14, "bold")
        ).pack(pady=(8, 2))

        # កែសម្រួលទំហំ Tabview ឱ្យត្រូវតាមទំហំ Window
        self.tabview = ctk.CTkTabview(self, width=700, height=460)
        self.tabview.pack(padx=10, pady=5)

        self.tab_pending = self.tabview.add("⏳ Pending Approval")
        self.tab_approved = self.tabview.add("👥 Active / Approved Users")
        self.tab_update = self.tabview.add("🚀 Auto-Update & Version Approve")

        self.setup_update_tab()
        self.setup_pending_tab()
        self.setup_approved_tab()

    # --- TAB AUTO UPDATE & VERSION APPROVE ---
    def setup_update_tab(self):
        frame = ctk.CTkFrame(self.tab_update)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            frame, 
            text="🚀 កំណត់ Version កម្មវិធី & អនុម័តសិទ្ធិប្រើប្រាស់ (Version Approval)", 
            font=("Khmer OS Battambang", 12, "bold")
        ).pack(pady=10)

        self.version_entry = ctk.CTkEntry(frame, placeholder_text="Version (ឧ. 2.1)", width=320, height=32)
        self.version_entry.pack(pady=5)

        self.url_entry = ctk.CTkEntry(frame, placeholder_text="Link ទាញយក (Google Drive / Mediafire...)", width=320, height=32)
        self.url_entry.pack(pady=5)

        # Status Label
        self.lbl_ver_status = ctk.CTkLabel(frame, text="ស្ថានភាពបច្ចុប្បន្ន៖ កំពុងពិនិត្យ...", font=("Khmer OS Battambang", 11, "bold"), text_color="#9CA3AF")
        self.lbl_ver_status.pack(pady=5)

        # Button Group
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)

        btn_update_ver = ctk.CTkButton(
            btn_frame, text="⚡ Push Update", width=130, height=32,
            fg_color="#D97706", hover_color="#B45309",
            font=("Khmer OS Battambang", 11, "bold"),
            command=self.push_new_version
        )
        btn_update_ver.pack(side="left", padx=4)

        self.btn_approve_ver = ctk.CTkButton(
            btn_frame, text="✅ Approve Version", width=140, height=32,
            fg_color="#059669", hover_color="#047857",
            font=("Khmer OS Battambang", 11, "bold"),
            command=lambda: self.set_version_status("approved")
        )
        self.btn_approve_ver.pack(side="left", padx=4)

        self.btn_block_ver = ctk.CTkButton(
            btn_frame, text="❌ Block Version", width=130, height=32,
            fg_color="#DC2626", hover_color="#B91C1C",
            font=("Khmer OS Battambang", 11, "bold"),
            command=lambda: self.set_version_status("pending")
        )
        self.btn_block_ver.pack(side="left", padx=4)

        self.load_current_version_info()

    def load_current_version_info(self):
        info = db_get("app_control/version_info")
        if info and isinstance(info, dict):
            self.version_entry.delete(0, "end")
            self.version_entry.insert(0, info.get("version", ""))
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, info.get("download_url", ""))
            
            status = info.get("status", "pending")
            if status == "approved":
                self.lbl_ver_status.configure(text="🟢 Status: APPROVED (អនុញ្ញាតឱ្យ User ប្រើប្រាស់/អាប់ដេត)", text_color="#10B981")
            else:
                self.lbl_ver_status.configure(text="🟡 Status: PENDING / BLOCKED (មិនទាន់អនុម័ត)", text_color="#F59E0B")

    def push_new_version(self):
        ver = self.version_entry.get().strip()
        url = self.url_entry.get().strip()

        if not ver or not url:
            messagebox.showerror("Error", "សូមបញ្ចូល Version និង Link ទាញយក!")
            return

        payload = {
            "version": ver,
            "download_url": url,
            "status": "pending",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if db_put("app_control/version_info", payload):
            self.lbl_ver_status.configure(text="🟡 Status: PENDING (រង់ចាំការ Approve)", text_color="#F59E0B")
            messagebox.showinfo("Success", f"បាន Push Version v{ver} ឡើង Cloud រួចរាល់!\n(ស្ថានភាព៖ Pending - សូមចុចប៊ូតុង Approve ដើម្បីបើកសិទ្ធិឱ្យ User)")
        else:
            messagebox.showerror("Error", "មិនអាចភ្ជាប់ទៅកាន់ Cloud បានទេ!")

    def set_version_status(self, new_status):
        info = db_get("app_control/version_info")
        if not info or not isinstance(info, dict):
            messagebox.showerror("Error", "មិនទាន់មានទិន្នន័យ Version នៅលើ Cloud ទេ សូម Push មុនសិន!")
            return

        info["status"] = new_status
        if db_put("app_control/version_info", info):
            if new_status == "approved":
                self.lbl_ver_status.configure(text="🟢 Status: APPROVED (អនុញ្ញាតឱ្យ User ប្រើប្រាស់/អាប់ដេត)", text_color="#10B981")
                messagebox.showinfo("Approved", "បាន Approve Version នេះជោគជ័យ! ឥឡូវនេះ User អាចទាញយក និងប្រើប្រាស់បានធម្មតា។")
            else:
                self.lbl_ver_status.configure(text="🟡 Status: PENDING / BLOCKED (មិនទាន់អនុម័ត)", text_color="#F59E0B")
                messagebox.showinfo("Blocked", "បានផ្អាកសិទ្ធិ (Block) Version នេះវិញហើយ។")
        else:
            messagebox.showerror("Error", "មិនអាចធ្វើបច្ចុប្បន្នភាព Status បានទេ!")

    # --- TAB PENDING ---
    def setup_pending_tab(self):
        top_frame = ctk.CTkFrame(self.tab_pending, fg_color="transparent")
        top_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkButton(
            top_frame, text="🔄 Refresh List", width=110, height=28, fg_color="#2563EB",
            font=("Khmer OS Battambang", 10),
            command=self.refresh_pending_list
        ).pack(side="right")

        self.scroll_pending = ctk.CTkScrollableFrame(self.tab_pending, width=660, height=360)
        self.scroll_pending.pack(pady=5)

        self.refresh_pending_list()

    def refresh_pending_list(self):
        for widget in self.scroll_pending.winfo_children():
            widget.destroy()

        users = db_get("pending_users")

        if not users:
            ctk.CTkLabel(self.scroll_pending, text="គ្មានទិន្នន័យអ្នកចុះឈ្មោះរង់ចាំ Confirm ទេ", font=("Khmer OS Battambang", 11)).pack(pady=20)
            return

        for user, data in users.items():
            card = ctk.CTkFrame(self.scroll_pending)
            card.pack(fill="x", pady=4, padx=3)

            info_text = f"👤 User: {user}  |  📧 Email: {data.get('email', '')}"
            ctk.CTkLabel(card, text=info_text, anchor="w", font=("Khmer OS Battambang", 10, "bold")).pack(fill="x", padx=8, pady=(4, 2))

            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(fill="x", padx=3, pady=4)

            dur_option = ctk.CTkOptionMenu(
                action_frame, 
                values=["3 ខែ (3 Months)", "6 ខែ (6 Months)", "1 ឆ្នាំ (1 Year)", "Lifetime (អាយុកាល)"],
                width=130, height=28, font=("Khmer OS Battambang", 10)
            )
            dur_option.set("1 ឆ្នាំ (1 Year)")
            dur_option.pack(side="left", padx=3)

            key_entry = ctk.CTkEntry(action_frame, placeholder_text="Key...", width=160, height=28, font=("Arial", 10))
            key_entry.pack(side="left", padx=3)

            btn_gen = ctk.CTkButton(
                action_frame, text="⚡ Key", width=55, height=28, fg_color="#D97706",
                font=("Khmer OS Battambang", 10),
                command=lambda e=key_entry, o=dur_option: self.fill_generated_key(e, o.get())
            )
            btn_gen.pack(side="left", padx=3)

            btn_confirm = ctk.CTkButton(
                action_frame, text="✅ Confirm", width=80, height=28, fg_color="#059669",
                font=("Khmer OS Battambang", 10),
                command=lambda u=user, d=data, e=key_entry, o=dur_option: self.confirm_user_key(u, d, e.get().strip(), o.get())
            )
            btn_confirm.pack(side="left", padx=3)

            btn_reject = ctk.CTkButton(
                action_frame, text="❌ Delete", width=65, height=28, fg_color="#DC2626",
                font=("Khmer OS Battambang", 10),
                command=lambda u=user: self.delete_pending_user(u)
            )
            btn_reject.pack(side="left", padx=3)

    def fill_generated_key(self, entry_widget, duration_choice):
        _, code = calculate_expiry(duration_choice)
        entry_widget.delete(0, "end")
        entry_widget.insert(0, generate_random_key(code))

    def confirm_user_key(self, username, user_data, activation_key, duration_choice):
        if not activation_key:
            messagebox.showerror("Error", "សូមចុចបង្កើត Key ជាមុនសិន!")
            return

        exp_date, _ = calculate_expiry(duration_choice)

        approved_payload = {
            "email": user_data["email"],
            "password": user_data["password"],
            "license_key": activation_key,
            "duration": duration_choice,
            "expiry_date": exp_date,
            "status": "ACTIVE",
            "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        if db_put(f"approved_users/{username}", approved_payload):
            db_delete(f"pending_users/{username}")
            messagebox.showinfo("Success", f"បាន Confirm Active ជូន {username} រួចរាល់!\n- រយៈពេល៖ {duration_choice}\n- ផុតកំណត់៖ {exp_date}\n- Key: {activation_key}")
            self.refresh_pending_list()
            self.refresh_approved_list()
        else:
            messagebox.showerror("Error", "មានបញ្ហាភ្ជាប់ Internet!")

    def delete_pending_user(self, username):
        if messagebox.askyesno("Confirm Delete", f"តើអ្នកពិតជាចង់លុប {username} ចោលឬ?"):
            if db_delete(f"pending_users/{username}"):
                messagebox.showinfo("Success", f"បានលុប {username} រួចរាល់")
                self.refresh_pending_list()

    # --- TAB APPROVED USERS & CUSTOM PASSWORD RESET ---
    def setup_approved_tab(self):
        top_frame = ctk.CTkFrame(self.tab_approved, fg_color="transparent")
        top_frame.pack(fill="x", padx=5, pady=2)

        ctk.CTkButton(
            top_frame, text="🔄 Refresh List", width=110, height=28, fg_color="#2563EB",
            font=("Khmer OS Battambang", 10),
            command=self.refresh_approved_list
        ).pack(side="right")

        self.scroll_approved = ctk.CTkScrollableFrame(self.tab_approved, width=660, height=360)
        self.scroll_approved.pack(pady=5)

        self.refresh_approved_list()

    def refresh_approved_list(self):
        for widget in self.scroll_approved.winfo_children():
            widget.destroy()

        users = db_get("approved_users")

        if not users:
            ctk.CTkLabel(self.scroll_approved, text="គ្មានទិន្នន័យ Active User នៅឡើយទេ", font=("Khmer OS Battambang", 11)).pack(pady=20)
            return

        for user, data in users.items():
            card = ctk.CTkFrame(self.scroll_approved)
            card.pack(fill="x", pady=4, padx=3)

            exp = data.get("expiry_date", "N/A")
            status = data.get("status", "ACTIVE")
            key = data.get("license_key", "N/A")
            dur = data.get("duration", "N/A")
            current_pass = data.get("password", "N/A")

            info_text = f"👤 User: {user}  |  🔑 Pass: {current_pass}  |  Key: {key}\n📅 ផុតកំណត់៖ {exp} ({dur})  |  Status: {status}"
            ctk.CTkLabel(card, text=info_text, anchor="w", font=("Khmer OS Battambang", 10, "bold")).pack(fill="x", padx=8, pady=(4, 2))

            action_frame = ctk.CTkFrame(card, fg_color="transparent")
            action_frame.pack(fill="x", padx=3, pady=4)

            pass_entry = ctk.CTkEntry(action_frame, placeholder_text="Pass ថ្មី...", width=110, height=28, font=("Arial", 10))
            pass_entry.pack(side="left", padx=3)

            btn_custom_pass = ctk.CTkButton(
                action_frame, text="✏️ Set Pass", width=75, height=28, fg_color="#2563EB",
                font=("Khmer OS Battambang", 10),
                command=lambda u=user, d=data, pe=pass_entry: self.set_custom_password(u, d, pe.get().strip())
            )
            btn_custom_pass.pack(side="left", padx=3)

            dur_option = ctk.CTkOptionMenu(
                action_frame, 
                values=["3 ខែ (3 Months)", "6 ខែ (6 Months)", "1 ឆ្នាំ (1 Year)", "Lifetime (អាយុកាល)"],
                width=130, height=28, font=("Khmer OS Battambang", 10)
            )
            dur_option.set(dur if dur in ["3 ខែ (3 Months)", "6 ខែ (6 Months)", "1 ឆ្នាំ (1 Year)", "Lifetime (អាយុកាល)"] else "1 ឆ្នាំ (1 Year)")
            dur_option.pack(side="left", padx=3)

            btn_renew = ctk.CTkButton(
                action_frame, text="🔄 Renew", width=70, height=28, fg_color="#D97706",
                font=("Khmer OS Battambang", 10),
                command=lambda u=user, d=data, o=dur_option: self.renew_user_time(u, d, o.get())
            )
            btn_renew.pack(side="left", padx=3)

            btn_del = ctk.CTkButton(
                action_frame, text="🗑️ Delete", width=65, height=28, fg_color="#DC2626",
                font=("Khmer OS Battambang", 10),
                command=lambda u=user: self.delete_approved_user(u)
            )
            btn_del.pack(side="left", padx=3)

    def set_custom_password(self, username, user_data, new_password):
        if not new_password:
            messagebox.showerror("Error", "សូមវាយបញ្ចូល Password ថ្មីក្នុងប្រអប់ជាមុនសិន!")
            return

        user_data["password"] = new_password
        if db_put(f"approved_users/{username}", user_data):
            messagebox.showinfo("Success", f"បានផ្លាស់ប្តូរ Password របស់ {username} ទៅជា '{new_password}' រួចរាល់!")
            self.refresh_approved_list()
        else:
            messagebox.showerror("Error", "មិនអាចធ្វើបច្ចុប្បន្នភាពបានទេ!")

    def renew_user_time(self, username, user_data, duration_choice):
        exp_date, code = calculate_expiry(duration_choice)
        new_key = generate_random_key(code)

        user_data["expiry_date"] = exp_date
        user_data["duration"] = duration_choice
        user_data["license_key"] = new_key
        user_data["status"] = "ACTIVE"

        if db_put(f"approved_users/{username}", user_data):
            messagebox.showinfo("Success", f"បានពន្យារពេល Active ជូន {username} ជោគជ័យ!\n- សុពលភាពថ្មី៖ {exp_date}\n- Key ថ្មី៖ {new_key}")
            self.refresh_approved_list()
        else:
            messagebox.showerror("Error", "មិនអាចធ្វើបច្ចុប្បន្នភាពបានទេ!")

    def delete_approved_user(self, username):
        if messagebox.askyesno("Confirm Delete", f"តើអ្នកពិតជាចង់លុប ឬផ្អាកគណនី {username} ឬ?"):
            if db_delete(f"approved_users/{username}"):
                messagebox.showinfo("Success", f"បានលុបគណនី {username} ចេញពីប្រព័ន្ធរួចរាល់!")
                self.refresh_approved_list()

if __name__ == "__main__":
    app = AdminApp()
    app.mainloop()
