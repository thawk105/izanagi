## 所見一覧 (real / refuted、各 1 行の成果物影響つき)

**P2 は条件付きで成立する。対象 CLI の新規 baseline attempt に帰属する WAL は、stock supply の緑と family admission の間接証拠になる。ただし、両腕の緑や成功 reason の実測記録ではない。**

| ID | 分類 | 所見と成果物への影響 |
|---|---|---|
| R1 | real | baseline meaning は `unestablished`。限定しないと README が「両腕の緑」「意味の確立」を過大に主張する。段 2 は既に認識している。 |
| R2 | real | 成功 arm record は失われる。WAL から `stock-inert-preprocess-root-location-only` という個別 reason を実測値として書くことはできない。 |
| R3 | real | 関門拒否時も下位 detail が失われる。README が全段について compiler rc・stderr・argv まで保存できると約束すると、実際の証拠粒度を超える。 |
| R4 | real | prefix・proxy・TMPDIR は実際の入力と到達成否を変えうる。「環境供給なので受理結果も一切不変」とすると規律 2 の説明が誤る。 |
| R5 | real | 最小 screening の成功は通常全点 family の成功を含意しない。「sweep 全体を再開可能」と一般化すると被覆外へ主張が広がる。 |
| R6 | real | P1 は投入元 CCBench を一時 patch する。「指定領域以外に書かない」という brief の不変条件と成果物の実行説明が衝突する。 |
| R7 | real | `_assert_single_tenant` は特定プロセスの検査である。「計算ノード全体の単独使用を証明」と記録すると観測範囲を超える。 |
| R8 | real | 段 2 の赤分類表は screening 前の source identity・perf preflight を明示していない。そこで止まった結果を関門赤へ誤分類しうる。 |
| F1 | refuted | 今回の baseline で request が空になり関門を素通りする経路はない。新規 baseline WAL の意味はこの点で崩れない。 |
| F2 | refuted | baseline の WAL replay・`force=True`・build cache hit による関門迂回はない。新規 attempt の照合を維持すれば過去の緑を代用しない。 |
| F3 | refuted | stock checkout 失敗や prepare 失敗を握り潰して評価へ進む経路はない。これらを関門通過として扱う必要はない。 |
| F4 | refuted | 両側が空の preprocess でも stock supply が緑になる、という攻撃は成立しない。非空出力と依存閉包の検査がある。 |
| F5 | refuted | 未使用の外部 output root への今回の書込みが、既存 official WAL・freeze・選択を自動更新する経路は確認できない。新 root 内の certified record 作成とは区別する。 |

## (P2) 緑 record の恒真性

**空 request と early return。** `_condition_requests_for_genome` が空になる条件は `genome.flags ∩ DEFINE_SPECS` が空であること。空なら helper は `None` を返す。しかし今回の baseline は `BACK_OFF=0, BACKOFF_FIXED=-1` を保持し、`BACKOFF_FIXED` は spec に存在する。したがって stock request が 1 件発行される。根拠は `backoff_sweep.py:257,409`、`condition_meaning_gate.py:74–77`、[screening_driver.py:93](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/screening_driver.py:93)。

`evaluate_candidate` の skip は `not force && terminal && !retryable_abort` の場合だけで、baseline は `force=True`。関門呼出しはその後、pipeline 呼出しと `try` の前にある。`force` は関門を無効化しない。根拠は `backoff_sweep.py:321–337`、[screening_driver.py:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/screening_driver.py:592)。

さらに `prepare_screening_campaign` は baseline の `bench-done` 件数の増加と、最新 bench より後の commit を要求する。ただし、その出口検査自体は attempt ID の一致まで見ていない。**段 2 が追加した「同一 variant・同一 `build_attempt_id`」の成果物照合は残すべきである。** `screening_driver.py:489–508`。

**stock checkout と prepare。** `patchharness.checkout` は `git worktree add` 非ゼロで `RuntimeError` を送出し、body の例外も抑止しない。cleanup の補助失敗を無視する箇所はあるが、checkout 失敗を成功へ変えるものではない。`patchharness.py:364–382`。呼び手も例外を捕捉せず、関門は candidate-abort 捕捉の外にある。`screening_driver.py:275–282,609–618`。

