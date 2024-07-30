from flask import Flask, render_template, request, jsonify
import openai
import re
from langchain_openai import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

app = Flask(__name__)
email_template = ""
history = []
sections = []

# Load environment variables from .env file
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

# Define the LangChain prompt template
prompt_template = PromptTemplate(
    input_variables=["prompt"],
    template="Generate HTML content based on the following prompt: {prompt}"
)

# HTML templates dictionary
html_templates = {
    "header": lambda content: f"<div class='header'><h1>{content}</h1></div>",
    "footer": lambda content: f"<div class='footer'><p>{content}</p></div>",
    "image": lambda content: f'<div class="image"><img src="{content}" alt="Image"></div>',
    "button": lambda content: f'<div class="button"><a href="{content[1]}" style="color: white; text-decoration: none;" target="_blank">{content[0]}</a></div>' if isinstance(content, tuple) else "",
    "table": lambda content: generate_table_html(content) if isinstance(content, str) else "",
    "paragraph": lambda content: f"<p>{content}</p>",
    "list": lambda content: generate_list_html(content) if isinstance(content, str) else "",
    "link": lambda content: f'<a href="{content}" target="_blank">{content}</a>',
    "div": lambda content: f"<div>{content}</div>",
    "span": lambda content: f"<span>{content}</span>",
    "section": lambda content: f"<section>{content}</section>",
    "article": lambda content: f"<article>{content}</article>",
    "nav": lambda content: f"<nav>{content}</nav>",
    "aside": lambda content: f"<aside>{content}</aside>"
}

# Define the LangChain chain
class TextToHTMLChain(LLMChain):
    def __init__(self, llm, prompt_template):
        super().__init__(llm=llm, prompt=prompt_template, output_key="text")

    def _call(self, inputs):
        prompt = inputs['prompt']
        section_type, content = self.parse_prompt(prompt)
        if section_type == "modify":
            command, target, value = content
            return {"text": self.modify_html_section(command, target, value)}
        elif section_type:
            return {"text": self.generate_html_section(section_type, content)}
        else:
            return {"text": f"<p>{prompt}</p>"}

    def parse_prompt(self, prompt):
        prompt = prompt.lower()

        # Regular expressions for different patterns
        header_patterns = [
            r'header\s*:\s*(.*)',
            r'i want the header to say\s*(.*)',
            r'make header showing\s*(.*)',
            r'create a header that says\s*(.*)',
            r'set the header to\s*(.*)'
        ]

        # Check for header patterns
        for pattern in header_patterns:
            match = re.match(pattern, prompt)
            if match:
                content = match.group(1).strip()
                return "header", content

        # Pattern for changing color
        if "change the color of the" in prompt:
            parts = prompt.split("change the color of the")
            if len(parts) > 1:
                target_and_color = parts[-1].strip().split("to")
                if len(target_and_color) == 2:
                    target = target_and_color[0].strip()
                    color = target_and_color[1].strip()
                    return "modify", ("change color", target, color)

        # Patterns for table creation in natural language
        table_patterns = [
            r'create a table with columns (.*) and rows (.*)',
            r'make a table where the headers are (.*) and the rows are (.*)',
            r'generate a table having columns (.*) and including rows (.*)',
            r'table:\s*(.*)'
        ]

        for pattern in table_patterns:
            match = re.match(pattern, prompt)
            if match:
                columns = match.group(1).strip()
                rows = match.group(2).strip() if len(match.groups()) > 1 else ""
                table_content = f"{columns}; {rows}"
                return "table", table_content

        # Pattern for button creation
        button_pattern = r'create a button with text (.*) that links to (.*)'
        match = re.match(button_pattern, prompt)
        if match:
            text = match.group(1).strip()
            link = match.group(2).strip()
            return "button", (text, link)

        # Generic pattern for other HTML elements
        generic_pattern = r'(paragraph|list|link|div|span|section|article|nav|aside)\s*:\s*(.*)'
        match = re.match(generic_pattern, prompt)
        if match:
            section_type = match.group(1).strip()
            content = match.group(2).strip()
            return section_type, content

        return None, None

    def generate_html_section(self, section_type, content):
        global sections
        if section_type in html_templates:
            html = html_templates[section_type](content)
            sections.append((section_type, html))
            self.update_email_template()
            return html
        else:
            return f"<div>{content}</div>"

    def modify_html_section(self, command, target, value):
        global sections

        modified_sections = []
        for section_type, section_html in sections:
            if target in section_html:
                if command == "change color":
                    if target == "header":
                        modified_section_html = re.sub(r'style="[^"]*"', '', section_html)
                        modified_section_html = modified_section_html.replace('<div', f'<div style="background-color:{value};"', 1)
                    elif target == "table":
                        modified_section_html = re.sub(r'style="[^"]*"', '', section_html)
                        modified_section_html = modified_section_html.replace('<table', f'<table style="background-color:{value};"', 1)
                    elif target == "paragraph":
                        modified_section_html = re.sub(r'style="[^"]*"', '', section_html)
                        modified_section_html = section_html.replace('<p', f'<p style="color:{value};"', 1)
                    elif target == "list":
                        modified_section_html = re.sub(r'style="[^"]*"', '', section_html)
                        modified_section_html = section_html.replace('<ul', f'<ul style="color:{value};"', 1)
                    elif target == "link":
                        modified_section_html = re.sub(r'style="[^"]*"', '', section_html)
                        modified_section_html = section_html.replace('<a', f'<a style="color:{value};"', 1)
                    modified_sections.append((section_type, modified_section_html))
                else:
                    modified_sections.append((section_type, section_html))
            else:
                modified_sections.append((section_type, section_html))
        
        sections = modified_sections
        self.update_email_template()
        return "".join(html for _, html in sections)

    def update_email_template(self):
        global email_template
        email_template = "".join(html for _, html in sections)

def generate_table_html(content):
    rows = content.split(";")
    headers = rows[0].split(", ")
    table_html = "<table class='dynamic-table'><tr>" + "".join([f"<th>{header}</th>" for header in headers]) + "</tr>"
    for row in rows[1:]:
        cells = row.split(", ")
        table_html += "<tr>" + "".join([f"<td>{cell}</td>" for cell in cells]) + "</tr>"
    table_html += "</table>"
    return table_html

def generate_list_html(content):
    items = content.split("; ")
    list_html = "<ul>" + "".join([f"<li>{item}</li>" for item in items]) + "</ul>"
    return list_html

# Create an instance of the chain
llm = OpenAI(model="gpt-4o", api_key=openai.api_key)
text_to_html_chain = TextToHTMLChain(llm=llm, prompt_template=prompt_template)

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
        result = text_to_html_chain.invoke({"prompt": prompt})
        email_template = "".join(html for _, html in sections)  # Update the email template from sections
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify(template=email_template)

@app.route('/reset-template', methods=['POST'])
def reset_template():
    global email_template, history, sections
    history.append(email_template)
    email_template = ""
    sections = []
    return jsonify(template=email_template)

@app.route('/undo', methods=['POST'])
def undo():
    global email_template, history, sections
    if history:
        email_template = history.pop()
        sections = [(m.group(1), m.group(0)) for m in re.finditer(r'(<(div|table|p|ul|a|span|section|article|nav|aside) class=\'(header|footer|image|button|dynamic-table|paragraph|list|link)\'.*?</\2>)', email_template, re.DOTALL)]
    return jsonify(template=email_template)

if __name__ == '__main__':
    app.run(debug=True)
