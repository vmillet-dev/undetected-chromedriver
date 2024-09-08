import argparse
import io
from urllib.request import urlretrieve, urlopen
import zipfile
import os
import re
import json
import shutil

def fetch_package(download_url):
  return urlretrieve(download_url)[0]

def unzip_package(fp, extract_root = '/', unzip_path = '/tmp/unzip_chrome', extract_sub_directory = ''):
  try:
    os.unlink(unzip_path)
  except (FileNotFoundError, OSError):
    pass

  os.makedirs(unzip_path, mode = 0o755, exist_ok = True)

  with zipfile.ZipFile(fp, mode = "r") as zf:
    zf.extractall(unzip_path)

  shutil.copytree(os.path.join(unzip_path, extract_sub_directory), extract_root, dirs_exist_ok = True)
  shutil.rmtree(unzip_path)

def download_and_install(version_prefix) :
  target_platform = "linux64"

  #chrome_download_url = 'https://storage.googleapis.com/chrome-for-testing-public/117.0.5870.0/linux64/chrome-linux64.zip'
  #chromedriver_download_url = 'https://storage.googleapis.com/chrome-for-testing-public/128.0.6613.119/linux64/chromedriver-linux64.zip'

  chrome_download_url = None
  chromedriver_download_url = None
  with urlopen("https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json") as conn:
    response = conn.read().decode()
  response_json = json.loads(response)
  for version_obj in response_json['versions'] :
    if ('version' in version_obj and version_obj['version'].startswith(version_prefix) and 'downloads' in version_obj) :
      downloads_obj = version_obj['downloads']
      #print("Check version: " + str(version_obj['version']) + ": " + str(downloads_obj))
      if ('chrome' in downloads_obj and 'chromedriver' in downloads_obj):
        #print("XXX")
        for platform_obj in downloads_obj['chrome'] :
          if platform_obj['platform'] == target_platform :
            chrome_download_url = platform_obj['url']
        for platform_obj in downloads_obj['chromedriver'] :
          if platform_obj['platform'] == target_platform :
            chromedriver_download_url = platform_obj['url']
        if chrome_download_url is not None and chromedriver_download_url is not None :
          break
        chrome_download_url = None
        chromedriver_download_url = None

  if chrome_download_url is None or chromedriver_download_url is None :
    print("Can't find download urls")
    return False

  print("Download chrome by url : " + str(chrome_download_url), flush = True)
  print("Download chromedriver by url : " + str(chromedriver_download_url), flush = True)
  extract_root = '/usr/bin/'
  unzip_package(fetch_package(chrome_download_url), extract_root = extract_root, extract_sub_directory = 'chrome-linux64')
  unzip_package(fetch_package(chromedriver_download_url), extract_root = extract_root, extract_sub_directory = 'chromedriver-linux64')
  os.chmod(os.path.join(extract_root, 'chrome'), 0o755)
  os.chmod(os.path.join(extract_root, 'chromedriver'), 0o755)
  os.system("sed -i 's/Google Chrome for Testing/Google Chrome\\x00for Testing/' " + str(extract_root) + "/chrome")
  # patch chromedriver
  with io.open(os.path.join(extract_root, 'chromedriver'), "r+b") as fh:
    content = fh.read()
    match_injected_codeblock = re.search(rb"\{window\.cdc.*?;\}", content)
    if match_injected_codeblock:
        target_bytes = match_injected_codeblock[0]
        new_target_bytes = (b'{;}'.ljust(len(target_bytes), b" "))
        new_content = content.replace(target_bytes, new_target_bytes)
        fh.seek(0)
        fh.write(new_content)
  with open(os.path.join(extract_root, 'cd.patched'), mode = 'a'): pass
  return True

def main(version_prefix) :
  download_and_install(version_prefix)

if __name__ == "__main__" :
  parser = argparse.ArgumentParser(description = 'linux_chromedriver_installer.')
  parser.add_argument("-v", "--version-prefix", type = str, default = '120.')
  args = parser.parse_args()

  main(args.version_prefix)
