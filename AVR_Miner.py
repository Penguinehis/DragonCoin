#!/usr/bin/env python3
"""
This is a fork / Mod of the:

Duino-Coin Official AVR Miner 4.2 © MIT licensed
https://duinocoin.com
https://github.com/revoxhere/duino-coin
Duino-Coin Team & Community 2019-2024
"""

from os import _exit, mkdir
from os import name as osname
from os import path
from os import system as ossystem
from platform import machine as osprocessor
from platform import system
import sys

from configparser import ConfigParser
from pathlib import Path

from json import load as jsonload
from random import choice
from locale import LC_ALL, getdefaultlocale, getlocale, setlocale
import zipfile

from re import sub
from socket import socket
from datetime import datetime
from statistics import mean
from signal import SIGINT, signal
from time import ctime, sleep, strptime, time
import pip

from subprocess import DEVNULL, Popen, check_call, call
from threading import Thread
from threading import Lock as thread_lock
from threading import Semaphore

import base64 as b64

import os

printlock = Semaphore(value=1)


# Python <3.5 check
f"Your Python version is too old. DragonCoin Miner requires version 3.6 or above. Update your packages and try again"


def install(package):
    try:
        pip.main(["install", package])
    except AttributeError:
        check_call([sys.executable, "-m", "pip", "install", package])
    call([sys.executable, __file__])


try:
    from serial import Serial
    import serial.tools.list_ports
except ModuleNotFoundError:
    print(
        "Pyserial is not installed. "
        + "Miner will try to automatically install it "
        + "If it fails, please manually execute "
        + "python3 -m pip install pyserial"
    )
    install("pyserial")

try:
    import requests
except ModuleNotFoundError:
    print(
        "Requests is not installed. "
        + "Miner will try to automatically install it "
        + "If it fails, please manually execute "
        + "python3 -m pip install requests"
    )
    install("requests")

try:
    from colorama import Back, Fore, Style, init

    init(autoreset=True)
except ModuleNotFoundError:
    print(
        "Colorama is not installed. "
        + "Miner will try to automatically install it "
        + "If it fails, please manually execute "
        + "python3 -m pip install colorama"
    )
    install("colorama")

try:
    from pypresence import Presence
except ModuleNotFoundError:
    print(
        "Pypresence is not installed. "
        + "Miner will try to automatically install it "
        + "If it fails, please manually execute "
        + "python3 -m pip install pypresence"
    )
    install("pypresence")

try:
    import psutil
except ModuleNotFoundError:
    print(
        "Psutil is not installed. "
        + "Miner will try to automatically install it "
        + "If it fails, please manually execute "
        + "python3 -m pip install psutil"
    )
    install("psutil")


def now():
    return datetime.now()


def port_num(com):
    return str("".join(filter(str.isdigit, com)))


class Settings:
    VER = "4.2"
    SOC_TIMEOUT = 15
    REPORT_TIME = 120
    AVR_TIMEOUT = 10
    BAUDRATE = 115200
    DATA_DIR = "DragonCoin AVR Miner " + str(VER)
    SEPARATOR = ","
    ENCODING = "utf-8"
    TEMP_FOLDER = "Temp"

    try:
        # Raspberry Pi latin users can't display this character
        "‖".encode(sys.stdout.encoding)
        BLOCK = " ‖ "
    except:
        BLOCK = " | "
    PICK = ""
    COG = " @"
    if osname != "nt" or bool(osname == "nt" and os.environ.get("WT_SESSION")):
        # Windows' cmd does not support emojis, shame!
        # And some codecs same, for example the Latin-1 encoding don`t support emoji
        try:
            "⛏ ⚙".encode(sys.stdout.encoding)  # if the terminal support emoji
            PICK = " ⛏"
            COG = " ⚙"
        except UnicodeEncodeError:  # else
            PICK = ""
            COG = " @"


class Client:
    """
    Class helping to organize socket connections
    """

    def connect(pool: tuple):
        s = socket()
        s.settimeout(Settings.SOC_TIMEOUT)
        s.connect((pool))
        return s

    def send(s, msg: str):
        sent = s.sendall(str(msg).encode(Settings.ENCODING))
        return True

    def recv(s, limit: int = 128):
        data = s.recv(limit).decode(Settings.ENCODING).rstrip("\n")
        return data

    def fetch_pool():
        NODE_ADDRESS = "134.65.226.191"
        NODE_PORT = 6000

        return (NODE_ADDRESS, NODE_PORT)


