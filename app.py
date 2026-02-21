from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from duckduckgo_search import DDGS
import os

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

historico_cache = {}

@app.route('/ask', methods=['POST'])
def ask_ai():
    data = request.json
    user_message = data.get("message", "").strip()
    user_message_lower = user_message.lower()
    
    if user_message_lower in historico_cache:
        return jsonify({"response": "⚡ *[Resposta via Cache KMZ]* ⚡\n\n" + historico_cache[user_message_lower]})

    contexto_web = ""
    palavras_chave = ["notícia", "notícias", "hoje", "últimas", "conflito", "pesquise", "google", "resuma", "procure"]
    
    if any(word in user_message_lower for word in palavras_chave):
        try:
            termo_busca = user_message_lower
            remover = ["pesquise e resuma sobre a", "pesquise", "resuma", "google", "busque por"]
            for r in remover:
                termo_busca = termo_busca.replace(r, "")
            
            resultados = DDGS().text(termo_busca.strip(), region='br-pt', max_results=3)
            if resultados:
                textos_limpos = [f"- {r['body'][:200].replace('\n', ' ')}..." for r in resultados]
                contexto_web = "--- INFORMAÇÕES RECENTES DA WEB ---\n" + "\n".join(textos_limpos) + "\n-----------------------------------\n\n"
        except Exception:
            contexto_web = "" 

    # O PROMPT BLINDADO
    system_prompt = """INSTITUCIONAL: Você é o KMZ AI, assistente de engenharia criado pela KMZ ENTERPRISE.
DIRETRIZES TÉCNICAS E REGRAS RÍGIDAS:
1. CÁLCULOS: Explique o passo a passo estrito e dê o resultado exato.
2. PROGRAMAÇÃO WEB: Se criar um site, separe claramente os blocos de código em HTML, CSS e JavaScript.
3. REGRA DO PDF: Se o usuário pedir para 'gerar um PDF', NUNCA escreva scripts em Python ou qualquer linguagem. Responda APENAS: "Para salvar este conteúdo, clique no botão **📥 Baixar PDF Oficial** no canto inferior da mensagem." e forneça o conteúdo normalmente em texto.
4. IMAGENS: Responda APENAS com este formato Markdown: ![Descricao](https://image.pollinations.ai/prompt/descricao-em-ingles)
5. TOM: Corporativo, técnico e em Português do Brasil."""

    mensagem_final = contexto_web + "Entrada do usuário: " + user_message

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": mensagem_final}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.2, 
        )
        resposta = chat_completion.choices[0].message.content
        historico_cache[user_message_lower] = resposta 
        return jsonify({"response": resposta})
    except Exception as e:
        return jsonify({"response": f"[Erro do Sistema KMZ]: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
