# [T-1357] 段1 brief — DENY_TABLE 縮小検出検査

## scope
`orchestrator/campaign/coder_effect_gate.py` の `DENY_TABLE` (5 category, identifier 計約96) が
個別 identifier 単位で黙って縮んでも既存テストが検知しない穴を塞ぐ**検査追加のみ**。
production の `DENY_TABLE` 内容・`scan_host_effects` の受理/拒否挙動は変更しない。

## 確定済みユーザー裁定
[T-1357] 2026-08-18 `/rulings` 全件第8回「設計する」。ratified 文言 (`docs/archive/worklog-phase3-0819-671.md:555`):
「禁止集合が縮んでいないことを意味で守る検査を設計する。変異 M6 が SURVIVED ですり抜けを実証しており、
正しさの門を緩める方向の穴である。」

## (P1) 実装対象ファイルの scope 選定 — 攻撃対象
T-1357 起票本文 (`docs/archive/worklog-phase3-0818-651.md:595`) の真の動機は role 契約 pin
(`.claude/agents/coder-v4-autonomous-sort.md` の closed-region 5 bullet を守る
SOURCE_FILE_SHA256 等 byte pin) だが、ratified 短縮文は対象ファイルを名指ししていない。
本 `/dev-wave` 引数は `coder_effect_gate.py` の `DENY_TABLE` へ明示的に narrow 指定した。
本 wave はこれに従いこのファイルへ限定し、role-contract-text 側の pin 穴は別懸念として
段7で worklog へ残す (実装しない・別 T 化を検討)。

## (P2) 引数の動機記述の stale 訂正 — 攻撃対象
引数が引用する「`test_coder_effect_gate.py:151` が bounded loop 通過を明示的に固定」は
2026-08-15 時点の事実。2026-08-18 commit `dc87fff7` (main 済み、[T-396] 裁定 B 実装) が
当該テスト (`test_ordinary_for_range_for_and_data_dependent_loops_pass`) を削除済みで、
現 line151 は無関係な別テスト (`test_explicit_unconditional_loop_headers_are_rejected`)。
本 wave の動機は代わりに (a) `output/insights/2026-08-15_t396-hole-allowlist-refuted/README.md` §7 の
DENY_TABLE 欠落項目表 (非決定 builtin 禁止の不在等)、(b) wave651 の一般教訓
「pin は bytes 同一性しか証明しない」(`docs/archive/worklog-phase3-0818-651.md:36-40`) で再構成する。
bounded loop 自体の拒否可否は変更しない (択一 B は解決済み・不覆)。

## 不変条件
(a) production `coder_effect_gate.py` の `DENY_TABLE` 内容・`scan_host_effects` 挙動は不変。
(b) 新検査は `DENY_TABLE` 自体から期待集合を導出しない (自己参照禁止 — M6 と同型の穴になる)。
(c) 新検査は独立 frozen 値に対し identifier 単位で「現在の集合 ⊇ frozen baseline」を検証する
(縮小だけを検知し拡張は許容 — 「縮んでいない」の直訳)。exact-equality にする場合は理由を明記。
(d) 一般化・共有 framework 化はしない (絶対規律5, DW-G03) — 本ファイル限定の局所修復。

## 既存被覆 (性質で先に検索済み) と純増検出力
`test_each_deny_table_category_has_a_mutation_killing_probe`
(`orchestrator/tests/test_coder_effect_gate.py:78-88`) が category 単位で 1 identifier/category だけ
非自己参照 golden probe (`_CATEGORY_PROBES`) を持つ。純増検出力 = 各 category の残り identifier
(概算 96 − 5 ≈ 91 件) の個別削除に対する検知力。

## 成果物影響 (DW-G05)
実装しない場合: 受理集合・certified 選択・材料レポートの値は不変 (production 未変更のため)。
失うのは「将来 DENY_TABLE から個別 identifier が黙って抜け落ちる」変異に対する検出力のみ。

## 変更面アンカー表
| file:line | 内容 |
|---|---|
| `orchestrator/campaign/coder_effect_gate.py:58-105` | `DENY_TABLE` 定義 (5 `DenyRule`) |
| `orchestrator/campaign/coder_effect_gate.py:117-132` | 既存 module-load 一意性検査 (重複は検知、削除は検知しない) |
| `orchestrator/tests/test_coder_effect_gate.py:67-88` | 既存 category-level probe (`_CATEGORY_PROBES`) |
| `orchestrator/tests/test_coder_effect_gate.py:91-98` | 既存 rule_id/category/identifier 一意性テスト |

## 成果物の形
`orchestrator/tests/test_coder_effect_gate.py` へ identifier 単位 frozen superset 検査を追加。
`coder_effect_gate.py` は不変が既定 (変更が要ると判断したら理由を明記し段4へ差し戻す)。

## 並列分割方針
分割なし。単一 codex `role=author` (段5) が担当。

## 受入・実測環境
純 Python unit test (CCBench/計算資源に非依存)。受入は標準 `tools/run_tests.py` 全走
(`tools/dev_wave_wait.py acceptance` 経由)。機体固有懸念なし。
