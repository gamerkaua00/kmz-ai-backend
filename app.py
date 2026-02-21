from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from duckduckgo_search import DDGS
import os

app = Flask(__name__)
CORS(app) # Permite que seu app KMZ acesse este servidor

# Inicializa a API da Groq com a chave secreta
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/ask', methods=['POST'])
def ask_ai():
    data = request.json
    user_message = data.get("message", "")
    
    contexto_web = ""
    # Palavras-chave que ativam a busca no Google/Web
    palavras_chave = ["notícia", "notícias", "hoje", "últimas", "conflito", "pesquise", "google", "resuma"]
    
    if any(word in user_message.lower() for word in palavras_chave):
        try:
            resultados = DDGS().text(user_message, max_results=3)
            contexto_web = "Informações recentes da web:\n" + "\n".join([r['body'] for r in resultados]) + "\n\n"
        except Exception:
            contexto_web = "" # Se a busca falhar, a IA responde com o que já sabe

    # A alma do seu assistente
    system_prompt = """Você é um assistente de engenharia, matemática e programação da KMZ. 
    1. Para cálculos de eletrônica (resistores, capacitores, etc) e matemática, demonstre a fórmula passo a passo e dê o resultado exato.
    2. Para códigos, forneça apenas a melhor solução, pronta para copiar e colar.
    3. Para assuntos gerais ou notícias, resuma as informações de forma clara.
    4. Responda sempre em Português do Brasil de forma direta. Sem enrolação."""

    mensagem_final = contexto_web + "Pergunta do usuário: " + user_message

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensagem_final}
            ],
            model="llama-3.3-70b-versatile",
        )
        resposta = chat_completion.choices[0].message.content
        return jsonify({"response": resposta})
    except Exception as e:
        return jsonify({"response": f"Erro interno: {str(e)}"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