prepare も同様である。configure/target 失敗は `MasstreeFetchContentError` として伝播し、arm evaluator に到達しない。したがって **「prepare 失敗による関門判定未到達」** と記録する。`buildcache.py:2093–2104`、`screening_driver.py:203–215`。

**空 preprocess による退化。** supply は実 configure と owner TU の preprocess を両側で実行する。その過程で次を検査している。

- 要求 macro の供給と値：`condition_meaning_gate.py:2232–2249`。
- preprocess 出力が非空：同 `2284–2287`。
- 依存閉包に owner TU と patch 対象が含まれる：同 `2292–2305`。
- compiler identity と比較可能な compile argv が一致する：同 `2612–2624`。
- 配置差だけとするには、残差なし・置換 1 件以上・root 依存 builtin の存在が必要：同 `2452–2455`。

よって空出力同士の一致は緑にならない。[非空・依存閉包検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/condition_meaning_gate.py:2284)

ただし stock supply の成功 reason は、完全一致の `stock-inert-preprocess-identical` と配置差だけの `stock-inert-preprocess-root-location-only` の二択である。同 `2663–2699`。**WAL だけでは今回どちらだったか識別できない。前回 insight の reason を今回へ転記してはいけない。**

**meaning と admission。** baseline に渡す `fixed_declarations.get(-1)` は `None`。mapping が非負値だけを対象にするためである。`backoff_sweep.py:98–131,325–327`。meaning evaluator はこの場合 `unestablished / meaning-witness-undeclared` を発行する。`condition_meaning_gate.py:3335–3341`。

family の条件は supply が全件 green、meaning が全件 green または unestablished。これは既存の受理条件であり、本 wave が緩めるものではない。[condition_meaning_gate.py:4098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/condition_meaning_gate.py:4098)

## 直接証拠の補強手段

**P1 の argv と既存出力をそのまま使う場合、関門の成功を直接記録する証拠は無い。** 次の証拠は帰属や順序を補強するが、arm record の代用にはならない。

| 手段 | 示せる範囲・限界 |
|---|---|
| stdout の `built/verify/bench` | 後続段への到達。関門固有の開始・終了時刻は出していない。`pipeline.py:2082,1517`。 |
| dispatch receipt・時刻列 | request、ノード、child rc、会計照合と外側の順序。`_job_trace` 自身も attestation・acceptance input ではないと明記。`dispatch_compute.py:710–717,1689–1697,4142–4146`。 |
| WAL の `ts` | 各 WAL record の発行時刻。関門時刻ではない。`wal.py:1587–1594`。 |
| `/scr/izanagi-screening-condition-gate-*` | 生存中に観測できれば prepare 用領域の作成痕跡。ただし領域は prepare 前に作られるので admission 成功は示さない。正常時は helper を抜ける時点で削除され、job 終了まで残らない。 |
| Python `-X` | 当環境の 3.10 の `-h` を確認。`importtime` は import、`tracemalloc` は割当、`faulthandler` は障害時の情報であり、正常な gate 呼出し・戻り値の記録にはならない。 |
| `IZANAGI_S4_EVIDENCE_ROOT` | **本経路では効かない。** production の読取は `p3_s4_loop.py:460`。screening driver には保存処理がない。 |

production 無変更という条件だけなら、補強手段はある。

- **外部 `strace` の子プロセス追跡。** `-f -ttt -s 8192 -e trace=process` 等で、screening 専用 base を渡す configure と requested/stock の owner preprocess の起動・終了を保存できる。これらは実行の直接痕跡になるが、family の戻り値は依然 WAL とコード構造から推論する。ローカルには `/usr/bin/strace` がある。計算ノードでの利用可否は未確認。計測への干渉があるので採用時は instrumentation 付き実測として記録し、性能比較に流用しない。
- **標準 `trace` の行実行ログ。** `--trace --timing --no-report` なら関門内部の通過行を stdout に残せる。ただし、このまま P2 に採用してはいけない。Python 3.10 の [trace.py:732](/usr/lib/python3.10/trace.py:732) は `SystemExit` を捕捉し、`cProfile` も [profile.py:60](/usr/lib/python3.10/profile.py:60) で捕捉する。CLI の `sys.exit(main(...))` の非ゼロを外側 rc に保持しないためである。