shares = [0, 0, 0]
hashrate_mean = []
ping_mean = []
diff = 0
donator_running = False
job = ""
debug = "n"
discord_presence = "y"
rig_identifier = "None"
donation_level = 0
hashrate = 0
config = ConfigParser()
mining_start_time = time()

if not path.exists(Settings.DATA_DIR):
    mkdir(Settings.DATA_DIR)

if not Path(Settings.DATA_DIR + "/Translations.json").is_file():
    url = (
        "https://raw.githubusercontent.com/"
        + "Penguinehis/"
        + "DragonCoin/master/Resources/"
        + "AVR_Miner_langs.json"
    )
    r = requests.get(url, timeout=5)
    with open(Settings.DATA_DIR + "/Translations.json", "wb") as f:
        f.write(r.content)

# Load language file
with open(Settings.DATA_DIR + "/Translations.json", "r", encoding="utf8") as lang_file:
    lang_file = jsonload(lang_file)

# OS X invalid locale hack
if system() == "Darwin":
    if getlocale()[0] is None:
        setlocale(LC_ALL, "en_US.UTF-8")

try:
    if not Path(Settings.DATA_DIR + "/Settings.cfg").is_file():
        locale = getdefaultlocale()[0]
        if locale.startswith("es"):
            lang = "spanish"
        elif locale.startswith("sk"):
            lang = "slovak"
        elif locale.startswith("ru"):
            lang = "russian"
        elif locale.startswith("pl"):
            lang = "polish"
        elif locale.startswith("de"):
            lang = "german"
        elif locale.startswith("fr"):
            lang = "french"
        elif locale.startswith("jp"):
            lang = "japanese"
        elif locale.startswith("tr"):
            lang = "turkish"
        elif locale.startswith("it"):
            lang = "italian"
        elif locale.startswith("pt"):
            lang = "portuguese"
        if locale.startswith("zh_TW"):
            lang = "chinese_Traditional"
        elif locale.startswith("zh"):
            lang = "chinese_simplified"
        elif locale.startswith("th"):
            lang = "thai"
        elif locale.startswith("az"):
            lang = "azerbaijani"
        elif locale.startswith("nl"):
            lang = "dutch"
        elif locale.startswith("ko"):
            lang = "korean"
        elif locale.startswith("id"):
            lang = "indonesian"
        elif locale.startswith("cz"):
            lang = "czech"
        elif locale.startswith("fi"):
            lang = "finnish"
        else:
            lang = "english"
    else:
        try:
            config.read(Settings.DATA_DIR + "/Settings.cfg")
            lang = config["AVR Miner"]["language"]
        except Exception:
            lang = "english"
except:
    lang = "english"


def get_string(string_name: str):
    if string_name in lang_file[lang]:
        return lang_file[lang][string_name]
    elif string_name in lang_file["english"]:
        return lang_file["english"][string_name]
    else:
        return string_name


def get_prefix(symbol: str, val: float, accuracy: int):
    """
    H/s, 1000 => 1 kH/s
    """
    if val >= 1_000_000_000_000:  # Really?
        val = str(round((val / 1_000_000_000_000), accuracy)) + " T"
    elif val >= 1_000_000_000:
        val = str(round((val / 1_000_000_000), accuracy)) + " G"
    elif val >= 1_000_000:
        val = str(round((val / 1_000_000), accuracy)) + " M"
    elif val >= 1_000:
        val = str(round((val / 1_000))) + " k"
    else:
        if symbol:
            val = str(round(val)) + " "
        else:
            val = str(round(val))
    return val + symbol


def debug_output(text: str):
    if debug == "y":
        print(
            Style.RESET_ALL
            + Fore.WHITE
            + now().strftime(Style.DIM + "%H:%M:%S.%f ")
            + Style.NORMAL
            + f"DEBUG: {text}"
        )


