import argparse
import asyncio, os, time
import sys
import json
from xmlrpc.client import Boolean
import pandas as pd
from pytz import utc
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dateutil import parser as date_parser
from datetime import datetime, timezone, timedelta
from exceptions import ChannelNotFoundException
from player import VLCPlayer
from bot import Bot
from data import SessionVideo, Paper
from dotenv import load_dotenv
from apscheduler.events import EVENT_JOB_ERROR


class PlaybackStatus:
    def __init__(self, session_name, session_number, playback_number):
        self.session_name = session_name
        self.session_number = session_number
        self.playback_number = playback_number
        

# Handles playback of scheduled videos and persists playback status.
class CSCWManager:
    def __init__(self, 
             bot, 
             tv_channel_id, 
             playlist_file, 
             papers_file, 
             authors_file, 
             media_path, 
             status_file = 'status.json',
             filler_video = '',
             test_mode = False):
        self.bot = bot
        self.player = VLCPlayer(test_mode) # Create the player
        self.tv_channel_id = tv_channel_id
        self.playlist_file = playlist_file
        self.media_path = media_path
        self.status_file = status_file
        self.filler_video = filler_video

        self.playback_status = PlaybackStatus(session_name = 'Idle', session_number=0, playback_number=0)

        self.papers_data = pd.read_csv(papers_file).fillna('')
        self.authors_data = pd.read_csv(authors_file).fillna('')
    

    def save_playback_status(self):
        out = { 
            "session_name": self.playback_status.session_name,
            "session_number": self.playback_status.session_number, 
            "playback_number": self.playback_status.playback_number
        }
        
        with open(self.status_file, "w") as outfile:
            json.dump(out, outfile)


    def load_playback_status(self):
        if not os.path.isfile(self.status_file):
            print('Cannot load status file. Play status unchanged.')
            return

        with open(self.status_file, 'r') as openfile:
            status_dict = json.load(openfile)

        self.playback_status.session_name = status_dict["session_name"]
        self.playback_status.session_number = status_dict["session_number"]
        self.playback_status.playback_number = status_dict["playback_number"]


    def create_session_message(self, session_videos):
        message = 'The session ' + self.playback_status.session_name + ' is about to start!\n\nThe following papers will be presented:'

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

            mapped_cycle = Paper.map_cycle(paper.cycle) # Map the cycle to the internal cycles used in the authors list

            if row["cycle"].lower() == mapped_cycle and int(row["id"]) == paper.id:
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

    # Play a filler video
    def play_filler(self):
        if self.filler_video != '':
                try:      
                    self.player.play_video(self.filler_video)
                except Exception as ex:
                    print('Error playing the filler video') 


    # Sends messages to session channel (before playback) for each video that is a paper presenation and then plays all session videos.
    async def broadcast_session(self, session_videos):
        for video in session_videos:
            #Only play the video with correct playback number. This is needed for cases where playback has restarted after first video.
            if not video.play_order == self.playback_status.playback_number:
                continue

            #Announce the video in the session channel, if it is a paper presentation
            if video.is_paper():
                try:
                    message = self.create_paper_message(video.paper)
                    channel_name = Bot.get_valid_name(self.playback_status.session_name, self.playback_status.session_number)
                    print('Sending presentation announcement to channel: ' + str(channel_name))
                    #await self.bot.send_message_by_name(channel_name, message) # Send message about the paper in the session channel
                except Exception as ex:
                    print('Error sending video announcement to session channel for paper ' + video.paper.title + 'Reason: ' + str(ex))
            else:
                print('Not a paper presentation. No announcement sent.')
            
            try:
                print('Now playing video # ' + str(video.play_order) + ': ' + video.video_path)

                # Save the playback status to file.
                self.playback_status.playback_number = video.play_order
                self.save_playback_status()

                self.player.play_video(video.video_path)
                time.sleep(1)

                while True:
                    if not self.player.is_playing():
                        break
                    continue

                self.playback_status.playback_number += 1 
            
            except Exception as ex:
                print('Error playing video ' + video.video_path + 'Reason: ' + str(ex))

        self.playback_status.session_name = 'idle'
        self.playback_status.session_number = 0
        self.playback_status.playback_number = 0

        self.save_playback_status()


    # Sends message to the main session channel for the session and then broadcast it. Reads the playlist and papers data from file
    # at the beginning of each session, to allow for the user to change playlist or paper info, any time before the session starts.
    async def start_session (self, session_number, session_name, play_number = 0, filler_video = ''):
        playlist_data = pd.read_csv(self.playlist_file).fillna('')

        session_videos = []

        for i, playlist_video in playlist_data.iterrows():
            if int(playlist_video["session_number"]) == int(session_number):
                paper = None
                video_path = os.path.join(self.media_path, playlist_video["file_name"])

                # If this is a paper, get the info for the paper
                if playlist_video["is_paper"]:
                    paper = Paper.get_paper(papers = self.papers_data, id = playlist_video["paper_id"], cycle = playlist_video["cycle"])
                else:
                    print('Not a paper')

                session_videos.append(SessionVideo(session_number = session_number, 
                    video_path = video_path, 
                    play_order = (int)(playlist_video["play_order"]),
                    paper = paper))

       
        # Update the current session name and number
        self.playback_status.session_name = session_name
        self.playback_status.session_number = session_number
        self.playback_status.playback_number = play_number

        # If the session is starting from the first video and there are videos to play, send an announcement.
        if self.playback_status.playback_number == 0 and len(session_videos) > 0:
            session_message = self.create_session_message(session_videos)
            try:
                print("Sending announcement for start of session: " + self.playback_status.session_name)
                # await self.bot.send_message(self.tv_channel_id, session_message)
            except Exception as ex:
                print('Sending session message failed for session "' + str(session_number) + '. ' + str(session_name) +'" Reason: ' + str(ex))

            # Set to 1 to enable first video in session to begin
            self.playback_status.playback_number = 1 
            self.save_playback_status()

        try:  
            await self.broadcast_session(session_videos)               
        except Exception as ex:
            print('Broadcasting session failed for session ' + str(session_number) + '. ' + str(session_name) +'. Reason: ' +str(ex))

        # Play a filler video after session
        self.play_filler()
      




