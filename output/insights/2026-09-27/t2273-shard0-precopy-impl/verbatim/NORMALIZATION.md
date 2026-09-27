# 逐語の可逆な最小正規化 (DW-S07)

`git diff --check` の行末空白に抵触したため、次の file の行末の半角空白 2 個 (markdown の改行指定) だけを除いた。可視文字は変えていない。原文は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/codex/` にある。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes | 空白を除いた行 |
|---|---|---:|---|---:|---|
| `s2-plan-out.md` | `b96f2bb62aa6e0d34a31ef061431eef6b3b98680397149d46a3c482bafc3740d` | 10,241 | `f777648ecd80876cb2823708aaf61e5c5dd980f6eecd2ced7689333bbea8c470` | 10,237 | 52, 53 |
| `s3-consult-b-out.md` | `38d8d19d89c130e351df85e232f97c41a3fb5aa8bbc4c624ed4b4f7de76e49d1` | 7,390 | `61145c3811c1fe4cece2a0eadc60d63a894f694d04ae175846e78ac54b07f7ff` | 7,380 | 3, 6, 9, 12, 15 |
| `s5-author-l-out.md` | `a1744c198340921273656e3fda8a867af44355f7fa8e466159b72d959bb680bc` | 3,530 | `cf55adc32b0f47aef046ee0a1d11e29c4d326f54c40f5ccdb7b68d4af35370e9` | 3,526 | 33, 34 |
| `s6-review-a-out.md` | `b985eb670c39b4c3c52099c9a0837cec1db54ee5a6bb468347736d4cf8cae216` | 4,705 | `b4c7a80a88a4967815c07e4f5fca802a6076eae3bd151a502f410bd9d3728a66` | 4,697 | 3, 6, 9, 12 |
| `s6-review-b-out.md` | `eb7c854cd3ba3f76c6c09020e18a30757fd90b33c38314228b97dedb8f609cc3` | 1,964 | `23b391c938e96703c3fd170fb1a553d615046f130859cfaf892d0d08e29ad0d8` | 1,962 | 3 |

復元法: 表の各行の行番号の行末に半角空白を 2 個ずつ足すと原文 sha256 に戻る (例: `sed -i '52,53s/$/  /' s2-plan-out.md`)。
