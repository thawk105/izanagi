## 所見

以下は静的読解による判定。新規 script・契約 test は未実装なので、変異の KILLED／SURVIVED は予測であり実測ではない。pytest・job 起動・書込みは行っていない。

1. **登録簿追加だけでは既存 hook test が赤になる。**
   - **対象:** plan §4:237、§9 の変更範囲。現物 `orchestrator/tests/test_hooks.py:3163,3239,4085,4580`。
   - **何が／正しくは:** production の sanctioned paths は登録簿から導出されるが、test の期待値は `_PEGASUS_EXPECTED_CLASSES` と `_PEGASUS_EXPECTED_ENTRIES` の二つの literal golden。plan の「手書き追加不要」は test 側について誤り。両方に新規2 entryを追加する必要がある。`_PEGASUS_DIRECT_COMMANDS` は前者から導出される。
   - **放置時の帰結:** `test_bash_pegasus_registry_schema_and_fixed_classes` と `test_bash_sanctioned_pegasus_paths_are_derived_from_registry` が赤。
   - **must-fix。** brief の純増 scope も、この既存 test 編集を含むよう訂正する。

2. **`TMPDIR=/scr/${PBS_JOBID}` と Python shim の組合せは `0:` 付き job ID で壊れる。**
   - **対象:** brief P5、plan §1 scratch。現物 `tools/pegasus/floor_campaign.sh:26`、`tools/pegasus/a5_second_boot_backoff_sweep.sh:184,257`。
   - **何が／正しくは:** 継承する job ID regex は `0:123.nqsv` を許す。その配下の shim directory を PATH に追加すると、`:` が PATH 区切りになり shim を探索できない。A-5 は `${PBS_JOBID//:/_}` に変換している。
   - **放置時の帰結:** shim の `python3` 解決契約が破れる。ただし今回の測定経路は選択済み `$PY` を使うため、これだけで job 非0になるとは断定できない。
   - **must-fix。** shim を置くなら scratch 名から `:` を除き、通常 ID と `0:` 付き ID の両方を契約 test に入れる。

3. **必須 command に `nm` が欠けている。driver の外部 process は binary と pgrep だけではない。**
   - **対象:** brief P5、plan §1 commands。現物 `floor_pair_driver.py:538,558,581,2117`、`orchestrator/campaign/buildcache.py:3761–3783`。
   - **何が／正しくは:** driver は Git command に加えて、各 session の binary 検査で `nm -C` を起動する。plan の必須 command 集合には `nm` がない。
   - **放置時の帰結:** `nm` がない compute 環境では前段を通過し、create-only JSONL を確保した後に `binary_binding_failed` を記録する。CLI は結果を出して rc=0になりうる（`floor_pair_driver.py:3132–3141`）。
   - **must-fix。** 前段に `nm` の存在確認を追加する。trace 検査本体は driver に残す。

4. **Python shim の必要性は、受入 pytest の実測と今回の driver 経路を分けて説明すべき。**
   - **対象:** plan §1 interpreter／scratch、runbook §3。現物 `orchestrator/calibrator/runner.py:536–546,636–664,1164–1195`、`floor_pair_driver.py:1590–1607,1622–1630`。
   - **何が／正しくは:** 今回の3 spec は `numactl_argv=[]`、`extra_env={}`、`use_perf=false`。runner は親環境を複写し、追加 env を反映して `FLAGS_*` を除去する。測定 subprocess の argv は binary から始まり、この経路には `python3` を探索する孫 process がない。runbook の shim 実測は pytest 経路の証拠。
   - **放置時の帰結:** 「shim がないと今回も古い Python で落ちる」という説明は証拠と不一致になる。
   - **情報。** `$PY` の明示選択と `-I -c` bootstrap は妥当。brief P5 の `-I -m` を直した plan は正しい。

