from flask import Flask, render_template, request, jsonify
import os
import json
from datetime import datetime
import uuid

app = Flask(__name__)

# In-memory storage for call data (in production, use a database)
call_data_storage = []

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
        # Get the webhook data from OmniDimension
        data = request.get_json()
        
        # Log the incoming webhook data
        print(f"Webhook received at {datetime.now()}")
        print(f"Data: {json.dumps(data, indent=2)}")
        
        # Extract relevant information from the webhook
        # Handle different possible data structures from OmniDimension
        call_id = data.get('call_id') or data.get('id') or f'call_{uuid.uuid4().hex[:8]}'
        user_id = data.get('user_id') or data.get('user') or data.get('customer_id', '')
        transcript = data.get('transcript') or data.get('conversation', '') or data.get('audio_text', '')
        summary = data.get('summary') or data.get('call_summary', '') or data.get('analysis', '')
        
        # Determine category based on content or provided category
        category = data.get('category', '')
        if not category and transcript:
            # Simple category detection based on keywords
            transcript_lower = transcript.lower()
            if any(word in transcript_lower for word in ['technical', 'error', 'bug', 'issue']):
                category = 'technical'
            elif any(word in transcript_lower for word in ['billing', 'payment', 'charge', 'invoice']):
                category = 'billing'
            elif any(word in transcript_lower for word in ['service', 'support', 'help']):
                category = 'service'
            elif any(word in transcript_lower for word in ['product', 'feature', 'upgrade']):
                category = 'product'
            else:
                category = 'other'
        
        # Determine priority based on content or provided priority
        priority = data.get('priority', 'medium')
        if priority == 'medium' and transcript:
            transcript_lower = transcript.lower()
            urgent_words = ['urgent', 'emergency', 'critical', 'immediate', 'asap']
            high_words = ['important', 'serious', 'problem', 'issue', 'broken']
            
            if any(word in transcript_lower for word in urgent_words):
                priority = 'urgent'
            elif any(word in transcript_lower for word in high_words):
                priority = 'high'
        
        # Calculate duration if provided
        duration = data.get('duration', 0)
        if isinstance(duration, str):
            try:
                duration = int(duration)
            except:
                duration = 0
        
        call_data = {
            'id': call_id,
            'timestamp': datetime.now().isoformat(),
            'webhook_data': data,
            'transcript': transcript,
            'summary': summary,
            'category': category,
            'priority': priority,
            'user_id': user_id,
            'duration': duration,
            'status': data.get('status', 'completed'),
            'sentiment': data.get('sentiment', 'neutral'),
            'language': data.get('language', 'en'),
            'call_type': data.get('call_type', 'voice'),
            'agent_id': data.get('agent_id', ''),
            'queue_time': data.get('queue_time', 0),
            'resolution_time': data.get('resolution_time', 0)
        }
        
        # Store the call data for viewing in reports
        call_data_storage.append(call_data)
        
        # Keep only the last 100 calls to prevent memory issues
        if len(call_data_storage) > 100:
            call_data_storage.pop(0)
        
        # Log the processed data
        print(f"Processed call data: {json.dumps(call_data, indent=2)}")
        
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Webhook received successfully',
            'call_id': call_data['id'],
            'processed_at': datetime.now().isoformat()
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
        'timestamp': datetime.now().isoformat(),
        'total_calls_received': len(call_data_storage),
        'last_call_time': call_data_storage[-1]['timestamp'] if call_data_storage else None
    }), 200

@app.route('/api/calls', methods=['GET'])
def get_calls():
    """Endpoint to retrieve call history for reports"""
    # Sort calls by timestamp (newest first)
    sorted_calls = sorted(call_data_storage, key=lambda x: x['timestamp'], reverse=True)
    
    return jsonify({
        'status': 'success',
        'calls': sorted_calls,
        'total_calls': len(sorted_calls),
        'last_updated': datetime.now().isoformat()
    }), 200

