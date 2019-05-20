API_KEY = ""
DONT_PRINT_USAGE_FOR = []
REP_DIRECTORY = "C:\\GabenStorage"
MAX_UPLOAD_SIZE_MB = 300
UNITY = {
    "2017.2.0f3": "C:\\Program Files\\Unity\\Editor\\Unity.exe",
	"2017.4.3f1": "C:\\Program Files\\Unity2017.4.3\\Editor\\Unity.exe"
}
QUOTES = ["I'm a handsome man with a charming personality.", \
    "If Nvidia makes better graphics technology, all the games are going to shine", \
    "If we come out with a better game, people are going to buy more PCs.", \
    "The PC is successful because we're all benefiting from the competition with each other.", \
    "I think Windows 8 is a catastrophe for everyone in the PC space.", \
    "The Steam store is this very safe, boring entertainment experience", \
    "Photoshop should be a free-to-play game.", \
    "The easiest way to stop piracy is not by putting antipiracy technology to work", \
    "Ninety percent of games lose money; 10 percent make a lot of money", \
    "Solar Games perhaps a best place to work", \
    "The programmers of tomorrow are the wizards of the future. ", \
    "Don't ever, ever try to lie to the internet.", \
    "I've always wanted to be a giant space crab.", \
    "George Lucas should have distributed the 'source code' to Star Wars.", \
    "The PS3 is a total disaster on so many levels", \
    "I'd like to thank Sony for their gracious hospitality, and for not repeatedly punching me in the face."]

def get_random_quote():
    import random
    return random.choice(QUOTES)