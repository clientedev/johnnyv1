import os
import base64
import requests
import json
from datetime import datetime

PPLX_API_KEY = os.getenv('PPLX_API_KEY') or os.getenv('PERPLEXITY_API_KEY')
PPLX_MODEL = 'sonar-pro'

def get_scanner_prompt(prompt_rules=None):
    base_prompt = """Você é um especialista em reciclagem de placas eletrônicas (PCBs) e recuperação de metais preciosos.
Com base na descrição fornecida pelo usuário sobre a placa eletrônica, classifique-a para fins de reciclagem.

CRITÉRIOS DE CLASSIFICAÇÃO:
- LOW (Baixo valor): Placas simples, poucas camadas, poucos componentes, baixa densidade de conectores dourados (ex: fontes, impressoras, TVs antigas)
- MEDIUM (Médio valor): Placas com densidade moderada de componentes, alguns conectores dourados, chips médios (ex: HDs, roteadores, placas de som)
- HIGH (Alto valor): Placas com alta densidade de componentes, muitos conectores dourados, chips BGA, processadores, memórias (ex: motherboards, celulares, servidores)

TIPOS COMUNS DE PLACAS E SEUS VALORES:
- Motherboard de PC/Servidor (geralmente HIGH) - ricos em ouro nos conectores e slots
- Placa de celular/smartphone (geralmente HIGH) - alta densidade de componentes valiosos
- Placa de fonte de alimentação (geralmente LOW) - poucos metais preciosos
- Placa de telecom/roteador (geralmente MEDIUM a HIGH) - conectores banhados a ouro
- Placa de HD/SSD (geralmente MEDIUM) - alguns componentes valiosos
- Placa de impressora (geralmente LOW) - baixo teor de metais preciosos
- Placa de TV/monitor (geralmente LOW a MEDIUM) - varia conforme a idade

INDICADORES DE VALOR PARA METAIS PRECIOSOS:
- Fingers/conectores dourados: quanto mais, maior o valor
- Chips BGA (Ball Grid Array): alto teor de ouro
- Conectores PCI/PCIe: contêm ouro
- Processadores e CPUs: ouro nos pinos e internamente
- Memórias RAM: fingers dourados

Use seu conhecimento sobre placas eletrônicas e datasets públicos de PCBs para fazer uma estimativa precisa.

RESPONDA EXCLUSIVAMENTE EM JSON com este formato exato (sem markdown, sem código, apenas o JSON puro):
{
  "grade": "LOW | MEDIUM | HIGH",
  "type_guess": "ex: placa de celular, motherboard de PC, fonte, telecom etc.",
  "explanation": "texto curto explicando a classificação (densidade de componentes, conectores dourados, etc.)",
  "confidence": 0.0,
  "metal_value_comment": "comentário curto sobre potencial de metais preciosos",
  "notes": "observações adicionais opcionais"
}"""
    
    if prompt_rules:
        base_prompt += f"\n\nREGRAS ADICIONAIS:\n{prompt_rules}"
    
    return base_prompt

