# 逐語・生記録の行末空白の可逆最小正規化 (DW-S07)

`git diff --check` に抵触した行の末尾の空白だけを除いた。可視文字は不変。
復元法: 各 file の「行」に「除いた bytes」(Python bytes 表記) を行末へ付け直すと、原文の sha256 と byte 数に戻る。
原本は wave 専用 dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-resume/`) の同名 file。集計器はその原本を読んだ (正規化の前)。

| file (insight dir 相対) | 原文 sha256 | 原文 bytes | 行: 除いた bytes | 正規化後 sha256 | 正規化後 bytes |
| --- | --- | --- | --- | --- | --- |
| `raw/job-out/S1-a/cell.txt` | `389d3c2f7f4e8cae78c184e33a608e72e8439a566a39eb78fda9ceb4a21bf657` | 550 | 6: b' ' | `e4f4cf05094d41c8e205884204af9319424e44a61ba4b40f6bcc246ac04192e4` | 549 |
| `raw/job-out/S1-b/cell.txt` | `2d10975f3d30260ec5d494c16f36c12460c05d8ebf065b7173900895d866afd5` | 550 | 6: b' ' | `dd7b1a4ebdc86b3a3a281e57b5e5e3640ca0ac84305ef7a60a8d47a79a263b16` | 549 |
| `raw/job-out/S2f-a/cell.txt` | `03789b59b20e1f4c23880222abb415d87139f25d496cca9caf0cfc8e3e5171c0` | 581 | 6: b' ' | `d1f14b68afee28fdd85313e4052312f32b5d4da526d07deb2a7fc3e1e32fe2d6` | 580 |
| `raw/job-out/S2f-b/cell.txt` | `573e722dca04d8f51144ba272a4ae0244b31783e526de31cf70d3dc220c7dda3` | 581 | 6: b' ' | `6cef8937fad7ed9e7009862db47c91e7932d86680cc09f5aaa07ffba799d0468` | 580 |
| `raw/job-out/S3cf-a/cell.txt` | `0785c15eb16cd24a2f2bbab1c48b80cfb816e8efa314eef8f7a9a22172f61f79` | 562 | 6: b' ' | `0689e698bff7a56a37410b428fe99bf5e0b9c1368a1e1465e5a765b4479514ba` | 561 |
| `raw/job-out/S3cf-b/cell.txt` | `b23e754ac1440e5ec25f3f4ac5ae5aee2319b731cdae08132fb3b8caad567496` | 562 | 6: b' ' | `0855ba443770afbd00dbcf4a11c26d5ca0e25d1de64cf92a70db11cc64bb4332` | 561 |
| `raw/job-out/S3f-a/cell.txt` | `9940626bbdf9180e41361bd4c3fd51c0c82958293dfe45720147e6b4ba9c77d1` | 558 | 6: b' ' | `84854710b3561642ef37ca30159cf184e75dd250d285ce59d80153b2675dac01` | 557 |
| `raw/job-out/S3f-b/cell.txt` | `6215dfc9af5b217685b8223212347fb01d6567b6a72cd7050bbf1e7e5743375b` | 558 | 6: b' ' | `822152b77eef6f1078eee056e1ea8aadd79048001294cceef39885284a5d6a9c` | 557 |
| `raw/job-out/S3u-a/cell.txt` | `11e41297851dbeef9e4b5535979771f3816cb80a45ac0c847546cd99442301b7` | 558 | 6: b' ' | `84089d428c5db6b6c9b429ba1bc3f08f1198d5a1b8a275f7924e6a5c8f52ae3c` | 557 |
| `raw/job-out/S3u-b/cell.txt` | `245dbf4867100293061a501bb440e119eb74b84deeba4f341b258d8f8bf1eb5d` | 558 | 6: b' ' | `ed3427db997713a2bc6ca4e78ca1110aee439172e9b96fc535eeba3f9f232ddd` | 557 |
| `raw/job-out/warm/cell.txt` | `fb9c4b55883b86b78c3cbf375c076c28679eab9279e84d116b301a5893e4a7f8` | 450 | 6: b' ' | `3b84bffbb34cfe0159fa1de3526b5fa922b73e62bed3c06b428be770d54c0905` | 449 |
| `raw/login-out/S1-a/cell.txt` | `1068d5205280a4d2f3d4fc4f0f79dd22f6f60903760d88afd186b5f5c4ecc273` | 538 | 6: b' ' | `07a76aca632ba3e24433bc1857ae0c8c6570a956e87344c66e53a26895d83265` | 537 |
| `raw/login-out/S2f-a/cell.txt` | `e7c51f89cfcc2acc4f6db50f994d450d42c9274b3528d0279a481a60c6f86481` | 569 | 6: b' ' | `96daa00f8297994b35e67345b4c37fdff75e98e03cb449930280d18fd5b9765d` | 568 |
| `raw/login-out/S3cf-a/cell.txt` | `ad1c3603041f0d7850b3cbf4d78e39c2fa497378536b411f462667dd66cb6b41` | 550 | 6: b' ' | `8c43999eea6bc74f6a8f31038aa5f54a41b987e6180e553f7c898d1f9955123d` | 549 |
| `raw/login-out/S3f-a/cell.txt` | `e3d3814100cc9973e59b663f0f7c2cc90cebc8cbe1a8890c16652a93a848c158` | 546 | 6: b' ' | `9182c68ceac8aec47bfce6edcee8412c8e0f3f6bba4851d0acdf60e80091e2c4` | 545 |
| `raw/login-out/S3u-a/cell.txt` | `3b90c1145f7a4d9fb50317bf99d56d1cec707051040c63299cf173b5675f04be` | 546 | 6: b' ' | `94b10e3ce1543dd7e44b38850fe9c3a8848750f9b85b6a013571b9ed49273b3f` | 545 |
| `verbatim/run-probe.log` | `4b98a2b0fcd261b1b7ecec23f405a4831360e4053a435a13ad3fc90669b9e6da` | 3949 | 26: b' ' | `a09fc59826537493597576bf58619cb3c029e027e83ea83f66a2d7f64298f43c` | 3948 |
| `verbatim/s6-review-out.md` | `e1a8d7c44ccfa10b704fac85a302b50becfdea5f693114c86e2db1f013df2d96` | 9823 | 38: b'  '; 39: b'  '; 40: b'  '; 43: b'  '; 44: b'  '; 45: b'  '; 48: b'  '; 49: b'  '; 50: b'  '; 53: b'  '; 54: b'  '; 55: b'  '; 58: b'  '; 59: b'  '; 60: b'  '; 63: b'  '; 64: b'  '; 65: b'  '; 68: b'  '; 69: b'  '; 70: b'  '; 73: b'  '; 74: b'  '; 75: b'  ' | `003b7936d9b8d34c2d474c0fa0000d6b12aca9439512ab91f65c01573200a40f` | 9775 |

計 18 file・41 行 (最初の記録 commit の 17 file・17 行に、段 6 review の逐語 1 file・24 行 (Markdown の改行用の行末空白 2 byte) を追加)。
