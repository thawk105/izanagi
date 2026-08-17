---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1222-growth-leak-fix
seq: 2
---

## 新規

### {{F:codex-evidence-nfc-fixture}}. repo 自身の非 NFC fixture が、それを読む codex 子の evidence を全損させる [コンテキスト浪費] [手順漏れ]

- 事象: 段 6 のレビュー子 3 本と fix 子 1 本が `accepted=False` / `evidence_status=invalid` で
  不受理になった。4 本とも正常完走している (`codex_exit_code=0`、`validator_rc=0`、
  `termination_verified=True`、`metering_status=complete`、出力 4.6〜10.5 KB、`## 総括` あり)。
  同じ wave の plan 子・consult 子 2 本・author 子は成功した。合計 4 本ぶんの
  レビュー工数と約 35 分が失われ、親は原因特定に更に 20 分を費やした。
- 根本原因: `orchestrator/tests/test_check_docs.py:4718, 4741` は NFC 検査そのものの fixture として
  **意図的に非 NFC の行**を持つ (`プ` を `フ` + U+309A COMBINING KATAKANA-HIRAGANA
  SEMI-VOICED SOUND MARK の結合列で書いたもの)。段 6 の子はこの file を読む/編集するのが仕事で、
  読んだ内容が codex の stdout event 列に載る。launcher の `parse_jsonl`
  (`tools/codex_worker_launch.py` の `_drain_stdout`) がその行を
  「JSONL は Unicode NFC でなければならない」で拒否し、`state.stdout_invalid = True` になる。
  `_evidence_status` はこれを `invalid` と判定し、成果物は捨てられる。
  **子の落ち度でも出力内容の問題でもない。**
- 恒久対応: memory `codex-evidence-loss-paths` の「repo 内非 NFC 行の echo」に、
  **加害側の具体 path (`orchestrator/tests/test_check_docs.py:4718,4741`) と回避経路**を足す。
  回避経路 = 子に当該領域を読ませず、`git show <commit>` で差分を監査させる
  (親が両 commit の `git show` 出力が NFC 清潔であることを確認してから渡す)。
  `grep -n` する場合も 4700〜4760 行に当たる pattern を使わせない。
- 再発検知: 不受理が出たら `tools/codex_worker_launch.py` の `parse_jsonl` を
  当該子の `attempt-0001.events.jsonl` へ 1 行ずつ適用し、拒否行と理由を出す。
  成功した子の event 列は拒否 0 行になるので、両者の差で原因行を特定できる。
  親はこの手順で拒否理由がすべて NFC であることを確定した。
- 限界: 現状は運用回避であり機械防壁ではない。非 NFC fixture を持つ file は他にもありうるので、
  「codex 子に読ませる前に対象 file の NFC 性を検査する」形の前置検査は未実装。

### {{F:uncommitted-work-lost-to-mutation-restore}}. 変異の復元が、同じ file の未 commit 修正を巻き戻した [手順漏れ]

- 事象: 段 6 fix 第 2 巡が `tools/check_docs.py` の cache identity へ `st_mode` と
  `st_ctime_ns` を足した (6 行)。親はそれを commit しないまま変異 M-F を同 file へ当て、
  後始末に `git checkout -- tools/check_docs.py` を打った。**変異と一緒に fix の 6 行も消えた。**
  テスト側 223 行は別 file だったため無事だった。復旧に fix 子 1 巡を追加で要した。
- 根本原因: `DW-O19` は「本走は統合 commit 後に限る」と定めている。親は変異 matrix 第 1 巡では
  これを守り `7b40d111` を作ってから変異を当てたが、第 2 巡では**同じ手順を省いた**。
  `git checkout --` は「commit 済みの状態へ戻す」操作なので、未 commit の正当な修正と
  一時変異を区別しない。
- 恒久対応: `DW-O19` の既存条文 (本走は統合 commit 後に限る) が正しく、docs の追加は不要。
  親の遵守漏れである。変異を当てる直前に `git status --porcelain <対象 file>` が空であることを
  確認する運用を memory へ書く。
- 再発検知: 変異適用 script の中で、対象 file が dirty なら適用を拒否する
  (本 wave の `mutate.py` は `clean()` 検査を持っており、これは正しく働いた。
  第 2 巡で親が使ったのは `mutate.py` ではなく素の `python3 -c` だったため検査を経ていない)。
- 副産物: identity 拡張が消えた状態の走行が、期せずして「identity から st_mode/st_ctime_ns を
  落とす変異」になり、`test_read_text_cache_invalidates_revoked_read_permission` ほか
  2 node が赤になった。新設テストが production の退行を捕まえることの実証にはなった。

## 再発

### F1

- **再発: 2026-08-17** — 親が進捗報告に書いた時刻 4 件 (09:05 / 09:32 / 09:47 / 10:50) が
  いずれも実測でなく推定で、実際は 08:52 / 08:54 / 09:01 / 10:45 だった。`date` を打たずに
  体感で書いたことが原因である。memory `reports-include-jst-timestamp` は「実測時刻を明記」と
  定めているが、**測らずに書く**経路を塞いでいなかった。以後は報告に時刻を書く直前に
  必ず `date` を実行する。
