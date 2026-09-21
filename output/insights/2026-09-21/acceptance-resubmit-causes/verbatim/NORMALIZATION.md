# verbatim の可逆最小正規化 (末尾空白の除去のみ、可視文字不変、DW-S07)

`git diff --check` の末尾空白抵触を避けるため、次の file の行末の空白 (半角空白 / tab) だけを除去した。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-resubmit-causes/` (codex/*.md、*.md、classification.md) にそのまま残る。復元は各行末へ記載の bytes を戻す。除去なしの file は前後の sha256 が一致する。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 除去 (行: 除去 bytes) |
|---|---|---|---|---|---|
| s3-consult.md | 263d8dafd60bbe55d46bd7b0045d13e18b1a5763122671bc2ba99c0b7dc37413 | 12741 | ed0afdde0d117d35694e072319bc66b622227786b69fc5ad2d1381929383bef5 | 12689 | 26 行、各行末の [b'  '] |
| s6-review.md | 36c8d7561e928be20a8a6e0145f0a7afe7a0b4a49592961cee1179895f70a9eb | 9417 | 8d53a7078fd0895feaf0ec292279be4ed4c3e7edc81707aa4e57c6acc3df4594 | 9371 | 23 行、各行末の [b'  '] |
| s6-focus.md | 92af7b4134a2e2f7dbb2a1e91ec79f6004fb4ad962f5b37d49e59db68719a53d | 6345 | 92af7b4134a2e2f7dbb2a1e91ec79f6004fb4ad962f5b37d49e59db68719a53d | 6345 |  |
| s3-consult-prompt.md | c1a7e40400fde51f6f2e87978466c4728ca45b2a05c8edc385c507c95bfa6e61 | 7795 | c1a7e40400fde51f6f2e87978466c4728ca45b2a05c8edc385c507c95bfa6e61 | 7795 |  |
| s6-review-prompt.md | 98bdb062b833f738c206542a804be31bfe236431e55eed9dba165b871066e6b8 | 6187 | 98bdb062b833f738c206542a804be31bfe236431e55eed9dba165b871066e6b8 | 6187 |  |
| s6-focus-prompt.md | 9051ee9199b64ee404e0d00106f8750c7b94b1926c803026bd5784cc29e40592 | 2898 | 9051ee9199b64ee404e0d00106f8750c7b94b1926c803026bd5784cc29e40592 | 2898 |  |
| s4-ruling.md | d97d1b9a9c60a4748d5904580bfb46fd084aff89f9164e9caac31118c45c2420 | 4253 | d97d1b9a9c60a4748d5904580bfb46fd084aff89f9164e9caac31118c45c2420 | 4253 |  |
| s1-brief.md | e97a18adb8e82632db3d22c6a04d5175ec89aafd871a76bfaf70b629d8db0d0e | 4176 | e97a18adb8e82632db3d22c6a04d5175ec89aafd871a76bfaf70b629d8db0d0e | 4176 |  |
| classification.md | b9a68058df87643b3db225b784f20ef5ab279fce1e2b16b3a64419ef762d3fc2 | 9706 | b9a68058df87643b3db225b784f20ef5ab279fce1e2b16b3a64419ef762d3fc2 | 9706 |  |
| origin.md | 690238eab9da595358318f3de0283a68251de48afa34381515fd10acae6c22ad | 1045 | 690238eab9da595358318f3de0283a68251de48afa34381515fd10acae6c22ad | 1045 |  |
| waves.txt | a4703a6c729342807a792d2b9dc11088c5e6d201a60f7a3d0043187216d2b1ca | 754 | a4703a6c729342807a792d2b9dc11088c5e6d201a60f7a3d0043187216d2b1ca | 754 |  |
| scripts.sha256 | cfadc74f126420e1b580058275b1f51264051c6b54ebe407d5395cbaf14ec7d3 | 728 | cfadc74f126420e1b580058275b1f51264051c6b54ebe407d5395cbaf14ec7d3 | 728 |  |
