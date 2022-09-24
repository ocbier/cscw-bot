

# Run "pip install gdown"
# "pip install pandas"
import gdown
import pandas as pd


def download(name):
    url = 'https://drive.google.com/open?id=1c0BIRg3qGyi7cZmqZfKuLWxMhzUX5Yl5'
    output = 'testdown.mp4'
    gdown.download(url, output, quiet=False, fuzzy=True)



submissions = pd.read_csv('video_metadata')

