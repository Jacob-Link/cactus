# 🌵 Cactus
I got frustrated with Claude Code sessions scattered everywhere, never knowing which one needed input. Built this over a weekend using existing tools (Textual + tmux). Dead simple, solves the problem for me, hope others can also find value in it 🌎

Claude Code sessions manager. See which ones need input, which are working, which are ready - all from one place.

## Install

**pipx** (recommended)
```bash
pipx install git+https://github.com/Jacob-Link/cactus.git
```

**uv**
```bash
uv tool install git+https://github.com/Jacob-Link/cactus.git
```

**From source**
```bash
git clone https://github.com/Jacob-Link/cactus.git
cd cactus
pip install -e .
```

Then run `cactus` from anywhere.

First time only: `tmux attach -t claude-<name>` in another terminal to interact with sessions.

## Keys

`n` new · `s` switch · `e` rename · `d` delete · `q` quit

## Status Colors

🔴 needs input · 🟡 working · 🟢 ready · ⚪ seen
