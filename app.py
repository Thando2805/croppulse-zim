import os
import json
import sqlite3
import threading
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from PIL import Image, ImageTk
import numpy as np
import tensorflow as tf

# PDF Generation Imports
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Check OpenCV availability for WebCam photo capture
try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# High-Contrast Modern Color Palette
COLORS = {
    "sidebar": "#022C22",         # Deep Emerald
    "sidebar_active": "#059669",  # Active Navigation Green
    "sidebar_hover": "#047857",   # Hover Emerald
    "page_bg": "#F1F5F9",         # Clean Slate Background
    "card_bg": "#FFFFFF",         # Pure White Card
    "border": "#CBD5E1",          # High Contrast Border
    "primary": "#059669",         # Primary Action Emerald
    "primary_dark": "#047857",
    "accent_blue": "#1D4ED8",     # Camera Action Blue
    "accent_blue_hover": "#1E40AF",
    "text_dark": "#0F172A",       # Dark Slate Header Text
    "text_muted": "#475569",      # Slate 600 Subtitle Text
    "badge_success_bg": "#DCFCE7",# High Confidence Tag BG
    "badge_success_fg": "#15803D",
    "badge_warning_bg": "#FEF3C7",# Moderate Confidence Tag BG
    "badge_warning_fg": "#B45309",
    "badge_danger_bg": "#FEE2E2", # Low Confidence Tag BG
    "badge_danger_fg": "#B91C1C",
}

# Expanded Crop Symptom Catalog
SYMPTOMS_CATALOG = {
    "🍅 Tomato": [
        "Concentric 'Target Ring' Spots",
        "Water-Soaked Dark Lesions",
        "Upward Leaf Curling / Cupping",
        "Black Speckles / Small Spots",
        "Velvety Mold under Leaves",
        "Dark Sunken Fruit Bottoms",
        "Yellow Leaf Margins / Chlorosis",
        "Stem Vascular Browning",
        "Bleached Sunscald Skin",
        "Fruit Deformation / Catfacing"
    ],
    "🌽 Maize": [
        "Cigar-Shaped Tan Lesions",
        "Rectangular Leaf Spots",
        "Powdery Brown Rust Pustules",
        "Chewed Leaf Whorls / Holes",
        "Yellow Chlorotic Mosaic Streaks",
        "Swollen Galls on Ears / Tassels",
        "White/Pink Mold on Ear Grains",
        "Stalk Soft Rot / Lodging",
        "Purple / Red Leaf Margins",
        "V-Shaped Tip Chlorosis"
    ],
    "🌿 General": [
        "Wilting / Drooping Foliage",
        "Stunted Overall Plant Growth",
        "Seedling Stem Collapse (Damping)",
        "White Powdery Surface Coating",
        "Stem Cankers / Lesions",
        "Root Softening / Blackening"
    ]
}


class CropPulseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CropPulse - AI Crop Disease Diagnostic Tool")
        self.root.geometry("1340x920")
        self.root.minsize(1150, 800)
        self.root.configure(bg=COLORS["page_bg"])

        self.model = None
        self.class_names = {}
        self.current_image_path = None
        self.symptom_vars = {}
        self.nav_buttons = {}

        self._init_db()
        self._setup_styles()
        self._build_ui()
        self.load_model_async()

    def _init_db(self):
        """Initialize SQLite database for diagnostic history logging."""
        self.conn = sqlite3.connect("crop_history.db", check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                disease TEXT,
                confidence REAL,
                mode TEXT,
                symptoms TEXT
            )
        ''')
        self.conn.commit()

    def _setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TNotebook", background=COLORS["card_bg"], borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 10, "bold"), padding=[10, 6])
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _font(self, size, weight="normal"):
        return ("Segoe UI", int(size), weight)

    def _label(self, parent, text="", size=11, weight="normal", fg=None, bg=None, **kwargs):
        return tk.Label(
            parent,
            text=text,
            font=self._font(size, weight),
            fg=fg or COLORS["text_dark"],
            bg=bg or COLORS["card_bg"],
            anchor=kwargs.pop("anchor", tk.W),
            justify=kwargs.pop("justify", tk.LEFT),
            **kwargs
        )

    def _build_ui(self):
        # ------------------------------------------------------------------
        # 1. SIDEBAR NAVIGATION
        # ------------------------------------------------------------------
        sidebar = tk.Frame(self.root, bg=COLORS["sidebar"], width=240)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        brand_frame = tk.Frame(sidebar, bg=COLORS["sidebar"])
        brand_frame.pack(fill=tk.X, padx=20, pady=(24, 28))

        logo_canvas = tk.Canvas(brand_frame, width=44, height=44, bg=COLORS["sidebar"], highlightthickness=0)
        logo_canvas.pack(anchor=tk.W, pady=(0, 8))
        logo_canvas.create_oval(2, 2, 42, 42, fill="#DFF8E9", outline="")
        logo_canvas.create_text(22, 22, text="🌿", font=("Segoe UI Emoji", 20))

        self._label(brand_frame, "CropPulse", 20, "bold", fg="white", bg=COLORS["sidebar"]).pack(anchor=tk.W)
        self._label(brand_frame, "AI Crop Health Diagnostics", 9, fg="#A7F3D0", bg=COLORS["sidebar"]).pack(anchor=tk.W, pady=(2, 0))

        nav_items = [
            ("📷", "Diagnostics", "diag"),
            ("📊", "History", "hist"),
            ("⚙️", "Settings", "settings")
        ]

        for icon, name, key in nav_items:
            is_active = (key == "diag")
            bg_color = COLORS["sidebar_active"] if is_active else COLORS["sidebar"]
            nav_row = tk.Frame(sidebar, bg=bg_color, cursor="hand2")
            nav_row.pack(fill=tk.X, padx=10, pady=3)

            lbl_icon = self._label(nav_row, icon, 12, fg="white", bg=bg_color, width=3)
            lbl_icon.pack(side=tk.LEFT, padx=(10, 0), pady=12)

            lbl_text = self._label(
                nav_row, name, 11, "bold" if is_active else "normal",
                fg="white" if is_active else "#D1FAE5", bg=bg_color
            )
            lbl_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=12)

            self.nav_buttons[key] = (nav_row, lbl_icon, lbl_text)

            for w in (nav_row, lbl_icon, lbl_text):
                w.bind("<Button-1>", lambda e, k=key: self.switch_tab(k))

        status_box = tk.Frame(sidebar, bg=COLORS["sidebar"])
        status_box.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=24)
        self.sys_status_label = self._label(status_box, "● Loading AI Model...", 10, "bold", fg="#FBBF24", bg=COLORS["sidebar"])
        self.sys_status_label.pack(anchor=tk.W)

        # ------------------------------------------------------------------
        # 2. MAIN WORKSPACE
        # ------------------------------------------------------------------
        main = tk.Frame(self.root, bg=COLORS["page_bg"])
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        header = tk.Frame(main, bg=COLORS["card_bg"], height=95, highlightbackground=COLORS["border"], highlightthickness=1)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        title_box = tk.Frame(header, bg=COLORS["card_bg"])
        title_box.pack(side=tk.LEFT, padx=28, pady=(16, 12), fill=tk.BOTH, expand=True)

        self._label(title_box, "Crop Health Workspace", 18, "bold").pack(anchor=tk.W)
        self._label(
            title_box,
            "Diagnose Tomato & Maize diseases via leaf image analysis or crop symptom checklists.",
            10,
            fg=COLORS["text_muted"]
        ).pack(anchor=tk.W, pady=(4, 0))

        self.pages_container = tk.Frame(main, bg=COLORS["page_bg"])
        self.pages_container.pack(fill=tk.BOTH, expand=True, padx=24, pady=20)

        self.diag_page = tk.Frame(self.pages_container, bg=COLORS["page_bg"])
        self.diag_page.pack(fill=tk.BOTH, expand=True)

        self.hist_page = tk.Frame(self.pages_container, bg=COLORS["page_bg"])
        self.settings_page = tk.Frame(self.pages_container, bg=COLORS["page_bg"])

        self._build_diagnostics_page()
        self._build_history_page()
        self._build_settings_page()

    def switch_tab(self, target_key):
        for key, (row, icon, text) in self.nav_buttons.items():
            if key == target_key:
                row.config(bg=COLORS["sidebar_active"])
                icon.config(bg=COLORS["sidebar_active"])
                text.config(bg=COLORS["sidebar_active"], font=self._font(11, "bold"), fg="white")
            else:
                row.config(bg=COLORS["sidebar"])
                icon.config(bg=COLORS["sidebar"])
                text.config(bg=COLORS["sidebar"], font=self._font(11, "normal"), fg="#D1FAE5")

        self.diag_page.pack_forget()
        self.hist_page.pack_forget()
        self.settings_page.pack_forget()

        if target_key == "diag":
            self.diag_page.pack(fill=tk.BOTH, expand=True)
        elif target_key == "hist":
            self.hist_page.pack(fill=tk.BOTH, expand=True)
            self.load_history_table()
        elif target_key == "settings":
            self.settings_page.pack(fill=tk.BOTH, expand=True)

    def _build_diagnostics_page(self):
        # LEFT COLUMN: Image Input + Tabbed Crop Symptoms
        left_card = tk.Frame(self.diag_page, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1)
        left_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 12))

        self._label(left_card, "1. Image Sample", 13, "bold").pack(anchor=tk.W, padx=20, pady=(12, 2))

        self.dropzone = tk.Frame(left_card, bg="#F8FAFC", highlightbackground="#94A3B8", highlightthickness=2)
        self.dropzone.pack(fill=tk.BOTH, expand=True, padx=20, pady=4)

        self.preview_label = tk.Label(
            self.dropzone,
            text="📸\n\nNo Leaf Image Selected\n(Upload photo or capture via webcam)",
            font=self._font(10, "bold"),
            fg=COLORS["text_muted"],
            bg="#F8FAFC",
            justify=tk.CENTER
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        btn_grid = tk.Frame(left_card, bg=COLORS["card_bg"])
        btn_grid.pack(fill=tk.X, padx=20, pady=4)

        btn_upload = tk.Button(
            btn_grid, text="📁 Upload", command=self.upload_image,
            font=self._font(9, "bold"), fg="white", bg=COLORS["primary"],
            activebackground=COLORS["primary_dark"], activeforeground="white",
            relief="flat", cursor="hand2", pady=5
        )
        btn_upload.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))

        btn_camera = tk.Button(
            btn_grid, text="📸 Camera", command=self.open_camera_modal,
            font=self._font(9, "bold"), fg="white", bg=COLORS["accent_blue"],
            activebackground=COLORS["accent_blue_hover"], activeforeground="white",
            relief="flat", cursor="hand2", pady=5
        )
        btn_camera.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        # DEDICATED IMAGE ANALYSIS BUTTON
        btn_img_analyze = tk.Button(
            btn_grid, text="🔍 Analyze Image", command=self.analyze_image_only,
            font=self._font(9, "bold"), fg="white", bg="#2563EB",
            activebackground="#1D4ED8", activeforeground="white",
            relief="flat", cursor="hand2", pady=5
        )
        btn_img_analyze.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))

        # TABBED SYMPTOM SELECTION SECTION
        symptom_header = tk.Frame(left_card, bg=COLORS["card_bg"])
        symptom_header.pack(fill=tk.X, padx=20, pady=(12, 2))

        self._label(symptom_header, "2. Observed Visual Symptoms", 13, "bold").pack(side=tk.LEFT)

        btn_clear_sym = tk.Button(
            symptom_header, text="Clear All", command=self.clear_symptoms,
            font=self._font(9), fg=COLORS["text_muted"], bg="#F1F5F9",
            relief="flat", cursor="hand2"
        )
        btn_clear_sym.pack(side=tk.RIGHT)

        notebook = ttk.Notebook(left_card)
        notebook.pack(fill=tk.X, padx=20, pady=4)

        for category, items in SYMPTOMS_CATALOG.items():
            tab_frame = tk.Frame(notebook, bg="#F8FAFC", highlightbackground=COLORS["border"], highlightthickness=1)
            notebook.add(tab_frame, text=f" {category} ")

            for i, sym in enumerate(items):
                var = tk.BooleanVar()
                self.symptom_vars[sym] = var
                chk = tk.Checkbutton(
                    tab_frame, text=f" {sym}", variable=var,
                    font=self._font(9), fg=COLORS["text_dark"],
                    bg="#F8FAFC", activebackground="#F8FAFC",
                    selectcolor="#FFFFFF", anchor=tk.W
                )
                chk.grid(row=i // 2, column=i % 2, sticky="w", padx=10, pady=3)

        btn_analyze = tk.Button(
            left_card, text="🔬 RUN FULL DIAGNOSIS (IMAGE + SYMPTOMS)", command=self.analyze_input,
            font=self._font(11, "bold"), fg="white", bg="#047857",
            activebackground="#065F46", activeforeground="white",
            relief="flat", cursor="hand2", pady=10
        )
        btn_analyze.pack(fill=tk.X, padx=20, pady=(8, 14))

        # RIGHT COLUMN: Diagnostic Results Card
        right_card = tk.Frame(self.diag_page, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1)
        right_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(12, 0))

        report_top_row = tk.Frame(right_card, bg=COLORS["card_bg"])
        report_top_row.pack(fill=tk.X, padx=20, pady=(16, 2))

        self._label(report_top_row, "Diagnostic Report", 15, "bold").pack(side=tk.LEFT)

        btn_pdf = tk.Button(
            report_top_row, text="📄 Export PDF", command=self.export_pdf_report,
            font=self._font(9, "bold"), fg="white", bg="#047857",
            activebackground="#065F46", activeforeground="white",
            relief="flat", cursor="hand2", padx=8, pady=4
        )
        btn_pdf.pack(side=tk.RIGHT, padx=(4, 0))

        btn_export = tk.Button(
            report_top_row, text="💾 Export TXT", command=self.export_report,
            font=self._font(9, "bold"), fg="white", bg=COLORS["accent_blue"],
            activebackground=COLORS["accent_blue_hover"], activeforeground="white",
            relief="flat", cursor="hand2", padx=8, pady=4
        )
        btn_export.pack(side=tk.RIGHT)

        self._label(
            right_card, "Neural vision network and crop rule diagnostic breakdown.",
            10, fg=COLORS["text_muted"]
        ).pack(anchor=tk.W, padx=20, pady=(0, 10))

        self.result_header = tk.Frame(right_card, bg="#F8FAFC", highlightbackground=COLORS["border"], highlightthickness=1)
        self.result_header.pack(fill=tk.X, padx=20, pady=4)

        self.badge_label = self._label(
            self.result_header, "●  READY FOR DIAGNOSIS", 10, "bold",
            fg=COLORS["badge_success_fg"], bg=COLORS["badge_success_bg"],
            padx=10, pady=3
        )
        self.badge_label.pack(anchor=tk.W, padx=14, pady=(10, 4))

        self.disease_label = self._label(self.result_header, "Awaiting Input Data", 15, "bold", bg="#F8FAFC")
        self.disease_label.pack(anchor=tk.W, padx=14)

        self.confidence_text = self._label(self.result_header, "Confidence Score: -- %", 10, "bold", fg=COLORS["text_muted"], bg="#F8FAFC")
        self.confidence_text.pack(anchor=tk.W, padx=14, pady=(4, 6))

        self.conf_bar = tk.Canvas(self.result_header, height=10, bg="#E2E8F0", highlightthickness=0)
        self.conf_bar.pack(fill=tk.X, padx=14, pady=(0, 12))

        self.report_area = scrolledtext.ScrolledText(
            right_card, wrap=tk.WORD, font=("Consolas", 10),
            bg="#FAFAFA", fg=COLORS["text_dark"], bd=1, relief="solid", padx=10, pady=10
        )
        self.report_area.pack(fill=tk.BOTH, expand=True, padx=20, pady=(8, 16))
        self.report_area.insert(tk.END, "Upload a leaf photo OR select tomato/maize symptoms to evaluate.\n")

    def _build_history_page(self):
        card = tk.Frame(self.hist_page, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True)

        header_frame = tk.Frame(card, bg=COLORS["card_bg"])
        header_frame.pack(fill=tk.X, padx=20, pady=16)

        self._label(header_frame, "Past Diagnostic Logs", 15, "bold").pack(side=tk.LEFT)

        btn_refresh = tk.Button(
            header_frame, text="🔄 Refresh", command=self.load_history_table,
            font=self._font(9), fg=COLORS["text_dark"], bg="#E2E8F0",
            relief="flat", cursor="hand2", padx=10, pady=3
        )
        btn_refresh.pack(side=tk.RIGHT)

        cols = ("ID", "Timestamp", "Disease Diagnosis", "Confidence", "Engine Mode")
        self.hist_tree = ttk.Treeview(card, columns=cols, show="headings", selectmode="browse")

        self.hist_tree.heading("ID", text="#")
        self.hist_tree.heading("Timestamp", text="Date & Time")
        self.hist_tree.heading("Disease Diagnosis", text="Disease Diagnosis")
        self.hist_tree.heading("Confidence", text="Confidence")
        self.hist_tree.heading("Engine Mode", text="Engine Mode")

        self.hist_tree.column("ID", width=40, anchor=tk.CENTER)
        self.hist_tree.column("Timestamp", width=160, anchor=tk.W)
        self.hist_tree.column("Disease Diagnosis", width=340, anchor=tk.W)
        self.hist_tree.column("Confidence", width=100, anchor=tk.CENTER)
        self.hist_tree.column("Engine Mode", width=200, anchor=tk.W)

        self.hist_tree.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

    def _build_settings_page(self):
        card = tk.Frame(self.settings_page, bg=COLORS["card_bg"], highlightbackground=COLORS["border"], highlightthickness=1)
        card.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self._label(card, "Application Settings", 16, "bold").pack(anchor=tk.W, padx=20, pady=(20, 10))

        db_frame = tk.Frame(card, bg="#F8FAFC", highlightbackground=COLORS["border"], highlightthickness=1)
        db_frame.pack(fill=tk.X, padx=20, pady=10)

        self._label(db_frame, "Database Storage", 12, "bold", bg="#F8FAFC").pack(anchor=tk.W, padx=14, pady=(10, 2))
        self._label(
            db_frame, "Clear all saved diagnosis logs from the local SQLite database.",
            10, fg=COLORS["text_muted"], bg="#F8FAFC"
        ).pack(anchor=tk.W, padx=14, pady=(0, 10))

        btn_purge = tk.Button(
            db_frame, text="🗑️ Clear Diagnostic History",
            command=self._purge_history_db,
            font=self._font(10, "bold"), fg="white", bg="#DC2626",
            activebackground="#B91C1C", activeforeground="white",
            relief="flat", cursor="hand2", padx=12, pady=6
        )
        btn_purge.pack(anchor=tk.W, padx=14, pady=(0, 14))

    def _purge_history_db(self):
        if messagebox.askyesno("Confirm Purge", "Are you sure you want to delete all historical logs? This cannot be undone."):
            self.cursor.execute("DELETE FROM history")
            self.conn.commit()
            messagebox.showinfo("Purged", "Diagnostic history database cleared.")

    def load_history_table(self):
        for item in self.hist_tree.get_children():
            self.hist_tree.delete(item)

        self.cursor.execute("SELECT id, timestamp, disease, confidence, mode FROM history ORDER BY id DESC")
        rows = self.cursor.fetchall()

        for row in rows:
            r_id, time_str, disease, conf, mode = row
            self.hist_tree.insert("", tk.END, values=(r_id, time_str, disease, f"{conf:.1f}%", mode))

    def export_report(self):
        report_content = self.report_area.get("1.0", tk.END).strip()
        disease_title = self.disease_label.cget("text")

        if not report_content or disease_title == "Awaiting Input Data":
            messagebox.showwarning("Export Warning", "No completed diagnosis to export yet. Please run a diagnosis first.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text file", "*.txt"), ("All files", "*.*")],
            title="Save Diagnostic Report As"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(report_content)
            messagebox.showinfo("Export Success", f"Report saved successfully:\n{file_path}")

    def export_pdf_report(self):
        disease_title = self.disease_label.cget("text")
        if disease_title == "Awaiting Input Data":
            messagebox.showwarning("Export Warning", "Please run a diagnosis before exporting a PDF.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Document", "*.pdf")],
            title="Save PDF Diagnostic Report"
        )
        if not file_path:
            return

        try:
            doc = SimpleDocTemplate(file_path, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
            styles = getSampleStyleSheet()
            story = []

            title_style = ParagraphStyle(
                'DocTitle',
                parent=styles['Heading1'],
                fontSize=20,
                textColor=colors.HexColor("#022C22"),
                spaceAfter=12
            )
            story.append(Paragraph("CropPulse AI - Diagnostic Field Report", title_style))
            story.append(Spacer(1, 10))

            data = [
                ["Field Property", "Diagnostic Value"],
                ["Disease Identified", disease_title],
                ["Confidence Rating", self.confidence_text.cget("text")],
                ["Report Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
            ]
            t = Table(data, colWidths=[160, 380])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#059669")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(t)
            story.append(Spacer(1, 16))

            report_body = self.report_area.get("1.0", tk.END).strip()
            body_style = ParagraphStyle('ReportBody', fontName='Courier', fontSize=9, leading=12)
            for line in report_body.split("\n"):
                story.append(Paragraph(line.replace(" ", "&nbsp;"), body_style))

            doc.build(story)
            messagebox.showinfo("Export Success", f"PDF report saved successfully:\n{file_path}")
        except Exception as e:
            messagebox.showerror("PDF Export Error", str(e))

    def load_model_async(self):
        def _load():
            model_path = os.path.join("models", "crop_disease_model.h5")
            json_path = os.path.join("models", "class_names.json")

            if not os.path.exists(model_path) or not os.path.exists(json_path):
                self.root.after(0, lambda: self.sys_status_label.config(text="● Image Model Missing", fg="#F59E0B"))
                return

            try:
                self.model = tf.keras.models.load_model(model_path)
                with open(json_path, "r") as f:
                    self.class_names = json.load(f)
                self.root.after(0, lambda: self.sys_status_label.config(text="● AI Model Ready", fg="#34D399"))
            except Exception:
                self.root.after(0, lambda: self.sys_status_label.config(text="● Load Error", fg="#EF4444"))

        threading.Thread(target=_load, daemon=True).start()

    def clear_symptoms(self):
        for var in self.symptom_vars.values():
            var.set(False)

    def upload_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Crop Leaf Image",
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if file_path:
            self.current_image_path = file_path
            self.display_preview(file_path)

    def display_preview(self, file_path):
        img = Image.open(file_path)
        img.thumbnail((380, 220), Image.Resampling.LANCZOS)
        self.preview_tk = ImageTk.PhotoImage(img)

        self.preview_label.config(image=self.preview_tk, text="")
        self.preview_label.image = self.preview_tk

    def open_camera_modal(self):
        if not HAS_OPENCV:
            messagebox.showerror("OpenCV Missing", "Run 'pip install opencv-python' in terminal to use camera features.")
            return

        cam_win = tk.Toplevel(self.root)
        cam_win.title("WebCam Capture - CropPulse")
        cam_win.geometry("640x520")
        cam_win.configure(bg=COLORS["card_bg"])
        cam_win.transient(self.root)
        cam_win.grab_set()

        cam_label = tk.Label(cam_win, bg="black")
        cam_label.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        cap = cv2.VideoCapture(0)

        def update_frame():
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                img.thumbnail((600, 440))
                img_tk = ImageTk.PhotoImage(image=img)
                cam_label.img_tk = img_tk
                cam_label.configure(image=img_tk)
                cam_label.current_frame = frame
                cam_win.after(15, update_frame)

        def capture_and_close():
            if hasattr(cam_label, 'current_frame'):
                temp_path = os.path.join("models", "temp_cap.jpg")
                os.makedirs("models", exist_ok=True)
                cv2.imwrite(temp_path, cam_label.current_frame)
                self.current_image_path = temp_path
                self.display_preview(temp_path)
            cap.release()
            cam_win.destroy()

        def on_cancel():
            cap.release()
            cam_win.destroy()

        cam_win.protocol("WM_DELETE_WINDOW", on_cancel)

        btn_snap = tk.Button(
            cam_win, text="📸 SNAP LEAF PHOTO", command=capture_and_close,
            font=self._font(11, "bold"), fg="white", bg=COLORS["primary"],
            pady=8, relief="flat", cursor="hand2"
        )
        btn_snap.pack(fill=tk.X, padx=12, pady=(0, 12))

        update_frame()

    def evaluate_symptoms_only(self, symptoms):
        s_set = set(symptoms)

        if "Cigar-Shaped Tan Lesions" in s_set:
            return "Maize: Northern Corn Leaf Blight (NCLB)", 92.0, [
                "• Apply foliar fungicides like Mancozeb or Azoxystrobin early.",
                "• Practice crop rotation with non-host crops (legumes/soybeans).",
                "• Plant resistant hybrid seed varieties in the next cycle."
            ]
        elif "Rectangular Leaf Spots" in s_set:
            return "Maize: Gray Leaf Spot (GLS)", 89.0, [
                "• Apply triazole or strobilurin fungicides at flowering stage.",
                "• Plow under crop residue to reduce fungal spore carryover.",
                "• Ensure adequate plant spacing to encourage airflow."
            ]
        elif "Powdery Brown Rust Pustules" in s_set:
            return "Maize: Common Rust (Puccinia sorghi)", 91.0, [
                "• Apply sulfur or copper-based sprays if rust hits early.",
                "• Monitor lower canopy leaves weekly for pustule spread.",
                "• Select resistant maize cultivars for high-humidity areas."
            ]
        elif "Chewed Leaf Whorls / Holes" in s_set:
            return "Maize: Fall Armyworm (Spodoptera frugiperda)", 94.0, [
                "• Apply Emamectin Benzoate or Chlorantraniliprole into the whorls.",
                "• Handpick caterpillars on small acreage plots.",
                "• Deploy pheromone traps for early adult moth detection."
            ]
        elif "Yellow Chlorotic Mosaic Streaks" in s_set:
            return "Maize: Maize Streak Virus (MSV)", 88.0, [
                "• Control leafhopper vectors using imidacloprid seed treatment.",
                "• Remove infected viral plants to prevent field-wide infection.",
                "• Plant early in the season to avoid high leafhopper populations."
            ]
        elif "Swollen Galls on Ears / Tassels" in s_set:
            return "Maize: Corn Smut (Ustilago maydis)", 90.0, [
                "• Remove swollen galls before they rupture and release spores.",
                "• Avoid mechanical injury during field cultivation.",
                "• Balance soil nitrogen levels to avoid lush tissue susceptibility."
            ]
        elif "White/Pink Mold on Ear Grains" in s_set or "Stalk Soft Rot / Lodging" in s_set:
            return "Maize: Fusarium / Gibberella Stalk & Ear Rot", 86.0, [
                "• Harvest early if ear rot is widespread to avoid mycotoxins.",
                "• Ensure balanced soil potassium and nitrogen levels.",
                "• Store harvested grain at moisture levels below 13%."
            ]
        elif "Water-Soaked Dark Lesions" in s_set:
            return "Tomato: Late Blight (Phytophthora infestans)", 93.0, [
                "• Apply protective copper octanoate or Chlorothalonil sprays.",
                "• Destroy infected vines immediately to stop airborne spores.",
                "• Avoid overhead irrigation; keep foliage dry."
            ]
        elif "Concentric 'Target Ring' Spots" in s_set:
            return "Tomato: Early Blight (Alternaria solani)", 90.0, [
                "• Prune infected lower leaves touching soil line.",
                "• Apply copper or Mancozeb fungicide every 7-10 days.",
                "• Apply organic mulch around base to prevent soil splashback."
            ]
        elif "Upward Leaf Curling / Cupping" in s_set:
            return "Tomato: Yellow Leaf Curl Virus (TYLCV)", 88.0, [
                "• Control whitefly vectors using insecticidal soap or yellow sticky traps.",
                "• Cover young plants with fine insect netting.",
                "• Remove symptomatic virus-infected plants immediately."
            ]
        elif "Black Speckles / Small Spots" in s_set:
            return "Tomato: Bacterial Speck / Spot", 85.0, [
                "• Spray copper hydroxide mixed with mancozeb for resistance control.",
                "• Avoid field work when foliage is wet.",
                "• Use certified disease-free seeds and seedlings."
            ]
        elif "Dark Sunken Fruit Bottoms" in s_set:
            return "Tomato: Blossom End Rot (Calcium Deficiency)", 95.0, [
                "• Maintain consistent soil moisture; avoid deep wet/dry cycles.",
                "• Apply foliar calcium spray (calcium chloride/nitrate).",
                "• Check soil pH (aim for 6.2 - 6.8 range)."
            ]
        elif "Velvety Mold under Leaves" in s_set:
            return "Tomato: Leaf Mold (Passalora fulva)", 87.0, [
                "• Increase greenhouse ventilation and lower indoor humidity.",
                "• Prune excessive canopy leaves to enhance airflow.",
                "• Apply bio-fungicide Bacillus subtilis."
            ]
        elif "Purple / Red Leaf Margins" in s_set:
            return "Nutrient Defic: Phosphorus Deficiency / Cold Stress", 83.0, [
                "• Apply soluble high-phosphorus fertilizer (e.g., Bone meal, DAP).",
                "• Check soil pH as cold or acidic soil inhibits P uptake."
            ]
        elif "V-Shaped Tip Chlorosis" in s_set:
            return "Nutrient Defic: Nitrogen Deficiency", 82.0, [
                "• Apply urea, ammonium nitrate, or organic blood meal.",
                "• Irrigate properly to carry nitrogen into active root zone."
            ]
        elif "White Powdery Surface Coating" in s_set:
            return "General: Powdery Mildew Fungal Infection", 89.0, [
                "• Apply neem oil, sulfur spray, or potassium bicarbonate solution.",
                "• Thin foliage to facilitate sunlight exposure and air circulation."
            ]
        elif "Seedling Stem Collapse (Damping)" in s_set:
            return "General: Damping Off (Pythium / Rhizoctonia)", 91.0, [
                "• Use sterile potting soil for seedling trays.",
                "• Avoid overwatering and damp soil conditions."
            ]
        elif "Stem Vascular Browning" in s_set or "Wilting / Drooping Foliage" in s_set:
            return "General: Vascular Fusarium / Bacterial Wilt", 84.0, [
                "• Drench root zone with Trichoderma viride bio-agent.",
                "• Practice strict multi-year crop rotation."
            ]
        else:
            return "General Crop Stress / Unclassified Pathology", 70.0, [
                "• Isolate plant sample and observe symptoms over 48 hours.",
                "• Ensure optimal soil pH, drainage, and balanced N-P-K nutrients.",
                "• Consult local agricultural extension officers for sample testing."
            ]

    def analyze_image_only(self):
        """Dedicated action handler for image-only diagnosis."""
        if not self.current_image_path:
            messagebox.showwarning("Image Required", "Please upload a photo or capture one using the camera first.")
            return

        if not self.model:
            messagebox.showerror("Model Missing", "AI Model is not loaded. Train/load your model first.")
            return

        self.disease_label.config(text="Analyzing Leaf Image Matrix...")
        self.report_area.delete("1.0", tk.END)
        self.report_area.insert(tk.END, "Processing neural network prediction on leaf sample...\n")

        def _infer():
            try:
                img = Image.open(self.current_image_path).convert("RGB")
                img_resized = img.resize((224, 224))
                img_array = np.array(img_resized, dtype=np.float32) / 255.0
                img_array = np.expand_dims(img_array, axis=0)

                preds = self.model.predict(img_array, verbose=0)
                pred_idx = int(np.argmax(preds[0]))
                conf = float(np.max(preds[0])) * 100

                raw_class = self.class_names.get(str(pred_idx), "Unknown Condition")
                clean_name = raw_class.replace("___", " - ").replace("_", " ")

                recs = []
                if "healthy" in clean_name.lower():
                    recs = ["• Foliage appears healthy with no major active lesions.", "• Maintain regular irrigation and weed control."]
                elif "blight" in clean_name.lower():
                    recs = ["• Spray copper or fungicide.", "• Remove infected leaves to stop spore dissemination."]
                else:
                    recs = ["• Apply targeted treatment or bio-fungicide.", "• Ensure proper plant spacing for canopy aeration."]

                self.root.after(0, lambda: self.update_report_ui(
                    clean_name, conf, [], recs, mode="Visual Image AI Only"
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Analysis Error", str(e)))

        threading.Thread(target=_infer, daemon=True).start()

    def analyze_input(self):
        selected_symptoms = [s for s, var in self.symptom_vars.items() if var.get()]
        has_image = self.current_image_path is not None
        has_symptoms = len(selected_symptoms) > 0

        if not has_image and not has_symptoms:
            messagebox.showwarning(
                "Input Required",
                "Please upload an image OR select at least one tomato/maize symptom to perform a diagnosis."
            )
            return

        if not has_image and has_symptoms:
            disease_name, confidence, recommendations = self.evaluate_symptoms_only(selected_symptoms)
            self.update_report_ui(disease_name, confidence, selected_symptoms, recommendations, mode="Symptom Diagnostic Engine")
            return

        if has_image:
            if not self.model:
                if has_symptoms:
                    disease_name, confidence, recommendations = self.evaluate_symptoms_only(selected_symptoms)
                    self.update_report_ui(disease_name, confidence, selected_symptoms, recommendations, mode="Symptom Fallback Engine")
                else:
                    messagebox.showerror("Model Missing", "AI Model is not loaded. Train/load your model first.")
                return

            self.disease_label.config(text="Analyzing Leaf Matrix...")
            self.report_area.delete("1.0", tk.END)
            self.report_area.insert(tk.END, "Processing neural network prediction...\n")

            def _infer():
                try:
                    img = Image.open(self.current_image_path).convert("RGB")
                    img_resized = img.resize((224, 224))
                    img_array = np.array(img_resized, dtype=np.float32) / 255.0
                    img_array = np.expand_dims(img_array, axis=0)

                    preds = self.model.predict(img_array, verbose=0)
                    pred_idx = int(np.argmax(preds[0]))
                    conf = float(np.max(preds[0])) * 100

                    raw_class = self.class_names.get(str(pred_idx), "Unknown Condition")
                    clean_name = raw_class.replace("___", " - ").replace("_", " ")

                    recs = []
                    if "healthy" in clean_name.lower():
                        recs = ["• Foliage appears healthy with no major active lesions.", "• Maintain regular irrigation and weed control."]
                    elif "blight" in clean_name.lower():
                        recs = ["• Spray copper or fungicide.", "• Remove infected leaves to stop spore dissemination."]
                    else:
                        recs = ["• Apply targeted treatment or bio-fungicide.", "• Ensure proper plant spacing for canopy aeration."]

                    self.root.after(0, lambda: self.update_report_ui(
                        clean_name, conf, selected_symptoms, recs,
                        mode="Image + Symptom Combined" if has_symptoms else "Visual Image AI"
                    ))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("Analysis Error", str(e)))

            threading.Thread(target=_infer, daemon=True).start()

    def update_report_ui(self, disease_name, confidence, symptoms, recommendations, mode="Diagnostic Engine"):
        self.disease_label.config(text=disease_name)
        self.confidence_text.config(text=f"Confidence Score: {confidence:.1f}% ({mode})")

        self.conf_bar.delete("all")
        bar_width = self.conf_bar.winfo_width()
        if bar_width <= 1:
            bar_width = 320
        fill_width = int(bar_width * (confidence / 100.0))

        if confidence >= 85.0:
            bar_color = "#059669"
            self.badge_label.config(
                text="●  HIGH CONFIDENCE DIAGNOSIS",
                fg=COLORS["badge_success_fg"], bg=COLORS["badge_success_bg"]
            )
        elif confidence >= 65.0:
            bar_color = "#D97706"
            self.badge_label.config(
                text="●  MODERATE CONFIDENCE DIAGNOSIS",
                fg=COLORS["badge_warning_fg"], bg=COLORS["badge_warning_bg"]
            )
        else:
            bar_color = "#DC2626"
            self.badge_label.config(
                text="●  LOW CONFIDENCE DIAGNOSIS",
                fg=COLORS["badge_danger_fg"], bg=COLORS["badge_danger_bg"]
            )

        self.conf_bar.create_rectangle(0, 0, fill_width, 10, fill=bar_color, width=0)

        report = []
        report.append("=" * 52)
        report.append(f"  DIAGNOSIS : {disease_name}")
        report.append(f"  ACCURACY  : {confidence:.1f}%")
        report.append(f"  ENGINE    : {mode}")
        report.append("=" * 52 + "\n")

        report.append("🔍 CHECKED VISUAL SYMPTOMS:")
        if symptoms:
            for s in symptoms:
                report.append(f"  [✓] {s}")
        else:
            report.append("  (No specific visual symptoms checked)")
        report.append("\n" + "-" * 52 + "\n")

        report.append("📋 ACTIONABLE TREATMENT PLAN:\n")
        for rec in recommendations:
            report.append(f"  {rec}")

        self.report_area.delete("1.0", tk.END)
        self.report_area.insert(tk.END, "\n".join(report))

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sym_str = ", ".join(symptoms) if symptoms else "None"
        self.cursor.execute(
            "INSERT INTO history (timestamp, disease, confidence, mode, symptoms) VALUES (?, ?, ?, ?, ?)",
            (timestamp, disease_name, confidence, mode, sym_str)
        )
        self.conn.commit()


if __name__ == "__main__":
    root = tk.Tk()
    app = CropPulseApp(root)
    root.mainloop()