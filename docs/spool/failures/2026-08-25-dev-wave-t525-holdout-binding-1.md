---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t525-holdout-binding
seq: 1
---

## 新規

### {{F:mutation-only-central-scenario-gap}}. wave の中心シナリオに直接テストが無く、緑 1670 件と敵対レビュー 2 本が揃って見落とした [テスト代表性]

- 事象: [T-525] は「freeze と違う条件の測定が H1 として receipt 化される」穴を閉じる wave である。
  実装後、焦点走 27 file が 1670 passed / 0 failed、段 6 の敵対レビュー 2 本も
  この点を所見に挙げなかった。ところが変異 matrix で
  `_assert_each_protected_argv_value_matches` の不一致 raise と
  `_consume_holdout_observation_run_once` の条件比較を **それぞれ単独で無効化しても、
  両方同時に無効化しても** テストが 1 件も落ちなかった (544 件緑のまま)。
- 根本原因: 既存テストが検査していたのは (a) 形が非 canonical な argv (ハイフン別名・
  2 token・終端後・bare・undashed) と (b) 値の**書式**が不正な argv (`0.90` / `080` /
  `false` / `0` / `00`) の 2 種類だけだった。どちらも手前の形式検査で落ちるため、
  束縛層まで到達しない。**「書式は妥当で値だけ freeze と違う」argv** —
  H1 の admission を持ったまま `--ycsb_rratio=20` や `--thread_num=24` で走る形 —
  を検査したテストが 1 件も無かった。これは wave が閉じようとしている当の中心シナリオである。
  拒否理由の網羅 (field x 不在/不正形/不一致) を「不一致」まで書いたつもりで、
  実際には不正形の case しか置いていなかった。
- 恒久対応: `orchestrator/tests/test_holdout_observation.py` の
  `test_canonical_value_mismatches_reach_both_binding_layers_and_are_rejected` を追加した。
  5 保護 field それぞれについて canonical かつ書式妥当な不一致値を本物の admission で拒否させ、
  値照合層と条件比較層が独立に発火する形にした。上記 3 変異はすべて KILLED になった。
- 再発検知: **単独変異が生存したとき「他層の mask」で片付けない。** 両層同時変異まで進め、
  それでも生存するならテスト集合の穴である。防壁が二重にあるほど単独変異は生存しやすく、
  masking と穴は単独変異の結果からは区別できない。
  受理集合を狭める wave では「拒否理由の網羅」を宣言する前に、
  **不在・不正形・不一致の 3 種が実際に別々の case として存在するか**を数える。

### {{F:not-accepted-artifact-adopted-on-content-check}}. 起動器が不採用にした成果物を内容検査の緑だけで採用した [権限逸脱]

- 事象: [T-525] の段 2 で codex 子が `evidence_status=invalid` / `outcome=not_accepted` /
  `launcher_rc=1` になり `-o` が書かれなかった。`attempt-0001.output.md` は 20,886 bytes で
  内容は完全だった。親は `tools/check_codex_output.py` rc=0 を確認してこれを採用し、
  段 3・4 を進めた。**F540 は「不採用の成果物を採用へ回してはならない — 内容検査が緑でも
  launcher の赤を迂回することになる」と明記している。** 親はこの逸脱を段 8 の改善候補として
  handoff へ書きながら、そのまま先へ進んだ。
- 根本原因: `DW-O01` の「採用は `tools/check_codex_output.py` の rc=0」という一文だけを読むと
  「rc=0 なら採用してよい」と読める。rc=0 は必要条件であって十分条件ではないが、
  入口にその限定が書かれていない。F540 の禁止は failures 台帳側にあり、
  段 2 の実行時に読む節ではない。
- 恒久対応: F540 が定める手当て (同じ prompt を別の `--job-id` で 1 回だけ再投入) を実施し、
  `outcome=accepted` / `launcher_rc=0` / `evidence_status=complete` の成果物を正規採用した。
  不採用版は「保全して読む価値はあるが唯一の根拠にしてはならない」二次資料として残した。
  **拘束力を持つ禁止は F540 本文の「不採用の成果物を採用へ回してはならない」であり、
  本エントリはその再発事例である。** `DW-O01` へ `launcher_rc=0` も必須と追記しようとしたが、
  `docs/dev-wave/**` の L1.5 予算が満杯で入らなかった (この 1 文だけで 9653 bytes > 予算 9566)。
  安全義務を削って空きを作ることは自己改善契約が禁じるため、入口追記は
  {{T:dw-o01-launcher-rc-budget}} としてユーザー裁定へ送った。
- 再発検知: receipt の `outcome` と `launcher_rc` を見ずに `check_codex_output.py` の rc だけで
  採用判断をしない。子の成果物を採用する前に receipt の 2 field を必ず読む。

## supersede 追記

- F540 **supersede: 2026-08-25** — 3 つ目の型の発火条件を特定した。子が読んだ repo の行に生の U+2028 / U+2029 が含まれると、codex CLI がその byte を JSONL event の `aggregated_output` へそのまま出し、`tools/codex_worker_launch.py` が JSONL を `str.splitlines()` で切る (6 箇所) ため 1 event 行が複数断片に割れて `stdout_invalid` が立つ。JSON はこの 2 文字を文字列内に生で許すが Python の `splitlines()` は改行として扱う、という不一致が原因である。追跡 14,208 file の全数検査で該当は 5 file (`orchestrator/campaign/p3_autonomous_workload_trial.py:2213` の sanitizer 正規表現、`orchestrator/tests/test_p3_autonomous_workload_trial.py:2837`、insight 3 件)。診断手順は events.jsonl の各行を `json.loads` し、割れた行の前後で当該 2 文字を探す。回避は当該行域を「読むな」と prompt へ明記することで、[T-525] では invalid が再発しなかった。恒久対応の候補は JSONL 分割を `split("\n")` へ変えることで、tool の出力契約に触れるため裁定パッケージへ回す。
