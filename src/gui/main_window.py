"""Ventana raíz y menú principal"""
import tkinter as tk
from tkinter import Menu
from spotipy import Spotify

from .playlists import (
    ventana_vaciar_playlists,
    ventana_eliminar_playlists,
    ventana_ver_playlists,
    ventana_crear_playlist,
)
from .podcasts import ventana_sincronizar_podcasts_data
from .artist_manager import VentanaGestorAutomatico
from .artistapy import ventana_artistapy
from .search_advanced import ventana_busqueda_avanzada
from .top_tracks import ventana_top_tracks

def build_main_window(sp: Spotify) -> tk.Tk:
    root = tk.Tk()
    root.title("Gestor Spotify (Modular)")
    root.geometry("840x620")

    menu_bar = Menu(root)
    root.config(menu=menu_bar)

    # --- PLAYLISTS ---
    menu_playlists = Menu(menu_bar, tearoff=0)
    menu_playlists.add_command(
        label="Vaciar Playlists",
        command=lambda: ventana_vaciar_playlists(sp, root)
    )
    menu_playlists.add_command(
        label="Eliminar Playlists",
        command=lambda: ventana_eliminar_playlists(sp, root)
    )
    menu_playlists.add_command(
        label="Ver Playlists",
        command=lambda: ventana_ver_playlists(sp, root)
    )
    menu_playlists.add_command(
        label="Crear Playlist",
        command=lambda: ventana_crear_playlist(sp, root)
    )
    menu_bar.add_cascade(
        label="Playlists",
        menu=menu_playlists
    )

    # --- PODCASTS ---
    menu_podcasts = Menu(menu_bar, tearoff=0)
    menu_podcasts.add_command(
        label="Sincronizar Podcasts (data)",
        command=lambda: ventana_sincronizar_podcasts_data(sp, root)
    )
    menu_bar.add_cascade(
        label="Podcasts",
        menu=menu_podcasts
    )

    # --- ARTISTA AUTO ---
    menu_gestor = Menu(menu_bar, tearoff=0)
    menu_gestor.add_command(
        label="Gestor Automático de Artistas",
        command=lambda: VentanaGestorAutomatico(root, sp)
    )
    menu_bar.add_cascade(
        label="Gestor Automático",
        menu=menu_gestor
    )

    # --- RECOMENDACIONES ---
    menu_reco = Menu(menu_bar, tearoff=0)
    menu_reco.add_command(
        label="#Artistapy",
        command=lambda: ventana_artistapy(sp, root)
    )
    menu_bar.add_cascade(
        label="Recomendaciones",
        menu=menu_reco
    )

    # --- BÚSQUEDA LIBRE ---
    menu_busqueda = Menu(menu_bar, tearoff=0)
    menu_busqueda.add_command(
        label="Por Frase Libre",
        command=lambda: ventana_busqueda_avanzada(sp, root)
    )
    menu_bar.add_cascade(
        label="Buscar Canciones",
        menu=menu_busqueda
    )

    # --- TOP TRACKS ---
    menu_bar.add_command(
        label="Top Tracks Artista",
        command=lambda: ventana_top_tracks(sp, root)
    )

    # --- Salir ---
    menu_bar.add_command(
        label="Salir",
        command=root.destroy
    )

    # Mensaje de bienvenida
    tk.Label(
        root,
        text="¡Bienvenido al Gestor Modular de Spotify!",
        font=("Arial", 14)
    ).pack(pady=20)

    # Barra de estado
    status = tk.Label(
        root,
        text="Listo",
        bd=1,
        relief=tk.SUNKEN,
        anchor=tk.W
    )
    status.pack(side=tk.BOTTOM, fill=tk.X)

    return root