追加計測や観測実装を must-fix にはしない。P1 のままなら README に「関門実行・成功は、実行 identity に対応するコード構造と新規 WAL による間接証拠」と明記すればよい。

## 規律 2 / 7

**規律 2。** env 前置自体は、関門の判定式・既定値・stock 比較・admission 条件を変更しない。しかし、環境を変えても実効的な受理結果が不変とは言えない。

| 入力 | 実際の作用 |
|---|---|
| `IZANAGI_OFFICIAL_OUTPUT_ROOT` | 出力先と root 検査の成否を変える。関門式や correctness 条件は変更しない。 |
| `CMAKE_PREFIX_PATH` | header/library の探索を変える。build identity の `dependency_prefix` にも入る。`buildcache.py:2624–2636,2681–2685,1330`。 |
| proxy | FetchContent の取得到達性を変える。取得できず失敗した入力が判定まで進めるようになる。 |
| `TMPDIR` | 一時 source/build/base の実パスと作成可否を変える。関門は配置由来の差を限定的に扱うので、単なる記録先変更とは言い切れない。 |
| `PATH` | 実際に選ばれる実行体を変えうる。toolchain 観測と実行時の値を記録する必要がある。 |

適切な説明は「現行判定式・既定値を維持したまま、この依存・取得・一時領域の条件で到達性を実測した」である。D1784 の「制御された拡張」を、環境も含めた不変性へ読み替えない。

correctness は別途残る。baseline は `screening=None` で verification を通し、commit は certified かつ非 aborted、bench 完了を要求する。WAL writer も live commit receipt を検証する。`pipeline.py:2390–2440,2530–2535,2571–2575`、`wal.py:1297–1321`。

**既存成果物への影響。** 未使用 root `O` を与えれば、campaign は `O/campaigns/<id>`、WAL はその `runs/wal.jsonl` に作られる。[layout.py:248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/orchestrator/campaign/layout.py:248)、`layout.py:203–208`。writer は渡された layout の WAL を開く。`wal.py:1274–1278`。

本経路には既存 root の WAL、freeze、選択ファイルを書き換える呼出しはない。最後のランキングも stdout への表示である。`backoff_sweep.py:496–508`。ただし、**新 root 内には通常の official/certified campaign record を作る**。「repo 外なので非認証の probe」とは説明できない。

**規律 7。** README では次を分ける。

- 実測事実：日時、request、ノード、argv/env、実行 tree・HEAD・pin・sha256、campaign/attempt、WAL、終了状態。
- コードからの推論：その実行コードでは新規 baseline WAL の前に stock supply と admission が必要だったこと。
- 未保存・未測定：arm JSON、正確な成功 reason、全点 family、将来 HEAD の到達性。

`build-done` には toolchain、toolchain record hash、binary の full hash、cache 使用、configure/build argv があるので、bench/commit だけでなくこれも保存すると「その道具」の記録を補強できる。`pipeline.py:2062–2081`。

過去測定は現在のコードとの差だけで無効にならず、今回の緑も将来コードの保証にはならない。

## README の主張の限定

「screening 関門が緑になった」と名乗る条件を、次の証拠組で定義する。

1. 未使用 official root と今回の dispatch request を対応付ける。
2. `campaign.lock` が `write-heavy`、最小 screening、実行契約を示す。
3. baseline の `build-start.payload.genome` が `BACK_OFF=0, BACKOFF_FIXED=-1` を示す。
4. **同じ variant・`build_attempt_id`** に新規 `bench-done` と後続 `commit` があり、対応する build/verification 記録も保存されている。
5. dispatch の `result.stage=child`、`child_rc=0`、receipt の `outcome.kind=child`、`rc=0`、`accounting_verified=true` を確認する。
6. stdout の campaign ID・結果と WAL が一致し、実測時コードが静的推論の対象と対応する。

推奨する本文は次の形である。

> 当該実行の新規 baseline attempt が bench-done と commit に到達し、正規 CLI が正常終了した。実測時コードの制御フローから、screening baseline の stock supply が緑で family admission を通過したと判断する。これは間接証拠であり、arm record は未保存である。baseline meaning は宣言未設定による unestablished で、成功 supply reason の二択は識別できない。