5. **snippet test は関数の意味を検査できるが、本番からの接続をまだ保証していない。**
   - **対象:** plan §5:259–265,268。現物の抽出型は `test_a5_second_boot_job_contract.py:59–62`。
   - **何が／正しくは:** `window_gate`／hostname 関数の抽出実行は有効。一方、`test_gate_order_and_calls`、argv、dry-run、receipt は検査方法が未確定。文字列の存在・順序だけなら、`if false; then window_gate ...; fi`、正しい argv を作った後の差替え、qsub 分岐の逆転を見逃す。
   - **放置時の帰結:** 関数単体と M0〜M6 が緑でも、実際には gate を呼ばない変異や dry-run から投入する変異が生存しうる。
   - **must-fix。** author 前に、実際の分岐・array 構築部分を抽出実行する node と観測値を固定する。実 qsub／driver は不要。signal 中断時の `wait` と driver rc 保存も、無害な child による検査対象にする。

6. **login 起動確認の「必ず hostname gate まで到達」は成立しない。**
   - **対象:** brief 起動確認、plan §7:297 および到達性留保。現物 `a5_second_boot_backoff_sweep.sh:243–271`、`test_hooks.py:4433–4439`、逐語 F660。
   - **何が／正しくは:** plan の site→scratch 順序なら `/scr` 不在による先行失敗は避けられる。A-5 をそのままコピーすると scratch 作成が hostname gate より前なので避けられない。plan は qstat 段を継承しない点も正しい。ただし hook が有効なら、新設 submitter は main 未登録、job body は着地後も login で `dispatch-required` のため script 到達前に拒否される。
   - **放置時の帰結:** `site/compute_node_required`, rc=4 を観測できず、hook 拒否で終わる。hook の rc と script の rc を混同してはならない。
   - **must-fix。** 完了条件を「実際の到達 gate の記録」に修正する。また plan:297 の直接 `git worktree add` は、依頼が指定した隔離 session の `.sh` 経由手順へ修正する。

7. **PBS／qsub の骨格は妥当だが、canonical cwd と伝播の実測は別に残る。**
   - **対象:** plan §1、§2、§3:171–185。現物 `floor_campaign.sh:1–6`、`submit_floor.sh:647–666`、`submit_a5_second_boot_backoff_sweep.sh:169–177`。
   - **何が／正しくは:** `-A SFC`、`-q gen_S`、`-b 1`、`--accept-sigterm=yes` を header、walltime を mode 別 `qsub -l` に置く設計に矛盾はない。8個の env 値は固定文字列・hex・安全な固定 path なので、comma／空白による `-v` 分割問題もない。`-o/-e` は絶対 path。
   - **放置時の帰結:** logical PWD を残す実装では、receipt の canonical root と `PBS_O_WORKDIR` の表記がずれうる。dry-run は PBS による値の配送を検査しない。
   - **should。** qsub は `cd -P -- "$REPO_ROOT"` 後に実行し、job 側でも realpath 同士を比較する。signal header は scheduler による終了から driver を保護しない。

8. **既存 body は一つを丸ごと型にせず、plan の選択的継承を維持する。**
   - **対象:** plan §1 継承表。現物 `floor_campaign.sh:169–184,441–462`、A-5:199–271、`probes/t2187_adaptive_const_probe.pbs:72–100`。
   - **何が／正しくは:** floor は interpreter／receipt の型、A-5 は固定 PATH と安全な scratch 名、t2417 が使う PBS body は scratch より先の hostname 判定が参考になる。A-5 の build・qstat・worktree 段は今回不要。floor の signal handler は即 exit なので、plan の「child を終了まで回収」と同じ実装ではない。
   - **放置時の帰結:** floor の trap をそのまま移植すると、driver の完了 rc 回収より先に shell が終了しうる。
   - **should。** signal 処理は「継承」とだけ記さず、今回の待機・receipt 契約を独立に検査する。

9. **親の三つの前提は概ね正しい。ただし「system lib のみ」の射程を限定する。**
   - **対象:** brief:33–46。現物 `floor_pair_driver.py:1590`、`runner.py:1085–1195`、`test_ccbench_spawn_sites.py:594–597,852–899`。
   - **何が／正しくは:** この呼出し経路には共有 home の bench lock 取得がない。shell build sink は実際に `cmake --build`＋`--target`＋`ycsb_*` であり、新規 test は `_BUILD_SCAN_PATHS` の外。
   - binary は読取専用の `readelf -d` と SHA-256 照合で確認した。NEEDED は brief 通り4ライブラリだけ。ただし旧 build directory の RUNPATH が残るため、NEEDED だけで compute 上の実際の解決先まで証明したことにはならない。
   - **放置時の帰結:** gflags/glog build を足す根拠はない。一方「compute で依存解決済み」と報告すると未実測を成功扱いする。
   - **情報。** t2772 の指定2編集面と新規 test の直接競合はない。golden 修正を加えても、この2ファイルの編集は不要。

