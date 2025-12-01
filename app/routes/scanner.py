from flask import Blueprint, request, jsonify, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import db, Usuario, ScannerConfig, ScannerAnalysis
from app.services.pcb_scanner import analyze_pcb_image, calculate_price_suggestion
from app.auth import admin_required
from datetime import datetime
import base64
import os

bp = Blueprint('scanner', __name__)

def get_scanner_config():
    config = ScannerConfig.query.first()
    if not config:
        config = ScannerConfig(
            enabled=True,
            price_low_min=5.0,
            price_low_max=15.0,
            price_medium_min=20.0,
            price_medium_max=50.0,
            price_high_min=60.0,
            price_high_max=150.0,
            prompt_rules=''
        )
        db.session.add(config)
        db.session.commit()
    return config

@bp.route('/api/scanner/analyze', methods=['POST'])
@jwt_required()
def analyze_pcb():
    try:
        usuario_id = get_jwt_identity()
        config = get_scanner_config()
        
        if not config.enabled:
            return jsonify({'erro': 'Scanner desativado pelo administrador'}), 403
        
        image_data = None
        description = None
        weight_kg = None
        
        if 'image' in request.files:
            image_file = request.files['image']
            image_data = image_file.read()
        
        if request.is_json:
            data = request.get_json()
            if 'image_base64' in data:
                image_data = data['image_base64']
            description = data.get('description')
            weight_kg = data.get('weight_kg')
        else:
            description = request.form.get('description')
            if 'weight_kg' in request.form:
                try:
                    weight_kg = float(request.form.get('weight_kg'))
                except:
                    pass
        
        result, error = analyze_pcb_image(
            image_data,
            weight_kg=weight_kg,
            prompt_rules=config.prompt_rules,
            description=description
        )
        
        if error:
            if 'não configurada' in error or 'não fornecida' in error or 'inválido' in error.lower():
                return jsonify({'erro': error}), 400
            return jsonify({'erro': error}), 500
        
        price_suggestion = None
        if weight_kg and result.get('grade'):
            price_suggestion = calculate_price_suggestion(
                result['grade'],
                weight_kg,
                {
                    'price_low_min': config.price_low_min,
                    'price_low_max': config.price_low_max,
                    'price_medium_min': config.price_medium_min,
                    'price_medium_max': config.price_medium_max,
                    'price_high_min': config.price_high_min,
                    'price_high_max': config.price_high_max
                }
            )
        
        try:
            analysis = ScannerAnalysis(
                usuario_id=int(usuario_id),
                grade=result.get('grade'),
                type_guess=result.get('type_guess'),
                explanation=result.get('explanation'),
                confidence=result.get('confidence'),
                weight_kg=weight_kg,
                price_suggestion=price_suggestion,
                components_detected=result.get('components_detected'),
                precious_metals=result.get('precious_metals_likelihood'),
                raw_response=result.get('raw_response')
            )
            db.session.add(analysis)
            db.session.commit()
            result['analysis_id'] = analysis.id
        except Exception as e:
            print(f'Erro ao salvar análise: {e}')
        
        response = {
            'grade': result.get('grade'),
            'type_guess': result.get('type_guess'),
            'visual_analysis': result.get('visual_analysis'),
            'explanation': result.get('explanation'),
            'confidence': result.get('confidence'),
            'metal_value_comment': result.get('metal_value_comment'),
            'notes': result.get('notes'),
            'components_detected': result.get('components_detected'),
            'precious_metals_likelihood': result.get('precious_metals_likelihood'),
            'price_suggestion': price_suggestion,
            'timestamp': result.get('timestamp')
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        print(f'Erro no scanner: {e}')
        return jsonify({'erro': str(e)}), 500

@bp.route('/api/scanner/config', methods=['GET'])
@jwt_required()
def get_config():
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
        
        config = get_scanner_config()
        return jsonify(config.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@bp.route('/api/admin/scanner-config', methods=['GET'])
@jwt_required()
def get_admin_config():
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
        
        config = get_scanner_config()
        return jsonify(config.to_dict()), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@bp.route('/api/admin/scanner-config', methods=['POST'])
@jwt_required()
def update_admin_config():
    try:
        usuario_id = get_jwt_identity()
        usuario = Usuario.query.get(usuario_id)
        
        if not usuario or usuario.tipo != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
        
        data = request.get_json()
        config = get_scanner_config()
        
        if 'enabled' in data:
            config.enabled = bool(data['enabled'])
        if 'price_low_min' in data:
            config.price_low_min = float(data['price_low_min'])
        if 'price_low_max' in data:
            config.price_low_max = float(data['price_low_max'])
        if 'price_medium_min' in data:
            config.price_medium_min = float(data['price_medium_min'])
        if 'price_medium_max' in data:
            config.price_medium_max = float(data['price_medium_max'])
        if 'price_high_min' in data:
            config.price_high_min = float(data['price_high_min'])
        if 'price_high_max' in data:
            config.price_high_max = float(data['price_high_max'])
        if 'prompt_rules' in data:
            config.prompt_rules = str(data['prompt_rules'])
        
        config.updated_at = datetime.utcnow()
        config.updated_by = int(usuario_id)
        db.session.commit()
        
        return jsonify({
            'mensagem': 'Configurações atualizadas com sucesso',
            'config': config.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@bp.route('/api/scanner/status', methods=['GET'])
def scanner_status():
    try:
        config = get_scanner_config()
        api_configured = bool(os.getenv('GEMINI_API_KEY'))
        
        return jsonify({
            'enabled': config.enabled,
            'api_configured': api_configured,
            'ready': config.enabled and api_configured,
            'model': 'gemini'
        }), 200
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@bp.route('/api/scanner/history', methods=['GET'])
@jwt_required()
def scanner_history():
    try:
        usuario_id = get_jwt_identity()
        limit = request.args.get('limit', 20, type=int)
        
        analyses = ScannerAnalysis.query.filter_by(
            usuario_id=int(usuario_id)
        ).order_by(
            ScannerAnalysis.created_at.desc()
        ).limit(limit).all()
        
        return jsonify([a.to_dict() for a in analyses]), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@bp.route('/scanner')
def scanner_page():
    return render_template('scanner.html')

@bp.route('/admin/scanner-config')
def admin_scanner_config_page():
    return render_template('admin-scanner-config.html')
