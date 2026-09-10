## 命題 1 — scope の縮小か

**real — 親は scope を縮めている。** 依頼文は「6 点の数値を揃える」だけでなく、「同一ビルド・同一 job 割付けで測る」という新規の測定行為を要求している (`brief.md:5-8`)。「これを実測で閉じる」「未測定の tail」という表現も、既存値の再掲より、指定座標を一つの比較可能な新規 campaign で閉じる読みが自然である。

**real — 既測 4 点の存在自体は正しい。** provenance から 3 workload 全てで 150、200、300、500 µs の throughput と abort 率、`CCBENCH_TRACE=0`、同一 repository/CCBench commit を確認した。各 workload は job 951689、951690、951691 の別 job である。750 はなく、1000 行は全 workload で `included=false, reason_code=F718` だった。

**refuted — 「真に未測定なのは 750 の 1 点だけ」は誤り。** 依頼座標として未充足なのは 750 と真の固定 1000 の 2 点である。1000 は既測ではなく、現符号化で固定 0 へ衝突して測定不能である (`patches/silo-backoff-fixed.patch:69-73`)。

**real — 既測 4 点の再測定には数値以外の価値がある。**

- 750 と同じ新規 job 内で並べることで、機体、時刻、toolchain、source、cache、測定順の差を排除できる。
- 既測値との再現性を確認できる。
- 6 点を一つの campaign identity、WAL、completion receipt へ束縛できる。
- tail の傾きを別 run の 4 点と新規 1 点の継ぎ合わせで説明する必要がなくなる。

したがって、**依頼どおり既測 4 点も含めて新規測定すべきであり、親の 0 job 推奨は誤り**である。ただし真の 1000 は現行不変条件のままでは実行不能なので、5 点の正確な再測定と 999 の代替測定を行っても「6 点完了」とは扱えない。

## 命題 2 — 凍結 pin 閉包

**refuted — 親の結論「既存格子を書き換えない」は正しいが、pin 閉包の列挙と現在状態の説明は不完全である。**

親の経路は次のとおり確認できた。

- **real — `EXTENDED_SWEEP_US`。** 定義は `orchestrator/campaign/backoff_extended_sweep.py:37-40`。genome と順序へ入る (`:282-306`)。`search_config.sweep_us` と `measurement_order` を通じ campaign identity に入る (`:327-355`)。identity は exact 5 key と search_config 全体の正準 SHA-256 から導かれる (`orchestrator/campaign/ident.py:196-235`, `orchestrator/campaign/campaign_lock.py:19-21`)。着地済み identity は `docs/paper-story/figures/README.md:175-179` と provenance に一致する。
- **real — extended grid の直接 test pin。** 上端だけでなく、追加点の literal、adaptive 状態集合、重複なし、点数、測定順まで pin される (`orchestrator/tests/test_backoff_extended_sweep.py:152-172,371-382`)。
- **real — `SWEEP_US`。** S1 generator は候補集合完全一致を要求し (`orchestrator/campaign/s1_known_axes_freeze.py:384-420`)、`_module_source` で `backoff_sweep.py` 全 bytes の SHAを保存する (`:421-423`)。literal golden は `orchestrator/tests/s1_expected_goldens.py:30-31`、直接検査は `orchestrator/tests/test_s1_known_axes_freeze.py:546-549`。
- **real — freeze tree の job 内 pin。** B-10 job は `output/s1-freeze` と `output/s8b-freeze` の合同 hash を前後で照合する (`tools/pegasus/b10_backoff_grid.sh:552-595`)。

親が落とした束縛は次である。

- **real — report の閉集合。** 31 点と静的集合の完全一致を要求する (`orchestrator/campaign/backoff_extended_sweep_report.py:83-96`)。
- **real — T-1941 consumer。** 独立な `EXPECTED_FIXED_GRID` と lock 内の `sweep_us` を完全一致で検査する (`orchestrator/campaign/backoff_requested_us.py:69-72,451-475,597-607`)。
- **real — plot/provenance の key pin。** schema、29/28 点格子、group ID、campaign identity、全入力 SHA が literal 化される (`tools/plotting/plot_b10_extended_backoff.py:33-46,75-155`, `orchestrator/tests/test_b10_extended_figure_provenance.py:42-117`)。
- **real — official perf の role pin。** path だけでなく surface role `R`、関数名、call 名、回数の tuple が閉じている (`orchestrator/tests/test_official_perf_closure.py:95-125,807-823`)。
- **real — GeneratorId の閉集合。** 新しい generator 名を足すと build-admission policy identity 全体が変わる (`orchestrator/campaign/build_admission.py:107-116,458-466`)。段 2 が既存 `BACKOFF_SWEEP` を再利用する判断は正しい。
- **real — receipt schema key。** 既存 completion schema は consumer が exact 名で要求する (`orchestrator/campaign/backoff_requested_us.py:563-569`)。
- **refuted — xdist group の追加 pin。** key 側から検索したが、今回の格子、driver、B-10 path を固有 group 名へ結ぶ xdist 契約は見つからなかった。

