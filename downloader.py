import sys
import os
import re
import threading
import urllib.request
import io
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp
from PIL import Image, ImageTk

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MrBaigDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Mr.Baig Downloader")
        self.root.geometry("900x700")
        
        # --- COLOR PALETTE ---
        self.bg_color = "#F0F4F8"
        self.header_bg = "#2C3E50"
        self.header_fg = "#FFFFFF"
        self.accent_color = "#3498DB"
        self.accent_hover = "#2980B9"
        self.text_color = "#333333"
        
        self.root.configure(bg=self.bg_color)
        
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
            
        self.ffmpeg_path = resource_path('ffmpeg.exe')
        self.setup_styles()
        
        self.url_var = tk.StringVar()
        self.download_path = tk.StringVar(value=os.path.join(os.path.expanduser('~'), 'Downloads'))
        
        # Keep track of the current thumbnail image so it doesn't get garbage collected
        self.current_thumbnail = None
        
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=self.header_bg, foreground=self.header_fg, font=("Segoe UI", 18, "bold"), padding=15)
        
        style.configure("Primary.TButton", background=self.accent_color, foreground=self.header_fg, font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Primary.TButton", background=[("active", self.accent_hover)])
        
        style.configure("Danger.TButton", background="#E74C3C", foreground=self.header_fg, font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Danger.TButton", background=[("active", "#C0392B")])

        # Custom Green Progress Bar
        style.configure("Green.Horizontal.TProgressbar", background="#2ECC71") # Green color
        
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28, background="#FFFFFF", fieldbackground="#FFFFFF", borderwidth=1)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#BDC3C7", foreground="#2C3E50", padding=5)
        style.map("Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "#FFFFFF")])

    def setup_ui(self):
        # Header
        header = ttk.Label(self.root, text="Mr.Baig Downloader", style="Header.TLabel", anchor="center")
        header.pack(fill="x")

        # Developer Text (Changed to black)
        dev_label = tk.Label(self.root, text="Developed By Zawar Baig", bg=self.bg_color, fg="black", font=("Segoe UI", 9, "bold italic"))
        dev_label.pack(anchor="w", padx=20, pady=(5, 0))

        content_frame = ttk.Frame(self.root, padding=20)
        content_frame.pack(fill="both", expand=True)

        # URL Input & Buttons
        url_frame = ttk.Frame(content_frame)
        url_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(url_frame, text="Video URL:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Segoe UI", 11))
        url_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        # Paste Button Added
        paste_btn = ttk.Button(url_frame, text="Paste", style="Primary.TButton", command=self.paste_url)
        paste_btn.pack(side="left", padx=(0, 5))

        fetch_btn = ttk.Button(url_frame, text="Download", style="Primary.TButton", command=self.start_fetch_thread)
        fetch_btn.pack(side="left", padx=(0, 5))
        
        clear_btn = ttk.Button(url_frame, text="Clear", style="Danger.TButton", command=self.clear_all)
        clear_btn.pack(side="left")

        # Save Path
        path_frame = ttk.Frame(content_frame)
        path_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(path_frame, text="Save To:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 24))
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path, font=("Segoe UI", 10), state="readonly")
        path_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        browse_btn = ttk.Button(path_frame, text="Browse", style="Primary.TButton", command=self.browse_folder)
        browse_btn.pack(side="left")

        # Video Info Area
        self.info_frame = ttk.Frame(content_frame)
        self.info_frame.pack(fill="x", pady=(0, 15))
        
        self.thumb_label = tk.Label(self.info_frame, bg=self.bg_color)
        self.thumb_label.pack(side="left", padx=(0, 15))
        
        self.title_label = ttk.Label(self.info_frame, text="", font=("Segoe UI", 11, "bold"), wraplength=500)
        self.title_label.pack(side="left", anchor="n")

        # Formats List (Treeview)
        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        columns = ("ID", "Extension", "Resolution", "Quality/Note", "Size", "Action")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        
        self.tree.column("ID", width=50)
        self.tree.column("Extension", width=80)
        self.tree.column("Resolution", width=100)
        self.tree.column("Quality/Note", width=250)
        self.tree.column("Size", width=90)
        self.tree.column("Action", width=140) 
        
        # Resetting text color so only the background alternates
        self.tree.tag_configure('oddrow', background="#F9F9F9", foreground=self.text_color)
        self.tree.tag_configure('evenrow', background="#FFFFFF", foreground=self.text_color)
            
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind('<ButtonRelease-1>', self.on_tree_click)

        # Status and Progress
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(content_frame, textvariable=self.status_var, font=("Segoe UI", 10, "italic"), foreground="#7F8C8D")
        self.status_label.pack(anchor="w", pady=(0, 5))

        self.progress_var = tk.DoubleVar()
        # Applying the Green style here
        self.progress_bar = ttk.Progressbar(content_frame, variable=self.progress_var, maximum=100, style="Green.Horizontal.TProgressbar")
        self.progress_bar.pack(fill="x")

    def paste_url(self):
        """Pastes URL from clipboard into the entry box"""
        try:
            clipboard_content = self.root.clipboard_get()
            self.url_var.set(clipboard_content)
        except tk.TclError:
            pass # Fails silently if clipboard is empty or contains non-text

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)

    def clear_all(self):
        self.url_var.set("")
        self.title_label.config(text="")
        self.thumb_label.config(image='')
        self.current_thumbnail = None
        self.tree.delete(*self.tree.get_children())
        self.status_var.set("Ready")
        self.progress_var.set(0)

    def format_size(self, bytes_size):
        if not bytes_size: return "Unknown"
        mb = bytes_size / (1024 * 1024)
        return f"{mb:.2f} MB"

    def start_fetch_thread(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter a valid URL.")
            return
        
        self.status_var.set("Fetching video information... Please wait.")
        self.tree.delete(*self.tree.get_children())
        self.title_label.config(text="")
        
        threading.Thread(target=self.fetch_formats, args=(url,), daemon=True).start()

    def load_thumbnail(self, thumb_url, title):
        try:
            req = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
            raw_data = urllib.request.urlopen(req).read()
            im = Image.open(io.BytesIO(raw_data))
            
            im.thumbnail((120, 80))
            photo = ImageTk.PhotoImage(im)
            
            self.root.after(0, lambda: self.thumb_label.config(image=photo))
            self.root.after(0, lambda: self.title_label.config(text=title))
            self.current_thumbnail = photo 
        except Exception as e:
            print("Could not load thumbnail:", e)

    def fetch_formats(self, url):
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'ffmpeg_location': self.ffmpeg_path 
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                thumb_url = info.get('thumbnail')
                title = info.get('title', 'Unknown Title')
                if thumb_url:
                    self.load_thumbnail(thumb_url, title)
                else:
                    self.root.after(0, lambda: self.title_label.config(text=title))

                formats = info.get('formats', [])
                formatted_list = []
                
                # Changed action text to look more like a button
                formatted_list.append(("best", "mp4/mkv", "Best Quality", "Auto-merges best video and audio", "Auto", "🔴 Download"))

                for f in formats:
                    f_id = f.get('format_id', 'N/A')
                    ext = f.get('ext', 'N/A')
                    res = f.get('resolution', f.get('width', 'N/A'))
                    if res == 'audio only' or f.get('vcodec') == 'none':
                        res = "Audio Only"
                    elif f.get('height'):
                        res = f"{f.get('width', '?')}x{f.get('height', '?')}"
                    
                    note = f.get('format_note', '')
                    vcodec = f.get('vcodec', '')
                    acodec = f.get('acodec', '')
                    details = f"{note} (V: {vcodec[:4] if vcodec != 'none' else 'none'}, A: {acodec[:4] if acodec != 'none' else 'none'})"
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    size_str = self.format_size(filesize)
                    
                    # Changed action text
                    formatted_list.append((f_id, ext, res, details, size_str, "🔴 Download"))

                self.root.after(0, self.update_treeview, formatted_list)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch formats:\n{str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def update_treeview(self, formats):
        for index, item in enumerate(formats):
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=item, tags=(tag,))
            
        self.status_var.set("Formats loaded. Click '🔴 Download' in any row to start.")

    def on_tree_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell": 
            return
            
        column = self.tree.identify_column(event.x)
        if column == '#6':
            item_id = self.tree.identify_row(event.y)
            if item_id:
                format_id = self.tree.item(item_id, 'values')[0]
                self.start_download(format_id)

    def start_download(self, format_id):
        url = self.url_var.get().strip()
        save_path = self.download_path.get()
        
        self.progress_var.set(0)
        self.status_var.set("Starting download...")
        
        threading.Thread(target=self.download_video, args=(url, format_id, save_path), daemon=True).start()

    def download_video(self, url, format_id, save_path):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

        def progress_hook(d):
            if d['status'] == 'downloading':
                percent_str = ansi_escape.sub('', d.get('_percent_str', '0.0%')).strip('% ')
                speed_str = ansi_escape.sub('', d.get('_speed_str', '0KiB/s')).strip()
                eta_str = ansi_escape.sub('', d.get('_eta_str', '00:00')).strip()
                
                try:
                    percent = float(percent_str)
                    self.root.after(0, self.progress_var.set, percent)
                    self.root.after(0, self.status_var.set, f"Downloading... {percent}% at {speed_str} (ETA: {eta_str})")
                except ValueError:
                    pass
            elif d['status'] == 'finished':
                self.root.after(0, self.status_var.set, "Merging video and audio... Please wait.")
                self.root.after(0, self.progress_var.set, 100)

        fmt_str = 'bestvideo+bestaudio/best' if str(format_id) == 'best' else str(format_id)

        ydl_opts = {
            'format': fmt_str,
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'quiet': True,
            'merge_output_format': 'mp4',
            'ffmpeg_location': self.ffmpeg_path 
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.root.after(0, lambda: self.status_var.set("Download Complete!"))
            self.root.after(0, lambda: messagebox.showinfo("Success", "Video downloaded successfully!"))
        except Exception as e:
            self.root.after(0, lambda: self.status_var.set("Download Failed."))
            self.root.after(0, lambda: messagebox.showerror("Download Error", str(e)))

if __name__ == "__main__":
    root = tk.Tk()
    app = MrBaigDownloader(root)
    root.mainloop()
