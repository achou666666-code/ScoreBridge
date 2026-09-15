# Clean installation verification — September 15, 2026

Before the fix, an export of commit 7723cfc had 68 passing tests, two failures,
and one local-evidence skip. Both failures involved instrument names: Flute
and Violin desk names depended on uncommitted local instrument changes.

The fix resolves canonical names, flat spellings and numbered desks, adds the
violin metadata missing from the committed catalog, and avoids reporting an
explicit Piano alias as an accidental fallback. It does not add all orchestral
instruments or establish audible sound quality.

`scripts/check_clean_install.py` exported the staged fix, created a fresh Python
3.14 environment, built and installed the package with test/image/websocket/MCP
extras, and verified imports came from site-packages. Result: **73 passed,
1 skipped**. The skip is the absent local Pirates page-classification evidence;
JavaScript plugin behavior and MCP entry-point tests ran. The working checkout
also passed all 74 tests, including its local evidence.

The new GitHub workflow repeats the clean installation check on Python 3.11
with Node 22. Its live run status is separate from this local result. These tests
exercise installation and software behavior, not desktop audio or transcription
accuracy. Existing unrelated instrument/parser edits were excluded from the
snapshot and retained in the working tree.
