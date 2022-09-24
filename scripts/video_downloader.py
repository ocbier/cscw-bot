import requests
import csv
import os
import os.path
import pathlib
import shutil

def download_file_from_google_drive(id, destination):
    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : 1 }
        response = session.get(URL, params = params, stream = True)

    save_response_content(response, destination)

def get_confirm_token(response):
    for key, value in response.cookies.items():
        if key.startswith('download_warning'):
            return value

    return None

def save_response_content(response, destination):
    CHUNK_SIZE = 32768

    with open(destination, "wb") as f:
        for chunk in response.iter_content(CHUNK_SIZE):
            if chunk: # filter out keep-alive new chunks
                f.write(chunk)

IDX_TIME = 2
IDX_LINK_VID = 2
IDX_LINK_SRT = 3
IDX_PCSURL = 4
IDX_TITLE = 5
IDX_PAPER_ID = 7

def get_paper_id(pcs_url):
    pcs_url = pcs_url[36:] # skip https://new.precisionconference.com/
    i_slash = pcs_url.find('/')
    cycle_id = pcs_url[:i_slash]
    sub_id = pcs_url[pcs_url.find("author/subs/")+12:]
    if sub_id.find('/') != -1:
        sub_id = sub_id[:sub_id.find('/')]
    return cycle_id+"_"+sub_id

def down_file(id, fpath):
    if os.path.isfile(fpath):
        print("Skipped:", fpath)
    else:
        download_file_from_google_drive(id, fpath)

def down_files(d):
    vid_id = d[IDX_LINK_VID][d[IDX_LINK_VID].find("id=")+3:]
    srt_id = d[IDX_LINK_SRT][d[IDX_LINK_SRT].find("id=")+3:]
    paper_id = d[IDX_PAPER_ID]
    print(paper_id)
    down_file(srt_id, 'files/'+paper_id+".srt")
    down_file(vid_id, 'files/'+paper_id+".mp4")


if __name__ == "__main__":
    valid_d = []
    with open (os.path.join('..', 'scheduling', 'links.csv')) as csvf:
        reader = csv.reader(csvf, delimiter=',')
        next(reader, None)  # skip the headers
        for row in reader:
            if not any(v == '' for v in row):
                valid_d.append(row)

    if len(valid_d):
        # add paper_id column
        for d in valid_d:
            d.append(get_paper_id(d[IDX_PCSURL]))

        # remove duplicates
        s = set()
        valid_d.reverse()
        clean_d = []
        for d in valid_d:
            if d[IDX_PAPER_ID] not in s:
                clean_d.append(d)
                s.add(d[IDX_PAPER_ID])
            else:
                print ("Removed Duplicate Submission:", d)
        valid_d = clean_d
        valid_d.reverse()

        # download
        if (True):
            i = 1
            for d in valid_d:
                print (i)
                i += 1
                down_files(d)