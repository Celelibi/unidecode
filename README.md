# unidecode : dissecting unicode strings
A small tool that takes in a string and prints the character names for each
character (actually, for each code point) as well as a few other informations.
Its intended use is for debugging encoding issues, decomposing emojis,
desambiguating confuable characters, or even for cases when you don't have a
font capable of rendering some characters.

It can take its input either from the arguments on the command line, or from
its standard input. In both cases, it can handle malformed byte sequence and
will display its interpretation of it.

It doesn't rely on any external dependency and should work on most systems
where its use is relevant. If it doesn't work on yours, feel free to open an
issue. 🙂

## Examples
It can read from stdin.
```
$ echo -n "ouï" | ./unidecode
Character     Dec.   Hex. UTF-8            Cat. Name
o              111     6F \x6f             Ll   LATIN SMALL LETTER O
u              117     75 \x75             Ll   LATIN SMALL LETTER U
ï              239     EF \xc3\xaf         Ll   LATIN SMALL LETTER I WITH DIAERESIS
```

Or use its first positional argument.
```
$ ./unidecode --nfd ouï
Character     Dec.   Hex. UTF-8            Cat. Name
o              111     6F \x6f             Ll   LATIN SMALL LETTER O
u              117     75 \x75             Ll   LATIN SMALL LETTER U
i              105     69 \x69             Ll   LATIN SMALL LETTER I
◌̈              776    308 \xcc\x88         Mn   COMBINING DIAERESIS
```

It will handle invalid data
```
$ echo -n "é\xff♥️" | ./unidecode
Character     Dec.   Hex. UTF-8            Cat. Name
é              233     E9 \xc3\xa9         Ll   LATIN SMALL LETTER E WITH ACUTE
\udcff       56575   DCFF \xff             Cs   (INVALID BYTE 0xFF)
♥             9829   2665 \xe2\x99\xa5     So   BLACK HEART SUIT
◌️            65039   FE0F \xef\xb8\x8f     Mn   VARIATION SELECTOR-16
```
Invalid data is not an error by default. To see what the `\udcff` means, see
[below](#encoding-options).

## Fields shown
Here's the list of fields shown, from right to left.
- Name: The unicode name for this code point. Or some alias name for control
  characters. This is arguably the most important field.
- Category: The unicode character catagory. For instance `Ll` = letter
  lowercase. The unicode website has the [full list of unicode
  categories](https://www.compart.com/en/unicode/category).
- UTF-8: The byte sequence representing this code point when encoded using
  UTF-8. Note that depending on the options, this might not be the input byte
  sequence.
- Hex. and Dec.: Hexadecimal and Decimal representation of the code point
  number.
- Character: A tenative of rendering of the character. Note that *mark* code
  points are accompanied of a dotted circle as a stand-in base character.

## Options
This program has a few options. Both related to normalization and encoding.

### Normalization options
- `--normalize` can take any of the four normalization form name: `NFC`, `NFD`,
  `NFKC` or `NFKD`. `C` vs. `D` variant means Compose vs. Decompose. The
  Composed variant tries to combine character modifiers into a single
  character, like `é = e + ◌́`. Decomposed variant does the opposite. The `K`
  variant performs a compatibility decomposition first, for instance `Ⅶ = V + I + I`.
  The default is to not do any normalization.
- `--nfc`, `--nfd`, `--nfkc` and `--nfkd` are shorthands for corresponding
  `--normalize`.

### Encoding options
- `--encoding` specifies the encoding to use to decode the input (argument or
  stdin). The default is `UTF-8`.
- `--encoding-error` specifies what to do in case of decoding errors. Valid
  values are `strict`, `ignore`, `replace`, `surrogateescape`. Default is
  `surrogateescape`.
- `--strict`, `--ignore`: aliases for the most useful `--encoding-error` values.

The `strict` error handler will produce an error if the input is malformed.

The `ignore` error handler will skip the erroneous bytes and keep decoding. The
exact behavior is that of [python's `codec`
module](https://docs.python.org/3/library/codecs.html#error-handlers).

The `replace` error handler will replace the malformed character with `�`, the
official replacement character.

And finally, the `surrogateescape` will replace invalid bytes with value `\x80`
or more with a surrogate character in the range `U+DC80 - U+DCFF`. Other
invalid bytes produce an error.

## Implementation details
Deading with unicode is not as straightforward as it may seem. Here are a few
implementation details worth knowing.

### Name of control characters
The unicode standard no longer define names for the control characters.
Including for the most widely used like tabs, carriage return and line feed.
This program add those back so that they can be shown and distinguished from
one another. The names were taken from the unicode-provided
[NameAliases.txt](https://www.unicode.org/Public/17.0.0/ucd/NameAliases.txt).
When several names are available, the first one was used. In fact, the program
`make_missing_names_table.py` in this repository was used to generate that
table.

### Use of dotted circles
Many unicode code points are not meant to be rendered by themselves. Those are
called *marks*, and they include (but are not limited to) diacritics and other
accents. When the program encounter a code point for a mark, it prepends a
dotted circle `◌` when displaying the `Character` column so that the mark has
something to *hold onto*. Without this, some marks would be applied to whatever
character is just left to it and mess up the rest of the terminal.

### Python's use of surrogates
Unicode defines surrogate *characters*. These are not real characters, but are
rather place holders without a specific meaning. Python uses the surrogate
range `U+DC80 - U+DCFF` to represent invalid bytes when decoding an UTF-8 with
the error handler `surrogateescape`. More specifically, the bytes with value
greater than `\x80` are encoded as the code point `0xdc80 + byte - 0x80`.

This allows python to not loose information when binary data is mixed with
UTF-8 data.

### encoding sys.argv
The use of surrogate characters mentioned above is actually used by default by
python with its `argv` array to access the program arguments.

This program tries its best to honor the requested `--encoding` and
`--encoding-error` options. (Meaning: encoding and re-decoding with the correct
parameters.) But if the automatic decoding produce an error, there's not much
we can do.

### encoding stdin
In order to read stdin as bytes, this program uses an API that's slightly less
standard than usual. Moreover, the goal is to make it an interactive and
reactive tool that doesn't wait for its full input before processing.
Therefore, this program tries to use `sys.stdin.buffer.read1()` first.
If not available, it tries `sys.stdin.buffer.read(4096)`, which would block on
non-interactive input.
If not available, it tries `sys.stdin.read(4096).encode()`. This is the least
preferred solution as it will produce errors if the data is not UTF-8
decodable. A warning is shown when this last option is used.

### Character width
The output of this program is shown as a table. To do this, the width of the
unicode character has to be known in order to pad the correct amount of space.
Which turns out to be very hard.

There's a pair of POSIX standard function
[`wcwidth`](https://pubs.opengroup.org/onlinepubs/9699919799/functions/wcwidth.html)
and
[`wcswidth`](https://pubs.opengroup.org/onlinepubs/9699919799/functions/wcswidth.html)
that are meant to output the number of terminal character covered by a give
character or string. Their implementation is not specified, though, only the
function API. The behavior of the glibc version of these functions depends on
the `LC_CTYPE` category of the current locale.

This program tries to access the function `wcswidth` using the `ctypes` module
to call native code. In case of failure to do so, a warning is shown and a
simplistic version is used instead.
