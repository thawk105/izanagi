# 親 brief — [T-2067] oracle manifest 群への床値選択強制

## 対象 repository

/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection
branch worktree-dev-wave-t2067-oracle-manifest-selection、base = local main 6ff06800d。

## scope

D1370 が定めた狭い公開 API `s8b_ratified_freeze.assert_g1_floor_selection_identity` を、
批准床値を静的 loader だけで読む oracle manifest 側の consumer へ強制する。
着地済みの s8c 側と同じ引数・同じ拒否理由で、g1 でだけ効かせる。

## 確定済みユーザー裁定 (蒸し返さない)

逐語は同 directory の rulings-verbatim.md にある。要点だけ再掲する。

- D1325: 削除された earlier run を戻す authority と、g2 以降の選択・投影は
  「戻さない・g1 のみ」で固定。g2 が実在してから設計する。
- D1370: `launch_validate` を再利用しない。狭い API を使う。activation HEAD、
  current build admission、closure、binding graph、live scan は持ち込まない。
  selected certificate と path 起動秒は検証しない。新しい拒否理由を作らない。
- D1371: C06 予算経路、起動証明書の実時間性、s8c production final claim 配線は実装しない。
  production へ test 専用の抜け道を入れて緑にすることはしない。
- D1313 / D1241: advisory / non-certifying 上限は解除しない。

## 親が実測した事実 (plan の前提。誤りを見つけたら反証を書け)

- `reverify_published_freeze` (s8b_ratified_freeze.py:3657) は `_launch_validate` を呼び、
  `_launch_validate` は s8b_ratified_freeze.py:3305 で選択 identity を既に強制する。
  よって s8b_oracle_report.py:2547、s8b_verdict.py:828、s8b_oracle_judge.py:749 は
  被覆済みであり、本 wave の実装対象ではない。
- 未被覆の load-only 入口は s8b_oracle_manifest.py:1205 の `build_approved_manifest` である。
  同 file の `build_manifest_from_ratified` (842) の呼び手は 1244 の 1 箇所だけで、
  それは `build_approved_manifest` 自身である。
- 着地済みの先例は s8c_result_judge.py:2075 `_load_selection_checked_ratified_floor` で、
  load → `assert_g1_floor_selection_identity` → `RatifiedFreezeError` を consumer 固有型へ
  再送出する形をとる。
- 既存 test の 2 正例 (orchestrator/tests/test_s8b_oracle_manifest.py:1369 と 1395) は
  `_synthetic_ratified_freeze` (同 file 272) が `generation_number=1`、
  `generation_commit="b"*40` の合成 freeze を返すため、gate を素通しでは通らない。
  この fixture 追随が本 wave の実作業の中心である。
- `_GENERATOR_SOURCES` (s8b_oracle_manifest.py:65) は s8b_oracle_manifest.py 自身を含まない。
  よって本 file の編集は manifest の generator_versions を動かさない。

## 不変条件

- 規律 2 を緩めない。既存の正例を通すために production へ test 専用の分岐・環境変数・
  「root が tmp なら飛ばす」型の抜け道を入れてはならない。D1371 が名指しで却下した形である。
- 新しい拒否理由を作らない。失敗は既存の `floor-selection-unverifiable` /
  `floor-selection-eligibility-underivable` / `floor-selection-rule-mismatch` へ畳む。
  consumer 層で ManifestCliError へ写すときも reason 文字列を新造しない。
- 凍結成果物の bytes を変えない。
- g1 以外では何も観測せずに返る、という D1370 の性質を壊さない。
- 検査を通すためだけの恒真な assert を書かない。

## (P1) 親の provisional 裁定 — 攻撃対象

- (P1-a) gate の位置は `build_approved_manifest` の `load_ratified_freeze` 直後とし、
  `build_manifest_from_ratified` には置かない。
- (P1-b) 既存 2 正例の追随は s8c 先例に倣い monkeypatch seam を使う。ただし選択 assert と
  loader の両方を stub した緑は機構を通らないので禁じる。実 callee を名指しで通る正例と
  負例を最低 1 本ずつ置く。
- (P1-c) s8b_oracle_driver.py:496 と 644 も静的 loader だけの経路である可能性があるが、
  これは「oracle manifest 群」ではない。本 wave では実装しない。所見として報告する。

## 成果物の形

production 1 file (s8b_oracle_manifest.py) + test 1 file
(orchestrator/tests/test_s8b_oracle_manifest.py) の差分。docs は親が別途書く。
仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外である。
