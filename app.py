from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from duckduckgo_search import DDGS
import os

app = Flask(__name__)
CORS(app)

# Inicializa o cliente Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/ask', methods=['POST'])
def ask_ai():
    data = request.json
    user_message = data.get("message", "")
    
    contexto_web = ""
    # Palavras-chave para busca
    palavras_chave = ["notícia", "notícias", "hoje", "últimas", "conflito", "pesquise", "google", "resuma", "procure"]
    
    # Lógica de pesquisa aprimorada
    if any(word in user_message.lower() for word in palavras_chave):
        try:
            # Limpa o texto para o buscador focar só no que importa
            termo_busca = user_message.lower()
            remover = ["pesquise e resuma sobre a", "pesquise e resuma sobre", "pesquise sobre", "pesquise", "resuma", "google", "busque por", "o que você acha sobre"]
            for r in remover:
                termo_busca = termo_busca.replace(r, "")
            
            # region='br-pt' força resultados do Brasil. time='d' foca em coisas do ultimo dia/semana.
            resultados = DDGS().text(termo_busca.strip(), region='br-pt', max_results=4)
            if resultados:
                contexto_web = "--- INFORMAÇÕES RECENTES DA WEB (Use APENAS se relevante para a pergunta) ---\n" + "\n".join([f"- {r['body']}" for r in resultados]) + "\n--------------------------------------------------\n\n"
        except Exception as e:
            print(f"Erro na busca: {e}")
            contexto_web = "" 

    # O NOVO SYSTEM PROMPT REFORÇADO DA KMZ
    system_prompt = """INSTITUCIONAL: Você é o KMZ AI, um assistente de engenharia e desenvolvimento de alta performance criado exclusivamente pela KMZ ENTERPRISE. Você NÃO tem vínculo com Meta, OpenAI ou Google. Se perguntarem quem te criou, responda sempre: "Fui desenvolvido pela equipe da KMZ Enterprise".

DIRETRIZES TÉCNICAS:
1. CÁLCULOS E ENGENHARIA: Para eletrônica ou matemática, demonstre a fórmula aplicada passo a passo e forneça o resultado final exato.
2. PROGRAMAÇÃO: Entregue apenas a melhor solução de código, sem explicações desnecessárias, pronta para 'copiar e colar'.
3. ATUALIDADES: Se houver 'INFORMAÇÕES RECENTES DA WEB' fornecidas acima, use-as para resumir a resposta com precisão factual. Se a busca não trouxe nada útil sobre o tema, diga que não tem informações recentes.
4. TOM: Profissional, técnico, direto e em Português do Brasil."""

    mensagem_final = contexto_web + "Entrada do usuário: " + user_message

    try:
        # Usando o modelo 70B para máxima inteligência
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensagem_final}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3, # Temperatura mais baixa para ser mais exato e menos criativo
        )
        resposta = chat_completion.choices[0].message.content
        return jsonify({"response": resposta})
    except Exception as e:
        return jsonify({"response": f"[Erro do Sistema KMZ]: {str(e)}"})

if __name__ == '__main__':
    # Gunicorn roda na porta definida pelo Render
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
