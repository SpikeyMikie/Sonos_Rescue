# Sonos Rescue

## Project overview

Sonos Rescue is a Python desktop application for controlling Sonos speakers without relying on the official Sonos desktop software. It uses the SoCo Python library to communicate directly with Sonos devices on the local network and aims to provide a cleaner, more flexible interface while exploring additional functionality not available in the official application.

---

---

## Motivation

Sonos has gradually removed or changed features from its desktop software, while many users prefer controlling their speakers from a PC rather than a mobile device. I started this project to learn Python while creating an alternative desktop controller tailored to my own workflow.

Along the way, the project became an opportunity to learn object-oriented programming, networking, GUI development, image handling, threading and software architecture.

---

---

## Current goals

- Update code to remove all Pylance and Mypy warnings and errors
- Modernise desktop GUI - i.e. change from tKinter to PyQt6
- Discover Sonos speakers on the local network
- Browse and play locally hosted music
- Display album artwork and track information
- Queue management
- Room management
- Volume and playback controls

- Local HTTP server for streaming files to Sonos devices

---

---

## Long-term vision

One long-term goal is to investigate replacing the original Sonos control hardware with a Raspberry Pi or similar embedded computer installed inside older Sonos speakers. Rather than relying on the official Sonos ecosystem, the speaker would run custom software developed as part of this project while reusing the existing amplifier and speaker hardware where practical.

This hardware work is still at the research and planning stage, but it is one of the motivations behind the software architecture.

---

---

## Collaboration

I am happy for others to collaborate and contribute, just submit your ideas on GitHub.
Likewise I added a GNU v3 license to allow any use (other than commercial), feel free to take it and make it you own! Credit and a link would be nice though! ;-)

## Credits / Acknowledgements

This project began as an exploration of the excellent SoCo-Tk project by Labero, which demonstrated how the SoCo library could be used to build a desktop Sonos controller.

My version has gradually diverged through refactoring, new features and architectural changes as I have learned Python and software engineering.

> Repo: https://github.com/labero/SoCo-Tk

**Technologies:**

Also, neither project could be completed without the excellent rahims SoCo python library!

> Repo: https://github.com/rahims/SoCo

---

---

## License:

GNU GENERAL PUBLIC LICENSE v3

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or(at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

Full license text can be found in COPYING.txt
See the [GNU General Public License](https://spdx.org/licenses/GPL-3.0-or-later.html) for more details.

---

---

## README TODO

The following sections are still to be added in the near future.

- **Features:** list of main features
- **Install** step-by-step instructions on how to install the project
    - Any software or package requirements should also be listed here.
- **How to use:** instructions on how use the project.

---

---