def title(title: str):
    if osname == "nt":
        """
        Changing the title in Windows' cmd
        is easy - just use the built-in
        title command
        """
        ossystem("title " + title)
    else:
        """
        Most *nix terminals use
        this escape sequence to change
        the console window title
        """
        try:
            print("\33]0;" + title + "\a", end="")
            sys.stdout.flush()
        except Exception as e:
            debug_output("Error setting title: " + str(e))


def handler(signal_received, frame):
    pretty_print(
        "sys0",
        get_string("sigint_detected")
        + Style.NORMAL
        + Fore.RESET
        + get_string("goodbye"),
        "warning",
    )

    _exit(0)


# Enable signal handler
signal(SIGINT, handler)


def load_config():
    global username
    global donation_level
    global avrport
    global hashrate_list
    global debug
    global rig_identifier
    global discord_presence
    global SOC_TIMEOUT

    if not Path(str(Settings.DATA_DIR) + "/Settings.cfg").is_file():
        print(
            Style.BRIGHT
            + get_string("basic_config_tool")
            + Settings.DATA_DIR
            + get_string("edit_config_file_warning")
        )
        username = input(
            Style.RESET_ALL
            + Fore.YELLOW
            + get_string("ask_username")
            + Fore.RESET
            + Style.BRIGHT
        )
        print(
            Style.RESET_ALL
            + get_string("dont_have_account")
            + Fore.YELLOW
            + get_string("wallet")
            + Fore.RESET
            + get_string("register_warning")
        )

        print(Style.RESET_ALL + Fore.YELLOW + get_string("ports_message"))
        portlist = serial.tools.list_ports.comports(include_links=True)

        for port in portlist:
            print(Style.RESET_ALL + Style.BRIGHT + Fore.RESET + "  " + str(port))
        print(Style.RESET_ALL + Fore.YELLOW + get_string("ports_notice"))

        port_names = []
        for port in portlist:
            port_names.append(port.device)

        avrport = ""
        rig_identifier = ""
        while True:
            current_port = input(
                Style.RESET_ALL
                + Fore.YELLOW
                + get_string("ask_avrport")
                + Fore.RESET
                + Style.BRIGHT
            )

            if current_port in port_names:
                confirm_identifier = input(
                    Style.RESET_ALL
                    + Fore.YELLOW
                    + get_string("ask_rig_identifier")
                    + Fore.RESET
                    + Style.BRIGHT
                )
                if confirm_identifier == "y" or confirm_identifier == "Y":
                    current_identifier = input(
                        Style.RESET_ALL
                        + Fore.YELLOW
                        + get_string("ask_rig_name")
                        + Fore.RESET
                        + Style.BRIGHT
                    )
                    rig_identifier += current_identifier
                else:
                    rig_identifier += "None"

                avrport += current_port
                confirmation = input(
                    Style.RESET_ALL
                    + Fore.YELLOW
                    + get_string("ask_anotherport")
                    + Fore.RESET
                    + Style.BRIGHT
                )
                if confirmation == "y" or confirmation == "Y":
                    avrport += ","
                    rig_identifier += ","
                else:
                    break
            else:
                print(
                    Style.RESET_ALL
                    + Fore.RED
                    + "Please enter a valid COM port from the list above"
                )

        else:
            rig_identifier = "None"

        config["AVR Miner"] = {
            "username": username,
            "avrport": avrport,
            "language": lang,
            "identifier": rig_identifier,
            "debug": "n",
            "soc_timeout": 45,
            "avr_timeout": 10,
            "discord_presence": "y",
            "periodic_report": 60,
        }

        with open(str(Settings.DATA_DIR) + "/Settings.cfg", "w") as configfile:
            config.write(configfile)

        avrport = avrport.split(",")
        rig_identifier = rig_identifier.split(",")
        print(Style.RESET_ALL + get_string("config_saved"))
        hashrate_list = [0] * len(avrport)

    else:
        config.read(str(Settings.DATA_DIR) + "/Settings.cfg")
        username = config["AVR Miner"]["username"]
        avrport = config["AVR Miner"]["avrport"]
        avrport = avrport.replace(" ", "").split(",")
        debug = config["AVR Miner"]["debug"]
        rig_identifier = config["AVR Miner"]["identifier"].split(",")
        Settings.SOC_TIMEOUT = int(config["AVR Miner"]["soc_timeout"])
        Settings.AVR_TIMEOUT = float(config["AVR Miner"]["avr_timeout"])
        discord_presence = config["AVR Miner"]["discord_presence"]
        Settings.REPORT_TIME = int(config["AVR Miner"]["periodic_report"])
        hashrate_list = [0] * len(avrport)


