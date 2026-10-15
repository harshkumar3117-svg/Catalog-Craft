# 🛍️ CatalogCraft AI

> **Local, Zero-Token-Cost Autonomous E-Commerce Listing Engine for Independent Sellers**

CatalogCraft AI uses a two-step local AI pipeline to automatically generate high-converting e-commerce product listings from product images — completely on-device, with zero API costs.

---

## ✨ Features

- 📸 **Image-to-Listing** — Upload a product photo and get a full listing generated automatically
- 🔭 **Moondream Vision** — Extracts product details from images locally via Ollama
- 🧠 **Llama 3.2 Copywriting** — Generates structured, platform-specific listings from vision output
- 🛒 **Multi-Platform Support** — Amazon, Etsy, Shopify, Meesho
- 🌐 **Multi-Language** — English & Hindi output
- 💰 **Smart Pricing** — AI-suggested price range with currency & rationale, based on actual product
- 📦 **Bulk Batch Mode** — Upload multiple images and process them all at once
- 📥 **CSV Export** — Download listings ready for marketplace upload
- 🔒 **Zero Token Cost** — No OpenAI / Gemini API keys needed

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.com/) installed and running
- `moondream` and `llama3.2` models pulled in Ollama

### 1. Pull the Models

```bash
ollama pull moondream
ollama pull llama3.2
```

### 2. Clone the Repository

```bash
git clone https://github.com/harshkumar3117-svg/Catalog-Craft.git
cd Catalog-Craft
```

### 3. Create Virtual Environment & Install Dependencies

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 4. Run the App

```bash
streamlit run app.py
```

App will open at `http://localhost:8501`

---

## 🧠 How It Works

```
Product Image
      ↓
  [Resize & Compress]          ← optimized for speed
      ↓
  Moondream (Vision Model)     ← describes product: type, color, material, features
      ↓
  Llama 3.2 (Text Model)       ← generates structured JSON listing
      ↓
  Platform-specific Listing    ← Amazon / Etsy / Shopify / Meesho
```

Two models, each doing what they do best:
- **Moondream** → understands the image
- **Llama 3.2** → writes the copy

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| UI | Streamlit |
| Vision Model | Moondream (Ollama) |
| Listing Model | Llama 3.2 (Ollama) |
| Image Processing | Pillow (PIL) |
| Data Export | Pandas |
| Validation | Pydantic |

---

## 📁 Project Structure

```
Catalog-Craft/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
├── .gitignore
└── README.md
```

---

## 🔒 Privacy

All processing happens **100% on your device**. No images or product data are ever sent to any external server or API.
