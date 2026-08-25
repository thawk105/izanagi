静的レビューのみ。Web、pytest、live qsub は実行しておらず、非実走を緑とは扱わない。

## 1. 裁定どおりの bundled argv は attempt sidecar で必ず停止する

- **所見**: inner-local と裁定必須の attempt sidecar がコード上で両立せず、完全な bundled 経路を通る argv は存在しない。
- **なぜ real か**: 裁定は bundled 文脈で `--attempt-out` を許すとしている (`s4-adjudication.md:93-100`)。しかし wrapper と harness は local と attempt pair の同時指定を無条件拒否する (`tools/mutation_worktree.py:1152-1161`, `tools/mutation_harness.py:2949-2956`)。正例テストは attempt pair、`--scratch-root`、spec hash、`--detached` を欠き、scheduler stub が実子を起動しない (`orchestrator/tests/test_pegasus_dispatch_compute.py:4391-4415`)。
- **壊れ方**: 実在 argv を bundled 用に `--runner-mode local` へ変え、`--force-dispatch` を除き、`--attempt-out ... --wrapper-attempt 1` を残す → dispatcher policy は通る → qsub 後に wrapper が rc=125 で停止する。attempt pair を落とせば実行自体は可能だが、裁定した attempt 対応証拠を失う。
- **重大度**: 正しさ防壁 / 実効性
- **成果物影響**: pair を残すと mutation ledger が生成されず、落とすと attempt 対応を備えた恒久 transport という成果物値にならない。単なる「1 job で動いた」dogfood では D131 #2 を証明できない。
- **提案**: task 内部からだけ設定される bundled marker を設け、compute site と marker の双方が真の場合に限り local attempt recorder を許す。同時に wrapper まで到達する end-to-end 正例を追加する。

現コードで動作だけを狙う argv は次の形で、これは policy を通る。ただし attempt 証拠を欠く。

```text
python3 tools/pegasus/dispatch_compute.py --walltime <十分な値> --task mutation -- \
  --source-repo ... --commit <sha> --scratch-root ... --spec ... \
  --expected-spec-sha256 ... --out ... \
  --runner-mode local --detached -- \
  python3 tools/run_tests.py <tracked test file...> -q -rf
```

## 2. mutation policy は bundled-local の構造を強制していない

- **所見**: policy は禁止 token の走査だけで、`--runner-mode local`、wrapper 必須引数、runner tail の構造を検証しない。
- **なぜ real か**: validator は全 token に対する blacklist だけである (`tools/pegasus/dispatch_compute.py:745-778`)。親側も同じ関数を呼ぶだけである (`tools/pegasus/dispatch_compute.py:2582-2595`)。
- **壊れ方**: `--runner-mode dispatch` かつ `--force-dispatch` なしの argv → policy と qsub は通る → collection が compute から nested `dispatch_compute --task tests` を起動し (`tools/mutation_harness.py:1389-1403`)、その後の baseline も dispatch receipt を得られず停止する。必須 wrapper 引数が欠けた正例テストも同様に qsub 後しか失敗しない。
- **重大度**: 受理集合 / 実効性
- **成果物影響**: 「mutation task が受理した」は「束ねた走行が開始できる」を意味しない。誤入力で最低 1 job、場合により nested submission を消費し、ledger は得られない。
- **提案**: wrapper argv を構造的に parse し、mutation task では local、detached、必要な path/hash、同一 Python と `tools/run_tests.py` を親と `_job_run` の双方で強制する。

## 3. D131 #1 は direct harness が残る限り閉じていない