def greeting():
    global greeting
    print(Style.RESET_ALL)

    current_hour = strptime(ctime(time())).tm_hour
    if current_hour < 12:
        greeting = get_string("greeting_morning")
    elif current_hour == 12:
        greeting = get_string("greeting_noon")
    elif current_hour > 12 and current_hour < 18:
        greeting = get_string("greeting_afternoon")
    elif current_hour >= 18:
        greeting = get_string("greeting_evening")
    else:
        greeting = get_string("greeting_back")

    print(
        Style.DIM
        + Fore.MAGENTA
        + Settings.BLOCK
        + Fore.YELLOW
        + Style.BRIGHT
        + get_string("banner")
        + Style.RESET_ALL
        + Fore.MAGENTA
        + f" {Settings.VER}"
        + Fore.RESET
        + " 2019-2024"
    )

    print(
        Style.DIM
        + Fore.MAGENTA
        + Settings.BLOCK
        + Style.NORMAL
        + Fore.MAGENTA
        + "https://github.com/Penguinehis/DragonCoin"
    )

    if lang != "english":
        print(
            Style.DIM
            + Fore.MAGENTA
            + Settings.BLOCK
            + Style.NORMAL
            + Fore.RESET
            + lang.capitalize()
            + " translation: "
            + Fore.MAGENTA
            + get_string("translation_autor")
        )

    print(
        Style.DIM
        + Fore.MAGENTA
        + Settings.BLOCK
        + Style.NORMAL
        + Fore.RESET
        + get_string("avr_on_port")
        + Style.BRIGHT
        + Fore.YELLOW
        + ", ".join(avrport)
    )

    if osname == "nt" or osname == "posix":
        print(
            Style.DIM
            + Fore.MAGENTA
            + Settings.BLOCK
            + Style.NORMAL
            + Fore.RESET
            + get_string("donation_level")
            + Style.BRIGHT
            + Fore.YELLOW
            + str(donation_level)
        )

    print(
        Style.DIM
        + Fore.MAGENTA
        + Settings.BLOCK
        + Style.NORMAL
        + Fore.RESET
        + get_string("algorithm")
        + Style.BRIGHT
        + Fore.YELLOW
        + "DUCO-S1A ⚙ AVR diff"
    )

    if rig_identifier[0] != "None" or len(rig_identifier) > 1:
        print(
            Style.DIM
            + Fore.MAGENTA
            + Settings.BLOCK
            + Style.NORMAL
            + Fore.RESET
            + get_string("rig_identifier")
            + Style.BRIGHT
            + Fore.YELLOW
            + ", ".join(rig_identifier)
        )

    print(
        Style.DIM
        + Fore.MAGENTA
        + Settings.BLOCK
        + Style.NORMAL
        + Fore.RESET
        + get_string("using_config")
        + Style.BRIGHT
        + Fore.YELLOW
        + str(Settings.DATA_DIR + "/Settings.cfg")
    )

    print(
        Style.DIM
        + Fore.MAGENTA
        + Settings.BLOCK
        + Style.NORMAL
        + Fore.RESET
        + str(greeting)
        + ", "
        + Style.BRIGHT
        + Fore.YELLOW
        + str(username)
        + "!\n"
    )


def init_rich_presence():
    # Initialize Discord rich presence
    global RPC
    try:
        RPC = Presence(905158274490441808)
        RPC.connect()
        Thread(target=update_rich_presence).start()
    except Exception as e:
        # print("Error launching Discord RPC thread: " + str(e))
        pass


def update_rich_presence():
    startTime = int(time())
    while True:
        try:
            total_hashrate = get_prefix("H/s", sum(hashrate_list), 2)
            RPC.update(
                details="Hashrate: " + str(total_hashrate),
                start=mining_start_time,
                state=str(shares[0])
                + "/"
                + str(shares[0] + shares[1])
                + " accepted shares",
                large_image="avrminer",
                large_text="DragonCoin, "
                + "a coin that can be mined with almost everything"
                + ", including AVR boards",
                buttons=[
                    {"label": "Visit duinocoin.com", "url": "https://duinocoin.com"},
                    {"label": "Join the Discord", "url": "https://discord.gg/k48Ht5y"},
                ],
            )
        except Exception as e:
            print("Error updating Discord RPC thread: " + str(e))

        sleep(15)


