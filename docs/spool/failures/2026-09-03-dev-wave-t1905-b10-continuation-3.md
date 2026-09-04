---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t1905-b10-continuation
seq: 3
---

## 新規

### {{F:qstat-job-memory-is-fork-sum}}. job 単位のメモリ表示を物理常駐量と読み、上限に迫っていると誤認した [計測汚染]

- 事象: 走行中の B-10 campaign job を `qstat` で見ると Memory が 115.29G まで跳ね、
  ユーザ利用上限 115GiB のすぐ下に見えた。短縮表示と `qstat -f` が同じ値を返すため
  読み違いではないと確認され、read-heavy (commit 数が約 4 倍) は上限を越えると誤認しかけた。
- 根本原因: 直列性検査器は `fork` で 16 子を作る。Linux の RSS は共有 copy-on-write ページを
  **触った全プロセスへ重複計上する**ため、job 単位の合計は親の常駐量の worker 数倍まで膨らむ。
  実測でもスパイクは隣接する定常値の 11.4-17.1 倍 (中心 13-14 倍) で並列度 16 と一致し、
  約 60 秒周期で 2 段に分かれた (fork する段が構文解析と辺候補計算の 2 つある)。
- 恒久対応: 並列化した producer の記憶量は **cgroup の `memory.current` を専用 scope で
  sampling して測る**。手順は `docs/pegasus-runbook.md` §7.0.0 が正本で、同節は
  「`/usr/bin/time -f %M` の per-process ピーク RSS を代理値にしてはならない — 多重プロセスを
  worker 数分の 1 に過小評価し、共有ページを二重計上し、file / slab / page table の charge を
  落とす」と既に明記している。**`qstat` の job 単位 Memory も同じ理由で代理値にしない。**
- 再発検知: 並列 producer の記憶量を論じる記録では、値の出所 (cgroup か per-process 合計か) を
  明示し、合計値を使うなら並列度で割った値と定常値の桁が合うかを併記する。
  桁が合わないまま上限との比較を書いたら誤りとする。

### {{F:d1480-cond2-unsatisfiable}}. 投入前の試し打ちを求める裁定が、実行面の不在と同一性束縛によって満たせなくなった [手順漏れ]

- 事象: D1480 条件 2 は「45 cell 全滅の可能性を 1 cell の安い試し打ちで本走の前に潰す」ことを
  ユーザー裁定として求めている。B-10 read-heavy の投入前にこれを満たそうとしたが、
  **現行 CLI にその実行面が無い** — `verify-perf` は 15 変種 45 セルへ進み、
  `report` は exact 135 セルを要求し、`probe` phase は待ちループの実測であって
  セルの試し打ちではない。
- 根本原因: 実行面を足すには driver を編集するしかないが、driver 自身の bytes が
  `analysis_code_sha256` として campaign 同一性へ入る。**足した瞬間に、同じ系列で走行中の
  balanced 45 セルが最終集約から外れる。** 条件 2 を字義どおり満たすことと、
  D1509 決定 3 が守ろうとした完走分を残すことが正面から衝突する。
  試し打ち機構を「本走の前に作る」ものとして設計せず、本走の driver と同一性を共有する形に
  置いたことが原因である。
- 恒久対応: **ユーザー裁定へ返した** (設計文書 §9 の問い 6 に 3 択で記録)。
  併せて、以後「投入前の試し打ち」を裁定条件に含める設計では、
  **試し打ちの実行面が本走の同一性束縛の外にあるか**を設計時に確かめる義務を
  同 §9 へ明記した。実体は `docs/b10-multinode-formal-run-design.md` §9 の問い 6。
- 再発検知: 投入前条件を持つ設計を書くとき、その条件を満たす操作が
  現行 CLI に存在するかを設計文書へ file:line で書く。書けなければ条件として採らない。

### {{F:policy-bytes-pin-missed-by-key-and-value-search}}. 設定 1 値の変更が、file 全体の hash pin を外して受入で赤になった [手順漏れ]

- 事象: `tools/pegasus/policy.json` の `b10_backoff_shape_walltime_s` を 43200 から 86400 へ
  変えたところ、受入全走が 20300 件中 2 件の赤を返した。
  `test_shared_pegasus_policy_owns_no_t126_qualification_keys` と
  `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` である。
  原因は同 file の**現行 bytes を sha256 で明示 pin する golden**
  (`orchestrator/tests/pegasus_policy_expected_goldens.py` の
  `EXPECTED_CURRENT_PEGASUS_POLICY_SHA256`) が外れたことだった。
- 根本原因: 親は pin 閉包を **key 名** (`b10_backoff_shape_walltime_s`) と
  **値の字面** (`43200` / `12:00:00` / `12 * 60 * 60`) で取った。
  **file 全体の hash を持つ pin は key 名も値も本文に持たないので、どちらの検索にも掛からない。**
  DW-O09 が指示する `git grep -n "<成果物パス>"` を走らせていなかった。
  段 2 のプランと段 3・段 6 の 4 レンズも全員が同じ探し方をしたので誰も見つけず、
  受入全走だけが見つけた。段 6 の焦点走も変更 file と同名の test file だけで、
  DW-O26 が求める「変更した production file を参照する consumer test」を引いていなかった。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O09` が既に
  「`git grep -n "<成果物パス>"` を使い bytes を pin する台帳・test・trust root を全列挙する」
  と定めており、規約側の不足ではない。**規約どおりに引かなかったことが原因である。**
  再発防止は既存 `DW-O09` の遵守と、`DW-O26` の焦点走拡張の遵守に閉じる。
  新しい節は足さない。
- 再発検知: 設定 file の中の 1 値を変える wave では、段 0 の閉包に
  `git grep -n "<変更する file の repo 相対 path>"` の出力を残す。
  この出力が無いまま段 5 へ進んだら閉包未了とする。
