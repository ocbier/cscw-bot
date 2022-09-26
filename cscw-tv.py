import asyncio, os, time
import pandas as pd
from pytz import utc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil import parser
from datetime import timezone
from exceptions import ChannelNotFoundException
from player import VLCPlayer
from bot import Bot
from dotenv import load_dotenv



class SessionVideo:
    def __init__(self, session_number, video_path, paper = None):
        self.session_number = session_number
        self.video_path = video_path
        self.paper = paper

    def is_paper(self):
        return self.paper is not None


class Paper :
    def __init__(self, title, id, cycle, talk_number, presenter = None): 
        self.title = title
        self.id = id
        self.cycle = cycle
        self.talk_number = talk_number
        self.presenter = presenter

    @staticmethod
    def get_paper (papers, cycle, id):
        for i, paper in papers.iterrows():
            if paper["cycle"] == cycle and paper["paper_id"] == id:
                return Paper(title = paper["title"], cycle = paper["cycle"] ,id = paper["paper_id"], talk_number = paper["talk_number"])



class CSCWManager:
    def __init__(self, bot_token, tv_channel_id, playlist_file, papers_file, authors_file, media_path):
        self.bot = Bot(bot_token) # Create the bot
        self.player = VLCPlayer() # Create the player
        self.tv_channel_id = tv_channel_id
        self.playlist_file = playlist_file
        self.media_path = media_path

        self.current_session_name = 'Idle'
        self.current_session_number = -1

        self.papers_data = pd.read_csv(papers_file).fillna('')
        self.authors_data = pd.read_csv(authors_file).fillna('')
    
    # obsolete
    def sort_papers(self, paper):
        return paper.talk_number

    def create_session_message(self, session_videos, session_name):
        message = 'The session ' + session_name + ' is about to start!\n\nThe following papers will be presented:'

        # Add titles to the announcement message
        count = 0 
        for count, video in enumerate(session_videos, start=1):
            if video.is_paper() and not video.paper.title.strip() == '':
                message = message + '\n' + str(count) + '. ' + video.paper.title.strip()

        return message


    def create_author_message(self, paper):
        message = ''

        j = 1
        for i, row in self.authors_data.iterrows():
            if row["cycle"] == paper.cycle and row["id"] == paper.id:
                column = "author_" + str(j)
                next_author = str(row[column]).strip() if column in self.authors_data.columns else None
                while next_author is not None and len(next_author) > 2:
                    cur_author = next_author
                    j += 1
                    column = "author_" + str(j)
                    next_author = str(row[column]).strip() if column in self.authors_data.columns else None
                    
                    #First author
                    if j == 2:
                        message += cur_author
                    # Normal case, after first
                    elif next_author is not None and len(next_author) > 2:
                        message += ', ' + cur_author    
                    # This is the last author
                    else:
                        message += ' and ' + cur_author



        message.strip().replace('\n', '')
        if len(message) > 2:
            return message

        return None


    def create_paper_message(self, paper):
        message = 'The video presentation for "' + paper.title + '" will be starting now!'

        # Display the author names
        authors = self.create_author_message(paper)
        if not authors is None:
            message = message + '\nAuthors: ' + authors

        if not (paper.presenter is None or paper.presenter == ''):
            message = message + '\nPresented by: ' + paper.presenter

        return message

        


    # Sends messages to session channel (before playback) for each video that is a paper presenation and then plays all session videos.
    async def broadcast_session(self, session_videos):
        for video in session_videos:
            #Announce the video in the session channel, if it is a paper presentation
            if video.is_paper():
                try:
                    message = self.create_paper_message(video.paper)
                    channel_name = Bot.get_valid_name(self.current_session_name, self.current_session_number)
                    print('Sending presentation announcement to channel: ' + str(channel_name))
                    await self.bot.send_message_by_name(channel_name, message) # Send message about the paper in the session channel
                except Exception as ex:
                    print('Error sending video announcement to session channel for paper ' + video.paper.title + 'Reason: ' + str(ex))
            else:
                print('Not a paper presentation. No announcement sent.')
            try:
                print('Now playing: ' + video.video_path)
                self.player.play_video(video.video_path)
                time.sleep(1)

                while True:
                    if not self.player.is_playing():
                        break
                    continue
            except:
                print('Error playing video ' + video.video_path)

            

    # Sends message to the main session channel for the session and then broadcast it. Reads the playlist and papers data from file
    # at the beginning of each session, to allow for the user to change playlist or paper info, any time before the session starts.
    async def start_session (self, session_number, session_name, filler_video = ''):
        
        playlist_data = pd.read_csv(self.playlist_file).fillna('')

        session_videos = []

        for i, playlist_video in playlist_data.iterrows():
            if playlist_video["session_number"] == session_number:
                paper = None
                video_path = os.path.join(self.media_path, playlist_video["file_name"])

                # If this is a paper, get the info for the paper
                if playlist_video["is_paper"]:
                    paper = Paper.get_paper(papers = self.papers_data, id = playlist_video["paper_id"], cycle = playlist_video["cycle"])
                    paper.presenter = playlist_video["presenter"]
                else:
                    print('Not a paper')

                session_videos.append(SessionVideo(session_number, video_path, paper))

        # Case for an empty session.
        if len(session_videos) < 1:
            return

        session_message = self.create_session_message(session_videos, session_name)

        try:
            await self.bot.send_message(self.tv_channel_id, session_message)
        except Exception as ex:
            print('Sending session message failed for session "' + str(session_number) + '. ' + str(session_name) +'" Reason: ' + str(ex))

        try:
            # Update the current session name and number
            self.current_session_name = session_name
            self.current_session_number = session_number
            await self.broadcast_session(session_videos)               
        except:
            print('Broadcasting session failed for session ' + str(session_number) + '. ' + str(session_name))

        self.current_session_name = 'idle'
        self.current_session_number = -1
        # Play a filler video after session, if specified.
        if filler_video != '':
                try:      
                    self.player.play_video(filler_video)
                except:
                    print('Error playing the filler video') 
        

    
