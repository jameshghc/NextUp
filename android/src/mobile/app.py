"""Next Up on Android: the app's own server, shown full-screen.

Everything the desktop app is, minus its window: nextup.py runs its HTTP
server on a thread inside this app, and a WebView shows the page. Its data
— library, settings, posters — goes in this app's private data folder,
never beside the code, which Android replaces whenever the app updates.
"""
import os
import traceback

import toga


class NextUp(toga.App):
    def startup(self):
        self.main_window = toga.MainWindow(title=self.formal_name)
        try:
            data = str(self.paths.data)
            os.makedirs(data, exist_ok=True)
            # Read by nextup.py as it's imported, so it has to be set first.
            os.environ["NEXTUP_HOME"] = data
            import nextup
            port = nextup.serve_in_thread()
            self.main_window.content = toga.WebView(
                url="http://127.0.0.1:%d/" % port, style=toga.style.Pack(flex=1))
        except Exception:
            # A blank white screen says nothing. The reason, on screen, says
            # what to fix.
            self.main_window.content = toga.Label(
                "Next Up couldn't start:\n\n" + traceback.format_exc())
        self.main_window.show()


def main():
    return NextUp()
