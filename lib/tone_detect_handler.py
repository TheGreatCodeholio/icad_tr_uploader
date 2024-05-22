import io
import logging
import traceback

from icad_tone_detection import tone_detect

module_logger = logging.getLogger('icad_tr_uploader.tone_detect')


def get_tones(tone_detect_config, wav_file_path):
    detected_tones = {
        "two_tone": [],
        "long_tone": [],
        "hi_low_tone": []
    }
    try:

        results = tone_detect(wav_file_path, tone_detect_config.get("matching_threshold", 2), tone_detect_config.get("time_resolution_ms", 50), tone_detect_config.get("tone_a_min_length", 0.8), tone_detect_config.get("tone_b_min_length", 2.8), tone_detect_config.get("hi_low_interval",0.2), tone_detect_config.get("hi_low_min_alternations", 3), tone_detect_config.get("long_tone_min_length", 1.5))
        detected_tones.update({
            "two_tone": results.two_tone_result,
            "long_tone": results.long_result,
            "hi_low_tone": results.hi_low_result
        })

    except Exception as e:
        traceback.print_exc()
        module_logger.error(f"<<Tone>> <<Detect>> - Error {e}")

    return detected_tones
