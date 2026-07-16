# 層3 機序仮説層 (mechanism_hypotheses) の原料配線設計 (2026-07-16)

**契機:** phase3.md「層3 renderer の対象拡大」の後半課題。層3 材料レポート v2 (sweep 対応)
までは事実層 (WAL/whiteboard の決定論射影) だが、予約区画 `mechanism_hypotheses` は原料が
永続化されていないため常に空である。本書は原料の配線 (どこで何を書き、renderer が何を
射影するか) の**設計のみ**を凍結する。実装は v3 (schema_version bump) で行い、本設計の
発効自体は現行成果物に不作用。

**分類: 設計。計測ゼロ・既存凍結に不作用。**

## 1. 現状の欠落 (事実)

- critic の機序帰属 (どの設計選択に性能差を帰属させたか) は**非永続**。whiteboard へは
  意図的に機序を落とした射影だけが残る (段 4 リーク制御、D39/D45。`p3_s4_loop.py` の
  `project_whiteboard` が正本)。
- coder/planner の構造化出力は proposal file (`load_proposal_file`) 経由で iteration ごとに
  消費され、campaign 成果物として残らない (診断ログはあるが構造化契約がない)。
- したがって renderer がいくら賢くなっても、機序仮説を「既存の構造化記録の完全射影」
  として出す原料が存在しない。

## 2. 配線設計 (v3 で実装)

1. **新しい永続面:** campaign dir に `runs/agent_outputs.jsonl` (append-only)。envelope は
   WAL と同形の 5 キー `{ts, stage, variant, env_tag, payload}`。stage は
   `planner_proposed` / `coder_proposed` / `critic_attributed` の 3 種のみ。payload は各役の
   構造化出力**全文** + 入力射影の canonical sha256 (`input_sha256`)。書き手は loop harness
   (`p3_s4_loop*.py` 系) だけで、guard_write の防護ツリーに追加して直接編集を拒否する。
2. **リーク制御との関係 (規律 2/6):** whiteboard への「機序を落とす」射影規律は planner/
   coder への**入力側**防壁であり、不変。`agent_outputs.jsonl` は**報告層 (人間向け)** の
   記録で、planner/coder の入力射影経路 (`whiteboard_for_planner` 等) からは構造的に分離
   する — 入力 builder はこのファイルを読む API を持たない。D47 の provenance 三点セット
   (raw 出力 / 射影版 / 対応表) と同方向の拡張。
3. **renderer v3 の射影:** `mechanism_hypotheses` = `critic_attributed` event の決定論射影
   (variant、帰属テキスト、diagnostic 数値、`source_ref`)。source-ref は `ao:` prefix を
   新設し、wal/wb と同じ内容ハッシュ双射検査の対象に加える。`agent_outputs.jsonl` が無い
   campaign (sweep、既存 loop) は空のまま + provenance フィールドで明示 (v2 の
   whiteboard_provenance と同型)。部分ファイル・未知 stage は fails-closed。
4. **発効条件:** 実装は次に agent 出力が生まれる loop 再走 (8b selector 実験の E 段相当) と
   同時。それまで v2 の `mechanism_hypotheses: []` (maxItems 0) を維持する。

## 3. 対象拡大の実測結果 (2026-07-16、v2)

- p3-s8a-trigger-sweep 系 6 campaign へ実レポート生成済み (双射 pass、abort 2 件射影、
  read-heavy の within-run floor は記録が無いため honest に no-matching-env-record)。
- backoff/s6-sort sweep 系 8 campaign は render 可能を確認 (生成は必要時)。例外 1 件:
  `backoff-sweep-silo-read-heavy-sweep-6f169f90` は bench-first screening (D58) の
  `screening` payload を bench_done に持ち、runs の閉じた schema に不適合 —
  screening campaign を層3 対象にする場合は schema 拡張を別途凍結する (本設計では扱わない)。