def pretty_print(sender: str = "sys0", msg: str = None, state: str = "success"):
    """
    Produces nicely formatted CLI output for messages:
    HH:MM:S |sender| msg
    """
    if sender.startswith("net"):
        bg_color = Back.BLUE
    elif sender.startswith("avr"):
        bg_color = Back.MAGENTA
    else:
        bg_color = Back.GREEN

    if state == "success":
        fg_color = Fore.GREEN
    elif state == "info":
        fg_color = Fore.BLUE
    elif state == "error":
        fg_color = Fore.RED
    else:
        fg_color = Fore.YELLOW

    print_queue.append(
        Fore.RESET
        + datetime.now().strftime(Style.DIM + "%H:%M:%S ")
        + Style.RESET_ALL
        + Fore.WHITE
        + bg_color
        + Style.BRIGHT
        + f" {sender} "
        + Style.RESET_ALL
        + " "
        + fg_color
        + msg.strip()
    )


def share_print(
    id,
    type,
    accept,
    reject,
    thread_hashrate,
    total_hashrate,
    computetime,
    diff,
    ping,
    reject_cause=None,
):
    """
    Produces nicely formatted CLI output for shares:
    HH:MM:S |avrN| ⛏ Accepted 0/0 (100%) ∙ 0.0s ∙ 0 kH/s ⚙ diff 0 k ∙ ping 0ms
    """
    thread_hashrate = get_prefix("H/s", thread_hashrate, 2)
    total_hashrate = get_prefix("H/s", total_hashrate, 1)

    if type == "accept":
        share_str = get_string("accepted")
        fg_color = Fore.GREEN
    elif type == "block":
        share_str = get_string("block_found")
        fg_color = Fore.YELLOW
    else:
        share_str = get_string("rejected")
        if reject_cause:
            share_str += f"{Style.NORMAL}({reject_cause}) "
        fg_color = Fore.RED

    print_queue.append(
        Fore.RESET
        + datetime.now().strftime(Style.DIM + "%H:%M:%S ")
        + Style.RESET_ALL
        + Fore.WHITE
        + Style.BRIGHT
        + Back.MAGENTA
        + " avr"
        + str(id)
        + " "
        + Style.RESET_ALL
        + fg_color
        + Settings.PICK
        + share_str
        + Fore.RESET
        + str(accept)
        + "/"
        + str(accept + reject)
        + Fore.MAGENTA
        + " ("
        + str(round(accept / (accept + reject) * 100))
        + "%)"
        + Style.NORMAL
        + Fore.RESET
        + " ∙ "
        + str("%04.1f" % float(computetime))
        + "s"
        + Style.NORMAL
        + " ∙ "
        + Fore.BLUE
        + Style.BRIGHT
        + f"{thread_hashrate}"
        + Style.DIM
        + f" ({total_hashrate} {get_string('hashrate_total')})"
        + Fore.RESET
        + Style.NORMAL
        + Settings.COG
        + f" {get_string('diff')} {diff} ∙ "
        + Fore.CYAN
        + f"ping {(int(ping))}ms"
    )


