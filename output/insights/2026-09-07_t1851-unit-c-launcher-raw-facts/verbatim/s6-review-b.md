[実測] 判定は **NO-GO**。production 実装には blocker を確認しなかったが、受入条件である test の実効性と変異の単一理由性に must-fix が 5 件ある。

## blocker

[実測] blocker は 0 件。

## must-fix

### 所見 1 — 既存 capture 引数の期待値が弱体化している

- (a) [実測] 旧 test の exact kwargs 比較が key 集合だけの比較へ緩和され、`extime`、`reps`、`use_perf` の値を検査しなくなった。これは「既存期待値を緩めない」に反する。
- (b) [実測] 差分は [s5-launcher.patch:615](/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-unit-c/s5-launcher.patch:615)、現物は [test_s8b_floor_attempt_launcher.py:351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:351)。
- (c) [推測] 放置時は launcher が検査後に capture 値を置換する回帰が緑となり、実測回数や perf 使用条件が変わって session 値、除外集合、certified 選択が変わりうる。
- (d) [推測] 所有 file `orchestrator/tests/test_s8b_floor_attempt_launcher.py` で、4 key の exact 集合に加え既存 3 値の exact equality と私有 sink の identity/type を個別に検査する。

### 所見 2 — fake が私有 sink と公開 `rep_observations` を同一 object にしている

- (a) [実測] `_bind_sink` は launcher が渡した list をそのまま `_Token.rep_observations` に代入する。一方、実体は私有 sink を更新後、`ScalePoint.rep_observations` へ別 list をコピーする。この乖離により、launcher が私有 sink でなく公開 measurement attribute を読んでも test が緑になる。
- (b) [実測] fake は [test_s8b_floor_attempt_launcher.py:179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:179) と [同:263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:263)。実体は [runner.py:938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/calibrator/runner.py:938) と [同:1046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/calibrator/runner.py:1046)。
- (c) [推測] 放置時は C1b で caller-facing の可変 view が raw repetition facts として封印され、E2 reason、レポートの rep 証跡、certified 受理集合が変わりうる。
- (d) [推測] 所有 test file で注入 sink を私有 field に保持し、`open()` 時に実体同形の 6-key rep record で更新する。公開 `rep_observations` は別コピーまたは意図的に異なる値とし、launcher の snapshot が注入 sink 由来であることを検査する。

### 所見 3 — real adapter node が新しい reserve signature を通っていない

- (a) [実測] `test_real_adapter_creates_and_exactly_reuses_complete_genesis` は reservation に v1 profile と marker `None` を載せたが、呼ぶのは `_ensure_registry_genesis` だけである。`_reserve`、classification、observation、terminal は通らない。marker forwarding node も `_RecorderRegistry` の `**kwargs` だけを使うため、両層 stub の緑が残る。
- (b) [実測] [test_s8b_floor_attempt_launcher.py:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:584)、[同:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:652)、[同:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:898)。実 adapter signature は [s8b_attempt_registry.py:1888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1888)。
- (c) [推測] launcherとadapterの引数・phase-handle契約が乖離した場合、production terminal row が 0 件となり、attempt registry参照とcertified coverageが欠落する。
- (d) [推測] 所有 test file の real adapter node を、v1 profile + marker `None` で少なくとも `_reserve`、できれば terminal まで通す integration 正例へ拡張する。adapter 本体は変更不要。

### 所見 4 — authority node が public API の forwarding を観測していない

- (a) [実測] node は public signature を検査する一方、recorder を通す呼出しは `_launch_floor_attempt_for_test` である。したがって public `launch_floor_attempt` の forwarding を別 authority に変える変異は生存する。
- (b) [実測] [test_s8b_floor_attempt_launcher.py:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:829)、内部 helper 呼出しは [同:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:841)、検査対象の public forwarding は [s8b_floor_attempt_launcher.py:832](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:832) と [同:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:849)。
- (c) [推測] 放置時は public launcher が別 authority ID/digest を台帳へ書いても緑となり、classification receipt の参照と受理 authority が変わる。
- (d) [推測] 所有 test file で production dependencies と固定 probe を差し替え、public `launch_floor_attempt` を実際に呼んで recorder の authority ID/digest を検査する。

### 所見 5 — M5 の負例が protocol digest 以外の gate も壊している

- (a) [実測] M5 node は protocol の `reps` を 3 から 4 へ変えるため、digest gate を外しても後続の capture reps equality gate が拒否する。node は error message mismatch で赤になるが、digest 束縛を外した入力が受理されたことによる赤ではない。
- (b) [実測] 入力は [test_s8b_floor_attempt_launcher.py:867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_s8b_floor_attempt_launcher.py:867)。digest gate は [s8b_floor_attempt_launcher.py:540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:540)、冗長 gate は [同:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:573)。
- (c) [推測] scientific artifact は直ちに変わらないが、mutation ledger が digest 束縛を単独で証明したと誤認し、受入根拠が不正確になる。
- (d) [推測] 所有 test file で `reps` を 3 のまま保ち、digest だけを変える無関係 field を変更する。

## nit

[実測] nit は 0 件。

## 変異 M1〜M12 の帰属

[実測] 全指定 node は存在する。判定は静的反実仮想による。

