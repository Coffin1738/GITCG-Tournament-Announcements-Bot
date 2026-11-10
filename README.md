# GITCG-Tournament-Announcements-Bot

A bot to send and schedule announcements for online Genius Invokation TCG Tournaments hosted in discord

# Round Announcy Function (RoundAnnouncyGenerator.py)

A script that posts timed round announcements to a Discord channel through a webhook. 

No Discord bot or account automation is involved. 

## Features

- **Scheduled announcements.** Rounds 1 to 5 go out automatically, 35 minutes apart (previous round posts get deleted after the start of the current round).
- **Localized timestamps.** Uses Discord's 'UNIX' time formats which get generated based on the timezone of the machine running the script.
- **Live controls.** While the script runs, type a command in the terminal to start the next round early, pause, or resume.
- **Local log.** Every announcement is appended to `RoundAnnouncement2.txt` with a UTC generation timestamp.

## Example output

Rounds 1 to 4:

```
@Tournaments: Asia

Round 2 has begun!
It ends <t:1794141000:R> / <t:1794141000:t>
Inactivity losses will be handed out <t:1794139800:R> / <t:1794139800:t>

[Decklist Dump](<https://example.com/decks>)
```

Round 5 omits the "It ends" line, since it is the last round.

## Requirements

- Python 3.8 or newer
- A Discord webhook URL for the target channel
- Two packages:

```bash
pip install requests python-dotenv
```

## Setup

1. **Create a webhook.** In Discord, open the channel settings, then **Integrations > Webhooks > New Webhook**, and copy the webhook URL.

2. **Create a `.env` file** in the same folder as the script:

   ```
   WEBHOOK=https://discord.com/api/webhooks/your-webhook-id/your-webhook-token
   ```

   No quotes and no spaces around `=`. Make sure the file is saved. An unsaved `.env` is silently empty.

3. **Configure the event** in `main()`:

   - `decklist`: the link shown in the "Decklist Dump" line.
   - `regions`: a mapping of region names to Discord role IDs. To get a role ID, enable Developer Mode (User Settings > Advanced), then right-click the role and choose **Copy Role ID**.
   - `region`: which region from that mapping this run announces for.

## Usage

Run the script:

```bash
python main.py
```

You will be prompted for a region, version no., week no., starting round, and starting time:

```
Pick Region (Asia, America, Europe):
Please enter game version (7-0, 7-1, 7-2, etc.):
Please enter week no.:
Starting round (1-5, default will be 1 if input is invalid):
Set start time (HH:MM UTC, blank for next 5-min mark):
```
  
  - region field isn't case sensitive
  - game version format must follow (x-x) for it to be valid
  - week number as well
  - starting round time entered will be pushed up to the nearest xx:x5 minute mark (for internal consistency)

### Commands

While the script is running, type a command and press Enter:

| Command | Action |
|---|---|
| `s`, `skip`, `next` | Start the next round early. It is rescheduled to the next 5-minute mark, and all following rounds shift accordingly. |
| `p`, `pause` | Pause the schedule. Nothing is sent while paused. |
| `r`, `resume` | Resume. The upcoming round is rescheduled to the next 5-minute mark from now. |

## Limitations

- **The script must keep running.** If it exits mid-event, restart it and enter the round to resume from. Because the previous message ID is not saved, the earlier round's message will not be auto-deleted after a restart.
- **A retry can rarely post a duplicate** if Discord received the message but the response was lost. Delete the extra one by hand.
- **Pausing delays, not preserves, the schedule.** Resuming moves the next round to the next 5-minute mark rather than shifting the old schedule by the paused time.
