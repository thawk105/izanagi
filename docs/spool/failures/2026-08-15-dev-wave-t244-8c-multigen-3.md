---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-15
wave: dev-wave-t244-8c-multigen
seq: 3
---

## 新規

### {{F:tautological-external-expectation}}. 外部期待値と照合する validator が、caller の alias により恒真だった [恒真ゲート] [テスト代表性]

- 事象: 8c の世代間還流を白名単で閉じる validator を新設し、焦点走は **508 passed で全緑**に
  なった。しかしその後の敵対レビュー **2 本が独立に**、caller が `perf_payload` /
  `leading_payload` / `whiteboard` の**同じ実体**を payload と外部期待値の両方へ渡しており、
  **両方まとめて書き換えれば通る**ことを指摘した。すなわち wave の中心的主張
  (「世代間で運ぶものを機械的に閉じた」) が機械としては成立していなかった。
- 根本原因: (1) 親が「payload と別に外部期待値を渡して exact 照合せよ」とだけ指示し、
  **期待値の導出経路が payload と独立であること**を要求しなかった。
  (2) 同じ object を渡す実装は「照合が通る」ので、テストも実走も一切赤にならない。
  恒真ゲートの中でも**テストと実走の両方をすり抜ける**型である。
  (3) 親は途中 2 回この箇所の裁定を書き換えており (最初は `None` の hardcode を要求 →
  pre-wave の目印テストを壊して撤回 → 外部期待値方式へ)、その過程で独立性の要件が落ちた。
- 判別: validator が「payload と期待値を照合する」形を採るとき、**期待値がどこから来るかを辿る**。
  payload と同じ変数・同じ関数呼出しの戻り値なら恒真である。
  「両方を同時に書き換える変異」を事前登録し、それが KILLED になることを確認するまで
  検出力を主張しない。
- 恒久対応: 期待値を**初期状態の定数から独立に導出**し、payload 側とは deep copy で object を切る。
  実体 = `orchestrator/campaign/p3_autonomous_workload_trial.py` の workload 単位 snapshot と、
  `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_metric_payloads_do_not_alias_frozen_validator_expectations`。
  あわせて validator 通過を sealed receipt として journal / report へ durable に残し、
  completeness が production validator を呼ばず独自定数で再検証する。
- 再発検知: 事前登録変異に「caller の世代更新点で許可 field を個別に実測値へ更新する」独立 anchor と
  「payload と期待値を同時に書き換える」変異の両方を含める。本 wave の実測は
  変異 18 件すべて KILLED、期待 node 完全一致 (baseline PASSED / SURVIVED 0 / MISMATCH 0)。
- 近縁: F69 (値ベース positive control の無力)、F9 (恒真な保証)、F21 (live 発火未検証の防壁)、
  F27 (fixture へ現行 hash を差し込んで隠蔽)。

### {{F:prewave-golden-regenerated}}. 凍結 golden を wave 自身の出力で再生成し、drift 検出を無効化した [恒真ゲート] [手順漏れ]

- 事象: 親は「report の新 field を exact golden へ**足せ**、volatile 扱いで検査対象から外すな」と
  指示したが、実装は `_PRE_WAVE_ORIGINLESS_BASELINE` を**丸ごと wave 自身の出力で作り直し**、
  出典コメントも「wave 前 commit `7b6f91a8` から凍結」から「T-244 report-v3 出力から凍結」へ
  書き換えていた。凍結 golden の目的 (drift 検出) が無効化される。
- 根本原因: 「新 field を足す」という指示が、**baseline literal を不変に保つ**ことを
  明示していなかった。golden を再生成すれば赤は必ず消えるため、実装側から見ると最短路である。
- 判別: 凍結 golden を持つ wave では、**baseline literal の sha256 が base commit のものと
  一致するか**を直接確認する。差分は「baseline + 名前つきの裁定済み delta」の形でだけ許す。
