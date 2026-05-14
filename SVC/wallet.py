import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog, scrolledtext
import ctypes
import json
import hashlib
import time
import threading
import asyncio
from p2p_node import SVC_P2PNode

lib = ctypes.CDLL("../svc-core/libspx_qec.so")

class SVCWallet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SVC Wallet (Simple P2P Mesh)")
        self.root.geometry("800x600")
        self.keychain = None
        self.p2p = SVC_P2PNode()
        self.p2p.on_receive_coin = self._on_coin_received
        self.p2p.on_ack_received = self._on_ack_received
        self.p2p_thread = None
        self.create_ui()

    def create_ui(self):
        tk.Label(self.root, text="SVC Wallet (Simple P2P Mesh)", font=("Arial", 18, "bold")).pack(pady=10)
        tk.Label(self.root, text="Anonymous peer-to-peer transfers + return-ack coins", fg="blue").pack()

        tk.Button(self.root, text="1. Load Keychain", command=self.load_keychain, width=50, height=2).pack(pady=5)
        tk.Button(self.root, text="2. Start Simple Mesh", command=self.start_p2p, width=50, height=2, bg="#2196F3").pack(pady=5)
        tk.Button(self.root, text="3. Send Coin via Mesh", command=self.send_coin, width=50, height=2).pack(pady=5)
        tk.Button(self.root, text="4. Send Test Message", command=self.send_test_message, width=50, height=2, bg="#FF9800").pack(pady=5)
        tk.Button(self.root, text="5. Show My Wallet Address", command=self.show_address, width=50, height=2).pack(pady=5)
        tk.Button(self.root, text="6. Connect to Peer (manual)", command=self.connect_to_peer, width=50, height=2, bg="#4CAF50").pack(pady=5)
        tk.Button(self.root, text="7. Scan Local Peers (8000-8050)", command=self.scan_local_peers, width=50, height=2, bg="#FF5722").pack(pady=5)
        tk.Button(self.root, text="Debug Peers", command=self.debug_peers, width=50, height=2, bg="#9C27B0").pack(pady=5)

        self.log = scrolledtext.ScrolledText(self.root, height=15)
        self.log.pack(pady=10, padx=10, fill="both", expand=True)

    def log_message(self, msg):
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log.see("end")

    def load_keychain(self):
        path = filedialog.askopenfilename(title="Select keychain", filetypes=[("Keychain", "*.kchain")])
        if path:
            with open(path) as f:
                self.keychain = json.load(f)
            self.log_message(f"✅ Loaded keychain (epoch {self.keychain['epoch']})")

    def start_p2p(self):
        if self.p2p_thread and self.p2p_thread.is_alive():
            self.log_message("Mesh already running")
            return
        self.p2p_thread = threading.Thread(target=self._run_p2p, daemon=True)
        self.p2p_thread.start()
        self.log_message("Starting mesh...")

    def _run_p2p(self):
        asyncio.run(self.p2p.start())

    def connect_to_peer(self):
        if not self.p2p_thread or not self.p2p_thread.is_alive():
            messagebox.showerror("Error", "Start mesh first!")
            return
        port_str = simpledialog.askstring("Connect to Peer", "Enter peer port:", initialvalue="8001")
        if port_str:
            asyncio.run(self.p2p.connect_to_peer(int(port_str)))
            self.log_message(f"Manual connect to port {port_str}")

    def scan_local_peers(self):
        if not self.p2p_thread or not self.p2p_thread.is_alive():
            messagebox.showerror("Error", "Start mesh first!")
            return
        self.log_message("🔎 Scanning 8000-8050 for peers...")
        for p in range(8000, 8051):
            if p == self.p2p.port: continue
            asyncio.run(self.p2p.connect_to_peer(p))
        self.log_message("Scan finished.")

    def debug_peers(self):
        count = len(self.p2p.writers)
        self.log_message(f"Debug: {count} active peer connection(s)")

    def send_coin(self):
        if not self.keychain:
            messagebox.showerror("Error", "Load keychain first!")
            return
        coin_path = filedialog.askopenfilename(title="Select coin to send (.coinbin)", filetypes=[("Coin", "*.coinbin")])
        if not coin_path: return
        with open(coin_path) as f:
            coin_data = f.read()
        receiver = simpledialog.askstring("Receiver", "Enter receiver wallet address")
        if not receiver: return
        asyncio.run(self.p2p.broadcast_coin(coin_data, receiver))
        self.log_message(f"✅ Sent coin to {receiver}")

    def send_test_message(self):
        asyncio.run(self.p2p.broadcast_coin("TEST_MESSAGE", "test-receiver"))
        self.log_message("✅ Sent test message")

    def _on_coin_received(self, coin_data, receiver):
        def safe_show():
            self.log_message(f"✅ Coin received via mesh for {receiver}")
            self.p2p.send_ack(receiver)          # now synchronous
            messagebox.showinfo("Received!", f"Coin received from {receiver}\nReturn-ack generated.")
        self.root.after(0, safe_show)

    def _on_ack_received(self, receiver):
        def safe_show():
            self.log_message(f"✅ Coin acknowledged by {receiver}")
            messagebox.showinfo("Acknowledged!", f"Your coin was received by {receiver}")
        self.root.after(0, safe_show)

    def show_address(self):
        if not self.keychain:
            messagebox.showerror("Error", "Load keychain first!")
            return
        addr = "SVC://" + hashlib.sha256(self.keychain["master_seed"].encode()).hexdigest()[:16]
        self.root.clipboard_clear()
        self.root.clipboard_append(addr)
        self.root.update()
        messagebox.showinfo("Your Wallet Address", f"Your address:\n{addr}\n\n✅ Copied to clipboard!")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SVCWallet()
    app.run()
