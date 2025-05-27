struct Header {
    char info[0x1B];
};

Header header_at_0x00 @ 0x00;

struct SecSep {
    u8 content[3];
};