def mine_avr(com, threadid, fastest_pool, thread_rigid):
    global hashrate, shares
    start_time = time()
    report_shares = 0
    last_report_share = 0
    while True:
        shares = [0, 0, 0]
        while True:
            try:
                ser.close()
                pretty_print(
                    "sys" + port_num(com),
                    f"No response from the board. Closed port {com}",
                    "success",
                )
                sleep(2)
            except:
                pass
            try:
                ser = Serial(
                    com,
                    baudrate=int(Settings.BAUDRATE),
                    timeout=int(Settings.AVR_TIMEOUT),
                )
                """
                Sleep after opening the port to make
                sure the board resets properly after
                receiving the DTR signal
                """
                sleep(2)
                break
            except Exception as e:
                pretty_print(
                    "sys" + port_num(com),
                    get_string("board_connection_error")
                    + str(com)
                    + get_string("board_connection_error2")
                    + Style.NORMAL
                    + Fore.RESET
                    + f" (avr connection err: {e})",
                    "error",
                )
                sleep(10)

        retry_counter = 0
        while True:
            try:
                if retry_counter > 3:
                    fastest_pool = Client.fetch_pool()
                    retry_counter = 0

                debug_output(f"Connecting to {fastest_pool}")
                s = Client.connect(fastest_pool)
                server_version = Client.recv(s, 6)

                if threadid == 0:
                    if float(server_version) <= float(Settings.VER):
                        pretty_print(
                            "net0",
                            get_string("connected")
                            + Style.NORMAL
                            + Fore.RESET
                            + get_string("connected_server")
                            + str(server_version)
                            + ")",
                            "success",
                        )
                    else:
                        pretty_print(
                            "sys0",
                            f"{get_string('miner_is_outdated')} (v{Settings.VER}) -"
                            + get_string("server_is_on_version")
                            + server_version
                            + Style.NORMAL
                            + Fore.RESET
                            + get_string("update_warning"),
                            "warning",
                        )
                        sleep(10)

                    Client.send(s, "MOTD")
                    motd = Client.recv(s, 1024)

                    if "\n" in motd:
                        motd = motd.replace("\n", "\n\t\t")

                    pretty_print(
                        "net" + str(threadid),
                        get_string("motd") + Fore.RESET + Style.NORMAL + str(motd),
                        "success",
                    )
                break
            except Exception as e:
                pretty_print(
                    "net0",
                    get_string("connecting_error")
                    + Style.NORMAL
                    + f" (connection err: {e})",
                    "error",
                )
                retry_counter += 1
                sleep(10)

        pretty_print(
            "sys" + port_num(com),
            get_string("mining_start")
            + Style.NORMAL
            + Fore.RESET
            + get_string("mining_algorithm")
            + str(com)
            + ")",
            "success",
        )

        # Perform a hash test to assign the starting diff
        prev_hash = "ba29a15896fd2d792d5c4b60668bf2b9feebc51d"
        exp_hash = "d0beba883d7e8cd119ea2b0e09b78f60f29e0968"
        exp_result = 50
        retries = 0
        while retries < 3:
            try:
                debug_output(com + ": Sending hash test to the board")
                ser.write(
                    bytes(
                        str(
                            prev_hash
                            + Settings.SEPARATOR
                            + exp_hash
                            + Settings.SEPARATOR
                            + "10"
                            + Settings.SEPARATOR
                        ),
                        encoding=Settings.ENCODING,
                    )
                )
                debug_output(com + ": Reading hash test from the board")
                result = ser.read_until(b"\n").decode().strip().split(",")
                ser.flush()

                if result[0] and result[1]:
                    _ = int(result[0], 2)
                    debug_output(com + f": Result: {result[0]}")
                else:
                    raise Exception("No data received from the board")
                if int(result[0], 2) != exp_result:
                    raise Exception(com + f": Incorrect result received!")

                computetime = round(int(result[1], 2) / 1000000, 5)
                num_res = int(result[0], 2)
                hashrate_test = round(num_res / computetime, 2)
                break
            except Exception as e:
                debug_output(str(e))
                retries += 1
        else:
            pretty_print(
                "sys" + port_num(com),
                f"Can't start mining on {com}"
                + Fore.RESET
                + f" - board keeps responding improperly. "
                + "Check if the code has been uploaded correctly "
                + "and your device is supported by DragonCoin.",
                "error",
            )
            break

        start_diff = "AVR"
        if hashrate_test > 1000:
            start_diff = "DUE"
        elif hashrate_test > 550:
            start_diff = "ARM"
        elif hashrate_test > 380:
            start_diff = "MEGA"

        pretty_print(
            "sys" + port_num(com),
            get_string("hashrate_test")
            + get_prefix("H/s", hashrate_test, 2)
            + Fore.RESET
            + Style.BRIGHT
            + get_string("hashrate_test_diff")
            + start_diff,
        )

        while True:
            try:

                debug_output(com + ": Requesting job")
                Client.send(
                    s,
                    "JOB"
                    + Settings.SEPARATOR
                    + str(username)
                    + Settings.SEPARATOR
                    + start_diff
                    + Settings.SEPARATOR,
                )
                job = Client.recv(s, 128).split(Settings.SEPARATOR)
                debug_output(com + f": Received: {job[0]}")

                try:
                    diff = int(job[2])
                except:
                    pretty_print(
                        "sys" + port_num(com), f" Node message: {job[1]}", "warning"
                    )
                    sleep(3)
            except Exception as e:
                pretty_print(
                    "net" + port_num(com),
                    get_string("connecting_error")
                    + Style.NORMAL
                    + Fore.RESET
                    + f" (err handling result: {e})",
                    "error",
                )
                sleep(3)
                break

            retry_counter = 0
            while True:
                if retry_counter > 3:
                    break

                try:
                    debug_output(com + ": Sending job to the board")
                    ser.write(
                        bytes(
                            str(
                                job[0]
                                + Settings.SEPARATOR
                                + job[1]
                                + Settings.SEPARATOR
                                + job[2]
                                + Settings.SEPARATOR
                            ),
                            encoding=Settings.ENCODING,
                        )
                    )
                    debug_output(com + ": Reading result from the board")
                    result = ser.read_until(b"\n").decode().strip().split(",")

                    if result[0] and result[1]:
                        _ = int(result[0], 2)
                        debug_output(com + f": Result: {result[0]}")
                        break
                    else:
                        raise Exception("No data received from AVR")
                except Exception as e:
                    debug_output(com + f": Retrying data read: {e}")
                    ser.flush()
                    retry_counter += 1
                    continue

            if retry_counter > 3:
                break

            try:
                computetime = round(int(result[1], 2) / 1000000, 5)
                num_res = int(result[0], 2)
                hashrate_t = round(num_res / computetime, 2)

                hashrate_mean.append(hashrate_t)
                hashrate = mean(hashrate_mean[-5:])
                hashrate_list[threadid] = hashrate
                total_hashrate = sum(hashrate_list)
            except Exception as e:
                pretty_print(
                    "sys" + port_num(com),
                    get_string("mining_avr_connection_error")
                    + Style.NORMAL
                    + Fore.RESET
                    + " (no response from the board: "
                    + f"{e}, please check the connection, "
                    + "port setting or reset the AVR)",
                    "warning",
                )
                break

            try:
                Client.send(
                    s,
                    str(num_res)
                    + Settings.SEPARATOR
                    + str(hashrate_t)
                    + Settings.SEPARATOR
                    + f"Official AVR Miner {Settings.VER}"
                    + Settings.SEPARATOR
                    + str(thread_rigid)
                    + Settings.SEPARATOR
                    + str(result[2]),
                )

                responsetimetart = now()
                feedback = Client.recv(s, 64).split(",")
                responsetimestop = now()

                time_delta = (responsetimestop - responsetimetart).microseconds
                ping_mean.append(round(time_delta / 1000))
                ping = mean(ping_mean[-10:])
                diff = get_prefix("", int(diff), 0)
                debug_output(com + f': retrieved feedback: {" ".join(feedback)}')
            except Exception as e:
                pretty_print(
                    "net" + port_num(com),
                    get_string("connecting_error")
                    + Style.NORMAL
                    + Fore.RESET
                    + f" (err handling result: {e})",
                    "error",
                )
                debug_output(com + f": error parsing response: {e}")
                sleep(5)
                break

            if feedback[0] == "GOOD":
                shares[0] += 1
                share_print(
                    port_num(com),
                    "accept",
                    shares[0],
                    shares[1],
                    hashrate,
                    total_hashrate,
                    computetime,
                    diff,
                    ping,
                )

            elif feedback[0] == "BLOCK":
                shares[0] += 1
                shares[2] += 1
                share_print(
                    port_num(com),
                    "block",
                    shares[0],
                    shares[1],
                    hashrate,
                    total_hashrate,
                    computetime,
                    diff,
                    ping,
                )

            elif feedback[0] == "BAD":
                shares[1] += 1
                share_print(
                    port_num(com),
                    "reject",
                    shares[0],
                    shares[1],
                    hashrate,
                    total_hashrate,
                    computetime,
                    diff,
                    ping,
                    feedback[1],
                )

            else:
                share_print(
                    port_num(com),
                    "reject",
                    shares[0],
                    shares[1],
                    hashrate,
                    total_hashrate,
                    computetime,
                    diff,
                    ping,
                    feedback,
                )

            if shares[0] % 100 == 0 and shares[0] > 1:
                pretty_print(
                    "sys0",
                    f"{get_string('surpassed')} {shares[0]} {get_string('surpassed_shares')}",
                    "success",
                )

            title(
                get_string("duco_avr_miner")
                + str(Settings.VER)
                + f") - {shares[0]}/{(shares[0] + shares[1])}"
                + get_string("accepted_shares")
            )

            end_time = time()
            elapsed_time = end_time - start_time
            if threadid == 0 and elapsed_time >= Settings.REPORT_TIME:
                report_shares = shares[0] - last_report_share
                uptime = calculate_uptime(mining_start_time)

                periodic_report(
                    start_time, end_time, report_shares, shares[2], hashrate, uptime
                )
                start_time = time()
                last_report_share = shares[0]