- **所見**: wrapper の共有 `<out>.lock` は wrapper 同士しか直列化せず、direct harness は引き続き node-local `/tmp` lock を使う。
- **なぜ real か**: 親裁定は wrapper lock で #1 を閉じる一方、direct harness を許可する (`s4-adjudication.md:72-76`)。wrapper は `<out>.lock` を取る (`tools/mutation_worktree.py:192-217`) が、harness は `tempfile.gettempdir()` 配下を使う (`tools/mutation_harness.py:2869-2889`)。
- **壊れ方**: 同じ共有 checkout を pegasus01 と pegasus02 から direct harness dispatch mode で起動する、または wrapper 内 harness と別 node の direct harness を同じ checkout に向ける → 各 node の `/tmp` flock は独立 → 同じ source を同時変異できる。
- **重大度**: 正しさ防壁
- **成果物影響**: baseline、失敗 node、KILLED/SURVIVED、復元結果が別走行と混ざり、mutation ledger の判定値自体が不正になり得る。
- **提案**: direct harness も共有 filesystem 上の canonical repo identity lock へ移行し、legacy `/tmp` holder との移行窓を閉じる。禁止しない裁定を維持するなら、この移行が必須である。

## 4. D131 #2 の永続 transport 証拠は bundled-local で切れる

- **所見**: bundled-local の ledger は inner receipt path を null にし、outer dispatch 証拠は既定で gitignore 下に残るだけで、両者の永続的な相互束縛がない。
- **なぜ real か**: local artifact は receipt/job stdout path を null とする (`tools/mutation_harness.py:1310-1343`)。CLI は split artifact root を公開せず (`tools/pegasus/dispatch_compute.py:3688-3741`)、既定 root は `output/pegasus-dispatch` (`tools/pegasus/dispatch_compute.py:2619-2624`) で gitignore 対象 (`.gitignore:26`)。wrapper receipt に outer request ID、outer receipt hash、ledger hashはない (`tools/mutation_worktree.py:1017-1037`)。
- **壊れ方**: bundled run 完了後に ignored dispatch directoryが掃除される → ledger と wrapper receipt は残るが、「どの PBS request の 1 job がこの collection/baseline/N 変異を生成したか」を再検証できない。
- **重大度**: 正しさ防壁
- **成果物影響**: queue 削減値と mutation 判定値を scheduler receipt、job stdout、accounting へ結べず、凍結成果物としての transport 証拠が欠ける。
- **提案**: mutation CLI で外部 artifact root を指定可能にし、outer receipt SHA/request IDを wrapper receipt と ledger に、ledger SHAを outer側成果物に結ぶ。

## 5. D131 #4 の argv 防壁は `-o addopts=...` で迂回できる

- **所見**: selector と任意 plugin の blacklist は pytest ini override を閉じておらず、tracked test file も task policy 自体では検査していない。
- **なぜ real か**: dispatcher が拒否するのは直接の `-k/-m/-p` 等だけ (`tools/pegasus/dispatch_compute.py:761-778`)。harness は `-o` の値を意味解析せず丸ごと飛ばす (`tools/mutation_harness.py:874-895`)。tracked 検査は qsub 後の harness で初めて行う (`tools/mutation_harness.py:899-912`)。
- **壊れ方**: runner tail に `-o "addopts=-k selected"` または `--override-ini=addopts=-p foreign_plugin` を入れる → task policy を通過 → selectorまたは plugin が pytest に再注入される。存在しない test path も qsub 前は受理される。
- **重大度**: 正しさ防壁 / 受理集合
- **成果物影響**: 実行 node 集合が事前登録した対象から変わり、KILLED/SURVIVED の値が別 suite に基づく可能性がある。不存在 path では job だけを消費する。
- **提案**: blacklist ではなく closed allowlist にする。少なくとも `-o/--override-ini/-c/--rootdir` 等の設定変更面を拒否し、tracked 通常 test file を親と `_job_run` でも検証する。

## 6. check_docs の TASKS alias 防壁にはまだ単純な迂回がある

- **所見**: container unpack は閉じたが、`for` 束縛や helper return で TASKS alias を作ると runtime enum を増やしても drift 検査を通る。
- **なぜ real か**: alias 判定は assignment、function default、call argument にしか `preserves_tasks_alias` を適用しない (`tools/check_docs.py:3400-3449`)。`ast.For` と `Return` は対象外で、inventory は元の literal `child_script` だけを抽出する (`tools/check_docs.py:3520-3561`)。
- **壊れ方**: 次を TASKS 定義後に追加する → `alias` の subscript write は TASKS を直接含まない → checker は元の4 taskだけを抽出 → runtime では `extra` task が親、CLI、`_job_run` の閉集合に入る。

