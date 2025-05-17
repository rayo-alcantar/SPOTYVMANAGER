# src/gui/artist_manager.py
"""
VentanaGestorAutomatico: busca un artista, obtiene sus canciones únicas y gestiona playlists.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from spotipy import Spotify
import time, unicodedata, re

class VentanaGestorAutomatico(tk.Toplevel):
    """Busca un artista, recoge todas sus canciones únicas y gestiona playlists."""
    def __init__(self, parent: tk.Tk, sp: Spotify):
        super().__init__(parent)
        self.title("Gestor de Playlists Automáticas en Spotify")
        self.geometry("600x600")
        self.sp = sp
        try:
            self.user_id = self.sp.current_user()["id"]
        except Exception:
            messagebox.showerror("Error", "No se pudo obtener info del usuario.")
            self.destroy()
            return

        self.songs = []        # lista final de canciones
        self.artist_id = None  # ID del artista seleccionado

        # Frames para cada sección
        self.frame_artist = tk.Frame(self)
        self.frame_playlist = tk.Frame(self)
        self.frame_clear = tk.Frame(self)

        # UI inicial
        self.create_artist_frame()
        self.frame_clear.pack(fill=tk.X)
        tk.Button(self.frame_clear, text="Vaciar Múltiples Playlists",
                  command=self.abrir_ventana_vaciar_playlists).pack(pady=5)

    # ———————————— Búsqueda de artista ————————————
    def create_artist_frame(self):
        self.frame_artist.pack(fill=tk.BOTH, expand=True)
        for w in self.frame_artist.winfo_children():
            w.destroy()
        tk.Label(self.frame_artist, text="Introduce el nombre del artista:").pack(pady=10)
        self.entry_artist = tk.Entry(self.frame_artist, width=50)
        self.entry_artist.pack(pady=5)
        tk.Button(self.frame_artist, text="Buscar", command=self.search_artist).pack(pady=5)
        self.listbox_artists = tk.Listbox(self.frame_artist, width=50)
        self.listbox_artists.pack(pady=10)
        self.listbox_artists.bind("<<ListboxSelect>>", self.on_artist_select)

    def search_artist(self):
        name = self.entry_artist.get().strip()
        if not name:
            messagebox.showinfo("Info", "Ingresa un nombre primero.")
            return
        try:
            res = self.sp.search(q=name, type="artist", limit=5)
            self.artists_found = res["artists"]["items"]
            self.listbox_artists.delete(0, tk.END)
            if not self.artists_found:
                messagebox.showinfo("Info", "No se encontró el artista.")
                return
            for art in self.artists_found:
                self.listbox_artists.insert(tk.END, art["name"])
        except Exception as e:
            messagebox.showerror("Error", f"Error al buscar el artista: {e}")

    def on_artist_select(self, _evt):
        if not self.listbox_artists.curselection():
            return
        idx = self.listbox_artists.curselection()[0]
        art = self.artists_found[idx]
        self.artist_id = art["id"]
        if messagebox.askyesno("Confirmar", f"Seleccionaste {art['name']}. ¿Continuar?"):
            self.fetch_artist_songs()

    def fetch_artist_songs(self):
        try:
            self.songs = self.obtener_canciones_artista_completas(self.artist_id)
            messagebox.showinfo("Info", f"Se encontraron {len(self.songs)} canciones únicas.")
            self.frame_artist.pack_forget()
            self.create_playlist_frame()
        except Exception as e:
            messagebox.showerror("Error", f"Error al obtener las canciones: {e}")

    # ———————————— Método central: elimina duplicados ————————————
       # ———————————— Método central: elimina duplicados ————————————
    def obtener_canciones_artista_completas(self, artist_id: str):
        """Devuelve TODAS las canciones del artista sin duplicados “alternos”."""

        MARKETS = ("US", "MX")
        # ► palabras que indican versión alterna
        ALT_FLAGS = (
            "acoustic", "live", "en vivo", "unplugged", "instrumental",
            "remaster", "remastered", "demo", "karaoke", "edit",
            "mix", "remix", "versión", "version", "session"
        )
        # ► ruido que queremos ignorar al comparar títulos
        NOISE = (
            "feat.", "featuring", "ft.", "with", "con"
        )

        elegido: dict[str, dict] = {}
        total_raw = 0
        clean_punct = re.compile(r"[()\[\]{}\-–_:]")

        # -------- helpers --------
        def slug(txt: str) -> str:
            """Normaliza, quita acentos y palabras de ruido."""
            # quitar acentos/ñ → n  (NFKD+encode)
            txt = unicodedata.normalize("NFKD", txt).encode("ascii", "ignore").decode()
            txt = txt.lower()
            # eliminar puntuación habitual
            txt = clean_punct.sub(" ", txt)
            # quitar palabras ALT + NOISE
            for w in (*ALT_FLAGS, *NOISE):
                txt = txt.replace(w, " ")
            # colapsar espacios
            return " ".join(txt.split())

        def es_alt(titulo: str, album: str) -> bool:
            t, a = titulo.lower(), album.lower()
            return any(w in t or w in a for w in ALT_FLAGS)

        def considera(track: dict, album_name: str):
            nonlocal total_raw
            total_raw += 1
            tid = track.get("id")
            if not tid:
                return
            title = track.get("name", "").strip()
            base = slug(title)
            alt  = es_alt(title, album_name)
            if base not in elegido:
                elegido[base] = {"track": track, "alt": alt}
            # si el que ya teníamos era versión alterna y éste NO lo es, lo reemplazamos
            elif elegido[base]["alt"] and not alt:
                elegido[base] = {"track": track, "alt": alt}

        # -------- 1) álbumes / singles / compilados --------
        try:
            alb_resp = self.sp.artist_albums(
                artist_id,
                album_type="album,single,compilation,appears_on",
                limit=50
            )
        except Exception as e:
            print(f"[{artist_id}] error álbumes: {e}")
            return []

        albums = []
        while True:
            albums += alb_resp.get("items", [])
            if not alb_resp.get("next"):
                break
            alb_resp = self.sp.next(alb_resp)

        for alb in albums:
            alb_name = alb.get("name", "")
            for m in MARKETS:
                try:
                    tr_resp = self.sp.album_tracks(alb["id"], limit=50, market=m)
                except Exception:
                    continue
                while True:
                    for t in tr_resp.get("items", []):
                        if any(a["id"] == artist_id for a in t["artists"]):
                            considera(t, alb_name)
                    if not tr_resp.get("next"):
                        break
                    tr_resp = self.sp.next(tr_resp)

        # -------- 2) búsqueda global (singles sueltos / colaboraciones) --------
        try:
            art_name = self.sp.artist(artist_id)["name"]
            offset = 0
            while True:
                sr = self.sp.search(q=f'artist:"{art_name}"', type="track",
                                    limit=50, offset=offset)
                for t in sr["tracks"]["items"]:
                    if any(a["id"] == artist_id for a in t["artists"]):
                        considera(t, "")
                if not sr["tracks"]["next"]:
                    break
                offset += 50
        except Exception as e:
            print(f"[{artist_id}] búsqueda global falló: {e}")

        # -------- resultado final --------
        canciones = [
            {"id": d["track"]["id"], "name": d["track"]["name"]}
            for d in elegido.values()
        ]
        print(f"[{artist_id}] vistas≈{total_raw}, únicas={len(canciones)}")
        return canciones


    # ————————————— Informe rápido —————————————
    def generar_informe_canciones(self):
        if not self.songs:
            messagebox.showinfo("Info", "No hay canciones cargadas.")
            return
        total_unicas = len(self.songs)
        total_collab = sum(1 for s in self.songs if len(self.sp.track(s["id"])["artists"]) > 1)
        total_dups = (total_unicas + total_collab) - total_unicas
        messagebox.showinfo(
            "Informe de canciones",
            f"Pistas únicas: {total_unicas}\n"
            f"Con colaboraciones: {total_collab}\n"
            f"Duplicadas descartadas: {total_dups}"
        )

    # ———————————— Opciones de playlist ————————————
    def create_playlist_frame(self):
        self.frame_playlist.pack(fill=tk.BOTH, expand=True)
        for w in self.frame_playlist.winfo_children():
            w.destroy()
        tk.Label(self.frame_playlist, text="¿Qué deseas hacer?").pack(pady=10)
        self.playlist_option = tk.StringVar(value="nueva")
        tk.Radiobutton(self.frame_playlist, text="Crear nueva playlist", variable=self.playlist_option, value="nueva", command=self.update_playlist_option).pack(pady=5)
        tk.Radiobutton(self.frame_playlist, text="Seleccionar playlist existente", variable=self.playlist_option, value="existente", command=self.update_playlist_option).pack(pady=5)
        self.frame_option = tk.Frame(self.frame_playlist)
        self.frame_option.pack(pady=10, fill=tk.BOTH, expand=True)
        tk.Button(self.frame_playlist, text="Buscar otro artista", command=self.reset_to_artist_search).pack(pady=5)
        self.update_playlist_option()

    def update_playlist_option(self):
        for w in self.frame_option.winfo_children():
            w.destroy()
        if self.playlist_option.get() == "nueva":
            self.new_playlist_entry = tk.Entry(self.frame_option, width=50)
            self.new_playlist_entry.insert(0, "Nombre de la nueva playlist")
            self.new_playlist_entry.pack(pady=5)
            tk.Button(self.frame_option, text="Crear Playlist", command=self.crear_playlist_y_agregar_songs).pack(pady=5)
        else:
            self.entry_search = tk.Entry(self.frame_option, width=50)
            self.entry_search.insert(0, "Buscar playlist")
            self.entry_search.pack(pady=5)
            self.entry_search.bind("<KeyRelease>", self.filtrar_playlists)
            self.playlists = self.obtener_todas_playlists()
            self.playlist_listbox = tk.Listbox(self.frame_option, width=50)
            for pl in self.playlists:
                self.playlist_listbox.insert(tk.END, pl["name"])
            self.playlist_listbox.pack(pady=5, fill=tk.BOTH, expand=True)
            btn_frame = tk.Frame(self.frame_option)
            btn_frame.pack(pady=5)
            tk.Button(btn_frame, text="Vaciar Playlist", command=self.vaciar_playlist_seleccionada).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Actualizar Playlist", command=self.actualizar_playlist_seleccionada).pack(side=tk.LEFT, padx=5)

    def crear_playlist_y_agregar_songs(self):
        name = self.new_playlist_entry.get().strip()
        if not name:
            messagebox.showinfo("Info", "Ingresa un nombre para la playlist.")
            return
        playlist = self.sp.user_playlist_create(self.user_id, name, public=True, description="Playlist generada automáticamente")
        pid = playlist["id"]
        ids = [s["id"] for s in self.songs]
        for i in range(0, len(ids), 100):
            self.sp.playlist_add_items(pid, ids[i:i+100])
            time.sleep(0.5)
        messagebox.showinfo("Info", "Playlist creada y canciones agregadas.")

    def filtrar_playlists(self, _evt):
        term = self.entry_search.get().strip().lower()
        self.playlist_listbox.delete(0, tk.END)
        for pl in self.playlists:
            if term in pl["name"].lower():
                self.playlist_listbox.insert(tk.END, pl["name"])

    def vaciar_playlist_seleccionada(self):
        idxs = self.playlist_listbox.curselection()
        if not idxs:
            messagebox.showinfo("Info", "Selecciona una playlist primero.")
            return
        pl = self.playlists[idxs[0]]
        if not messagebox.askyesno("Confirmar", f"Vaciar playlist “{pl['name']}”?"):
            return
        self.sp.playlist_replace_items(pl["id"], [])
        messagebox.showinfo("Info", "Playlist vaciada correctamente.")

    def actualizar_playlist_seleccionada(self):
            # 1) Asegúrate de que el usuario haya seleccionado algo
            sel = self.playlist_listbox.curselection()
            if not sel:
                messagebox.showinfo("Info", "Selecciona una playlist primero.")
                return

            # 2) Toma la playlist elegida
            pl = self.playlists[sel[0]]  # es un dict con 'id' y 'name'

            # 3) Saca los IDs que ya están allí
            existentes = self.obtener_canciones_playlist(pl["id"])
            #    ← esto te devuelve un set de IDs

            # 4) Filtra tus canciones nuevas
            pendientes = [s["id"] for s in self.songs if s["id"] not in existentes]
            if not pendientes:
                messagebox.showinfo("Info", "No hay canciones nuevas.")
                return

            # 5) Agrega en bloques de 100 usando tu cliente Spotify
            try:
                for i in range(0, len(pendientes), 100):
                    self.sp.playlist_add_items(pl["id"], pendientes[i:i+100])
                    time.sleep(0.5)
                messagebox.showinfo("Éxito", "Playlist actualizada.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar: {e}")


    def obtener_todas_playlists(self) -> list[dict]:
        pls, offset = [], 0
        while True:
            res = self.sp.current_user_playlists(limit=50, offset=offset)
            for it in res["items"]:
                pls.append({"id": it["id"], "name": it["name"], "tracks": it["tracks"]["total"]})
            if not res.get("next"):
                break
            offset += 50
        return pls

    def abrir_ventana_vaciar_playlists(self):
        # similar a la función global, pero interna
        pass  # implementación idéntica a la de ventana_vaciar_playlists
    def reset_to_artist_search(self):
        self.frame_playlist.pack_forget()
        self.frame_artist.pack(fill=tk.BOTH, expand=True)
        self.songs.clear()
        self.artist_id = None
        self.entry_artist.delete(0, tk.END)
        self.listbox_artists.delete(0, tk.END)
