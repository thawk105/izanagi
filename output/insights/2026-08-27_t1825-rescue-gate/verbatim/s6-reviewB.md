### 所見 1: 新 schema にも無条件 `false` の削除許可 field が再生成されている
- 重大度: must-fix
- 型: 発火しない保証
- 根拠: `s4-adjudication.md:92-94` は死んだ許可 field の再作成を禁止するが、`tools/check_branch_rescue.py:1247` と `tools/check_branch_rescue.py:1309` は `branch_delete_authorized: False` を常に出力する。`tools/check_branch_rescue.py:1701-1710` の判断集約はこの値を一切参照しない。
- 成果物影響: 新 JSON にも判断を変えない定数 field が残り、実在しない削除防壁を consumer に読ませる。
- 提案: 旧 checker から受け取る値の境界検査 `tools/check_branch_rescue.py:1296-1297` だけを残し、新 schema へは再出力しない。JSON 全階層に authorization field が無いことを負例で固定する。

### 所見 2: audit の必須終端が欠けても `--ledger-check` は rc=0 を返せる
- 重大度: must-fix
- 型: 契約と実物の不一致
- 根拠: `docs/unreachable-object-ledger.md:85-89` は最終 `elapsed_seconds=` 欠落を削除停止と定める。一方、`tools/check_branch_rescue.py:1444-1456` の完全性判定は summary、commit 行数、rc だけを検査する。このため stdout が逐語 `要確認 0 件` のみで rc=0 なら完全扱いとなり、`tools/check_branch_rescue.py:1725-1729` から rc=0 へ落ちる。
- 成果物影響: 打ち切りまたは契約不完全な audit 出力を「未記帳ゼロ」と受理し、空台帳のまま通知を出さない。
- 提案: audit の公開終端を厳密に検査し、欠落・重複・終端後の出力を `audit-contract-invalid`、rc=2 にする。`要確認 0 件` だけの負例を追加する。

### 所見 3: 配線テストは frontmatter と単なる言及を実行配線として受理する
- 重大度: must-fix
- 型: 発火しない保証
- 根拠: 現物の配線は `.claude/commands/cleanup-branches.md:17-20` に可視の実行命令として存在する。しかし `orchestrator/tests/test_branch_rescue_ledger.py:25-43` は frontmatter を除外せず、同 file `:72-75` は任意の可視行に path substring があることしか検査しない。例えば description に両 path を置き、本文を「実行しない」としても緑になる。
- 成果物影響: 実行 caller が消えても path の言及だけで検査を通り、gate が再び呼び手ゼロになり得る。
- 提案: frontmatter、fence、comment を除外した §1 本文について、`python3 tools/check_branch_rescue.py`、`--ledger-check`、全候補を一括で渡す命令を同じ bullet から検査する。否定文と frontmatter-only の変異を赤にする。

### 所見 4: 台帳の `gc_headroom_at_loss` が標本由来であることは schema に固定されていない
- 重大度: should-fix
- 型: 意味の欠落
- 根拠: `tools/check_branch_rescue.py:1097-1100` の実行時 `headroom` は fanout `17` の標本由来で、総 loose 数は別の観測値である。しかし `docs/unreachable-object-ledger.md:31-33` は三 field を単に integer とし、`tools/check_branch_rescue.py:1341-1350` も型しか検査しない。`parent-dogfood.md:89-90` が指摘した由来は未固定である。
- 成果物影響: 禁止された `gc.auto - total loose count` 由来の値でも正規 entry として受理され、台帳上の余裕を過大表示できる。
- 提案: 標本 count、標本 threshold、標本 headroom と総 loose 観測値を名前で分離し、`headroom = max(threshold - sample_count, 0)` を検証する。

## 総括

- blocker: 0
- must-fix: 3
- should-fix: 1
- land 判定: **NO-GO**
- この gate は実データで発火するか: **呼出し自体は YES、契約どおりの完全な gate としては NO**。現 command は実行命令であり、空台帳と正常な audit 非 0 件なら `tools/check_branch_rescue.py:1475-1510` から rc=3 に到達する。audit の rc 不一致、timeout、UTF-8 不正も rc=2 に倒れる。ただし所見 2 の終端欠落だけは rc=0 へ漏れる。

移動前後の既存安全義務、C3-1/C3-2/C3-3、23 field の片側追加・欠落検出、`object_retention_provided: false`、三つの coverage exclusion は静的には保持されている。command は 3,996 byte、SHA-256 は報告値 `dd4c31c...cde3` と一致した。D981 の「pin と対象を同じ patch で動かせる」構造は広がっても狭まってもおらず、現状維持である。pytest は実走していない。