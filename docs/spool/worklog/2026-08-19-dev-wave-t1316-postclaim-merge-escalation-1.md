---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1316-postclaim-merge-escalation
seq: 1
title: '[T-1316] 受入 postclaim merge の author 要件を条件付き Codex 昇格にした (D554、コード+テスト+記録、branch worktree-dev-wave-t1316-postclaim-merge-escalation、変異matrix = 本走 4/4 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- D554 (2026-08-19 ユーザー裁定) の実装。`tools/dev_wave_wait.py` の受入 postclaim merge を
  「merge_message_file 未指定時は self-report (`product=claude; role=integrator`) を生成し、
  既存の `check_ai_provenance.py --message-file` 判定 (両親と食い違う実装面 path があるときだけ
  Codex role=author を要求) へそのまま委譲する」設計へ変更した。
- 段2 codex plan・段3 敵対相談2レンズが、command 引数の指定範囲 (postclaim のみ) より広く
  preclaim gate (`tools/dev_wave_wait.py:3739-3747`) も緩和しないと変更が実行時に到達しないと
  独立に確認した。scope レンズは当初 NO-GO 判定 (blocker 8件) だったが、精査の結果 D554 決定文が
  `role=integrator` の無条件付与を明示例示していること、caller identity の機械束縛欠如・
  rename 扱い・明示 Codex message の path-author attestation 欠如は D554 の scope 外 (裁定
  パッケージ候補) と裁定し、docs 変更のうち `docs/dev-wave/operations.md` DW-O17 への注記だけ
  予算超過 (実測: 残 26 bytes) で見送った。
- 段5 実装子 (Codex `role=author`, model=gpt-5.6-luna, reasoning=max) が
  `tools/dev_wave_wait.py` + `orchestrator/tests/test_dev_wave_wait.py` を実装。段6 敵対レビュー
  2本は blocker 0件・nit 6件 (テスト名3件が旧挙動のまま、fake conflict テストの名前倒れ1件、
  self-report bytes 定数の重複1件、path-aware provenance stub の実装面判定が `tools/*.py` 限定で
  規約より狭い1件)。fix (一枚岩投入) で改名4件・定数統一・stub 精度向上を実施し、統合後の焦点
  再レビューで 5件 closed・1件 partial (`patches/` 除外の細部、今回のテストシナリオに無関係と
  親裁定で対応不要とした) を確認した。
- 変異 matrix: probe 走で4変異 (self-report role値変更・product値変更・self-report/明示ファイル
  優先分岐の反転・preclaim gate 復活) が実質 KILLED 相当と確認し、実測 failed_nodes を
  expected_nodes として確定した正式 spec で本走し、4/4 KILLED・matches_expectation 全件 True・
  MISMATCH/SURVIVED/TIMEOUT いずれも 0 を確認した (`output/insights/2026-08-19_t1316-postclaim-merge-escalation/mutation/mutation-spec.json`)。
- 実装 commit `35f7918b`。trailer は段5/6 Codex receipt から実測した
  `product=codex; model=gpt-5.6-luna; reasoning=max; role=author` (親の統合は機械的代行のため
  integrator 行は付与せず)。commit 後の既定 full-history 監査 rc=0・4348件・新規違反なし。
- 付帯タスク (command 引数): 取り残し branch `worktree-rulings-20260819-selfimprove` の F419
  失敗知見は、main 側 `docs/failures.md` に byte 単位で既に同一内容が存在すると確認し
  (blob 照合)、追加作業なしで完了とした。
- 段4裁定完了まで DW-O20 (`check_wave_startup.py`) を実行せず、submodule 未初期化・handoff の
  worktree 内残留・HEAD の local main からの遅れを段5投入準備中に発見・是正した (実装着手前で
  実害なし)。F50 と同型の再発として failures fragment へ記録した。

## 次の一手差分

### 完了

- [T-1316] D554 の実装・敵対レビュー・fix・変異 matrix・記録を完了した。受入は本 fragment
  commit 後に投入する。
  remaining: none
  base: 4c518be17fda52ed22fc3b4e249b2d323a09324439df81278386127308179f0d