10. **P1／P2／P6 は採用可能だが、並走・queue 待ちの保証にはしない。**
    - **対象:** brief P1/P2/P6、plan §8。現物 `docs/pegasus-runbook.md:1344–1352,1379–1384,1466–1481`、A-5 submitter:48–55。
    - **何が／正しくは:** 記録上の gen_S は submit/user limit が UNLIMITED、group が200。ただしこれは同時実行数の保証ではない。混雑待ちで残窓が10時間未満になれば、plan の job gate は rc=4で拒否する。30時間要求が既存 floor の記す86400秒上限を超える点と、10時間要求の優先度・fair-share 効果は分けるべきで、後者の実測根拠はない。
    - 共有 bench lock による直列化はない。`/scr` は node local、runner は rep ごとに一時 directory を作成・除去する。ただし容量不足なら scratch 作成拒否または測定失敗となる。複数 spec の出力は分離できても、同一 spec の重複投入は create-only 出力で競合する。
    - evidence root は `dev-wave-jobs` の兄弟なので、その配下の空 `.git` は祖先ではない。A-5 helper を流用して evidence を `dev-wave-jobs` 配下に置くと、空 directory でも `.git.exists()` により拒否される。
    - **放置時の帰結:** 「6 window job を分割したから独立・並走成功」とはならず、待機拒否や出力競合が起こりうる。
    - **should。** 後続投入手順に、spec ごとの重複防止、同一 HEAD 維持、queue 待ち後の拒否を明記する。

## 登録簿閉包の検査一覧

「登録簿追加で必ず赤になるもの」と「本件では変更不要な関連検査」を区別する。

| 検査 | file:line | 赤になる条件 | plan の対応 |
|---|---|---|---|
| canonical registry loader | `tools/pegasus_admission_registry.py:98–135` | field 順、path ソート、JSON bytes 不一致 | あり |
| 実行体 inventory | `test_hooks.py:4523–4549` | 新規 script と登録簿 key が不一致 | あり |
| 全 entry golden | `test_hooks.py:3163,3239,4085` | 新規2 entryを期待 class／全field集合へ追加しない | **漏れ** |
| sanctioned 集合 | `test_hooks.py:4580–4589` | local-ok submitter が実集合にだけ増える | **手書き不要との記述が誤り** |
| login／suspect bit pin | `test_hooks.py:3686,4433` | golden 更新後、class と受理 bit が不一致 | 明示不足。class golden 更新で対象追加 |
| fallback 投影 | `hooks/guard_bash.py:207,285–307`、`test_hooks.py:4467` | 非Pegasus path の投影不一致 | あり。本件2 pathでは変更不要 |
| registry 異常時の縮退 | `hooks/guard_bash.py:300–307`、`test_hooks.py:4066,4131` | 不正 registry で direct entry を許可 | 明示不足。新entry自体の追加で赤にはならない |
| runbook 投影表 | `tools/check_docs.py:4465–4499` | path/class/evidence の集合不一致 | あり。M6対象 |
| runbook unknown 表 | `tools/check_docs.py:4502–4562` | 未登録path、不適切なclass説明、必須警告欠落 | **列挙漏れ**。今回の2行追加は不要 |
| runbook 実測表 | `tools/check_docs.py:4565–4599` | evidence=`runbook §7.0 実測` の集合と不一致 | **列挙漏れ**。static evidenceなので追加不要 |
| hook installation の HEAD 束縛 | `tools/check_codex_hooks.py:41–46,296–357` | working registry が HEAD blob と不一致 | pin 対象の言及あり。commit 前後の検証順を明記すべき |
| worker launch 束縛 | `test_codex_worker_launch.py:3747–3756` | 起動対象の registry bytes が HEAD と不一致 | あり。なおこの test 自体は意図した拒否を検証する |
| Codex hook pin test | `test_codex_hooks.py:492–495,538–548` | pin 対象集合や drift 拒否が壊れる | **列挙漏れ**。entry数の golden ではなく本件編集不要 |
| docs 合成 fixture | `test_check_docs.py:1151–1169` | 合成 registry と合成 runbook の不整合 | **列挙漏れ**。実 registryをコピーしないので2 entry追加不要 |
| plain runner coverage | `test_plain_runner_coverage.py:35–86` | 新規testに自走harnessもallowlist登録もない | あり。planの `_run()` 方式で満たせる |
| shell build sink 閉包 | `test_ccbench_spawn_sites.py:852–899` | 新しい shell build sink が生じる | あり。今回は生じない |
| duration ledger | `acceptance_duration_ledger.json:2`、`conftest.py:1792–1819`、`tools/acceptance_shards.py:392–404` | 新node欠落だけでは赤にならない。unknown cost／1秒への fallback がある | **列挙漏れ**。架空の所要時間を追加する必要はない |

