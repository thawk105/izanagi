# verbatim の可逆最小正規化 (末尾空白の除去のみ、可視文字不変、DW-S07)

`git diff --check` の末尾空白抵触を避けるため、次の file の行末の空白 (半角空白 / tab) だけを除去した。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-waiter-collect-latency/` (codex/*.md、verbatim/*) にそのまま残る。復元は各行末へ記載の bytes を戻す。記載の無い file は無変更。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 除去 (行: 除去 bytes) |
|---|---|---|---|---|---|
| coverage.txt | bb7ecd8c0b8cae3121fdd18fffcaf01d89f503577daee5f8e82af444289d977c | 2903 | 63361da0a078c32354458648e0bc1c877782f4fc3c1194061a26032013e2e153 | 2892 | 11 行 (2, 3, 4, 13, 14, 16, 17, 25, 26, 28, 29)、各行末の [b' '] |
| s3-consult-A.md | e74eabe3a05c6675cdc6a4c234983b8fd68376c36ac11f91a3d1b0c62203051e | 8689 | 249f620a153f569d63242587f98580950d0153fe377a0534cb93d7ebcfcc545e | 8683 | 3 行 (53, 54, 55)、各行末の [b'  '] |
| s6-focus-A.md | ef0f049cd965a5b271ed4d4b9e8abc520947c1e89ebaef1a0d8dd808508c2fdc | 4885 | 217683b1aa0ea1edafa419d5239022bfb980ae0f1578573595e91412a24be6a0 | 4875 | 5 行 (23, 26, 29, 34, 35)、各行末の [b'  '] |
| s6-focus-B.md | 827b9b5dd5dd8599c47290523f7f03a5e53ba203cf029a6cf0b2b6c231b94054 | 3824 | 52457359e908eaba992b240bbc2a23acbaec3c288640aa0da6a4112bb7a9f515 | 3820 | 2 行 (30, 31)、各行末の [b'  '] |
| s6-focus-C.md | 34cd5aa29ff547b914a39fcb54d8ffa68c23b7b6c6133b820432e04a18e2bc6a | 3532 | d0f09f8e055c89d01b96ca5674f8f4556186ad71fb925b02fd1da793c498d7db | 3528 | 2 行 (30, 31)、各行末の [b'  '] |
| s6-review-A.md | 480df9d977a36bde59f51cb5042c8786fc7baa3e89d26d7e8691dd7071f1ea95 | 8968 | e54793680342071d1739357cf21d8265d999cac832e0efb66e64376ec57c139d | 8926 | 21 行 (9, 10, 13, 14, 17, 18, 21, 22, 25, 26, 29, 30, 33, 34, 37, 38, 41, 42, 61, 62, 63)、各行末の [b'  '] |
