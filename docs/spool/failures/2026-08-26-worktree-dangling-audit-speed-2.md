---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: worktree-dangling-audit-speed
seq: 2
---

## 新規

### {{F:progress-interval-doubles-as-poll-timeout}}. 進捗の報告間隔と poll 待ち時間を同じ定数にして busy-spin した [恒真ゲート]

- 事象: 到達不能 commit 監査へ進捗出力を足したところ、`orchestrator/tests/test_audit_dangling_commits.py`
  が 4 秒から 10 分超・メモリ 12.5 GB へ膨らみ、単調増加のまま終わらなくなった。計算ノードの job を
  qdel で止めて切り分けた。
- 根本原因: `_git_with_heartbeat()` が `HEARTBEAT_INTERVAL_SECONDS` を
  **「どれくらいの間隔で報告するか」と「1 回の `communicate` で何秒待つか」の両方**に使っていた。
  テストが報告間隔を 0.0 にすると `communicate(timeout=0.0)` が即座に `TimeoutExpired` を投げ続け、
  進捗行をマイクロ秒ごとに出すループになる。テストだけの問題ではなく、間隔を小さく設定した運用でも
  1 コアを焼き続ける。**依頼が求めた進捗出力そのものが持ち込んだ回帰である。**
- 恒久対応: poll 待ち時間を報告間隔から分離し、下限 0.1 秒・上限 1.0 秒を置いた
  (`tools/audit_dangling_commits.py` の `POLL_FLOOR_SECONDS` / `POLL_CEILING_SECONDS`)。
  報告期限は独立した変数で管理し、間隔 0 は「poll のたびに必ず報告する」を意味するようにした。
- 再発検知: 報告間隔 0 でも poll 回数が有界であることを実時間に依存せず固定する control
  (`orchestrator/tests/test_audit_dangling_commits.py`)。下限を外す変異で赤になる。
- 併記: 特定には親が `pip install --user py-spy` でサンプラを入れ、走行中のプロセスへ `py-spy dump` を
  当てた。**それまでに 4 つの仮説を外している** (直積の走査コスト、`git grep`、規模テスト、
  landed blob の memory)。サンプラが無い間、律速は外から一切見えなかった。

### {{F:review-finding-closed-per-instance-leaves-twin}}. レビュー所見を実例単位で閉じて同型の第 2 実例を残した [手順漏れ]

- 事象: 段 6 のレビューが「repo 外候補の重複除去が `x not in <list>` で二次化する」と 1 箇所を
  名指し、そこを直して閉じた。後日の実測で、**同じ形が `_landed_reference_matches()` にも残っていた**。
  pattern 出現 255 万・(key, 外部 file) 対 189,732 の規模で爆発し、監査が 15 分以上終わらなくなった。
- 根本原因: 所見を「指摘された実例」の単位で閉じ、**所見の型に対して同型の全件を洗い出す指示を
  出していなかった。** 名指しされた実例が唯一とは限らない。
- 恒久対応: 修正を投げる子の指示へ「同じ型が他に無いか、AST で全参照を走査して全件列挙せよ。
  置き換えたもの・据え置いたものとその理由を報告せよ」を入れる。本 wave の修正子はこれで
  第 2 実例 (参照結果の重複除去) を自力で見つけて直し、第 3 実例が無いことを membership 21 式の
  全件検査で確認した。
- 再発検知: 二次から線形への置き換えが受理集合を変えないことを固定する control と、
  list 版なら現実的な時間で終わらない規模での完了 control
  (`orchestrator/tests/test_audit_dangling_commits.py`)。

### {{F:fail-closed-branch-not-measured-against-real-distribution}}. fail-closed の判断を実 repo の分布で裏取りせず、監査自体を実行不能にしかけた [測り方の誤り]

- 事象: 修正子が「単親の空 commit が出すバイト列は、切り詰められた出力と byte 上区別できない」と
  正しく観察し、**fail-closed で rc=2 (実行不能) にした。** 判断の形としては正しい。しかし親が実測すると、
  対象 repo の到達不能 commit **2,804 本のうち 2,023 本 (72%) がその形**だった。そのまま land すれば
  掃除の必須ゲートが 1 度も通らなくなる。
- 根本原因: fail-closed の枝を足すとき、**その枝が実データで何 % 発火するかを測っていなかった。**
  形の正しさと運用可能性は別である。
- 恒久対応: 切り詰めの検出を「形の厳格さ」から「完全性検査」へ移した — record 境界は OID の
  先読みで決まるので stream 途中の record は切り詰められず、末尾 record は git の rc=0 と
  「要求した OID がちょうど 1 回ずつ現れる」検査が保証する。この論拠をコード中のコメントに残し、
  書けなければ実装を変えず止めることを修正子の指示に入れた。
- 再発検知: record を 1 本まるごと落とした synthetic 出力 (git rc=0 を装う) が rc=2 になる control と、
  実 git の 4 形 (単親 + path、combined 非空、combined 空、単親の空 commit) を 1 batch へ入れた
  fixture (`orchestrator/tests/test_audit_dangling_commits.py`)。
- 併記: git は diff の種別で header と path 列の区切りを変える (単親は LF、combined は NUL、
  単親の空 commit は区切り無し)。synthetic fixture だけで書いていた間はこの差が見えず、
  1 度は「LF だけを受ける」形にして回帰させた。**実 git を回す fixture を 1 本持つことが要る。**
