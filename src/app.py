"""
Lanza la aplicación completa
"""
from .auth import get_spotify_client
from .gui.main_window import build_main_window

def main() -> None:
    sp = get_spotify_client()
    root = build_main_window(sp)
    root.mainloop()

if __name__ == "__main__":
    main()
