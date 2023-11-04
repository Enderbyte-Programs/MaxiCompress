# MaxiCompress

The Best of Every Compression Algorithm. In general, there is a 15% improvement between ZIP and MXC

## File Format

The structure of the file is

DATA [
    HEADER [
        Length (8 bytes)
        Rest of header (n-8 bytes) [
            Relative name
            *
            Length
            *
            Compression type
            :
        ] 
    ]
    DATA
]

### The Header

The first 8 bytes of the file are the length in little endian format. The length provided includes these 8 bytes.
After that there are the file location blocks.

The rest of the header is split with a : character.