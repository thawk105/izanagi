---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1381-schedule-index-convention
seq: 1
title: schedule_index の cell-ordinal 規約を docstring として明示する (コード+テスト、branch worktree-dev-wave-t1381-schedule-index-convention)
---

## 本文

- [T-1381] `orchestrator/campaign/s8b_oracle_manifest.py` の `schedule_index` が
  build_schedule() の rows 平坦化通し番号 (cell ordinal) であることと、反復内 row 添字
  (`schedule_index % C`、構築時の性質であり `_validate_schedule` が独立検証する
  manifest-schema 不変条件ではない)・`s8b_oracle_n_pilot` の observation `seq`
  (schedule_index そのもの)・`s1_direct_comparison` の attempt 添字 (無関係な別 namespace)
  との対応を module / `build_schedule()` docstring へ明示した。field 名は契約で固定されて
  おり改名しない。対応関係を検証する pinning test を 1 件追加した。実装 commit `5b500b92`。
- DW-C00 の 3 条件 (設計択一が割れる/正しさ防壁に触る/受理集合が変わる) がいずれも不成立と
  判断し、段2・3 (codex plan/敵対相談) と段6 review-agent-pair を省略した軽量版で進めた。
  攻撃対象とした「反復内位置 (`position`) は表示専用で admission ticket 消費の鍵ではない」は
  実測 (`s8b_oracle_n_pilot.py:965-967` vs `:1010`) で確認済み。
- 変異検証: 親が `DW-M05` の自己登録同等物として手動 tracked-file 変異 (rows 構築を
  replicate-major から round-robin へ入れ替え、schedule_index の反復内連続性のみ破る) で
  `DW-M08` 準拠の dual-run を実施した。変更前 HEAD (3 file 対象、162 passed) は変異ありでも
  全緑のまま SURVIVED、実装後は新規 test だけが FAIL して KILLED (163 中 1 件、他 162 は
  緑のまま) — 単一理由性を実測確認した。両走とも復元後 byte 一致を確認。
- **セッション異常・救出**: 段6 の post-change 変異再検証で、実装子の未 commit docstring
  変更が乗った tree に対し `git status --porcelain` の非空確認を怠って `git checkout --`
  で復元し、実装子の成果も巻き戻った (F174 と同型の再発、2回目)。直後の `git diff --stat`
  で検知し、直前に取得済みの `git diff` 全文から docstring 2 箇所を verbatim 再現して
  完全復元 (復元後 diff が元の author diff と byte 一致、テスト再走で確認)。実害なし。
  詳細は F174 への再発追記 (本 wave 内 fragment) を参照。
- 着手前確認 (指示どおり): 並行 wave `dev-wave-t1142-n-pilot-admission-redesign` は稼働中
  プロセスを確認したが、`s8b_oracle_manifest.py`・その test file には file 非重複
  (merge-base 差分で実測)、概念的にも非矛盾 (t1142 Unit2 の `global_schedule_index` は
  本 wave が明示した flatten 通し番号の理解と整合)。land 待ち不要と判断した。
- 実測: `python3 tools/run_tests.py` で当 module を参照する consumer test 12 file
  (752 passed, 19 skipped)、`python3 tools/check_docs.py` 違反なし、
  `python3 tools/check_ai_provenance.py` 新規違反なし (4572件)。

## 次の一手差分

### 完了

- [T-1381] schedule_index の cell-ordinal 規約を docstring として明示し、対応関係を
  検証する pinning test を追加した。実装 commit `5b500b92`。
  remaining: none
  base: 998c478485e8ffce6123e3a8e759889f1d846582a583dbb8430a3c4ef95bbb76

### 新規

- {{T:dw-o19-precondition-hardening}} **P3・新規**: `DW-O19` (段6の一時変異手順) の
  「変異前をclean確認し」を、file 単位の差分確認でなく `git status --porcelain` 全体の
  非空確認として明文化する。F174 の恒久対応で改善候補として起票済みだったが未反映のまま
  2回目の再発 (F174 参照) に至った。
