import configparser
import os
import sys
import traceback 
import argparse

from twitchApi import TwitchApi

DIRPATH = os.path.dirname(os.path.realpath(__file__))
CONFIGFILE = os.path.join(DIRPATH, "config.ini")
DATABASEFILE = os.path.join(DIRPATH, "clips.sqlite3")

twitchApi: TwitchApi = None
config = {}

if os.path.exists(CONFIGFILE):
  print(f"local config file exits")
  print(f"loading configs from {CONFIGFILE}")
  try:
    config = configparser.ConfigParser()
    config.read(CONFIGFILE, encoding='utf8')
    config = config['settings']
  except Exception as e:
    print(f"config parse error while reading {CONFIGFILE}")
    print(e)


def init_twitchApi(argDatabase, argClientId, argClientSecret, argStreamer, argReadSize, argProxy):
  global config, twitchApi
  databaseFile = argDatabase if argDatabase != None else DATABASEFILE
  clientId = argClientId if argClientId != None else config.get('clientId', None)
  clientSecret = argClientSecret if argClientSecret != None else config.get('clientSecret', None)
  streamerId = argStreamer if argStreamer != None else config.get('streamerId', None)
  readSize = int(argReadSize) if argReadSize != None else config.get('readSize', 40)
  proxy = argProxy if argProxy != None else config.get('proxy', None)
  
  if clientId == None:
    raise Exception("client_id is needed")
  if clientSecret == None:
    raise Exception("clientSecret is needed")
  if streamerId == None:
    raise Exception("streamer_id is needed")
  twitchApi = TwitchApi(databaseFile, clientId, clientSecret, streamerId, readSize, proxy)


def make_database():
  global twitchApi
  try:
    twitchApi.read_all_clips()
  except Exception as e:
    traceback.print_exception(e)
    sys.exit(0)


def download_clips_from_database(argDownloadDirectory, argConcurrency, argSaveJson, argForceDownload):
  global config, twitchApi
  try:
    downloadDirectory = argDownloadDirectory if argDownloadDirectory != None else config.get('downloadDirectory', None)
    saveJson = argSaveJson if argSaveJson != None else config.get('saveJson', False)
    forceDownload = argForceDownload if argForceDownload != None else config.get('forceDownload', False)
    
    if downloadDirectory == None:
      raise Exception(f"download directory is not specified!")
    
    concurrency = argConcurrency if argConcurrency != None else config.get('concurrency', 6)
    try:
      concurrency = int(argConcurrency)
    except:
      concurrency = 6
    
    if concurrency < 0:
      concurrency = 1
    
    twitchApi.download_clips_from_database(downloadDirectory, concurrency, saveJson, forceDownload)
  except Exception as e:
    traceback.print_exception(e)
    sys.exit(0)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    prog="Twitch Clip Archiver",
    description="Read all clips and save to database. Download clips if needed.",
    epilog="It reads `config.ini` first then apply arguments if passed.",
  )
  
  parser.add_argument("-n", "--skip-build-database", action="store_true", help="use existing database without requesting from server")
  parser.add_argument("-d", "--download", action="store_true", help="download all clips in database")
  parser.add_argument("-j", "--save-json", action="store_true", help="save clip information as json file")
  parser.add_argument("-f", "--force-download", action="store_true", help="re-download file if marked as downloaded")
  
  parser.add_argument("--client-id", help="twitch client id")
  parser.add_argument("--client-secret", help="twitch client secret")
  
  parser.add_argument("-b", "--database", help="database path")
  parser.add_argument("-s", "--streamer", help="streamer loginName(not nickname!!!) or broadcaster_id(number string)")
  parser.add_argument("-o", "--download-directory", help="path to save clips")
  parser.add_argument("--read-size", help="the number of clips fetch from twitch server. larger is inaccurate")
  parser.add_argument("--concurrency", help="download concurrency (default=6)")
  parser.add_argument("--proxy", help="proxy url")

  args = parser.parse_args() 
  
  init_twitchApi(args.database, args.client_id, args.client_secret, args.streamer, args.read_size, args.proxy)
  if args.skip_build_database != True:
    print(f"Read clips from twitch server...")
    make_database()
  if args.download == True:
    print(f"Download clips...")
    download_clips_from_database(
      args.download_directory, 
      args.concurrency,
      (args.save_json == True),
      (args.force_download == True)
    )
  