| 変異 | 判定 | 根拠 |
|---|---|---|
| M1 | KILLED が期待できる | capture callable 自体が `pytest.fail`。pre競合以外は valid |
| M2 | KILLED が期待できる | open 前の sink は空、open 後だけ3件。ただし公開 attr から読む別変異は所見2により生存 |
| M3 | KILLED が期待できる | gate 除去後は genesis/reserve を経て `post_probe=pytest.fail` に到達 |
| M4 | KILLED が期待できる | 登録どおり public 引数を復活させる変異は signature assertion が殺す。ただし forwarding 単独変異は所見4 |
| M5 | 冗長 gate に遮られる | digest gate 除去後も reps gate が拒否。node は message mismatch で赤 |
| M6 | KILLED が期待できる | unavailable receipt と `use_perf=True` の不一致だけを直接 helper で検査 |
| M7 | KILLED が期待できる | preのみ競合、post非競合、failures空の直接 helper 検査 |
| M8 | KILLED が期待できる | preだけ変更した digest pair が同値となり `len(set)==3` が赤 |
| M9 | KILLED が期待できる | extra-key caseが最初にあり、緩和すると `pytest.raises` が赤 |
| M10 | KILLED が期待できる | OSError伝播なら terminal resultと後続eventへ到達しない |
| M11 | KILLED が期待できる | protocol/binding/use_perfはvalidで、capture repsだけ不一致 |
| M12 | KILLED が期待できる | fakeはraise前にsinkを埋め、誤snapshotなら空tuple assertionが赤 |

追加 5 node は、mode負例、official+available負例、marker forwarding は対象 gateへ直接到達する。[実測] protocol callableとreceipt callableは、callable gateを外しても後続canonical/receipt validatorが拒否し、message mismatchで赤となるため単一理由ではない。

## 所有外への波及

- [実測] `s8b_attempt_registry.py` から launcher への runtime import はなく、docstring参照だけである。[s8b_attempt_registry.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2)
- [実測] launcher は adapter module を [s8b_floor_attempt_launcher.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:23) で importする。
- [実測] `launch_floor_attempt`、`FloorAttemptReservation`、`OpenedFloorAttempt.post_probe/open_error`、public `classification_authority` の所有外 caller/test参照は 0 件。launcher module を importするのは所有 test fileだけである。
- [実測] `test_ccbench_spawn_sites.py:212` の pin は1のままで、`subprocess.run` のAST上のspawn siteも `_owned_post_probe` 1箇所のまま。[test_ccbench_spawn_sites.py:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/tests/test_ccbench_spawn_sites.py:212)
- [実測] `_reserve` は `consumption_marker` を明示転送する。[s8b_floor_attempt_launcher.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:601)
- [実測] adapter の型は `FloorAttemptConsumptionMarker | None`、reservation carrier は親契約どおり `object | None`。[s8b_attempt_registry.py:1904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1904)

## 到達可能性 matrix

| 条件 | production 固定依存経路 | launcher自身の強制 |
|---|---|---|
| `probe_after=None` iff pre競合 | [実測] 成立 | [実測] 分岐構造で成立 |
| pre競合時に failure null、launch空、measurement null、sink空 | [実測] 成立 | [実測] 成立 |
| opened時にsink長=`reps` | [実測] real runnerはopen冒頭でreps件を作るため成立 | [実測] launcherは長さを検査しない |
| failure時にmeasurement None | [実測] capture/open failureとも成立 | [実測] 成立 |

[実測] production固定依存で不成立の組合せは確認しなかった。[推測] `_launch_floor_attempt_for_test` では「open成功だがsink長が0またはreps不一致」「openがNoneを返しfailureもNone」「任意objectをmeasurementとして返す」が `OpenedFloorAttempt` に載りうる。また dataclass の直接構築でも任意組合せを作れる。C1b validatorでの拒否対象である。

## 規模と focus 集合

- [実測] production は `+220/-35`。上限 `+150〜220/-40以内` に適合するが追加行は上限ちょうど。
- [実測] test は `+400/-37`。追加上限 `+250〜400` に適合するが上限ちょうど。
- [実測] 変更は所有2 fileだけで、`git diff --check` は静的に問題なし。
- [実測] 所有外の波及候補は `test_ccbench_spawn_sites.py::test_reviewed_ccbench_measurement_launches_use_bounded_sites` と `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`。現差分ではpinと`__main__`が維持されるため静的には緑。
- [実測] 両 file はbaseline 38 fileに含まれる。baseline外で赤になりうる所有外testは確認しなかった。

## 実装子報告との照合

- [実測] `+220/-35`、`+400/-37`、新設17 node、総29 node、変更2 file、production caller 0 は現物と一致する。
- [実測] pytestと自走harnessが未実走という申告も報告内で明記されており一致する。
- [実測] 「29 direct-call passed」「meta 4 passed」「py_compile/checker passed」は提示資料に実行logがなく、今回の静的レビューでは追認不能だが、現物との直接矛盾は確認できない。
- [実測] 「fake tokenをScalePoint同形へ更新」は指定3 attributeの存在だけなら一致するが、sink aliasとrep record形は実体と異なるため、実契約まで同形という主張は所見2のとおり不成立。
- [実測] 行数、node数、pytest未実走範囲について、上記以外の食い違いはない。

## 総括

- [実測] blocker 0件 / must-fix 5件 / nit 0件。
- [実測] production `+220/-35`、test `+400/-37`。双方とも追加上限ちょうど。
- [実測] production固定経路の到達可能性matrixは成立。
- [実測] M1〜M4、M6〜M12は指定変異をKILL見込み。M5は冗長gate依存。
- [実測] 所有外public consumerは0件。focus外の予想赤も0件。
- [実測] pytest/self-run harnessは未実走。
- [推測] testの境界証明と単一理由性を直すまで **NO-GO**。