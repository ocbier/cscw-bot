import vlc, time

class VLCPlayer:

    def __init__(self):
        self.vlc_instance = vlc.Instance('--input-repeat=-1', '--mouse-hide-timeout=0', '--freetype-font=Verdana', '--freetype-rel-fontsize=22')
        self.player = self.vlc_instance.media_player_new()


    def play_video(self, video):
        media = self.vlc_instance.media_new(video)
        self.player.set_media(media)
        self.player.set_fullscreen(True)
        self.player.play()


    def is_playing(self):
        playing = set([1,2,3,4])
        return self.player.get_state() in playing


    def play_playlist(self, files):
        for video in files:
            try:
                self.play_video(video)
                
                time.sleep(1)

                while True:
                    state = self.player.get_state()
                    if not self.is_playing():
                        break
                    continue
            except:
                raise RuntimeError('Error playing video ' + video)

    