`evidence` の二文字列は既存と逐語一致する。job body は registry:70付近、submitter は :316–320 や :346–350 に同じ文字列がある。`submit_floor.sh` 自体の evidence は `legacy-admitted (未実測)` なので、その entry の丸写しにはしない。

## 変異 × test の殺傷表

全 node は未実装。以下は plan 通りに実装した場合の予測。

| 変異 | 対応 node／実行 | 静的判定・必要条件 |
|---|---|---|
| M0 コメント追記 | 新規契約test全体 | **SURVIVED が妥当**。通常コメントなら runtime 等価。ただし抽出 marker／全文 hash の対象にしないこと |
| M1 job class反転 | `test_registry_entries` | 全fieldの独立期待値比較なら **KILLED** |
| M2 rr95 pin一桁変更 | `test_frozen_spec_pins` | D2138・実file SHAを独立に照合すれば **KILLED**。submitter自身から期待値を生成してはならない |
| M3 `<=` → `<` | `test_window_gate_boundaries` | `now=not_after-duration` を実関数に渡すので **KILLED**。plan は境界を踏んでおり、この点は不足なし |
| M4 hostname条件を `:` | `test_hostname_gate` | 条件command全体を `:` に置換すれば login負例で **KILLED**。regex文字列だけの置換とは区別して exact diff を固定する |
| M5 execute → validate | `test_driver_argv` | 禁止literal検査でも **KILLED** は可能。ただし mode別の実argv構築を実行確認しないと接続の正しさは残る |
| M6 runbook行削除 | 新規契約test、直接 `check_docs.py` | 契約testは **SURVIVED**、直接checkerは集合不一致で **KILLED／rc=1** の予測 |
| 追加候補：gate呼出しを到達不能化 | `test_gate_order_and_calls` | 存在／順序regexだけなら **SURVIVED**。現在のplanでは殺傷未確定 |
| 追加候補：dry-run条件反転 | `test_dry_run_has_no_execution` | 分岐の実行観測がなければ殺傷未確定 |
| 追加候補：signal後のwaitを一回で終了 | receipt／signal検査 | planの関数一覧には専用実行検査がない。driver rcの誤記録を見逃しうる |
| 追加候補：scratch名のcolon正規化除去 | interpreter／PATH検査 | 現行M0〜M6では覆わない。`PBS_JOBID=0:...` の値が必要 |

新規 test の名前は plain-runner メタテストの対象になるが、自走 harness 案で対応できる。spawn-sites の production scan は tests directory を含まないため、新規 file の追加だけでその行番号 pin が動くことはない。

## 総括

plan は `-I -m`、evidence 所有、窓境界、hostname 判定について brief を適切に訂正している。  
着手前の必須修正は、hook golden 2集合の更新、scratch 名の colon 処理、`nm` の前段確認、契約testの実行検査方法の固定。  
login smoke は script の rc=4 到達を保証できず、hook拒否を別成果として記録する必要がある。  
M3 の境界値と M0 の通常コメントは妥当だが、M0〜M6だけでは本番分岐・signal処理の接続を覆わない。  
PBS配送・compute成功・queue待ち時間は未実測。今回の静的検証で成功扱いにはできない。