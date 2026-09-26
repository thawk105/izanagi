---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: worktree-dev-wave-t2797-b5-v2-prep
seq: 1
---

## 新規

### {{F:b5-critic-instruction-quarantine-loop}}. critic 診断が他 role 宛ての「指示」を名乗り、coder の検疫が同じ診断に 11 回続けて却下した [手順漏れ]

- 事象: B-5 v1 本走の write-heavy の LLM 系列 (2026-09-23) で、14 機会のうち 11 件が coder の `instruction_like_content_detected=true` の申告により K2 consumer の検疫で却下された。
  評価 1 の critic 診断の `## recommend` 項 3 が「採否の読み方 (次の critic 評価への指示)」と別 role 宛ての指示を名乗り、11 件の coder がすべてこの節だけを名指しした。
  評価 2 が起きないので critic は走り直さず、同じ診断が 11 回入力された (A だけを消費する吸収状態)。検疫は設計どおり働いた。
- 根本原因: critic の役割文書は出力を「次の一手の構造化指示」と定め、B-5 の critic への入力は recommend / avoid が次の planner・coder へデータとして逐語で渡ることも、
  他 role 宛ての指示・採否手順を書かないことも述べていなかった。coder の役割文書は指示めいた文字列の検出で必ず true を求める。両者の間の約束が入力に無かった。
- 恒久対応: `tools/b5_llm_round.py` の v2 cohort の critic 入力 (`output_format_request`) に要請を足した ({{D:b5-v2-execution-contract}})。検疫・coder の役割文書・節抽出は変えない。
  吸収状態そのものは機構で防がず、`docs/b5-generator-contrast-preregistration-v2.md` §4.1 で開示した。
- 再発検知: `orchestrator/tests/test_b5_llm_round.py` の v2 critic prompt の bytes test。本走では台帳の却下 event の理由を系列ごとに数える (v2 §7.4 の報告項目)。

## 再発

### F283

- **再発: 2026-09-26** — [T-2797] v2 準備 wave で、段 5 の統合状態を未 commit のまま焦点走に出し、189 件の赤の大半が contract-loader-drift (`p3_s4_loop.py` の disk bytes が HEAD blob と不一致) の偽赤になった。統合 commit の後の再走は 3 件 (本 wave の新規部分) だった。
