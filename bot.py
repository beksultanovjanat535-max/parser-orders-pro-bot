import telebot, requests, re, warnings, os, threading
from bs4 import BeautifulSoup
from bs4 import XMLParsedAsHTMLWarning
from flask import Flask

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ==== НАСТРОЙКИ ====
TOKEN = os.environ.get("TELEGRAM_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ==== FLASK (чтобы Render не усыплял) ====
@app.route("/")
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# ==== ПАРСЕР ====
def get_orders(keyword):
    url = "https://www.fl.ru/rss/all.xml"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers, timeout=15)
    soup = BeautifulSoup(r.content, "lxml")
    items = soup.find_all("item")
    found = []
    kw = keyword.lower()
    for item in items:
        t = item.find("title")
        if not t: continue
        title = re.sub(r'<!\[CDATA\[|\]\]>', '', t.text).strip()
        if kw not in title.lower(): continue
        link = ""
        if item.find("link") and item.find("link").text.strip():
            link = item.find("link").text.strip()
        elif item.find("guid"):
            link = item.find("guid").text.strip()
        found.append({"title": title, "link": link})
    return found

# ==== КОМАНДЫ БОТА ====
@bot.message_handler(commands=['start'])
def start(m):
    bot.send_message(m.chat.id, "Привет! Ищу заказы на FL.ru.\n\nНапиши слово: парсинг, python, бот")

@bot.message_handler(content_types=['text'])
def search(m):
    kw = m.text.strip()
    if len(kw) < 2:
        bot.send_message(m.chat.id, "Слишком короткое слово")
        return
    bot.send_message(m.chat.id, f"Ищу: {kw}...")
    try:
        orders = get_orders(kw)
    except Exception as e:
        bot.send_message(m.chat.id, f"Ошибка: {e}")
        return
    if not orders:
        bot.send_message(m.chat.id, f"По слову {kw} ничего нет")
        return
    bot.send_message(m.chat.id, f"Найдено: {len(orders)}")
    for o in orders[:5]:
        bot.send_message(m.chat.id, f"{o['title']}\n\n{o['link']}", disable_web_page_preview=True)

# ==== ЗАПУСК ====
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot started!")
    bot.polling(none_stop=True)
