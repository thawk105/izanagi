---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t828-cancellation-record
seq: 1
title: CFAB-R4-CANCELLATION-RECORD を resolved にした — 段6 敵対レビューが decoy 脆弱性2件を発見・修正 (コード + テスト + docs + 記録、branch worktree-dev-wave-t828-cancellation-record、変異 matrix = baseline 84 passed・3/3 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- [T-828] (2026-08-12 /rulings 裁定 (a)) を実装した。段2 codex plan (read-only) + 段3
  敵対相談2本 (read-only) は blocker 0 件・must-fix 1 件 (共通 fence-robustness の cancellation
  版3本は kill power ゼロの冗長 test と判定、不採用)。
- 段5 実装後、親が自ら `tools/run_tests.py` を実走して検証したところ、revocation/cancellation
  両テーブルの `reason` 制約文言が同一のため、既存の revocation 側テストまで壊れる
  `text.count(target)==1` 衝突を発見した (fix1 で解消、86 passed)。
- 段6 敵対レビュー2本: レンズA (正しさ・網羅性) は所見なし。レンズB (decoy 構成) が、
  fence 無しの平文 canonical decoy で `_extract_design_cancellation_schema` を欺けることを
  実証 (must-fix)。fix2 (record 名一意性検査を先に追加、revocation にも同型を一般化 —
  DW-G03) で解消、regression pin 2本、88 passed。
- fix2 統合後の焦点再レビュー (DW-S06-C) が NO-GO — 全角 homoglyph で fix2 の byte-exact
  検査を回避できることを実証。fix3 (NFKC 正規化) で解消、regression pin 2本、90 passed。
  親が自ら追加検証し、ゼロ幅文字混入では NFKC でも同型 decoy が理論上なお成立すると確認、
  この残存はここで追加対応を打ち切り {{F:record-name-decoy-slips-past-table-prefix-check}}
  へ記録した (恒久対応の設計判断は {{D:record-name-uniqueness-defense}})。
- 段2 plan・段3 レンズA・親の3者が独立算出した `required_gates.entries_sha256`
  (`51efdac4...`) が一致し、独立性を確保できた。
- 変異事前登録は当初 M1 (cancellation の外側 schema 等価性検査) の期待 node を過大に見積もり
  1 回 MISMATCH になった (plaintext/homoglyph decoy テストと table-only fence decoy テストは
  実際には extractor 内部の別チェックで拒否されており、M1 の担当ではなかった)。spec を訂正して
  再投入し、baseline 84 passed・3/3 KILLED・SURVIVED 0・MISMATCH 0 で緑にした。
- Codex 子 (author・fix×3・review×3・plan・consult×2、全 model=gpt-5.6-luna・reasoning=max)
  はいずれも Pegasus dispatch preflight (`qstat -Q rc=1`) へ到達できず pytest 未実走のため、
  親が全段で `tools/run_tests.py` を実走して検収した。

## 次の一手差分

### 完了

- [T-828] gate `CFAB-R4-CANCELLATION-RECORD` を resolved にし、段0の blocking gate を 5→4 件へ
  進めた。残る decoy 耐性の限界は {{F:record-name-decoy-slips-past-table-prefix-check}} へ
  既知の残存として記録し、追加タスクは起票しない。
  remaining: none
  base: 0f6d137ddb51c8b8ed62053f1d775624976f3bd7b986e254615fe9204a31a668