# Overall approach: Schedule all the video playlists to play for each session start time in both weeks and play the video(s) for each session in playlists. Ensure that all start times are in UTC and that the clock used is UTC. Iterate over each session row (indexed by #) in the time table and schedule the videos for each session in both weeks. Lookup the corresponding data for each session in session_data.
async def main():
    media_path = 'videos'
    scheduling_path = 'scheduling'
    playlist_file = os.path.join(scheduling_path, 'playlist.csv')
    papers_file = os.path.join(scheduling_path, 'papers.csv')
    authors_file = os.path.join(scheduling_path, 'authors.csv')
    sessions_file = os.path.join(scheduling_path, 'sessions.csv')
    filler_video = os.path.join(media_path, 'cscw_filler.mp4')

    scheduler = AsyncIOScheduler(timezone=utc)

    load_dotenv()
    bot_token = os.getenv('TOKEN')
    live_tv_channel = int(os.getenv('TV_CHANNEL_ID'))
    manager = CSCWManager(bot_token = bot_token, 
        tv_channel_id = live_tv_channel,
        playlist_file = playlist_file,
        papers_file = papers_file,
        authors_file = authors_file,
        media_path = media_path)


    timetable_data = pd.read_csv(sessions_file)

    print ('Scheduling sessions...')
    for i, session_row in timetable_data.iterrows():
        
    
        # Schedule the session to be broadcast at the correct time for both week 1 and week 2
        try:
            w1_time = parser.parse(session_row["w1_time_utc"]).replace(tzinfo=timezone.utc)# Get the datetime for week 1 as utc
            w2_time = parser.parse(session_row["w2_time_utc"]).replace(tzinfo=timezone.utc)# Get the datetime for week 2 as utc
        except Exception as ex:
            print('Could not parse date for row ' + str(i+2) + ' in file ' + sessions_file + '. Reason: ' + str(ex))
            continue

        scheduler.add_job(manager.start_session, 'date', run_date=w1_time, kwargs = {
            'session_number': session_row["session_number"],
            'session_name': session_row["session_name"],
            'filler_video': filler_video
            })
        scheduler.add_job(manager.start_session, 'date', run_date=w2_time, kwargs = {
            'session_number': session_row["session_number"],
            'session_name': session_row["session_name"],
            'filler_video': filler_video
            })

    scheduler.start()
    print("Scheduling complete.")
    print('Starting Discord bot. Please keep this script running.')

    try:
        await manager.bot.start()
    except BaseException as ex:
        print('Bot failed to start. ' + str(ex))

  
    

asyncio.run(main()) # Start the app



