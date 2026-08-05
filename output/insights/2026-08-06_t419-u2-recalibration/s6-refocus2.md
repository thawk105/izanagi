## 対応表

| ID | 判定 | 根拠 file:line |
|---|---|---|
| NR-01 | `closed` | SHA-256 は [cli.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:490) で全 `profile` を対象にし、その同じ値を [cli.py:496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:496) に保存する。canonicalization 識別子 [cli.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:79) は実装 [cli.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:439) と一致し、テストも production 定数ではなく literal を使う（[test_calibrator_certify.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:692)）。 |
| NR-02 | `regressed` | 既存 file/symlink との `O_EXCL` 衝突時に消さない点は閉じた。しかし inode 検査が `stat(path)` [cli.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:323) と `unlink(path)` [cli.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:332) に分離した TOCTOU であり、正常 return 後も caller が持つのは inode でなく bool [cli.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:838) だけである。さらにこの危険な cleanup を共有 helper の全 caller へ新規拡大した。 |
| NR-03 | `closed` | shape、policy、値取得が一つの `try` 内で一度だけ評価される（[execution_guard.py:226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:226)）。public は policy 不一致で band 前に短絡し（[execution_guard.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:246)）、先頭帯外で走査を止める（[execution_guard.py:273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/execution_guard.py:273)）。custom Mapping の `keys` / `__contains__` / `get` 例外も `False`＋構造化 error になる（[test_execution_guard.py:726](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_execution_guard.py:726)）。 |

## 新規所見

| ID | 根拠 file:line | real / speculative | 成果物影響 | 区分 |
|---|---|---|---|---|
| R2-01（NR-02 再回帰） | [cli.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:323)、[cli.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:332)、[cli.py:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:841)、[cli.py:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:859) | real | `stat` 後の差替えで他者 inode を削除でき、正常書込み中の差替えでは意図した digest 名へ別 bytes を publish できる。 | must-fix |
| R2-02 | [cli.py:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:305)、[test_calibrator_certify.py:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:804)、[snapshot-fix1.patch:709](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/snapshot-fix1.patch:709) | real | 現 fixture は全 write 後の `fsync` を失敗させるため、名前に反して partial/short write 経路を固定していない。現成果物への直接影響はないが回帰検出穴が残る。 | nit |

**must-fix は 1 件。**

### G-1 の反証

作成前から存在する file/symlink は、`os.open(...O_EXCL)` が [cli.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:301) で `try` より前に失敗し、`temporary_owned` も `False` のままなので削除されない。追加テストも file と symlink を個別に固定している（[test_calibrator_certify.py:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/tests/test_calibrator_certify.py:850)）。

しかし次の実行順序で破れる。

1. P が `O_EXCL` で inode A を作成し、`fstat` する。
2. I/O 失敗後、P の `stat(path)` が A を確認する。
3. Q が path を inode B へ差し替える。
4. P の `unlink(path)` が B を削除する。

さらに正常書込み中に Q が path を B へ差し替えると、helper は A の fd を fsync して正常 return する。caller は path の inode を再確認せず [cli.py:854](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:854) で B を target へ rename する。target 名は A の SHA-256 から作られる一方（[cli.py:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:833)）、後段検査は B の SHA を記録するだけで期待 digest と比較せず、clock しか検査しない（[cli.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:535)、[cli.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:556)）。self-pass な B なら誤った content-addressed publish が成功する。

`fstat` 自体が失敗して `created_stat is None` の場合も、条件 [cli.py:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:324) が ownership 不明を拒否せず `else: unlink` へ流す。

unlink 失敗は helper 内で握り潰されず wrapper 化され（[cli.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:337)）、publish caller では構造化拒否になる（[cli.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:867)）。ただし link-unlink fallback の unlink 失敗後に caller が再び unlink する経路は残り（[cli.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:373)、[cli.py:861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:861)）、同じ差替え問題を持つ。

### `_write_exclusive` の全 caller

| caller | 成果物 | 固有の波及 |
|---|---|---|
| [cli.py:657](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:657) | `rejection.json` | 書込み失敗時の path-based cleanup を共有 |
| [cli.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:817) | `candidate.json` / rejected `calibration.json` | outer handler も candidate を ownership 検査なしで削除する（[cli.py:909](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:909)） |
| [cli.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:822) | `calibration.md` | 共有 cleanup |
| [cli.py:823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:823) | `window-probes.json` | 共有 cleanup |
| [cli.py:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:841) | publish temp | bool ownership、差替え削除・差替え publish |
| [cli.py:874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:874) | `published-self-comparison.json` | publish 後 sidecar の置換・削除 |
| [cli.py:885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:885) | `publish.json` | publish 成功後 receipt の置換・削除 |
| [cli.py:923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:923) | fallback `calibration.json` | 共有 cleanup。再拒否 receipt 自体が失敗すると stderr のみ |

