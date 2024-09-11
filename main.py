from stem import Signal
from stem.control import Controller
import requests
import subprocess
import time
import psutil
import platform
import json
import sys
import threading
import keyboard


### Global vars ###
# Version
VERSION = 0.2

# Default username
username = "[NO-USERNAME-FOUND]"

# Cool print logos
BASIC = "\033[0m[*]"
ERROR = "\033[31m[!]"
INFO = "\033[34m[?]"
OTHER = "\033[32m[-]"

### Pre-discord funcs ###
#region Pre-discord
def is_program_running(program_name):
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == program_name:
            return True
    return False

def test_tor_connection():
    proxies = {
        'http': 'socks5h://127.0.0.1:9050',
        'https': 'socks5h://127.0.0.1:9050'
    }
    response = requests.get('http://httpbin.org/ip', proxies=proxies)
    return response.json()['origin']

def torRequest(url: str, headers: dict = None, data=None, mode="get"):
    """ 
    Makes a GET request to the given URL using the Tor proxy,
    refreshing the IP address first if needed.

    :param url: The URL to make the request to
    :return: The response object
    """
    def get_tor_session():
        session = requests.Session()
        session.proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        return session

    def renew_tor_ip():
        with Controller.from_port(port=9051) as controller:
            controller.authenticate()  # Provide the password if needed
            controller.signal(Signal.NEWNYM)

    # Use the function to renew IP if needed
    renew_tor_ip()

    session = get_tor_session()
    if mode == "get":
        return(session.get(url, headers=headers, data=data))
    elif mode == "post":
        return(session.post(url, headers=headers, data=data))

def bash(command: str, capture=True):
    return subprocess.run(command, shell=True, capture_output=capture, text=True)

def getTor():
    # Get Tor location
    torLocation = bash('where firefox')
    if torLocation.stderr == "INFO: Could not find files for the given pattern(s).\n":
        print(f"{ERROR} Tor is not installed (or not in Path!)")
        time.sleep(10)
        exit()
    elif torLocation.stderr != "":
        raise(Exception(f"{ERROR} Unknown error: " + torLocation.stderr))

    return torLocation.stdout

def clear_console(title=True):
    # Determine the OS and run the appropriate command
    if platform.system() == 'Windows':
        subprocess.run('cls', shell=True)
    else:
        subprocess.run('clear', shell=True)
    if title:
        print(f"TorCord v{VERSION} / logged on as {username}")
        print("use 'tc/back' to go back\n\n")

def accessData(mode="r", data=None):
    if mode == "r":
        try:
            with open('data.json', 'r') as file:
                data = json.load(file)
            return data
        except:
            return {}
    elif mode == "w":
        with open('data.json', 'w') as file:
            # Write the data to the file
            json.dump(data, file)
        return True

### - ###
#endregion

### Discord funcs ###
#region Discord
def discordRequest(url: str, mode="get", data=None):
    response = torRequest(url, headers={'Authorization': token}, mode=mode, data=data)
    try:
        if response.json()["message"] == "401: Unauthorized":
            print(f"{ERROR} Invalid token!")
            data = accessData("r")
            data["token"] = "CLEANED"
            accessData("w", data)
    except:
        pass
    return response.json()

def getGuilds(token):
    response = discordRequest("https://discordapp.com/api/users/@me/guilds")
    guilds = []
    for server in response:
        guilds.append((str(server['name']), str(server['id'])))
    return guilds

def getChannels(guildId: int):
    #TODO: get DMs
    channelsLst = discordRequest(f"https://discordapp.com/api/guilds/{guildId}/channels")
    channelRsp = []
    for i in channelsLst:
        if int(i["type"]) != 0:
            continue
        channelRsp.append((str(i['name']), str(i['id'])))
    return channelRsp

def getMessages(channelId: int):
    return list(discordRequest(f"https://discordapp.com/api/channels/{channelId}/messages"))

def postMessage(channelId: int, message: str):
    return discordRequest(f"https://discordapp.com/api/channels/{channelId}/messages", mode="post", data={"content": message})

