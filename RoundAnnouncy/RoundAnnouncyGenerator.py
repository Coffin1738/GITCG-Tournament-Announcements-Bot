import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone, timedelta
import requests
import time
import threading

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(env_path)
WEBHOOK_URL = os.getenv('WEBHOOK')

def strip_time(dt: datetime):
    return dt.replace(second=0, microsecond=0)

def next_5min(dt: datetime):
    return dt + timedelta(minutes=5 - dt.minute % 5)

class RoundAnnouncement:
    def __init__(self, round_no=1, region=0, decklist='None'):
        self.round_no = round_no
        self.region = region
        self.decklist = decklist
        self.start_time = strip_time(datetime.now(timezone.utc))
        self._update_times()
    
    def _update_times(self):
        self.end_time = self.start_time + timedelta(minutes=35)
        self.inactivity_time = self.start_time + timedelta(minutes=35)

    def next_round_limit(self):
        self.start_time += timedelta(minutes=35)
        self.round_no += 1
        self._update_times()
    
    def start_in_5(self):
        self.start_time = next_5min(self.start_time)
        self._update_times()

    def restart_from_now(self):
        self.start_time = strip_time(datetime.now(timezone.utc))
        self.start_in_5()

    def set_start_time(self, hour: int, minute: int):
        self.start_time = next_5min(self.start_time.replace(hour=hour,minute=minute))
        self._update_times()

    def __str__(self):
        if self.round_no == 5:
            return f'\n\n>>> <@&{self.region}>\n\n' + f'Round {self.round_no} has begun!\n' + f'Inactivity losses will be handed out <t:{int(self.inactivity_time.timestamp())}:R> / <t:{int(self.inactivity_time.timestamp())}:t>\n\n'+ f'[Decklist Dump](<{self.decklist}>)'
        return f'\n\n>>> <@&{self.region}>\n\n' + f'Round {self.round_no} has begun!\n' + f'It ends <t:{int(self.end_time.timestamp())}:R> / <t:{int(self.end_time.timestamp())}:t>\n' + f'Inactivity losses will be handed out <t:{int(self.inactivity_time.timestamp())}:R> / <t:{int(self.inactivity_time.timestamp())}:t>\n\n'+ f'[Decklist Dump](<{self.decklist}>)'

def log_announcement(log_ancmnt: str, path=Path(__file__).resolve().parent / 'RoundAnnouncement2.txt'):
    generated = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    with open(path, 'a', encoding='utf-8') as f:
        f.write(f'{"=" * 100}\n')
        f.write(f'Generated: {generated}\n')
        f.write(f'{log_ancmnt}\n\n')

def send_announcement(anncmnt: str):
    r = requests.post(
        WEBHOOK_URL,
        params={'wait': 'true'},
        json={'content': str(anncmnt).strip()},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()['id']

def delete_announcement(message_id: str):
    r = requests.delete(f'{WEBHOOK_URL}/messages/{message_id}', timeout=10)
    r.raise_for_status()

def send_with_retry(anncmnt: str, attempts=3):
    for i in range(attempts):
        try:
            return send_announcement(anncmnt)
        except requests.RequestException as e:
            print(f'Send failed ({e}), retry {i + 1}/{attempts}')
            time.sleep(5)
    raise RuntimeError('Could not send announcement')

skip_event = threading.Event()
running = threading.Event()
running.set()

def input_listener():
    while True:
        cmd = input().strip().lower()
        if cmd in ('s', 'skip', 'next'):
            skip_event.set()
            print('Skipped. next round now begins to the closest xx:x5')
        elif cmd in ('p', 'pause'):
            running.clear()
            print('Paused. Type "r" to resume.')
        elif cmd in ('r', 'resume'):
            running.set()
            print('Resumed.')

def sleep_until(target: datetime):
    while True:
        if not running.is_set():
            while not running.wait(timeout=1):
                pass
            skip_event.clear()
            return 'resumed'

        remaining = (target - datetime.now(timezone.utc)).total_seconds()
        if remaining <= 0:
            return 'arrived'
        if skip_event.wait(timeout=min(remaining, 1)):
            skip_event.clear()
            return 'skipped'

def main(): # Execute main program when there is less than 5 minutes left before tourney starts
    
    regions = {
        'asia': (1050374179167412234, 'as'),
        'america' : (1050374055196377089, 'na'),
        'europe' : (1050374169730232381, 'eu'),
    }
    
    region_name = input('Pick Region (Asia, America, Europe): ').lower()
    version = input('Please enter game version (7-0, 7-1, 7-2, etc.): ')
    week = input('Please enter week no.: ')
    reg = regions[region_name][1]
    region = regions[region_name][0]
    decklist = f'https://gitcg-community.vercel.app/en/weekly/{version}/{reg}/{week}/decks'
    
    try:
        start_round = int(input('Starting round (1-5, default will be 1 if input is invalid): ') or 1)
        if start_round > 5 or 1 > start_round:
            raise ValueError
    except ValueError:
        start_round = 1

    anncmnt = RoundAnnouncement(start_round, region, decklist)
    
    try:
        hour, minute = map(int, input('Set start time (HH:MM UTC, blank for next 5-min mark): ').split(':'))
        anncmnt.set_start_time(hour, minute)
    except ValueError:
        print('Invalid time, using the next 5-minute mark.')
        anncmnt.start_in_5()
    
    threading.Thread(target=input_listener, daemon=True).start()
    print("Type 's', 'p', 'r' to start, pause or resume the round.")

    previous_id = None

    while True:
        status = sleep_until(anncmnt.start_time)
        if status != 'arrived':
            anncmnt.restart_from_now()
            continue

        log_announcement(anncmnt)
        message_id = send_with_retry(anncmnt)
        skip_event.clear()

        if previous_id:
            try:
                delete_announcement(previous_id)
            except requests.RequestException as e:
                print(f'Could not delete previous message: {e}')
        previous_id = message_id

        if anncmnt.round_no >= 5:
            break
        anncmnt.next_round_limit()

    while sleep_until(anncmnt.end_time) != 'arrived':
        pass

    send_with_retry(f'## {region_name.capitalize()} Weekly Tournament is concluding...\n>>> Commencing end of announcements...\nSending regards to all remaining players...\n **[{region_name} Decklist Dump]({decklist}) <:kleesis:1098293491278286878>**') 
    
    try:
        delete_announcement(previous_id)
    except requests.RequestException as e:
        print(f'Could not delete final round message: {e}')
    
    print('Closing message sent. Done.')

if __name__ == "__main__":
    main()