非競合経路では、正常 publish 後に temp が残る反例、または通常の fsync 失敗後に temp が残る反例は得られなかった。だが競合時の所有保証は反証済みである。

### G-2

保存 profile は hash 対象と同じ引数であり、部分集合ではない。呼出し側も判定に渡した同じ `profile` を診断生成へ渡す（[cli.py:757](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:757)、[cli.py:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:764)）。

識別子は `sort_keys=True`、compact separators、`ensure_ascii=True`、UTF-8 を正確に表し、production helper から自動生成されていない。テスト側も literal と成果物内 profile だけから再計算する。

保存対象の exact schema は CPU/core/cache/NUMA/TSC/effective-clock/visibility のみで、timestamp、path、nonce、submit epoch は含まない（[schema_v2.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:548)）。ただし list・文字列長に明示的上限がないため（[schema_v2.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/schema_v2.py:94)）、人工的な巨大 profile に対する絶対的サイズ上限は反証できなかった。現 production probe で巨大化する具体例は得られていない。

### G-3 境界入力

静的制御フローを元 HEAD、fix1 snapshot、現在版で比較した結果は以下。

| 入力 | 元 HEAD | fix1 | fix2 |
|---|---:|---:|---:|
| 非 Mapping／missing・extra key | `False` | `False` | `False` |
| 非 policy tolerance＋巨大 sample | `False`、band 未評価 | 同左 | 同左 |
| policy 2.0、上下境界の等号 | `True` | `True` | `True` |
| 1 ULP 帯外、NaN、空列、非変換値 | `False` | `False` | `False` |
| 帯内 numeric string、bool、int、長さ不一致 | `True` | `True` | `True` |
| 先頭帯外＋後続巨大 int | `False`、後続未評価 | 同左 | 同左 |
| policy 2.0＋巨大 median | `OverflowError` | `OverflowError` | `OverflowError` |
| custom Mapping の shape/get 例外 | 漏出または未発火 | 漏出経路あり | `False`＋構造化 error |

最後の行だけが意図した変更である。owned production caller は CLI の literal dict（[cli.py:453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/calibrator/cli.py:453)）と silo の検証済み profile から作る literal dict（[silo_ladder_rung1.py:1967](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-u2-recalibration/orchestrator/campaign/silo_ladder_rung1.py:1967)）であり、戻り値回帰は見つからない。

### 既存テストの変更

snapshot-fix1→現在差分で、既存の `assert`、`skip`、`xfail`、`parametrize` の削除・変更は **0件**。追加は assertion 12 件で、1巡目に許可された4 nodeも変更されていない。

変更された既存 fixture は temp failure 2本だけで、assertion は維持されている。ただし現在の fixture は全 `os.write` 完了後の fsync を落とすため、旧 fixture が実際に作っていた partial file（[snapshot-fix1.patch:713](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/snapshot-fix1.patch:713)）とは検査対象が異なる。これは R2-02 の nit とした。

追記4の sidecar inventory と mutation 再登録は現コードと一致し、NR-04/NR-05を再度開く反例は得られなかった（[s4-adjudication.md:215](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t419-u2-recalibration/s4-adjudication.md:215)）。

## GO / NO-GO

**NO-GO**

NR-01 と NR-03 は閉じたが、NR-02 は shared cleanup への TOCTOU 拡大と差替え publish を導入したため `regressed`。must-fix 1件が残る。

親実測の **667 passed / 2 skipped / 0 failed** は所与として扱うが、追加テストは作成前衝突と非競合 fsync failure しか踏まず、作成後の inode 差替えを扱わない。私は pytest を実走しておらず、緑は主張しない。

## 総括

- NR-01 は全 hash preimage と一致する canonicalization 識別子が成果物内に揃い、closed。
- NR-03 は shape→policy→band の短絡と custom Mapping 例外集約が成立し、closed。
- NR-02 は作成前衝突だけ閉じたが、path-based cleanup を全 caller へ広げて regressed。
- inode 差替えで他者削除または誤 content-addressed publish が可能な must-fix が1件残る。
- 既存 assertion の緩和・削除は0件。partial-write fixture の検査ずれは nit。
- pytest は実走せず、親の 667 passed / 2 skipped を私自身の緑とはしない。
- 以上により **NO-GO**。