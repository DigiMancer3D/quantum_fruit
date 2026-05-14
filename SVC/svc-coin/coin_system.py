import ctypes
import json
import os
from tkinter import Tk, Label, Button, messagebox, filedialog

# Load the shared library we just built
lib = ctypes.CDLL("../svc-core/libspx_qec.so")

# Function signatures
lib.spx_init_context.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
lib.spx_compress.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.POINTER(ctypes.c_size_t)]
lib.spx_decompress.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_size_t]
lib.spx_fill.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
lib.spx_extract.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
lib.spx_verify.argtypes = [ctypes.c_char_p, ctypes.c_uint32]
lib.spx_free.argtypes = [ctypes.c_char_p]

class CoinSystem:
    def __init__(self):
        self.root = Tk()
        self.root.title("SVC Coin System — Self-Verifying Coin Manipulator")
        self.root.geometry("700x500")
        self.keychain = None
        self.coin_bin = None
        self.create_ui()

    def create_ui(self):
        Label(self.root, text="Self-Verifying Coin System", font=("Arial", 18, "bold")).pack(pady=10)
        Label(self.root, text="Uses SPX-QEC + Phase 2 Keychain", fg="blue").pack()

        Button(self.root, text="1. Load Keychain (from Phase 2)", command=self.load_keychain, width=50, height=2).pack(pady=8)
        Button(self.root, text="2. Create New Coin", command=self.create_new_coin, width=50, height=2).pack(pady=8)
        Button(self.root, text="3. Fill Coin (add tx/proof)", command=self.fill_coin, width=50, height=2).pack(pady=8)
        Button(self.root, text="4. Extract Random Tx/Proof", command=self.extract_random, width=50, height=2).pack(pady=8)
        Button(self.root, text="5. Verify Coin", command=self.verify_coin, width=50, height=2).pack(pady=8)
        Button(self.root, text="6. Save Coin Bin", command=self.save_coin, width=50, height=2).pack(pady=8)

        self.status = Label(self.root, text="Ready — load a keychain first", fg="green", font=("Arial", 10))
        self.status.pack(pady=20)

    def load_keychain(self):
        path = filedialog.askopenfilename(title="Select svc_keychain_*.json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path) as f:
                self.keychain = json.load(f)
            self.status.config(text=f"✅ Loaded keychain (epoch {self.keychain['epoch']})", fg="green")
            messagebox.showinfo("Success", f"Loaded {len(self.keychain['roles'])} role keys")

    def create_new_coin(self):
        if not self.keychain:
            messagebox.showerror("Error", "Load a keychain first!")
            return
        self.coin_bin = f"SPX!NEW_COIN|epoch:{self.keychain['epoch']}|master:{self.keychain['master_seed'][:16]}..."
        self.status.config(text="✅ New coin created (empty history)", fg="green")

    def fill_coin(self):
        if not self.coin_bin:
            messagebox.showerror("Error", "Create a coin first!")
            return
        data = "tx_amount:1.23|proof:ABC123|last_send:0xdeadbeef"
        key = self.keychain["roles"]["rolling"]
        new_bin_ptr = lib.spx_fill(self.coin_bin.encode(), data.encode(), key.encode())
        self.coin_bin = ctypes.string_at(new_bin_ptr).decode()
        lib.spx_free(new_bin_ptr)
        self.status.config(text="✅ Coin filled with new tx/proof", fg="green")

    def extract_random(self):
        if not self.coin_bin:
            messagebox.showerror("Error", "Create/fill a coin first!")
            return
        key = self.keychain["roles"]["last-send"]
        extracted_ptr = lib.spx_extract(self.coin_bin.encode(), key.encode())
        result = ctypes.string_at(extracted_ptr).decode()
        lib.spx_free(extracted_ptr)
        messagebox.showinfo("Extracted", f"Random tx/proof slice:\n{result}")

    def verify_coin(self):
        if not self.coin_bin:
            messagebox.showerror("Error", "No coin to verify!")
            return
        ok = lib.spx_verify(self.coin_bin.encode(), 0x53505821)
        msg = "✅ Coin is valid (SPX self-verification passed)" if ok else "❌ Coin verification FAILED"
        self.status.config(text=msg, fg="green" if ok else "red")
        messagebox.showinfo("Verification", msg)

    def save_coin(self):
        if not self.coin_bin:
            messagebox.showerror("Error", "No coin to save!")
            return
        path = filedialog.asksaveasfilename(defaultextension=".coinbin")
        if path:
            with open(path, "w") as f:
                f.write(self.coin_bin)
            messagebox.showinfo("Saved", f"Coin saved to {path}")

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CoinSystem()
    app.run()