重要な現在状態も親から漏れている。**real — S1 source SHA pin は既に live bytes と不一致である。** `backoff_sweep.py` の現 SHA は `42101e...`、freeze 記録は `4e7fa9...` (`output/s1-freeze/known_axes_freeze.json:151-155`)。generator 自身も現 SHA `8fea2b...` に対し記録 `1d4d45...` である。`verify_document` は `:868-889` で拒否する。したがってこれは歴史的 pin ではあるが、現在「検査が緑だから一切編集不能」という説明にはできない。`SWEEP_US` 自体は独立 golden があるため変更不可という結論は変わらない。

追加だけで赤になる面は以下である。

- **real — 新しい perf predicate を持つ Python driver:** production file inventory が検出する (`test_official_perf_closure.py:516-550,888-905`)。
- **real — 新規登録した Pegasus path:** `test_hooks.py:2572-2640,2641-3044,3445-3456` と runbook 投影検査 `tools/check_docs.py:4404-4438` が同期しない限り赤。
- **refuted — 未使用の別格子定数を追加するだけ:** 自動的に赤にする既存検査はない。既存 `EXTENDED_SWEEP_US` を変えた場合だけ `test_backoff_extended_sweep.py:152-172` が赤になる。
- **refuted — 新しい別名 artifact を追加するだけ:** generic な閉集合検査はない。既存 B-10/figure artifact 名を変更すれば `test_backoff_extended_sweep.py:578-583,794-802` と plot/provenance literal が赤になる。
- **refuted — 未登録 job body file を置くだけ:** pytest の exact file inventory は見つからない。ただし実行時には未登録 path として拒否される (`hooks/guard_bash.py:609-623,1200-1210`)。

## 命題 3 — 登録簿を触るか

**real — 段 2 の既存 path 再利用案なら、登録簿は機械契約上触らずに済む。**

registry は明確に path を key にする。loader は `entries` の各 key を canonical repo-relative path として検査し、path から entry への mapping を返す (`tools/pegasus_admission_registry.py:69-77,93-117,120-136`)。hook も exact path lookup だけを行う (`hooks/guard_bash.py:609-623`)。対象 file の内容 SHA は見ていない。

**real — 既登録 path の内容変更だけでは registry 更新は不要。** `test_hooks.py:3445-3456` が比較するのは registry の path と 4 field であり、対象 script の bytes ではない。既存 `b10_backoff_grid.sh` と `submit_b10_backoff_grid.sh` の class、primary gate、evidence が変わらない限り更新不要である。現在の `reason` は B-10 専用に見えるが、reason は実行許可の判定値ではない。説明を更新すれば registry と `test_hooks` literal の両方を変える必要が生じるため、本 scope では据え置きが最小である。

**real — runbook は二重管理である。** `docs/pegasus-runbook.md:484-487` が `(path, class, evidence)` の集合完全一致を明記し、実装は `tools/check_docs.py:4404-4438,4541-4587` で検査する。

新規 path 追加時の必須同期は最低 3 file である。

- `tools/pegasus/admission_registry.json`
- `orchestrator/tests/test_hooks.py`
- `docs/pegasus-runbook.md`

その path を運用手順として `tools/pegasus/README.md` に記載するなら、宣言表との一致検査 (`tools/check_docs.py:4682-4802`) のため同 README も必要となり、計 4 file になる。

**real — t2189 の実差分は registry の既存 2 entry の `reason` だけである。** `probes/t2187_adaptive_const_probe.pbs` と `.py` の `reason` を変更し、class/gate/evidence/path は変えていない。

**refuted — 本 wave の専用 path 追加が必ず JSON の同じ位置で衝突する、とはいえない。** 通常の `tools/pegasus/t2266_*` と `submit_t2266_*` は root-level の別位置へ整列され、t2189 が編集する `tools/pegasus/probes/t2187_*` (`admission_registry.json:172-183`) とは同じ位置ではない。`tools/pegasus/probes/t2266_*` と命名した場合だけ、t2187 と t293 の間へ入り直接隣接する。段 2 の既存 path 再利用案なら差分自体がないため競合しない。

## 命題 4 — 実装量と scope

**refuted — B-10 再利用という骨格は scope に合うが、段 2 プラン全体はそのままでは不足と過剰が混在する。**

測定成立に必要で、段 2 が正しく含めたものは、既存 B-10 path の opt-in mode、別格子と別 campaign identity、既存 condition gate と build authority の再利用、trace-disabled bench、3 workload の同時 fan-out、WAL からの数値出力である。

削るか縮めるべきものは次である。

