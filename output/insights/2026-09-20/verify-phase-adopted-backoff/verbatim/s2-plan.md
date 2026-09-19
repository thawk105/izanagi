## 計画

以下の略記は、今回読んだ射影の実在ファイルを指す。行番号は射影ファイル内の番号であり、転記元文書の番号ではない。新規ファイルにはまだ行番号がないため、変更元・根拠の `file:line` を示す。

- `J` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verify-phase-adopted-backoff`
- `R` = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-verify-phase-adopted-backoff`
- `先例` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-verifier-cli-timing-probe/probe/verifier_cli_timing_probe.py`
- `校正器` = `R/orchestrator/campaign/s1_verify_extime_calibration.py`
- `1681` = `R/output/insights/2026-09-18/verifier-cli-timing-probe/README.md`

1. **runner の骨格**

   作成先は `J/probe/verify_phase_runner.py`。repo 内実装は変更しない（`J/s1-brief.md:39`、`:51`）。

   | 先例の関数・段 | 流用・変更 |
   |---|---|
   | `now():33`、`sha():37`、`write_json():45` | 流用。JSON の一時ファイル＋fsync＋replace を維持 |
   | `timing_record():58`、`timing_values():102`、`timed_process():110` | 流用。唯一の reaper を `wait4` とし、process group の timeout 処理を維持 |
   | `new_result():62` | job／rep／attempt／校正停止理由／保全情報を追加 |
   | `bench_argv():72` | rr95 固定を workload→rr5/50/95 の閉じた対応に変更 |
   | `verifier_argv():78` | CLI の形を維持。ただし commit witness 欠落時の引数省略は本走では使わない |
   | `configure_argv():86` | 候補別 define を渡せるよう変更 |
   | `count_c_lines():156`、`file_inventory():167` | 流用。C 行再計数と全行数・hash 計測は別区間のまま |
   | `project_verifier():176` | 生値転記を維持。実行失敗と verifier verdict を別 field にする |
   | `run():204` | 共通 setup/build と `measure_rep` に分割。校正ループ／4反復ループから呼ぶ |
   | setup `:214`、依存準備 `:255`、build `:271` | 計算ノード判定・toolchain・hydrate 済み依存利用・warmup/build の順序を維持 |
   | checkout `:267` | 下記の `checkout`＋`applied` に変更 |
   | trace→verify `:290` | 毎 rep 独立ディレクトリで実行 |
   | copy `:338`、cleanup `:352` | 検証済み永続保全の後だけ scratch を削除する形へ変更 |
   | `markdown():368`、`main():512` | 単発表示から候補全体の集計へ変更 |
   | `selftest():412` | argv、停止規則、集計、再開・重複検出、圧縮／非圧縮分岐を追加。実行は親 |

   **patch と identity。** `TMPDIR` を job 専用 `/scr` に設定してから、次の順序に固定する。

   ```python
   with checkout(PIN, base_dir=str(repo / "external/ccbench")) as source:
       assert_pinned_clean(source, PIN)
       with applied(str(repo / "patches/silo-backoff-fixed.patch"), PIN, source):
           evidence = resolve_evidence(
               genome, "511c953", ccbench_dir=source, cxx="g++")
           # 期待 identity 照合 → configure/build → 再照合 → trace/verify
   ```

   `checkout(pin_commit, base_dir="")` は `patchharness.py:346`、scratch 配置は `:362`、`applied(patch_path, pin_commit, ccbench_dir="")` は `:247`。patch 適用後に `assert_pinned_clean` を呼ばない。適用後は tracked dirty が正常である。build 後は同じ引数で evidence を再解決して照合する（`source_digest.py:2424`）。

   この順序は T-1998 の導出手順（`J/refs/t1998-prereg-s4-2.txt:8`）と A-2 の patch 適用済み隔離木での解決（`J/refs/a2-observed-positive-s1-s2.txt:7`）に対応する。`resolve_evidence` の keyword-only 引数と返り値は `source_digest.py:2413`、記録 field は `:190` の `source_root / ccbench_commit / genome_sha256 / src_token / source_bytes_sha256 / tracked_clean / tracked_diff_sha256 / tracked_paths`。

   fixed-5 の canonical genome と source digest は T-1998 JSON block を parse して採る（`J/refs/t1998-prereg-s5.txt:3`、`:20`）。`BACKOFF_NOINLINE=0` は configure に明示するが、T-1998 の canonical genome に勝手に追加しない。fixed-10 も brief の genome を用いる。完全な実測 token/digest を毎回保存し、既知の digest・token prefix 不一致、または `stock` なら停止する。**A-2 token 全桁と fixed-10 digest の期待値は射影にない**ため、完全照合の補完は後述の段4事項とする。

   **configure。** 次を固定する。

   ```text
   -DCCBENCH_TRACE=1
   -DCCBENCH_BACK_OFF=1
   -DCCBENCH_BACKOFF_FIXED=<5|10>
   -DCCBENCH_BACKOFF_NOINLINE=0
   -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
   -DCCBENCH_NO_WAIT_OF_TICTOC=0
   -DCCBENCH_WAL=0
   ```

   根拠は `J/s1-brief.md:12`、`:17`、A-2 controlled defines は `J/refs/operational-facts.md:29`。Release、sanitizer OFF、compiler launcher 空、CCACHE OFF、依存 source 指定は先例 `:86` を踏襲する。warmup と本 build に同じ define 集合を渡す。`cxx="g++"` の実体・version と build compiler の実体も記録し、不一致なら測定前に停止する。plain cmake の binary を既存 campaign binary と同一とは主張しない（`1681:34`）。

   **サブコマンド。**

   ```text
   selftest
   calibrate --candidate fixed-5|fixed-10 --workload write-heavy|balanced|read-heavy
   verify --candidate ... --workload ... --reps 4 --extime 3|6|10 --job-index 1|2
   summarize --input <J/run> --output <summary.json>
   ```

   実走には共通で `--repo-root / --third-party-cache / --scratch-root / --output-dir` を要求する。`--third-party-cache` に渡すのは hydrate 出力の `.source_root`。候補・workload・反復数・timeout は段4で固定し、records/threads 等を任意変更する入口は設けない。

   JSON は `verify-phase-adopted-backoff/v1` とし、次を持つ。

   | 区分 | 必須内容 |
   |---|---|
   | 識別 | phase、candidate、workload、extime、job-index、rep-id、attempt-id、hostname、UTC、runner sha、ruling sha |
   | 条件・identity | genome、patch sha、全 argv、上記 SourceEvidence、binary sha、python realpath/version、repo HEAD、verifier module 別 sha |
   | seed identity | 論理 rep-id、attempt-id、PID、開始時刻、`seed_mode=self-seeded`、数値 seed は null |
   | process 計時 | Popen直前／復帰／wait4復帰の monotonic、wall、rc、signal、timeout、user/sys/maxrss |
   | bench/count | stdout/stderr path、commit/batch witness、abort、throughput、C 行数と再計数 wall |
   | verifier | 生 JSON/stderr path、parse_ok、**原 verdict**、certified、anomaly_count、anomalies、integrity、proof_surfaces 有無 |
   | 実行状態 | execution_status、failure_reason、`operational_outcome`、OOM 証拠 |
   | 保全 | file 別原本 hash/bytes/lines、codec、保全先、圧縮後 hash/bytes、保全完了 flag |
   | 校正・会計 | selection_eligible、stop_reason、job monotonic wall、段別 wall、予算消費 |

   seed 数値を創作しない。独立性は自己シードする別 process の操作的仮定に限る（`J/refs/phase-doc-seedn.txt:1`）。

   **timeout/OOM。** verifier hard timeout は P3 の **1800秒**。先例 `:125` の watchdog を使う。timeout・OOM で JSON が得られなければ原 verdict は null、`operational_outcome=indeterminate` とする。CLI 自身の `indeterminate` と区別し、`certified=false` 等の架空の CLI 出力を作らない。SIGKILL だけで OOM と断定せず、取得可能な cgroup `memory.events` 差分や scheduler 記録を保存し、証拠がなければ `killed_unknown` とする。CLI rc=2・壊れた JSON も pass にしない（`orchestrator/verifier/cli.py:11`、`:76`）。

   **trace 保全。** inventory は先例同様 verifier 前に実施し、page cache 条件を記録する（`1681:66`）。全 trace 原本を **verifier 起動前に永続側へ保全完了**させ、OOM／walltime kill でも入力を残す。各 file を `zstd -T0` で圧縮し、一時出力から rename、圧縮前 hash/bytes/lines と圧縮後 hash/bytes を記録。zstd 不在なら非圧縮コピー＋hash 照合とし、圧縮後 field は null にする。圧縮失敗を「不在」と扱わず停止する。途中 bench の trace も可能な範囲で保全し、完全性を別記する。保全・hash・圧縮の時間は verifier wall に含めず job 予算には含める（`J/s1-brief.md:30`）。

   **単独性・計時。** 計算ノード上で毎 bench と毎 verifier の直前に `_assert_single_tenant()` を呼ぶ。実行中ずっと単独だったとの保証には拡張しない（先例 `:216`、`:295`、`1681:122`）。bench、verifier、build、圧縮等の runner 管理 process は Popen直前〜wait4復帰、Python 内の計数・inventory は関数前後、job 全体は setup 開始〜保全・cleanup 終了の monotonic を記録する。job wall と内訳を二重加算しない。

2. **段Aの校正規則**

   `J/s1-brief.md:26`、`:28` と `J/refs/phase-doc-iv.txt:19` に従い、機械可読設定を次とする。

   ```json
   {
     "extime_candidates": [3, 6, 10],
     "runs_per_extime": 1,
     "verifier_limit_s": 600,
     "verifier_hard_timeout_s": 1800,
     "trace_hard_timeout_s": 120,
     "stop_on_wall_gt_limit": true,
     "stop_on_incomplete_verifier": true,
     "calibration_anomaly_disqualifies_candidate": true,
     "minimum_extime_s": 3
   }
   ```

   bench timeout 120秒は `pipeline.py:409`、`:446`、校正器 `:64` に合わせる。先例の900秒は計時 probe 固有なので移植しない。

   各候補×workload で 3→6→10 を各1回。完走した校正の anomaly は wall に関係なく候補失格。完走 wall >600秒、timeout、OOM はその extime 以上を打ち切り、未実走を `not_run` と停止理由付きで保存する。CLI の indeterminate・パース失敗も選択適格にしない。

   `choose_extime(results: Sequence[Mapping], limit_s: float) -> int` は流用可能（校正器 `:130`）。必要 field は `extime` と有限非負の `verifier_walltime_s`（`:149`、`:156`）。ただし verdict を検査しないため、runner が先に適格性を検査する。正常に完了した昇順 prefix だけを渡し、timeout/OOM の打切り時間を「完走した verifier wall」として渡さない。途中で異常停止した prefix を正常な校正完了と誤認させないよう、停止理由も必須とする。

   `calibrate_candidates` 全体は流用しない。既存 `_validate_candidate` は非 certified を一括失敗にし、P3 の記録区分を表現できない（校正器 `:170`、`:191`、`:198`）。既存 `main` の g_rl／freeze／cygnus 束縛も実行しない（`:230`、`:437`）。

   6秒の見積りは単純比例で `421.707×2=843.414秒`、既往の6秒実測は974.7秒。1800秒は後者に約825秒の余裕があり、600秒で kill する誤りを避けられる。ただし別候補・別nodeでの完走保証ではない（`1681:79`、`J/refs/phase-doc-iv.txt:21`）。

   **read-heavy 10秒を無条件に禁止する規則ではない。** 今回の6秒が >600秒または不完走なら10秒は実走しない。6秒が ≤600秒で適格なら10秒へ進む。過去の974.7秒だけを理由に今回の6秒を省略しない。

3. **候補ごとの extime 確定と4時間予算**

   各 workload の正常完了・適格な extime 集合を作り、その共通部分の最大値を初期値とする。空集合なら3秒へ丸めず「候補なし」とする（校正器 `:163`、`J/s1-brief.md:26`）。

   候補 \(c\)、workload \(w\)、extime \(e\) について、

   \[
   T_{cw}(e)=T_{\rm bench}+T_{\rm count}+T_{\rm verifier}
   \]

   \[
   \widehat B_c(e)=\sum_w8T_{cw}(e)
       +\sum_{w,k}F_{cwk}
       +\sum_w8A_{cw}(e)
   \]

   とする。`F` は6 job分の setup/build/cleanup 固定費、`A` は反復ごとの inventory・hash・圧縮・転送費。後者を省くと、P5 の必須作業が予算から消える（`1681:78`、`:80`）。

   見込みが14400秒を超えたら10→6→3の一段下へ移り、同じ計算を繰り返す。3秒でも超える、または3秒の適格結果がない場合は段Bを投入せず未確定とする。並列化による経過時間短縮を合計予算の削減として数えない。

   校正・失敗・retry の消費も別欄に累積し、段4で「4h/候補」がこれらを含むかを明記する。射影の旧総予算規則は校正・build・失敗・retry も計上対象である（`J/refs/phase-doc-iv.txt:1`）。推奨は、4hの残額から校正等の既消費も控除する保守的な統一会計。並列投入前に候補全体の予定消費を予約し、各jobが独立に同じ残額を使わないよう親が台帳を管理する。

   段4追補には全校正行、共通集合、初期値、費用内訳、段下げ履歴、確定 extime、予算残額、ruling sha を記す（`J/s1-brief.md:35`、`:40`）。

   workload 別 extime 案は軽い workload の trace を長くできる一方、条件が3値となり比較・会計が複雑になる。
   P1の候補共通値を採用し、このwaveでは代案へ切り替えない。

4. **段Bの分割・投入・再開**

   段Aは6 job、段Bは12 job、1 nodeにつき1 runner。各段B job は4反復を直列実行し、`job-index=1` に rep 1〜4、`=2` に rep 5〜8を割り当てる（`J/s1-brief.md:29`）。

   ```text
   J/run/calib/<cand>-<wl>/extime-<e>/
   J/run/verify/<cand>-<wl>-<k>/rep-<i>/attempt-<a>/
   ```

   job ごとに `job.json`、rep ごとに `result.json` と原資料を置く。先例 `:225` の「既存ならランダムな別出力先へ逃がす」動作は廃し、予定repとattemptを明示的に管理する。

   段B job の所要見込みは、

   \[
   \widehat W_{cwk}=F_{cwk}+4\{T_{cw}(e_c)+A_{cw}(e_c)\}
   \]

   とする。1681の値を仮置きすると bench＋count＋verify は4反復で約1768秒、inventory＋非圧縮copyを加えて約1850秒、buildを仮に240秒とすれば約35分。ただし stock の参考値であり、圧縮込みの候補校正値で置換する（`1681:76`、`:78`、`:80`、`J/refs/operational-facts.md:9`）。

   予約walltimeは期待値と別に、setup/build上限、4回のbench上限・verifier hard timeout、保全・終了余裕を足して決める。期待35分という理由だけで短いwalltimeを指定しない。

   submit-tree は段A用6本＋段B用12本の**計18本**を各段の投入前に作る。親が固定HEADから `git worktree add --detach`、`dev_wave_submodule_init.py --worktree <abs>`、hydrate を済ませる。投入後は各treeの `output/` 以外を変更しない（`J/refs/operational-facts.md:5`、`:9`）。

   dispatch CLI に `--repo-root` はない。各 submit-tree 内の script 自身を起動する。

   ```text
   python3.10 <submit-tree>/tools/pegasus/dispatch_compute.py
     --task generic --walltime <HH:MM:SS>
     --queue-wait-timeout 14400 --overall-grace 14400
     -- python3.10 -B <J>/probe/verify_phase_runner.py verify
        --repo-root <submit-tree> ...
   ```

   前半の引数は `dispatch_compute.py:4728`、`:4750`、後半の `--repo-root` は**新runnerの引数**。dispatch の既定repoは script の配置から決まる（`:3601`）。clean envなので必要設定は argv に載せる（`:155`）。

   再投入は verdict の良否で選ばず、未完了repだけを同じ候補・workload・extime・rep-idで継続する。完了した anomaly／indeterminate を含む記録は捨てない。verifier未完了でも trace 保全済みなら同じtraceの検証を再開し、benchを再生成しない。traceが失われた場合だけ同条件の新attemptを作り、失敗attemptと消費時間も残す。**記録済み indeterminate がretry成功で消える集計はしない。** rc≠0だけでjob全体を再測定せず、dispatch receiptとrep記録で未完了範囲を確定する。

5. **`summarize` の判定**

   候補ごとに workload 3行×rep 8列の24枠を出し、各枠に verdict／certified／anomaly_count／attempt参照を載せる。校正は同じ候補表の別区画に workload×extime として併記し、未実走セルには停止理由を表示する（`J/s1-brief.md:28`、`:33`）。

   集計規則は次の順序で固定する。

   ```text
   校正または検証に anomaly が1件以上:
       失格
   それ以外で、24枠すべてが記録・保全済み、
   CLI verdict=serializable、certified=true、anomaly_count=0、
   実行・identity不備や未解決indeterminateなし:
       pass
   それ以外:
       未確定
   ```

   CLI の `non-serializable` を確定異常として保持する。anomaly件数は原 `anomaly_count` を合計し、表示制限付き `anomalies` 配列長で代用しない。`total_cycles` は原JSONにあれば別に転記する（先例 `:178`、`:187`、`1681:90`）。

   indeterminate件数は「CLIが返した件数」と「timeout/OOM等の運用上の件数」を分け、未実走・JSON不正も別件数にする。未知の anomaly_count を0にしない。重複rep、欠番、異なるruling/identityの混入は集計不成立として pass を出さない。

   600秒は校正の選択閾値であり、段Bで600秒を超えて完走した正規 verdict を書き換える条件にはしない。所要超過は会計へ反映し、extimeを途中変更しない（`J/s1-brief.md:35`）。CLIを用いた結果を pipeline の capability 認証へ昇格しない（`pipeline.py:614`、`1681:119`）。

6. **記録物**

   `J/s1-brief.md:39` の成果物配置に従う。

   | 成果物 | 節構成 |
   |---|---|
   | insight README | 結果と完了状態／条件・規律1／候補identityとbuild／校正全表・停止理由／extime選定計算／24枠判定表・校正判定／予算・失敗・retry／限定・既往との関係／一次資料pathとhash |
   | results 系列稿 | この1結果が答える問い／対象と固定条件／校正・反復方法／一次資料からの候補別結果／未確定・失格の扱い／限定／一次資料リンク |
   | decisions fragment 1本 | 日付・P2裁定／候補別extime確定値と追補参照／記録先3箇所／phase doc追記繰延べ理由／凍結解除・再発行を行わないこと |
   | worklog fragment | 実装・校正・投入・結果・reviewの事実と未完了事項 |

   results は「1 file＝この検証相の1結果」とし、protocol statusを研究全体の成否へ拡張しない。trace-enabled throughput は性能値でないと明記し、`1−εⁿ` は主張しない。既往のA-2/T-1998 certifiedや2026-07-16校正は保持して併記する（`J/s1-brief.md:33`、`J/refs/a2-observed-positive-s1-s2.txt:48`）。

   `docs/paper-story/README.md` 本体は今回の射影外なので読んでいない。「results系列」規則は依頼文の指定として適用し、実在しない挿入行番号は付けない。親が編集時に表の位置を確認する。

   phase doc繰延べ理由と模擬FreezeErrorは、今回再実験した事実ではなく**親のbriefに記載された事実**として引用する（`J/s1-brief.md:21`、`:27`）。逐語資料とrunner sourceは `verbatim/` に保存し、job側runnerとのhash対応を記す。

7. **リスク表**

   | 事象 | 検知方法 | 対処 |
   |---|---|---|
   | 6秒read-heavyのメモリ不足 | wait4 maxrss、取得可能なcgroup peak/events、scheduler記録 | 1800秒timeoutとOOMを区別して記録。P3で当該extime以上停止。約88GiBは推定で、完走保証にしない（`1681:79`） |
   | queue滞留・overall timeout | dispatch receiptの状態履歴・reason | queue待ちと実走を区別し、未完了分だけ再投入。RUN時の期限再設定も考慮（`dispatch_compute.py:4155`、`:4200`） |
   | hydrate失敗・外部net不在 | hydrate rc、`.source_root`、configure log | 投入前にstagingを完成。永続cache直指定へ逃げない（`J/refs/operational-facts.md:5`） |
   | pinned-clean失敗 | `assert_pinned_clean`例外 | patch/build前に停止。汚れた木を自動修復して続行しない（`patchharness.py:174`） |
   | 期待identity不一致 | source digest/token、build前後evidence、compiler実体 | fail-closed。stockや新digestを観測後の期待値に置き換えない（`source_digest.py:2413`） |
   | `/scr`容量不足 | 各rep前の空き容量、校正trace bytes | build＋最大trace＋圧縮作業領域の見積りを満たさなければ起動しない。保全確認後に前repを削除（`J/refs/operational-facts.md:4`） |
   | walltime killでtrace消失 | 永続manifest・hash・rep状態 | verifier前に保全。未保全なら完了扱いしない（`J/s1-brief.md:30`） |
   | zstd不在・圧縮失敗 | 実行可能fileの有無、rc、hash | 不在のみ非圧縮。失敗は記録して停止 |
   | 単独性を確認できない | node上の `_assert_single_tenant()` | processを起動せず未完了記録。割当てだけを専有の証拠にしない（`J/refs/operational-facts.md:11`） |
   | 予算不足・3秒でも不適格 | 候補全体の予約額・累積job wall・校正集合 | Nを削らず未確定。retryを無料扱いしない（`J/refs/phase-doc-iv.txt:1`、校正器 `:163`） |
   | 同一treeから並行dispatch | rc=16・orphan hold | 18本の独立submit-treeを使用（`J/refs/operational-facts.md:9`） |

## brief と食い違う点

- **dispatch の `--repo-root` はCLIに存在しない。** 運用射影 `J/refs/operational-facts.md:9` と `dispatch_compute.py:4727` が不一致。代案は、各submit-tree内の dispatch scriptを直接起動すること。P4の投入構造は維持できる。

- **overall期限は投入時から固定ではない。** 運用射影 `J/refs/operational-facts.md:8` に対し、現行コードは初期期限を設定後、信頼できるRUN初観測時に再設定する（`dispatch_compute.py:4155`、`:4200`）。代案は現行実装どおりの期限計算を投入計画に記録する。

- **期待identityが完全照合には不足する。** brief `:14`、`:15` と A-2射影 `:17`、`:19` はtoken prefixのみで、fixed-10のsource digestもない。代案は、親が段4でA-2原資料の全桁期待値を独立に補完し、runner起動条件として固定すること。今回の射影だけで全桁一致を確認済みとは書けない。

- **4hの会計範囲は未確定部分がある。** P1の式は検証24回＋固定費だが、旧規定は校正・失敗・retry等を含める（`J/s1-brief.md:26`、`J/refs/phase-doc-iv.txt:1`）。代案は、校正を含む候補別総額を4hに束縛し、inventory・圧縮・保全費も算入すると段4で明記すること。

- **「6秒は約88GiBで完走見込み」は資源保証に使えない。** 元の43.95GiBは同時に生きるprocess tree全体の合計ではない（`1681:79`）。代案は、1800秒で実走し、OOM証拠を保存してP3のindeterminate分岐を適用すること。

- **brief冒頭の完了条件は常に達成できるとは限らない。** 「24件記録しpass/失格確定」（`J/s1-brief.md:6`）に対し、P3は校正anomalyで本走禁止、timeout等では未確定を許す（`:28`）。代案は、「校正失格なら本走未実施を記録、indeterminate等が残れば未完了・未確定」と報告し、24件やpassを埋め合わせないこと。

P1の候補共通extime、P2の追記繰延べ、P3の1800秒、P4の6＋12 job、P5の全trace保全には従う。

## 総括

先例を基に、patch適用済みidentity、校正停止規則、24枠集計、全trace保全をrepo外runnerへ実装する。
最大のリスクは、校正を含む総予算と6秒read-heavyのメモリ消費である。
段3では、全桁identityの補完、4hの会計範囲、indeterminateをretryで消さない集計を重点的に攻撃してほしい。
静的読取りのみ実施。ファイル変更・selftest・pytest・計算ノード実走は行っていない。