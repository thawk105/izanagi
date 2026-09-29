---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-ro-gc-publish
seq: 2
---

## 再発

### F100

- **再発: 2026-09-29** (実害: session が約 15 分止まりユーザー手番を要した) — [T-2911] VHash md_22 wave の親が段 5 の実装子の dry-run を `cd <Codex author の子 worktree> && python3 tools/dev_wave_codex.py … --dry-run` で打ち、harness の追跡 cwd が子 worktree へ移って以後の全 Bash が隔離 guard に拒否された。これまでの復帰手順 `EnterWorktree(path=<自分の wave worktree>)` は、login の load average 約 45 の下で内部の `git worktree list` が 10 秒の上限を超え、11 回連続で時間切れになった。子エージェントも同じ cwd を継ぐので代行できず、ユーザーの `! cd` も同じ guard に拒否された。ユーザーの許可を得て `ExitWorktree(keep)` で抜け、元の作業場所から実装子を起動し、約 20 分後に負荷が下がって同じ worktree で作業を続けた。書き込みの取り違えは無い。同型: `dev_wave_codex.py` は `--repo-root` を取るので `cd` は要らない。高負荷時は `EnterWorktree(path)` が効かないことがあるので、そもそも `cd` を前置しない (memory `worktree-discipline` の「cwd の罠」、本エントリの 2026-09-18 の 3 件と同型)。

### F110

- **再発: 2026-09-29** (near miss、計算ノード job 1 本 428 秒を空費) — [T-2911] VHash md_22 の driver が Cicada の verify の受理条件に判定器の `integrity.clean` を要求していた。`Integrity.clean()` は数値項目・commit 照合に加えて証拠面 (X/P/I) を要求し、Cicada には証拠面が無いので**どの走行でも偽**だった (上限 indeterminate の理由そのもの)。verify1 の 24 走は巡回 0・数値項目 0・txn 数 = commit 数だったのに driver は rc=1 を返した。段 6 fix5 で先例 (md_14 の検査起動器の `stock_pass`) と同じ「数値項目 0 かつ txn 数一致」に直し、verify2 で 24/24 受理。段 4 の裁定 (B-3) を書いた時点で「その field が実環境で取りうる値を実測し、要求する値が到達可能か確かめてから述語を採用する」(DW-O13) を Cicada の既存 verify 出力 (md_3 の表) に当てていなかった。記録 = `output/insights/2026-09-29/vhash-readonly-gc-publish/README.md` §4・§12、`verbatim/s6-fix5-ruling.md`。

### F139

- **再発: 2026-09-29** — [T-2911] VHash md_22 の新 driver が計算ノードの smoke で 2 回止まった。(1) workload macro の owner TU `cc/cicada/ycsb_cicada.cc` が masstree の `config.h` (build 時にしか生成されない) を include し、新しい source copy で condition gate の前処理が失敗 (smoke1、job 内 19 秒)。(2) 計器 build に長い tx 用 macro の中でだけ定義される実行時 flag (`izanagi_long_kind`) を渡し `unknown command line flag` (smoke2)。どちらも先例 (md_14 の driver の `dependency` 腕、silo_policy_coverage の `_prepare_build_dependencies`、vlife patch の macro と flag の対応) に答えがあった。段 5 の実装子の prompt に「既存 driver・CCBench との外部交点表」を作らせたが、依存物 build の順序と flag の定義 macro は表に入っていなかった。恒久対応は F139 のまま (実機の書式・生成物は先例の実装か最安の生死確認で確かめてから driver に書く)。記録 = 同 README §12、`verbatim/s6-fix3-ruling.md`・`s6-fix4-ruling.md`。
