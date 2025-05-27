#pragma endian little

import std.mem;

struct Header {
    char file_type_and_version[0x1B];
};

Header header @ 0x0;

struct MusicEntry {
    char16 file_path[0x100];
    u8 length;
    padding[1];
    u8 day;
    u8 month;
    u16 year;
    padding[1];
    u8 unknown[8];
    padding[1];
};

MusicEntry file_1 @ 0x1B;
MusicEntry file_2 @ 0x22B;
MusicEntry file_3 @ 0x43B;