from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for call data (in production, use a database)
call_data_storage = []

# Expected JSON structure from OmniDimension
EXPECTED_WEBHOOK_FIELDS = [
    'call_id', 'transcript', 'summary', 'category', 'priority',
    'user_id', 'duration', 'status', 'sentiment', 'intent',
    'entities', 'confidence', 'language', 'channel'
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('webhook-test.html')

@app.route('/reports')
def reports():
    return render_template('reports.html')

@app.route('/health')
def health():
    return {'status': 'healthy'}

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for OmniDimension to send call data"""
    try:
        # Log the incoming request
        logger.info(f"=== WEBHOOK RECEIVED ===")
        logger.info(f"Timestamp: {datetime.now()}")
        logger.info(f"Headers: {dict(request.headers)}")
        logger.info(f"Content-Type: {request.content_type}")
        
        # Get the webhook data from OmniDimension
        if not request.is_json:
            logger.error("Request is not JSON format")
            return jsonify({
                'status': 'error',
                'message': 'Request must be JSON format'
            }), 400
        
        data = request.get_json()
        
        # Log the raw incoming webhook data
        logger.info(f"Raw webhook data:")
        logger.info(json.dumps(data, indent=2))
        
        # Validate the data structure
        validation_result = validate_webhook_data(data)
        if not validation_result['valid']:
            logger.error(f"Data validation failed: {validation_result['errors']}")
            return jsonify({
                'status': 'error',
                'message': f'Data validation failed: {validation_result["errors"]}'
            }), 400
        
        # Extract relevant information from the webhook
        call_data = {
            'id': data.get('call_id', f'call_{datetime.now().timestamp()}'),
            'timestamp': datetime.now().isoformat(),
            'webhook_data': data,
            'transcript': data.get('transcript', ''),
            'summary': data.get('summary', ''),
            'category': data.get('category', ''),
            'priority': data.get('priority', ''),
            'user_id': data.get('user_id', ''),
            'duration': data.get('duration', 0),
            'status': data.get('status', 'completed'),
            'sentiment': data.get('sentiment', ''),
            'intent': data.get('intent', ''),
            'confidence': data.get('confidence', 0),
            'language': data.get('language', 'en'),
            'channel': data.get('channel', 'web')
        }
        
        # Store the call data for viewing in reports
        call_data_storage.append(call_data)
        
        # Keep only the last 100 calls to prevent memory issues
        if len(call_data_storage) > 100:
            call_data_storage.pop(0)
        
        # Log the processed data
        logger.info(f"Processed call data:")
        logger.info(json.dumps(call_data, indent=2))
        logger.info(f"Total calls stored: {len(call_data_storage)}")
        logger.info("=== WEBHOOK PROCESSED SUCCESSFULLY ===")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Webhook received successfully',
            'call_id': call_data['id'],
            'timestamp': call_data['timestamp']
        }), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing webhook: {str(e)}'
        }), 500

def validate_webhook_data(data):
    """Validate the incoming webhook data structure"""
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Data must be a JSON object")
        return {'valid': False, 'errors': errors}
    
    # Check for required fields (at least one of these should be present)
    required_fields = ['call_id', 'transcript', 'summary']
    if not any(field in data for field in required_fields):
        errors.append(f"At least one of these fields must be present: {required_fields}")
    
    # Check for unexpected field types
    if 'duration' in data and not isinstance(data['duration'], (int, float)):
        errors.append("Duration must be a number")
    
    if 'confidence' in data and not isinstance(data['confidence'], (int, float)):
        errors.append("Confidence must be a number")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }

@app.route('/api/webhook', methods=['GET'])
def webhook_status():
    """Health check endpoint for the webhook"""
    return jsonify({
        'status': 'healthy',
        'message': 'Webhook endpoint is active',
        'timestamp': datetime.now().isoformat(),
        'total_calls_received': len(call_data_storage)
    }), 200

@app.route('/api/calls', methods=['GET'])
def get_calls():
    """Endpoint to retrieve call history for reports"""
    return jsonify({
        'status': 'success',
        'calls': call_data_storage,
        'total_calls': len(call_data_storage)
    }), 200

@app.route('/api/webhook/logs', methods=['GET'])
def get_webhook_logs():
    """Endpoint to view recent webhook activity"""
    return jsonify({
        'status': 'success',
        'message': 'Check server logs for detailed webhook activity',
        'total_calls_received': len(call_data_storage),
        'last_call_timestamp': call_data_storage[-1]['timestamp'] if call_data_storage else None
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)

    

