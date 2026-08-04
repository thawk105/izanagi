# [T-428] 段 1 brief — reflux_ir を production 受理経路へ配線し、候補表現を 5-bit wire へ閉じる

日付: 2026-08-04。branch `worktree-dev-wave-t428-reflux-wiring`。軽量版不可 (受理集合が変わる、DW-C00)。

## scope

trigger-gating 軸の候補受理を「構造検疫を通る任意の 1 行 C++」から「5-bit wire だけ」へ縮小する。
consumer 閉包 5 面を同一変更単位で塞ぐ: (a) `p3_s4_loop_trigger_gating.py` の受理点
(`load_proposal_file:571-601` / `_quarantine_and_audit:358-402`)、(b) proposal schema
(`projection_guard.assert_closed_proposal_schema` — 現状キー集合のみで値は無検査)、(c) materialize
(`p3_s4_loop.quarantine:184-221` — 生文字列を書く)、(d) build cache (`pipeline.variant_id` /
`source_digest.src_token` — mask 概念なし)、(e) replay (`wal.replay:716-747` — 再検証なし)。
binding 欠落 artifact の拒否は `artifact_admission` 面。D96 手続 (新 D + 境界テスト同一変更単位) を満たす。

**成果物影響 (DW-G05):** 実装しない場合、受理集合は任意 1 行 C++ のままで D121 P1 が恒偽のまま
残り、多世代開放の前提が永久に成立しない。既存 certified 選択・レポート・台帳の値は変わらない
(現行運転は 1 世代 cap 内で、歴史 artifact の bytes にも触れない)。

## 確定済みユーザー裁定 (前提)

- D96 ([T-110]): 受理集合変更は新 D + 境界テスト追随を同一変更単位で。機械検査は新設しない。
- D121 決定 (7): P1 = 「候補表現が固定 5-bit IR に閉じる」∧「全 32 mask 監査済み emitter」。
- D149: emitter は監査済み (順序保証)。決定 (6) が wiring 時の D96 手続を予告。決定 (4) の
  0 bit 拒否契約は leaf の API 契約。D114: `MAX_APPROVED_GENERATIONS = 1` は不変。

## 前提実測 (brief 前、親 + Explore 子の一次確認)

- `reflux_ir` の production import ゼロ (grep 全走査。consumer はテストのみ) — D149 決定 (6) と一致。
- 自由受理の実在: `CoderProposalTriggerGating.implementation` は `__post_init__` なし・schema は
  キー集合のみ・構文契約は 5 識別子 grep のみ (file:line は scope 節)。
- 変更面の周辺 pin (DW-O09): freeze 系 = `s1_expected_goldens.py` / `test_frozen_artifacts.py` /
  `test_s1_*_freeze.py`、reflux golden = `reflux_ir_expected_goldens.py` (テスト専用台帳)。
  分類: 全て凍結 snapshot / 独立 golden で、本 wave はどの bytes にも触れない (不変条件 I1/I2)。
  DW-O10 は非適用 (凍結成果物の producer 出力 bytes が変わらないため)。

## 不変条件

- I1: 凍結成果物 (s1-freeze、campaign 歴史記録、golden 台帳) の bytes 不変。
- I2: `orchestrator/campaign/reflux_ir.py` は変更しない (D149 の監査主張を保つ)。変更が必要と
  判明したら停止して裁定へ。
- I3: 拒否は既存 reject 経路 (WAL subtype 記録) の開示水準を超えない。[T-429] (多面開示の閉鎖)
  は本 wave の scope 外 — 開示を新たに増やさないことだけを守る。
- I4: `MAX_APPROVED_GENERATIONS = 1`・cap-lift FAIL・規律 1〜3 に触れない。
- I5: sort / backoff 軸の受理経路 (`p3_s4_loop.py` 共有部) の挙動を変えない。trigger-gating 専用の
  縮小に閉じる。

## 親の provisional 裁定 (攻撃対象)

- (P1) proposal は `implementation` 自由文字列をやめ、5 文字 wire を運ぶ。loop は
  `parse_wire → TriggerGateIR → emit_predicate` の唯一経路で C++ を導出し、coder 由来の C++ を
  materialize に渡さない。代替案 (implementation を受けて byte 照合) は段 4 で棄却/採用を確定。
- (P2) binding = raw mask を WAL payload・provenance entry・report に同梱し、materialize 済み
  ソースとの整合 (emit_predicate 再計算一致) を replay / admission で再検証する。mask は
  `variant_id` へ直接は足さない (src_token 経由で既に決定的束縛があるため、二重会計を避ける) —
  ここは段 3 の攻撃点。
- (P3) binding 欠落の拒否は trigger-gating 軸の新規 artifact に限る (歴史 artifact を遡って
  拒否しない。遡及拒否は受理済み台帳の意味を変えるためユーザー裁定事項)。
- (P4) coder 子 (`coder-v4-autonomous-trigger-gating`) の出力契約変更が要るなら agent 定義の
  変更も同一変更単位。ただし遮断設計 (ツールなし・構造化出力) は変えない。
- (P5) 受入環境 = この login node、`tools/run_tests.py` 全走 + `check_docs` + provenance 監査。
  性能実測なし (dev harness のみ)。

## 検出力の純増 (DW-S01 の被覆検索)

既存被覆 (test_p3_s4_loop_trigger_gating 59 本、test_diff_quarantine 38 本、test_p3_s4_loop、
test_reflux_ir 17 本) は構造検疫・識別子ブラックリスト・IR 単体契約を固定するが、**語彙の 5-bit
閉包・binding 束縛・replay 再検証はどのテストも固定していない**。純増 = (i) 自由 C++ の拒否、
(ii) wire 不正の拒否、(iii) binding 欠落 WAL/provenance の検出、(iv) replay の binding 再検証、
(v) 境界テストの新受理集合への追随 (D96)。

## 並列分割方針

段 5 は Codex author 2 体・所有分離を仮置き: 子 A = 受理経路 + schema + 唯一経路化 (loop driver、
projection_guard、agent 契約)、子 B = binding + admission/replay + 境界テスト追随。ファイル所有の
重なりは段 4 で確定。段 2 プラン起草 1 体 (read-only)、段 3 敵対 2 レンズ、段 6 敵対レビュー 2 本。
