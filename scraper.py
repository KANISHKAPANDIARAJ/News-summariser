from newspaper import Article

def scrape_article(url):
    try:
        article = Article(url)
        article.download()
        article.parse()

        print("\n✅ Title:", article.title)
        print("\n📄 First 500 Characters of the Article:\n", article.text[:500])
        return article.title, article.text
    except Exception as e:
        print("\n❌ Error:", e)
        return None, None

if __name__ == "__main__":
    url = input("🔗 Enter a valid article URL: ").strip()
    if url.startswith("http"):
        title, text = scrape_article(url)
        if title and text:
            print("\n✅ Successfully Scraped!")
        else:
            print("\n❌ Failed to fetch article. Try another link.")
    else:
        print("\n❌ Invalid URL! Please enter a proper URL starting with 'http'.")
