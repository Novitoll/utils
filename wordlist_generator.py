import os
import argparse

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("--wl", help="Wordlist")
  args = parser.parse_args()
  
  with open(args.wl, "r") as f:
    words = [w.strip() for w in f.readlines()]
    f.close()
  
  opts = []
  for w in words:
    for o in words:
      if o == w:
        print "%s is %s" % (o, w)
        continue
      # lower
      opts.append("".join([w, o]).lower())
      # another
      opts.append("".join([o, w]))
      # underscore
      opts.append("_".join([w, o]).lower())

  with open("out", "w+") as f:
    for o in opts:
      f.write("%s\n" % o)

