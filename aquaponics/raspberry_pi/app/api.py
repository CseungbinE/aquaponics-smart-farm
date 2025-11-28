import csv
import io
import json
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, send_file, current_app
# 주의: database.py와 config.py가 같은 app 폴더 내에 있어야 합니다.
# 실제 실행 시 main.py에서 db와 config 객체를 주입하거나 전역으로 관리해야 합니다.
# 여기서는 main.py에서 app.config['DB_MANAGER']와 app.config['SYSTEM_CONFIG']로 접근한다고 가정합니다.

api_bp = Blueprint('api', __name__)

# ==========================================
# 헬퍼 함수: 응답 포맷 표준화
# ==========================================
def make_response(data=None, status="success", code=200):
    """
    API.md에 정의된 표준 응답 포맷을 생성합니다.
    {
      "timestamp": "...",
      "status": "success",
      "data": { ... }
    }
    """
    response = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
    }
    if data is not None:
        if status == "success":
            # 어떤 엔드포인트는 data 키 바로 아래에 내용을 넣고, 
            # 어떤 것은 data 키 없이 필드들을 병합하기도 합니다. 
            # 여기서는 편의상 data 필드 안에 넣거나, data가 딕셔너리면 병합합니다.
            if isinstance(data, dict):
                response.update(data)
            else:
                response['data'] = data
    
    return jsonify(response), code

def get_db():
    """Flask app context에서 DB 매니저 객체를 가져옵니다."""
    return current_app.config.get('DB_MANAGER')

def get_sys_config():
    """Flask app context에서 Config 객체를 가져옵니다."""
    return current_app.config.get('SYSTEM_CONFIG')

# ==========================================
# 1. Health Check
# ==========================================
@api_bp.route('/health', methods=['GET'])
def health_check():
    """시스템 상태 확인"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }), 200

# ==========================================
# 2. Get Current Readings
# ==========================================
@api_bp.route('/api/current', methods=['GET'])
def get_current_readings():
    """최신 센서 데이터 조회"""
    try:
        db = get_db()
        # DB에서 가장 최신 레코드 1개를 가져오는 함수 호출
        latest = db.get_latest_reading()
        
        # 센서별 상태 정보 (Mock data logic - 실제 구현에 맞게 수정 필요)
        sensor_health = {}
        config = get_sys_config()
        if config:
            for sensor_name, settings in config.get('hardware', {}).get('sensors', {}).items():
                sensor_health[sensor_name] = {
                    "sensor_id": 0, # DB나 Config에서 ID 매핑 필요
                    "name": sensor_name,
                    "is_healthy": settings.get('enabled', False),
                    "last_reading": {
                        "value": latest.get(sensor_name) if latest else 0,
                        "unit": "" # Config에서 단위 가져오기 가능
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
    """과거 데이터 조회"""
    try:
        days = int(request.args.get('days', 1))
        limit = int(request.args.get('limit', 1000))
        
        db = get_db()
        # database.py에 get_history(days, limit) 메서드가 있어야 함
        data = db.get_history(days=days, limit=limit)
        
        return make_response({
            "days": days,
            "count": len(data),
            "data": data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 4. Get Statistics
# ==========================================
@api_bp.route('/api/statistics', methods=['GET'])
def get_statistics():
    """통계 데이터 조회"""
    try:
        hours = int(request.args.get('hours', 24))
        
        db = get_db()
        # database.py에 get_statistics(hours) 메서드가 있어야 함
        stats = db.get_statistics(hours=hours)
        
        return make_response({
            "hours": hours,
            "statistics": stats
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 5. Get Active Alerts
# ==========================================
@api_bp.route('/api/alerts/active', methods=['GET'])
def get_active_alerts():
    """활성 경고 조회"""
    try:
        db = get_db()
        alerts = db.get_active_alerts()
        
        return make_response({
            "count": len(alerts),
            "alerts": alerts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 6. Get Alerts by Range
# ==========================================
@api_bp.route('/api/alerts', methods=['GET'])
def get_alerts():
    """기간별 경고 조회"""
    try:
        # 기본값: 최근 7일
        default_start = (datetime.now() - timedelta(days=7)).isoformat()
        default_end = datetime.now().isoformat()
        
        start_date = request.args.get('start_date', default_start)
        end_date = request.args.get('end_date', default_end)
        
        db = get_db()
        alerts = db.get_alerts_by_range(start_date, end_date)
        
        return make_response({
            "count": len(alerts),
            "alerts": alerts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 7. Create Alert (Manual)
# ==========================================
@api_bp.route('/api/alerts', methods=['POST'])
def create_alert():
    """수동 경고 생성"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        db = get_db()
        # database.py에 create_alert 메서드 필요
        new_alert = db.create_alert(
            sensor_name=data.get('sensor_name'),
            alert_type=data.get('alert_type', 'WARNING'),
            value=data.get('value'),
            message=data.get('message', 'Manual Alert')
        )
        
        return make_response({"alert": new_alert}, status="created", code=201)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 8. Resolve Alert
