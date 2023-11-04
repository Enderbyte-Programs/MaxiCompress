import gzip
import lzma
import bz2
import sys
import os
import shutil
import math

NAMESLIST = []
SIZESLIST = []
COMPLIST = []

class plaintext:
    @staticmethod
    def compress(ind):
        return ind

    

def compressf(fl):
    """Returns tuple: (name,size,data)"""
    ogf = os.path.getsize(fl)
    with open(fl,"rb") as f:
        data = f.read()

    gzcomp = gzip.compress(data)
    bzcomp = bz2.compress(data) 
    lzcomp = lzma.compress(data)
    nl = ["plaintext","gzip","bz2","lzma"]
    usedcomp = nl[[ogf,len(gzcomp),len(bzcomp),len(lzcomp)].index(min([ogf,len(gzcomp),len(bzcomp),len(lzcomp)]))]

    if usedcomp == "plaintext":
        return (b'x\00',ogf,data)
    elif usedcomp == "gzip":
        return (b'\x01',len(gzcomp),gzcomp)
    elif usedcomp == "bz2":
        return (b'\x02',len(bzcomp),bzcomp)
    elif usedcomp == "lzma":
        return (b'\x03',len(lzcomp),lzcomp)
    #print(fl.ljust(80),usedcomp.ljust(5),str(round(100 - min([ogf,len(gzcomp),len(bzcomp),len(lzcomp)]) / ogf * 100,0))+"%")

args = sys.argv[1:]
if len(args) == 0:
    print("Please provide an input file or folder")
    sys.exit(-1)
args[0] = os.path.abspath(args[0])
args[1] = os.path.abspath(args[1])
if not "--decompress" in args:
    DATA = []
    
    if os.path.isfile(args[0]):
        ftd = compressf(args[0])
        DATA = [ftd[2]]
        NAMESLIST.append("/"+os.path.split(args[0])[1])
        SIZESLIST.append(ftd[1])
        COMPLIST.append(ftd[0])
    elif os.path.isdir(args[0]):
        for subdir, dirs, files in os.walk(args[0]):
            for file in files:
                af = os.path.join(subdir,file)
                if os.path.getsize(af) == 0:
                    continue#Skip empty files
                ftd = compressf(af)
                NAMESLIST.append(af.replace(args[0],"",1))
                SIZESLIST.append(ftd[1])
                COMPLIST.append(ftd[0])
                DATA.append(ftd[2])
    else:
        print("Please provide a valid file or folder")
        sys.exit(-1)

    #Compile header
    HEADERS = []
    ci = 0
    for e in NAMESLIST:
        HEADERS.append(e.encode() + b"*" + str(SIZESLIST[ci]).encode() + b"*" + COMPLIST[ci])
        ci += 1

    final_header = b":".join(HEADERS)
    headerlength = len(final_header) + 8#Limit 8 bytes for header length size
    final_data = headerlength.to_bytes(length=len(str(headerlength))).lstrip(b'\0').rjust(8,b'\0') + final_header + b"".join(DATA)

    OUTFILE = args[1]
    with open(OUTFILE,'wb') as f:
        f.write(final_data)

else:
    #Do decompress instead
    if not os.path.isfile(args[0]):
        print("Please provide a valid file")
        sys.exit(-1)
    with open(args[0],'rb') as f:
        data = f.read()

    header_length = int.from_bytes(data[0:8])
    header_data = data[8:header_length]
    datacores = header_data.split(b":")

    if not os.path.isdir(args[1]):
        os.mkdir(args[1])

    offset = header_length

    for block in datacores:
        subm = block.split(b"*")
        
        #print(subm)
        if not os.path.isdir(args[1].encode()+os.path.split(subm[0])[0]):
            os.mkdir(args[1].encode()+os.path.split(subm[0])[0])
        with open(args[1]+subm[0].decode(),"w+b") as g:
            writedata = data[offset:offset+int(subm[1])]#Extract data
            #print(len(writedata))
            if subm[2] == b'\0':
                g.write(writedata)
            elif subm[2] == b'\x01':
                g.write(gzip.decompress(writedata))
            elif subm[2] == b'\x02':
                g.write(bz2.decompress(writedata))
            elif subm[2] == b'\x03':
                g.write(lzma.decompress(writedata))
        offset += int(subm[1])