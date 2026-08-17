## 所見

### R1. 本来の cross-mode 重複読取を復活させる変異が 4 node を全通過する

**主張:** `newline=""` から `newline=None` への cache 共有だけを削除する変異は、新設 4 node を壊さない。物理読取の重複だけが復活する。

**根拠:** cross-mode 共有の本体は `tools/check_docs.py:914-931`。物理 open node は同じ既定 mode を 2 回読むだけ (`orchestrator/tests/test_check_docs.py:3987-3998`)。newline node は raw → normalized の値だけを検査し、open 数を検査しない (`:4009-4029`)。従って `:914-931` を無効化しても、2 回目を再 open すれば期待本文は得られ、全 node が通る。親自身、本来の比例源を異なる newline mode 間の重複と特定している (`parent-verification.md:23-24`)。

**帰結:** wave が除去した 468 件規模の重複 open/decodeを、既定テストに検出されず復活させられる。受入 wall の corpus 比例係数が再増加する。

**深刻度:** `must-fix`

### R2. identity は access-state の変化を見逃し、旧版だけが赤になる入力がある

**主張:** `(mtime_ns, size, ino, dev)` は内容差し替え以外にも不足する。初回読取後に `chmod` や ACL で読取権限を剥奪した場合、4 値は一致しうる。

**根拠:** 2 回目も `lstat()` は行うが、regular bit しか検査しない (`tools/check_docs.py:885-891`)。identity に `st_mode` と `st_ctime_ns` は含まれず (`:902-907`)、一致すれば open せず本文を返す (`:910-940`)。旧版は再 open して `PermissionError` を finding にする。親が記録した残差は「4 値一致のまま本文が変わる」場合だけである (`parent-verification.md:67-68`)。

**帰結:** 実行中に読取不能となった文書を旧版は拒否するが、新版は cached text で後続検査を続け、land gate の受理集合を広げる。

**深刻度:** `must-fix`

### R3. identity node は過剰決定で、4 field の照合を防御していない

**主張:** 現 fixture は size・inode・mtimeを同時に変えるため、identity の一部しか見ない実装でも通る。

**根拠:** `"old\n"` を `"replacement content\n"` の別 file で置換している (`orchestrator/tests/test_check_docs.py:4057-4069`)。例えば identity を実質 `st_size` だけに弱めてもこの fixture は再読取される。一方、同じ size と mtime を持つ別 inodeへの置換は stale になる。M-E は identity 照合を丸ごと消しただけであり、各 field の脱落を攻撃していない (`parent-verification.md:94-98`)。これは過剰決定 fixture を単独変異の証拠から外す `DW-M03` とも不整合 (`docs/dev-wave/mutation.md:16-20`)。

**帰結:** B-R1 の回帰防壁は存在するが、identity contract の弱体化を検出できない。

**深刻度:** `must-fix`

### R4. 「変異 5/5 KILLED」は段 6 の受入証拠として成立していない

**主張:** 変異結果は専用 harness 契約を経ていない。

**根拠:** `DW-M05` は `tools/mutation_harness.py`、固定 HEAD、内容比較、`flock`、signal 復元を要求する (`docs/dev-wave/mutation.md:28-35`)。使用された `mutate.py` は source の置換と `git checkout --` だけで、test 実行・rc・失敗 node の記録も持たない (`mutate.py:50-88`)。親文書もこの独自 script を本走根拠にしている (`parent-verification.md:87-103`)。

**帰結:** 5 件が手動走行で赤になった事実はありえても、最終 acceptance-grade の mutation matrix とは扱えない。標準 harness での再走が必要。

**深刻度:** `must-fix`

### R5. post-fix の 457 passed は必読証拠と食い違う

**主張:** 指示には `457 passed / 3 skipped` とあるが、「親の全実測」と指定された文書には記録がない。

**根拠:** `parent-verification.md:107-111` が記録する焦点走は `1122d724` 時点の `453 passed / 3 skipped` であり、`7b40d111` での再走は「後段で再実施する」と明記されている。

**帰結:** 実走自体を否定しないが、post-fix consumer 走行を監査可能な証拠へ反映するまでは最終受入根拠が欠ける。

**深刻度:** `must-fix`

## 前巡所見の対応表

| 前巡所見 | 判定 | 理由 |
|---|---|---|
| cache の正しさを守る既定走行 node が無い | **partial** | 4 node は追加されたが、R1 の cross-mode cache 無効化が生存する。 |
| identity 照合が無い | **partial** | 実装は追加されたが、R2 の access-state 漏れと R3 の過剰決定 fixture が残る。 |

## refuted

- 新設 4 node が成長比例という疑いは refuted。すべて `tmp_path` を使い、`REPO` と `_main` を monkeypatch して実 corpus への到達を遮断している (`orchestrator/tests/test_check_docs.py:3970-4076`)。
- `_ReadTextCacheEntry` の field 追加による consumer 破損は見つからない。constructor は `tools/check_docs.py` 内だけにあり、全箇所が identity を渡している。
- 既存テストの削除・skip・hold 追加は差分にない。追加 node 名も `GROWTH_TEST_HOLDS` に存在しない。
- raw stdout は提示された故障注入 fixtureについて実際に byte 一致している。ただし全受理集合の同一性証明ではない。
- pytest はこのレビューでは実走していない。親の数値をこのレビュー自身の緑とは扱わない。

## 総括

**NO-GO**

cross-mode growth leak を復活させる生存変異、旧版だけが拒否する access-state 変化、identity fixture の過剰決定が残る。加えて mutation matrix と post-fix 焦点走の証拠を受入契約どおり整える必要がある。