from flask import Flask, request, jsonify
import os
import re
import json
from dotenv import load_dotenv
from google import genai

# Load environment variables
# Di Vercel, ini membaca dari Project Settings
load_dotenv() 
api_key = os.getenv("GEMINI_API_KEY")

# Pengecekan ini sangat penting untuk debug di Vercel
if not api_key:
    # Error ini akan muncul di log Vercel jika variabelnya tidak ada
    raise ValueError("GEMINI_API_KEY environment variable not found.")

class RecipeAssistant:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_prompt(self, ingredients):
        if not ingredients:
            return "Please provide a valid list of ingredients..."
        return f"""
Saya ingin kamu menjadi asisten dapur.
Berikut daftar bahan yang saya miliki: {ingredients}
Tugasmu adalah:
- Periksa apakah bahan yang saya berikan termasuk bahan makanan yang bisa dimasak.
- Jika semua bahan **bukan bahan makanan**, jangan tampilkan apa pun.
- Jika ada minimal satu bahan makanan valid, berikan minimal 12 resep berbeda yang **menggunakan bahan-bahan yang saya miliki**.
⚠️ Jawaban HARUS hanya berupa JSON valid TANPA PENJELASAN TAMBAHAN, dalam format:
[
  {{
    "nama": "Nama masakan",
    "bahan": ["bahan 1", "bahan 2"],
    "langkah": ["Langkah 1", "Langkah 2"]
  }},
  ... (minimal 12 resep berbeda)
]
""".strip()

    def search_recipes(self, ingredients):
        prompt_text = self.generate_prompt(ingredients)
        print(f"📥 Bahan diterima: {ingredients}")
        try:
            response = self.model.generate_content(
                prompt_text,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            result_text = response.text
            print("📤 Output mentah dari Gemini:\n", result_text)
            parsed_json = json.loads(result_text)
            return parsed_json
        except Exception as e:
            # Ini akan mencetak error spesifik ke log Vercel Anda
            print(f"❌ Terjadi error saat memanggil Gemini atau mem-parsing JSON: {e}")
            raise

# Inisialisasi Flask App
app = Flask(__name__)

# Inisialisasi asisten
assistant = RecipeAssistant(api_key)

# PENTING: Rute sekarang diawali dengan /api/ agar cocok dengan vercel.json
@app.route('/api/search', methods=['POST'])
def handle_search():
    ingredients = request.json.get('ingredients')
    if not ingredients:
        return jsonify({'error': 'No ingredients provided'}), 400
    
    try:
        recipes = assistant.search_recipes(ingredients)
        return jsonify(recipes)
    except Exception as e:
        # Mengembalikan error umum ke pengguna, detailnya ada di log
        return jsonify({'error': 'Failed to generate recipes.', 'details': str(e)}), 500

# Rute lain juga harus diawali dengan /api/
@app.route('/api/save_favorite', methods=['POST'])
def handle_save_favorite():
    recipe_name = request.json.get('recipe_name')
    print(f"🔖 Menyimpan resep favorit: {recipe_name}")
    return jsonify({'message': f"Resep '{recipe_name}' telah disimpan!"})

