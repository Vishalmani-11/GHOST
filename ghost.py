#!/usr/bin/env python3
# ghost.py - makes your linux machine invisible on network
# written by @VishalM
# learned this from experimenting with CachyOS and nmap lol

import os
import sys
import subprocess
import time

# just some colors to make output readable
G = "\033[92m"
R = "\033[91m"
Y = "\033[93m"
C = "\033[96m"
W = "\033[97m"
B = "\033[94m"
RS = "\033[0m"
BOLD = "\033[1m"

def p(msg, t="info"):
    tag = {
        "ok":   f"{G}[+]{RS}",
        "err":  f"{R}[-]{RS}",
        "warn": f"{Y}[!]{RS}",
        "run":  f"{C}[*]{RS}",
    }.get(t, f"{W}[~]{RS}")
    print(f"  {tag} {msg}")

def sh(cmd):
    # just runs a shell command silently, returns true/false
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return r.returncode == 0

def sh_out(cmd):
    # runs command and prints output
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if r.stdout.strip():
        for line in r.stdout.strip().split("\n"):
            print(f"    {C}{line}{RS}")

def check_root():
    if os.geteuid() != 0:
        p("need to run as root bro", "err")
        p(f"try: {Y}sudo python3 ghost.py{RS}", "warn")
        sys.exit(1)

# -------------------------------------------------------
# the actual nftables rules
# drop everything inbound by default
# only allow traffic that YOU started (established/related)
# also auto-bans port scanners for 30 mins
# -------------------------------------------------------
nft_config = """
flush ruleset

table inet ghost {

    set scanners {
        type ipv4_addr
        flags dynamic, timeout
        timeout 30m
    }

    chain input {
        type filter hook input priority 0;
        policy drop;

        iif "lo" accept
        ct state established, related accept
        ct state invalid drop

        # auto ban anyone scanning ports
        ip saddr @scanners drop
        tcp flags & (fin|syn|rst|ack) == syn limit rate over 15/minute \
            add @scanners { ip saddr }

        # drop weird scan packets (xmas, null)
        tcp flags & (fin|syn|rst|psh|ack|urg) == (fin|syn|rst|psh|ack|urg) drop
        tcp flags & (fin|syn|rst|psh|ack|urg) == 0x0 drop

        ct state new limit rate 50/second accept
        drop
    }

    chain forward {
        type filter hook forward priority 0;
        policy drop;
    }

    chain output {
        type filter hook output priority 0;
        policy accept;
    }
}
"""

# kernel params to go full stealth
# ignore pings, prevent spoofing, syn flood protection etc
sysctl_config = """
net.ipv4.icmp_echo_ignore_all = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_syn_retries = 2
net.ipv4.tcp_synack_retries = 2
net.ipv4.tcp_max_syn_backlog = 4096
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_rfc1337 = 1
"""

# mac randomization config for NetworkManager
mac_config = """
[device]
wifi.scan-rand-mac-address=yes

[connection]
wifi.cloned-mac-address=random
ethernet.cloned-mac-address=random
"""


def ghost_on():
    print(f"\n{G}{BOLD}  turning ghost mode on...{RS}\n")
    time.sleep(0.4)

    # kill any existing firewalls first so they dont conflict
    p("stopping other firewalls if any...", "run")
    for svc in ["firewalld", "ufw", "iptables"]:
        sh(f"systemctl stop {svc} 2>/dev/null")
        sh(f"systemctl disable {svc} 2>/dev/null")
    p("done", "ok")

    # write and apply nftables rules
    p("setting up nftables firewall...", "run")
    with open("/etc/nftables.conf", "w") as f:
        f.write(nft_config)
    sh("systemctl enable nftables 2>/dev/null")
    sh("systemctl restart nftables 2>/dev/null")
    sh("nft -f /etc/nftables.conf")  # apply directly too, nftables is oneshot
    p("firewall up — all inbound dropped", "ok")

    # kernel level stealth
    p("applying kernel stealth params...", "run")
    with open("/etc/sysctl.d/99-ghost.conf", "w") as f:
        f.write(sysctl_config)
    sh("sysctl --system 2>/dev/null")
    p("ping ignored, anti-spoof on, syn flood protection on", "ok")

    # randomize mac address on every wifi connect
    p("enabling mac randomization...", "run")
    os.makedirs("/etc/NetworkManager/conf.d", exist_ok=True)
    with open("/etc/NetworkManager/conf.d/ghost-mac.conf", "w") as f:
        f.write(mac_config)
    sh("systemctl restart NetworkManager 2>/dev/null")
    p("mac will be random on every connection", "ok")

    # kill services that announce your presence on the network
    p("killing noisy services (avahi, cups)...", "run")
    for svc in ["avahi-daemon", "cups", "cupsd"]:
        sh(f"systemctl stop {svc} 2>/dev/null")
        sh(f"systemctl disable {svc} 2>/dev/null")
    p("done", "ok")

    print(f"""
{G}
  ghost mode is ON 👻

  - firewall: all inbound dropped
  - port scanners: auto banned for 30 mins
  - ping: ignored
  - mac address: randomized
  - avahi/cups: killed

  if someone nmaps you they'll just see "host seems down"
{RS}""")


