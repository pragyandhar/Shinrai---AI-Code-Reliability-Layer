### UTF-8 vs UTF-16?
#### ANSWER:
UTF-8 aur UTF-16 dono text encoding formats hain.
Ye decide karte hain ki characters ko bytes mein kaise store kiya jaye.

Example
```
Character:
A

Unicode code point:
U+0041

Storage:
UTF-8 → 1 byte
UTF-16 → 2 bytes
------------------------------
Character:
क

Unicode:
U+0915

Storage:
UTF-8 → 3 bytes
UTF-16 → 2 bytes
```

| Feature               | UTF-8        | UTF-16        |
| --------------------- | ------------ | ------------- |
| English text          | Smaller      | Larger        |
| Hindi/Chinese         | Often larger | Often smaller |
| Compatible with ASCII | Yes          | No            |
| Web standard          | Yes          | Rare          |
| Storage unit          | 8-bit        | 16-bit        |

----
- Followup: Why UTF-8 dominates?

Most websites and APIs use UTF-8 because English characters are very compact.

For example:
```
Hello World
UTF-8 → 11 bytes
UTF-16 → 22 bytes
```
Almost double.
