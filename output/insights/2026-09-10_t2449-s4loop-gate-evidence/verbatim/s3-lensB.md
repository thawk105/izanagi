## 読んだ資料

射影された7資料はすべて読取可能だった。別 checkout、`hooks/`、`docs/pegasus-runbook.md` は射影外のため読んでいない。テストは実行していない。

- [親 brief](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/prompts/s1-brief.md:1)
- [段2 plan](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:1)
- [job body](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:1)
- [Pegasus README §6–§7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/README.md:291)
- [job-contract test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop_job_contract.py:1)
- [loop driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1)
- [T-2406 一次資料](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-08_t2406-s4loop-gflags-prologue/README.md:1)

## real 所見 (成果物影響つき)

1. **[手順漏れ][テスト代表性] plan は親 brief の argv 要件を放棄している。**

   親 brief は preprocess argv が現在の record に無く、追加が必要だと明記している [s1-brief.md:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/prompts/s1-brief.md:37)。一方 plan は `_run_process` を変更せず argv を断念する [s2-plan.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:17)。

   plan 自身、「live consumer は無い」「固定 digest golden も無い」と認めている [s2-plan.md:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:45)。過去 evidence の whole-file manifest は過去 bytes を固定するが、将来の producer 出力を比較する consumer とは限らない。これを P1b の反証と扱う根拠は、射影資料内では成立していない。

   成果物影響: red record は残っても、失敗した実コマンドを特定できず、gflags/include 経路との関係を答えられない可能性がある。

2. **[手順漏れ][ドリフト] evidence root の永続性を job body は保証していない。**

   job body の拒否は実行 checkout とその git-common root の内側だけである [p3_s4_loop_pegasus.sh:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:120)。以下は拒否されない。

   - `/scr/...` や `$TMPDIR` 配下
   - 別 repository の配下
   - 永続性のない任意 directory

   実際、job-local scratch は `/scr/$USER/...` である [p3_s4_loop_pegasus.sh:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:187)。README の「どの repository の配下でもない」は job body より強い operator 契約である [README.md:365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/README.md:365)。plan は具体的な永続 path を決めていない。

   成果物影響: JSON、`job.stdout`、`job.stderr`、`compute-result.json` が job 終了後に消え、wave の唯一の成果がゼロになる。

3. **[手順漏れ] driver が見るのは canonical 化前の環境値である。**

   `IZANAGI_S4_EVIDENCE_ROOT` は必須検査され [p3_s4_loop_pegasus.sh:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:17)、lowercase の `evidence_root` へ canonical 化される [p3_s4_loop_pegasus.sh:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:99)。しかし元変数へ再 export せず、driver は後で起動される [p3_s4_loop_pegasus.sh:580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:580)。

   qsub から環境として入った元値は子 Python に継承されるため、README の絶対 path を守れば正常に届く。一方、job body は相対値を拒否しない。検査後に `cd "$repo"` する [p3_s4_loop_pegasus.sh:212](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:212)ため、相対値では shell と driver が別 directory を指し得る。既存実行テストも絶対 path しか使っていない [test_p3_s4_loop_job_contract.py:1286](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop_job_contract.py:1286)。

   成果物影響: job body 自身の receipt と新規 gate record が別 root に分裂するか、gate record だけ書けない。

4. **[手順漏れ] green 後の timeout は「gate が通った」証拠にならない。**

   gate は [p3_s4_loop.py:1825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1825)、`run_campaign` はその後 [p3_s4_loop.py:1857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1857)。plan は green 経路で環境参照も書込みもしない [s2-plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:79)。

   したがって green 後に build/verify/bench が walltime で殺されると、red record は無い、成功結果も無い、という曖昧な状態になる。通常の非0終了なら EXIT trap が `compute-result.json` を作る [p3_s4_loop_pegasus.sh:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:137)が、scheduler の強制 kill では trap 実行を前提にできない。

   成果物影響: 「green だった」のか「gate 到達前に死んだ」のか判定できず、1本の投入が答えを返さない。

