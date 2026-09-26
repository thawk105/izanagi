# 逐語の可逆な最小正規化 (DW-S07)

`git diff --check` の行末空白に抵触したため、次の 1 file だけ行末空白を除いた。可視文字は変えていない。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 変更 |
|---|---|---:|---|---:|---|
| `s3-consult-a-out.md` | `e340d320154a72dcdd5833a657af175d1d9d2f36edfd62a83fa055aea84480a1` | 7,394 | `cd68c455df086bed7d530d7751d5a2e5e45df660dc04a0514e3498918b3d92e9` | 7,390 | 33 行目と 34 行目の行末の空白 2 個 (markdown の改行指定) を削除 |

復元法: 33 行目と 34 行目の行末に半角空白を 2 個ずつ足すと原文 sha256 に戻る (`sed -i '33,34s/$/  /' s3-consult-a-out.md`)。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy/codex/s3-consult-a-out.md` にある。
