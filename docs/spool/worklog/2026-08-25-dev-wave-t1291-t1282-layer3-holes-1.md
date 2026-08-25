---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1291-t1282-layer3-holes
seq: 1
title: [T-1291]+[T-1282] 層 3 の bench payload 閉包を producer から導出し、名指し artifact を描画可能にした。[T-1282] の起票時の前提は実測で反証した (コード + テスト、branch worktree-dev-wave-t1291-t1282-layer3-holes)
---

## 本文

**[T-1282] の起票時の前提は誤りだった。** 「bench 到達走では層 3 の失敗文言がどこにも永続しない」
という entry 612 の記述は、`report.json` だけを探して `attempts.jsonl` を見ていなかったことによる。
文言は `run-finish` イベントの `cell_admission_failures` として **fsync 済みで永続していた**。
これを入れた `d5f1c95f` (2026-08-16) は、entry 612 が記述した pilot 走行 HEAD `5a19b8ab`
(2026-08-17) の**祖先**であり、当該 4 走にも効いていた。journal 追記は関門
`assert_campaign_layer3_chain` より**手前**で起きる。

**ただし実務上の訴えは正しく、原因が違った。** 永続する文言は「layer3 schema 検証に失敗」という
潰れた 1 行で、`jsonschema` が持っていた validator・instance path・offending property は
`__cause__` にしか無く捨てられていた。そこで直す対象を「2 つ目の artifact を足す」から
「既に永続している記録を構造化して濃くする」へ差し替えた。段 2 プランの当初案 (専用 artifact を
書く) は不採用とした — 診断の正本が二重化するうえ、journal は関門の手前で
`attempt_journal_sha256` により封印されるので、関門自身の失敗理由は後から追記できない。

**key の穴だけでは成果物が得られなかった。** `screening` を schema へ足した直後、名指し artifact は
今度は `settled: null` で落ちた。全 30 campaign の実測値域は `False` 296 件 / `True` 76 件 /
不在 54 件 / **`null` 1 件**で、その `null` 1 件は **`screening: true` の行そのもの**だった。
key の穴と値の穴が同じ 1 行に同居しており、両方塞いで初めて描画できる。これは B-9 が要求する
「値整合検査」の側の穴である。

**段 3 の 2 レンズが `settled` の直し方で正面から対立した。** 一方は「schema は boolean のまま
view 側で `null` を不在へ正規化せよ」、他方は「schema を boolean/null にせよ」。**後者を採った。**
根拠は 3 つとも実測である — (1) `layer3_report.py` の docstring が report を「完全射影」と定義して
おり、producer が出した key を view で消すのは契約違反で「静定が不明」と「key が無い」を
区別不能にする、(2) 層 3 report の `runs[].settled` を読む consumer は test 外に**存在しない**
(全件検索)、(3) `settled` は `required` に無く不在が既に 54 件許容されている = `null` は実質的な
受理集合の拡大ではなく不在より情報の多い形を受け取るだけで、producer comment のとおり
fails-closed の一次ゲートは `competing_bench_pids` である。

**両レンズが揃って主張した「`schema_version` を v4 へ上げよ」は不採用にした。** 論点は
「旧 checkout の v3 reader が新 v3 document を読めない」= **前方**互換であり、本 wave の要求
(**後方**互換) とは別物である。先例 2 件を実測した — `rep_returncodes` は `067f4b1f` (07-20) で
`schema_version` を v2 のまま `runs.items` へ追加、`perf_observation` は `f383d75d` (08-17) で
v3 のまま追加。v4 化は reader を v2/v3/v4 の 3 経路にし、現行の「v3 schema を変異させて v2 reader を
導く」導出鎖を複雑にするため、後方互換をむしろ壊しやすい。**前方互換は保証しない**ことを
{{D:layer3-runs-widening-holds-version}} に記録した。

**診断の追加そのものが新しい失敗経路を作っていた。** 抽出は全域関数のはずだったが、
`validator_value` に surrogate escape を含むと抽出成功後の `_canonical_json_bytes` が
`PredictionRunnerError` を投げ、`run-finish` の追記が飛んで元の関門例外が別型へ置換される。
レビューが指摘し、親が独立に再現した。返却前に canonical encode/decode を通し失敗を degraded 形へ
閉じることで解消した ({{F:diagnosis-adds-new-failure-path}})。

