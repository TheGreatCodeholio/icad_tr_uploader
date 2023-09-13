# iCAD Trunk Recorder Uploader
Script to upload audio files from trunk recorder to various services.

## Requirements
- Python < 3.6

**Python Libraries**
- requests 
- colorama
- DateTime
- argparse

## Installation
`git clone https://github.com/TheGreatCodeholio/icad_tr_uploader.git`
`pip3 install -r requirements.txt`

In your Trunk-Recorder configuration under your system.
```
"audioArchive": true, # saves audio files
"uploadScript": "/home/ccfirewire/icad_tr_uploader/upload.sh chemung-ny",
```

- `audioArchive` required to make Trunk-Recorder save audio files.
- `uploadScript` Path to the icad_tr_uploader upload.sh including systems shortname as a parameter.


Copy upload_example.sh to upload.sh and modify for your environment
```bash
#! /bin/bash

cd /home/ccfirewire/icad_rtl_uploader
python3 tr_uploader.py ${1} ${2}
status=$?

if [ $status -ne 0 ]; then
    echo "Error with python script, exit status: $status"
    exit 0
else
    exit 0
fi

```

## Configuration
copy config_example.json to config.json



## Configuration Sections
Defaults are in bold

### Global Section
- `log_level` (log verbosity level) - **1 Debug**, 2 Info, 3 Warning, 4 Error, 5 Critical
- `systems` (holds the information for each system) - **`{}`**

### Systems Sections
Inside of the Systems Global Section you add a system by its shortname define in TR configuration. Inside of that JSON is where the system configuration goes.
```json
"systems": {
    "system1_short_name":{
        "enabled": 1
     },
     "system2_short_name":{
        "enabled": 0
     }
}
```
- `mp3_bitrate` (bitrate for mp3): integer - sets the bitrate for converted mp3 files
- `m4a_bitrate` (bitrate for m4a): integer - sets the bitrate for converted m4a files
- `archive_days` (days to archive files): `-1` - Removes all files after script runs **`0`** - Do nothing, `1` or more - remove files after `1` or more days 
- `archive_path` (path to archive files to): string `"/home/ccfirewire/chemung_archive"`
- `rdio_systems` (holds configuration for RDIO systems): list of JSON
- `openmhz` (holds configuration for Uploading to OpenMHZ): JSON
- `icad_detect_api` (holds configiration for Uploading to iCAD TOne Detect): JSON

### RDIO Section
Each RDIO server you want to upload the system to should be added to the list `[]`
Example has two systems in it. 
```json
[
  {
    "enabled": 0,
    "system_id": 1111,
    "rdio_url": "http://example.com:3000/api/trunk-recorder-call-upload",
    "rdio_api_key": "example-api-key"
  },
  {
    "enabled": 1,
    "system_id": 1111,
    "rdio_url": "http://example.com:3000/api/trunk-recorder-call-upload",
    "rdio_api_key": "example-api-key"
  }
]
```

- `enabled` (enable/disable): integer - `0` Disabled, `1` Enabled
- `system_id` (RDIO System ID): integer
- `rdio_url` (URL to RDIO Upload API): string - "http://example.com:3000/api/trunk-recorder-call-upload"
- `rdio_api_key` (API Key for RDIO): string

### OpenMHZ Section
Upload to a single OpenMHZ system
```json
"openmhz": {
    "enabled": 0,
    "short_name": "example",
    "api_key": "example-api-key"
},
```

- `enabled` (enable/disable): integer - `0` Disabled, `1` Enabled
- `short_name` (system short name for OpenMHZ): string
- `api_key` (api key for OpenMHZ): string

### iCAD Tone Detect API Section
Upload to iCAD Tone Detect Instance

```json
"icad_detect_api": {
    "enabled": 0,
    "talkgroups": [1, 2, 4],
    "icad_url": "https://detect.example.com/tone_detect",
    "icad_api_key": ""
}
```
- `enabled` (enable/disable): integer - `0` Disabled, `1` Enabled
- `talkgroups` (talkgroup\s to send for detection): list of integers `[1, 2]`
- `icad_url` (URL path to iCad Tone Detect API): string 
- `icad_api_key` (API Key for iCAD): string - currently unused leave empty `""`

### Full Example of config.json
```json
{
  "log_level": 1,
  "systems": {
    "chemung-ny": {
      "archive_days": 14,
      "archive_path": "/home/ccfirewire/chemung_archive",
      "rdio_systems": [
        {
          "enabled": 1,
          "system_id": 1111,
          "rdio_url": "http://example.com:3000/api/trunk-recorder-call-upload",
          "rdio_api_key": "eu2i3-pmwek-rkd3-s4b-d33ff"
        }
      ],
      "openmhz": {
        "enabled": 1,
        "short_name": "chemung-ny",
        "api_key": "eu2i3-kyubp-rkd3-s4b-d33ff"
      },
      "icad_detect_api": {
        "enabled": 1,
        "talkgroups": [1],
        "icad_url": "https://detect.example.com/tone_detect",
        "icad_api_key": ""
      }
    }
  }
}
```

### Full Example of System in Trunk Recorder
```json

{
  "type": "conventionalP25",
  "squelch": -32,
  "channelFile": "/home/ccfirewire/tr_config/chemung_county_p25_channels.csv",
  "shortName": "chemung-ny",
  "callLog": true,
  "audioArchive": true,
  "uploadScript": "/home/ccfirewire/icad_tr_uploader/upload.sh chemung-ny",
  "compressWav": false,
  "digitalLevels": 2,
  "decodeMDC": true,
  "minDuration": 1.0
}
```