### - ### 
#endregion

### Message listener ### 
#region MessageListener
# Variables
messageListenerStatus = False # Status
messageInput = [] # Stores the input
inputMessage = "Input Message >>> " # What is the message that they're inputting on
baseRsp = "" # "base response", what is currently on the screen, update as necessary, remember to clear

def startMessageListener():
    """
    Starts a thread that will listen for new messages in a channel and update the console accordingly

    The thread will sleep for 1 second if there are no new messages, and will otherwise update the console with the new messages

    :return: None
    """
    def output():
        global baseRsp # Base response (what is written before)
        global messages # messages ??? (technical debt am i right)
        global channel
        
        while True:
            # Close thread when necessary
            if not messageListenerStatus:
                return
            
            # If there are no messages in the channel, no need to update the console
            incMessage = getMessages(channel[1])
            incMessage.reverse()
            if incMessage == messages:
                time.sleep(1)
                continue
            messages = incMessage

            # Renew the base response
            # Prepare a response to the user
            baseRsp = f"[>] Messages in {channel[0]}:\n"
            for message in messages:
                # TODO: add pings and timestamps
                # Rest of the message
                baseRsp += f"{message['author']['username']} [>] {message['content']}\n"

            # make messageInput to string
            stored_input = ""
            for i in messageInput:
                stored_input += str(i)

            # Edit console
            clear_console()
            print(baseRsp + f"\n{inputMessage}{stored_input}", end="")

    thread = threading.Thread(target=output, name="Message Listener thread")
    thread.start()

def capture_input():
    global messageInput
    global baseRsp
    global channel
    while True:
        event = keyboard.read_event()
        if event.event_type == keyboard.KEY_DOWN:
            if event.name == 'enter':  # Enter key pressed
                if messageInput == ['t', 'c', '/', 'b', 'a', 'c', 'k']: #back from the message input
                    messageInput = []
                    return False
                sentMessage = ""
                for i in messageInput: sentMessage += str(i)
                postMessage(channel[1], sentMessage)
                messageInput = []
                clear_console()
                print(baseRsp)
                return True
            elif event.name == 'backspace':  # Backspace key pressed
                if messageInput:
                    messageInput.pop()
                    sys.stdout.write('\b \b')  # Remove character from the screen
                    sys.stdout.flush()
            elif len(event.name) == 1:  # Regular character key
                messageInput.append(event.name)
                sys.stdout.write(event.name)
                sys.stdout.flush()
            elif event.name == 'space':
                messageInput.append(' ')
                sys.stdout.write(' ')
                sys.stdout.flush()

### - ### 
#endregion

### Main ###
#region Connection

clear_console(False)

# Load config
print(f"{BASIC} Loading config...")
try:
    with open("config.json", "r") as file:
        config = json.load(file)
except FileNotFoundError:
    print(f"{ERROR} config.json does not exist!")
    with open("config.json", "w") as file:
        json.dump({"headless": True}, file)  # default config
    config = {"headless": True}
    print(f"{INFO} Created config.json!")
headless = config["headless"]

# Get Tor
print(f"{BASIC} Getting Tor location...")
torLocation = getTor()
torLocation = torLocation.rstrip('\n')

print(f"{BASIC} Tor has been found! Location: " + torLocation)

