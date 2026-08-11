# 段 1 brief — [T-817] verifier-policy epoch を campaign identity へ入れ、witness なし COMMIT を再評価する

wave slug: `t817-verifier-epoch` / branch: `worktree-dev-wave-t817-verifier-epoch` / base: main `11978dcb`

## scope

- **S1** verifier-policy epoch を campaign identity へ入れる。
- **S2** 既存 WAL の witness なし COMMIT を再評価する機構 — 同一 run の保存済み stdout witness と
  突き合わせ、突き合わせ不能なものを「検証不能」として**現行 certified 選択から除外**する。
- **scope 外**: 凍結成果物の再生成、CCBench の改変、P2-2 の再計測、trace 形式の変更 ([T-816] の面)。

## 確定済みユーザー裁定 (2026-08-11 /rulings 第 13 回、worklog 430)

(a) 条件付き。ログが残る記録は再実行なしで突き合わせ、**ログが無く再評価不能な記録だけ**を検証不能
として現行 certified 選択から除外。一括除外 (b)・現状維持 (c) は不採用。
**実装 wave はまずログ残存率を実測してから設計する。** 受理集合と campaign identity に触れるため
変異つき専用 wave。

## 段 1 実測 (一次資料 = 実 WAL 30 本 + output 全走査。probe は repo 外)

- **M1** WAL 30 本: `verify_done` 572 件 (`certified=true` 571 / `false` 1)、`commit` 459 件。
  **`commit_witness` を持つ記録は 0 件。**
- **M2** `output/` 10,291 ファイル走査で実 stdout (`commit_counts_:<数字>`) は 193 件。
  **全件が `output/env/pegasus/` 配下の別 producer** (t141 較正 / silo_ladder_rung1 raw bundle /
  t139 probe / t155)。**campaign pipeline の run に対応する残存は 0 件。**
- **M3** 機序: `pipeline._run_trace` (`orchestrator/campaign/pipeline.py:349-362`) は
  `capture_output=True` の stdout をその場で parse するだけで保存せず、trace_dir は
  `tempfile.mkdtemp` の使い捨て (`pipeline.py:928`)。**保存経路が存在しない** (消えたのではない)。
- **M4** 消費側: `replay.load_landscape` (`orchestrator/campaign/replay.py:119-150`) が
  `verify_done.certified` と `bench_done.median_tps` を配り、`assert_complete`
  (`replay.py:153-166`) が「8 genome 全 certified」を要求する。`guided.py:136` は replay の
  certified をそのまま誘導 WAL へ書く。
- **M5** 凍結側: `output/s1-freeze/known_axes_freeze.json` は
  `orchestrator/tests/test_frozen_artifacts.py:39` が bytes を pin。producer
  `s1_known_axes_freeze._p2_entry` (`:337-345`) は P2-2 WAL を読むが、artifact は凍結済みで
  **再生成しない** (DW-O09/O10: 本 wave は producer を走らせない → 出力 bytes 不変)。
- **M6** 旧記録の epoch は 1 つでない: 572 件のうち `aborts` を持つのは 518 件、`workload` は 512 件。
  witness 以前にも段差がある。
- **M7** identity 側の既存作法: `ident.screening_search_config` (`ident.py:100-125`) は
  「None ならキー自体を返さず歴史的 campaign-id を完全に温存する」。`canonical_preimage`
  (`ident.py:149-180`) は `search_config` を丸ごと覆う。

- **M8** 歴史 campaign の lock は v1 の素の pre-image で、`search_config` に `build_admission` も
  `verify` も持たない (実測: `output/campaigns/p2-2-silo-balanced-enumerate-f1588056/campaign.lock`
  = `{"ccbench_commit":"6656e93","search_config":{records,scale,space,threads,workload,ycsb},...}`)。
  一方 `ident.canonical_preimage` は `build_admission` 不在を **ValueError** で拒否する
  (`ident.py:158-162`)。**歴史 campaign は既に id 再計算では引けず**、`replay.discover_campaign_dir`
  の dir 名 prefix discover だけが到達経路である (`replay.py:93-113`、C1 として明文化済み)。
- **M9** `orchestrator/campaign/ident.py` は enforcement source closure の 8 path の 1 つ
  (`campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS`、`campaign_lock.py:29-38`)。disk bytes と
  記録 commit blob を照合するため、**未 commit の編集はテストを大量に赤くし、変異の帰属も壊す**
  ([T-756] wave が `pipeline.py` で実測、worklog (428))。段 5→6 の順序設計に直結する。
