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
"compressWav": true, # Converts to mp3 and m4a 
```

- `AudioArchive` required to make Trunk-Recorder save audio files.
- `uploadScript` Path to the icad_tr_uploader upload.sh including systems shortname as a parameter.
- `compressWav` Converts WAV to MP3 and M4A. The MP3 is required to upload to RDIO and iCAD Tone Detect and M4A is required for OpenMHZ


Copy upload_example.sh to upload.sh and modify for your environment
```bash
#! /bin/bash

cd /home/ccfirewire/icad_rtl_uploader
python3 main.py ${1} ${2}
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
```
"systems": {
    "system1_short_name":{
        "enabled": 1
     },
     "system2_short_name":{
        "enabled": 0
     }
}
```

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

Final Full Example in etc/config_example.json