5. **[規律2][手順漏れ] 保存失敗隔離が `OSError` に限定されている。**

   plan は I/O error を収集して最後に拒否を送出する [s2-plan.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2449-s4loop-gate-evidence/artifacts/dev-wave-t2449-s4loop-gate-evidence/s2-plan.md:24)。これは `OSError` については正しい。しかし `canonical_json()`、ASCII encode、エラー文字列化など保存処理全体の予期しない `Exception` を隔離する契約が書かれていない。

   拒否本文を先に不変な文字列へ確定し、各 arm の「serialize→open→write→fsync」全体を `Exception` 境界内に置かなければ、保存側例外が元の gate rejection を置換できる。

   成果物影響: 最も必要な red 時に、gate の理由ではなく evidence writer の traceback だけが残り得る。

6. **[計測汚染][手順漏れ] 投入前提が不足している。**

   README の qsub command は job body を相対 path で指定している [README.md:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/README.md:383)。T-2406 一次資料自身も `cd "$REPO_ROOT"` と submodule PIN checkout の欠落を持越しとしている [T-2406 README.md:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-08_t2406-s4loop-gflags-prologue/README.md:72)。

   また driver は gate より前に single-tenant 検査と CCBench PIN/clean 検査を行う [p3_s4_loop.py:2630](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:2630)。別計測 job が生きていれば、今回の gate に到達しない。

   成果物影響: qsub 自体が失敗するか、別 job のため gate 前停止となり、計算ノード1本を消費しても目的の観測が無い。

7. **[権限逸脱][手順漏れ] hook に関する親 brief の一般化は射影内では未証明。**

   確認できたのは、契約テストが exact path key を `dispatch-required` として要求していることだけである [test_p3_s4_loop_job_contract.py:1706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop_job_contract.py:1706)。hook の照合・canonicalization・絶対 path 処理は射影外なので確認不能。

   exact relative path 以外、すなわち新規 file、別 script、絶対 path invocation が同じ許可を得るとは結論できない。

   成果物影響: 登録済みという推論だけで投入すると hook に拒否される、または未登録 surface を許可済みと誤認する。

## refuted (プラン / 親 brief が正しい点)

- 正しい絶対 path を `qsub -v` で渡す限り、元の `IZANAGI_S4_EVIDENCE_ROOT` は driver に継承される。plan の「値は見える」は正しい。ただし canonical 値ではない。
- gate は terminal-WAL skip より前である。gate 呼出しが [p3_s4_loop.py:1825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1825)、`run_campaign` が `:1857`、duplicate 解決が `:1868`。したがって、gate の red/green 判定だけなら fixture 値変更は不要。green 後も実 build させるなら未使用値が必要。
- 通常の red と通常の writable evidence root では、driver の RuntimeError → EXIT trap の流れで job 非0後も `job.stderr` と `compute-result.json` が残る。
- plan は job body を触らないため、現行の exact `CMAKE_PREFIX_PATH` 契約とは衝突しない。exact 3行は [test_p3_s4_loop_job_contract.py:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/tests/test_p3_s4_loop_job_contract.py:452)で固定されている。
- canonical evidence export を追加するだけなら、現行 CMAKE 検査や stage-order 検査は赤にならない。ただし、その export の除去を殺す既存テストも無い。
- `OSError` を収集し、外側の `RuntimeError` を `raise ... from first_error` とする案自体は拒否を握り潰さない。外側 message に reason/detail が残ることが条件。

## 投入契約のチェックリスト (親がそのまま使える形で)