# ==========================================
@api_bp.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """경고 해결 처리"""
    try:
        db = get_db()
        success = db.resolve_alert(alert_id)
        
        if success:
            return make_response({"status": "resolved"})
        else:
            return jsonify({"error": "Alert not found or update failed"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 9. Calibrate Sensor
# ==========================================
@api_bp.route('/api/calibration/<sensor_name>', methods=['POST'])
def calibrate_sensor(sensor_name):
    """센서 캘리브레이션 데이터 저장"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No calibration data"}), 400
            
        db = get_db()
        # 1. DB에 캘리브레이션 기록 저장
        db.save_calibration(sensor_name, data)
        
        # 2. (선택사항) Arduino로 시리얼 명령을 보내는 로직이 여기에 추가될 수 있음
        # 예: serial_manager.send_command(f"CALIB_{sensor_name}...")
        
        return make_response({
            "sensor": sensor_name,
            "status": "calibrated",
            "points": data.get('points')
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 10. Get Calibration Data
# ==========================================
@api_bp.route('/api/calibration/<sensor_name>', methods=['GET'])
def get_calibration(sensor_name):
    """센서 캘리브레이션 이력 조회"""
    try:
        db = get_db()
        calib_data = db.get_latest_calibration(sensor_name)
        
        if calib_data:
            return make_response({"calibration": calib_data})
        else:
            return jsonify({"error": "No calibration found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 11. Get Configuration
# ==========================================
@api_bp.route('/api/config', methods=['GET'])
def get_config():
    """현재 설정 조회"""
    try:
        config = get_sys_config()
        # 전체 설정을 반환하거나, 민감한 정보는 제외하고 반환
        return make_response({
            "config": config.config_data,  # Config 객체 내부의 딕셔너리
            "thresholds": config.config_data.get('monitoring', {}).get('alert_thresholds', {})
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 12. Update Configuration
# ==========================================
@api_bp.route('/api/config', methods=['POST'])
def update_config():
    """설정 업데이트"""
    try:
        new_data = request.json
        if not new_data:
            return jsonify({"error": "No config data"}), 400
            
        config = get_sys_config()
        # Config 객체에 update 메서드가 있어야 함
        config.update(new_data)
        config.save() # 파일로 저장
        
        return make_response({"status": "updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==========================================
# 13. Export Data (Bonus)
# ==========================================
@api_bp.route('/api/export', methods=['GET'])
def export_data():
    """데이터 내보내기 (CSV/JSON)"""
    try:
        format_type = request.args.get('format', 'json')
        hours = int(request.args.get('hours', 24))
        
        db = get_db()
        data = db.get_history(hours=hours, limit=10000) # Export는 limit을 크게
        
        if format_type == 'json':
            return make_response({
                "hours": hours,
                "count": len(data),
                "data": data
            })
            
        elif format_type == 'csv':
            # CSV 생성
            si = io.StringIO()
            if data:
                # 키(헤더) 추출
                keys = data[0].keys()
                cw = csv.DictWriter(si, fieldnames=keys)
                cw.writeheader()
                cw.writerows(data)
            
            output = si.getvalue()
            
            return send_file(
                io.BytesIO(output.encode('utf-8-sig')), # 한글 깨짐 방지 BOM
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'export_{datetime.now().strftime("%Y%m%d_%H%M")}.csv'
            )
        else:
            return jsonify({"error": "Invalid format"}), 400
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500