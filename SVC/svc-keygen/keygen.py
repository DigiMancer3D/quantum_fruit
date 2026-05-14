import tkinter as tk
from tkinter import messagebox, filedialog
from fruit_bitmapper import FruitBitmapper
import hashlib
import json
import os
import time

class SVCKeygen:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SVC Keygen — Fruit Bitmapper + PQC Roles")
        self.root.geometry("620x420")
        self.bitmapper = FruitBitmapper()
        self.create_ui()

    def create_ui(self):
        tk.Label(self.root, text="Self-Verifying Coin Key Generator", font=("Arial", 18, "bold")).pack(pady=15)
        tk.Label(self.root, text="Uses upgraded Fruit Bitmapper + scent-maths + epoch", fg="blue").pack()

        tk.Button(self.root, text="GENERATE NEW KEYCHAIN", command=self.generate_keychain,
                  width=40, height=3, font=("Arial", 12, "bold"), bg="#4CAF50", fg="white").pack(pady=30)

        self.status_label = tk.Label(self.root, text="Ready — click button to start", fg="green", font=("Arial", 10))
        self.status_label.pack(pady=10)

    def generate_keychain(self):
        try:
            bitmap = self.bitmapper.generate_bitmap()
            master_seed = self.bitmapper.extract_high_entropy_seed(bitmap)

            roles = ["fill", "spend", "last-send", "rolling", "mix", "fuse", "cut", "multi-sig", "vault"]
            keychain = {
                "epoch": self.bitmapper.epoch,
                "master_seed": master_seed.hex(),
                "roles": {}
            }

            for role in roles:
                role_seed = hashlib.sha3_512(master_seed + role.encode()).digest()
                keychain["roles"][role] = role_seed.hex()

            filename = f"svc_keychain_{self.bitmapper.epoch}.kchain"
            with open(filename, "w") as f:
                json.dump(keychain, f, indent=2)

            messagebox.showinfo("Success!", f"Keychain created!\n\nFile: {filename}\n9 PQC role keys generated")
            self.status_label.config(text=f"✅ Saved: {filename}", fg="green")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = SVCKeygen()
    app.run()
