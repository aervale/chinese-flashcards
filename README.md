# Chinese Flashcards

A flashcard app I built to study my second-year Chinese vocab. It's a single HTML
file with no build step or dependencies — just open `index.html` in a browser.

I originally kept all of this in a Google Sheet that used a spaced-repetition
system, and rebuilt it here so it's nicer to use and works on my phone.

## How it works

Every word lives in one of five buckets:

```
Daily  →  Bidaily  →  Weekly  →  Retired        Archive
```

- Answer a card correctly and it moves up a level (Daily → Bidaily → … → Retired).
- Miss it and it drops back down and gets shown again before the round ends.
- **Archive** is the backlog — words I haven't started drilling yet. When I've
  mastered my current set I move a few of these into Daily.

The study queue is weighted toward words I've missed most, so the stuff I'm bad
at comes up more often.

## Features

- Study by character (汉字 → meaning) or by meaning (meaning → 汉字).
- **Practice sets** — instead of drilling a whole bucket, you pick which buckets
  to draw from and how many words (e.g. 50 from Daily + Bidaily), and train only
  that subset. A **Weakest** button builds the set from your lowest-accuracy
  words instead. The set is saved per profile and persists until you reset it.
- Audio for every word and example sentence — clips are stored in `audio/`, so
  pronunciation works fully offline.
- Optional compound-word quizzing, limited to compounds whose characters are all
  in your current practice set.
- Per-word stats (correct / missed / accuracy) and a searchable, sortable list
  of all ~2,600 words.
- Add your own words, move words between buckets, reset stats per word or globally.
- Light and dark themes.
- An RPG layer: XP and levels, a customizable character, and attributes that
  level up as you study (Power, Consistency, Memory, Wisdom, Focus, Diligence).
- Multiple profiles, each with its own save file and character. A new profile
  starts from scratch — every word in the Archive backlog, level 1, attributes 0.
  Creating one never touches other profiles.
- Progress is saved in the browser and can be exported to / imported from a CSV.
  Each profile saves to its own file, named `progress_<profile>_<date>.csv`,
  kept locally in a `checkpoints/` folder (git-ignored — not published).
- Words are organized into batches by how well you know them: Learning →
  Reviewing → Familiar → Mastered, plus an Archive backlog. A new profile starts
  with a default deck of the 10 most common words in Learning.

## Data

- Word list, buckets, HSK levels and frequency ranks come from my own sheet.
- Definitions are padded out with common compounds (组词) and example sentences
  so each entry shows how the character is actually used.
- Audio is pre-rendered Mandarin TTS, generated with [Piper](https://github.com/rhasspy/piper)
  using the `zh_CN-chaowen-medium` voice. That voice is trained on a CC0
  (public-domain) dataset, so the clips are free to use and redistribute with no
  attribution required. The script that regenerates them is `generate_audio_colab.py`.

## Notes

Opening the file directly with `file://` works in Safari. Chrome is stricter
about loading the local `audio/` files that way — if audio is silent, either use
Safari or serve the folder with `python3 -m http.server` and open
`http://localhost:8000`.

## Background images

The cityscape backgrounds in `img/` are from Wikimedia Commons, under their
respective licenses (attribution required):

- `city1.jpg` — "Shanghai skyline at night" by Ernest Jourdier (CC BY 4.0)
- `city2.jpg` — "Hong Kong Harbour Night 2019-06-11" by Benh Lieu Song (CC BY-SA 4.0)
- `city3.jpg` — "Cijin Island, Kaohsiung" by Jirka Matousek (CC BY 2.0)
