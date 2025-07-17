
import struct
import time

def dos_time_and_date():
    t = time.localtime()
    dos_time = (t.tm_hour << 11) | (t.tm_min << 5) | (t.tm_sec // 2)
    dos_date = ((t.tm_year - 1980) << 9) | (t.tm_mon << 5) | t.tm_mday
    return dos_time, dos_date

# ---- CRC32 MANUAL ----
def make_crc32_table():
    table = []
    for i in range(256):
        c = i
        for j in range(8):
            if c & 1:
                c = 0xEDB88320 ^ (c >> 1)
            else:
                c >>= 1
        table.append(c)
    return table

_crc32_table = make_crc32_table()

def crc32_manual(data: bytes) -> int:
    crc = 0xFFFFFFFF
    for b in data:
        crc = (crc >> 8) ^ _crc32_table[(crc ^ b) & 0xFF]
    return crc ^ 0xFFFFFFFF
# -----------------------

def write_local_file_header(f, name, crc, size):
    dos_time, dos_date = dos_time_and_date()
    f.write(b'PK\x03\x04')                        # local file header signature
    f.write(struct.pack('<HHHHH', 20, 0, 0, dos_time, dos_date))
    f.write(struct.pack('<III', crc, size, size))
    f.write(struct.pack('<HH', len(name), 0))     # file name length, extra length
    f.write(name.encode('utf-8'))

def write_central_dir_entry(f, name, crc, size, offset):
    dos_time, dos_date = dos_time_and_date()
    f.write(b'PK\x01\x02')                        # central dir signature
    f.write(struct.pack('<HHHHHH', 0x14, 20, 0, 0, dos_time, dos_date))
    f.write(struct.pack('<III', crc, size, size))
    f.write(struct.pack('<HHHHH', len(name), 0, 0, 0, 0))
    f.write(struct.pack('<II', 0, offset))        # external attr, offset
    f.write(name.encode('utf-8'))

def write_end_of_central_dir(f, count, size, offset):
    f.write(b'PK\x05\x06')
    f.write(struct.pack('<HHHHIIH', 0, 0, count, count, size, offset, 0))

def main():
    files = input("Files to zip (space separated): ").strip().split()
    zip_name = "output.zip"

    with open(zip_name, "wb") as zipf:
        central_dir = []
        for name in files:
            with open(name, "rb") as fin:
                data = fin.read()
            crc = crc32_manual(data)
            offset = zipf.tell()
            write_local_file_header(zipf, name, crc, len(data))
            zipf.write(data)
            central_dir.append((name, crc, len(data), offset))

        cd_start = zipf.tell()
        for entry in central_dir:
            write_central_dir_entry(zipf, *entry)
        cd_end = zipf.tell()
        write_end_of_central_dir(zipf, len(central_dir), cd_end - cd_start, cd_start)

    print("ZIP criado com sucesso:", zip_name)
print("\033c\033[43;30m\n")
if __name__ == "__main__":
    main()
