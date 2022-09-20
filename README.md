# cscw-bot Discord bot with automated broadcast notifications and automated streaming

## Description
Discord bot which automatically handles broadcasting announcements and scheduled video playback in VLC player with minimal user input required. 

### Features
- Sends announcements to a specified Discord channel whenever conference sessions are about to start. 
- Automatically plays conference videos for a session at scheduled times, with subtitles
- Announces videos to individual session channels

## Setup
Run `pip install -r requirements.txt` to ensure that all dependencies are installed. 

Ensure that the files `sessions.csv` and `timetable.csv` for the session and scheduling data are in a directory called "scheduling" within the root directory. The format of these files is described in the section Metadata Files, further on in this readme. Also, ensure that video and subtitle files are in a directory called "videos" in the root directory. See the section "Videos and Subtitle Files" for more info. Finally, the file `.env` must be present in the root directory (see the Settings section).


## Usage
To initiate the bot and automated playback, run `cscw-tv.py`. This will schedule Discord announcements and video playback to occur at the times specified in the timetable (`timetable.csv`). Note that this script should be kept running, otherwise the scheduled events will be cancelled. 


# Scheduling Metadata Files
The following are required csv files which must be present in the "scheduling" directory:
- `sessions.csv`: Includes the IDs and names of each session, as well as the paper names, conference cycle, and paper IDs.\
![plot](./docs/sessions.png)

- `timetable.csv`: Contains the start datetime of each of the numbered sessions, index by session ID. This file contains a column for the session number, week 1 session time, and week 2 session time. Note that all datetimes are in UTC (24-hour format).\
![plot](./docs/timetable.png)

# Video and Subtitle Files
Video and subtitle files must be included within the "videos" directory. Video files should be in a .mp4 file format The file names should follow the following format "cycle_paperid.mp4".

 The subtitles should be in a .srt format and must be present in the same directory as videos. Subtitle files must have identical file names to the corresponding video file.


## Settings
The following settings must be specified in `.env`. This file should not be included in source control, as it includes sensitive data:
- `TOKEN`: The private Discord bot token. 
- `TV_CHANNEL_ID`: The ID of the Discord channel where announcements about session will be sent when the session starts.