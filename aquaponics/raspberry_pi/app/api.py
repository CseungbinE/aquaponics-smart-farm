import csv
import io
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file, current_app

api_bp = Blueprint('api', __name__)

# ==========================================
# 헬퍼 함수
# ==========================================
def make_response(data=None, status="success", code=200):
    """표준 API 응답 생성"""
    response = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
    }
    if data is not None:
        if isinstance(data, dict):
            response.update(data)
        else:
            response['data'] = data
    return jsonify(response), code

def get_db():
    """DB 매니저 객체 반환"""
    return current_app.config.get('DB_MANAGER')

def get_sys_config():
    """시스템 설정 객체 반환"""
    return current_app.config.get('SYSTEM_CONFIG')

def get_sensor_manager():
    """[추가] 센서 매니저 객체 반환 (아두이노 명령 전송용)"""
    return current_app.config.get('SENSOR_MANAGER')

# ==========================================
# 1. Health Check
# ==========================================
@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.1.0"
    }), 200

# ==========================================
# 2. Get Current Readings (단위 추가 보완)
# ==========================================
@api_bp.route('/api/current', methods=['GET'])
def get_current_readings():
    try:
        db = get_db()
        latest = db.get_latest_reading()
        
        sensor_health = {}
        config = get_sys_config()
        
        if config:
            # 설정에서 임계값 정보(단위 포함) 가져오기
            thresholds = config.config_data.get('monitoring', {}).get('alert_thresholds', {})
            
            for sensor_name, settings in config.get('hardware', {}).get('sensors', {}).items():
                # Config 키와 매칭 (대소문자 처리)
                threshold_key = sensor_name
                if sensor_name == 'Temp': threshold_key = 'temperature'
                if sensor_name == 'Level': threshold_key = 'water_level'
                
                unit = thresholds.get(threshold_key, {}).get('unit', '')

                sensor_health[sensor_name] = {
                    "sensor_id": 0,
                    "name": sensor_name,
                    "is_healthy": settings.get('enabled', False),
                    "last_reading": {
                        "value": latest.get(sensor_name) if latest else 0,
                        "unit": unit  # [보완] Config에서 가져온 단위 적용
                    }
                }

        return make_response({
            "readings": latest if latest else {},
            "sensor_health": sensor_health
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 3. Get Historical Data
# ==========================================
@api_bp.route('/api/history', methods=['GET'])
def get_history():
    try:
        days = int(request.args.get('days', 1))
        limit = int(request.args.get('limit', 1000))
        data = get_db().get_history(days=days, limit=limit)
        return make_response({"days": days, "count": len(data), "data": data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 4. Get Statistics
# ==========================================
@api_bp.route('/api/statistics', methods=['GET'])
def get_statistics():
    try:
        hours = int(request.args.get('hours', 24))
        stats = get_db().get_statistics(hours=hours)
        return make_response({"hours": hours, "statistics": stats})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 5. Get Alerts
# ==========================================
@api_bp.route('/api/alerts/active', methods=['GET'])
def get_active_alerts():
    try:
        alerts = get_db().get_active_alerts()
        return make_response({"count": len(alerts), "alerts": alerts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    try:
        default_start = (datetime.now() - timedelta(days=7)).isoformat()
        default_end = datetime.now().isoformat()
        start = request.args.get('start_date', default_start)
        end = request.args.get('end_date', default_end)
        alerts = get_db().get_alerts_by_range(start, end)
        return make_response({"count": len(alerts), "alerts": alerts})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/alerts', methods=['POST'])
def create_alert():
    try:
        data = request.json
        new_alert = get_db().create_alert(
            data.get('sensor_name'), 
            data.get('alert_type', 'WARNING'),
            data.get('value'), 
            data.get('message', 'Manual Alert')
        )
        return make_response({"alert": new_alert}, status="created", code=201)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    try:
        if get_db().resolve_alert(alert_id):
            return make_response({"status": "resolved"})
        else:
            return jsonify({"error": "Alert not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 9. Calibrate Sensor (아두이노 명령 전송 추가)
# ==========================================
@api_bp.route('/api/calibration/<sensor_name>', methods=['POST'])
def calibrate_sensor(sensor_name):
    """
    센서 캘리브레이션 처리
    1. DB에 기록 저장
    2. Arduino로 시리얼 명령 전송 (중요!)
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No calibration data"}), 400
            
        # 1. DB 저장
        get_db().save_calibration(sensor_name, data)
        
        # 2. [보완] Arduino로 명령 전송
        # 포인트 데이터 예시: {"low": 410, "mid": 307}
        points = data.get('points', {})
        sensor_mgr = get_sensor_manager()
        
        sent_commands = []
        if sensor_mgr and hasattr(sensor_mgr, 'send_command'):
            # 센서별 명령 접두어 매핑
            prefix_map = {
                "pH": "CALIB_PH",
                "EC": "CALIB_EC",
                "DO": "CALIB_DO",
                "turbidity": "CALIB_TURB"
            }
            
            cmd_prefix = prefix_map.get(sensor_name)
            if cmd_prefix:
                for point_name, raw_value in points.items():
                    # 명령 포맷: CALIB_PH:LOW:410
                    cmd = f"{cmd_prefix}:{point_name.upper()}:{raw_value}"
                    sensor_mgr.send_command(cmd)
                    sent_commands.append(cmd)
            else:
                print(f"No serial command prefix for {sensor_name}")

        return make_response({
            "sensor": sensor_name,
            "status": "calibrated",
            "points": points,
            "arduino_commands": sent_commands
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/calibration/<sensor_name>', methods=['GET'])
def get_calibration(sensor_name):
    try:
        calib = get_db().get_latest_calibration(sensor_name)
        if calib: return make_response({"calibration": calib})
        else: return jsonify({"error": "No calibration found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 11. Configuration
# ==========================================
@api_bp.route('/api/config', methods=['GET'])
def get_config():
    try:
        config = get_sys_config()
        return make_response({
            "config": config.config_data, 
            "thresholds": config.config_data.get('monitoring', {}).get('alert_thresholds', {})
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/api/config', methods=['POST'])
def update_config():
    try:
        config = get_sys_config()
        config.update(request.json)
        config.save()
        return make_response({"status": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 13. Export Data
# ==========================================
@api_bp.route('/api/export', methods=['GET'])
def export_data():
    try:
        format_type = request.args.get('format', 'json')
        hours = int(request.args.get('hours', 24))
        
        db = get_db()
        data = db.get_history(hours=hours, limit=10000)
        
        if format_type == 'json':
            return make_response({"hours": hours, "count": len(data), "data": data})
        elif format_type == 'csv':
            si = io.StringIO()
            if data:
                # [보완] 컬럼 순서 고정 (보기 좋게)
                field_order = ['id', 'timestamp', 'pH', 'EC', 'temperature', 'DO', 'water_level', 'turbidity', 'status']
                # 실제 데이터에 있는 키만 필터링
                existing_keys = data[0].keys()
                ordered_keys = [k for k in field_order if k in existing_keys]
                # 나머지가 있다면 뒤에 추가
                remaining_keys = [k for k in existing_keys if k not in ordered_keys]
                final_keys = ordered_keys + remaining_keys
                
                cw = csv.DictWriter(si, fieldnames=final_keys)
                cw.writeheader()
                cw.writerows(data)
            
            return send_file(
                io.BytesIO(si.getvalue().encode('utf-8-sig')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'export_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
            )
        else:
            return jsonify({"error": "Invalid format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500