```python
for alias in (TASKS,):
    alias["extra"] = _TaskSpec(...)
```

- **重大度**: 正しさ防壁
- **成果物影響**: runbook inventoryが4 taskのままでも実行時受理集合は5 taskになり、閉集合の成果物値が偽になる。
- **提案**: TASKS の定義外 load を原則拒否し、許可する読み取り形だけを列挙する。少なくとも `For/AsyncFor`、return/closure、match capture の負例を追加する。

## 7. 親の実測は「対象 file」については支持されるが、selector-free への一般化は破れる

- **所見**: frozen ledger に full-suite 反例は見つからない一方、実在する本走には新 policy が拒否する selector、nodeid、`--deselect` が複数存在する。
- **なぜ real か**: `-k` の実在例は `output/insights/2026-08-25_t1263-certification-scope/mutation-result.json:585-597`、nodeid は `output/insights/2026-08-20_t1356-sort-closed-region-wiring/mutation-result-m1.json:136-144`、`--deselect` は `output/insights/2026-08-20_t1421-c06-machine-checkable-promotion/mutation/mutation-out.json:970-985`。
- **壊れ方**: runner 経路を変異しないが `-k` や nodeid を必要とする既存 matrixを bundled 化する → `mutation` policy が qsub 前に拒否 → legacy dispatch の N+2 job のまま残る。
- **重大度**: 実効性 / 受理集合
- **成果物影響**: queue 削減の適用集合は「runner path を含まない変異」よりさらに狭く、「かつ selector-free」である。これを数えないと削減率を過大表示する。
- **提案**: frozen ledger群から bundled-eligible 集合を機械集計し、成果物には eligible 件数と非対象理由を記録する。selectorを広げるかは裁定へ返す。

## 8. generic は実装上動くが、D895 の「任意 argv」は guarded 経路では未充足

- **所見**: hook scope 外化により `python -m pytest` は valid generic argv でも通常の guarded login 経路から呼べない。
- **なぜ real か**: amendment 自身が拒否を認める (`s4-adjudication-amendment.md:14-16`)。hook は sanctioned 判定より先に argv 全域の `-m pytest` を拒否する (`hooks/guard_bash.py:1155-1175`, `hooks/guard_bash.py:1212-1229`)。runbook も同じ制限を明記する (`docs/pegasus-runbook.md:586-589`)。
- **壊れ方**: `dispatch_compute.py --task generic -- python3 -m pytest -q` → dispatcherへ届く前に hook 拒否。一方 `-- pytest -q` は通るため、綴り依存の受理集合になる。
- **重大度**: 受理集合
- **成果物影響**: D895 の値は「任意コマンド task 完成」ではなく「dispatcher実装済み、guarded clientでは一部 argv 未到達」となる。
- **提案**: 本 wave を partial と記録し、hook 正規変更 waveへ裁定を返す。mutation の実在 `python tools/run_tests.py` 形にはこの hook 欠陥は必須 blocker ではない。

## 9. 束ね効果の静的計数

- **所見**: eligible な fresh runを正しく inner-local で起動できれば、qsub は N+2 回から1回へ実際に減る。
- **なぜ real か**: collection は dispatch modeで1回の tests taskを作る (`tools/mutation_harness.py:1389-1403`)。baseline は `_run_tests` 1回 (`tools/mutation_harness.py:2008-2040`)、各変異も1回 (`tools/mutation_harness.py:2153-2164`)。outer task の qsub は1回 (`tools/pegasus/dispatch_compute.py:3002-3015`)。compute上の run_tests はlocalへ進む (`tools/run_tests.py:2620-2640`)。
- **壊れ方**: runner pathを含む、selectorが必要、または上記 attempt契約を要求する入力では bundled-local を選べず、この削減は得られない。
- **重大度**: 実効性
- **成果物影響**: eligible な N 変異について削減値は `N+1` 回。無条件の全 matrix 削減値ではない。
- **提案**: dogfoodでは outer receiptから qsub exactly one、ledgerから collection/baseline/N完了、attempt対応を同時に証明する。

