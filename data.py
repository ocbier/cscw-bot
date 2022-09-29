class SessionVideo:
    def __init__(self, session_number, video_path, play_order, paper = None):
        self.session_number = session_number
        self.video_path = video_path
        self.play_order = play_order
        self.paper = paper
        
    def is_paper(self):
        return self.paper is not None
    
    @staticmethod
    def sort_video(video):
        return video.play_order



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
            paper_cycle = paper["cycle"].lower()
            paper_id = int(paper["paper_id"])
            if paper_cycle == cycle.lower() and paper_id == int(id):
                return Paper(title = paper["title"], 
                cycle = paper_cycle, 
                id = paper_id, 
                talk_number = paper["talk_number"],
                presenter = paper["presenter"])

    # Maps a URL cycle identifier (e.g., CSCW21d) to a cycle name used internally (e.g., July21)
    @staticmethod
    def map_cycle(cycle):
        name = None

        match cycle:
            case 'cscw21b': 
                name = 'jan'    
            case 'cscw21d':
                name = 'apr'
            case 'cscw22a':
                name = 'jul21'
            case 'cscw22b':
                name = 'jan22'
        
        return name