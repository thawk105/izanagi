# 段 1 brief — [T-244] P3 生死実験 (dev-wave-t244-p3-liveness)

対象 = `output/insights/2026-08-05_t244-p3-design/README.md` §8 の `DW-G01` 生死実験。
確定裁定 = worklog (236) / D179 §9 の U-1〜U-6・U-8・U-9。**U-7・U-10 は未決のまま。**

## 段 1 前の前提実測 (すべて本 wave で実測。裁定時点の想定と食い違う点を含む)

- **N1** production authority `orchestrator/campaign/reflux_origin_authority_v2.json` は
  `{"authority_schema":...,"origins":[]}` の 71 bytes。entry 追加には 13 field manifest が要り、
  `budget_policy` (= U-10) と evidence ref 2 本 (= U-7) を含む。**両方とも未決。**
- **N2** ledger は evidence path を dereference せず (`EvidenceDigest` docstring)、budget 値の
  意味も検査しない (`_authority_from_bytes` は構造・正準性・導出 hash のみ)。よって適当な値でも
  **機械的には通る**。U-7/U-10 は機械 blocker ではなく**統治 blocker**である。
- **N3** 公開 API (`commit_event` / `read_origin` / `read_sealed_batch`) は `_production_store()`
  固定で scratch seam を持たない。非 production の唯一の seam は private `_fixture_store_for_test`
  (完全な一時 git repo が要る)。
- **N4** commit→prepare→seal は `test_reflux_origin_ledger.py` が synthetic bytes で既に被覆済み。
  よって本実験の**純増検出力**は「**実 E driver が出した wire bytes と実 outcome/evidence を
  現行 batch API が受理し、同一候補 R=2 の replicate counter を更新し、seal で復元できるか**」だけ。
- **N5** `python3 -m campaign.p3_s4_loop_trigger_gating --preview-wire 11111` は login で rc=0。
  実 `working_diff` と `diff_digest=7919a7d2...` を返す (実測済み)。
- **N6** 同 CLI の fixture-main / `--run-iteration` は login で
  `ExecutionGuardError: 計測用 env bytes は site='PEGASUS_LOGIN' では生成できない`。
  `--no-build` でも同じ。**計算ノードが要る** (実測済み)。§8 が「E は実走可能」と書いた前提の限定。

## scope (成果物影響つき、`DW-G05`)

- **S1 使い捨て liveness probe 1 本** (≤100 行、`output/insights/2026-08-05_t244-p3-liveness/` に置く。
  先例 = `2026-08-03_t361-t362-cluster-probes/driver/`)。実 wire を入力に、一時 git repo の
  fixture store へ `BatchCommitted → BatchResultsPrepared → BatchSealed` を R=2 で通し、
  receipt 1 個を保存する。
  → 実装しない場合: P3 の (3) 結線が「ledger 単体テストは緑だが実 driver 出力で動くか不明」のまま残り、
  D96 分割 wave の起票根拠 (受理・counter・seal が生きている) が空のままになる。
- **S2 実測 receipt 1 個 + 判定表**を insight へ凍結する。
  → 実装しない場合: 次 wave が同じ生死確認をやり直す。
- **S3 記録** (worklog / decisions fragment、insight)。U-7/U-10 未決が段取りに与えた制約を明記する。
  → 実装しない場合: U-10 が「値を決めれば済む」と誤読され、production provisioning が
  未裁定のまま解禁されうる (N2 が機械的に通してしまうため)。

## 本 wave で**やらないこと** (U-9 (a)、D96)

reservation FSM (U-5)・report v3・origin-proofs sidecar・completeness・
`member_row_count`/`distinct_candidate_count` の field 分離 (U-4)・critic 後置 (U-8)・
ever-issued cell 台帳 (U-3) の**本体実装は一切しない**。すべて D96 の分割 wave の対象。

## 不変条件

- **I1** `orchestrator/campaign/reflux_origin_authority_v2.json` を変更しない。`origins` は `[]` のまま。
  N2 により適当な値でも通るが、U-7/U-10 未決の値を commit することは production provisioning に
  あたるため禁止する。
- **I2** 名乗りの上限は D179 §7。本 wave が名乗ってよいのは「実 driver 出力に対する
  ledger 受理・replicate counter 更新・seal 復元の**生死のみ**」。P3 充足・部分 P3/P4・
  provisioning 解禁・kill-before-commit 対策・科学的有効性・「候補 batch を作った」は名乗らない。
- **I3** U-4 に従い、single-candidate × R=2 の記録には `distinct_candidate_count=1` を probe 出力と
  記録の両方へ明示し、「候補 batch」と呼ばない。
- **I4** 既存 tracked file を編集しない (probe は新規ファイルのみ)。ledger 本体は読むだけ。
- **I5** probe が private seam `_fixture_store_for_test` を使うことを probe 冒頭に明記し、
  「production 経路を通した」と読める記述を作らない。

## 判断が割れうる前提 (親の provisional 裁定。攻撃対象)

- **(P1)** E leg の範囲。親の provisional = **login の `--preview-wire` だけで足りる**。
  N6 の通り実行 leg は計算ノードを要し、seal に必要な `outcome` / `evidence_digest` は
  文字列と sha256 であって ledger は意味を検査しない (N2) ため、compute leg を足しても
  **ledger 側の生死判定は変わらない**。compute の `--no-build` dry-pass 1 本を足すかは費用対効果の判断。
- **(P2)** 判定の合格条件。親の provisional = 「(a) 3 event が receipt を返す (b) 同一 wire の
  R=2 が `replicate_ordinal` 0/1 として別 member に載る (c) seal 後に
  `read_sealed_batch` 相当で wire bytes が復元でき preview の bytes と一致する
  (d) 負の control として R=2 の commitment を同一にすると拒否される」の 4 点。
- **(P3)** 軽量版判定。親の provisional = **軽量版** (受理集合不変・防壁不接触・実装面は probe 1 本)。
  段 2・3 を省き、`4→5→6→7→8→9`。ただし本 wave の産物が「主張」そのものであるため、
  段 6 の敵対レビューは**省かず 2 本**回す (恒真な probe = 何も証明しない probe の検出が主目的)。

## 環境

- 実測・受入は Pegasus **login ノード** (probe は git + hashlib のみで重い処理を持たない。
  §7.0 の量基準で login 可)。compute leg を採る場合のみ qsub。
- 受入全走 (pytest) は計算ノードで行う (runbook §7)。

## 並列分割方針

実装面は probe 1 本のみのため段 5 は Codex `role=author` 実装子 1 本。段 6 はレビュー 2 本を並列。
