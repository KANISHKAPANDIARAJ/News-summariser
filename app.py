from flask import Flask, render_template, request
from transformers import BartForConditionalGeneration, BartTokenizer
from newspaper import Article  
import torch

app = Flask(__name__)

# Load BART model and tokenizer
model_name = "facebook/bart-large-cnn"
model = BartForConditionalGeneration.from_pretrained(model_name)
tokenizer = BartTokenizer.from_pretrained(model_name)

def fetch_article_text(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception:
        return None

def summarize_text(text):
    if not text.strip():
        return "No valid text provided for summarization."

    inputs = tokenizer([text], max_length=1024, return_tensors="pt", truncation=True)
    with torch.no_grad():
        summary_ids = model.generate(inputs["input_ids"], num_beams=4, max_length=150, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

@app.route('/', methods=['GET', 'POST'])
def index():
    summary = None
    error = None

    if request.method == 'POST':
        input_type = request.form.get('input_type')
        if input_type == 'url':
            url = request.form.get('url')
            if url:
                article_text = fetch_article_text(url)
                if article_text:
                    summary = summarize_text(article_text)
                else:
                    error = "Failed to fetch article content. Please check the URL."
            else:
                error = "Please enter a valid URL."
        elif input_type == 'text':
            text = request.form.get('text')
            if text and text.strip():
                summary = summarize_text(text)
            else:
                error = "Please enter text to summarize."

    return render_template('index.html', summary=summary, error=error)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

