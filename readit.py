#!/usr/bin/env python

# import yaml


# with open('samples/sample1.yaml', 'r') as s:
#     samp = s.read()

# x=yaml.safe_load_all(samp)
# breakpoint()


import yaml
import pprint

from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

if __name__ == '__main__':
    stream = open("samples/sample1.yaml", 'r')
    dictionary = yaml.load_all(stream, Loader)

    blah = list(dictionary)
    pprint.pprint(blah, indent=4, width=1)


    for doc in dictionary:
        print("New document:")
        for key, value in doc.items():
            print(key + " : " + str(value))
            if type(value) is list:
                print(str(len(value)))


