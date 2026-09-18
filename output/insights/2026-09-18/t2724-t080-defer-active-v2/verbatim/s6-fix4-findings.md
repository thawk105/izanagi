# 段 6 fix-4 の指示 (親、2026-09-18 14:00 JST)

焦点再レビュー (`s6-rereview-1`) は NO-GO、must-fix は 1 件 (RR-1)。両木の焦点走は緑 (chain 無し 2672 passed / 0 failed、chain 有り 1097 passed / 0 failed、修正前 45 node の残存 0)。基点 = 現 tip `b0a7804d7` (= fix-3 `8b8bb96f2` + runbook docs commit + main 44b00f2af の merge)。

## I1. RR-1 — 接続 fixture の受入材料を親 root から読まない (test 側のみ)

fix-3 で接続 9 node (接続 8 + draft 1) を real-repo reader 登録から外した根拠は「実 root 読取りは shared base を組む 1 回だけ」だったが、`test_s8b_ratified_freeze.py:build_production_emitter_g1` の receipt 接続分岐は copy 後にも親 root を読む: (a) `:1044` `_real_bytes(calibration_path)` (親 `_ROOT` の calibration file)、(b) `:1045〜1047` `_PREDICTION_SOURCE_PATHS` / `_PREDICTION_PARSER_PATH` の不足分を `Path(_ROOT) / relative` から補う。shared base の key lock は real-repo writer と共有する lock ではないので、登録解除の前提が成立しない。

直し方 (receipt 接続分岐 = `receipt_root` が渡された経路だけ):
- (a) calibration bytes は **receipt_root (= 接続 base の copy) 内の同 path** から読む。接続 base は実 root の tracked output を複製しているので `root / calibration_path` は存在するはず。存在しなければ fail-closed (assert) — 親 root へ fallback しない。
- (b) `_PREDICTION_SOURCE_PATHS` / `_PREDICTION_PARSER_PATH` も同様に **root 内の存在を要求**し、不足なら fail-closed。接続 base は `orchestrator/` 全体と `output/s8b-freeze/holdout_freeze.json` を持つので存在するはず。親 root へ fallback しない。
- `_install_emitter_selector_prediction` (`:706〜`) が `Path(_ROOT) / relative` を読む分岐も、接続経路では到達しない (destination が存在する) ことを現物で確認し、到達しうるなら同様に fail-closed へ。
- 通常の emitter fixture (`_prepare_emitter_base` 経路、receipt_root 無し) は従来どおり親 root から材料を取ってよい (その test 群の分類は変えない)。
- 変更後、接続 9 node が test 実行中に親 root / 共有 ccbench を読む経路が **shared base の構築 (key ごとに session に 1 回、既存 stub-free e2e と同じ)** 以外に無いことを `grep -n "_ROOT\|ROOT /" ` 等で静的に列挙し、報告に表で書く。

## I2. 変えないもの

production 3 file、S、走査除外・hold・allowlist、既存 tracked test の期待値、fix-3 の登録簿 (RR-1 が閉じれば現状の未登録が正しい)。sink pin は不変。

## I3. RR-4 (報告の量化) は親が README で直す。fix 子は対応不要。

## 対応表

I1〜I2 を closed / partial / regressed で。所有外への波及 (test_s8b_ratified_freeze.py の他 caller: `load_emitter_g1`、g2 emitter、通常 fixture) を静的列挙。
