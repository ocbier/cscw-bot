import pandas as pd
import os


media_path = os.path.join('..', 'videos')
scheduling_path = os.path.join('..', 'scheduling')
video_suffix = 'mp4'
out_file = os.path.join(scheduling_path, 'playlist.csv')

  


# Maps a URL cycle identifier (e.g., CSCW21d) to a cycle name used internally (e.g., July21)
def map_cycle(cycle):
    name = None

    match cycle:
        case 'cscw21b': 
            name = 'apr'
        
        case 'cscw21d':
            name = 'jan22'

        case 'cscw22a':
            name = 'jul21'

        case 'cscw22b':
            name = 'jan'
    
    return name

def get_session_number(papers, cycle, paper_id):
    for i, paper in papers.iterrows():
        if str(paper["cycle"]).lower() == cycle and str(paper["paper_id"]) == paper_id:
            return paper["session_number"]


    return None


submission_data = pd.read_csv(os.path.join(scheduling_path, 'links.csv'))
papers_data = pd.read_csv(os.path.join(scheduling_path, 'papers.csv'))

playlist_items = []

files_found = 0
playlist_items_added = 0
for i, submission_info in submission_data.iterrows():
    pcs_url = submission_info["URL of your paper's PCS submission page"]

    # Ensure there is a PCS url
    if pcs_url is None:
        print('No PCS URL provided for row ' + str(i + 1))
        continue

    parts = str(pcs_url).split('/')
    if len(parts) < 7:
        print('Invalid PCS URL for row ' + str(i + 1))
        continue

    pcs_cycle = parts[3].strip()
    paper_id = parts[6].strip()
    video_file = pcs_cycle + '_' + paper_id + '.' + video_suffix

    # Ensure the video file exists
    if not os.path.isfile(os.path.join(media_path, video_file)):
        print('Associated file for PCS URL ' + pcs_url + ' not found. ' + 'Expected: ' + str(os.path.abspath(os.path.join(media_path, video_file))))
        continue
    
    files_found += 1
    cycle_name = map_cycle(pcs_cycle)

    if cycle_name is None:
        print('Invalid cycle name for row ' + str(i + 1))
        continue

    session_number = get_session_number(papers_data, cycle_name, paper_id)
    
    if session_number is None:
        print('Could not get associated session number for paper id: ' + str(paper_id) + ' in cycle: ' + str(cycle_name))
        continue

    is_paper = True
    presenter = submission_info["Name of the Presenting Author"]

    playlist_row = [video_file, session_number, is_paper, paper_id, cycle_name, presenter]
    playlist_items.append(playlist_row)

    playlist_items_added += 1
    # End for

# Create dataframe containing the playlist data
out_df = pd.DataFrame(data=playlist_items, columns=['file_name', 'session_number', 'is_paper', 'paper_id', 'cycle', 'presenter'])

#Write to UTF-8 csv file
out_df.to_csv(out_file, index=False, encoding='utf-8')

print ('Finished writing playlist file in ' + os.path.abspath(out_file))
print('**Results**\n\tSubmissions processed: ' + str(len(submission_data)) + '\n\t' + 'Videos found: ' + str(files_found) + '\n\tPlaylist items created: ' + str(playlist_items_added))







    
    
