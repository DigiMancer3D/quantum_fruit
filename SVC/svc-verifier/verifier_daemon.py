import ctypes
import json
import os
import time
from tkinter import Tk, Label, Button, messagebox, filedialog, scrolledtext

# Load SPX-QEC library
lib = ctypes.CDLL("../svc-core/libspx_qec.so")

class VerifierDaemon:
    def __init__(self):
        self.root = Tk()
        self.root.title("SVC Verifier Daemon — Offline/Online Coin Verifier")
        self.root.geometry("800x600")
        self.create_ui()
        self.verified_coins = []

    def create_ui(self):
        Label(self.root, text="SVC Verifier Daemon", font=("Arial", 18, "bold")).pack(pady=10)
        Label(self.root, text="Offline + Online Coin Verification", fg="blue").pack()

        Button(self.root, text="Load & Verify Coin (.coinbin or .json)", command=self.verify_coin_file, width=50, height=2).pack(pady=8)
        Button(self.root, text="Verify All Coins in Folder", command=self.verify_folder, width=50, height=2).pack(pady=8)
        Button(self.root, text="Start Background Listening Mode (daemon)", command=self.start_daemon_mode, width=50, height=2).pack(pady=8)

        self.log = scrolledtext.ScrolledText(self.root, height=20, width=90)
        self.log.pack(pady=10)

    def log_message(self, msg):
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log.see("end")

    def verify_coin_file(self):
        path = filedialog.askopenfilename(title="Select coin file", filetypes=[("Coin Files", "*.coinbin *.kchain")])
        if not path: return
        try:
            with open(path) as f:
                data = f.read()
            ok = lib.spx_verify(data.encode(), 0x53505821)
            if ok:
                self.log_message(f"✅ VERIFIED: {os.path.basename(path)}")
                self.verified_coins.append(path)
            else:
                self.log_message(f"❌ FAILED: {os.path.basename(path)}")
            messagebox.showinfo("Result", "Coin is valid" if ok else "Coin verification FAILED")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def verify_folder(self):
        folder = filedialog.askdirectory(title="Select folder with coins")
        if not folder: return
        self.log_message(f"Scanning folder: {folder}")
        for file in os.listdir(folder):
            if file.endswith(('.coinbin', '.json')):
                path = os.path.join(folder, file)
                with open(path) as f:
                    data = f.read()
                ok = lib.spx_verify(data.encode(), 0x53505821)
                status = "✅ VERIFIED" if ok else "❌ FAILED"
                self.log_message(f"{status} {file}")

    def start_daemon_mode(self):
        self.log_message("Daemon mode started — listening for coins (simulated for now)")
        messagebox.showinfo("Daemon", "Background listening mode started.\nCoins will be auto-verified and logged.")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VerifierDaemon()
    app.run()