| 主張してよい | 主張してはいけない |
|---|---|
| 当該環境・コードで CLI から baseline stock supply/admission まで到達した | 両腕とも green、全 macro の意味が確立した |
| baseline の新規 measured commit が得られた | rc=0 だから候補も certified commit した |
| stock owner TU の preprocess 比較が現行条件を満たしたと推論する | 今回の reason が必ず `root-location-only` だった |
| 1 workload・2 genome の経路を観測した | 通常 7 値 family、他 workload、他 driver も通る |
| 実測時点の到達性が確認された | 将来 HEAD、別依存環境、A-5 と等価である |
| baseline と候補の結果を別々に記録する | adaptive backoff が実行時に動作した、性能優位を証明した |

候補の `screen-slower-than-floor` は rc=0 と両立する。`backoff_sweep.py:535–547`。また `stale-baseline` なら bench-first screening を無効化して verify-first へ進むため、**条件関門通過と性能 screening の発火も別々に記録する**。`pipeline.py:2326–2350`。

baseline commit 後に候補で失敗した場合、baseline の関門通過まで否定しない。ただし今回定義した「CLI 全体正常終了」の完了条件は未達とする。

## 赤のときの記録粒度

| 段 | 残せる識別子 | 限界 |
|---|---|---|
| dispatch・launcher | outcome、stage、rc、request、stderr | 子未到達なら関門結果は未到達。 |
| site・calibration・attestation | 例外型、本文、traceback、CLI rc | execution receipt 自体はこの CLI から永続化されない。 |
| patch・stock checkout | `RuntimeError`、git rc、stderr 末尾、pin、traceback | stock checkout 失敗を `stock-tree-unavailable` arm と捏造しない。 |
| driver/screening prepare | `MasstreeFetchContentError`、configure/target、下位例外、rc が含まれる場合はその rc | 引数検査等は prepare のラップ前に失敗し、別例外型となることもある。 |
| driver gate | `RuntimeError` と `macro=status/reason` | **arm 名・requested value・arm detail が落ちる。** 同じ macro の複数 request を本文だけで特定できない。 |
| screening gate | `ConditionMeaningGateError`、外側 code、`macro:arm=status/reason` | **下位 rc・stderr・argv・digest は通常残らない。** |
| screening 前 source identity | `RuntimeError` 等、traceback | gate 未到達。段 2 の分類表へ追加する。 |
| screening 前 perf preflight | `PerfPreflightError` と理由、または temp 作成等の例外 | gate 未到達。単なる perf unavailable と probe error を分ける。 |
| build・correctness・bench | WAL abort reason、attempt、error/verification/rep の payload | 保存された項目だけを書く。下流未到達を別の赤にしない。 |
| timeout・強制終了 | scheduler/accounting、最後の durable record、ログ | 最後の記録から「中断位置」を示し、未観測の関門 reason を補完しない。 |

driver の縮約は `backoff_sweep.py:218–227`、screening の縮約は `screening_driver.py:240–249`。下位 process の detail は `condition_meaning_gate.py:1610–1621` で生成されても、`2597–2605` で arm record に移された後、上記 driver 境界で捨てられる。

したがって、一次資料 §1 の**段名と拒否 reason**程度は概ね残せるが、§1.1 の成功 arm 表や §1.2 の compiler stderr 原文と同じ粒度を全段で約束することはできない。特に driver gate と screening gate が不足する。

追加すべき前段の根拠は `screening_driver.py:582–599`、`source_digest.py:2382–2411`、`orchestrator/calibrator/perf_preflight.py:261–269`。stdout/stderr は receipt の末尾抜粋だけでなく原本を保存する。`dispatch_compute.py:1761–1780`。

## 親 brief の誤り

