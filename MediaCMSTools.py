import re
import os
import io
import requests
import json
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import asksaveasfile
from PIL import ImageTk, Image
from util.mediacms import MediaCMS_API
from util.mediacms import MEDIACMS_VIDEO_REGEX
import util.youtube as yt

class MediaCMSTools:
  def __init__(self, root):
    self.initialize_mediacms_api()

    root.title("MediaCMS Tools")

    self.mainframe = ttk.Frame(root, padding="12 12 12 12")
    self.mainframe.grid(column=0, row=0, sticky=(N, W, E, S))

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    self.mediacms_video_url_label = ttk.Label(self.mainframe, text="MediaCMS Video Link")
    self.mediacms_video_url_label.grid(column=1, row=1, sticky=W)
    
    self.mediacms_video_url = StringVar()
    self.mediacms_video_url_entry = ttk.Entry(self.mainframe, width=60, textvariable=self.mediacms_video_url)
    self.mediacms_video_url_entry.grid(column=2, row=1, sticky=(W, E), padx=12)

    self.load_mediacms_video_url_button = ttk.Button(self.mainframe, text="Load", command=self.load_mediacms_video_url)
    self.load_mediacms_video_url_button.grid(column=3, row=1, sticky=W, padx=12)

    self.mediacms_video_thumbnail = ttk.Label(self.mainframe, padding="12 12 12 12")
    self.mediacms_video_thumbnail.grid(column=1, row=2, columnspan=2, sticky=(W,E))

    self.mediacms_video_info = ttk.Frame(self.mainframe, padding="12 12 12 12")
    self.mediacms_video_info.grid(column=3, row=2, sticky=(N, W, E, S))

    self.mediacms_video_title_label = ttk.Label(self.mediacms_video_info, text="Title:")
    self.mediacms_video_title_label.grid(column=1, row=1, sticky=(N, W, E))

    self.mediacms_video_title = StringVar()
    self.mediacms_video_title_entry = ttk.Entry(self.mediacms_video_info, width=30, textvariable=self.mediacms_video_title)
    self.mediacms_video_title_entry.grid(column=1, row=2, sticky=(N, W, E, S))

    self.mediacms_video_desc_label = ttk.Label(self.mediacms_video_info, text="Description:")
    self.mediacms_video_desc_label.grid(column=1, row=3, sticky=(N, W, E, S))

    self.mediacms_video_desc_entry = Text(self.mediacms_video_info, height=10, width=40)
    self.mediacms_video_desc_entry.grid(column=1, row=4, sticky=(W, E, S))

    self.mediacms_video_tags_label = ttk.Label(self.mediacms_video_info, text="Tags (comma separated):")
    self.mediacms_video_tags_label.grid(column=1, row=5, sticky=(N, W, E))

    self.mediacms_video_tags = StringVar()
    self.mediacms_video_tags_entry = ttk.Entry(self.mediacms_video_info, width=30, textvariable=self.mediacms_video_tags)
    self.mediacms_video_tags_entry.grid(column=1, row=6, sticky=(N, W, E, S))

    self.mediacms_video_actions = ttk.Frame(self.mainframe, padding="12 12 12 12")
    self.mediacms_video_actions.grid(column=3, row=3, sticky=(N, W, E, S))

    self.mediacms_video_download = ttk.Button(self.mediacms_video_actions, text="Download clip", command=self.download_mediacms_video)
    self.mediacms_video_download.grid(column=1, row=1, sticky=W)

    self.mediacms_video_upload_to_youtube = ttk.Button(self.mediacms_video_actions, text="Connect to YouTube", command=self.connect_to_youtube)
    self.mediacms_video_upload_to_youtube.grid(column=2, row=1, sticky=W, padx=12)

  def initialize_mediacms_api(self, credentials_path="./credentials.json"):
    with open(credentials_path) as cred_file:
      cred_data = json.load(cred_file)
    
    self.mediacms_url = cred_data['mediacms']['url']
    self.mediacms_auth = (cred_data['mediacms']['username'], cred_data['mediacms']['password'])
    self.mediacms_api = MediaCMS_API(self.mediacms_url, self.mediacms_auth)

  def load_mediacms_video_url(self):
    url = self.mediacms_video_url.get()
    urlmatch = re.search(MEDIACMS_VIDEO_REGEX, url)
    
    if urlmatch is None:
      print(f"Failed to match url in {url}")
      return False
    
    mediacms_instance_url = urlmatch.group(1)

    self.loaded_clip_id = urlmatch.group(2)
    self.loaded_clip_info = self.mediacms_api.get_clip_info(self.loaded_clip_id)

    self.mediacms_video_title.set(self.loaded_clip_info['title'])
    self.mediacms_video_desc_entry.delete("1.0", END)
    self.mediacms_video_desc_entry.insert("1.0", self.loaded_clip_info['description'])

    raw_thumb = self.mediacms_api.get_clip_thumbnail_raw(self.loaded_clip_id)
    im = Image.open(io.BytesIO(raw_thumb))
    image = ImageTk.PhotoImage(im)

    self.current_thumbnail = image
    self.mediacms_video_thumbnail.configure(image=self.current_thumbnail)

  def download_mediacms_video(self):
    filename = asksaveasfile(initialfile="video.mp4", defaultextension=".mp4", filetypes=[("All files", "*.*"), ("Video files", "*.mp4")])
    self.mediacms_api.download_clip(self.loaded_clip_id, filename.name)

  def connect_to_youtube(self):
    self.youtube_connection = yt.get_authenticated_service()

    if self.youtube_connection is not None:
      self.mediacms_video_upload_to_youtube.configure(text="Upload to YouTube", command=self.upload_loaded_clip_to_youtube)

  def upload_loaded_clip_to_youtube(self):
    dled = self.mediacms_api.download_clip(self.loaded_clip_id, "./temp.mp4")
    if (dled):
      print("Done downloading temp clip")
    else:
      print("Failed to download temp clip")
      return
    
    title = self.mediacms_video_title.get()
    description = self.mediacms_video_desc_entry.get("1.0", END)
    tags = self.mediacms_video_tags.get()

    yt.initialize_upload(self.youtube_connection, "./temp.mp4", title, description, keywords=tags)

    if os.path.exists("./temp.mp4"):
      os.remove("./temp.mp4")