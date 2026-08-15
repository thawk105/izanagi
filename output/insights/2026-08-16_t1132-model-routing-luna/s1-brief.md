# t1132 段1 brief — codex model routing (sol→luna) 再検討

**scope**: `docs/dev-wave/operations.md` DW-O01 の model 権威行 (`docs/dev-wave/operations.md:14`) が
指定する dev-wave 段2 (plan)・段5 (author)・段6 (review/fix/focus) の codex model を
`gpt-5.6-sol` → `gpt-5.6-luna` (+ reasoning effort `high`→`max`、段5/6限定) へ変更できるか検討する。
段3 (敵対相談) の現行 sol+luna 混成は変更しない (D241 済裁定、対象外)。

**確定済みユーザー裁定**:
- D241 (2026-08-08, `docs/decisions.md:11243`): ほぼ同一のユーザー依頼を「段3のみ2レンズ混成、
  他段 sol 維持」で裁定済み。全 luna 化は NO-GO (段3検出力低下、規律2該当)。91%/30% の数値は
  policy 根拠として自己否定済み (circular・非盲検・n=1・事前登録なし)。
- D243/D266 (`docs/decisions.md:11340`, `:12259`): 段6 review/focus の reasoning=high は
  ユーザー明示裁定で据え置き。A/B 証拠が未認証のため引き下げ不可、supersede は明示ユーザー裁定のみ。

**不変条件 (コード実測)**:
- (I1) `tools/dev_waves/launch_authority.py:396-397`: 他段(2/5/6)の model は段3レンズ1の model と
  一致必須。(I2) `orchestrator/tests/test_dev_wave_launch_authority.py:98-101`: 段3の2レンズは
  異なる model 必須。→ 全段 luna 化は現行コードで構造的に不能 (D241 の拒否構成を機械的に阻止)。
- (I3) 他段(2/5/6)は現行コードで単一の `other_model` に束ねられ、段2/5 だけを段6 と切り離す
  独立設定は出来ない (分離にはコード変更が要る)。

**(P1) provisional [親の暫定判断・攻撃対象]**: 段2(plan)・段5(author)の出力は下流
(段3敵対相談 / 段6敵対レビュー+変異matrix+受入全走) で独立再検査されるが、段6自体は終端検出層で
下流に独立検査が無い。ゆえに段6を無評価で luna 化するのは、D241 が段3を保護した論理と対称的に
危険、というのが親の暫定判断。

**(P2) provisional [攻撃対象]**: T-184/T-189 (妥当な比較実験の設計) は今も未着手で、
「品質がほとんど変わらない」を裏付ける新規証拠はゼロ。この wave 内で即席の n=1 比較を作ることは、
2026-08-08 に「circular・非盲検・n=1」として自己否定されたのと同型の誤りを繰り返すだけで
証拠にならない、というのが親の暫定判断。証拠皆無のまま何らかの変更に踏み切ってよい範囲はどこまでか。

**成果物の形**: 段2は「段2/5を luna@max へ変更する場合の具体的 docs/code 編集案」を file:line 粒度で
起草する (I3 を解く実装を含む案・含まない案の両方を検討可)。段3 は2レンズで、
(a) I1〜I3 を踏まえた実行可能性、(b) P1 のリスク非対称の妥当性、(c) 証拠皆無のまま実施してよいか、
(d) 「flip trick」(権威行の sol/luna 位置を入れ替えるだけで docs-only のまま段2/5/6 を luna 化する
案。`--lane sol` が実際には luna を起動する名前逆転という footgun がある) を安易な近道として
採用してよいか、を攻撃する。

**変更面 (実アンカー、実装する場合のみ)**:
- `docs/dev-wave/operations.md:14` (DW-O01 権威行) — parent 直接編集可 (docs-only)
- `tools/check_docs.py:264-267` (`DEV_WAVE_DW_O01_MODEL_AUTHORITY_LITERAL`) — 実装子必須
- `orchestrator/tests/test_check_docs.py:6922-7256` 周辺の期待値 — 実装子必須
- `orchestrator/tests/test_dev_wave_launch_authority.py:98-145` — 変更範囲次第で実装子必須
- I3 を解く場合のみ `tools/dev_waves/launch_authority.py` — 実装子必須、受理集合変更 → 変異matrix要

**分割方針**: 段2・段3は各1回相当 (段3は2並列)。実装が要る場合の段5は単一実装単位
(所有パス素集合 = 上記ファイル群)。worktree 分割は不要な規模。
