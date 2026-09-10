# [T-1361] 焦点走を consumer test まで広げる義務を新規 L2 節 DW-O26 へ収容

## 裁定

[T-1361] P1 (2026-08-18 /rulings 全件第8回、`docs/archive/worklog-phase3-0819-671.md:571-573`、
[T-1245] と同一裁定): 「焦点走を consumer test まで広げる義務は新規 L2 節へ収容する。実測された穴
(F242 再発) で受入全走を1本失っているため、束の中で最優先とする。」

F242 (2026-08-18 再発分、`docs/failures.md:6770-6781`): 焦点走の対象 file 集合は「変更した
test file」だけでなく「変更した production file を import・実行する consumer test」まで広げる
必要がある、という恒久対応は `DW-O18` の L2 単節予算 (995/1000、余裕5 bytes) に収まらず未実装
だった。

## 実施内容

1. **予算精査 (段1 相当)**: `.claude/commands/dev-wave.md` の余白は 8 bytes (9492/9500) と実測。
   代替収容先 `DW-O18` (995/1000)・`DW-C01` (991/1000、今回実測) もいずれも満杯。前例 commit
   `ebf6b133` (2026-08-18, DW-C01 新設) の手口 (range 表記への圧縮) は既に本ファイルへ
   適用済みで再現不可と判明。
2. **段2 codex plan**: pin されていない安全な圧縮候補 3 箇所 (計 -15 bytes) を発見し、
   row 18 セルの複数節拡張 grammar (`, ` 区切り) が正当と確認 (`verbatim/s2-plan.md`)。
3. **収容方針**: `docs/dev-wave/operations.md` に新規節 `DW-O26` を追加。番号は `DW-O07`/
   `DW-O15` (削除済み ID、復活に新規裁定が要る) を避け、未使用の `DW-O26` を採用。
   `tools/check_docs.py` の `REQUIRED_REFERENCE_SECTIONS["docs/dev-wave/operations.md"]` は
   `_OPERATION_NUMBERS` 由来の集合と `{"DW-O26"}` の**独立 union**で登録し、
   `_OPERATION_NUMBERS`/`_ALL_OPERATIONS` 自体は不変のまま (段5/段6 `|C|` 行への波及を回避)。
   `CONDITION_DISPATCH_CONTRACT["18"]` を `(DW-O18, DW-O26)` へ個別上書き (`"15"` の
   既存パターンを踏襲)。
4. **段5 実装 (Codex author)**: `tools/check_docs.py` + `orchestrator/tests/test_check_docs.py`
   を実装。1回目は内容が正確ながら `## 総括` トレーラー欠落で not_accepted (親の prompt 不備)。
   中断子の部分成果物を保全し、2回目 (監査・確定 prompt) で accepted (`verbatim/s5-author.md`)。
5. **親の docs 編集**: `.claude/commands/dev-wave.md` (3箇所の安全圧縮 + row18 拡張、
   差引 -5 bytes、9487/9500 着地) と `docs/dev-wave/operations.md` (`## DW-O26` 節、
   470 bytes) を直接編集。
6. **段6 敵対レビュー2本**: レンズA (consumer 網羅・採番衝突・順序検査・typed-edge 閉包・親の
   圧縮編集) は追加所見なし。レンズB (テスト網羅性) が、親が既に見つけていた2件に加え
   3件目の real (同型の改行欠落バグが `test_dev_wave_operation_order_rejects_...` にも
   潜在するが弱い assertion で隠れている) を発見 (`verbatim/s6-lensA.md`,
   `verbatim/s6-lensB.md`)。**launcher の dirty-tree preflight
   (`docs/dev-wave/{operations,workers}.md` が HEAD と異なると codex dispatch 全体が rc=2)
   に実際に抵触し、operations.md を一時的に HEAD へ退避 → レビュー/fix 投入 → 復元、という
   運用で回避した (T-1362 handoff に記載済みの既知の罠を実地で踏んだ)。**
7. **段6 fix (Codex author)**: 3件とも修正確定 (`verbatim/s6-fix.md`)。親が実測で
   472 passed, 3 skipped, 0 failed を確認 (codex 子はいずれも Pegasus dispatch 不調
   (`qstat -Q` rc=1 等) で pytest 実走不能だったため、親の実測が必須だった)。
8. **変異事前登録・本走 (段4 相当、手動)**: `mutation-ledger.md` 参照。baseline PASSED・
   4/4 KILLED・SURVIVED 0・MISMATCH 0。M1〜M3 は本ファイル特有の shared-fixture cascade
   (273〜274件) を伴う冗長gateとして記録し、単独理由の証拠は直接等価 assert 1件へ帰属させた。
9. **自己適用**: 今回の T-1361 義務そのものを自 wave の焦点走選定へ適用した。変更した
   production file (`tools/check_docs.py`) を参照する consumer test を `grep -rl` で
   洗い出し、`orchestrator/tests/test_check_docs.py` 以外 (`test_dev_wave_land.py`,
   `test_hooks.py`, `test_dev_waves_checker.py`, `test_dev_waves_integration.py`,
   `test_dev_waves_git_state.py`, `test_spool_fold.py`) はいずれも check_docs.py を
   synthetic stub へ置換するか無関係な定数 (`WORKLOG_ROTATE_BYTES` 等) を参照するだけで、
   今回変更した symbol (`REQUIRED_REFERENCE_SECTIONS` 等) を実際に exercise していないと
   確認し、焦点走の対象を `test_check_docs.py` に確定した。

## 副次的な発見 (今回の scope 外、記録のみ)

- `docs/handoff/2026-08-19-t1362-reasoning-pin.md` が「段9で停止・ユーザー裁定待ち」と
  記載したまま残存しているが、T-1362 は commit `0333abe6` で main へ既に着地済みと確認した
  (`git log --oneline -- tools/dev_waves/launch_authority.py`、および本 wave 内で
  `--stage author` に `--reasoning` を渡すと機械的に rc=2 で拒否される実測)。**land の
  handoff 保護ガードにより本 wave からは削除できない** (削除を含む tip は rc=21)。
  ユーザーへ別途報告。