scheduler = AsyncIOScheduler(timezone=utc)

def error_listener(event):
    print('Bot is stopping. ' + str(event))
    scheduler.shutdown(wait=False)
    os._exit(1)

# Overall approach: Schedule all the video playlists to play for each session start time in both weeks and play the video(s) for each session in playlists. Ensure that all start times are in UTC and that the clock used is UTC. Iterate over each session row (indexed by #) in the time table and schedule the videos for each session in both weeks. Lookup the corresponding data for each session in session_data.
async def main():
    media_path = 'videos'
    scheduling_path = 'scheduling'
    status_file = os.path.join('.', 'status.json')
    playlist_file = os.path.join(scheduling_path, 'playlist.csv')
    papers_file = os.path.join(scheduling_path, 'papers.csv')
    authors_file = os.path.join(scheduling_path, 'authors.csv')
    sessions_file = os.path.join(scheduling_path, 'sessions.csv')
    filler_video = os.path.join(media_path, 'cscw_filler.mp4')

    timetable_data = pd.read_csv(sessions_file)

    #Set up the command-line argument for test mode
    args_parser = argparse.ArgumentParser()
    args_parser.add_argument('-t', '--test', help='Test mode active. Defaults to false', default = False, type=bool)
    args = args_parser.parse_args()

    if args.test:
        print('***Running bot in test mode***')

    # Load configuration file
    load_dotenv()
    bot_token = os.getenv('TOKEN')
    live_tv_channel = int(os.getenv('TV_CHANNEL_ID'))
    guild_id = os.getenv('GUILD_ID')

    bot = Bot(bot_token, guild_id, test_mode = args.test) # Create the bot
    
    manager = CSCWManager(bot = bot, 
        tv_channel_id = live_tv_channel,
        playlist_file = playlist_file,
        papers_file = papers_file,
        authors_file = authors_file,
        media_path = media_path,
        status_file = status_file,
        filler_video = filler_video,
        test_mode = args.test)

    manager.load_playback_status()

    print ('Scheduling sessions...')
    for i, session_row in timetable_data.iterrows():
        
        # Schedule the session to be broadcast at the correct time for both week 1 and week 2
        try:
            w1_time = date_parser.parse(session_row["w1_time_utc"]).replace(tzinfo=timezone.utc)# Get the datetime for week 1 as utc
            w2_time = date_parser.parse(session_row["w2_time_utc"]).replace(tzinfo=timezone.utc)# Get the datetime for week 2 as utc
        except Exception as ex:
            print('Could not parse date for row ' + str(i+2) + ' in file ' + sessions_file + '. Reason: ' + str(ex))
            continue

        scheduler.add_job(manager.start_session, 'date', run_date=w1_time, kwargs = {
            'session_number': session_row["session_number"],
            'session_name': session_row["session_name"],
            })
        scheduler.add_job(manager.start_session, 'date', run_date=w2_time, kwargs = {
            'session_number': session_row["session_number"],
            'session_name': session_row["session_name"],
            })

        #If there is an incomplete session, schedule that session to restart at the correct playback number
        if manager.playback_status.playback_number > 0:
            resume_time = datetime.now(timezone.utc) + timedelta(seconds=10)
            scheduler.add_job(manager.start_session, 'date', run_date=resume_time, kwargs = {
                    'session_number': manager.playback_status.session_number,
                    'session_name': manager.playback_status.session_name,
                    'play_number': manager.playback_status.playback_number
                    })


        scheduler.add_listener(error_listener, EVENT_JOB_ERROR)
        scheduler.start()
        print("Scheduling complete.")
                
        # Play filler video to start
        manager.play_filler()
                
        print('Starting Discord bot. Please keep this script running.')
            
        await manager.bot.start()
           
        
   


asyncio.run(main()) # Start the app



