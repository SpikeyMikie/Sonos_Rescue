from requests import get
from soco import SoCo
from soco import discover


# discover devices (zones) on the network
for zone in discover():
    print(zone.player_name, zone.ip_address)

# create a SoCo instance for the lounge zone
zone_lounge = SoCo("192.168.86.35")
print("Zone Lounge:", zone_lounge)

# change then check the current night mode status, alternate: True / False
zone_lounge.night_mode = False
print("Night Mode:", zone_lounge.night_mode)

# list available actions for a zone
print("Available Actions:", zone_lounge.available_actions)

print("Is Soundbar?:", zone_lounge._is_soundbar)
print("Is Subwoofer?:", zone_lounge.is_subwoofer)
print("Is Satellite?:", zone_lounge._is_satellite)
print("Is playing TV?:", zone_lounge.is_playing_tv)
print(zone_lounge.speaker_info)
speaker_info = zone_lounge.get_speaker_info('zone_name')
print("Speaker Name:", speaker_info['zone_name'])
print(speaker_info.get('zone_name'))
