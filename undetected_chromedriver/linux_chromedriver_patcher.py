import os
import sys
import io
import re

def patch(bin_path) :
  os.system("sed -i 's/Google Chrome for Testing/Google Chrome\\x00for Testing/' '" + str(bin_path) + "'")
  # patch chromedriver
  with io.open(bin_path, "r+b") as fh:
    content = fh.read()
    match_injected_codeblock = re.search(rb"\{window\.cdc.*?;\}", content)
    if match_injected_codeblock:
        target_bytes = match_injected_codeblock[0]
        new_target_bytes = (b'{;}'.ljust(len(target_bytes), b" "))
        new_content = content.replace(target_bytes, new_target_bytes)
        fh.seek(0)
        fh.write(new_content)
  with open(os.path.join(os.path.dirname(bin_path), 'cd.patched'), mode = 'a'): pass
  return True

if __name__ == "__main__" :
  patch(sys.argv[1])