- **M11** 旧記録は既に epoch を自己申告している (実測): `commit.payload.verify_configs` は
  `["legacy"]` 289 / `["legacy","s2"]` 111 / **不在 59**。`verify_done` の key 集合はちょうど 3 種
  (`aborts`+`workload` あり 512 / どちらも無し 54 / `aborts` のみ 6)。
  **P2-2 の 24 件 (= replay/guided の landscape 全体) は最古の階層** — `verify_configs` 不在かつ
  `aborts`・`workload` 無しかつ `commit_witness` 無し。つまり P2-5 の選択材料は
  abort 集計 gate も witness gate も通っていない世代の記録に載っている。
- **M10** verifier 構成は既に identity 内にいる — `SEARCH_CONFIG_VERIFY_KEY = "verify"`
  (`pipeline.py:117`)、値 `"legacy+s2"`。epoch を新 key にするか `verify` の意味論拡張にするかは
  設計択一である。

## 承認済み裁定の前提を覆す新事実 (段 4 で再裁定する)

- **N1** 裁定が (a) を (b) より優先した理由は「検証すれば通る記録まで捨てない」。M2/M3 より
  **その集合は空**。(a) を条件どおり適用すると結果は 571 件全除外 = (b) と同一の帰結になる。
- **N2** 素直に除外すると `assert_complete` が発火し、P2-5 の replay/guided アームが動かなくなる。
  凍結成果物は bytes 凍結済みゆえ不変 (M5)。

## 不変条件

- 規律 2: 「witness 無し = 検証不能」を「certified」へ丸めない。除外を黙って緑にしない。
- 規律 3: 除外は pass/fail でなく**構造化理由**を返す (どの epoch のどの欠落か)。
- 凍結成果物の bytes を 1 bit も変えない (M5 の pin)。WAL も 1 bit も書き換えない。
- CCBench 無改変。既存テストの期待値を反転・緩和・削除・skip しない。

## 親の provisional 裁定 (P1〜P4 は攻撃対象)

- **(P1)** 「現行 certified 選択」= 生きた選択経路 (replay/guided の landscape と今後の certified
  選択) に限る。bytes 凍結済みの歴史成果物は epoch E0 の歴史記録として不変 ([T-816] と同じ扱い)。
  根拠 = ユーザー指示が replay.py / guided.py を名指しした。
- **(P2)** epoch は `search_config` の新 key として入れ、`screening_search_config` と同じ
  「不在 = 歴史保存」意味論にする (既存 campaign-id を割らない)。
- **(P3)** 旧記録の epoch は記録の形から導出する (`commit_witness` 不在 ⇒ pre-witness epoch)。
- **(P4)** 突き合わせ機構は「残存 witness が 0 件」を**恒真な検査にしない** — 残っていれば必ず
  拾い、同一 run 由来でない witness を権威にしない (t756 段 6 blocker 3 と同型の罠)。

## 成果物影響 (DW-G05)

- S1 未実装 → 新旧 policy の記録が同じ campaign identity に同居し、certified の受理集合が
  verifier policy の変更に対して不変に見える (proof chain が policy 世代を証明しない)。
- S2 未実装 → 現行の選択材料に witness 不在の旧 certified が残り、FN-1 偽陰性経路が
  certified の土台に残る (規律 2 の趣旨)。

## 成果物の形

コード = epoch 定義の正本 + `ident.py` の identity key + 消費側 (replay/guided) の epoch 対応 +
除外の構造化診断。テスト = 新設 gate の正例・負例、歴史 campaign-id 不変の metamorphic、
除外理由の構造。変異事前登録は段 4。

## 並列分割方針

- 単位 A = identity/epoch (`ident.py` + epoch module + 該当テスト)
- 単位 B = 消費側 (`replay.py` / `guided.py` + 該当テスト)
- B は A の epoch API に依存 → A 先行、所有パス限定 patch を展開してから B を投入。

## 受入・実測環境

性能計測を伴わない (計測なし)。テスト実走は計算ノード dispatch。並走 [T-804] (spec_sha256 伝播) と
identity 面が近いので main を都度マージし、識別子設計が衝突したら止めて報告する。
