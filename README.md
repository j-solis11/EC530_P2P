# P2P Chat System

A Python-based peer-to-peer chat system with a central server that facilitates user discovery and room management. Users connect to the server to see who is online and can then directly message other users or join chat rooms for group discussions. The actual communication happens peer-to-peer, with the server only managing visibility and room keys.

## Features:
- Peer-to-peer communication between users.
- Central server manages active user lists and chat rooms.
- Users can send direct messages to others connected to the server or in the same room.
- Users can create and join chat rooms using unique server-generated keys.
- Ability to mute/unmute users to ignore their messages.
- Displays a list of active users.
- Keep-alive mechanism to detect disconnected users.
- Command-line interface for all interactions.

## Usage:

### Run the Server
Start the server with:
python server.py

Start any clients after with:
python client.py

### Commands
USERS : See current available users (whether in chat room or server)
mute <user>: Muting a user
unmute <user>: Unmuting a user
muted: Viewing muted users
create_room <name>: Creating a room with the room name
join_room <room_key>: Joining a room using the room key
leave_room: Leaving the current room
msg <user>: Messaging a user in your chat room or server privately