- **real — `s2-plan.md:83` の大きな private-helper 切り出しは一般化寄り。** 既存 `run_workload` の本体を全面移動せず、mode ごとの point/config 選択を最小分岐で注入できるなら、その方が scope に合う。
- **real — `s2-plan.md:91` の「既存格子と既存 identity 不変」の新規重複検査は削減可能。** 既に `test_backoff_extended_sweep.py:152-172,371-396` が格子・順序・identity 感度を検査する。必要なのは T-2266 mode の直接的な格子、CLI、job routing の最小テストだけである。
- **refuted — 既存 gate の維持は scope 外の追加 gateではない。** `_require_backoff_condition_gate` と既存 pipeline correctness をそのまま通すことは規律 2 の維持に必要である。

欠けているものは次である。

- **real — 1000 の未達扱い。** 999 を測っても 1000 の測定にはならない。`T2266_REQUESTED_US` へ 999 を入れる命名も不正確で、original request と realized grid を別 field にする必要がある。
- **判定不能 — baseline の identity。** 段 2 は固定 0 を baseline とするが (`s2-plan.md:79`)、固定 0 は no-backoff ではない (`test_backoff_extended_sweep.py:169-180`)。投影された依頼には baseline の flags が書かれていない。決着には baseline の `BACK_OFF` と `BACKOFF_FIXED` を明示して同じ trace-disabled job で測る必要がある。
- **real — run kind の provenance 束縛。** `s2-plan.md:87-89` は qsub env への mode 伝達だけで、submit event、failure receipt、reservation、completion への記録がない。現行生成箇所は `submit_b10_backoff_grid.sh:98-161` と `b10_backoff_grid.sh:31-137,384-416,596-623`。全 receipt に exact run kind を保存しなければ、どの mode を実行した成果物か閉じない。
- **real — report の実装先が未指定。** `s2-plan.md:85` は `.dat` と JSON を出すとだけ述べる一方、`s2-plan.md:87` は既存 report を実行しない。driver 内で書くのか、既存 report に opt-in mode を足すのかを file:function 単位で確定する必要がある。
- **real — 完了条件が未定義。** T-2266 mode では exact な expected genome 数、全 commit、abort なし、report 作成済みを completion 前に検査する必要がある。これは新しい科学 gate ではなく、依頼した測定が完走したことの最低限の確認である。

## 段 2 プランへの所見

- **refuted — `s2-plan.md:57-62,105,115,121-133`:** 「既存再解析だけ」「0 job 推奨」は依頼の測定行為と同一 job 条件を落とす。削除すべき。
- **refuted — `s2-plan.md:79,117`:** `T2266_REQUESTED_US` に 999 を含めている。要求集合 `(150,200,300,500,750,1000)` と実現集合を分離すべき。
- **判定不能 — `s2-plan.md:79`:** 固定 0 を baseline とする根拠がない。`backoff_extended_sweep.py:285-293` は no-backoff、adaptive、fixed を別点としている。baseline flags の裁定が必要。
- **real — `s2-plan.md:81`:** 別 search_config に grid、順序、F718、requested/realized endpoint を入れる方針は campaign identity の仕組み (`ident.py:196-229`) に合う。
- **refuted — `s2-plan.md:83`:** 全実行本体の helper 化は最小変更より広い。mode 選択部だけへ限定すべき。
- **refuted — `s2-plan.md:85,87`:** T-2266 report を誰が生成するか欠落している。既存 report は exact 31 点を要求する (`backoff_extended_sweep_report.py:83-96`) ため、そのまま流用できない。
- **refuted — `s2-plan.md:87-89`:** `B10_RUN_KIND` の qsub env 束縛だけでは不十分。submit、failure、reservation、completion の全 receipt へ含める必要がある。
- **real — `s2-plan.md:91`:** T-2266 格子と branch routing の直接テストは必要。ただし既存格子 pin の重複追加は不要。
- **real — `s2-plan.md:101,107`:** 新規 Pegasus path を作らず registry を避ける結論は正しい。
- **refuted — `s2-plan.md:119`:** 専用 path は t2189 と同じ JSON 位置で必ず衝突するわけではない。競合理由は「同じ file」までであり、位置は命名依存である。

## 総括

- 親の 0 job 推奨は依頼の scope を縮小しており、誤り。
- 150、200、300、500 も、750 と同じ新規 job 内で再測定すべき。
- 750 と真の固定 1000 が未充足であり、「未測定は 750 だけ」は誤り。
- 現行符号化では真の 1000 は測れず、999 は代替点でしかない。
- 既存 `SWEEP_US` と `EXTENDED_SWEEP_US` は変更しない結論は正しい。
- 親の pin 列挙は report、consumer、plot、schema、role、GeneratorId、identity key を落としている。
- 既存 B-10 driver/job/submitter の opt-in 再利用なら admission registry は変更不要。
- 新規 path の registry 同期は最低 3 file、README に運用記載するなら 4 file。
- 段 2 は baseline 定義、run kind の全 receipt 束縛、report 実装先、完了条件が不足。
- 実行本体の全面 helper 化と重複 pin test は scope に対して過剰。
- pytest は実行していない。所見は指定資料、live source、hash 比較、git diff の静的検査に基づく。