@app.route('/api/calls/stats', methods=['GET'])
def get_call_stats():
    """Endpoint to get call statistics"""
    if not call_data_storage:
        return jsonify({
            'status': 'success',
            'stats': {
                'total_calls': 0,
                'avg_duration': 0,
                'success_rate': 0,
                'urgent_calls': 0,
                'categories': {},
                'priorities': {}
            }
        }), 200
    
    total_calls = len(call_data_storage)
    completed_calls = len([call for call in call_data_storage if call['status'] == 'completed'])
    success_rate = (completed_calls / total_calls) * 100 if total_calls > 0 else 0
    
    avg_duration = sum(call['duration'] for call in call_data_storage) / total_calls if total_calls > 0 else 0
    urgent_calls = len([call for call in call_data_storage if call['priority'] == 'urgent'])
    
    # Category distribution
    categories = {}
    for call in call_data_storage:
        category = call['category']
        categories[category] = categories.get(category, 0) + 1
    
    # Priority distribution
    priorities = {}
    for call in call_data_storage:
        priority = call['priority']
        priorities[priority] = priorities.get(priority, 0) + 1
    
    return jsonify({
        'status': 'success',
        'stats': {
            'total_calls': total_calls,
            'avg_duration': round(avg_duration, 2),
            'success_rate': round(success_rate, 2),
            'urgent_calls': urgent_calls,
            'categories': categories,
            'priorities': priorities
        }
    }), 200

@app.route('/api/test/add-sample-data', methods=['POST'])
def add_sample_data():
    """Add sample call data for testing"""
    try:
        sample_calls = [
            {
                'id': f'sample_call_{i}',
                'timestamp': datetime.now().isoformat(),
                'webhook_data': {
                    'call_id': f'sample_call_{i}',
                    'user_id': f'user_{i}',
                    'transcript': f'Sample call transcript {i} - Customer reported a technical issue.',
                    'summary': f'Sample call summary {i} - Technical issue resolved.',
                    'category': 'technical',
                    'priority': 'medium',
                    'duration': 120 + (i * 30),
                    'status': 'completed'
                },
                'transcript': f'Sample call transcript {i} - Customer reported a technical issue.',
                'summary': f'Sample call summary {i} - Technical issue resolved.',
                'category': 'technical',
                'priority': 'medium',
                'user_id': f'user_{i}',
                'duration': 120 + (i * 30),
                'status': 'completed',
                'sentiment': 'neutral',
                'language': 'en',
                'call_type': 'voice',
                'agent_id': 'sample_agent',
                'queue_time': 5,
                'resolution_time': 300
            }
            for i in range(1, 6)
        ]
        
        # Add urgent call
        urgent_call = {
            'id': 'urgent_call_1',
            'timestamp': datetime.now().isoformat(),
            'webhook_data': {
                'call_id': 'urgent_call_1',
                'user_id': 'urgent_user',
                'transcript': 'URGENT: System is down and customers cannot access their accounts!',
                'summary': 'Critical system outage affecting all users.',
                'category': 'technical',
                'priority': 'urgent',
                'duration': 300,
                'status': 'completed'
            },
            'transcript': 'URGENT: System is down and customers cannot access their accounts!',
            'summary': 'Critical system outage affecting all users.',
            'category': 'technical',
            'priority': 'urgent',
            'user_id': 'urgent_user',
            'duration': 300,
            'status': 'completed',
            'sentiment': 'negative',
            'language': 'en',
            'call_type': 'voice',
            'agent_id': 'urgent_agent',
            'queue_time': 0,
            'resolution_time': 600
        }
        
        sample_calls.append(urgent_call)
        
        # Add to storage
        call_data_storage.extend(sample_calls)
        
        return jsonify({
            'status': 'success',
            'message': f'Added {len(sample_calls)} sample calls',
            'total_calls': len(call_data_storage)
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error adding sample data: {str(e)}'
        }), 500

@app.route('/api/test/clear-data', methods=['POST'])
def clear_data():
    """Clear all call data"""
    try:
        global call_data_storage
        call_data_storage = []
        
        return jsonify({
            'status': 'success',
            'message': 'All call data cleared',
            'total_calls': 0
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Error clearing data: {str(e)}'
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

    
