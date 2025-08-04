from flask import Flask, request, jsonify, send_from_directory
import os
import re
import json
from dotenv import load_dotenv
from google import genai

# Inisialisasi Flask App
# static_folder='../static' akan mencari folder static di luar folder api
app = Flask(__name__, static_folder='..', static_url_path='')

# Load environment variables
load_dotenv() 
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY environment variable not found.")

class RecipeAssistant:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def generate_prompt(self, ingredients):
        # ... (Fungsi generate_prompt Anda tidak perlu diubah) ...
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
            print(f"❌ Terjadi error: {e}")
            raise

# Inisialisasi asisten
assistant = RecipeAssistant(api_key)

# Rute untuk menyajikan file index.html dari root directory
@app.route('/')
def home():
    # Mengirim file index.html yang sekarang ada di folder yang sama
    return send_from_directory('.', 'index.html')

# Rute untuk API search
@app.route('/api/search', methods=['POST'])
def handle_search():
    ingredients = request.json.get('ingredients')
    if not ingredients:
        return jsonify({'error': 'No ingredients provided'}), 400
    try:
        recipes = assistant.search_recipes(ingredients)
        return jsonify(recipes)
    except Exception as e:
        return jsonify({'error': 'Failed to generate recipes.', 'details': str(e)}), 500

# Rute untuk API save_favorite
@app.route('/api/save_favorite', methods=['POST'])
def handle_save_favorite():
    recipe_name = request.json.get('recipe_name')
    print(f"🔖 Menyimpan resep favorit: {recipe_name}")
    return jsonify({'message': f"Resep '{recipe_name}' telah disimpan!"})