**エージェント工数と基盤事象。** codex 子は plan 1 / consult 2 / author 2 / review 2 / fix 3 の
計 10 本。うち **`evidence_status=invalid` による不採用が 2 件** (段 2 plan、段 6 fix-b)。いずれも
codex 側 rc=0 で完走し成果物 bytes も十分だったが launcher が公開を拒んだもので、外から診断できない。
再投入で解決した。**再投入時の落とし穴を 2 つ実測した** — (a) `--max-attempts > 1` は
`--sandbox read-only` のときだけ許可され workspace-write では argv 段階で rc=2、
(b) job-id は prompt 内容の sha256 なので同じ prompt で再投入すると
`NG: 既存の完全な receipt は上書きできない` で弾かれ、prompt 内容を変えて分離する必要がある。

**段 5 の実装子 2 本はテストを 1 件も実走できなかった** (自 cgroup が 16 GiB 上限に当たり pytest
child が起動せず、runner rc=16)。したがって子の「done」は静的実装の申告であって検査通過の証拠では
なく、親の実走で初めて 7 件の赤が判明した。7 件は単一根本原因で、新テストが `runs.items` を単独
schema として validator へ渡すため `$ref: #/definitions/wal_ref` が解決できず、目的の検査へ到達する
前に例外死していた。**つまりその 7 件は受理集合を何も検査していなかった。**

**未 commit の作業ツリーでテストを走らせてはならない。** 1 回目の焦点走は 239 件赤
(10 failed + 229 errors) になったが、原因は自 wave の回帰ではなく
`contract-loader-drift: disk bytes が HEAD blob と不一致` だった。統合を commit した後は 0 件。

## 次の一手差分

### 完了

- [T-1291] `screening` / `screening_disabled` を層 3 の `runs.items` へ optional 追加し、
  producer 側に 17 key の runtime 閉包検査を置いた。母集合は手書き定数を正本にせず
  `_run_bench` の実代入を AST で収集して照合する。名指し artifact
  `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90` が `build_report` を
  最後まで通ることを実測で確認した (runs 2 行、うち 1 行が `screening: true`)。
  remaining: none
  base: ad9d9729b3280bf0cc6630cd64453aeaca5999daed146afe3d23a13af412357c

- [T-1282] 起票時の前提を実測で反証したうえで、real な穴 (永続する文言が潰れた 1 行で
  offending property が読めない) を閉じた。`jsonschema` の構造化 cause を catch 点で射影し、
  関門の手前で fsync される `run-finish` イベントへ載せた。関門の挙動・終了 rc・
  `report.json` の有無は変えていない。
  remaining: none
  base: 927d303765955af18f3a3a612466788dfd6f3a4e8e912495053e01158ebeaa9c

### 新規

- {{T:layer3-chain-gate-reason-not-persisted}} **P2・新規**: 関門
  `assert_campaign_layer3_chain` 自身の失敗理由はどこにも永続しない。cell 側の失敗は journal に
  残るが、gate がなぜ発火したかは残らない。journal は `attempt_journal_sha256` により関門の手前で
  封印されるため後追い追記ができず、第 2 artifact が要る。その consumer 意味論 (成功走と誤認
  されないこと) は独立の裁定を要する。

- {{T:guided-second-bench-done-producer}} **P2・新規**: `orchestrator/campaign/guided.py` も
  `STAGE_BENCH_DONE` を直接 emit するが payload は 3 key しかなく、層 3 の必須 `cv` / `rounds` を
  欠く。historical-raw admission を通った guided WAL は層 3 で必ず落ちる。本 wave の閉包は
  `pipeline._run_bench` に限定し、検査の docstring へ scope 限定を明記した。既存の穴であり
  本 wave が作ったものではない。

- {{T:bench-payload-extra-second-key}} **P2・新規**: `_BENCH_PAYLOAD_EXTRA_KEYS` に 2 つ目の key を
  足した瞬間、1 key だけ渡す既存 caller が missing 扱いで拒否される。現 repo に該当 caller は
  無いので既存経路は壊れないが、第 2 拡張を入れる際は単一 union でなく「許可する exact key
  bundle の閉集合」にする必要がある。
