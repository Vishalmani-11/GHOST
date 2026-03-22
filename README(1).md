```
   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
  ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
  ██║  ███╗███████║██║   ██║███████╗   ██║   
  ██║   ██║██╔══██║██║   ██║╚════██║   ██║   
  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   
   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝  

  make your linux machine invisible on any network
                  by @VishalM
```

> scan the network. you won't show up. 👻

![screenshot](screenshot.png)

---

## what is this

a python tool that makes your linux machine completely invisible on any network.

one command and you disappear — nobody can ping you, nobody can scan you.

```bash
sudo nmap -sn 192.168.x.0/24

→ Host seems down. 👻
```

---

## how it works

| what | how |
|---|---|
| 🔥 nftables firewall | drops all unsolicited inbound packets |
| 👻 kernel stealth | ignores all pings at kernel level via sysctl |
| 🚫 auto ban | port scanners get blacklisted for 30 mins |
| 🎭 mac randomization | new mac address on every connection |
| 🔇 kill noisy services | stops avahi and cups from announcing you |
| 🌊 syn flood protection | rate limits new connections |

---

## usage

```bash
# clone it
git clone https://github.com/VishalM/ghost.py
cd ghost.py

# run interactive menu
sudo python3 ghost.py
```

or use it directly with args:

```bash
sudo python3 ghost.py on      # go invisible
sudo python3 ghost.py off     # come back
sudo python3 ghost.py status  # see current state
```

---

## what the menu looks like

```
  ghost.py — by @VishalM
  makes your linux machine invisible on any network

  1  turn ghost mode ON
  2  turn ghost mode OFF
  3  check status
  4  exit

  pick one:
```

---

## requirements

- linux (tested on arch / cachyos)
- python 3
- nftables → `sudo pacman -S nftables`
- NetworkManager

---

## the story behind this

I was messing around with two laptops on my phone's hotspot late at night.

ran nmap from my Arch laptop. my CachyOS laptop didn't show up at all.

I thought it had some advanced firewall. checked it — **nothing installed.**

turns out my phone was doing **client isolation** — silently blocking devices on the same hotspot from seeing each other. that one discovery sent me deep into nftables, kernel hardening, MAC randomization and network stealth.

built this tool from everything I learned that night.

> the best lessons don't come from courses. they come from asking *"wait... why?"*

---

## disclaimer

this is for educational purposes and personal security only.  
use it to protect yourself — not for anything shady.  
you are responsible for how you use this.

---

made by [@VishalM](https://github.com/VishalM) — drop a ⭐ if this helped you!
