#!/usr/bin/python3

import sys, getopt, os
import random
import subprocess
import re

# Clips audio at random from video or audio input files in specified folder.
# Requires ffmpeg to be in PATH.

################################################################################
# Main
################################################################################
def main(argv):
    # Defaults
    rng_seed = 1337
    random_clip_start = True 
    if rng_seed:
        random.seed(rng_seed)
    else:
        random.seed()

    clip_start_mins = 0     # In minutes
    clip_len_mins = 5       # In minutes
    clip_dir = "."          # Folder to clip audio from
    audio_lang = "jpn"
    prior_format = ("mp4", "mkv", "mp3", "aac")
    audio_format = "aac"
    
    # Parse arguments
    if len(sys.argv) != 0:
        try:
            opts, args = getopt.getopt(argv, "hd:l:s:t:", ["clip_dir=", "language=", "clip_start=", "clip_length="])
        except getopt.GetoptError:
            print_usage()
            sys.exit(2)

        for opt, arg in opts:
            if opt == '-h':
                print_usage()
                sys.exit()
            elif opt in ('-d', '--clip_dir='):
                clip_dir = str(arg)
            elif opt in ('-l', '--language='):
                audio_lang = str(arg)
            elif opt in ('-s', '--clip_start='):
                clip_start_mins = int(arg)
                random_clip_start = False
            elif opt in ('-t', '--clip_length='):
                clip_len_mins = int(arg)

    clip_len_sec = clip_len_mins * 60
    print("Clip length: {} minutes".format(clip_len_mins))
    print("Clip directory: {}".format(clip_dir))
    print("Clip language: {}".format(audio_lang))
    print()

    # Regex
    duration_pattern = re.compile("\s+Duration: (?P<hour>\d{2}):(?P<minute>\d{2}):(?P<second>\d{2})\.(?P<decimal>\d{2})")
    audio_format_pattern = re.compile("\s+Stream.*\({lang}\): Audio: (?P<format>\w+)".format(lang=audio_lang))
    patterns = (duration_pattern, audio_format_pattern)

    # Get list of files from folder
    folder_list = os.listdir(clip_dir)

    # Find valid files
    valid_files = []
    for file in folder_list:
        if file[-3:] in prior_format:
            valid_files.append(file)

    print("Valid files found to process:")
    for file in valid_files:
        print("  " + file)
    print()

    # Clip audio from each file using ffmpeg
    print("Result clipped audio:")
    for file in valid_files:
        # Find audio total length and format (extension)
        audio_len, audio_format = get_audio_length_and_format(clip_dir, file, patterns)

        # Get random start time if enabled
        clip_start_sec = clip_start_mins * 60
        if random_clip_start:
            clip_start_sec = random.randrange(audio_len)
            # Ensure there is at least clip_len_sec to clip out of file
            clip_start_sec = min(clip_start_sec, audio_len - clip_len_sec)

        # Execute ffmpeg
        clip_range_str = "s{start_time}_e{end_time}".format(start_time=clip_start_sec, end_time=(clip_start_sec + clip_len_sec))
        clip_file_name = "{infile}_{cliprange}.{ext}".format(infile=file[:-4], cliprange=clip_range_str, ext=audio_format)
        runstr = "ffmpeg -y -i \"{dir}\\{infile}\" -ss {start_time} -t {duration} -map 0:m:language:{lang} -c:a copy \"{outfile}\"".format(dir=clip_dir, infile=file, start_time=clip_start_sec, duration=clip_len_sec, lang=audio_lang, outfile=clip_file_name)
        # subprocess.run(runstr, capture_output=True, text=True)
        try:
            subprocess.run(runstr, check=True, capture_output=True, text=True)
            #print(runstr)
            print("  " + clip_file_name)
        except subprocess.CalledProcessError as e:
            print("ERROR: Failed to clip audio from \"{}\"!".format(file))      

################################################################################
# Gets the audio length in seconds and audio format
################################################################################
def get_audio_length_and_format(clip_dir, file, patterns):
    # Defaults
    audio_len = 0
    audio_format = "aac"
    duration_pattern, audio_format_pattern = patterns

    runstr = "ffmpeg -i \"{dir}\\{infile}\"".format(dir=clip_dir, infile=file)
    outstr = subprocess.run(runstr, capture_output=True, text=True)
    
    duration_match = re.search(duration_pattern, str(outstr))
    if duration_match:
        audio_len += int(duration_match.group('hour')) * 3600
        audio_len += int(duration_match.group('minute')) * 60
        audio_len += int(duration_match.group('second'))
        # Drop the decimal portion
    else:
        print("\nERROR: Unable to determine file length! Defaulting to 0...")

    format_match = re.search(audio_format_pattern, str(outstr))
    if format_match:
        audio_format = format_match.group('format')
    else:
        print("\nERROR: Unable to determine audio format! Defaulting to \"aac\"...")
    
    return (audio_len, audio_format)

################################################################################
# Prints usage
################################################################################
def print_usage():
    print("Usage: clip_audio_samples.py [OPTION]... -d <dir_to_clip_from>")
    print("  -d, --clip_dir")
    print("      directory to clip files from")
    print("  -l, --language")
    print("      audio language track to clip, defaults to \"jpn\"")
    print("  -s, --clip_start")
    print("      start time (in minutes) where to clip in each file, if not specified a random position is chosen")
    print("  -t, --clip_length")
    print("      time to clip out (in minutes), defaults to 5 minutes")
    

################################################################################
# Strip off script name in arg list
################################################################################
if __name__ == "__main__":
    main(sys.argv[1:])