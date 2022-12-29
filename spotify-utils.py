import requests
import os
import pyperclip

channelName = 'music'
spotifyHeaders = {
    'Authorization': 'Bearer placeholder',
    'Content-Type': 'application/json',
}
slackHeaders = {
    'content-type': 'multipart/form-data; boundary=----WebKitFormBoundaryy1UYCxUIDLOcDkqB',
    'Authorization': 'Bearer <USE your slack bot user token with read channel access which starts with xoxp >',
}

spotifyBaseUrl = 'https://api.spotify.com/v1/'
spotifyPlaylistUrl = 'https://api.spotify.com/v1/playlists/{playlistId}/tracks'
trackQueryParam = '?uris=spotify:track:{trackId}'
slackSearchUrl = 'https://slack.com/api/search.messages?query=in:{channelName} before:{endTime} after:{startTime} <https://open.spotify.com&pretty=true&page={pageCount}';


def addTrackToPlaylist(playlistId, trackId):
    json_data = {}
    addURL = spotifyPlaylistUrl + trackQueryParam;
    addURL = addURL.format(playlistId=playlistId, trackId=trackId)
    # print(addURL)
    response = requests.post(
        addURL,
        headers=spotifyHeaders,
        json=json_data, )
    # print(response.json())


def findExistingTracksInPlaylist(playlistId):
    response = requests.get(
        spotifyPlaylistUrl.format(playlistId=playlistId),
        headers=spotifyHeaders,
    )
    #print(response.json())
    items = response.json()['items']
    trackIdList = []

    for item in items:
        trackId = item['track']['id']
        trackIdList.append(trackId)
    # print(trackIdList)
    return set(trackIdList)


def cleanTrackId(trackId):
    index = 0
    for c in trackId:
        if c.isalnum():
            index = index + 1;
            continue
        trackId = trackId.replace(c, '')
        # print("repalcing", c)
        index = index + 1
    return trackId


def scrapeChannelForSpotifyTrackIds(startTime, endTime):
    pageCount = 0;
    totalPages = 1;
    trackIdList = [];

    data = '{\n    \n}'
    while (pageCount < totalPages):
        response = requests.get(
            slackSearchUrl.format(channelName=channelName, endTime=endTime, startTime=startTime, pageCount=pageCount),
            headers=slackHeaders,
            data=data, )
        pageCount = pageCount + 1;
        totalPages = response.json()['messages']['paging']['pages']
        response_data = response.json()['messages']['matches'];
        for match in response_data:
            # print(match['text'])
            tid = match['text'].split('/')[4].split('?')[0]
            tid = cleanTrackId(tid)
            trackIdList.append(tid)
            # print(trackIdList)
    return set(trackIdList)


def pushSongstoPlaylist(playlistId, trackIdList):
    tracksInPlaylist = findExistingTracksInPlaylist(playlistId)
    for trackId in trackIdList:
        if (trackId in tracksInPlaylist):
            continue
        # print("pushing", trackId)
        addTrackToPlaylist(playlistId, trackId)


def getSpotifyToken():
    os.popen('spotify-token').read()
    return pyperclip.paste()


def fetchUserId():
    userUrl = spotifyBaseUrl + 'me/'
    response = requests.get(
        userUrl,
        headers=spotifyHeaders,
    )
    return response.json()['id']
def getIdFromExistingPlaylists():
    playlistUrl = spotifyBaseUrl + 'me/playlists'
    response = requests.get(
        playlistUrl,
        headers=spotifyHeaders,
    )
    print("enter playlist number from the list below")
    responseJson = response.json()['items']
    count = 1
    playlistIds = {

    }
    for item in responseJson:
        print(str(count) + ":" + item['name'])
        playlistIds[count] = item['id']
        count = count + 1
    num=input("enter number\n")
    return playlistIds[int(num)]


def getPlaylistId(makeNewPlaylist):
    if (makeNewPlaylist == 'N' or makeNewPlaylist == 'n'):
        return getIdFromExistingPlaylists()

    playlistName = input("Enter Playlist Name\n")
    playlist_data = {
        'name': playlistName,
        'description': 'playlist made through slack scraper script',
        'public': True,
    }
    makeNewPlaylistUrl = 'https://api.spotify.com/v1/users/{userId}/playlists';
    response = requests.post(makeNewPlaylistUrl.format(userId = fetchUserId()), headers=spotifyHeaders,
                             json=playlist_data)
    #print(response.json()['uri'].split(":")[2])
    return response.json()['uri'].split(":")[2]


def processRequest():
    makeNewPlaylist = input("make new playlist?Y/N\n")
    playlistId = getPlaylistId(makeNewPlaylist)
    startTime = input("enter start date in yyyy-MM-dd:")
    endTime = input("enter end date in yyyy-MM-dd:")
    trackIdList = scrapeChannelForSpotifyTrackIds(startTime, endTime)
    pushSongstoPlaylist(playlistId, trackIdList)


if __name__ == '__main__':
    token = "Bearer " + getSpotifyToken()
    # print("token:", token)
    spotifyHeaders['Authorization'] = token
    processRequest()