def analyze_pcb_image(image_data, weight_kg=None, prompt_rules=None, description=None):
    if not PPLX_API_KEY:
        return None, 'Chave API do Perplexity não configurada. Configure PPLX_API_KEY ou PERPLEXITY_API_KEY.'
    
    if not description or not description.strip():
        return None, 'IMPORTANTE: A API Perplexity não suporta análise de imagens. Por favor, forneça uma descrição textual da placa (tipo, componentes visíveis, conectores, etc.) no campo "description" para que a análise possa ser realizada.'
    
    try:
        headers = {
            'Authorization': f'Bearer {PPLX_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        system_prompt = get_scanner_prompt(prompt_rules)
        
        user_message = f"""Analise a seguinte placa eletrônica para reciclagem de metais preciosos.

DESCRIÇÃO DA PLACA FORNECIDA PELO USUÁRIO:
{description.strip()}

Com base nesta descrição e seu conhecimento sobre PCBs para reciclagem, forneça uma classificação considerando:
- Densidade de componentes mencionada ou típica para este tipo de placa
- Presença de conectores dourados (fingers) mencionada ou típica
- Tipo de placa identificado
- Potencial de metais preciosos (ouro, prata, paládio)

"""
        
        if weight_kg:
            user_message += f"Peso estimado da placa: {weight_kg} kg\n"
        
        user_message += "\nResponda SOMENTE com o JSON no formato especificado, sem markdown ou texto adicional."
        
        payload = {
            'model': PPLX_MODEL,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_message}
            ],
            'max_tokens': 1024,
            'temperature': 0.3,
            'top_p': 0.9,
            'stream': False
        }
        
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            try:
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                
                content = content.strip()
                if content.startswith('{'):
                    end_idx = content.rfind('}') + 1
                    content = content[:end_idx]
                
                result = json.loads(content)
                
                if 'grade' not in result:
                    result['grade'] = 'MEDIUM'
                if 'type_guess' not in result:
                    result['type_guess'] = 'Placa eletrônica não identificada'
                if 'explanation' not in result:
                    result['explanation'] = 'Análise baseada em características típicas'
                if 'confidence' not in result:
                    result['confidence'] = 0.5
                if 'metal_value_comment' not in result:
                    result['metal_value_comment'] = 'Avaliação baseada em padrões típicos de placas'
                if 'notes' not in result:
                    result['notes'] = ''
                
                result['components_detected'] = result.get('components_detected', [])
                result['precious_metals_likelihood'] = result.get('precious_metals_likelihood', {
                    'gold': 'MEDIUM',
                    'silver': 'MEDIUM',
                    'palladium': 'LOW'
                })
                
                result['raw_response'] = data['choices'][0]['message']['content']
                result['model'] = data.get('model', PPLX_MODEL)
                result['timestamp'] = datetime.now().isoformat()
                
                return result, None
                
            except json.JSONDecodeError as e:
                return {
                    'grade': 'MEDIUM',
                    'type_guess': 'Não foi possível identificar',
                    'explanation': content[:500] if content else 'Erro no processamento',
                    'confidence': 0.3,
                    'metal_value_comment': 'Análise inconclusiva',
                    'notes': f'Erro de parse JSON: {str(e)}',
                    'raw_response': content,
                    'parse_error': True
                }, None
        else:
            error_msg = f'Erro na API Perplexity: {response.status_code}'
            try:
                error_detail = response.json()
                error_msg += f' - {json.dumps(error_detail)}'
            except:
                error_msg += f' - {response.text}'
            return None, error_msg
            
    except requests.exceptions.Timeout:
        return None, 'Timeout ao conectar com a API Perplexity. Tente novamente.'
    except requests.exceptions.RequestException as e:
        return None, f'Erro de conexão com a API Perplexity: {str(e)}'
    except Exception as e:
        return None, f'Erro ao analisar: {str(e)}'

def calculate_price_suggestion(grade, weight_kg, config):
    if not config or not weight_kg:
        return None
    
    try:
        weight = float(weight_kg)
        
        if grade == 'LOW':
            min_price = float(config.get('price_low_min', 0))
            max_price = float(config.get('price_low_max', 0))
        elif grade == 'MEDIUM':
            min_price = float(config.get('price_medium_min', 0))
            max_price = float(config.get('price_medium_max', 0))
        elif grade == 'HIGH':
            min_price = float(config.get('price_high_min', 0))
            max_price = float(config.get('price_high_max', 0))
        else:
            return None
        
        if min_price == 0 and max_price == 0:
            return None
        
        avg_price = (min_price + max_price) / 2
        
        return {
            'price_per_kg_min': min_price,
            'price_per_kg_max': max_price,
            'price_per_kg_avg': avg_price,
            'total_min': round(min_price * weight, 2),
            'total_max': round(max_price * weight, 2),
            'total_avg': round(avg_price * weight, 2),
            'weight_kg': weight,
            'grade': grade
        }
    except Exception as e:
        print(f'Erro ao calcular preço: {e}')
        return None