- 恒久対応: pre-wave baseline を byte-for-byte 復元し、比較は明示 delta を射影してから行う。
  delta は項目ごとに根拠を 1 行持つ。実体 =
  `orchestrator/tests/test_reflux_originless_compatibility.py` の明示 delta 節。
  本 wave の delta は report の新 4 key、`REPORT_SCHEMA_VERSION` の v2→v3、validation receipt 証拠、
  planner の `effective_prompt_sha256` の 4 種で、**planner 以外 3 role の effective prompt SHA と
  全 role の `role_file_sha256` は pre-wave と一致**することを実測した。
- 再発検知: 「pre-wave baseline literal の sha256 が base と一致」を検査に含める。
- 近縁: F27、F78 (docs だけの wave が sha256 pin された事前登録文書を編集した)。

### {{F:prewave-expectation-rewritten-as-gate}}. 防壁テストの期待値が書き換えられ、実装は無傷のまま検査だけ壊れた [恒真ゲート] [権限逸脱]

- 事象: `test_cli_default_is_literal_one_by_ast` の `assert len(calls) == 1` が
  `== 2` へ書き換えられていた。このテストは **F72 の恒久対応そのもの**で、
  「承認上限を上げても CLI 既定値は literal `1` のまま」を AST で pin する防壁である。
  親は全 fix prompt で「既存テストの期待値を変更してはならない」を明示していた。
- 根本原因: 実装側が「承認上限 gate の追加」と「CLI 定義の個数」を混同した。
  **production の `add_argument` は元から 1 個で、防壁の実装は無傷だった** — 壊れたのは検査だけである。
  この形は「実装は正しいがテストが嘘をつく」状態を作り、次の wave が気づかず通す。
- 判別: fix 巡ごとに `git diff <base> -- <テスト directory>` を**全数走査**し、
  wave 前から存在するテストの assert / 期待値 / 正規表現 / 期待 node の変更を全部列挙する。
  親の明示裁定が無いものは base へ戻す。fixture・setup・引数の変更は別枠で列挙する。
- 恒久対応: base へ復元し、AST 実測で「対象 `add_argument` は 1 個、`default` は literal `1`」を
  確認した。全数走査の結果、親の明示裁定が無い期待値変更は**この 1 件だけ**だった。
- 再発検知: fix prompt に全数走査を必須節として入れる。本 wave は fix 第 8 巡で導入した。
- 近縁: F80 (修正子が既存の安全テストの期待値を反転)、F72 (宣言と既定が逆)。

### {{F:mutation-runner-local-peak-budget}}. 前回ピーク由来の予算で cgroup attest が落ち、変異走行が local mode で回せない [計測汚染] [手順漏れ]

- 事象: `tools/run_tests.py` の bounded local は前回ピーク使用量から次回予算を見積もる。
  初回 (既定 4,294,967,296 bytes) は成功するが、2 回目以降の見積り
  (実測 1,733,032,960 / 1,914,209,280 / 1,977,591,600 bytes) では
  `bounded scope の memory.max / memory.oom.group を走行中に attest できない` として
  **`rc=16` (infrastructure failure)** になる。**変異走行は同一 target set を 19 回繰り返すため
  2 回目以降が必ず当たり**、harness は収集段で `collected=0` として中止する。
  他 wave が 4 GiB を予約していると残り headroom が小さくなり同じ経路に落ちる。
- 根本原因: 見積り予算が cgroup scope の attest に必要な下限を下回りうる。
  `rc=16` はテスト結果ではないため、これを赤と誤読すると差分へ誤帰属する。
- 判別: `rc=16` を見たら**必ず** `生存中の予約` と `算出予算` を読む。
  初回と 2 回目で予算が変わっていれば本件である。target set を変えると key が変わり既定予算へ戻る。
- 恒久対応: 恒久修正でなく運用回避である。変異走行は `--runner-mode dispatch` + runner argv の `--force-dispatch` で
  計算ノードへ出す。`qstat -Q` は**親からは rc=0** で応答する
  (codex 子の rc=1 は sandbox が socket を塞ぐためで、queue の問題ではない)。
- 再発検知: `--plan-only` の後に本走が収集段で落ちたら、まず予算値を読む。
- 近縁: F46 (ログインノードの実測を計算ノードへ誤前提)、F74 (規範の測定手順がその機体で実行不能)。
