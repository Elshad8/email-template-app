import openai
from bs4 import BeautifulSoup
import logging
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
openai.api_key = os.getenv('API_KEY')

async def generate_html(prompt):
    try:
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that generates clean, well-structured HTML code based on user instructions."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000
        )
        html_content = response['choices'][0]['message']['content']
        
        # Validate and prettify HTML
        soup = BeautifulSoup(html_content, 'html.parser')

        # Ensure there is a body element
        if not soup.body:
            body_tag = soup.new_tag('body')
            soup.append(body_tag)
        
        # Add responsive CSS
        style_tag = soup.new_tag('style')
        style_tag.string = """
            .generated-content {
                max-width: 100%;
                width: 100%;
                display: block;
                margin: 0 auto;
            }
            .generated-content img {
                max-width: 100%;
                height: auto;
            }
        """
        if soup.head:
            soup.head.append(style_tag)
        else:
            head_tag = soup.new_tag('head')
            head_tag.append(style_tag)
            soup.insert(0, head_tag)
        
        # Wrap content in a div with the class generated-content
        if soup.body:
            wrapper = soup.new_tag('div', **{'class': 'generated-content'})
            for element in soup.body.contents:
                wrapper.append(element.extract())
            soup.body.append(wrapper)
        
        pretty_html = soup.prettify()
        
        return pretty_html
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise

async def apply_html_changes(html_content, change_instruction):
    try:
        # Construct the prompt for making changes
        prompt = f"Here is the HTML content:\n\n{html_content}\n\nPlease make the following change: {change_instruction}"

        # Request the modification
        response = await openai.ChatCompletion.acreate(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an assistant that modifies HTML code based on user instructions."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1000
        )
        modified_html = response['choices'][0]['message']['content']
        
        # Validate and prettify HTML
        soup = BeautifulSoup(modified_html, 'html.parser')

        # Ensure there is a body element
        if not soup.body:
            body_tag = soup.new_tag('body')
            soup.append(body_tag)

        # Add responsive CSS
        style_tag = soup.new_tag('style')
        style_tag.string = """
            .generated-content {
                max-width: 100%;
                width: 100%;
                display: block;
                margin: 0 auto;
            }
            .generated-content img {
                max-width: 100%;
                height: auto;
            }
        """
        if soup.head:
            soup.head.append(style_tag)
        else:
            head_tag = soup.new_tag('head')
            head_tag.append(style_tag)
            soup.insert(0, head_tag)
        
        # Wrap content in a div with the class generated-content
        if soup.body:
            wrapper = soup.new_tag('div', **{'class': 'generated-content'})
            for element in soup.body.contents:
                wrapper.append(element.extract())
            soup.body.append(wrapper)
        
        pretty_html = soup.prettify()
        
        return pretty_html
    except openai.error.OpenAIError as e:
        logging.error(f"OpenAI API error: {e}")
        raise
