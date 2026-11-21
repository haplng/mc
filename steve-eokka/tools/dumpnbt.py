import sys, gzip, io, nbtlib
for p in sys.argv[1:]:
    print("=====", p)
    raw = open(p,'rb').read()
    try:
        f = nbtlib.File.parse(io.BytesIO(gzip.decompress(raw)))
        print("(gzip)")
    except Exception as e:
        f = nbtlib.File.parse(io.BytesIO(raw))
        print("(raw)")
    print(nbtlib.serialize_tag(f, indent=1)[:6000])
