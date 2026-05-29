# -*- coding: utf-8 -*-
"""ART.DAT decode/encode for AG (Allied General). Format:
header 0x0E bytes, then 16B index entries [name4][type4][BEoff][BEsize] until idx_end(BE@8).
RLEi chunk: 'RLEi'(4) BEsize(4) name(4) palname(4) 0000(4) W(2BE) H(2BE) sub(4) then row-based stream.
  index_size = 8 + chunk_size ; chunk_size = 20 + len(stream) ; stream starts at off+28.
Row stream: per row decode to W px. tokens: 0x00 NN=literal NN; 0x80|n=literal n; 0x01-0x7F=run c of next color.
Decoder stops after H rows -> trailing bytes ignored (allows in-place zero-pad if re-encoded <= original).
CPal chunk: data off+22, 8B entries [BEidx][R.G.B.] -> RGB=(b0,b2,b4)."""
import struct

def load(path):
    d=bytearray(open(path,"rb").read())
    idx_end=struct.unpack_from(">I",d,8)[0]
    entries=[]; p=0x0E
    while p+16<=idx_end:
        entries.append([bytes(d[p:p+4]),bytes(d[p+4:p+8]),struct.unpack_from(">I",d,p+8)[0],struct.unpack_from(">I",d,p+12)[0],p])
        p+=16
    return d, entries

def find(entries,name,typ):
    for e in entries:
        if e[0]==name and e[1]==typ: return e
    return None

def parse_pal(d,e):
    off,size=e[2],e[3]; pal=[(0,0,0)]*256; q=off+22; end=off+8+size
    while q+8<=end:
        idx=struct.unpack_from(">H",d,q)[0]
        if idx<256: pal[idx]=(d[q+2],d[q+4],d[q+6])
        q+=8
    return pal

def decode_rle(d,e):
    off,size=e[2],e[3]
    W=struct.unpack_from(">H",d,off+20)[0]; H=struct.unpack_from(">H",d,off+22)[0]
    pn=bytes(d[off+12:off+16]); sub=bytes(d[off+24:off+28])
    end=off+8+size; i=off+28; rows=[]
    for r in range(H):
        row=[]
        while len(row)<W and i<end:
            c=d[i]; i+=1
            if c==0x00: m=d[i]; i+=1; row+=list(d[i:i+m]); i+=m
            elif c&0x80: m=c&0x7F; row+=list(d[i:i+m]); i+=m
            else: col=d[i]; i+=1; row+=[col]*c
        row=(row[:W]+[0]*W)[:W]; rows.append(row)
    stream_len=i-(off+28)
    return W,H,pn,sub,rows,stream_len

MAXRUN=125   # original never exceeds 125 (0x7D); 0x7E/0x7F avoided
MAXLIT=125   # original literal max 125 (0xFD); 0xFE/0xFF are reserved/special tokens
def encode_row(row,W):
    out=bytearray(); i=0
    while i<W:
        j=i
        while j<W and row[j]==row[i] and (j-i)<MAXRUN: j+=1
        runlen=j-i
        if runlen>=3:
            out.append(runlen); out.append(row[i]&0xFF); i=j
        else:
            lit=[]
            while i<W and len(lit)<MAXLIT:
                k=i
                while k<W and row[k]==row[i] and (k-i)<3: k+=1
                if (k-i)>=3: break
                lit.append(row[i]&0xFF); i+=1
            out.append(0x80|len(lit)); out+=bytes(lit)
    return bytes(out)

def encode_row_literal(row,W):
    """Pure-literal encoding (no run tokens). Each row = chained 0x80|n literals, n<=125."""
    out=bytearray(); i=0
    while i<W:
        n=min(125, W-i)
        out.append(0x80|n); out+=bytes(b&0xFF for b in row[i:i+n]); i+=n
    return bytes(out)

def encode_stream(rows,W,literal_only=False):
    s=bytearray()
    enc=encode_row_literal if literal_only else encode_row
    for row in rows: s+=enc(row,W)
    return bytes(s)

