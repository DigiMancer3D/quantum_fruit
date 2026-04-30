import tkinter as tk
from tkinter import colorchooser, messagebox, Toplevel, filedialog
import subprocess
import sys
import random
import json
import time
import os
import hashlib
import threading

def install_pillow():
    try:
        from PIL import Image
        return
    except ImportError:
        print("Pillow not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow"])
        print("Pillow installed successfully.")

install_pillow()
from PIL import Image, ImageDraw, ImageTk, ImageFilter

def b58encode(v):
    alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    n = int.from_bytes(v, 'big')
    res = []
    while n:
        n, r = divmod(n, 58)
        res.append(alphabet[r])
    return ''.join(reversed(res))

class FruitBitmapper(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Fruit Bitmapper")
        self.geometry("1070x1080")

        self.canvas_width = 600
        self.canvas_height = 600
        self.bg_color = (245, 232, 199, 255)

        self.image = Image.new("RGBA", (self.canvas_width, self.canvas_height), self.bg_color)
        self.draw = ImageDraw.Draw(self.image)

        self.layers = []
        self.current_color = None
        self.last_fruit = None
        self.last_bump = None

        self.last_region = {}

        # State tracking for consistent epoch + smart filename type
        self.canvas_epoch = None
        self.canvas_source = None  # "Orange", "G1", "Custom", "KEY", etc.

        self.base_scent_profiles = {
            "Orange": {"mu": 0.35, "sigma": 0.22},
            "Lemon": {"mu": 0.65, "sigma": 0.19},
            "Pineapple": {"mu": 0.28, "sigma": 0.31},
            "Strawberry": {"mu": 0.52, "sigma": 0.25},
            "Pomegranate": {"mu": 0.41, "sigma": 0.27},
            "Lime": {"mu": 0.72, "sigma": 0.18},
            "Raspberry": {"mu": 0.48, "sigma": 0.24},
            "G1": {"mu": 0.5, "sigma": 0.35},
            "G2": {"mu": 0.5, "sigma": 0.28},
            "Custom": {"mu": 0.5, "sigma": 0.3}
        }

        self.opacity_on = False
        self.secured_on = False

        self.custom_params = {
            "spacing": 22, "pert": 7, "min_r": 3, "max_r": 8,
            "color": "#006400", "density": 1.0, "use_gaussian_pert": False
        }

        self.width_var = tk.IntVar(value=600)
        self.height_var = tk.IntVar(value=600)

        self.fruits = {
            "Orange": {"default_color": "#FF9F1C", "spacing": 18, "pert": 6, "min_r": 4, "max_r": 9,
                       "math_desc": "Jittered rectangular grid: x = i*spacing + uniform(-pert,pert), y similar. Radius [min_r, max_r]."},
            "Lemon": {"default_color": "#FFEA00", "spacing": 20, "pert": 7, "min_r": 5, "max_r": 11,
                      "math_desc": "Jittered rectangular grid (larger pert & bumps) for lemon peel texture."},
            "Pineapple": {"default_color": "#FFB300", "spacing": 35, "pert": 4, "min_r": 8, "max_r": 15,
                          "math_desc": "Hexagonal staggered grid: y = j*spacing, x = i*spacing + (j%2)*(spacing/2) + jitter. Larger structured bumps."},
            "Strawberry": {"default_color": "#FF4D4D", "spacing": 12, "pert": 8, "min_r": 2, "max_r": 5,
                           "math_desc": "Dense jittered grid with tiny radii mimicking strawberry achenes."},
            "Pomegranate": {"default_color": "#C0392B", "spacing": 26, "pert": 8, "min_r": 6, "max_r": 14,
                            "math_desc": "Jittered rectangular grid with medium spacing + high pert for leathery, seeded pomegranate rind."},
            "Lime": {"default_color": "#7CFC00", "spacing": 18, "pert": 5, "min_r": 4, "max_r": 10,
                     "math_desc": "Tight jittered rectangular grid (smaller pert) for bright, smooth lime peel texture."},
            "Raspberry": {"default_color": "#E30B5D", "spacing": 14, "pert": 6, "min_r": 2, "max_r": 5,
                          "math_desc": "Very dense jittered grid with tiny radii simulating raspberry drupelets."},
            "G1": {"default_color": "#808080", "spacing": 24, "pert": 9, "min_r": 5, "max_r": 13,
                   "math_desc": "Gaussian blur placement: positions/sizes use Gaussian (normal) distribution jitter. Grey bumps for soft blur-like effect."},
            "G2": {"default_color": "#1C1C1C", "spacing": 24, "pert": 9, "min_r": 4, "max_r": 11,
                   "math_desc": "Gaussian sampling placement (crypto-style quantum-resistant seed method): black bumps with Gaussian-distributed locations & sizes."}
        }

        self.build_ui()
        self.update_display()

    def build_ui(self):
        top_frame = tk.Frame(self, bg="#333", height=40)
        top_frame.pack(fill="x")
        top_frame.pack_propagate(False)

        buttons = [
            ("Exit", self.quit_app),
            ("Reset", self.reset_canvas),
            ("Clear", self.clear_canvas),
            ("Export", self.export_crumbs),
            ("Save PNG", self.save_canvas)
        ]
        for text, cmd in buttons:
            btn = tk.Button(top_frame, text=text, command=cmd, bg="#555", fg="white", relief="flat", padx=8)
            btn.pack(side="left", padx=4, pady=5)

        tk.Button(top_frame, text="Export Key (active)", command=self.export_active_key, bg="#4CAF50", fg="white", relief="flat", padx=8).pack(side="left", padx=4, pady=5)
        tk.Button(top_frame, text="Export Secured Key", command=self.export_secured_key, bg="#2196F3", fg="white", relief="flat", padx=8).pack(side="left", padx=4, pady=5)
        tk.Button(top_frame, text="Key", command=self.generate_quantum_key, bg="#9C27B0", fg="white", relief="flat", padx=12, font=("Helvetica", 10, "bold")).pack(side="left", padx=4, pady=5)

        self.opacity_btn = tk.Button(top_frame, text="No Opacity", command=self.toggle_opacity, bg="#555", fg="white", relief="flat", padx=8)
        self.opacity_btn.pack(side="left", padx=4, pady=5)
        self.secured_btn = tk.Button(top_frame, text="Insecure Layers", command=self.toggle_secured, bg="#555", fg="white", relief="flat", padx=8)
        self.secured_btn.pack(side="left", padx=4, pady=5)

        title = tk.Label(self, text="Fruit Bitmapper", font=("Helvetica", 20, "bold"), pady=10)
        title.pack()

        fruits_frame1 = tk.Frame(self)
        fruits_frame1.pack(pady=8)
        row1_fruits = ["Orange", "Lemon", "Lime", "Strawberry", "Raspberry", "Pineapple", "Pomegranate"]
        for fruit in row1_fruits:
            col = self.fruits[fruit]["default_color"]
            btn = tk.Button(fruits_frame1, text=fruit, bg=col, fg="black", width=10, height=2,
                           command=lambda f=fruit: self.apply_fruit(f))
            btn.pack(side="left", padx=4)

        fruits_frame2 = tk.Frame(self)
        fruits_frame2.pack(pady=8)
        g1_btn = tk.Button(fruits_frame2, text="G1", bg="#808080", fg="white", width=10, height=2,
                           command=lambda: self.apply_fruit("G1"))
        g1_btn.pack(side="left", padx=4)
        g2_btn = tk.Button(fruits_frame2, text="G2", bg="#1C1C1C", fg="white", width=10, height=2,
                           command=lambda: self.apply_fruit("G2"))
        g2_btn.pack(side="left", padx=4)
        custom_btn = tk.Button(fruits_frame2, text="Custom", bg="#006400", fg="white", width=10, height=2,
                               command=self.open_custom_popup)
        custom_btn.pack(side="left", padx=4)

        generate_frame = tk.Frame(self)
        generate_frame.pack(pady=8)
        tk.Button(generate_frame, text="Generate G Sample", bg="#9E9E9E", fg="white", width=16, height=2,
                  command=self.generate_g_sample).pack(side="left", padx=4)
        tk.Button(generate_frame, text="Generate G Key", bg="#607D8B", fg="white", width=16, height=2,
                  command=self.generate_g_key).pack(side="left", padx=4)
        tk.Button(generate_frame, text="Generate F Sample", bg="#FF9800", fg="white", width=16, height=2,
                  command=self.generate_f_sample).pack(side="left", padx=4)
        tk.Button(generate_frame, text="Generate F Key", bg="#F44336", fg="white", width=16, height=2,
                  command=self.generate_f_key).pack(side="left", padx=4)
        tk.Button(generate_frame, text="Generate I Key", bg="#3F51B5", fg="white", width=16, height=2,
                  command=self.generate_i_key).pack(side="left", padx=4)

        color_frame = tk.Frame(self)
        color_frame.pack(pady=10)
        tk.Label(color_frame, text="Color Picker:").pack(side="left", padx=5)
        self.color_swatch = tk.Label(color_frame, width=5, height=2, relief="solid", bg="#FF9F1C")
        self.color_swatch.pack(side="left", padx=5)
        tk.Button(color_frame, text="Pick Color", command=self.pick_color).pack(side="left", padx=5)

        size_frame = tk.Frame(self)
        size_frame.pack(pady=8)
        w_frame = tk.Frame(size_frame)
        w_frame.pack(side="left", padx=20)
        tk.Label(w_frame, text="Canvas Width:").pack(side="left")
        tk.Label(w_frame, textvariable=self.width_var, width=6, relief="sunken", bg="#fff").pack(side="left", padx=5)
        tk.Button(w_frame, text="↑", width=3, command=lambda: self.adjust_size('w', 50)).pack(side="left", padx=1)
        tk.Button(w_frame, text="↓", width=3, command=lambda: self.adjust_size('w', -50)).pack(side="left", padx=1)

        h_frame = tk.Frame(size_frame)
        h_frame.pack(side="left", padx=20)
        tk.Label(h_frame, text="Canvas Height:").pack(side="left")
        tk.Label(h_frame, textvariable=self.height_var, width=6, relief="sunken", bg="#fff").pack(side="left", padx=5)
        tk.Button(h_frame, text="↑", width=3, command=lambda: self.adjust_size('h', 50)).pack(side="left", padx=1)
        tk.Button(h_frame, text="↓", width=3, command=lambda: self.adjust_size('h', -50)).pack(side="left", padx=1)

        tk.Button(size_frame, text="Apply Resize", command=self.resize_canvas, bg="#4CAF50", fg="white", padx=12).pack(side="left", padx=20)

        self.image_label = tk.Label(self)
        self.image_label.pack(pady=10)

        self.status_label = tk.Label(self, text="Ready – use 'Key' for full quantum fruit key generation",
                                     font=("Helvetica", 10), relief="sunken", anchor="w", bg="#EEE",
                                     wraplength=1080, justify="left")
        self.status_label.pack(fill="x", side="bottom", ipady=6)

    def toggle_opacity(self):
        self.opacity_on = not self.opacity_on
        self.opacity_btn.config(text="Opacity On" if self.opacity_on else "No Opacity")
        self.status_label.config(text=f"Opacity toggled {'ON (per-layer alpha applied)' if self.opacity_on else 'OFF'}")

    def toggle_secured(self):
        self.secured_on = not self.secured_on
        self.secured_btn.config(text="Secured Layers" if self.secured_on else "Insecure Layers")
        self.status_label.config(text=f"Secured Layers toggled {'ON (Gaussian blur per new layer)' if self.secured_on else 'OFF'}")

    def update_display(self):
        photo = ImageTk.PhotoImage(self.image)
        self.image_label.config(image=photo)
        self.image_label.image = photo

    def get_dynamic_scent_profile(self, fruit):
        epoch = int(time.time())
        epoch_str = str(epoch)
        epoch_mod = int(epoch_str[-6:]) if len(epoch_str) >= 6 else epoch
        mu_shift = (epoch_mod % 1000) / 2000.0 - 0.25
        sigma_shift = (epoch_mod % 777) / 3000.0
        base = self.base_scent_profiles.get(fruit, {"mu": 0.5, "sigma": 0.3})
        mu = max(0.1, min(0.9, base["mu"] + mu_shift))
        sigma = max(0.1, min(0.6, base["sigma"] + sigma_shift))
        return {"mu": mu, "sigma": sigma}

    def generate_bumps(self, fruit, w, h, custom_mode=False, custom_params=None, force_density=None):
        if custom_mode:
            params = custom_params or self.custom_params
            spacing = params["spacing"]
            pert = params["pert"]
            min_r = params["min_r"]
            max_r = params["max_r"]
            density = params.get("density", 1.0)
            use_gauss = params.get("use_gaussian_pert", False)
        else:
            params = self.fruits[fruit]
            spacing = params["spacing"]
            pert = params["pert"]
            min_r = params["min_r"]
            max_r = params["max_r"]
            density = force_density if force_density is not None else 1.0
            use_gauss = fruit in ["G1", "G2"]

        eff_spacing = spacing / max(density, 0.1)

        profile = self.get_dynamic_scent_profile(fruit)
        scent_bias_x = random.gauss(profile["mu"] * w, profile["sigma"] * w)
        scent_bias_y = random.gauss(profile["mu"] * h, profile["sigma"] * h)

        forbidden = set()
        if fruit in self.last_region:
            last = self.last_region[fruit]
            forbidden.add(last)
            forbidden.add((last + 1) % 8)
            forbidden.add((last - 1) % 8)
        allowed_regions = [i for i in range(8) if i not in forbidden]
        start_region = random.choice(allowed_regions)
        self.last_region[fruit] = start_region

        region_col = start_region % 4
        region_row = start_region // 4
        start_offset_x = int(region_col * (w / 4)) + random.randint(-int(w/8), int(w/8))
        start_offset_y = int(region_row * (h / 2)) + random.randint(-int(h/8), int(h/8))

        seed_val = hash(fruit) + int(scent_bias_x) + int(scent_bias_y) + start_region + len(self.layers) * 17
        random.seed(seed_val)

        bumps = []
        is_pineapple = fruit == "Pineapple"
        rows = int(h / eff_spacing) + 4

        if fruit == "G1":
            epoch = int(time.time())
            light_center_x = (w / 2) + (epoch % 200 - 100)
            light_center_y = (h / 2) + ((epoch // 10) % 200 - 100)
            for j in range(-2, rows):
                y_base = j * eff_spacing + random.uniform(-pert/2, pert/2)
                y = y_base + scent_bias_y * 0.1
                offset = (j % 2 * eff_spacing / 2) if is_pineapple else 0
                cols = int(w / eff_spacing) + 4
                for i in range(-2, cols):
                    x_base = i * eff_spacing + offset + random.uniform(-pert, pert)
                    dist = ((x_base - light_center_x)**2 + (y - light_center_y)**2)**0.5
                    light_factor = max(0.25, 1.0 - (dist / (w * 0.75))**2)
                    x = x_base + scent_bias_x * 0.18 * light_factor
                    if 0 < x < w and 0 < y < h:
                        r = random.uniform(min_r, max_r) * light_factor
                        bumps.append((x, y, r))
            return bumps

        if fruit == "G2" or use_gauss:
            epoch = int(time.time())
            start_shift_x = (epoch % 300 - 150) * 0.8
            start_shift_y = ((epoch // 7) % 300 - 150) * 0.8
            for j in range(-2, rows):
                y = j * eff_spacing + random.gauss(scent_bias_y * 0.25 + start_shift_y, pert * 1.6)
                offset = (j % 2 * eff_spacing / 2) if is_pineapple else 0
                cols = int(w / eff_spacing) + 4
                for i in range(-2, cols):
                    x = i * eff_spacing + offset + random.gauss(scent_bias_x * 0.25 + start_shift_x, pert * 1.6)
                    if 0 < x < w and 0 < y < h:
                        r = random.gauss((min_r + max_r)/2, (max_r - min_r)/2.5)
                        bumps.append((x, y, max(min_r, min(max_r, r))))
            return bumps

        for j in range(-2, rows):
            y = start_offset_y + j * eff_spacing + random.uniform(-pert/2, pert/2) + scent_bias_y * 0.15
            offset = (j % 2 * eff_spacing / 2) if is_pineapple else 0
            cols = int(w / eff_spacing) + 4
            for i in range(-2, cols):
                x = start_offset_x + i * eff_spacing + offset + random.uniform(-pert, pert) + scent_bias_x * 0.15
                if 0 < x < w and 0 < y < h:
                    r = random.uniform(min_r, max_r)
                    bumps.append((x, y, r))
        return bumps

    def apply_layer(self, bumps, color, fruit_name, is_custom=False):
        # Update epoch & source only when canvas actually changes
        if self.canvas_epoch is None or len(self.layers) == 0:
            self.canvas_epoch = int(time.time())
            self.canvas_source = fruit_name

        if self.opacity_on:
            layer_level = len(self.layers) + 1
            opacity_percent = min(100, layer_level * 20)
            alpha = int(opacity_percent * 2.55)
        else:
            alpha = 255

        temp = Image.new("RGBA", (self.canvas_width, self.canvas_height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp)

        for x, y, r in bumps:
            if r > 0:
                temp_draw.ellipse((x-r, y-r, x+r, y+r), fill=(*self.hex_to_rgb(color), alpha))

        if self.secured_on:
            temp = temp.filter(ImageFilter.GaussianBlur(radius=2.8))

        self.image = Image.alpha_composite(self.image, temp)
        self.draw = ImageDraw.Draw(self.image)

        self.layers.append({
            "fruit": fruit_name,
            "color": color,
            "bumps": [(round(x,2), round(y,2), round(r,2)) for x,y,r in bumps if r > 0],
            "opacity_percent": int(alpha / 2.55) if self.opacity_on else 100,
            "secured": self.secured_on
        })

        if bumps:
            self.last_bump = bumps[-1]

        self.update_display()

        desc = self.fruits.get(fruit_name, {}).get("math_desc", "Custom mapping applied")
        extra = f" | Opacity {self.layers[-1]['opacity_percent']}% | Secured: {self.secured_on}"
        self.status_label.config(text=f"Last applied: {fruit_name} → {desc}{extra}")

    def hex_to_rgb(self, hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def apply_fruit(self, fruit):
        if fruit not in self.fruits:
            return
        fruit_info = self.fruits[fruit]
        color = self.current_color or fruit_info["default_color"]
        self.last_fruit = fruit
        bumps = self.generate_bumps(fruit, self.canvas_width, self.canvas_height)
        self.apply_layer(bumps, color, fruit)

    def open_custom_popup(self):
        popup = Toplevel(self)
        popup.title("Custom Mapping Live Adjuster")
        popup.geometry("620x680")
        p = self.custom_params.copy()
        preview_size = 300
        preview_label = tk.Label(popup)
        preview_label.pack(pady=10)

        def update_preview():
            preview = Image.new("RGBA", (preview_size, preview_size), self.bg_color)
            p_draw = ImageDraw.Draw(preview)
            temp_bumps = self.generate_bumps("Custom", preview_size, preview_size, custom_mode=True, custom_params=p)
            for x, y, r in temp_bumps:
                if r > 0:
                    p_draw.ellipse((x-r, y-r, x+r, y+r), fill=(*self.hex_to_rgb(p["color"]), 220))
            photo = ImageTk.PhotoImage(preview)
            preview_label.config(image=photo)
            preview_label.image = photo

        def make_control(label_text, key, step=1, minv=1, maxv=100):
            frame = tk.Frame(popup)
            frame.pack(fill="x", padx=20, pady=4)
            tk.Label(frame, text=label_text, width=22, anchor="w").pack(side="left")
            var = tk.DoubleVar(value=p[key]) if isinstance(p[key], float) else tk.IntVar(value=p[key])
            val_label = tk.Label(frame, textvariable=var, width=8, relief="sunken")
            val_label.pack(side="left", padx=8)
            def change(delta):
                new_val = max(minv, min(maxv, var.get() + delta))
                var.set(new_val)
                p[key] = new_val
                update_preview()
            tk.Button(frame, text="↑", command=lambda: change(step)).pack(side="left", padx=2)
            tk.Button(frame, text="↓", command=lambda: change(-step)).pack(side="left", padx=2)
            return var

        make_control("Spacing", "spacing", step=2, minv=6, maxv=60)
        make_control("Perturbation", "pert", step=1, minv=1, maxv=30)
        make_control("Min Radius", "min_r", step=1, minv=1, maxv=20)
        make_control("Max Radius", "max_r", step=1, minv=2, maxv=30)
        make_control("Density Multiplier", "density", step=0.1, minv=0.1, maxv=2.5)

        def pick_custom_color():
            col = colorchooser.askcolor(title="Custom Dot Color")[1]
            if col:
                p["color"] = col
                update_preview()
        tk.Button(popup, text="Pick Custom Color", command=pick_custom_color, bg=p["color"], fg="white").pack(pady=8)

        gauss_var = tk.BooleanVar(value=p["use_gaussian_pert"])
        tk.Checkbutton(popup, text="Use Gaussian Perturbation (crypto-style)", variable=gauss_var,
                       command=lambda: p.update({"use_gaussian_pert": gauss_var.get()}) or update_preview()).pack()

        update_preview()

        btn_frame = tk.Frame(popup)
        btn_frame.pack(pady=20)
        def stick_and_use():
            self.custom_params = p.copy()
            self.apply_custom(p)
            popup.destroy()
        def use_only():
            self.apply_custom(p)
            popup.destroy()
        tk.Button(btn_frame, text="Stick + Use", command=stick_and_use, bg="#28a745", fg="white", width=22).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Use", command=use_only, bg="#17a2b8", fg="white", width=22).pack(side="left", padx=8)
        tk.Button(btn_frame, text="Cancel", command=popup.destroy, width=12).pack(side="left", padx=8)

    def apply_custom(self, params):
        color = self.current_color or params["color"]
        self.last_fruit = "Custom"
        # Update state for Custom button usage
        if self.canvas_epoch is None or len(self.layers) == 0:
            self.canvas_epoch = int(time.time())
            self.canvas_source = "Custom"
        bumps = self.generate_bumps("Custom", self.canvas_width, self.canvas_height, custom_mode=True, custom_params=params)
        self.apply_layer(bumps, color, "Custom", is_custom=True)

    def pick_color(self):
        color = colorchooser.askcolor(title="Choose color for next overlay")[1]
        if color:
            self.current_color = color
            self.color_swatch.config(bg=color)

    def save_canvas(self):
        if not self.layers:
            messagebox.showinfo("Save", "Nothing to save yet!")
            return
        # Use the captured epoch for this canvas state
        epoch = self.canvas_epoch or int(time.time())
        # Smart type for filename
        save_type = self.canvas_source or self.last_fruit or "stacked"
        if save_type == "KEY":
            save_type = "KEY"
        filename = f"{epoch}_{save_type}_bitmap.png"
        self.image.convert("RGB").save(filename)
        messagebox.showinfo("Saved", f"Saved as {filename}")

    def compute_key(self):
        all_bumps = []
        for layer in self.layers:
            for b in layer.get("bumps", []):
                all_bumps.append(b)
        bump_data = str(sorted(all_bumps)).encode('utf-8')
        base = hashlib.sha3_512(bump_data).hexdigest()

        key_set = {
            "SPHINCS+": base[:128],
            "Falcon (pqm4)": hashlib.sha3_512(bump_data + b'falcon_pqm4').hexdigest()[:128],
            "kyber-CRYSTALS Dilithium": hashlib.sha3_512(bump_data + b'dilithium').hexdigest()[:128],
            "PQC": hashlib.sha3_512(bump_data + b'generic_pqc').hexdigest()[:128],
            "Stateless Quantum Resistant Cryptography": hashlib.sha3_256(bump_data).hexdigest()
        }
        return key_set

    def find_void_cycle(self):
        voids = []
        bg_r, bg_g, bg_b = self.bg_color[:3]
        tried = 0
        while len(voids) < 8 and tried < 2000:
            tried += 1
            x = random.randint(20, self.canvas_width - 20)
            y = random.randint(20, self.canvas_height - 20)
            pixel = self.image.getpixel((x, y))
            if abs(pixel[0] - bg_r) < 30 and abs(pixel[1] - bg_g) < 30 and abs(pixel[2] - bg_b) < 30:
                if not any(abs(x - vx) < 40 and abs(y - vy) < 40 for vx, vy in voids):
                    voids.append((x, y))
        if len(voids) < 4:
            voids = [(self.canvas_width//4, self.canvas_height//4),
                     (self.canvas_width*3//4, self.canvas_height//4),
                     (self.canvas_width//4, self.canvas_height*3//4),
                     (self.canvas_width*3//4, self.canvas_height*3//4)]
        random.shuffle(voids)
        cycle = voids[:random.randint(4, 8)]
        desc = f"start ({cycle[0][0]},{cycle[0][1]}) -> "
        for i in range(1, len(cycle)):
            dx = cycle[i][0] - cycle[i-1][0]
            dy = cycle[i][1] - cycle[i-1][1]
            desc += f"({dx:+},{dy:+}) -> "
        dx = cycle[0][0] - cycle[-1][0]
        dy = cycle[0][1] - cycle[-1][1]
        desc += f"({dx:+},{dy:+}) -> start"
        return desc

    def show_please_wait(self, message="Please Wait...\nProcessing quantum fruit mapping"):
        popup = Toplevel(self)
        popup.title("")
        popup.geometry("500x140")
        popup.resizable(False, False)
        popup.grab_set()
        popup.transient(self)
        lbl = tk.Label(popup, text=message, font=("Helvetica", 12, "bold"), padx=30, pady=30)
        lbl.pack(expand=True)
        return popup

    def generate_quantum_key(self):
        wait_popup = self.show_please_wait("Generating ultra-dense quantum fruit key...\n\nThis may take a few seconds")

        def run_key_generation():
            self.clear_canvas()
            visible_w = self.canvas_width
            visible_h = self.canvas_height
            max_w = max(1600, visible_w * 2)
            max_h = max(1600, visible_h * 2)
            P = visible_w
            Q = visible_h
            fruit_list = list(self.fruits.keys())
            random.shuffle(fruit_list)
            cycle_idx = 0
            fill_target = random.uniform(0.92, 0.98)
            current_fill = 0.0
            section = 0
            while current_fill < fill_target or section < 45:
                fruit = fruit_list[cycle_idx % len(fruit_list)]
                cycle_idx += 1
                new_visible_w = max(200, int(visible_w * random.uniform(0.8, 1.2)))
                new_visible_h = max(200, int(visible_h * random.uniform(0.8, 1.2)))
                visible_w, visible_h = new_visible_w, new_visible_h
                sub_w = random.randint(int(max_w*0.7), int(max_w*0.98))
                sub_h = random.randint(int(max_h*0.7), int(max_h*0.98))
                bumps = self.generate_bumps(fruit, sub_w, sub_h, force_density=random.uniform(2.2, 3.5))
                scale_x = visible_w / max_w
                scale_y = visible_h / max_h
                scaled_bumps = [(x * scale_x, y * scale_y, r * ((scale_x + scale_y)/2)) for x, y, r in bumps]
                color = self.fruits[fruit]["default_color"]
                self.after(0, lambda b=scaled_bumps, c=color, f=fruit: self.apply_layer(b, c, f))
                current_fill += len(bumps) / (max_w * max_h / 80)
                section += 1
                if section % 5 == 0 and random.random() < 0.8:
                    g = "G1" if random.random() < 0.5 else "G2"
                    bumps_g = self.generate_bumps(g, sub_w, sub_h, force_density=random.uniform(2.5, 4.0))
                    scaled_g = [(x * scale_x, y * scale_y, r * ((scale_x + scale_y)/2)) for x, y, r in bumps_g]
                    self.after(0, lambda b=scaled_g, c=self.fruits[g]["default_color"], f=g: self.apply_layer(b, c, f))
            prime_sizes = [19, 23, 29, 31]
            ratio_idx = random.randint(0, len(prime_sizes)-1)
            final_w = prime_sizes[ratio_idx] * (P // 20)
            final_h = prime_sizes[ratio_idx] * (Q // 20)
            self.after(0, lambda: self.resize_canvas_to(final_w, final_h))
            # Set KEY source and epoch once at the end
            self.canvas_epoch = int(time.time())
            self.canvas_source = "KEY"
            key_set = self.compute_key()
            void_desc = self.find_void_cycle()
            keyring = {
                "SPHINCS+": key_set["SPHINCS+"],
                "Falcon_pqm4": key_set["Falcon (pqm4)"],
                "Dilithium": key_set["kyber-CRYSTALS Dilithium"],
                "PQC": key_set["PQC"],
                "Stateless_QR": key_set["Stateless Quantum Resistant Cryptography"]
            }
            proof_data = json.dumps(key_set, sort_keys=True).encode()
            proof_hash = hashlib.sha3_512(proof_data).digest()
            base58_proof = b58encode(proof_hash)[:88]
            epoch = self.canvas_epoch
            filename = f"{epoch}.QFKeychain"
            output = {
                "epoch": epoch,
                "P": final_w,
                "Q": final_h,
                "key_set": key_set,
                "keyring": keyring,
                "base58_signature_proof": base58_proof,
                "void_cycle_description": void_desc,
                "generation_notes": "Quantum Fruit Randomness – ultra-dense coverage + epoch-dynamic scent/G1/G2 + dual-canvas"
            }
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2)
            self.after(0, lambda: self.finish_key_generation(wait_popup, filename))

        threading.Thread(target=run_key_generation, daemon=True).start()

    def finish_key_generation(self, wait_popup, filename):
        wait_popup.destroy()
        self.status_label.config(text=f"Quantum Key generated → {filename}")
        messagebox.showinfo("Quantum Key Ready", f"Saved {filename}\n\nUltra-dense fruit map created with minimal voids for true quantum randomness.")

    def resize_canvas_to(self, new_w, new_h):
        scale_x = new_w / self.canvas_width
        scale_y = new_h / self.canvas_height
        new_image = Image.new("RGBA", (new_w, new_h), self.bg_color)
        new_draw = ImageDraw.Draw(new_image)
        for layer in self.layers:
            color = layer["color"]
            for x, y, r in layer["bumps"]:
                nx = x * scale_x
                ny = y * scale_y
                nr = r * ((scale_x + scale_y) / 2)
                if 0 < nx < new_w and 0 < ny < new_h:
                    new_draw.ellipse((nx-nr, ny-nr, nx+nr, ny+nr), fill=(*self.hex_to_rgb(color), 255))
        self.image = new_image
        self.draw = new_draw
        self.canvas_width = new_w
        self.canvas_height = new_h
        self.update_display()

    def generate_g_sample(self):
        self.clear_canvas()
        self.opacity_on = False
        self.secured_on = False
        self.opacity_btn.config(text="No Opacity")
        self.secured_btn.config(text="Insecure Layers")
        for i in range(8):
            self.apply_fruit("G1" if i % 2 == 0 else "G2")
        self.status_label.config(text="G Sample (Falcon pqm4 style) generated")

    def generate_f_sample(self):
        self.clear_canvas()
        self.opacity_on = False
        self.secured_on = False
        self.opacity_btn.config(text="No Opacity")
        self.secured_btn.config(text="Insecure Layers")
        fruits = ["Orange","Lemon","Pineapple","Strawberry","Pomegranate","Lime","Raspberry"]
        for i in range(10):
            self.apply_fruit(fruits[i % len(fruits)])
        self.status_label.config(text="F Sample (SPHINCS+ style) generated")

    def generate_f_key(self):
        self.clear_canvas()
        self.opacity_on = True
        self.secured_on = True
        self.opacity_btn.config(text="Opacity On")
        self.secured_btn.config(text="Secured Layers")
        fruits = ["Orange","Lemon","Pineapple","Strawberry","Pomegranate","Lime","Raspberry"]
        for i in range(10):
            self.apply_fruit(fruits[i % len(fruits)])
        self.status_label.config(text="F Key (SPHINCS+) generated")

    def generate_g_key(self):
        self.clear_canvas()
        self.opacity_on = True
        self.secured_on = True
        self.opacity_btn.config(text="Opacity On")
        self.secured_btn.config(text="Secured Layers")
        for i in range(8):
            self.apply_fruit("G1" if i % 2 == 0 else "G2")
        self.status_label.config(text="G Key (Falcon pqm4) generated")

    def generate_i_key(self):
        filename = filedialog.askopenfilename(title="Select mapping for I Key (Dilithium)", filetypes=[("All files", "*.*")])
        if not filename:
            return
        self.clear_canvas()
        try:
            if filename.endswith(".png"):
                loaded = Image.open(filename).convert("RGBA").resize((self.canvas_width, self.canvas_height), Image.Resampling.LANCZOS)
                self.image = loaded
                self.draw = ImageDraw.Draw(self.image)
                self.layers = []
                self.update_display()
                self.status_label.config(text="I Key base (Dilithium) imported")
            else:
                self.status_label.config(text="Only PNG supported for I[mport] Key importing")
        except Exception:
            messagebox.showerror("Import Error", "Could not load the selected file.")

    def export_active_key(self):
        key_set = self.compute_key()
        epoch = self.canvas_epoch or int(time.time())
        filename = f"{epoch}_active_key.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== Stateless Quantum Resistant Cryptography Key Set (Active) ===\n")
            f.write("{Stateless Quantum Resistant Cryptography, SPHINCS+, Falcon (pqm4), kyber-CRYSTALS Dilithium, PQC}\n\n")
            for k, v in key_set.items():
                f.write(f"{k}: {v}\n")
        messagebox.showinfo("Active Key", f"Saved {filename}")

    def export_secured_key(self):
        key_set = self.compute_key()
        epoch = self.canvas_epoch or int(time.time())
        filename = f"{epoch}_secured_key.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("=== Secured Quantum Resistant Key Set ===\n")
            f.write("{kyber-CRYSTALS Dilithium, SPHINCS+, Falcon (pqm4), Stateless Quantum Resistant Cryptography, PQC}\n\n")
            for k, v in key_set.items():
                f.write(f"{k}: {v}\n")
        messagebox.showinfo("Secured Key", f"Saved {filename}")

    def export_crumbs(self):
        data = {
            "canvas_size": [self.canvas_width, self.canvas_height],
            "size_ratio": round(self.canvas_width / self.canvas_height, 2),
            "layers": self.layers,
            "opacity_toggle_was_used": self.opacity_on,
            "secured_toggle_was_used": self.secured_on
        }
        used = {layer["fruit"] for layer in self.layers}
        header = "=== MATHS FOR USED FRUITS/MAPPINGS ===\n"
        for f in sorted(used):
            if f in self.fruits:
                header += f"{f}: {self.fruits[f]['math_desc']}\n"
        header += "\n=== LAYERS DATA ===\n"
        unused = set(self.fruits.keys()) - used
        footer = "\n=== MATHS FOR UNUSED FRUITS/MAPPINGS ===\n"
        for f in sorted(unused):
            footer += f"{f}: {self.fruits[f]['math_desc']}\n"
        footer += f"\nCanvas size: {self.canvas_width}x{self.canvas_height}, ratio: {data['size_ratio']}"
        key_set = self.compute_key()
        footer += "\n\n=== STATELESS QUANTUM RESISTANT SIGNATURE HASH KEY SET ===\n"
        footer += "{Stateless Quantum Resistant Cryptography, SPHINCS+, Falcon (pqm4), kyber-CRYSTALS Dilithium, PQC}\n"
        for k, v in key_set.items():
            footer += f"{k}: {v}\n"
        with open("FruitMapper.crumbs", "w", encoding="utf-8") as f:
            f.write(header)
            f.write(json.dumps(data, indent=2))
            f.write(footer)
        messagebox.showinfo("Export", "Exported to FruitMapper.crumbs (includes full quantum key set)")

    def adjust_size(self, dim, delta):
        if dim == 'w':
            new_val = max(200, self.width_var.get() + delta)
            self.width_var.set(new_val)
        else:
            new_val = max(200, self.height_var.get() + delta)
            self.height_var.set(new_val)

    def resize_canvas(self):
        new_w = self.width_var.get()
        new_h = self.height_var.get()
        if new_w == self.canvas_width and new_h == self.canvas_height:
            return
        # Canvas changed → new epoch
        self.canvas_epoch = int(time.time())
        self.canvas_source = self.canvas_source or "RESIZE"
        scale_x = new_w / self.canvas_width
        scale_y = new_h / self.canvas_height
        new_image = Image.new("RGBA", (new_w, new_h), self.bg_color)
        new_draw = ImageDraw.Draw(new_image)
        for layer in self.layers:
            color = layer["color"]
            scaled_bumps = []
            for x, y, r in layer["bumps"]:
                nx = x * scale_x
                ny = y * scale_y
                nr = r * ((scale_x + scale_y) / 2)
                if 0 < nx < new_w and 0 < ny < new_h:
                    new_draw.ellipse((nx-nr, ny-nr, nx+nr, ny+nr), fill=(*self.hex_to_rgb(color), 255))
                scaled_bumps.append((round(nx, 2), round(ny, 2), round(nr, 2)))
            layer["bumps"] = scaled_bumps
        self.image = new_image
        self.draw = new_draw
        self.canvas_width = new_w
        self.canvas_height = new_h
        if self.layers and self.layers[-1]["bumps"]:
            self.last_bump = self.layers[-1]["bumps"][-1]
        self.update_display()
        self.status_label.config(text=f"Canvas resized to {new_w}×{new_h} – layers scaled")

    def clear_canvas(self):
        self.image = Image.new("RGBA", (self.canvas_width, self.canvas_height), self.bg_color)
        self.draw = ImageDraw.Draw(self.image)
        self.layers = []
        self.last_bump = None
        self.last_region = {}
        self.canvas_epoch = None
        self.canvas_source = None
        self.status_label.config(text="Canvas cleared – ready for new fruit/mapping")
        self.update_display()

    def reset_canvas(self):
        self.clear_canvas()
        self.current_color = None
        self.color_swatch.config(bg="#FF9F1C")
        self.last_fruit = None
        self.last_bump = None
        self.width_var.set(600)
        self.height_var.set(600)
        self.opacity_on = False
        self.secured_on = False
        self.opacity_btn.config(text="No Opacity")
        self.secured_btn.config(text="Insecure Layers")

    def quit_app(self):
        if messagebox.askokcancel("Exit", "Quit Fruit Bitmapper?"):
            self.destroy()

if __name__ == "__main__":
    app = FruitBitmapper()
    app.mainloop()