- [ ] 現行 main 系の固定 SHAから、primaryでも `.claude/worktrees/` / `.codex/worktrees/` でもない専用 checkout を作る。
- [ ] `external/ccbench` を `PIN=028f34d` に checkoutし、superproject・CCBenchとも tracked clean にする。
- [ ] 同時に走る別の計測 job がないことを確認する。今回の qsub は1本だけ。
- [ ] runbook §6の正本値を使い、repo外の永続 cache root を設定する。値を推測しない。
- [ ] T-2232 の消失済み root を再利用せず、新たに `fetch`（必要時）→`hydrate`→`verify`→`verify-deps` を行う。
- [ ] `IZANAGI_S4_THIRDPARTY_SOURCE_ROOT` には hydrate JSON の `.source_root` だけを渡す。cache rootを渡さない。
- [ ] evidence root は絶対・canonical・永続 path とし、`/scr`、`$TMPDIR`、あらゆる repository 配下を避ける。
- [ ] 毎回一意で空の attempt directory を `0700` で作る。再利用しない。
- [ ] planが canonical値を再exportしない間は、相対 evidence pathを絶対に使わない。
- [ ] `EXPECTED_HEAD=$(git -C "$REPO_ROOT" rev-parse HEAD)` が full lowercase SHAであることを確認する。
- [ ] `cd "$REPO_ROOT"` 後に、登録済みの相対 path `tools/pegasus/p3_s4_loop_pegasus.sh` を qsubする。
- [ ] fixture走行では proposal/K2 envをすべて省く。green後の実buildも見たい場合だけ、既存terminalと異なる `IZANAGI_S4_FIXTURE_VALUE` を渡す。
- [ ] `-o` と `-e` を永続 attempt directory の `job.stdout` / `job.stderr` へ向ける。
- [ ] qsub job idと投入時のSHA・fixture値・hydrate `.source_root` を控える。
- [ ] red後は両arm JSON、`job.stderr` のreason/detail、`compute-result.json.driver_rc` を照合する。
- [ ] green後にrc0で完走しなかった場合、現planではgreenと断定しない。
- [ ] dedicated checkoutとcampaign WALは証拠回収・一次資料化が終わるまで削除しない。
- [ ] hookについては exact relative path の許可を親側で再確認する。絶対path、新規script、別scriptへ一般化しない。

## gate が通った場合の見積り

- 前回実測は、prologue・prebuild・gate拒否まで43秒 [T-2406 README.md:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-08_t2406-s4loop-gflags-prologue/README.md:39)。
- job予約は3時間 [p3_s4_loop_pegasus.sh:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/tools/pegasus/p3_s4_loop_pegasus.sh:5)。
- driver前の明示 timeout の合計上限は、gflags 180秒、glog 360秒、prebuild 1800秒、計2340秒＝39分。ただしcopy・検査等は別。
- driver tail は build×2→verify→bench [p3_s4_loop.py:1838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1838)。bench設定自体は `extime=1, reps=2` [p3_s4_loop.py:1476](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/orchestrator/campaign/p3_s4_loop.py:1476)だが、build/verify全体の上限は射影資料から算定できない。

結論として、3時間に収まるとはまだ言えない。通常エラーなら stdout/stderr、reservation、prebuild receipt、compute-result が残る。scheduler hard killでは stdout/stderrと既作成receiptは残るが、compute-resultは保証されず、green markerもないためgate通過は判定不能である。

## nit / 裁定パッケージ候補

- **P1b再裁定:** 過去evidenceのwhole-file manifestを、将来producerの互換性拘束と数えるか。数えないならargv追記を復活させないと親briefのscope未達。
- **green証拠:** red-only報告を維持してtimeout時の不明を受け入れるか、gate直後に受理集合を変えないgreen outcome sidecarを永続化するか。
- **canonical root:** READMEの絶対path operator契約だけで閉じるか、job bodyで `export IZANAGI_S4_EVIDENCE_ROOT="$evidence_root"` を行うか。
- **例外境界:** evidence保存全体の任意 `Exception` が元拒否を置換しない契約を明文化する。
- **hook証明:** 親briefの登録済み主張を検証するには、exact hook実装またはprobe結果を次段の射影へ加える必要がある。
- **変異帰属:** planの `without_evidence_root` とgreen testは、新規保存処理を丸ごと削除しても通るため、新機能のload-bearing testではない。またI/O三ケースを1 nodeへ束ねる案は個別帰属を失う。既存CMAKE検査の冗長maskは既に一次資料で実証済み [T-2406 README.md:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2449-s4loop-gate-evidence/output/insights/2026-09-08_t2406-s4loop-gflags-prologue/README.md:93)。なお `test_p3_s4_loop.py` は今回の射影外なので、既存nodeによる先行killのfile:line断定はしていない。

## 総括

planのred通常経路は概ね成立するが、このままでは成果達成を保証しない。停止条件は主に三つある。

1. 永続evidence rootが具体化・機械保証されていない。
2. green後のtimeoutがgate結果を曖昧にする。
3. argv断念により親briefの明示scopeを満たさない。

加えて、相対path、qsub cwd、fresh hydrate、single-tenant、hook exact pathがoperator依存である。これらを投入前に閉じない限り、「計算ノードで1本走らせたが、欲しい答えは残らなかった」を再現し得る。