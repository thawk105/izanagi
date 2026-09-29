---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-ro-gc-publish
seq: 2
---

## 新規

### {{F:same-value-pin-automerge}}. 2 つの wave が同じ件数 pin を同じ値へ書き換え、git の 3-way 合成が衝突なしで 1 回分の加算だけを残した [手順漏れ] [near miss]

- 事象: 2026-09-30、[T-2911] VHash md_22 wave の受入前に local main 17995a4fe (VHash hot block wave が着地) を取り込むと、登録簿 7 file が衝突した。衝突は「同じ位置へ別の項目を足した」型で和集合にすれば解けるが、衝突の外で、両 wave がそれぞれ新 macro 3 件を足したことに伴う件数 pin (`_COMPILE_TIME_BRANCH_MACROS` 51→54、`MEANING_SUPPORTED_MACROS` 52→55、交差表の `proven-unreachable` 55→58・65→68、s8b sink の `covered` 69→72 など) を**同じ新値へ**書き換えていた。git は両側が同一の変更をしたと見て衝突なしで 1 回分だけを残すので、合成結果の pin は両 wave の追加の合算 (+6) でなく +3 のままになる。登録項目の衝突だけを解いて commit すると受入で赤になり、合算がたまたま別の変更と打ち消し合えば誤った件数で緑になりうる。
- 根本原因: 件数 pin は「集合の要素数」という派生値で、両側の追加が独立でも書き換え後の literal は一致しうる。3-way 合成は literal の一致を「同じ変更」と扱うので、派生値の合算が要る箇所を衝突として表に出さない。
- 恒久対応: 両側が同じ登録簿へ追加した取り込みでは、衝突の有無にかかわらず、両側差分の数値 literal の変更を突き合わせ、同じ行を両側が同値へ書き換えた箇所を合成の対象として列挙し、合成後のコードから値を導出する (本 wave の段 6 追補裁定 FM-2、`output/insights/2026-09-29/vhash-readonly-gc-publish/README.md`)。memory `acceptance-discipline` に手順を置く。
- 再発検知: 取り込みの前に、merge-base から両側への差分で `-`/`+` の対になった数値 literal の変更を両側で比べ、同じ行が同じ新値へ変わっていれば赤として扱う。

## 再発

### F815

- **再発: 2026-09-30** (実害: Codex 子 1 本が prompt を読む前に停止、数分) — [T-2911] VHash md_22 wave の親が、main 取り込みの競合解消を Codex author に書かせるため、子の worktree で `git merge --no-ff --no-commit` した衝突状態を作ってそのまま子を投入した。子は `NG: Codex hook 配線の exact 検証に失敗: tools/pegasus/admission_registry.json: working bytes が HEAD blob から drift` で起動時に停止した (F815 の本文と同一の文言)。段取りの文面には「clean な木に書かせる」とあったが、衝突箇所を子に実物で見せたい意図で merge 状態の木を用意した。子の木を clean な wave HEAD に戻し、3 版と両側差分を job dir に射影し、main 側の file は `git show <main SHA>:<path>` で読ませる形で再投入した。

### F100

- **再発: 2026-09-29** (実害: session が約 15 分止まりユーザー手番を要した) — [T-2911] VHash md_22 wave の親が段 5 の実装子の dry-run を `cd <Codex author の子 worktree> && python3 tools/dev_wave_codex.py … --dry-run` で打ち、harness の追跡 cwd が子 worktree へ移って以後の全 Bash が隔離 guard に拒否された。これまでの復帰手順 `EnterWorktree(path=<自分の wave worktree>)` は、login の load average 約 45 の下で内部の `git worktree list` が 10 秒の上限を超え、11 回連続で時間切れになった。子エージェントも同じ cwd を継ぐので代行できず、ユーザーの `! cd` も同じ guard に拒否された。ユーザーの許可を得て `ExitWorktree(keep)` で抜け、元の作業場所から実装子を起動し、約 20 分後に負荷が下がって同じ worktree で作業を続けた。書き込みの取り違えは無い。同型: `dev_wave_codex.py` は `--repo-root` を取るので `cd` は要らない。高負荷時は `EnterWorktree(path)` が効かないことがあるので、そもそも `cd` を前置しない (memory `worktree-discipline` の「cwd の罠」、本エントリの 2026-09-18 の 3 件と同型)。

### F110

- **再発: 2026-09-29** (near miss、計算ノード job 1 本 428 秒を空費) — [T-2911] VHash md_22 の driver が Cicada の verify の受理条件に判定器の `integrity.clean` を要求していた。`Integrity.clean()` は数値項目・commit 照合に加えて証拠面 (X/P/I) を要求し、Cicada には証拠面が無いので**どの走行でも偽**だった (上限 indeterminate の理由そのもの)。verify1 の 24 走は巡回 0・数値項目 0・txn 数 = commit 数だったのに driver は rc=1 を返した。段 6 fix5 で先例 (md_14 の検査起動器の `stock_pass`) と同じ「数値項目 0 かつ txn 数一致」に直し、verify2 で 24/24 受理。段 4 の裁定 (B-3) を書いた時点で「その field が実環境で取りうる値を実測し、要求する値が到達可能か確かめてから述語を採用する」(DW-O13) を Cicada の既存 verify 出力 (md_3 の表) に当てていなかった。記録 = `output/insights/2026-09-29/vhash-readonly-gc-publish/README.md` §4・§12、`verbatim/s6-fix5-ruling.md`。

### F139

- **再発: 2026-09-29** — [T-2911] VHash md_22 の新 driver が計算ノードの smoke で 2 回止まった。(1) workload macro の owner TU `cc/cicada/ycsb_cicada.cc` が masstree の `config.h` (build 時にしか生成されない) を include し、新しい source copy で condition gate の前処理が失敗 (smoke1、job 内 19 秒)。(2) 計器 build に長い tx 用 macro の中でだけ定義される実行時 flag (`izanagi_long_kind`) を渡し `unknown command line flag` (smoke2)。どちらも先例 (md_14 の driver の `dependency` 腕、silo_policy_coverage の `_prepare_build_dependencies`、vlife patch の macro と flag の対応) に答えがあった。段 5 の実装子の prompt に「既存 driver・CCBench との外部交点表」を作らせたが、依存物 build の順序と flag の定義 macro は表に入っていなかった。恒久対応は F139 のまま (実機の書式・生成物は先例の実装か最安の生死確認で確かめてから driver に書く)。記録 = 同 README §12、`verbatim/s6-fix3-ruling.md`・`s6-fix4-ruling.md`。
