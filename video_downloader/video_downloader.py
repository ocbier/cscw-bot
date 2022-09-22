# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

# Run "pip install gdown"

import gdown


def print_hi(name):
    url = 'https://drive.google.com/open?id=1c0BIRg3qGyi7cZmqZfKuLWxMhzUX5Yl5'
    output = 'testdown.mp4'
    gdown.download(url, output, quiet=False, fuzzy=True)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/