| 前提 | 判定 |
|---|---|
| 1：CLI は薄い入口 | **refuted：誤りは確認できない。** `main` は引数を `run_workload` に渡す。`backoff_sweep.py:511–531`。 |
| 2：A-5 はそのまま使えない | **refuted：誤りは確認できない。** 起動は screening 無指定、finalize は 8 genome・abort ゼロを要求する。`a5_second_boot_backoff_sweep.sh:581–583,641–653`。 |
| 3：generic の環境・cwd・保護 | **real：interpreter の一般化に注意。** dispatcher の選定と任意 argv の `python3` 解決は別。段 2 の子 `python3.10` 明示は妥当。request directory だけの read-only は投入元を保護しない。 |
| 4：prefix roots に記録 | **real：その field については誤り。** 対象 pipeline は snapshot/外部 compiler input 設定を渡さず、`compiler_input_dependency_prefix_roots` は空になる。ambient prefix 自体は build identity に入る。 |
| 5：同版 prefix・過去使用 | **refuted：今回の静的検査では誤りを立証できない。** ただし同版から A-5 と同じ binary・link 成功を導くことはできず、brief も link 未測と認めている。 |
| 6：floor・required attestation | **refuted：構造上は支持。** floor は repo の env scope、Pegasus compute は required contract を使う。`layout.py:600–603`、`p2_2.py:218–253`。今回の通過実績ではない。 |
| 7：関門は無条件で走る | **real：関数一般の記述としては過大。** 空 request・terminal skip がある。「今回の baseline は非空 request、force=True なので関門を経る」に修正する。request の実測値自体はコードと一致する。 |
| 8：単独性 | **real：保証範囲が狭い。** `pgrep -af ycsb_.*\\.exe` は他の高 CPU 処理や scheduler 排他を証明しない。`runner.py:382–405`。00:33 の queue 数は過去の観測として扱い、現在値へ一般化しない。 |

ほかに次の訂正が必要である。

- **P1 の書込み不変条件との衝突は real。** `patchharness.applied` は投入元へ apply/revert する。`patchharness.py:255–263`。段 2 の指摘を支持する。
- **P5 の上限説明は real。** prepare は driver・baseline・候補の計 3 回、完全 build は trace/perf の計 4 回。関門の 120 秒は各 subprocess、通常 build の timeout 既定は `None`。90 分は予算であって各段上限から導かれる保証ではない。
- **「これで sweep driver の新規測定を再開できる」は real の過大一般化。** 正確には最小 screening 経路の生死確認である。全点 family の成功は別であり、screening 関門の過去の赤から非 screening 分岐の停止まで導くこともできない。`backoff_sweep.py:452–494`。

## must-fix / should-fix / nit

**must-fix**

- R1・R2：緑の定義を stock supply と family admission に限定し、meaning 未確立・成功 reason 未保存を明記する。段 2 の限定を最終 README まで維持する。
- R3：赤の記録粒度の約束を修正し、prepare 未到達・関門拒否・失われた detail を区別する。
- R4・R5：環境供給を結果不変と説明せず、全点 sweep・A-5・将来コードへ一般化しない。
- R6：P1 と投入元への書込み禁止を段 4 で整合させる。終了後 clean だけではこの不変条件を満たさない。
- P2 の新規 root・同一 attempt・会計照合済み CLI rc の条件を落とさない。

**should-fix**

- R7：単独性の観測範囲を明記する。
- R8：source identity・perf preflight を赤分類表に追加する。
- WAL 全文と `build-done` の toolchain/binary 証拠を保存する。
- 前提 4 の prefix roots、前提 7 の「無条件」、P5 の回数・timeout 説明を訂正する。

**nit／追加実装を要求しない事項**

- tracer の採用、arm record 永続化、追加負例実測は完了条件にしない。
- 関門と計測 build の `config.h` 非束縛、masstree autotools の compiler 非束縛は既知限界として残す。今回の修正へ拡張しない。

## 総括

**P2 の恒真性攻撃は、今回の baseline と新規 attempt に限定すれば成立しなかった。** 一方、緑の意味・成功 reason・赤の詳細・被覆範囲には明確な限界がある。段 2 の限定付き P2 を採用し、上記の記録条件と主張の修正を反映するのが妥当である。

指定 7 ファイルはすべて読了した。静的検査のみで、実測・pytest・編集・job 投入は行っていない。補助探索で `orchestrator/patchharness.py` と `orchestrator/campaign/perf_preflight.py` は存在せず、それぞれ実ファイル `orchestrator/campaign/patchharness.py`、`orchestrator/calibrator/perf_preflight.py` を確認した。