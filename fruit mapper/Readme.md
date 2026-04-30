# 🍊 Fruit Bitmapper

**Procedural fruit texture generator + quantum-resistant cryptographic key creator**

A beautiful, interactive Python Tkinter application that lets you stack realistic bumpy fruit skins (orange peel oil glands, pineapple scales, strawberry achenes, etc.) and generate ultra-dense, mathematically-rich patterns for art, procedural textures, and true quantum-inspired randomness.

The program also includes a powerful **"Key"** button that produces cryptographically strong, stateless quantum-resistant keys derived from the voids and bump placements in the generated maps.

![Fruit Bitmapper Screenshot](https://raw.githubusercontent.com/DigiMancer3D/quantum_fruit/refs/heads/main/Screenshot_20260430_000950.png)  
*(Add your favorite screenshot here)*

## ✨ Features

- Realistic fruit bump textures: Orange, Lemon, Pineapple, Strawberry, Pomegranate, Lime, Raspberry
- Special G1 (Gaussian blur / light-diffusion) and G2 (pure Gaussian crypto sampling)
- Live **Custom** editor with real-time preview, sliders, color picker, and "Stick / Use" options
- **"Key"** button → ultra-dense fruit map + full quantum-resistant key set
- Consistent epoch-based filenames across PNG, `.crumbs`, and `.QFKeychain`
- Smart filename types (`KEY`, `Custom`, fruit name)
- Dual-canvas system (hidden large canvas for dense mapping + dynamic visible canvas)

## 🧠 Maths & Concepts Behind the Project

### 1. Fruit Bump Mapping
Each fruit uses a mathematically defined distribution of dots:
- **Citrus (Orange/Lemon/Lime)**: Jittered rectangular grid  
  `x = i·spacing + U(-pert, pert)`  
  `y = j·spacing + U(-pert, pert)`
- **Pineapple**: Hexagonal staggered lattice
- **Strawberry/Raspberry**: Very dense jittered grid with tiny radii
- **Pomegranate**: Medium spacing + high perturbation for leathery look

### 2. G1 & G2 Special Mappings
- **G1**: Bi-sectional diffusion + CGI light-transfer model  
  Uses inverse-square radial falloff from a dynamically drifting center (epoch-driven) to simulate soft light diffusion.
- **G2**: Pure Gaussian (normal distribution) sampling  
  True cryptographic-style quantum-resistant randomness with per-layer starting point shifts.

### 3. Epoch-Dynamic Scent Profiles
Real chemical volatile compounds (limonene for citrus, esters for pineapple, etc.) are turned into Gaussian parameters (`μ`, `σ`). These parameters are further randomized using the current epoch so every run produces a **completely unique** starting bias.

### 4. 8th Sub-Division Avoidance
The canvas is divided into 8 regions. Each new layer of the same fruit/G-type is forced into a **different, non-adjacent** region , guaranteeing visual variety and true randomness.

### 5. Dual-Canvas "Key" Generation
- Hidden large "max" canvas for dense mapping
- Dynamic visible canvas that randomly grows/shrinks
- Final output is ultra-dense with near-zero white space
- Voids are analyzed to produce a real cycle description and cryptographic keys

### 6. Quantum-Resistant Key Derivation
Bump positions → SHA3-512 entropy → derived keys:
- SPHINCS+
- Falcon (mupq's pqm4)
- kyber-CRYSTALS Dilithium
- Generic PQC
- Stateless Quantum Resistant Cryptography

Plus a base58 signature proof.

## 🚀 Installation & Running

### Linux (Recommended)

```bash
# 1. Download the file
wget https://github.com/DigiMancer3D/quantum_fruit/blob/main/fruit%20mapper/fruitmapper.py

# 2. Make it executable
chmod +x fruitmapper.py

# 3. Run it
./fruitmapper.py
```

Or simply:

```bash
python3 fruitmapper.py
```

Pillow will be automatically installed on first run if missing.

### Windows

1. Download `fruitmapper.py`
2. Make sure Python 3.8+ is installed (from python.org)
3. Double-click the file **or** run in Command Prompt / PowerShell:

```cmd
python fruitmapper.py
```

Pillow will auto-install on first launch.

### macOS

```bash
python3 fruitmapper.py
```

(Pillow auto-installs if needed.)

## 📖 How to Use

- Click fruit buttons to overlay realistic textures
- Use **G1** / **G2** for Gaussian/crypto mappings
- Click **Custom** for live parameter tweaking
- Use the big **Key** button for a full ultra-dense quantum randomness map + cryptographic key file
- **Save** → creates `{epoch}_{type}_bitmap.png`
- **Export** → creates `FruitMapper.crumbs` (full data + maths + keys)
- **Export Key (active)** / **Export Secured Key** → quick text files with PQC keys

## 📁 Output Files

- `{epoch}_KEY_bitmap.png` , the beautiful dense image
- `FruitMapper.crumbs` , human-readable JSON with layers, maths, and full key set
- `{epoch}.QFKeychain` , complete quantum key set + base58 proof

## 🔬 Technical Concepts Summary

- **Gaussian sampling** for G2 and scent bias
- **Light-diffusion model** for G1
- **Epoch-based randomization** for reproducibility + uniqueness
- **Sub-division avoidance** for maximum visual variety
- **Void-cycle analysis** for cryptographic entropy

## ❤️ Credits

Coded by Grok 4.2 (xAI).  

---

**Star the repo if you enjoy creating beautiful fruit textures and quantum keys!** 🍓🍍🍊

```


