import pandas as pd
import os
from os.path import isfile, join


media_path = os.path.join('..', 'videos')
scheduling_path = os.path.join('..', 'scheduling')
video_suffix = 'mp4'
out_file = os.path.join(scheduling_path, 'playlist.csv')

  

def get_presentation_info(papers, target_cycle, target_id):
    for i, paper in papers.iterrows():      

        paper_cycle = paper["cycle"].lower().strip()
        paper_id = str(paper["paper_id"])

        if len(paper_cycle) < 1 or len(paper_id) < 1:
            continue

        if paper_cycle == target_cycle.lower() and paper_id == str(target_id):
            return {
                "session_number": paper["session_number"],
                "talk_number": paper["talk_number"]
            }


    return None

# Pre-process data and ensure that numbers are stored as integers.
papers_data = pd.read_csv(os.path.join(scheduling_path, 'papers.csv')).dropna()
papers_data['paper_id'] = papers_data['paper_id'].astype(int)
papers_data['session_number'] = papers_data['session_number'].astype(int)
papers_data['talk_number'] = papers_data['talk_number'].astype(int)


playlist_items = []
existing_files = []

playlist_items_added = 0
files = [f for f in os.listdir(media_path) if isfile(join(media_path, f))]

for video in files:
    video_lower = video.lower()
    parts = str(video_lower).split('_')
    if len(parts) < 2:
        print('Invalid file name for file ' + str(video))
        continue

    pcs_cycle = parts[0]
    second = parts[1].split('.')
    
    if not second[1] == video_suffix:
        continue
    
    if len(pcs_cycle) < 5:
        print('Invalid cycle name ' + str(pcs_cycle))
        continue

    paper_id = second[0]

    if len(paper_id) == 0:
        print('Invalid paper id ' + str(paper_id))
        continue

    if video in existing_files:
        print('Ignoring entry for video ' + str(video))
        continue

    existing_files.append(video_lower)
    
    presentation_info = get_presentation_info(papers_data, pcs_cycle, paper_id)
    
    if presentation_info is None:
        print('Could not get associated session number for paper id: ' + str(paper_id) + ' in cycle: ' + str(pcs_cycle))
        continue

    is_paper = True
    
    playlist_row = [video, presentation_info["session_number"], is_paper, paper_id, pcs_cycle, presentation_info["talk_number"]]
    playlist_items.append(playlist_row)

    playlist_items_added += 1
    # End for

# Create dataframe containing the playlist data
out_df = pd.DataFrame(data=playlist_items, columns=['file_name', 'session_number', 'is_paper', 'paper_id', 'cycle', 'talk_number'])


out_df.sort_values(['session_number', 'talk_number'])

#Write to UTF-8 csv file
out_df.to_csv(out_file, index=False, encoding='utf-8')

print ('Finished writing playlist file in ' + os.path.abspath(out_file))
print('**Results**\n\tTotal files processed: ' + str(len(files)) + '\n\t' + 'Valid video files found: ' + str(len(existing_files)) + '\n\tPlaylist items created: ' + str(playlist_items_added))







    
    
