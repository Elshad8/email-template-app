from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
email_template = ""
history = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update-template', methods=['POST'])
def update_template():
    global email_template, history
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400

    history.append(email_template)

    try:
        if prompt.startswith('header:'):
            header_text = prompt[len('header:'):].strip()
            if not header_text:
                raise ValueError("Header text cannot be empty")
            email_template += f"<h1>{header_text}</h1>"
        elif prompt.startswith('subheader:'):
            subheader_text = prompt[len('subheader:'):].strip()
            if not subheader_text:
                raise ValueError("Subheader text cannot be empty")
            email_template += f"<h2>{subheader_text}</h2>"
        elif prompt.startswith('list:'):
            list_items = prompt[len('list:'):].strip().split(',')
            if not list_items:
                raise ValueError("List items cannot be empty")
            email_template += "<ul>" + "".join(f"<li>{item.strip()}</li>" for item in list_items) + "</ul>"
        elif prompt.startswith('paragraph:'):
            paragraph_text = prompt[len('paragraph:'):].strip()
            if not paragraph_text:
                raise ValueError("Paragraph text cannot be empty")
            email_template += f"<p>{paragraph_text}</p>"
        elif prompt.startswith('bold:'):
            bold_text = prompt[len('bold:'):].strip()
            if not bold_text:
                raise ValueError("Bold text cannot be empty")
            email_template += f"<b>{bold_text}</b>"
        elif prompt.startswith('italic:'):
            italic_text = prompt[len('italic:'):].strip()
            if not italic_text:
                raise ValueError("Italic text cannot be empty")
            email_template += f"<i>{italic_text}</i>"
        elif prompt.startswith('quote:'):
            quote_text = prompt[len('quote:'):].strip()
            if not quote_text:
                raise ValueError("Quote text cannot be empty")
            email_template += f"<blockquote>{quote_text}</blockquote>"
        elif prompt.startswith('image:'):
            image_url = prompt[len('image:'):].strip()
            if not image_url:
                raise ValueError("Image URL cannot be empty")
            email_template += f'<img src="{image_url}" alt="Image">'
        elif prompt.startswith('link:'):
            parts = prompt[len('link:'):].strip().split(',')
            if len(parts) != 2:
                raise ValueError("Invalid link format. Use 'link: text, url'")
            link_text, link_url = parts
            if not link_text or not link_url:
                raise ValueError("Link text and URL cannot be empty")
            email_template += f'<a href="{link_url.strip()}">{link_text.strip()}</a>'
        else:
            email_template += f"<p>{prompt}</p>"
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(template=email_template)

@app.route('/reset-template', methods=['POST'])
def reset_template():
    global email_template, history
    history.append(email_template)
    email_template = ""
    return jsonify(template=email_template)

@app.route('/undo', methods=['POST'])
def undo():
    global email_template, history
    if history:
        email_template = history.pop()
    return jsonify(template=email_template)

if __name__ == '__main__':
    app.run(debug=True)
