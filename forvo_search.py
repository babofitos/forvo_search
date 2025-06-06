from aqt import mw, gui_hooks
from aqt.webview import AnkiWebView, AnkiWebViewKind
from aqt.qt import QAction, QKeySequence, QUrl, QWebEnginePage, QByteArray, QMimeData, QShortcut, pyqtSignal
from aqt.utils import showWarning
import os
import base64
import json
import requests
import platform
addon_name = mw.addonManager.addonFromModule(__name__)

class CustomView(AnkiWebView):
    def __init__(self):
        super().__init__(parent=None, kind=AnkiWebViewKind.MAIN)
        self.setWindowTitle("Forvo Search")
        self.config = mw.addonManager.getConfig(__name__)
        self.resize(self.config["width"], self.config["height"])
        self.set_open_links_externally(False)
        self.set_bridge_command(self.bridge_command, self)
        add_shortcut_to_window(self)
        self.body = open_file('web', 'index.html')
        mw.forvo_page.word_changed.connect(self.update_word_in_ui)
        mw.forvo_page.pronunciations_ready.connect(self.create_pronunciation_rows)
        mw.forvo_page.no_page_found.connect(self.handle_no_page)
        mw.forvo_page.no_pronunciations_found.connect(self.handle_no_pronunciations)

    #save the window's size to config when it is resized
    def resizeEvent(self, event):
        self.config["width"] = self.width()
        self.config["height"] = self.height()
        mw.addonManager.writeConfig(__name__, self.config)
        super().resizeEvent(event)

    def closeEvent(self, event):
        #if a word is searched and then the window is closed, the word won't be searched again if the window is re-opened, so reset word
        mw.forvo_page.reset_word()
        super().closeEvent(event)

    def handle_no_page(self):
        self.eval("pageNotFound();")
        
    def handle_no_pronunciations(self):
        self.eval("noPronunciationsFound();")

    def open_empty_window(self):
        #view shown when window is not already open
        if self.isVisible():
            return
        
        self.prepare_view()
        self.show()
        self.activateWindow()

    def prepare_view(self):    
        """
        stdHtml will call gui_hooks.webview_will_set_content and append the css and js in the html.
        Anki will inject its default css initially because the last arg is True
        """
        self.stdHtml(self.body, None, None, "", self, True)
        
    
    def update_word_in_ui(self, word):
        self.activateWindow()
        self.stdHtml(self.body, None, None, "", self)
        self.evalWithCallback(f'fillWordInInput("{word}");showFetchForvoMessage("{word}");', lambda _: self.show())

    def create_pronunciation_rows(self, data):
        #invoke function in web/script.js that we appended into the html in the hook
        self.eval(f'createRow({data});')

    def bridge_command(self, pycmd_msg):
        """
        pycmd_msg is a stringified JSON object
        {   type: '[search|copy]',
            val: "word"|[index, "url"]
        }   
        """
        pycmd_msg = json.loads(pycmd_msg)

        if (pycmd_msg["type"] == 'search'):
            mw.forvo_page.search(pycmd_msg["val"])

        elif (pycmd_msg["type"] == 'copy'):
            #when the copy button is clicked in webview, we receive the url here of the corresponding row
            #url - [i, url], i is the index the row that copy was clicked from
            row, url = pycmd_msg["val"]
            
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
    pronunciations_ready = pyqtSignal(list)
    no_page_found = pyqtSignal()
    no_pronunciations_found = pyqtSignal()
    word_changed = pyqtSignal(str)

    def __init__(self, *args):
        super().__init__()
        self.link_extractor_js = open_file('', 'linkExtractor.js')
        self.word = ""
    
    def reset_word(self):
        self.word = ""

    def search(self, word):
        #don't need to search if current word already being shown
        if word == self.word:
            return
        
        self.word = word

        self.word_changed.emit(word)

        self.pronunciations = []
        self.load(QUrl(f"https://ja.forvo.com/word/{word}/#ja"))
        self.loadFinished.connect(self.get_audio_links)

    def search_from_clipboard(self):
        clipboard = mw.app.clipboard()
        word = clipboard.text().strip()
        #prevent accidental searches with long text
        if word and len(word) < 30:
            self.search(word)

    def get_audio_links(self, success):
        #disconnect the signal or subsequent searches will double function call each time
        self.loadFinished.disconnect(self.get_audio_links)

        if not success:
            self.no_page_found.emit()
        else:
            lang = mw.addonManager.getConfig(__name__)["lang"]
            #need to include the double quotes around the lang because the fn expects a string
            #effectively getUrls("ja")
            self.runJavaScript(self.link_extractor_js + '("' + f"{lang}" + '")', self.decode_links)
        
        #no longer need to be connected to Forvo, so simulate a disconnect by loading a blank page
        self.load(QUrl("about:blank"))

    def decode_links(self, links):
        #links is a JSON.stringify'd array of arrays with a base url and base64 encoded string
        #[["https://audio12.forvo.com/audios/mp3/","'YS9rL2FrXzkxMTAxMjdfNzZfMTMyOTc5MF8xLm1wMw=='", "author", "votes"],...]
        #we return an empty array if we didn't find any pronunciations to scrape
        arr = json.loads(links)
        if len(arr) == 0:
            self.no_pronunciations_found.emit()
            return
        
        self.pronunciations = []
        for i in arr:
            base_url = i[0]
            file_name = i[1]
            author = i[2]
            votes = i[3]
            url = base_url + base64.b64decode(file_name).decode('utf-8')
            self.pronunciations.append([author, url, votes])

        self.pronunciations_ready.emit(self.pronunciations)

def open_file(folder, filename):
    path = os.path.join(mw.addonManager.addonsFolder(), addon_name, folder, filename)
    with open(path, 'r') as script:
        return script.read()

def on_webview_will_set_content(web_content, context):
    #this function fires on every AnkiWebView, so filter those out
    if not isinstance(context, CustomView): 
        return
    #add our custom js and css into the html
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.css.append(f"/_addons/{addon_package}/web/style.css")
    web_content.js.append(f"/_addons/{addon_package}/web/script.js")



shortcut = mw.addonManager.getConfig(__name__)["shortcut"]

def add_shortcut_to_window(window):
    print('window', type(window))
    qshortcut = QShortcut(QKeySequence(shortcut), window)
    qshortcut.activated.connect(mw.forvo_page.search_from_clipboard)

mw.forvo_page = ForvoPage()

mw.addonManager.setWebExports(__name__, r"web.*")

gui_hooks.webview_will_set_content.append(on_webview_will_set_content)

mw.custom_view = CustomView()

fetch_action = QAction("Fetch Forvo Search", mw)
fetch_action.setShortcut(QKeySequence(shortcut))
mw.addAction(fetch_action)
fetch_action.triggered.connect(mw.forvo_page.search_from_clipboard)

open_action = QAction("Open Forvo Search", mw)
mw.addAction(open_action)
open_action.triggered.connect(mw.custom_view.open_empty_window)
mw.form.menuTools.addAction(open_action)

#fires on browser (not deck browser) as well
gui_hooks.editor_web_view_did_init.append(add_shortcut_to_window)
gui_hooks.previewer_did_init.append(add_shortcut_to_window)