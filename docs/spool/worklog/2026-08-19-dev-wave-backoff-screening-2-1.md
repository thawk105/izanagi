---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-backoff-screening-2
seq: 1
title: backoff_sweep.py --screening の初回ablation (D58) を試みたがPegasusのg++-13欠如で実行不能と判明し、cygnus到達手段待ちとして記録した (docsのみ、branch worktree-dev-wave-backoff-screening-2)
---

## 本文

- 背景: `docs/phase3.md` 現行チェックポイント (38-41 行) が指示する「ablation は初回採用 campaign で
  設計 insight §5-7 の 4 基準により実施する」を、`backoff_sweep.py`(D58 bench-first screening v2 の
  初回適用対象、screening 無しの3 workload 分は既に実行済み) で試みた。
- write-heavy/balanced/read-heavy の3 workload について `backoff_sweep.py --screening <workload>` を
  Pegasus 計算ノード (gen_S queue、単独性確認・投入前チェックリスト実施済み、割当ノード
  bnode009/bnode021/bnode029) へ並列 qsub dispatch した (request 924646/924647/924648.nqsv)。
  投入有効性検査 (出力dir永続化・qstat可視性・会計痕跡) は全て確認できたが、3件とも起動 6 秒で
  `source_digest.resolve()` の fails-closed (D23) — `g++-13` が PATH に無い — で停止した
  (traceback は `source_digest.py:389 _dump_macros`)。
- Pegasus に `g++-13` が login (`pegasus02`) / compute (bnode009/021/029 実測) とも不在と確認した。
  `apt list --installed` では `gcc-13-base` (ランタイムlib) のみ導入済みで、コンパイラ本体
  (`gcc-13`/`g++-13`) は未導入。導入には root 権限が要る。これは F221 の再発 (段2プランでなく
  親の brief 前提測で直接踏んだ) として記録した。
- D293 (2026-08-11、床値 campaign の compiler site 依存化は toolchain 束縛検査が同時に入る場合に
  だけ land 可、という決定) の理由「compiler 差は backoff 級の差を容易に上回る」が、backoff 効果を
  直接測る本 campaign にもそのまま当てはまる。system compiler (gcc 11.4.0 実在確認済み) への
  shim による route-around は、既存 screening 無し結果 (env_tag=linux-baremetal、g++-13 相当で
  測定済みと推定) との比較可能性を compiler 差で汚染するため採用しなかった (規律1/4 の精神に
  従い、測定条件を計測機の外で変えない)。
- cygnus (linux-baremetal) への到達手段は、このセッション (Pegasus login node `pegasus02` 起点の
  背景 job) には無い (`~/.ssh/config` に cygnus 未登録、独立agentでの疎通確認は行っていないが
  ネットワーク境界上妥当と判断)。
- 結果: ablation は未実施のまま。既存 screening 無し3 campaign
  (`backoff-sweep-silo-{write-heavy-sweep-493813a7,balanced-sweep-484c663e,read-heavy-sweep-610004b9}`)
  のデータは無傷 (`screening_driver.prepare_screening_campaign` が screening policy を
  `search_config` へ merge してから `campaign_id` を算出するため on/off は別 campaign 空間になる
  設計だが、起動直後に落ちたため実際の書き込み発生自体が無かった)。
- 副次的に判明した事実: worktree 隔離セッションの Bash が harness 側の既知バグで全滅する事象
  (`worktree-bash-total-lockout-reported` memory と同一症状) にこの wave でも遭遇し、
  `ExitWorktree(keep)` → 別名で `EnterWorktree` の再作成で復旧した (作業ツリーへの
  commit は無かったため損失なし)。

## 次の一手差分

### 新規

- {{T:backoff-screening-ablation}} **P2・新規**: D58 bench-first screening v2 の初回 ablation
  (insight §5-7 の4基準: 誤棄却ゼロ・結論不変・機械時間削減率・on/off fitness の floor 内一致) を
  実施する。前提条件のどちらかが満たされ次第、再開できる:
  (a) cygnus (linux-baremetal) への到達手段を持つセッションから実行する、または
  (b) `backoff_sweep.py`/`p2_2.py` へ D293 と同型の site 依存 compiler 解決 +
  toolchain 束縛検査 (measurement env と compiler を契約に紐付ける) を実装する別 wave を先に land する
  (`source_digest` の identity 計算に関わるため D23 領域の設計レビューを要し、実行のみでは対応不可)。
  実行済みの screening 無し3 campaign データ (上記3件) は既存のまま比較対象として使える。