# Kill pre-existing Tor because Tor doesn't like two instances
if is_program_running('tor.exe'):
    subprocess.run(["taskkill", "/f", "/im", "tor.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"{ERROR} Tor was active. It has been closed.")

print(f"{BASIC} Starting Tor...")

if headless:
    bash(f'start "" "{torLocation}" --headless', False)
else:
    bash(f'start "" "{torLocation}"', False)

print(f"{BASIC} Waiting for Tor to start...")
counter = 0
while True:
    counter += 1
    if is_program_running('tor.exe'):
        break
    time.sleep(0.1)
    if counter >= 600:
        print(f"{ERROR} Could not start Tor!")

print(f"{BASIC} Tor has started, waiting for connection...")
counter = 0
while True:
    try:
        counter += 1
        test_tor_connection()
        break
    except:
        pass
    if counter >= 10:
        print(f"{ERROR} Could not connect to Tor! See if Tor is configured to connect automatically.")
        time.sleep(10)
        exit()

print(f"{BASIC} Connected to Tor!")

print(f"{BASIC} Loading data...")
# (distinction between data and config)
# (Config = everything on the host / Data = everything we get and/or validate from Discord)
# (Loading configs is much faster so we can do it before the program starts, data is slower, so it's better to have it's own section)

# Continue testing tokens until a valid one is found
while True:
    data = accessData()
    # See if token exists in the data file
    try:
        token = data["token"]

        # Token was cleared by the system
        if token == "CLEANED":
            print(f"{ERROR} the system has cleaned your (invalid) token.")
            token = input(f"{BASIC} Enter your token >>> ")
            accessData("w", {"token": token})

        # Test token
        response = torRequest("https://discordapp.com/api/users/@me/guilds", headers={'Authorization': token})
        if str(response)== "<Response [401]>":
            print(f"{ERROR} Invalid token!")
            token = input(f"{BASIC} Enter your token >>> ")
            accessData("w", {"token": token})
        elif str(response) == "<Response [200]>":
            break
        else:
            print(f"{ERROR} Something went wrong with connecting to discord:" + str(response))

    # (token does not exist)
    except KeyError:
        print(f"{ERROR} Token not found in data file!")
        token = input(f"{BASIC} Enter your token >>> ")
        accessData("w", {"token": token})

# Load username
try:
    username = str(discordRequest("https://discordapp.com/api/users/@me")["username"])
except Exception as e:
    print(f"{ERROR} Could not load username!")

print(f"{BASIC} Data loaded, starting TorCord!")
time.sleep(1.5)
#endregion 

# "Global" view
while True:
    #TODO: notifications "tab"
    # Get servers they're in
    guilds = getGuilds(token)

    # Prepare response
    counter = 0
    serverRsp = "[>] Servers:\n"
    for i in guilds:
        counter += 1
        serverRsp += f"[{counter}] {str(i[0])}: {str(i[1])}\n"

    # Print response
    clear_console()
    print(serverRsp)

    # Ask for channels
    selection = input("Which server would you like to focus into? >>> ")

    # Let user exit
    if selection == "tc/back":
        exit()

    # Convert to int
    selection = int(selection)

    # Check to see if it's a valid selection
    if selection > counter or selection < 1:
        print(f"{ERROR} Invalid selection!")
        time.sleep(1.5)
        continue

    # Parse the server ID
    server = int(guilds[selection - 1][1])
    while True:

        # Get channels and prepare a response to the users
        channels = getChannels(server)
        counter = 0
        Rsp = "[>] Channels:\n"
        for i in channels:
            counter += 1
            Rsp += f"[{counter}] {str(i[0])}: {str(i[1])}\n"
        clear_console()
        print(Rsp)

        # Get user response
        selection = input("Which channel would you like to focus into? >>> ")

        # Allow user to leave channel selection
        if selection == "tc/back":
            break
        selection = int(selection)

        # Figure which channel they meant
        if selection > counter or selection < 1:
            print(f"{ERROR} Invalid selection!")
            time.sleep(1.5)
            continue
        channel = channels[selection - 1]

        # Get messages
        messages = getMessages(channel[1]) # channel[1] = channel ID
        messages.reverse() # Reverse the messages because they come oldest -> newest

        # Prepare a response to the user
        Rsp = f"[>] Messages in {channel[0]}:\n"
        for message in messages:
            # Rest of the message
            Rsp += f"{message['author']['username']} [>] {message['content']}\n"
        clear_console()
        print(Rsp)

        # start listening for messages in the channel
        baseRsp = Rsp
        messageListenerStatus = True
        startMessageListener()
        while True:
            print(inputMessage, end="")
            selection = 0 # Dunno why this needs to be here, but i'm getting issues if it isn't
            if not capture_input():
                messageListenerStatus = False
                break