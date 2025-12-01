import os
import base64
import requests
import json
from datetime import datetime

PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_MODEL = 'llama-3.1-sonar-large-128k-online'

def get_scanner_prompt(prompt_rules=None):
    base_prompt = """Você é um especialista em reciclagem de placas eletrônicas (PCBs) e recuperação de metais preciosos.
Analise a imagem da placa eletrônica fornecida e classifique-a para fins de reciclagem de metais preciosos.

CRITÉRIOS DE CLASSIFICAÇÃO:
- LOW (Baixo valor): Placas simples, poucas camadas, poucos componentes, baixa densidade de conectores dourados
- MEDIUM (Médio valor): Placas com densidade moderada de componentes, alguns conectores dourados, chips médios
- HIGH (Alto valor): Placas com alta densidade de componentes, muitos conectores dourados, chips BGA, processadores, memórias

TIPOS COMUNS DE PLACAS:
- Motherboard de PC/Servidor (geralmente HIGH)
- Placa de celular/smartphone (geralmente HIGH)
- Placa de fonte de alimentação (geralmente LOW)
- Placa de telecom/roteador (geralmente MEDIUM a HIGH)
- Placa de HD/SSD (geralmente MEDIUM)
- Placa de impressora (geralmente LOW)
- Placa de TV/monitor (geralmente LOW a MEDIUM)

RESPONDA EXCLUSIVAMENTE EM JSON com este formato exato:
{
  "grade": "LOW" | "MEDIUM" | "HIGH",
  "type_guess": "tipo provável da placa",
  "explanation": "explicação curta do motivo da classificação",
  "confidence": número entre 0 e 1,
  "components_detected": ["lista de componentes identificados"],
  "precious_metals_likelihood": {
    "gold": "LOW" | "MEDIUM" | "HIGH",
    "silver": "LOW" | "MEDIUM" | "HIGH",
    "palladium": "LOW" | "MEDIUM" | "HIGH"
  }
}"""
    
    if prompt_rules:
        base_prompt += f"\n\nREGRAS ADICIONAIS:\n{prompt_rules}"
    
    return base_prompt

def analyze_pcb_image(image_data, weight_kg=None, prompt_rules=None):
    if not PERPLEXITY_API_KEY:
        return None, 'Chave API do Perplexity não configurada. Configure PERPLEXITY_API_KEY.'
    
    try:
        if isinstance(image_data, bytes):
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        elif image_data.startswith('data:image'):
            image_base64 = image_data.split(',')[1] if ',' in image_data else image_data
        else:
            image_base64 = image_data
        
        headers = {
            'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        system_prompt = get_scanner_prompt(prompt_rules)
        
        user_message = "Analise esta placa eletrônica para reciclagem de metais preciosos."
        if weight_kg:
            user_message += f" O peso estimado da placa é {weight_kg} kg."
        
        payload = {
            'model': PERPLEXITY_MODEL,
            'messages': [
                {'role': 'system', 'content': system_prompt},
                {
                    'role': 'user',
                    'content': [
                        {'type': 'text', 'text': user_message},
                        {
                            'type': 'image_url',
                            'image_url': {
                                'url': f'data:image/jpeg;base64,{image_base64}'
                            }
                        }
                    ]
                }
            ],
            'max_tokens': 1024,
            'temperature': 0.3,
            'top_p': 0.9,
            'return_images': False,
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
                
                result = json.loads(content.strip())
                
                if 'grade' not in result:
                    result['grade'] = 'MEDIUM'
                if 'type_guess' not in result:
                    result['type_guess'] = 'Placa eletrônica não identificada'
                if 'explanation' not in result:
                    result['explanation'] = 'Análise baseada em características visuais'
                if 'confidence' not in result:
                    result['confidence'] = 0.5
                
                result['raw_response'] = data['choices'][0]['message']['content']
                result['model'] = data.get('model', PERPLEXITY_MODEL)
                result['timestamp'] = datetime.now().isoformat()
                
                return result, None
                
            except json.JSONDecodeError:
                return {
                    'grade': 'MEDIUM',
                    'type_guess': 'Não foi possível identificar',
                    'explanation': content[:500],
                    'confidence': 0.3,
                    'raw_response': content,
                    'parse_error': True
                }, None
        else:
            error_msg = f'Erro na API Perplexity: {response.status_code}'
            try:
                error_detail = response.json()
                error_msg += f' - {error_detail}'
            except:
                pass
            return None, error_msg
            
    except Exception as e:
        return None, f'Erro ao analisar imagem: {str(e)}'

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
