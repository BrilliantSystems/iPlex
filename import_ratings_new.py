#todo:
#print behavior to log file and console for automatic imports.

from datetime import datetime
import sys
import os
import time
from plexapi.server import PlexServer
from plexapi.exceptions import BadRequest
#from libpytunes import Library
import tomllib

def yn_prompt(question, default, yesResponse, noResponse):
    options = ""
    if default is None:
        options = "[y/n]"
    elif default == "y":
        options = "[Y/n]"
    elif default == "n":
        options = "[y/N]"

    while True:
        choice = input(f"\n{question} {options}: ")
        choice = choice.lower()
        if choice == "":
            if default is not None:
                if default == "y":
                    print(yesResponse)
                    return True
                else:
                    print(noResponse)
                    return False
            else:
                print("Invalid input. Please enter y/yes or n/no.")
        
        elif choice == "y" or choice == "yes":
            print(yesResponse)
            return True
        
        elif choice == "n" or choice == "no":
            print(noResponse)
            return False

        else:
            print("Invalid input. Please enter y/yes or n/no.")

def progress_bar(completed, total, message):
    progressFraction = completed / total
    progressPercent = str(int(progressFraction * 100)) + "%"
    terminalWidth = os.get_terminal_size().columns
    terminalWidth -= (4 + len(message) + len(progressPercent))
    progress = int(progressFraction * terminalWidth) * "\u2588"
    padding = (terminalWidth - len(progress)) * "\u2591"

    print(f"\r{message}: {progress}{padding} {progressPercent}", end='', flush=True)


if __name__ == '__main__':
    #open config file and save it to local variable config
    config = {}
    with open("config.toml", "rb") as configFile:
        config = tomllib.load(configFile)

    #create local variables for config values
    plexUrl = config["PlexInfo"]["url"]
    plexServerToken = config["PlexInfo"]["serverToken"]
    plexServerName = config["PlexInfo"]["serverName"]
    plexLibraryName = config["PlexInfo"]["libraryName"]

    iTunesLibraryFile = config["iTunesInfo"]["libraryFile"]

    autoImport = config["ImportSettings"]["autoImport"]
    useComputedSongRatings = config["ImportSettings"]["useComputedSongRatings"]
    overwriteExistingSongRatings = config["ImportSettings"]["overwriteExistingSongRatings"]
    useComputedAlbumRatings = config["ImportSettings"]["useComputedAlbumRatings"]
    overwriteExistingAlbumRatings = config["ImportSettings"]["overwriteExistingAlbumRatings"]

    #check for autoImport. if not automatically importing, take user input for import behavior
    if not autoImport:
        useComputedSongRatings = yn_prompt("Do you wish to use computed song ratings from iTunes?", 
                                           "n",
                                           "Using computed song ratings.",
                                           "Ignoring computed song ratings.")
        overwriteExistingSongRatings = yn_prompt("Do you wish to overwrite existing song ratings in Plex?", 
                                                 "y",
                                                 "Overwriting existing Plex song ratings.",
                                                 "Skipping existing Plex song ratings.")
        useComputedAlbumRatings = yn_prompt("Do you wish to use computed album ratings from iTunes?",
                                            "y",
                                            "Using computed album ratings.",
                                            "Ignoring computed album ratings.")
        overwriteExistingAlbumRatings = yn_prompt("Do you wish to overwrite existing album ratings in Plex?",
                                                  "y",
                                                  "Overwriting existing Plex album ratings.",
                                                  "Skipping existing Plex album ratings.")
    
    #load library from iTunes
    #iTunesLibrary = Library(iTunesLibraryFile)

    for i in range(101):
        time.sleep(0.05)
        progress_bar(i, 100, "test progress bar")
    print("\ndone!")