## 所見

### 1 / blocker / over-rejection 正例が恒真

対象: `orchestrator/tests/test_check_docs.py:2679`、`test_check_docs.py:568`

**実測:** 現行 `operations.md` は 8,329 bytes、`DW-O20` は 489 bytes。+154 bytes なら実ファイルは 8,483 bytes となり、旧 file cap 8,400 を超える。一方 synthetic fixture は約753 bytesで、+154しても約1.5KB未満。旧 file cap・aggregate を残した実装でも緑になる。

**なぜ壊れるか:** `test_dev_wave_l2_accepts_dw_o20_plus_154_bytes` は L2単節 643 bytesしか検証せず、裁定の「旧 cap 解放」を検出していない。

**提案:** fixture の operations 全体を少なくとも 8,247 bytes以上に独立 paddingし、O20 +154で旧 8,400 capを超える構成にする。

### 2 / major / synthetic fixture が production contract と自己整合

対象: `orchestrator/tests/test_check_docs.py:458`、`test_check_docs.py:568`

**実測:** `_write_command_guard_docs()` は `STAGE_*_DISPATCH_CONTRACT`、`CONDITION_DISPATCH_CONTRACT`、`CONDITION_TRIGGER_CONTRACT` から synthetic dispatch と trigger 表を生成する。

**なぜ壊れるか:** production の期待集合と fixture が同時に drift すると、baseline と多数の positive control が同じ誤りを共有する。層予算の 10,625 / 9,566 / 1,000 は literal と独立 slicer で作られており、この点は問題ない。

**提案:** dispatch fixture の基準表・trigger は少なくとも独立 literal にし、production contract の変更を自動追従させない。

### 3 / blocker / pytest の受入証拠なし

対象: `s6-fix.md:28`、`s5tests2.log:827`

**実測:** fix 後も runner は `qstat -Q preflight rc=1`、runner rc=16で pytest 開始前に停止。fix 前ログは `191 failed, 159 passed`。standalone `python3 -B tools/check_docs.py` のみ rc=0。pytest の緑は主張できない。

**なぜ壊れるか:** M1〜M12、共有 edge、O20 正例、provenance consumer の実走結果が存在しない。

**提案:** runner 復旧後に全 node と mutation matrix を再走し、rc=0を確認するまで land しない。

## M1〜M12 の実在検証

| 変異 | KILL 実在性 | mask |
|---|---|---|
| M1 | あり。`[l1]` は L1比較だけが赤要因 | registry/dispatch変更なし |
| M2 | あり。`[l1_5]` も同様 | なし |
| M3 | あり。`[l2_section]` は1,001 bytesかつ他層正常 | なし |
| M4 | あり。`[stage-u-to-c]` は flatten集合不変なので typed照合だけが必要 | なし |
| M5 | あり。`[stage-marker-missing]` の `||` が fallback U で緑化する | `|U/C|` 等は別の構造検査で赤くなるため、KILL根拠は `||` |
| M6 | あり。`[condition-always]` は trigger以外不変 | なし |
| M7 | あり。L1 fixture の preamble 分が除外されると閾値未満になる | なし |
| M8 | あり。fixtureは1,001 bytesかつ1,000文字以下 | なし |
| M9 | あり。allowlist内 bare pathなので closure/allowlistでは赤くならない | なし |
| M10 | あり。raw `^##` 化で fence/comment/raw HTML内の偽H2がslice境界になる | なし |
| M11 | **あり。ただし `[malformed-heading]` のみ** | 他の3 parameterは1:1差を作らない |
| M12 | あり。共有 edge の `(owner, mode)` literal assertが落ちる | なし |

M11の独立 probe は、malformed H2で `slices=1`、可視登録数 `0`、それでも `covered == actual` でした。したがって1:1検査を除去すると合計一致だけでは赤くならず、現行の1:1 findingだけが実在するKILLです。事前登録は `[malformed-heading]` まで明記すべきです。

同じ入力を既存 node が先に拒否する新規 node は確認できません。旧 file-cap test の削除は同一入力の重複削除ではなく、裁定済み契約変更に伴う置換です。

## fixture・fix・期待値の監査

`_grow_test_section()` は `match.end()` から末尾改行だけを戻して payload を挿入するため、payload後の改行と次のH2は保持されます。ASCIIは指定byte数、multibyteは「あ」3 bytesを使い、H2を連結しません。対象: `test_check_docs.py:2351`。

削除された旧期待値は以下です。

- `REFERENCE_LIMITS` の core / operations 個別 cap assert
- 旧 25,200 aggregate assert
- 個別 cap +1、aggregate 25,201、cap-sum 110%超過・境界の各 assert
- 旧 `reference_byte_over` / `aggregate_over` mutation case
- 旧 per-file exact-boundary / plus-one tests

これは裁定で旧 cap・aggregateを削除したため、構成の置換としては正当です。skip・xfail化、期待値の反転はありません。typed U/C findingへの文言変更と `dispatch_allowlist` の期待件数1→2は、検出面の増加です。

`PROVENANCE_REFERENCE_LIMITS`、provenance dispatch contract、受理集合はdiff上不変です。ただしprovenance test群も未実走です。

## 総括

- O20 +154 正例は旧 file cap を跨がず、主要な過剰拒否解除を検出しない。
- pytest は未実走で、受入緑を主張できない。
- M1〜M12は概ねKILL可能。M11は `[malformed-heading]` を明示登録すべき。
- provenance family のdiff上の不変性は確認済みだが、動的検証は未実走。

判定: **NO-GO**