def ghost_off():
    print(f"\n{Y}{BOLD}  turning ghost mode off...{RS}\n")
    time.sleep(0.4)

    p("flushing nftables rules...", "run")
    sh("nft flush ruleset")
    sh("systemctl stop nftables 2>/dev/null")
    sh("systemctl disable nftables 2>/dev/null")
    p("firewall cleared", "ok")

    p("resetting kernel params...", "run")
    if os.path.exists("/etc/sysctl.d/99-ghost.conf"):
        os.remove("/etc/sysctl.d/99-ghost.conf")
    # explicitly reset ping ignore — just deleting the file isnt enough
    sh("sysctl -w net.ipv4.icmp_echo_ignore_all=0")
    sh("sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=0")
    sh("sysctl --system 2>/dev/null")
    p("kernel back to normal", "ok")

    p("removing mac randomization...", "run")
    mac_file = "/etc/NetworkManager/conf.d/ghost-mac.conf"
    if os.path.exists(mac_file):
        os.remove(mac_file)
    sh("systemctl restart NetworkManager 2>/dev/null")
    p("mac randomization off", "ok")

    p("re-enabling services...", "run")
    sh("systemctl enable --now avahi-daemon 2>/dev/null")
    p("services restored", "ok")

    print(f"""
{Y}
  ghost mode is OFF 🔓

  your machine is visible again
  firewall cleared, ping working, mac static
{RS}""")


def status():
    print(f"\n{C}{BOLD}  current status:{RS}\n")

    # check if our nft table is loaded (not systemctl — nftables is oneshot type)
    r = subprocess.run("nft list ruleset 2>/dev/null", shell=True, capture_output=True, text=True)
    if "ghost" in r.stdout:
        p("nftables firewall: ON 🔥", "ok")
    else:
        p("nftables firewall: OFF", "err")

    r = subprocess.run("sysctl net.ipv4.icmp_echo_ignore_all", shell=True, capture_output=True, text=True)
    if "= 1" in r.stdout:
        p("ping ignore: ON 👻", "ok")
    else:
        p("ping ignore: OFF", "warn")

    if os.path.exists("/etc/NetworkManager/conf.d/ghost-mac.conf"):
        p("mac randomization: ON", "ok")
    else:
        p("mac randomization: OFF", "warn")

    print(f"\n  {C}open ports right now:{RS}")
    sh_out("ss -tulnp | grep -v '127.0.0.1' | grep -v '::1'")

    print(f"\n  {C}network interfaces:{RS}")
    sh_out("ip -br addr show")


def banner():
    print(f"""
{G}{BOLD}
  2588258825882588258825882557 258825882557  258825882557 2588258825882588258825882557 25882588258825882588258825882557258825882588258825882588258825882557
  2588258825542550255025502550255d 258825882551  2588258825512588258825542550255025502588258825572588258825542550255025502550255d255a2550255025882588255425502550255d
  258825882551  258825882588255725882588258825882588258825882551258825882551   258825882551258825882588258825882557     258825882551   
  258825882551   25882588255125882588255425502550258825882551258825882551   25882588255125882588255425502550255d     258825882551   
  255a2588258825882588258825882554255d258825882551  258825882551255a2588258825882588258825882554255d25882588258825882588258825882557   258825882551   
   255a25502550255025502550255d 255a2550255d  255a2550255d 255a25502550255025502550255d 255a255025502550255025502550255d   255a2550255d   
{RS}{C}     make your linux machine invisible on any network{RS}
{G}                     by @VishalM{RS}
    """)

def banner():
    print(f"""
{G}{BOLD}
   ██████╗ ██╗  ██╗ ██████╗ ███████╗████████╗
  ██╔════╝ ██║  ██║██╔═══██╗██╔════╝╚══██╔══╝
  ██║  ███╗███████║██║   ██║███████╗   ██║   
  ██║   ██║██╔══██║██║   ██║╚════██║   ██║   
  ╚██████╔╝██║  ██║╚██████╔╝███████║   ██║   
   ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝   ╚═╝  
{RS}{C}      make your linux machine invisible on any network{RS}
{G}                      by @VishalM{RS}
    """)

def menu():
    banner()
    print(f"""
  {G}1{RS}  turn ghost mode ON
  {Y}2{RS}  turn ghost mode OFF
  {C}3{RS}  check status
  {R}4{RS}  exit
    """)

    choice = input(f"  pick one: ").strip()

    if choice == "1":
        confirm = input(f"\n  {Y}this will block all inbound connections. continue? (y/n): {RS}").strip().lower()
        if confirm == "y":
            ghost_on()
        else:
            p("cancelled", "warn")

    elif choice == "2":
        confirm = input(f"\n  {Y}your machine will be visible again. continue? (y/n): {RS}").strip().lower()
        if confirm == "y":
            ghost_off()
        else:
            p("cancelled", "warn")

    elif choice == "3":
        status()

    elif choice == "4":
        print(f"\n  {C}stay invisible — @VishalM{RS}\n")
        sys.exit(0)

    else:
        p("invalid choice", "err")
        menu()


if __name__ == "__main__":
    check_root()

    # can also use args directly: ghost.py on / off / status
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()
        if arg == "on":
            ghost_on()
        elif arg == "off":
            ghost_off()
        elif arg == "status":
            status()
        else:
            print(f"  usage: sudo python3 ghost.py [on/off/status]")
    else:
        menu()
