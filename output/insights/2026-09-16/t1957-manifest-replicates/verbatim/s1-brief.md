# 段 1 brief — [T-1957] 8c trial manifest へ cell ごとの反復数を持たせる

## 研究前進

論文 §8 B-2 (descriptor を条件にした合成の因果証拠) の正式系列 8c は、実走前に確定する
6 cell manifest を発行しないと動かない。8b 設計 §10.2 は逐語で
「`n` は整数かつ 2 以上。登録した `n` は観測反復数と exact に一致しなければならない —
**manifest は cell ごとに `n` を持ち**、全 cell の観測反復集合が登録値と完全一致しないときは
当該対比を判定不能とする」と要求する。現行 schema `p3-8c-trial-manifest/v2` の trial key 集合は
`{trial_id, arm, holdout, campaign_id, generations}` で `n` が無く、**仕様に適合する manifest を
そもそも書けない**。本 wave は schema に cell ごとの `n` を足し、型・範囲・cell 間整合を
機械検証する validator を置く。完了判定 = (1) 正しい 6 cell manifest が load を通る正例 1 本、
(2) `n` 欠落・非整数・bool・`n<2`・cell 間不整合を拒否する負例、(3) 受入全走と変異 matrix が緑。

## 段 1 実測 (一次資料)

- 対象 path は `orchestrator/campaign/trial_registry.py`。8b oracle manifest
  (`8b-oracle-manifest/v1`、schedule 行に `replicate_index` を既に持つ) とは別物。
- **記録済み manifest は 0 件。** `git grep -l "p3-8c-trial-manifest"` = 6 file (decisions / 実装 /
  test / insight 3 件) でいずれも実体でない。`output/s8c-trial-registry/` 不在。
  `git ls-files --others --exclude-standard -- output/` = 0 件なので未追跡の実体も無い。
  job-evidence にも 8c 系列は無い。→ **反復数を復元する母集合が空。復元不能な範囲も移行対象も無い。**
- 8c 事前登録 §5 の「反復単位対比の判定パラメータ (H1 / H2: n・…)」欄は未記入。同 doc の記入規約は
  「同欄を記入してよいのは、型・単位・範囲を機械検証する consumer が実在するときに限る」と定める。
  8b §10.2 も「値を記入してよいのは…schedule generator・manifest・反復束縛が固定済みであること」を
  先頭に挙げる。**schema 固定は §5 記入の前提工程であり、順序は逆でない。**
- **凍結境界 (DW-O09)。** `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g1..g15.json`
  が `section5_field_names_sha256` / `normative_body_sha256` / `protected_sha256` /
  `section6_conditions_sha256` で事前登録 doc を pin する。→ 事前登録 doc は本 wave で編集しない。
- **key 集合の第 2 の pin。** `orchestrator/campaign/s8c_preregistration_evidence.py:1650-1656` の C03
  評価器が `_trial_canonical_tuple` の参照属性に 5 key を要求するが **`<=` の部分集合検査**なので
  6 個目の追加では赤にならない (実測: 演算子は `<=`)。
- **受入側の既存不整合 (本 wave では直さない)。** `trial_registry.py:3600-3612` は
  genesis の `attempt_index == 0` slot 集合を `replicate_index` を 0 に固定した期待集合と比較する。
  よって **n≥2 の genesis は構造的に受理されない**。8b §10.2 は n≥2 を要求するので、
  ここは将来必ず変わる。ただし修正は受理集合を広げるため D959 が禁じる向きであり scope 外。

## scope

- in: `trial_registry.py` の `_TRIAL_KEYS:117` / `TrialSpec:276` / `_parse_trials:755` /
  `load_trial_manifest:805` / `_trial_dict:827` / `_trial_canonical_tuple:1566` /
  `MANIFEST_SCHEMA_VERSION:55`、および `orchestrator/tests/test_trial_registry.py`。
- **registration も同じ経路を共有する。** `_parse_trials` と `_trial_dict` は manifest と
  `p3-8c-trial-registration/v2` (`REGISTRATION_SCHEMA_VERSION:56`、生成 `:844`、解析 `:913`) の
  両方が使う。片方だけ足すと registration が manifest を写せなくなるので、両方を同時に扱う。
  記録済み registration も 0 件 (`output/s8c-trial-registry/registry.jsonl` 不在)。
- out: 事前登録 doc の編集、§5 の記入、manifest / genesis / registry の実体発行、
  受入 gate `:3600-3612` の受理集合拡大、族一般化、仮想リスク向けの追加 gate・検査・台帳。

## 不変条件

- 規律 2 を緩めない。受理集合を広げる変更を入れない (追加 key は必須にして狭める向きだけ)。
- `docs/phase3-8c-preregistration.md` と `docs/phase3-8b-descriptor-design.md` を編集しない。
- artifact を 1 件も発行しない。§5 の欄を埋めない。
- 実装面は Codex `role=author` が書き、親は docs だけ書く (D95)。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- (P1-a) schema 拡張は D959 の「(b)〜(e) を順序を入れ替えて先に解除してはならない」に**当たらない**。
  根拠は上の実測 3 点 (artifact 0 発行・§5 不記入・受理集合は狭まる向き) と、8b §10.2 が
  manifest 固定を §5 記入の前提として先に置いていること。
- (P1-b) 反復数の置き場所は **trial (= cell) ごと**とする。8b §10.2 の逐語「manifest は cell ごとに
  `n` を持ち」に従う。§5 は n を holdout 単位 (H1/H2) で置くので、同一 holdout の 3 arm で
  値が一致することを validator が要求する。
- (P1-c) schema version は v3 へ上げる。記録済み実体 0 件なので後方互換は不要。

## 成果物と分割

コード + テスト + worklog / insight。実装子 1 本 (単一 module + 単一 test file で所有が割れない)。
段 2 plan 1 本、段 3 レンズ 2 本、段 6 review 2 本。受理集合が変わるので軽量版にしない。
