from quart import Quart, request, jsonify, render_template
from generators import generate_html, apply_html_changes

app = Quart(__name__)
conversations = {}

@app.route('/')
async def index():
    return await render_template('index.html')

@app.route('/generate-html', methods=['POST'])
async def generate_html_endpoint():
    data = await request.get_json()
    prompt = data.get('instruction')
    conversation_id = data.get('conversation_id')
    
    if conversation_id not in conversations:
        # New conversation
        html_content = await generate_html(prompt)
        conversations[conversation_id] = {
            'name': prompt.split('.')[0][:50],
            'content': [html_content]
        }
    else:
        # Existing conversation, apply changes
        change_instruction = prompt
        current_html = conversations[conversation_id]['content'][-1]
        html_content = await apply_html_changes(current_html, change_instruction)
        conversations[conversation_id]['content'].append(html_content)
    
    return jsonify({'html': html_content})

@app.route('/get-conversation', methods=['GET'])
async def get_conversation():
    conversation_id = request.args.get('conversation_id')
    html_content = conversations.get(conversation_id, {}).get('content', [])
    return jsonify({'html': "".join(html_content)})

@app.route('/get-conversations', methods=['GET'])
async def get_conversations():
    return jsonify({
        'conversations': [
            {'id': convo_id, 'name': convo['name']}
            for convo_id, convo in conversations.items()
        ]
    })

@app.route('/reset-template', methods=['POST'])
async def reset_template():
    # Clear any server-side conversation or state if needed
    # This might involve clearing some session or in-memory state
    return jsonify({"status": "reset successful"})

@app.route('/undo', methods=['POST'])
async def undo():
    data = await request.get_json()
    conversation_id = data.get('conversation_id')
    
    if conversation_id in conversations and len(conversations[conversation_id]['content']) > 1:
        conversations[conversation_id]['content'].pop()
        html_content = conversations[conversation_id]['content'][-1]
    else:
        html_content = ''
        conversations.pop(conversation_id, None)
    
    return jsonify({'html': html_content})

if __name__ == '__main__':
    from hypercorn.config import Config
    from hypercorn.asyncio import serve

    config = Config()
    config.bind = ["127.0.0.1:5000"]

    import asyncio
    asyncio.run(serve(app, config))
