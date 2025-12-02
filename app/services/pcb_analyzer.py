import cv2
import numpy as np
import base64
from io import BytesIO

LOW_THRESHOLD = 15
HIGH_THRESHOLD = 45

MIN_COMPONENT_AREA = 50
MAX_COMPONENT_AREA = 50000

def analyze_pcb_image(image_data) -> dict:
    """
    Analisa uma imagem de placa eletrônica usando OpenCV.
    Retorna um dicionário com:
      - components_count: número aproximado de componentes detectados
      - density_score: valor numérico de densidade (0.0 a 1.0)
      - grade: 'LOW' | 'MEDIUM' | 'HIGH'
      - debug: campos auxiliares para depuração
    """
    try:
        if isinstance(image_data, bytes):
            image_bytes = image_data
        elif isinstance(image_data, str):
            if image_data.startswith('data:image'):
                base64_data = image_data.split(',')[1] if ',' in image_data else image_data
                image_bytes = base64.b64decode(base64_data)
            else:
                image_bytes = base64.b64decode(image_data)
        else:
            return {
                'components_count': 0,
                'density_score': 0.0,
                'grade': 'LOW',
                'error': 'Formato de imagem inválido'
            }
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {
                'components_count': 0,
                'density_score': 0.0,
                'grade': 'LOW',
                'error': 'Não foi possível decodificar a imagem'
            }
        
        height, width = img.shape[:2]
        total_area = height * width
        
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        lower_green1 = np.array([35, 30, 30])
        upper_green1 = np.array([85, 255, 255])
        
        lower_green2 = np.array([75, 20, 20])
        upper_green2 = np.array([100, 255, 255])
        
        lower_brown = np.array([10, 30, 30])
        upper_brown = np.array([30, 255, 200])
        
        mask_green1 = cv2.inRange(hsv, lower_green1, upper_green1)
        mask_green2 = cv2.inRange(hsv, lower_green2, upper_green2)
        mask_brown = cv2.inRange(hsv, lower_brown, upper_brown)
        
        pcb_mask = cv2.bitwise_or(mask_green1, mask_green2)
        pcb_mask = cv2.bitwise_or(pcb_mask, mask_brown)
        
        components_mask = cv2.bitwise_not(pcb_mask)
        
        kernel = np.ones((3, 3), np.uint8)
        components_mask = cv2.morphologyEx(components_mask, cv2.MORPH_OPEN, kernel, iterations=2)
        components_mask = cv2.morphologyEx(components_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        blurred = cv2.GaussianBlur(components_mask, (5, 5), 0)
        
        contours, _ = cv2.findContours(blurred, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_contours = []
        total_component_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if MIN_COMPONENT_AREA <= area <= MAX_COMPONENT_AREA:
                valid_contours.append(contour)
                total_component_area += area
        
        components_count = len(valid_contours)
        
        density_score = min(1.0, total_component_area / (total_area * 0.3))
        
        if components_count < LOW_THRESHOLD:
            grade = 'LOW'
        elif components_count < HIGH_THRESHOLD:
            grade = 'MEDIUM'
        else:
            grade = 'HIGH'
        
        large_components = sum(1 for c in valid_contours if cv2.contourArea(c) > 1000)
        small_components = sum(1 for c in valid_contours if cv2.contourArea(c) <= 1000)
        
        if large_components > 20:
            grade = 'HIGH'
        elif large_components > 10 and grade == 'LOW':
            grade = 'MEDIUM'
        
        return {
            'components_count': components_count,
            'density_score': round(density_score, 3),
            'grade': grade,
            'debug': {
                'image_size': f'{width}x{height}',
                'total_contours': len(contours),
                'valid_contours': components_count,
                'large_components': large_components,
                'small_components': small_components,
                'component_area_ratio': round(total_component_area / total_area, 4) if total_area > 0 else 0,
                'thresholds': {
                    'low': LOW_THRESHOLD,
                    'high': HIGH_THRESHOLD
                }
            }
        }
        
    except Exception as e:
        return {
            'components_count': 0,
            'density_score': 0.0,
            'grade': 'LOW',
            'error': str(e)
        }


def get_type_guess_from_analysis(analysis: dict) -> str:
    """
    Tenta adivinhar o tipo de placa com base na análise.
    """
    components = analysis.get('components_count', 0)
    density = analysis.get('density_score', 0)
    debug = analysis.get('debug', {})
    large = debug.get('large_components', 0)
    
    if components > 60 or (large > 25 and density > 0.5):
        return 'Placa de alta densidade (possivelmente motherboard, celular ou servidor)'
    elif components > 35 or (large > 15 and density > 0.3):
        return 'Placa de média densidade (possivelmente roteador, HD ou placa de vídeo)'
    elif components > 20:
        return 'Placa de baixa-média densidade (possivelmente fonte, impressora ou periférico)'
    else:
        return 'Placa simples (possivelmente fonte de alimentação, controle remoto ou eletrônico básico)'


def generate_local_explanation(grade: str, components_count: int, density_score: float) -> str:
    """
    Gera uma explicação local (fallback) quando a API Perplexity não está disponível.
    """
    grade_labels = {
        'LOW': 'baixo valor',
        'MEDIUM': 'valor intermediário', 
        'HIGH': 'alto valor'
    }
    
    grade_label = grade_labels.get(grade, 'valor não determinado')
    
    if grade == 'HIGH':
        return (
            f'Esta placa foi classificada como de {grade_label} para reciclagem de metais preciosos. '
            f'Foram detectados aproximadamente {components_count} componentes eletrônicos com uma '
            f'densidade de {density_score:.1%}. A alta quantidade de componentes indica maior '
            f'probabilidade de presença de ouro em conectores, chips BGA e processadores.'
        )
    elif grade == 'MEDIUM':
        return (
            f'Esta placa foi classificada como de {grade_label} para reciclagem. '
            f'Foram detectados aproximadamente {components_count} componentes com densidade de {density_score:.1%}. '
            f'A placa possui quantidade moderada de componentes que podem conter metais preciosos.'
        )
    else:
        return (
            f'Esta placa foi classificada como de {grade_label} para reciclagem. '
            f'Foram detectados aproximadamente {components_count} componentes com densidade de {density_score:.1%}. '
            f'Placas simples geralmente contêm menos metais preciosos, mas ainda podem ter valor em cobre e estanho.'
        )
