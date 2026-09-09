---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2503-pbs-binding
seq: 1
title: [T-2503] t316 probe の runtime PBS 束縛を .pbs へ戻し、誤対象を殺す負例を実走で置いた (コード + テスト + insight、branch worktree-dev-wave-t2503-pbs-binding、変異 4/5 KILLED + 事前登録した等価変異 1 件が期待どおり SURVIVED・期待 node 完全一致)
---

## 本文

- 欠陥は段 6 の敵対レビューが指摘し親が git 履歴で裏取りした既報 ([T-2503] の起票内容) のとおりで、
  本 wave は起票時の記述を一次資料で追認したうえで直した。詳細と限界は
  `output/insights/2026-09-09_t2503-pbs-binding/README.md`。
- **保証範囲を狭める裁定をした。** 段 3 レンズ A の real 所見を採り、この束縛が証明するのは
  「Python preflight 時点で runtime spool と worktree の `.pbs` の bytes が一致すること」までとし、
  実行された命令列の同一性は主張しないと決めた。起票時の「次に走らせると必ず落ちる」も
  「先行関門をすべて通過した実行では決定的に拒否される」へ条件化した。
- **正例単独では比較行を固定しない**という所見も real として採った。比較の存在は負例が、
  比較対象の正しさは正例が固定する。この分担は机上の主張ではなく変異走行で分離を実測した
  (m03 は負例だけ、m02 は正例だけが殺す)。
- 段 3 / 段 6 の 4 レンズが出した所見のうち、refuted は「恒真ゲートである」「負例が変異を
  逃す」「規律 2 を緩めている」「凍結 bytes pin がある」「hooks・runbook・perf inventory が
  赤になる」「受入台帳が未知 node を拒否する」など。fix を要する real 所見は段 6 では 0 件で、
  段 3 の real 所見 (git 環境隔離の順序、git subprocess の timeout 欠落、`delenv` の
  `raising=False` と identity/template/cwd の明示、変異の node 分離) は段 4 で裁定して
  段 5 の実装指示に織り込んだため、fix 子は起動していない。
- **scope 外の real 所見をユーザー裁定へ返す** ({{T:t316-condition-gate-bound-path-drift}})。
  実装はしていない。
- セッション異常: 段 5 実装子を `--reasoning xhigh` 付きで投入して rc=2 で即死した
  (author / review / fix / focus 段では caller が effort を指定できない)。argv を直して
  別 job として再投入した。変異走行は 4 回やり直した (原因と対処は F273 / F932 の再発追記に記録)。
- エージェント工数: codex 子 6 本 (plan 1 / consult 2 / author 1 / review 2)、model call 合計 104。
  fix 子と focus 子は起動していない。

## 次の一手差分

### 完了

- [T-2503] 束縛対象を名前付き定数へ直し、誤対象を指す変異を殺す正例・負例を同じ単位に置いた。
  変異は事前登録どおり 4/5 KILLED + 等価変異 1 件 SURVIVED、期待 node 完全一致。
  remaining: none
  base: 7cabc578f3214972c6e474ed8970902f05563ef048be55ccaa86aab071085e37

### 新規

- {{T:t316-condition-gate-bound-path-drift}} **P2・新規・ユーザー裁定待ち**:
  `tools/pegasus/probes/t316_sandbox_backend_probe.pbs:54-59` の `BOUND_PATHS` は 4 件で
  `orchestrator/campaign/condition_meaning_gate.py` を含まないが、
  `t316_sandbox_backend_probe.py:36` は module import 時にその file を import し、
  Python 側の dirty 検査はその後に走る。dirty な condition gate は、どちらの束縛関門よりも
  前に import-time のコードを実行しうる。取りうる形は (a) shell の `BOUND_PATHS` へ 5 件目を
  足す、(b) Python の import を dirty 検査の後へ遅らせる、(c) 既知限界として記録する。
  成果物影響 = 放置すると、t316 の receipt が「束縛された 5 path で走った」と記録していても、
  そのうち 1 path については実行より後に検査したことになる。
  [T-2503] の段 3 レンズ A が出し、段 6 の 2 レンズが追認した scope 外の real 所見。