def periodic_report(start_time, end_time, shares, blocks, hashrate, uptime):
    """
    Displays nicely formated uptime stats
    """
    seconds = round(end_time - start_time)
    pretty_print(
        "sys0",
        get_string("periodic_mining_report")
        + Fore.RESET
        + Style.NORMAL
        + get_string("report_period")
        + str(seconds)
        + get_string("report_time")
        + get_string("report_body1")
        + str(shares)
        + get_string("report_body2")
        + str(round(shares / seconds, 1))
        + get_string("report_body3")
        + get_string("report_body7")
        + str(blocks)
        + get_string("report_body4")
        + str(get_prefix("H/s", hashrate, 2))
        + get_string("report_body5")
        + str(int(hashrate * seconds))
        + get_string("report_body6")
        + get_string("total_mining_time")
        + str(uptime)
        + "\n",
        "success",
    )


def calculate_uptime(start_time):
    uptime = time() - start_time
    if uptime >= 7200:  # 2 hours, plural
        return str(uptime // 3600) + get_string("uptime_hours")
    elif uptime >= 3600:  # 1 hour, not plural
        return str(uptime // 3600) + get_string("uptime_hour")
    elif uptime >= 120:  # 2 minutes, plural
        return str(uptime // 60) + get_string("uptime_minutes")
    elif uptime >= 60:  # 1 minute, not plural
        return str(uptime // 60) + get_string("uptime_minute")
    else:  # less than 1 minute
        return str(round(uptime)) + get_string("uptime_seconds")


print_queue = []


def print_queue_handler():
    """
    Prevents broken console logs with many threads
    """
    while True:
        if len(print_queue):
            message = print_queue[0]
            del print_queue[0]
            print(message)
        sleep(0.1)


if __name__ == "__main__":
    init(autoreset=True)
    Thread(target=print_queue_handler).start()
    title(f"{get_string('duco_avr_miner')}{str(Settings.VER)})")

    if sys.platform == "win32":
        os.system("")  # Enable VT100 Escape Sequence for WINDOWS 10 Ver. 1607

    try:
        load_config()
        debug_output("Config file loaded")
    except Exception as e:
        pretty_print(
            "sys0",
            get_string("load_config_error")
            + Settings.DATA_DIR
            + get_string("load_config_error_warning")
            + Style.NORMAL
            + Fore.RESET
            + f" ({e})",
            "error",
        )
        debug_output(f"Error reading configfile: {e}")
        sleep(10)
        _exit(1)

    try:
        greeting()
        debug_output("Greeting displayed")
    except Exception as e:
        debug_output(f"Error displaying greeting message: {e}")

    try:
        fastest_pool = Client.fetch_pool()
        threadid = 0
        for port in avrport:
            Thread(
                target=mine_avr,
                args=(port, threadid, fastest_pool, rig_identifier[threadid]),
            ).start()
            threadid += 1
    except Exception as e:
        debug_output(f"Error launching AVR thread(s): {e}")

    if discord_presence == "y":
        try:
            init_rich_presence()
        except Exception as e:
            debug_output(f"Error launching Discord RPC thread: {e}")
