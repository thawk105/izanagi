---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-f241-perf-attribution
seq: 1
title: F241 の根本原因は「perf の不在」ではなく「振り分け役を呼んでいた」ことだった — 同じ台帳が既に反証を持っていた (docs のみ、branch worktree-dev-wave-f241-perf-attribution、実装面の差分 0)
---

## 本文

- **依頼と結論。** F241 の「計算ノードに現行 kernel 用 perf が無く、環境側に linux-tools を
  入れてもらう以外に道はない」を実測で裏取りした。観測 (literal `perf` の rc=2) は真だが、
  そこからの帰属が誤っていた。`/usr/bin/perf` は完全一致する版が無ければ他版へ fallback せず
  exit 2 する振り分け役であり、既設の実体は動く。詳細と射程は
  `output/insights/2026-09-04_f241-perf-attribution/`、台帳反映は F241 の supersede と F1 の再発。
- **測定。** gen_S へ 24 job を投入し 23 job が返却 (request 975613 のみ scheduler 出力・probe
  出力とも戻らず、原因不明のため除外。回収率 23/24)。6 distinct bnode、うち bnode092 と
  bnode101 で 17 run を占める。同一 node・同一 run の対比で literal は 23/23 が `stat` rc=2、
  絶対 path 2 本は 46/46 が rc=0 で 4 event すべて実数値。両側 control は全 run で成立。
  ログインノードでは絶対 path の `--version` が rc=0、`stat` は `perf_event_paranoid=4` により
  rc=255 で、**不在ではなく権限**であることを分離して観測した。
  **これは F241 の 8 node と同等の標本強度ではない** (6 distinct node)。過去の実測を合算して
  8 と数えていない。
- **probe は repo へ入れていない。** 実装面を増やさないため job dir (repo 外) に置き、
  逐語は `probe-verbatim.md` へ貼った。実装面の差分は 0 であり、D95 決定 2 により変異 matrix を
  免除した (受入全走は免除していない)。
- **段 3 の敵対レンズが親の provisional 裁定を 2 件覆した。** (1) 親は「誤りは恒久対応の 1 文に
  局在する」としたが、F241 の「perf を外す回避を採ってはならない」も現行の受理集合 (D352、
  `use_perf=false` が eligible) と矛盾しており、3 点の訂正が要る。(2) 親は新しい F を起こす案を
  持っていたが、台帳の運用規則は同型なら新 F を禁じており、F1 の再発が整合する。
- **b10 事前登録文書への追記は行っていない。ユーザー手番として残す。**
  `docs/b10-backoff-shape-preregistration.md` §7 の「(この計算ノードに perf は無い)」は
  本測定により誤りである。しかし `orchestrator/campaign/b10_backoff_shape_sweep.py` の
  `run_formal` は `report` を含む全 phase で `load_preregistration` を通し、作業木の bytes が
  `git show <prereg_commit>:<path>` と完全一致することを要求する。2026-09-04 時点で別 wave
  (`dev-wave-t1905-b10-continuation`) が `prereg 77b33e37d` に束縛された B-10 正式走を実行中で
  (request `974207.nqsv` の `verify-perf balanced`、および 13.7〜17.5 時間の read-heavy 走行が
  予定)、同 wave は段 0 で「事前登録を含む b10 系の編集面に稼働 wave との重複なし」を確定して
  いる。1 byte の追記でも残り phase が `prereg-blob` で停止し、確定済みの非重複をこちらから
  破ることになる。**これは brief 執筆時に未見だった事実**であり、依頼の縮小ではなく適用時点の
  差し戻しである。訂正文の本文と適用の安全条件は下記の新規項に置いた。
- **伝播先の全数走査。** `docs/` と `output/` を否定形の複数の言い回しで走査し、44 箇所を
  分類した。訂正対象は F241 と b10 事前登録の 2 件だけで、`docs/decisions.md` の D348 / D352 と
  `docs/pegasus-runbook.md` の環境事実は**既に正確**なので変更していない。archive worklog、
  過去 wave の insight、逐語は歴史記録として一切書き換えていない (規律 7)。
- **実測した道具の欠陥。** `qstat <request-id>` は request が存在しなくても
  `Batch Request: <id> does not exist on nqsv.` と表示しつつ **rc=0** を返す。rc を生死判定に
  使う待ち手は全件「生存中」になり空転する。本 wave の最初の待ち手が実際に空転しかけた。
  生死は done-marker か qstat の出力本文で判定する。

## 次の一手差分

### 新規

- {{T:b10-prereg-perf-erratum}} **P2・ユーザー手番**: `docs/b10-backoff-shape-preregistration.md`
  の §7 の括弧書き「この計算ノードに perf は無い」への erratum を、文書末尾へ追記して適用する。
  本文と根拠は `output/insights/2026-09-04_f241-perf-attribution/README.md` の「未適用の訂正」節。
  §7 の本文行は書き換えず、`## 10.` として末尾に足す形が規律 7 に適合する
  (段 3 レンズ A が §0 内挿入案を不適合と裁定)。**適用の安全条件**は次のいずれか —
  (a) `dev-wave-t1905-b10-continuation` の B-10 正式走 (balanced + read-heavy + report) が
  すべて完了し `prereg 77b33e37d` を指す残り phase が無くなる、
  (b) 同 wave が残り phase を追記を含まない固定 checkout からだけ実行すると確定する。
  適用時は `parse_preregistration` の canonical machine spec block が 1 個のままであること
  (marker 文字列を書かない) と、`as_dict()` / `spec_sha256` が不変であることを実走で確かめる。
