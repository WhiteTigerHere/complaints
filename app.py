from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return render_template('webhook-test.html')

@app.route('/health')
def health():
    return {'status': 'healthy'}

@app.route('/api/webhook', methods=['POST'])
def webhook():
    """Webhook endpoint for OmniDimension to send call data"""
    try:
        # Get the webhook data from OmniDimension
        data = request.get_json()
        
        # Log the incoming webhook data
        print(f"Webhook received at {datetime.now()}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        # Extract relevant information from the webhook
        call_data = {
            'timestamp': datetime.now().isoformat(),
            'webhook_data': data,
            'call_id': data.get('call_id', 'unknown'),
            'transcript': data.get('transcript', ''),
            'summary': data.get('summary', ''),
            'category': data.get('category', ''),
            'priority': data.get('priority', ''),
            'user_id': data.get('user_id', ''),
            'duration': data.get('duration', 0),
            'status': data.get('status', 'completed')
        }
        
        # Here you can process the call data
        # For example, save to database, send notifications, etc.
        
        # Log the processed data
        print(f"Processed call data: {json.dumps(call_data, indent=2)}")
        
        # You could save this to a database or file
        # save_call_data(call_data)
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Webhook received successfully',
            'call_id': call_data['call_id']
        }), 200
        
    except Exception as e:
        print(f"Error processing webhook: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Error processing webhook: {str(e)}'
        }), 500

@app.route('/api/webhook', methods=['GET'])
def webhook_status():
    """Health check endpoint for the webhook"""
    return jsonify({
        'status': 'healthy',
        'message': 'Webhook endpoint is active',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/calls', methods=['GET'])
def get_calls():
    """Endpoint to retrieve call history (for testing)"""
    # This would typically fetch from a database
    # For now, return a sample response
    return jsonify({
        'status': 'success',
        'calls': [
            {
                'id': 'sample_call_1',
                'timestamp': datetime.now().isoformat(),
                'status': 'completed',
                'duration': 120
            }
        ]
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

    
