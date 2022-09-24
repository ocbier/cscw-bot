import pandas as pd
import os


media_path = os.path.join('..', 'videos')
video_suffix = 'mp4'

  


# Maps a URL cycle identifier (e.g., CSCW21d) to a cycle name used internally (e.g., July21)
def map_cycle(cycle):
    name = None

    match cycle:
        case 'cscw21b': 
            name = 'apr'
        
        case 'cscw21d':
            name = 'Jan22'

        case 'cscw22a':
            name = 'July21'

        case 'cscw22b':
            name = 'jan'
    
    return cycle_name


def get_session_number(papers, cycle, paper_id):

    for i, paper in papers.iterrows():
        if paper["cycle"] == cycle and paper["paper_id"] == paper_id:
            return paper["session_number"]

    return 0




submission_data = pd.read_csv(os.path.join('..', 'scheduling', 'links.csv'))
papers_data = pd.read_csv(os.path.join('..', 'scheduling', 'papers.csv'))

playlist_items = []

for i, submission_info in submission_data.iterrows():
    pcs_url = submission_info["URL of your paper's PCS submission page"]

    # Ensure there is a PCS url
    if pcs_url is None:
        print('No PCS URL provided for row ' + (i + 1))
        continue

    parts = pcs_url.split('/')
    if len(parts) < 7:
        print('Invalid PCS URL for row ' + (i + 1))
        continue

    pcs_cycle = parts[3].strip()
    paper_id = parts[6].strip()
    video_file = pcs_cycle + '_' + paper_id + '.' + video_suffix

    # Ensure the video file exists
    if not os.path.isfile(video_file):
        print('The associated file for PCS URL ' + pcs_url + ' does not exist. ' + 'Expected file ' + video_file)
        continue

    cycle_name = map_cycle(pcs_cycle)

    if cycle_name is None:
        print('Invalid cycle name for row ' + (i + 1))
        continue

    session_number = get_session_number(papers_data, cycle_name, paper_id)
    is_paper = True
    presenter = submission_info["Name of the Presenting Author"]

    playlist_row = [video_file, session_number, is_paper, paper_id, cycle_name, presenter]
    playlist_items.append(playlist_row)
    # End for

out_df = pd.DataFrame(data=playlist_items, columns=['file_name', 'session_number', 'is_paper', 'paper_id', 'cycle', 'presenter'])

    






    
    
