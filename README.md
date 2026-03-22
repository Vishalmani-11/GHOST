ghost.py 👻

make your linux machine invisible on any network

![Uploading 2026-03-21_23-44-26.png…]()


what is this
a simple python tool that makes your linux machine completely invisible on any network.
when ghost mode is on — nobody can ping you, nobody can scan you, you just disappear.
sudo nmap -sn 192.168.x.0/24

→ Host seems down. 👻

how it works
it does a few things under the hood:

sets up a nftables firewall that drops all unsolicited inbound packets
applies kernel level stealth params via sysctl — ignores all pings
auto bans anyone who tries to port scan you for 30 mins
randomizes your MAC address on every connection
kills avahi and cups — services that announce your presence on the network


usage
bash# clone it
git clone https://github.com/Vishalmani-11/ghost.py
cd ghost.py

# run it (needs root)
sudo python3 ghost.py
or use it directly with args:
bashsudo python3 ghost.py on      # go invisible
sudo python3 ghost.py off     # come back
sudo python3 ghost.py status  # check current state

requirements

linux (tested on arch / cachyos)
python 3
nftables (sudo pacman -S nftables)
NetworkManager


the story behind this
I was messing around with two laptops on my phone's hotspot late at night.
ran nmap from my Arch laptop to scan the network. my CachyOS laptop didn't show up at all.
I thought it had some advanced firewall. checked it — nothing installed.
turns out my phone was doing client isolation — silently blocking devices on the same hotspot from seeing each other. that one discovery sent me down a rabbit hole of learning about nftables, kernel hardening, MAC randomization and network stealth.
built this tool from everything I learned that night.

disclaimer
this is for educational purposes and personal use only.
use it to protect yourself — not to do anything shady.

author
made by @VishalM
if this helped you, drop a ⭐ on the repo!
