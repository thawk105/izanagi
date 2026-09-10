# 逐語の可逆最小正規化 (DW-S07)

`git diff --check` が `s3-lensA.md` の**行末空白 9 行**を検出したため、
可視文字を変えない最小の正規化を当てた。他の 6 file は無改変である。

## 対象

| 項目 | 値 |
|---|---|
| file | `verbatim/s3-lensA.md` |
| 正規化 | 各行の行末空白の除去のみ (`line.rstrip()` を全行へ適用) |
| 影響行数 | 9 行 (いずれも Markdown の hard line break を作る行末 2 空白) |
| 可視文字 | 不変 |

## hash と byte 数

| 状態 | bytes | sha256 |
|---|---|---|
| 原文 | 8361 | `1d343842821382360fc56c1055152c7a9f8b98415164b834295aa78cb2c02a7a` |
| 正規化後 | 8343 | `618bd76c71d22404bf3bfc797dfcc8598c3a0a306a55d884c3a32fea866f5929` |

## 無改変の file (参考)

| file | bytes | sha256 |
|---|---|---|
| `s2-plan.md` | 18188 | `40b35498b7804b51ad2fc82c67adb3ef8f0001dbbc240cf5c84b3e297f67ae85` |
| `s3-lensB.md` | 12499 | `d5075b5b15d27fbc74b70a6065d28bb8c8e3985e3993fe01c44949049a0e7283` |
| `s5-author.md` | 3865 | `65bd82040415696ac673b269375c527dc2121ee8ab8d4b48ee09e2a14f909070` |
| `s6-fix.md` | 5311 | `2b266b2bbfcd9565d878ec91af1bd7818ad1b4706aea2ad4f2d2fcf0ad71bad9` |
| `s6-lensC.md` | 9576 | `8f49169050eb02fbc78256a8acf652f3b32099d9b2a28938335a2882d991becb` |
| `s6-lensD.md` | 20862 | `e5b8d375f61e3fa204075bc16aefc7a2785ddd3f69e0f556cd96bef27162f595` |

## 復元法

除去したのは、次の 9 行の**行末 2 空白**だけである
(いずれも Markdown の hard line break 記法)。各行の末尾へ 2 空白を戻せば原文の
byte 列と sha256 が一致する。原文は 8361 bytes、正規化後は 8343 bytes で、
差の 18 bytes は 9 行 x 2 空白に一致する。

- `1. **受理集合: NG。**`
- `3. **完全一致: NG。**`
- `4. **`SURVIVED` / `TIMEOUT`: 問題なし。**`
- `5. **flaky hold: 計画した結果契約は妥当。**`
- `6. **production 経路: 問題なし。**`
- `7. **負例の向き: fanout 側が NG。**`
- `1. **BLOCKER — 接尾辞規則が path 内の `@` まで test identity から消す。**`
- `2. **MAJOR — fanout verifier が正規化後重複を拒否しない。**`
- `3. **MAJOR — fanout の負例が包含への弱体化を検出しない。**`