fresh、pending mutation=N の静的計数は次のとおり。

| 経路 | outer | collection | baseline | 変異 N 件 | 合計 |
|---|---:|---:|---:|---:|---:|
| 従来 wrapper/harness dispatch | 0 | 1 | 1 | N | N+2 |
| bundled + inner local | 1 | 0 | 0 | 0 | 1 |
| outer + inner dispatchを仮に許可 | 1 | 1 | 1 | N | N+3 |

現実装では最後の形の `--force-dispatch` を policy が拒否するため、実在 argvそのままなら qsub前に0回で停止する。forceを落として dispatch modeだけ残すと、outerとcollectionまで進んだ後に壊れ、正常な N+3 完走にはならない。

## 10. 攻撃したが破れなかった補助面

- **所見**: D131 #3、#5、#6、generic `<argv>` の現実装、fanout/full-suite反例探索は今回の静的攻撃では破れなかった。
- **なぜ real か**:
  - #3: harnessとwrapperが evidence付き site 判定で login/suspect の local を拒否する (`tools/mutation_harness.py:2938-2944`, `tools/mutation_worktree.py:1136-1142`)。
  - #5: mutation/generic は clean base env、DEVNULL、repo cwd、shell=Falseを使う (`tools/pegasus/dispatch_compute.py:781-906`)。
  - #6: deadline は RUN 初観測で張り直され、qdel は fresh qstat gateを通る (`tools/pegasus/dispatch_compute.py:3143-3197`, `tools/pegasus/dispatch_compute.py:1971-2000`)。atomic保証ではないという裁定修正とも整合する。
  - `<argv>`: 現在の `_job_run` は genericだけ直接 argvを実行する (`tools/pegasus/dispatch_compute.py:895-906`)。
  - fanout: 過去 brief も実 kernel admissionは一度も通っていないと記録する (`output/insights/2026-08-16_t851-fanout-exact-n/brief.md:15-24`)。full-suite mutation ledgerの反例も見つからなかった。
- **壊れ方**: 上記の明示範囲では具体的な反例なし。`check_docs.py` が `<argv>` の実行意味まで保証するわけではないが、runbookも検査を inventory 同期だけと明記している (`docs/pegasus-runbook.md:610-614`)。
- **重大度**: nit / backlog、または破れず
- **成果物影響**: この静的レビューで変更すべき成果物値はない。
- **提案**: #3/#5/#6は維持する。fanoutとfull-suiteについては「稼働中3 processからの一般化」ではなく、D433と frozen ledger探索を根拠として記録する。

## 総括

### (a) must-fix

1. bundled-local で attempt sidecarを通せる task由来契約を実装し、実 wrapperまで通す正例を追加する。
2. mutation policyを構造化し、local、detached、必須引数、runner identityをqsub前と `_job_run` で強制する。
3. direct harnessを許すなら、その lockを共有 lockへ移行して D131 #1 を閉じる。
4. outer receipt、job stdout、wrapper receipt、ledger、attemptを永続的に相互束縛して D131 #2 を閉じる。
5. pytest ini overrideを含む argv迂回を閉じる。
6. `check_docs.py` の `For`/return alias迂回を閉じる。

### (b) 裁定へ返すべきもの

1. selector、nodeid、`--deselect` を使う実在 matrixを bundled 対象外のままにするか。
2. hook変更なしの generic を D895 完了と呼ぶか、partial と記録するか。
3. official `DW-M07` は今も local attemptを禁止している (`docs/dev-wave/mutation.md:43-50`)。bundled例外を同正本へ入れるか。

### (c) 攻撃したが破れなかった箇所

- eligible な inner-local では qsub が実際に N+2 から1へ減る。
- login/suspect の local site gate。
- mutation/generic の clean child env、stdin、cwd、rc区別。
- fresh qstat gateとRUN後deadline rebaseの限定保証。
- 現在の generic direct argv実行。
- fanoutの成功実運用例と mutation full-suite実例は見つからず、既存証拠は親の観測を支持した。