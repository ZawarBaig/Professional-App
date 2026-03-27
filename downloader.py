import sys
import os
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class MrBaigDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("Mr.Baig Downloader")
        self.root.geometry("850x650")
        
        # --- COLOR PALETTE ---
        self.bg_color = "#F0F4F8"        # Soft blue-grey background
        self.header_bg = "#2C3E50"       # Dark slate blue
        self.header_fg = "#FFFFFF"       # White text
        self.accent_color = "#3498DB"    # Vibrant blue buttons
        self.accent_hover = "#2980B9"    # Darker blue on hover
        self.text_color = "#333333"      # Dark grey text
        
        self.root.configure(bg=self.bg_color)
        
        # Load the custom icon
        icon_path = resource_path('icon.ico')
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
            
        self.ffmpeg_path = resource_path('ffmpeg.exe')
        
        self.setup_styles()
        
        self.url_var = tk.StringVar()
        self.download_path = tk.StringVar(value=os.path.join(os.path.expanduser('~'), 'Downloads'))
        
        self.setup_ui()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # General Frame and Label Styles
        style.configure("TFrame", background=self.bg_color)
        style.configure("TLabel", background=self.bg_color, foreground=self.text_color, font=("Segoe UI", 10))
        
        # Header Style
        style.configure("Header.TLabel", background=self.header_bg, foreground=self.header_fg, font=("Segoe UI", 18, "bold"), padding=15)
        
        # Professional Button Style
        style.configure("Primary.TButton", background=self.accent_color, foreground=self.header_fg, font=("Segoe UI", 10, "bold"), borderwidth=0, padding=8)
        style.map("Primary.TButton", background=[("active", self.accent_hover)])
        
        # Treeview (List) Style
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28, background="#FFFFFF", fieldbackground="#FFFFFF", borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#BDC3C7", foreground="#2C3E50", padding=5)
        style.map("Treeview", background=[("selected", self.accent_color)], foreground=[("selected", "#FFFFFF")])

    def setup_ui(self):
        # 1. Full-width Header
        header = ttk.Label(self.root, text="Mr.Baig Downloader", style="Header.TLabel", anchor="center")
        header.pack(fill="x")

        # 2. Main Content Container
        content_frame = ttk.Frame(self.root, padding=20)
        content_frame.pack(fill="both", expand=True)

        # URL Input
        url_frame = ttk.Frame(content_frame)
        url_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(url_frame, text="Video URL:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, font=("Segoe UI", 11))
        url_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        fetch_btn = ttk.Button(url_frame, text="Download", style="Primary.TButton", command=self.start_fetch_thread)
        fetch_btn.pack(side="left")

        # Save Path
        path_frame = ttk.Frame(content_frame)
        path_frame.pack(fill="x", pady=(0, 15))
        
        ttk.Label(path_frame, text="Save To:", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 24))
        path_entry = ttk.Entry(path_frame, textvariable=self.download_path, font=("Segoe UI", 10), state="readonly")
        path_entry.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        browse_btn = ttk.Button(path_frame, text="Browse", style="Primary.TButton", command=self.browse_folder)
        browse_btn.pack(side="left")

        # Formats List (Treeview)
        tree_frame = ttk.Frame(content_frame)
        tree_frame.pack(fill="both", expand=True, pady=(0, 15))
        
        columns = ("ID", "Extension", "Resolution", "Quality/Note", "Size")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", selectmode="browse")
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        
        self.tree.column("ID", width=60)
        self.tree.column("Extension", width=80)
        self.tree.column("Resolution", width=120)
        self.tree.column("Quality/Note", width=300)
        self.tree.column("Size", width=100)
        
        # Adding alternating row colors (Zebra stripes)
        self.tree.tag_configure('oddrow', background="#F9F9F9")
        self.tree.tag_configure('evenrow', background="#FFFFFF")
            
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Download Button (Centered)
        self.download_btn = ttk.Button(content_frame, text="↓ Download Selected Format", style="Primary.TButton", command=self.start_download_thread, state="disabled")
        self.download_btn.pack(pady=(0, 15), ipadx=20, ipady=5)

        # Status and Progress
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(content_frame, textvariable=self.status_var, font=("Segoe UI", 10, "italic"), foreground="#7F8C8D")
        self.status_label.pack(anchor="w", pady=(0, 5))

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(content_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x")

        # 3. Footer with Developer Name
        footer_frame = tk.Frame(self.root, bg=self.bg_color)
        footer_frame.pack(side="bottom", fill="x", padx=20, pady=10)
        
        dev_label = tk.Label(footer_frame, text="Developed By Zawar Baig", bg=self.bg_color, fg="#95A5A6", font=("Segoe UI", 9, "bold italic"))
        dev_label.pack(side="left")

    def browse_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)

    def format_size(self, bytes_size):
        if not bytes_size: return "Unknown"
        mb = bytes_size / (1024 * 1024)
        return f"{mb:.2f} MB"

    def start_fetch_thread(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("Error", "Please enter a valid URL.")
            return
        
        self.status_var.set("Fetching available formats... Please wait.")
        self.tree.delete(*self.tree.get_children())
        self.download_btn.config(state="disabled")
        
        threading.Thread(target=self.fetch_formats, args=(url,), daemon=True).start()

    def fetch_formats(self, url):
        ydl_opts = {
            'quiet': True, 
            'no_warnings': True,
            'ffmpeg_location': self.ffmpeg_path 
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                formatted_list = []
                formatted_list.append(("best", "mp4/mkv", "Best Quality", "Auto-merges best video and audio", "Auto"))

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
                    
                    formatted_list.append((f_id, ext, res, details, size_str))

                self.root.after(0, self.update_treeview, formatted_list)

        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Failed to fetch formats:\n{str(e)}"))
            self.root.after(0, lambda: self.status_var.set("Ready"))

    def update_treeview(self, formats):
        for index, item in enumerate(formats):
            # Apply zebra striping based on odd/even rows
            tag = 'evenrow' if index % 2 == 0 else 'oddrow'
            self.tree.insert("", "end", values=item, tags=(tag,))
            
        self.status_var.set("Formats loaded. Select one and click Download.")
        self.download_btn.config(state="normal")

    def start_download_thread(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Error", "Please select a format from the list first.")
            return
            
        format_id = self.tree.item(selected_item[0])['values'][0]
        url = self.url_var.get().strip()
        save_path = self.download_path.get()
        
        self.download_btn.config(state="disabled")
        self.progress_var.set(0)
        
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

        # Force format_id to string to prevent yt-dlp crashing on pure numbers
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
        finally:
            self.root.after(0, lambda: self.download_btn.config(state="normal"))

if __name__ == "__main__":
    root = tk.Tk()
    app = MrBaigDownloader(root)
    root.mainloop()
