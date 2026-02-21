from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from duckduckgo_search import DDGS
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Sistema de Cache
historico_cache = {}

@app.route('/ask', methods=['POST'])
def ask_ai():
    data = request.json
    user_message = data.get("message", "").strip()
    user_message_lower = user_message.lower()
    
    if user_message_lower in historico_cache:
        return jsonify({"response": "⚡ *[Resposta Rápida via Cache KMZ]* ⚡\n\n" + historico_cache[user_message_lower]})

    contexto_web = ""
    palavras_chave_web = ["notícia", "notícias", "hoje", "últimas", "conflito", "pesquise", "google", "resuma", "procure", "feriado", "atual", "youtube", "vídeo", "2026"]
    
    if any(word in user_message_lower for word in palavras_chave_web):
        try:
            termo_busca = user_message_lower
            remover = ["pesquise e resuma sobre a", "pesquise e coloque em pdf", "coloque em pdf", "pesquise", "resuma", "google", "busque por"]
            for r in remover:
                termo_busca = termo_busca.replace(r, "")
            
            # ADICIONADO TIMEOUT DE 10 SEGUNDOS (O Escudo Anti-Travamento)
            ddgs = DDGS(timeout=10)
            textos_limpos = []
            
            resultados = ddgs.text(termo_busca.strip(), region='br-pt', max_results=3)
            if resultados:
                textos_limpos.extend([f"- [WEB]: {r['body'][:200].replace(chr(10), ' ')}..." for r in resultados])
                
            if "youtube" in user_message_lower or "vídeo" in user_message_lower:
                videos = ddgs.videos(termo_busca.strip(), region='br-pt', max_results=2)
                if videos:
                    textos_limpos.extend([f"- [YOUTUBE]: {v['title']} (Link: {v['content']})" for v in videos])

            if textos_limpos:
                contexto_web = "--- DADOS DA WEB E YOUTUBE PARA EMBASAR A RESPOSTA ---\n" + "\n".join(textos_limpos) + "\n----------------------------------------------------\n\n"
        except Exception as e:
            print("Erro na busca (Timeout ou Bloqueio):", e)
            contexto_web = "" 

    data_atual = datetime.now().strftime("%d/%m/%Y")

    system_prompt = f"""INSTITUCIONAL: Você é o KMZ AI, inteligência artificial de engenharia corporativa.
CRIADOR: Você foi desenvolvido exclusivamente por Kauã Mazur dos Reis, CEO e fundador da KMZ Enterprise.
CONTEXTO: Hoje é {data_atual}. O ano é 2026. O usuário está em Campo Largo, PR.

DIRETRIZES PARA ECONOMIA DE TOKENS E INTELIGÊNCIA:
1. SEJA DIRETO E ORGANIZADO: Use tópicos. Responda de forma concisa.
2. CÁLCULOS: Explique o passo a passo de forma exata.
3. PROGRAMAÇÃO: Separe claramente os códigos HTML, CSS e JS.
4. GATILHO DE PDF: Se o usuário pedir para "gerar um PDF", "salvar em PDF" ou "colocar em PDF", adicione EXATAMENTE a tag [AUTO_PDF] no final da sua resposta. A tag fará o sistema baixar o arquivo. NUNCA programe scripts Python para isso.
5. PESQUISA: Baseie-se nas 'DADOS DA WEB E YOUTUBE' fornecidas. Se a pesquisa falhou ou não encontrou a data, diga a verdade diretamente.
6. IMAGENS: Responda APENAS com formato Markdown: ![Descricao](https://image.pollinations.ai/prompt/descricao-em-ingles)"""

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
