#todo:
#print behavior to log file and console for automatic imports.

import os
import time
from plexapi.server import PlexServer
from libpytunes import Library
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
    #open config file and save it to local variable
    config = {}
    with open("config.toml", "rb") as configFile:
        config = tomllib.load(configFile)

    #create local variables for config values
    plexUrl = config["PlexInfo"]["url"]
    plexServerToken = config["PlexInfo"]["serverToken"]
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
    iTunesLibrary = Library(iTunesLibraryFile)

    #dictionary for indexed iTunes songs. key structure: [artist][album][track] -> song data
    iTunesSongIndex = {}

    #dictionary for indexed iTunes albums. key structure [album name] -> data from first song on album.
    iTunesAlbumIndex = {}

    #index will track the progress of the loop.
    print("Indexing iTunes Songs and Albums...")
    index = 0
    songsWithRatings = 0
    albumsWithRatings = 0
    for x, song in iTunesLibrary.songs.items():
        #see if song has a valid rating value

        if song and song.rating and song.rating > 10 and (not song.rating_computed or useComputedSongRatings):
            #convert name, album, and artist data to string from XML.
            songName = str(song.name)
            songAlbum = str(song.album)
            songAlbumArtist = str(song.album_artist)
            
            #plex uses a rating system between 1 and 10, and iTunes uses between 10 and 100.
            songRating = song.rating / 10

            #add artist if it doesn't already exist:
            if songAlbumArtist not in iTunesSongIndex:
                iTunesSongIndex[songAlbumArtist] = {}
            
            #add album to index if it doesn't already exist.
            if songAlbum not in iTunesSongIndex[songAlbumArtist]:
                iTunesSongIndex[songAlbumArtist][songAlbum] = {}

            #add rating to song index, and increment songsWithRatings for final count
            iTunesSongIndex[songAlbumArtist][songAlbum][songName] = songRating
            songsWithRatings += 1
        
        #see if song's album has a valid rating value
        if song and song.album_rating and song.album_rating > 10 and (not song.album_rating_computed or useComputedAlbumRatings):
            artistName = str(song.album_artist)
            albumName = str(song.album)

            #only add album data if it doesn't exist
            if song.album_artist not in iTunesAlbumIndex:
                artistName = str(song.album_artist)
                iTunesAlbumIndex[artistName] = {}

            if song.album not in iTunesAlbumIndex[artistName]:
                albumRating = song.album_rating / 10
                iTunesAlbumIndex[artistName][albumName] = albumRating
                albumsWithRatings += 1

        #update progress bar with song/album being processed
        progress_bar(index, len(iTunesLibrary.songs.items())-1, f"Indexing iTunes library...")
        index += 1

    print(f"\niTunes songs with ratings: {songsWithRatings}")
    print(f"iTunes albums with ratings: {albumsWithRatings}")

    #connect to plex server and get music library
    print("\nConnecting to Plex server...")
    plexServer = PlexServer(plexUrl, plexServerToken)
    musicLibrary = plexServer.library.section(plexLibraryName)

    #load music library into plexSongs variable
    print(f"Loading Plex music library '{plexLibraryName}'...")
    plexSongs = musicLibrary.searchTracks()
    plexSongsCount = len(plexSongs)
    print(f"Number of songs on Plex: {plexSongsCount}")
    time.sleep(1)
    
    index = 0

    #temp!
    matchingSongs = 0
    matchingAlbums = 0
    for song in plexSongs:
        songArtist = str(song.artist().title)
        songAlbum = str(song.album().title)
        songName = str(song.title)

        #check to see if there is a match for the song in the iTunes index
        if songArtist in iTunesSongIndex:
            if songAlbum in iTunesSongIndex[songArtist]:
                if songName in iTunesSongIndex[songArtist][songAlbum]:
                    if song.userRating is None or overwriteExistingSongRatings:
                        songRating = iTunesSongIndex[songArtist][songAlbum][songName]
                        matchingSongs += 1
                        song.rate(songRating)

        #check to see if there is a match for the album in the iTunes index
        if songArtist in iTunesAlbumIndex:
            if songAlbum in iTunesAlbumIndex[songArtist]:
                album = song.album()
                albumRating = iTunesAlbumIndex[songArtist][songAlbum]
                if album.userRating != albumRating and (album.userRating is None or overwriteExistingAlbumRatings):
                    matchingAlbums += 1
                    album.rate(albumRating)

        progress_bar(index, len(plexSongs)-1, f"Applying ratings to Plex library...")
        index += 1
    
    print(f"\nPlex tracks rated: {matchingSongs}")
    print(f"Plex albums rated: {matchingAlbums}")
    print("Rating import complete.")