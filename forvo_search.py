from aqt import mw, gui_hooks
from aqt.webview import AnkiWebView, AnkiWebPage
from aqt.qt import QAction, QKeySequence, QUrl, QMainWindow, QWebEnginePage, QVBoxLayout, QWebEngineView, QByteArray, QMimeData
from aqt.utils import showWarning
import os
import base64
import json
import requests
import platform
addon_name = mw.addonManager.addonFromModule(__name__)

class CustomView(AnkiWebView):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Forvo Search")
        self.config = mw.addonManager.getConfig(__name__)
        self.resize(self.config["width"], self.config["height"])
        self.set_open_links_externally(False)
        self.set_bridge_command(self.bridge_command, self)

    def prepare_view(self):
        body = open_file('web', 'index.html')
        self.stdHtml(body, None, None, "", self)
        self.show()
    
    #save the window's size to config when it is resized
    def resizeEvent(self, event):
        self.config["width"] = self.width()
        self.config["height"] = self.height()
        mw.addonManager.writeConfig(__name__, self.config)
        super().resizeEvent(event)

    def create_pronunciation_rows(self, data):
        #invoke function in web/script.js that we appended into the html in the hook
        self.evalWithCallback(f'createRow({data});', lambda val: self.activateWindow())

    def bridge_command(self, url):
        print(url)
        #when the copy button is clicked in webview, we receive the url here of the corresponding row
        #url - [i, url], i is the index the row that copy was clicked from
        row, url = json.loads(url)
        
        #headers to prevent anti-scraping detection
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(url, headers=headers)
    
        if response.status_code == 200:
            media_folder = mw.col.media.dir()
            file_name = url.split('/')[-1]
            file_path = os.path.join(media_folder, file_name)
            with open(file_path, 'wb') as file:
                file.write(response.content)

            mime_data = QMimeData()

            #filepath uri differs between windows and unix
            file_uri_base = "file:///"
            if platform.system() != 'Windows':
                file_uri_base = "file://"
            file_uri = file_uri_base + file_path

            mime_data.setData("text/uri-list", QByteArray(file_uri.encode()))

            #set the MIME data to the clipboard
            mw.app.clipboard().setMimeData(mime_data)
            print(f"MP3 from {url} copied to clipboard!")

            #update webview with success
            self.eval(f"downloadSuccess({row})")
        else:
            showWarning(f"Failed to download MP3. Status code: {response.status_code}")

class ForvoPage(QWebEnginePage):
    def __init__(self, word, *args):
        super().__init__()
        # self.set_open_links_externally(False)
        self.link_extractor_js = open_file('', 'linkExtractor.js')
        self.pronunciations = []
        self.load(QUrl(f"https://ja.forvo.com/word/{word}/#ja"))
        self.connection = self.loadFinished.connect(self.get_audio_links)

    def get_audio_links(self, success):
        if not success:
            mw.custom_view.stdHtml("Page not found")
            mw.custom_view.activateWindow()
        else:
            self.runJavaScript(self.link_extractor_js, self.decode_links)

    def decode_links(self, links):
        #links is a JSON.stringify'd array of arrays with a base url and base64 encoded string
        #[["https://audio12.forvo.com/audios/mp3/","'YS9rL2FrXzkxMTAxMjdfNzZfMTMyOTc5MF8xLm1wMw=='", "author"],...]
        #we return an empty array if we didn't find any pronunciations to scrape
        arr = json.loads(links)
        if len(arr) == 0:
            mw.custom_view.stdHtml('No pronunciations found')
            mw.custom_view.activateWindow()
            return
        
        self.pronunciations = []
        for i in arr:
            base_url = i[0]
            file_name = i[1]
            author = i[2]
            url = base_url + base64.b64decode(file_name).decode('utf-8')
            self.pronunciations.append([author, url])

        self.loadFinished.disconnect(self.connection)
        del mw.forvo_page
        mw.custom_view.create_pronunciation_rows(self.pronunciations)

def open_file(folder, filename):
    path = os.path.join(mw.addonManager.addonsFolder(), addon_name, folder, filename)
    with open(path, 'r') as script:
        return script.read()

def forvo_search():
    clipboard = mw.app.clipboard()
    word = clipboard.text().strip()
    #prevent accidental searches with long text
    if word and len(word) < 30:
        mw.forvo_page = ForvoPage(word)
        #keep using existing window if it's already open
        if not hasattr(mw, "custom_view"):
            mw.custom_view = CustomView()
        mw.custom_view.prepare_view()

def on_webview_will_set_content(web_content, context):
    #this function fires on every AnkiWebView, so filter those out
    if not isinstance(context, CustomView): 
        return
    #add our custom js and css into the html
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.css.append(f"/_addons/{addon_package}/web/style.css")
    web_content.js.append(f"/_addons/{addon_package}/web/script.js")

mw.addonManager.setWebExports(__name__, r"web.*")
shortcut = mw.addonManager.getConfig(__name__)["shortcut"]
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
action = QAction("Forvo Search", mw)
action.setShortcut(QKeySequence(shortcut))
action.triggered.connect(forvo_search)
mw.form.menuTools.addAction(action)