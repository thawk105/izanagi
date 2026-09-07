---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2333-shard-timeline
seq: 1
title: [T-2333] 受入 shard の report.json へ session timeline の観測 field を足した — 判定は 1 つも足さず、足していないことを変異で固定した (コード + テスト、branch worktree-dev-wave-t2333-shard-timeline、変異 matrix = baseline PASSED・KILLED 11・SURVIVED 0・MISMATCH 0・期待 node 完全一致 11/11)
---

## 本文

D1647 の射程どおり、観測 field を 1 key だけ足した。gate・判定は足さず、D1620 の測定面も変えていない。
逐語・変異台帳・受入受領証は `output/insights/2026-09-08_t2333-shard-session-timeline/`。

**段 3 の両レンズが同じ blocker を主張し、親が段 4 で覆した。** 主張は「`_REPORT_FIELDS` へ
`session_timeline` を必須追加するのは D1647 の『受理集合には触れず』違反」である。refuted の根拠は
{{D:session-timeline-report-fields}} に書いた。ただし所見の核は採用し、plan が予定していた
`validate_report_evidence` への形検査を却下した ({{D:no-timeline-shape-validation}})。

**段 3 が実欠陥を 4 件見つけ、すべて採用した。** うち 1 件は観測の目的そのものを潰すもので、
collection 終了時刻の採取位置が実際の collection 終端より早い ({{D:collection-finish-clock-position}})。
残る 3 件は、観測の採取失敗が受入の rc を変えうる点、xdist の crash report が epoch 0 を混入させる点、
`item.config` の直接参照が既存の protocol 契約テストを赤にする点。

**受入台帳の余裕がほぼ無いことを実測した。** 権威 probe で測ると被覆率は 90.012039% で、
90% を割らずに足せる新 node は **2 件**しかなかった (base 時点では 7 件)。追加した 16 node を
すべて登録した。段 3 レンズ A が「親の測り方が権威と違うかもしれない」と指摘したので権威 probe で
測り直し、`consumer_keys` 集合が `--collect-only -q` の素朴な行抽出と集合等価であることを確認した
(指摘は refuted)。

**受入を 1 回捨てた。** 段 6 の中間走行の 1 本目は post-claim merge が
`stage=merge rc=70 source_rc=1` で落ちた。
走行中に main が進み、受入台帳の `nodeid_count` の 1 行が再び衝突したためである。test node を
足す wave 同士はこの 1 行で必ず衝突する ({{F:ledger-nodeid-count-merge-collision}})。

**環境側の詰まりを 2 件外した。** どちらも当 wave 固有ではない。
(a) `output/pegasus-dispatch/` に stale な orphan hold が残り、この repo からの dispatch が
全 session 分止まっていた。対象 job は qstat に不在で `child_rc=0` の完走記録があったので、
記録どおり hold 2 ファイルを外した。解除後 provenance 監査は rc=0 (44 秒)。
(b) 変異走が残した `*.orphan-stop.json` sidecar。hold だけ消しても再走が即中止する。

**背景の待ち手が 4 回誤検知した。** producer 稼働中に「完了」を出し、走行中の変異注入を
「復元忘れ」と誤読しかけた。真因は待ち手 script 側で 2 つ — 背景コマンドと Monitor の command に
書いた改行が空白へ潰れて loop が崩れること、sandbox 内では他プロセスへ signal を送れず
`kill -0` が必ず失敗することである ({{F:background-waiter-false-completion}})。
段 8 でこの根本原因へ訂正した (初稿は wrapper pid の exec 置換という推測を書いていた)。

**エージェント工数。** 段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ A / B)、段 5 実装 1 本、
段 6 レビュー 2 本 (レンズ C / D)、変異 spec 1 本 + 較正 1 本、main 取り込みの合成監査 2 本
(main が 2 回進んだため)。段 6 の両レビューとも must-fix ゼロで fix 子は起動していない。

**段 3 レンズ D が親の変異事前登録の誤りを 1 件見つけた。** M8 の killer は「xdist 集約テスト」では
なく `test_worker_payload_carries_observations_and_defaults_without_state` である。前者は
`_WORKER_PAYLOADS` を直接組み立てるので M8 では緑のままになる。spec 側を実測に合わせた。

## 次の一手差分

### 完了

- [T-2333] 受入 shard の report.json へ session timeline の観測 field を足した。
  gate・判定は足さず、D1620 の測定面も変えていない。変異 11/11 KILLED、受入は child-green。
  remaining: none
  base: 349bc517ae56641a83657006a7aae9cc1aeba2e922a560a7bef3589b3f2c9963

### 新規

- {{T:acceptance-wall-timeline-decomposition}} **P1・新規**: [T-2273] の内訳確定に
  `session_timeline` を実際に使う。受入全走の shard report から、shard-0 の wall より
  collection 区間・worker 占有・real-repo lock 保持を引き、残る 95〜207 秒が受入形固有
  (collection / deselect / LPT / report 生成) か host 差かを判定する。観測点は本 wave で
  入ったので、次は測って読むだけである。
- {{T:ledger-nodeid-count-merge-collision-relief}} **P3・新規**: 受入台帳の
  `nodeid_count` が、test node を足す wave 同士の必然的な衝突点になっている
  ({{F:ledger-nodeid-count-merge-collision}})。派生値なので台帳に持たず consumer が数える、
  あるいは merge driver を与えるなどの案がありうる。**ユーザー裁定が要る** — 台帳の schema と
  既存 consumer に触れるため。