## ---- V2 (CORRECT) format: stream@off+26, each row = [BE16 rowlen][tokens], rowlen=2+len(tokens)
## tokens: 0xFF n = skip n (transparent); 0x80|n = literal n (n<=126, never 0xFF); 0x01-0x7F = run n + color.
def decode_rle_v2(d,e):
    off,size=e[2],e[3]
    W=struct.unpack_from(">H",d,off+20)[0]; H=struct.unpack_from(">H",d,off+22)[0]
    pn=bytes(d[off+12:off+16]); chunk_end=off+size; cur=off+26; rows=[]   # size = FULL chunk (incl 8B hdr)
    for r in range(H):
        rowlen=struct.unpack_from(">H",d,cur)[0]
        i=cur+2; tend=cur+rowlen; row=[]
        while len(row)<W and i<tend:
            c=d[i]; i+=1
            if c==0xFF: n=d[i]; i+=1; row+=[0]*n
            elif c&0x80: n=c&0x7F; row+=list(d[i:i+n]); i+=n
            else: n=c&0x7F; col=d[i]; i+=1; row+=[col]*n
        rows.append((row[:W]+[0]*W)[:W])
        cur+=rowlen
    return W,H,pn,rows

MAXRUN_V2=125; MAXLIT_V2=125   # match original exactly: never emit 0x7E/0x7F run or 0xFE/0xFF literal (reserved)
def encode_row_v2(row,W):
    out=bytearray(); i=0
    while i<W:
        j=i
        while j<W and row[j]==row[i] and (j-i)<MAXRUN_V2: j+=1
        runlen=j-i
        if runlen>=3:
            out.append(runlen); out.append(row[i]&0xFF); i=j   # run: count(1-7F)+color
        else:
            lit=[]
            while i<W and len(lit)<MAXLIT_V2:
                k=i
                while k<W and row[k]==row[i] and (k-i)<3: k+=1
                if (k-i)>=3: break
                lit.append(row[i]&0xFF); i+=1
            out.append(0x80|len(lit)); out+=bytes(lit)
    return bytes(out)

def encode_stream_v2(rows,W):
    s=bytearray()
    for row in rows:
        tok=encode_row_v2(row,W)
        rowlen=2+len(tok)
        s+=struct.pack(">H",rowlen); s+=tok
    return bytes(s)

def patch_inplace_v2(d,e,rows,W):
    off,size=e[2],e[3]
    chunk_end=off+size                 # size = FULL chunk length (incl 8B RLEi+size header)
    space=chunk_end-(off+26)
    stream=encode_stream_v2(rows,W)
    if len(stream)>space: return False,len(stream),space
    d[off+26:off+26+len(stream)]=stream
    for k in range(off+26+len(stream), chunk_end): d[k]=0   # zero-pad ONLY within this chunk
    return True,len(stream),space

def patch_inplace_lit(d,e,rows,W):
    off,size=e[2],e[3]
    old_space=(off+8+size)-(off+28)
    stream=encode_stream(rows,W,literal_only=True)
    if len(stream)>old_space: return False,len(stream),old_space
    d[off+28:off+28+len(stream)]=stream
    for k in range(off+28+len(stream), off+8+size): d[k]=0
    return True,len(stream),old_space

def patch_inplace(d,e,rows,W):
    """Re-encode rows into chunk e IN PLACE (zero-pad trailing). Requires new stream<=old chunk space.
    Returns (ok, new_stream_len, old_chunk_bytes_after_off+28)."""
    off,size=e[2],e[3]
    old_space=(off+8+size)-(off+28)   # bytes available for stream
    stream=encode_stream(rows,W)
    if len(stream)>old_space:
        return False,len(stream),old_space
    d[off+28:off+28+len(stream)]=stream
    for k in range(off+28+len(stream), off+8+size):
        d[k]=0
    return True,len(stream),old_space
