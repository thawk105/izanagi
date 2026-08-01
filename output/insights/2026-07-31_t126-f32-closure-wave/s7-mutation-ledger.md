authority: none
default_effect: no-state-change

# T-126 F3-2 closure — 変異 matrix 台帳 (`DW-O19` 本走)

## 走行条件

- anchor commit: `b36aaa1` (実装 `4bcbc2c` → main 統合 `887e899` → 予約 policy 分離 `b36aaa1`)
- job: Pegasus 計算ノード `875906.nqsv` (bnode012)、`result.rc=0`
- harness: `.codex/dev-wave-t126-f32-closure-jobs/mutation_harness.py`
  (`flock` 単一走行 guard、anchor 一意性検査、注入実在確認、`git checkout --` 復元 + 内容比較、
  subprocess timeout、`-rf` の FAILED node 記録)
- 対象 test: T-126 4 file + `test_campaign.py` の 5 file、32 workers
- **baseline 失敗 0 node** (無変異走行が完全に緑)
- 走行後の tracked tree は完全復元 (`git status --porcelain` に tracked dirt なし)

結果: **mutations=35 / killed=35 / survived=0 / HARNESS-STOP=0**。
survivor が無いため `DW-M02` の「所見ゼロを変異なしで緑と数えない」再照準は不要。

## 本 wave の新規 5 件 — 事前登録と実測の突き合わせ (`DW-M08`)

事前登録の正本は `s6-review-adjudication.md` の「変異事前登録の期待赤 (fix 1 後の確定版)」。
全 mutant で `test_fr3_mutation_node_registry_is_exact_and_complete` が赤になるのは
anchor 消失による設計上の性質であり、事前に宣言済み。

| ID | 事前登録した期待赤 | 実測した新規赤 | 一致 |
|---|---|---|---|
| M9e | T1、T5、T8[stage=True, clean=True] の 2 param、meta-test | 同 5 node | **完全一致** |
| M9g | T1、T3、T4、T5、T8[stage=True] の 4 param、meta-test | 同 9 node | **完全一致** (過剰決定は宣言済み) |
| M9h | T6[early-malformed-name]、meta-test | 同 2 node | **完全一致** |
| M9i | T9[empty]、T9[complete]、meta-test | 同 3 node | **完全一致** |
| M9j | T8[semantics=semantic-valid] の 4 param、meta-test | 同 5 node | **完全一致** |

### 特筆すべき 2 点

1. **M9i が `test_m9a_targetless_full_staging_is_discarded_to_nonretry_failure[attempt]` を
   巻き添えにしていない。** 段 6 のレンズ C1 / D1 が独立に指摘した「二重 unlink で
   `FileNotFoundError` が escape し、正例が偽の理由で赤になる」欠陥は、lifecycle 判定を
   単一定数へ寄せる fix で構造的に解消した。実測がそれを裏付けている。
   これにより「回収を targetless へ広げない」という本 wave の中心裁定に、
   単一理由の正例変異による裏取りが付いた。

2. **M9j で `semantics=semantic-invalid` の 4 param が緑のまま残った。** guard を削除しても
   この 4 param が赤にならないのは、guard が意味検証と一致していて構造だけ valid な canonical には
   発火しないことの直接証拠である。段 6 の C2 (述語が広すぎて正規 attempt を恒久拒否する) の
   closure が、param の判別力として実測された。

## 既登録 30 件

M1〜M7、M8a〜M8d、M9a〜M9d、M10a〜M10d、M11a〜M11b ほかの既登録 30 件も同じ走行で
全件 KILLED、HARNESS-STOP 0。anchor は全 35 件が `source.count(old) == 1` を満たし、
既登録分の逐語は本 wave で 1 byte も変更していない。

## 診断走行の erratum (`DW-M02`)

統合 commit 前に、worktree を汚さない隔離 scratch (`/scr`) で診断走行を試みた
(`874776.nqsv`、bnode045)。`mutations=35 killed=35 survived=0 stops=0` を得たが、
**baseline の失敗が 123 node あり無効**である。scratch copy が `.git` と submodule を欠くため
T-126 テスト群が baseline で落ちており、事前登録の期待赤が baseline 失敗集合に埋もれた。
各 mutation の `new_failed_nodes` は meta-test 1 件のみで、単一理由性の裏取りにならない。
初回結果は消さず、本走 (`875906.nqsv`) を権威とする。worktree の前後 SHA-256 は一致しており、
診断走行による汚染はない。
