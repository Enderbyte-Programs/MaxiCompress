import gzip
import lzma
import bz2
import sys
import os
import curses
import cursesplus
NAMESLIST = []
SIZESLIST = []
COMPLIST = []

class plaintext:
    @staticmethod
    def compress(ind):
        return ind

def compressf(fl,stdscr,pobj:cursesplus.ProgressBar):
    """Returns tuple: (name,size,data)"""
    ogf = os.path.getsize(fl)
    with open(fl,"rb") as f:
        data = f.read()
    pobj.value = 0
    pobj.step("gzip")
    gzcomp = gzip.compress(data)
    pobj.step("bzip")
    bzcomp = bz2.compress(data) 
    pobj.step("xz")
    lzcomp = lzma.compress(data)
    nl = ["plaintext","gzip","bz2","lzma"]
    usedcomp = nl[[ogf,len(gzcomp),len(bzcomp),len(lzcomp)].index(min([ogf,len(gzcomp),len(bzcomp),len(lzcomp)]))]
    pobj.step("Packaging")
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

def do_setup_routine(stdscr):
    pass

if len(args) == 0:
    args.append(input("Input file/directory> "))
    args.append(input("Output file> "))
args[0] = os.path.abspath(args[0])
args[1] = os.path.abspath(args[1])
def do_compress_routine(stdscr):
    DATA = []
    cursesplus.displaymsgnodelay(stdscr,["Compressing data"])
    p1=cursesplus.ProgressBar(stdscr,5,message="Overall progress")
    p2 = cursesplus.ProgressBar(stdscr,5,bar_location=cursesplus.ProgressBarLocations.BOTTOM)
    if os.path.isfile(args[0]):
        p1.step("Compressing")
        ftd = compressf(args[0],stdscr,p2)
        DATA = [ftd[2]]
        NAMESLIST.append("/"+os.path.split(args[0])[1])
        SIZESLIST.append(ftd[1])
        COMPLIST.append(ftd[0])
    elif os.path.isdir(args[0]):
        todo = []
        for subdir, dirs, files in os.walk(args[0]):
            for file in files:
                af = os.path.join(subdir,file)
                if os.path.getsize(af) == 0:
                    continue#Skip empty files
                todo.append(af)
        p1.max = len(todo) + 4
        p1.step("Compressing")
        for af in todo:
            ftd = compressf(af,stdscr,p2)
            NAMESLIST.append(af.replace(args[0],"",1))
            SIZESLIST.append(ftd[1])
            COMPLIST.append(ftd[0])
            DATA.append(ftd[2])
            p1.step(af)
            
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
    headerlength = len(final_header) + 4#Limit 4 bytes for header length size
    final_data = headerlength.to_bytes(length=len(str(headerlength))).lstrip(b'\0').rjust(4,b'\0') + final_header + b"".join(DATA)
    p1.step("Writing")
    OUTFILE = args[1]
    with open(OUTFILE,'wb') as f:
        f.write(final_data)
    p1.done()

def decompress_routine(stdscr):
    p = cursesplus.ProgressBar(stdscr,5,bar_location=cursesplus.ProgressBarLocations.CENTER,message="Decompressing")
    p.step("Reading")
    if not os.path.isfile(args[0]):
        print("Please provide a valid file")
        sys.exit(-1)
    with open(args[0],'rb') as f:
        data = f.read()

    header_length = int.from_bytes(data[0:4])
    header_data = data[4:header_length]
    datacores = header_data.split(b":")
    p.max = len(datacores) + 2
    if not os.path.isdir(args[1]):
        os.makedirs(args[1])

    offset = header_length

    for block in datacores:
        subm = block.split(b"*")
        p.step("Decompressing")
        
        #print(subm)
        if not os.path.isdir(args[1].encode()+os.path.split(subm[0])[0]):
            os.makedirs(args[1].encode()+os.path.split(subm[0])[0])
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
    p.done()

if not "--decompress" in args:
    curses.wrapper(do_compress_routine)
else:
    #Do decompress instead
    curses.wrapper(decompress_routine)