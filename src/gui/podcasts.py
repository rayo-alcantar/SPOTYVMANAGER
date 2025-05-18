# src/gui/podcasts.py
"""
Ventana para sincronizar podcasts con sus playlists (data_podcasts) en wxPython.
"""

import wx
from spotipy import Spotify
from ..utils.spotify_utils import (
	get_podcast_episodes,
	get_playlist_items,
	add_episodes_to_playlist,
)

# Lista de pares {podcast, playlist}
data_podcasts = [
	{"podcast": "0u8dE1kc9CkFn8bONEq0hE", "playlist": "1MreMp1Qm4gyKZa5B2HZun"},
	# ... completa con tu lista original ...
]

class VentanaSincronizarPodcastsData(wx.Frame):
	"""
	Ventana de sincronización de episodios de podcasts con sus playlists, mostrando progreso y log de acciones.
	"""
	def __init__(self, parent: wx.Window, sp: Spotify):
		super().__init__(parent, title="Sincronizar Podcasts (data_podcasts)", size=(520, 300))
		self.sp = sp

		panel = wx.Panel(self)
		sizer = wx.BoxSizer(wx.VERTICAL)
		panel.SetSizer(sizer)

		# Etiqueta de estado general
		label = wx.StaticText(panel, label="Sincronizando podcasts con sus playlists…")
		label.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
		sizer.Add(label, 0, wx.TOP | wx.LEFT | wx.RIGHT, 8)

		# Barra de progreso
		self.prog = wx.Gauge(panel, range=len(data_podcasts), style=wx.GA_HORIZONTAL)
		self.prog.SetMinSize((460, 30))
		sizer.Add(self.prog, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)

		# Etiqueta de estado de elemento actual
		self.lbl_estado = wx.StaticText(panel, label="Esperando…")
		sizer.Add(self.lbl_estado, 0, wx.ALL | wx.EXPAND, 6)

		# Área de log
		self.txt_log = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP, size=(480, 120))
		self.txt_log.SetMinSize((480, 100))
		self.txt_log.SetName("Log de sincronización de podcasts")
		sizer.Add(self.txt_log, 1, wx.ALL | wx.EXPAND, 10)

		# Botón para iniciar sincronización
		btn = wx.Button(panel, label="Iniciar sincronización")
		btn.Bind(wx.EVT_BUTTON, self.sincronizar)
		btn.SetMinSize((200, 44))
		sizer.Add(btn, 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 8)

		panel.Layout()
		self.Centre()
		self.Show()

	def log(self, msg: str):
		"""
		Agrega una línea al área de log y asegura el scroll automático.
		"""
		self.txt_log.AppendText(msg + "\n")
		self.txt_log.ShowPosition(self.txt_log.GetLastPosition())
		wx.YieldIfNeeded()

	def sincronizar(self, _evt):
		"""
		Recorre todos los pares podcast-playlist y sincroniza episodios, mostrando el progreso y mensajes.
		"""
		total = len(data_podcasts)
		self.prog.SetValue(0)

		for idx, pair in enumerate(data_podcasts, start=1):
			pod_id, pl_id = pair["podcast"], pair["playlist"]
			try:
				podcast_name = self.sp.show(pod_id, market="US")["name"]
			except Exception:
				podcast_name = f"Podcast {pod_id[:8]}…"
			try:
				playlist_name = self.sp.playlist(pl_id, fields="name")["name"]
			except Exception:
				playlist_name = f"Playlist {pl_id[:8]}…"

			self.lbl_estado.SetLabel(f"{idx}/{total}  {podcast_name} → {playlist_name}")
			wx.YieldIfNeeded()

			eps = get_podcast_episodes(self.sp, pod_id)
			if not eps:
				self.log(f"❌ {podcast_name}: sin episodios o error.")
				self.prog.SetValue(idx)
				continue

			antes = set(get_playlist_items(self.sp, pl_id))
			add_episodes_to_playlist(self.sp, pl_id, eps)
			despues = set(get_playlist_items(self.sp, pl_id))
			nuevos = len(despues) - len(antes)
			if nuevos:
				self.log(f"✅ {podcast_name}: {nuevos} nuevos → {playlist_name}")
			else:
				self.log(f"• {podcast_name}: 0 nuevos")
			self.prog.SetValue(idx)

		self.lbl_estado.SetLabel("¡Sincronización completa!")
		wx.MessageBox("Todos los podcasts han sido sincronizados.", "Terminado", wx.OK | wx.ICON_INFORMATION)

def ventana_sincronizar_podcasts_data(sp: Spotify, parent: wx.Window):
	"""
	Invoca la ventana de sincronización de podcasts.
	"""
	VentanaSincronizarPodcastsData(parent, sp)