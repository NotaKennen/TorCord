## TorCord
TorCord is a Discord client that uses Tor to connect to Discord. TorCord is entirely based on the terminal, so there is no GUI. As far as I'm aware, it *can* run on Mac and/or Linux, but the screen might be a bit weird. Recommended to be used on Windows (tested on Windows 11).

### Usage
To use TorCord, you must first have Tor. You can download Tor from [here](https://www.torproject.org/). Once Tor is installed, you need place the Tor into PATH. After that, you should be able to run "where tor" and get the path of your Tor installation. After that, you should be able to run TorCord normally.

When you first log in, you can see a list of servers you can "focus" into. This will allow you to see the messages in the server. Once focused, it will also show the last ~30 messages (this is not a technical limit, I just didn't feel like coding more to make it larger). You can then send messages into the channel, and see any messages other send. Currently images and stickers are not supported (maybe in the future, somehow?), so they will just display as blank messages.

### Features
Right now TorCord is somewhat lacking in features (as it's not really designed to be used seriously), but the main feature of discord exists: servers and messages (specifically servers, DMs are not implemented). The main point of the entire project is just to get Discord to work through Tor, which I'd say worked pretty well. I might make it more complex in the future, but for now, it's good enough.

### Documentation
The codebase is a mess. There is no real "documentation", but I sure do hope you're willing to read some code if you want to see the project. I do believe that the code is at least *somewhat* readable, so you can read the code if you want.

### Known bugs
- You can see and focus into channels you shouldn't be seeing, the program will crash if you do this.
- The program sometimes crashes when exiting focus from a channel (seemingly randomly).
- The program can sometimes try to run bash code (based on what you wrote in your messages) after closing itself, but only when exiting in very specific situations (shouldn't happen in normal use... I think?).
- Slight screen flickering due to it re-printing the entire terminal (by design).
- Will not connect to Tor properly if ran from a secondary script (might be a computer specific issue).
