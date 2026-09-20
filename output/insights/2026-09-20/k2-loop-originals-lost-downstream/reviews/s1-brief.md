# 段 1 brief — K2 loop 原本消失の下流影響 (docs-only、2026-09-20 21:03 JST)

wave `dev-wave-k2-loop-originals-lost-downstream`、起点 local main `7baf3f375` (fresh worktree、開始 gate rc=0 20:52 JST)。
起票 = 記録 wave `dev-wave-cleanup-backup-loss-record` (branch tip `f43322f8a`、**未 land**) の worklog fragment の新規 T
「K2 loop 原本消失の下流影響」。採番済み ID は無い (main の worklog 末尾 entry 1754 に不在、spool は空)。

## 研究前進

論文ストーリー §8 B-6 / B-9 と fig12 が依拠する K2 手動 loop 3 巡の provenance を、原本消失後に「どこまで主張できるか」で
確定し、4 巡目 ([T-2795] 修復後、D2172 項 3 (iv)) の入力元 (round 3 派生物からの再構成 / 別走) の択をユーザー裁定へ返す。
完了判定 = 対応表と裁定パッケージが insight に着地し、worklog fragment が [T-2795] へ導線を持つ。

## scope

- 対象主張: story 2026-09-20 版 §8 B-6・B-9、fig12、[T-2808] fig12b、層 3 材料レポート (round 2 / 3 `layer3_report.json`)、
  [T-2795] 4 巡目 (round 3 からの再開)。
- 成果物: (1) 主張ごとの対応表「主張 / 要る一次資料 / 残存資料 / 現在確認できる範囲 / 要る限定」、(2) 次巡 checkpoint の択の裁定パッケージ。
- 編集面 (実アンカー): 新規 `output/insights/2026-09-20/k2-loop-originals-lost-downstream/` (README + reviews + materials)、
  `docs/phase3.md` 項 4 の [T-2795] 項の直後に 1 行、`docs/spool/worklog/2026-09-20-dev-wave-k2-loop-originals-lost-downstream-1.md`。
- 触らないもの: 稿 (`docs/paper-story/2026-09-20.md`、`results/2026-09-20-k2-manual-loop-three-rounds.md`)、fig12 の bytes、
  4 insight の erratum 節 (記録 wave の所有)、**`docs/paper-story/README.md` (story 20260920b wave が同節を編集中、mtime 20:57 JST)**
  — stale 注記に積む 1 段落は本 insight §5 に README 用の文面として置き、peer へ事実を送る。
- scope 外: 過去結果の一括無効化、再走の結論、稿の書換え (規律 7)、仮想リスク向けの gate・検査・台帳・一般化。規律 2 は不変。

## 確定済みユーザー裁定・既裁定

- D2172 項 3: (i) 同 job pair、(iv) 4 巡目 = 新規生成 1 回 + 同 job stock 対照 1 本 (1 job)。D2187: pair 修復方向 (実装は別 wave)、
  再投入・4 巡目の予算再提示はユーザー。ユーザー「記録していいよ」(19:3x JST) は記録 wave の起動で、本 wave の裁定ではない。
- 規律 7: 記録された測定は現行コードとの差だけでは無効にならない。原本消失は「再検算できる強さ」を変えるが、当時の判定を変えない。

## 不変条件

- 3 巡の値・判定・結論 (certified / anomaly 0 / continue、815,983 tps 等) は変えない。稿・図の bytes は不変。
- 「消失」「再構成可能」「内容同一」「bytes 同一」を区別して書く。再構成物は原本ではなく「派生物から作った、記録 sha256 と一致する複製」と呼ぶ。
- 不在の断定は走査した path と時刻を書いて限定する。

## 段 1 で実測した前提 (brief 前)

- 記録 wave の一次資料・fragment・4 insight の erratum 差分を読了。ListAgents (20:55 JST): 稼働 17 session に [T-2795] wave は無い (entry 1754 で着地済み)。
- t2746 job dir `scratch-campaign/` の 6 file を sha256 実測: WAL・loop_state・digest・受領証・**campaign.lock** (`fc7acaca…`) が 3 巡稿 §5.1 と一致、AO のみ別走。
  → 記録 wave の「campaign.lock は照合不能」「roundtrip は sha256 の記録も無し」は、**3 巡稿 §5.1 (消失前の同日に再計算) が全 3 巡の原本 sha256 と bytes を持つ**ので埋まる (P1)。
- round 3 `loop_state.json` (`917ba3d3…`) は `materials/run-summary.json` の `loop_state` から harness の writer 形式で **byte 一致**再構成できる (round 2 scratch で手順検算)。
- round 2 / 3 の本走 AO (`804c62c7…` / `66d3e737…`) は repo の `layer3_report.json` の `agent_outputs` から **byte 一致**再構成できる。
- round 2 / 3 の WAL は `layer3_report.json` の `variants[].events` から**内容同一** (canonical ref 5/5 が `materials/wal-refs.json` と一致) だが、
  payload の key 順 (挿入順) が失われており **bytes は再構成できない**。digest は repo に逐語無し (再描画は固定 checkout + WAL 内容で原理上可能、未実測)。
- T-2795 pair 走の原本 5 file は `submit-tree-pair` に無傷 (sha 5/5 一致) だが、その worktree は **unlocked + 未追跡 `output/exploration/`** で、撤去された候補 1 と同型 (P2)。
- 4 巡目は harness の `load_loop_state` で round 3 の tree を再開する設計ではない: round 3 自身が「round 2 の tree は `start_wall` 超過で入口停止するので fresh tree + 新 WAL」と記録し、
  前巡の状態は親の射影 (whiteboard・current_perf・critic 逐語・knowledge-input) で運んだ (P3)。

## provisional 裁定・攻撃対象

- (P1) 3 巡稿 §5.1 を「原本の sha256 の記録」として採る (記録 wave の README は insight の記載範囲について言っており矛盾しない)。
- (P2) `submit-tree-pair` の lock は本 wave では打たない (隔離 session の guard が他 worktree への git 操作を拒否)。裁定パッケージの 1 項として、
  次に触る非隔離 session (T-2795 修復 wave または cleanup) が `git worktree lock` を打つ。gate・台帳は足さない。
- (P3) 「round 3 の `loop_state.json` からの再開」= 親の射影の入力元の問題であり、必要な入力は全部 repo 内派生物にある。推奨は「別走 (fresh tree) + 射影は repo 派生物 (再構成物を含む) から」で、
  再構成した `loop_state.json` を harness に load させる形は採らない (start_wall 超過で入口停止する上、再構成物を原本の位置に置く必要が無い)。

## 分割方針

軽量版 (DW-C00): 段 2・3 省略。実装面ゼロ (親が docs を書く、probe script は job dir に置き repo へ入れない)。段 6 は一次資料から事実を
再抽出する docs-only なので read-only codex レビュー 1 本 (2 レンズ = 対応表の不在断定・sha 照合の攻撃 + 裁定パッケージの推奨への攻撃)。
変異 matrix は実装面ゼロで免除。受入は `dev_wave_wait.py acceptance` (docs のみの差分)。
