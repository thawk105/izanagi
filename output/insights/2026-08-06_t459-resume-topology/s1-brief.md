# 段 1 brief — [T-459] crash 後 resume が build_start を二重に追記する欠陥

wave: `dev-wave-t459-resume-topology` / branch `worktree-dev-wave-t459-resume-topology` (base 67175e1a)

## scope

`build_start` 済みで terminal (commit / abort) に達しないまま process が死んだ variant を、
次 run が**同一 variant の二つ目の `build_start`** で再評価する経路を閉じる。閉じ方は
「未終端 attempt を終端させてから再評価する」形に限る。attempt topology 検査そのものを
緩める変更は scope 外 (規律 2)。

## 段 1 実測 (親、login node、いずれも本走でない)

- M1: 実 WAL API で `build_start`(attempt A) だけを書いた campaign は `replay` 成功・
  `resumable=True`・`terminal_variants=∅`。続けて同 variant へ attempt B の `build_start` を
  書くと `replay` が `AttemptTopologyError: build_start: variant に未終端 attempt がある:
  active=A next=B`。→ 起票内容は real (probe: job tmp、成果物なし)。
- M2: `loop.run_campaign` は `terminal_variants` で skip を決めるため、未終端 variant は
  再評価対象になる (`loop.py:171-186`)。`pipeline.evaluate` は `build_start` を無条件に
  emit する (`pipeline.py:709`)。`model.EvalState.resumable` の docstring は
  「リカバリで破棄して再評価すべき」と宣言しており、topology 検査と正面から矛盾する。
- M3: 波及先は campaign 全体。`artifact_admission` は records へ
  `wal._validate_attempt_topology` を直呼びし、例外を `ArtifactAdmissionError` に翻訳する
  (`artifact_admission.py:645-661`)。1 variant の二重 start でその campaign の artifact 全部が
  admission から落ちる。
- M4: `output/` 配下の WAL 30 本に未終端 attempt は 0 件、`build_attempt_id` を持つ record も
  0 件 (全部 pre-policy 形式)。既存 artifact は未被害で、修正は既存 bytes を変えない。
- M5: WAL bytes の pin は `artifact_admission` の overlay ledger record (`wal_sha256`)、
  `qualification` の protocol source pin (`artifacts.py:804`, `identity.py:182`,
  `contract.py:152`)、`tools/plotting/plot_backoff.py` の receipt。path key でなく
  `wal_sha256` field key で張られているため、path 検索だけでは見つからない (DW-O09/F30)。
- M6: 発火 gate (DW-G04): `loop.run_campaign` は `ident.bind_admission_policy` を無条件に
  通すので、**今後生成される campaign はすべて post-policy = topology 検査対象**。
  発火条件は「post-policy campaign が build_start 後・terminal 前に落ちる」で、
  既存 artifact path ではなく M1 の再現で示す。

## 不変条件 (破ったら赤)

1. topology 検査を弱めない。未終端 attempt を無視・除外・後付け許容する方向の変更は不可。
   終端 record を追記して topology を満たす形だけを許す。
2. 既存 campaign WAL の bytes を変えない (M4/M5)。read 経路が WAL を書くようにしない。
   とくに `artifact_admission` は read-only を保つ。
3. crash した variant を沈黙のうちに永久 skip にしない (D25/B-3)。成果物から候補が
   静かに落ちる形は不可。
4. 追記する終端 record は attempt の `build_admission_receipt_sha256` 規則を満たす
   (receipt 有りの attempt には同じ SHA、無しには載せない)。
5. AI provenance / land 境界 / push 禁止は従来どおり。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 終端形は **recovery-abort** を採る。同一 attempt ID を再開する状態機械 (起票時の
  もう一方の案) は、admission receipt の再導出と build 途中状態の再現が要るため不採用。
- **(P2)** 書き込み seam は `ident.ensure_resumable_wal` (identity 照合済みの run だけが
  物理修復する既存 seam) とし、`wal.replay` は read-only のまま残す。trigger orphan の
  先例 (`wal.replay` 内で recovery abort を書く) は拡張しない。
- **(P3)** recovery-abort の reason は `RETRYABLE_ABORT_REASONS` に入れ、同 run 内で
  再評価させる。入れないと不変条件 3 を破る。
- **(P4)** `ensure_resumable_wal` を通らない resume 経路 (`s6_sort_sweep`,
  `s8a_trigger_sweep`, `p3_s4_loop*`, `p3_s4_loop_trigger_gating` は
  `ensure_campaign_identity` だけを呼ぶ) も同 wave の scope に含め、resume 前に必ず通る
  1 点へ寄せる。分割が妥当なら段 4 で切る。

## 成果物影響 (DW-G05)

放置すると、crash を挟んだ post-policy campaign の WAL は次 replay と artifact admission で
**campaign 単位で拒否**される。その campaign 由来の certified 選択・layer3 report・
台帳参照は、実行時に committed と報告された後から失効する (M3)。

## 成果物の形

`orchestrator/campaign/` の resume 経路への差分 + real WAL writer を使う crash-after-start
境界テスト (fake evaluate では隠れる、起票の指摘)。docs は worklog / decisions fragment。

## 並列分割

段 2 は 1 本 (plan)。段 3 は 2 レンズ並列。段 5 は単一所有 (wal/ident/loop は結合が強く分割で
競合する) で 1 本。段 6 は敵対レビュー 2 本 + fix。

## 受入・実測環境

pytest は計算ノード (`tools/run_tests.py` の dispatch)。login node では今回のような軽量 probe
のみ。実測値は測った checkout を併記する。
