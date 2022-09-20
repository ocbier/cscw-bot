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

media_path = 'videos'
sessions_path = 'scheduling'


class PaperVideo:
    def __init__(self, name, id, session, session_number, talk_number = 0, video_path = '', presenter = ''):
        self.name = name
        self.id = id
        self.session = session
        self.session_number = session_number
        self.video_path = video_path
        self.presenter = presenter
        self.talk_number = talk_number
        


class CSCWManager:
    def __init__(self, bot_token, tv_channel_id):
        self.bot = Bot(bot_token) # Create the bot
        self.player = VLCPlayer() # Create the player
        self.tv_channel_id = tv_channel_id
    
    def sortPapers(self, paper):
        return paper.talk_number

    # Sends messages to channel corresponding to the session for each paper and then play each paper presentation
    async def broadcast_session(self, papers):

        sorted_papers = sorted(papers, key=self.sortPapers)

        for paper in sorted_papers:
            message = 'The video presentation for ' + paper.name + ' will be starting now!'
            try:
                if paper.presenter != None and isinstance(paper.presenter, str):
                    message = message + '\nPresenter: ' + paper.presenter

                await self.bot.send_message_by_name(paper.session, paper.session_number, message) # Send message about the paper in the session channel
            except Exception as ex:
                print('Error sending video announcement to session channel for paper ' + paper.name + 'Reason: ' + str(ex))
            try:
                self.player.play_video(paper.video_path)
                time.sleep(1)

                while True:
                    if not self.player.is_playing():
                        break
                    continue
            except:
                print('Error playing video ' + paper.video_path)

            

    # Sends message to the main session channel for the session and then broadcast it.
    async def start_session (self, papers, filler_video = ''):
        message = 'The session ' + papers[0].session + ' is about to start!'
        try:
            await self.bot.send_message(self.tv_channel_id, message)
        except Exception as ex:
            print('Sending session message failed for session "' + papers[0].session + '" Reason: ' + str(ex))

        try:
            await self.broadcast_session(papers)               
        except:
            print('Broadcasting session failed for session ' + papers[0].session)

        # Play a filler video after session, if specified.
        if filler_video != '':
                try:
                    self.player.play_video(filler_video)
                except:
                    print('Error playing the filler video') 
        

    
# Overall approach: Schedule all the video playlists to play for each session start time in both weeks and play the video(s) for each session in playlists. Ensure that all start times are in UTC and that the clock used is UTC. Iterate over each session row (indexed by #) in the time table and schedule the videos for each session in both weeks. Lookup the corresponding data for each session in session_data.
async def main():
    scheduler = AsyncIOScheduler(timezone=utc)

    load_dotenv()
    bot_token = os.getenv('TOKEN')
    live_tv_channel = int(os.getenv('TV_CHANNEL_ID'))
    manager = CSCWManager(bot_token, live_tv_channel)


    session_data = pd.read_csv(os.path.join(sessions_path, 'sessions.csv'))
    timetable_data = pd.read_csv(os.path.join(sessions_path, 'timetable.csv'))

    print ('Scheduling videos...')
    for i, session_times in timetable_data.iterrows():
        session_papers = []
        for m, paper_info in session_data.iterrows():
            # Add all the paper ids with rows that have matching session ids to the lists for both weeks
            if paper_info["session_number"] == session_times["session_number"]:
                session_papers.append(PaperVideo(id = paper_info["cycle"] + '_' + str(paper_info["paper_id"]), 
                name = paper_info["title"], 
                session = paper_info["session_name"],
                session_number = paper_info["session_number"],
                presenter = paper_info["presenter"],
                talk_number = int(paper_info["talk_number"]),
                video_path=os.path.join(media_path, paper_info["cycle"] + '_' + str(paper_info["paper_id"]) + '.mp4')))
        
    
        # Schedule the session to be broadcast at the correct time for both week 1 and week 2
        w1_time = parser.parse(session_times["w1_time_utc"]).replace(tzinfo=timezone.utc)# Get the datetime for week 1 as utc
        w2_time = parser.parse(session_times["w2_time_utc"]).replace(tzinfo=timezone.utc)# Get the datetime for week 2 as utc

        filler_video = os.path.join(media_path, 'cscw_filler.mp4')

        scheduler.add_job(manager.start_session, 'date', run_date=w1_time, kwargs = {
            'papers': session_papers,
            'filler_video': filler_video
            })
        scheduler.add_job(manager.start_session, 'date', run_date=w2_time, kwargs = {
            'papers': session_papers,
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



