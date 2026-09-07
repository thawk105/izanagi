## 位置除外の意味

現行実装は、生の `events` から `zip(events, events[1:])` を作り、`current` の割当を `following` の窓へ対応させています。[backoff_counterfactual_analysis.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:375) [backoff_counterfactual_analysis.py:381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:381)

v2 の「`seq = 0` を位置だけで除く」は、`seq` の値で任意の event を選別するのではなく、連続性検査済みの生列から `analysis_events = events[1:]` を作ること、と実装するべきです。

- 生 event 数を `m` とすると、残存 event は raw `event1 ... event(m-1)` の `m-1` 件です。
- 対は `zip(analysis_events, analysis_events[1:])` とし、最初は必ず `(event1, event2)`、最後は `(event(m-2), event(m-1))` です。
- raw `event0` は `current`、`following` のどちらにも現れず、分母にも分子にも使われません。
- 残存 outcome 対は `m-2` 件なので、`outcome_count = len(analysis_events) - 1`、`index = 0 ... m-3` と残存集合基準で数え直します。
- `membership` は `current` と index/count を受け取るため、raw `event1` を `index=0` として渡します。[backoff_counterfactual_analysis.py:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:377) [backoff_counterfactual_analysis.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:383)

数え直しは必須です。単に raw の対から `(event0,event1)` だけを filter すると、`membership` が見る index は `1 ... m-2`、count は `m-1` のままです。時間 block は `(4 * index) // count` なので、この一つずれが層を変えます。[backoff_counterfactual_analysis.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:660)

例えば現行 fixture のように生 event が25件なら、正しい残存 outcome は23件です。正しく rebasing した index `0..22`、count `23` の block 件数は `6,6,6,5` ですが、raw index `1..23`、count `24` のままなら `5,6,6,6` になります。先頭の対が第1 blockから失われ、末尾側が1件増えます。

`assignment_rate_all_events` は明示的に生の全 event を記述する診断値なので、[backoff_counterfactual_analysis.py:435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:435) は変更せず、推定量に使う列だけを除外後集合へ切り替えます。

## 0 commit 判定の範囲

現行の `any(... for event in events)` は raw `event0` を含む全 event を見ています。[backoff_counterfactual_analysis.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:389)

変更後は次の順序にします。

- [backoff_counterfactual_analysis.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:379) で raw `events` を保持したまま `analysis_events = events[1:]` を作る。
- [backoff_counterfactual_analysis.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:380) 以降の pair、index、count を `analysis_events` 基準にする。
- [backoff_counterfactual_analysis.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:389) を `any(event["window_commits"] == 0 for event in analysis_events)` にする。

ここは `selected` だけを調べてはいけません。層別 membership に入らなかった event や、最後の `following` event にある 0 を見逃すためです。位置除外後に残った run 全体を調べ、`seq >= 1` の残存 event に 0 が一件でもあれば、従来どおり `window_commits_zero` でその run、ひいては主判定全体を inconclusive にします。[backoff_counterfactual_analysis.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:389) [backoff_counterfactual_analysis.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:456)

これは事前登録 v1 の「処置後 outcome による個別除外をしない」という規則を、位置除外後の集合にそのまま適用する変更です。[backoff-counterfactual-preregistration.md:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:214)

## 事前登録 sha の 2 分割

現行の単一 `PREREGISTRATION_SHA256` は、解析規則の file hash と測定成果物内の記録を兼用しています。[backoff_counterfactual_analysis.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:17)

次の2定数へ分けます。

- `MEASUREMENT_PREREGISTRATION_SHA256_V1`
  - 値は逐語の `ee7617f57bf6816fd8bfb42b5830926be1174ebcca617ed122c3fbca62f127a6`。
  - `_load_artifact` の top-level `counterfactual_preregistration` と、各 row の同 field にだけ使います。[backoff_counterfactual_analysis.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:300) [backoff_counterfactual_analysis.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:318) [backoff_counterfactual_analysis.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:331)
- `ANALYSIS_PREREGISTRATION_SHA256_V2`
  - v2 文書の bytes を確定、先に commit した後で計算した SHA-256 の逐語値。
  - `analyze_counterfactual` が渡された `preregistration_path` を検査する箇所だけに使います。[backoff_counterfactual_analysis.py:570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:570)

取り違えを構造的に防ぐため、`_load_artifact(path, expected_hash=preregistration_sha256)` は廃止し、`_load_artifact(path)` 内で v1 定数を使います。[backoff_counterfactual_analysis.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:581) `_validate_row` の引数も `expected_artifact_hash` のように測定束縛だと分かる名前へ改めます。

`analyze_counterfactual` の実 SHA 計算は残し、比較対象だけを v2 定数へ替えます。返却結果の `preregistration.sha256` も、実際に検査済みの v2 file hashをそのまま記録します。[backoff_counterfactual_analysis.py:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:571) [backoff_counterfactual_analysis.py:675](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:675)

v1 は完全一致のままです。v1/v2の両方を許す集合、任意の64桁 hex、呼出し側指定値を受理する変更はしません。

## テスト設計

[test_backoff_counterfactual_analysis.py:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:21) の golden は、実装 module から取得せず、次の独立した逐語値へ分けます。

- `MEASUREMENT_PREREGISTRATION_SHA256_V1 = "ee7617f5...127a6"`
- `ANALYSIS_PREREGISTRATION_SHA256_V2 = "<確定した v2 の逐語 SHA>"`
- version 検査も `"izanagi-backoff-counterfactual-analysis/v2"` を逐語で比較する。

最低限、次を追加・更新します。

- `test_seq_zero_is_excluded_before_pairing_and_membership_is_rebased`
  - `_run_difference` に小さい手作り run と記録用 membership を渡す。
  - membership が raw `seq=1` を `index=0` で最初に受け、count が `len(events)-2`、最後の index が `count-1` であることを逐語の組で確認する。
  - commit 値から `(event1,event2)` を含む期待 estimate をテスト側で独立計算し、event0 の commit/assignment を変えても estimate が不変であることを確認する。

- `test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory`
  - 12 synthetic primary run の raw `seq=0` に `window_commits=0` を置く。
  - test-local の逐語 v1 oracle、すなわち raw 全 event の `any(window_commits == 0)` を実行し、v1 判定が `inconclusive` になることを確認する。
  - 同じ成果物を v2 public API へ渡し、`confirmatory_complete is True`、`decision == "equivalent"` を確認する。production に v1 compatibility mode は足さない。

- `test_seq_ge_one_zero_commit_remains_inconclusive_under_v2`
  - 残存列の最後の eventなど `seq >= 1` に0を置く。
  - `decision == "inconclusive"`、`theta_log is None`、`window_commits_zero` を確認する。最後の event を使えば、誤って `selected` の current だけを検査する変異も殺せます。
  - 現行の combined test [test_backoff_counterfactual_analysis.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:337) は missing-arm と zero-commit に分けると変異との対応が明瞭です。

- `test_artifacts_remain_bound_to_literal_v1_preregistration_sha`
  - top-level と全 row の `counterfactual_preregistration` を独立 golden の v2 SHAへ同時に変え、不適格になることを確認する。
  - top-level は v1のまま、1 rowだけv2にした場合も不適格になることを確認する。[test_backoff_counterfactual_analysis.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:326)

- `test_analysis_preregistration_file_is_bound_to_literal_v2_sha256`
  - 現行の file-bound test [test_backoff_counterfactual_analysis.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:462) を改名し、実 file hash が独立 v2 golden と一致すること、1 byte変更した file が拒否されることを確認する。

既存 fixture は [test_backoff_counterfactual_analysis.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:148) で現行文書の hash を計算して成果物へ入れています。v2化後はこれを必ず独立した v1逐語値へ変更します。変更しなければ全 fixture が「v2で測定された成果物」になり、厳格な v1 artifact pin によって既存 test が一斉に失敗します。

また、位置除外後の通常 fixture は割当数が現行の `12/12` から `11/12` になるため、[test_backoff_counterfactual_analysis.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:292) の期待値を更新します。post-treatment field が除外に使われない検査は event0ではなく、残存する raw event1以降へ移します。

## 副作用

- `ANALYSIS_VERSION` は `/v2` へ上げるべきです。推定対象集合、pair index、zero-commit 判定範囲が変わるためです。[backoff_counterfactual_analysis.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:15)
- live repo の pin は、現時点では定義 [backoff_counterfactual_analysis.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:15) と結果への出力 [backoff_counterfactual_analysis.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:674) だけです。既存テストに version の独立 pin はないので、public analysis testへ逐語 `/v2` assertionを追加します。
- `_validate_trace` の `seq` 検査は raw artifact が `0..n-1` で連続することを検証しています。[backoff_counterfactual_analysis.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:130) [backoff_counterfactual_analysis.py:151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:151) 解析時の位置除外とは別の admission 検査なので変更不要です。むしろこの検査があるため、安全に `events[1:]` を raw `seq=0` の位置除外と同一視できます。
- `acceptance_duration_ledger.json` への登録は本 wave では不要です。現時点で当該テストファイルの node ID は台帳に一件もありません。台帳欠落は test admission ではなく、個別 lookup が `None` を返し、既知 cost から導いた未知 costで並べ替えるだけです。[conftest.py:1534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/conftest.py:1534) [conftest.py:1594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/conftest.py:1594) 実測済みの完全 JUnit から台帳全体を再生成する別作業を、この変更へ混ぜません。
- `analyze_counterfactual` の live Python consumer は解析 module自身と当該テストだけです。公開 export もこの関数だけで、[backoff_counterfactual_analysis.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:13) CLI entrypoint はありません。親の inline 呼出し以外に更新対象となる consumer はありません。
- producer は将来の走行時に current文書の hash を計算します。[t2187_adaptive_const_probe.py:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:839) [t2187_adaptive_const_probe.py:2782](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:2782) 本 wave は producerを実行しないので、この SHA write path は変更不要です。

## 副題 not_certified

性能用の既存文字列は変更できません。`_performance_artifact_identity` が `kind == "performance-only-probe"` と同時に `not_certified == NOT_CERTIFIED` を exact比較しているため、[t2187_adaptive_const_probe.py:1744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:1744) [t2187_adaptive_const_probe.py:1765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:1765) [t2187_adaptive_const_probe.py:1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:1770) の文字列を変えると、既存の凍結性能成果物が `performance-artifact-invalid` になります。性能 plot loader も同じ旧文言を exact要求しています。[plot_t2187_adaptive_consts.py:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/plotting/plot_t2187_adaptive_consts.py:338)

修正は次の限定分岐にします。

- [t2187_adaptive_const_probe.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:65) の既存 `NOT_CERTIFIED` と旧性能文言は不変。
- 隣に `DIAGNOSTIC_NOT_CERTIFIED = "trace-enabled diagnostic runs only; no serializability check was run"` を追加。
- [t2187_adaptive_const_probe.py:2758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:2758) の `_artifact_contract_metadata` に mode別 `not_certified` を持たせる。
- [t2187_adaptive_const_probe.py:3313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3313) の共通代入を削除する。`kind` と `throughput_scope` は既に `backoff_trace` で分岐しています。[t2187_adaptive_const_probe.py:3308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3308)
- producer test [test_t2187_adaptive_const_probe.py:2079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2079) で診断文言と性能文言をそれぞれ逐語比較する。
- 少なくとも一つの性能 artifact fixtureは `probe.NOT_CERTIFIED` ではなく旧文言の test-local literal を使い、`_performance_artifact_identity` が引き続き受理することを確認する。[test_t2187_adaptive_const_probe.py:2008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2008)

解析器の `_load_artifact` は `not_certified` を admission field に含めていないため、既存の凍結診断成果物も拒否されません。[backoff_counterfactual_analysis.py:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:307)

この副題は本題と同じ commit に混ぜるべきではありません。本題は事前登録と解析規則の凍結順序を証明する commit chain、副題は将来の producer 文言修正です。v2 docs commit、解析器/test commitの後に、採用する場合だけ独立した副題 commitにします。

## 変更手順

- 本題1: [backoff-counterfactual-preregistration.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:8) に v2 の日付、変更理由、v1結果で見た構造量、`seq=0` 除外後の推定値は未観測であること、既存12成果物は v1 SHAに束縛されたままであることを追記する。
- 本題2: [backoff-counterfactual-preregistration.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:27) の「見たもの」に、v1の inconclusive と57件中55件が raw `seq=0` だった構造的計数を追記する。
- 本題3: [backoff-counterfactual-preregistration.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:112) の推定量を、raw `seq=0` を位置で除いた後に indexを振り直し、最初の対を raw `(event1,event2)` とする定義へ改訂する。
- 本題4: [backoff-counterfactual-preregistration.md:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:197) の time blockを残存 outcomeの index/count 基準と明記する。
- 本題5: [backoff-counterfactual-preregistration.md:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/docs/backoff-counterfactual-preregistration.md:214) の許可除外を「raw先頭 `seq=0` の位置除外」と「後続 eventを持たない最後の更新」の exact 2件にする。0 commit規則は「位置除外後の残存 eventに一件でもあれば全体 inconclusive」とし、それ以外は緩めない。
- 本題6: v2文書だけを先に commitし、その bytesの SHA-256 を確定する。以後、解析実走まで文書を変更しない。
- 本題7: [backoff_counterfactual_analysis.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:15) で analysis versionを `/v2` へ上げ、v1測定 SHAとv2解析 SHAを分割する。
- 本題8: [backoff_counterfactual_analysis.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:230) と [backoff_counterfactual_analysis.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:300) を v1 artifact SHA専用にし、呼出し側のv2 hashを渡さない形へ変更する。
- 本題9: [backoff_counterfactual_analysis.py:375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:375) で `analysis_events = events[1:]`、残存 count/index、残存全 eventのzero検査を実装する。
- 本題10: [backoff_counterfactual_analysis.py:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:571) は実 file hash対 v2定数、[backoff_counterfactual_analysis.py:581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:581) はartifact対 v1定数へ分離する。
- 本題11: [test_backoff_counterfactual_analysis.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:18) 以降のgolden、[test_backoff_counterfactual_analysis.py:141](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:141) のfixture、既存期待件数を更新し、上記の正負例とrebasing検査を追加する。
- 副題1: [t2187_adaptive_const_probe.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:65) に診断用定数だけを追加する。
- 副題2: [t2187_adaptive_const_probe.py:2758](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:2758) と [t2187_adaptive_const_probe.py:3313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3313) で診断時だけ新文言を選ぶ。
- 副題3: [test_t2187_adaptive_const_probe.py:2008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2008) と [test_t2187_adaptive_const_probe.py:2079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2079) に独立逐語goldenの性能受理・診断文言検査を置く。

## 変異事前登録候補

1. [backoff_counterfactual_analysis.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:379): `analysis_events = events[1:]` を `events` に戻す。  
   kill: `test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory`、`test_seq_zero_is_excluded_before_pairing_and_membership_is_rebased`。

2. [backoff_counterfactual_analysis.py:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:380): `outcome_count = len(analysis_events)-1` を `len(events)-1` に戻す。  
   kill: `test_seq_zero_is_excluded_before_pairing_and_membership_is_rebased`。

3. [backoff_counterfactual_analysis.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:383): 残存 zipを使わず、raw zipの enumerate後に `seq != 0` でfilterする。  
   kill: 同上。membershipへ渡る最初の indexが1になるため確実に死ぬ。

4. [backoff_counterfactual_analysis.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:389): zero scanを `analysis_events` から raw `events` に戻す。  
   kill: `test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory`。

5. [backoff_counterfactual_analysis.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:389): zero scanを `selected` の `current` だけに狭める、または検査自体を削除する。  
   kill: `test_seq_ge_one_zero_commit_remains_inconclusive_under_v2`。zeroを最後のfollowing eventへ置く。

6. [backoff_counterfactual_analysis.py:572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:572): v2文書 hashの比較対象を v1測定定数へ取り違える。  
   kill: `test_analysis_preregistration_file_is_bound_to_literal_v2_sha256` と public analysis正例。

7. [backoff_counterfactual_analysis.py:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:318): artifact pinを v2定数へ取り違える、または `{v1,v2}` のどちらも受理する。  
   kill: 通常のv1 fixtureを使う public analysis tests、および `test_artifacts_remain_bound_to_literal_v1_preregistration_sha`。

8. [backoff_counterfactual_analysis.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:15): analysis versionを `/v1` のままにする。  
   kill: `test_public_analysis_pairs_next_window_and_uses_equal_run_clusters` に追加する逐語 `/v2` assertion。

9. [t2187_adaptive_const_probe.py:3313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3313): 診断側でも常に旧 `NOT_CERTIFIED` を書く、または逆に性能側へ診断文言を書く。  
   kill: `orchestrator/tests/test_t2187_adaptive_const_probe.py::test_not_certified_text_is_mode_specific_without_changing_performance_identity`。

## 総括

- must-fix は、v2文書の先行凍結、残存集合でのpair/index/count再構成、残存全 eventへの0 commit規則、v1測定SHAとv2解析SHAの厳格な分離です。
- `seq` 連続性検査、producerのSHA write path、acceptance duration ledgerは変更不要です。
- v2 artifactを受理してはいけません。既存12成果物の測定束縛は逐語 v1 SHAのままです。
- 副題は性能文言を1 byteも変えず、診断生成時だけ分岐させ、独立commitにします。
- 未解決なのはv2文書を確定した後に決まる `ANALYSIS_PREREGISTRATION_SHA256_V2` の逐語値だけです。
- read-only指定に従い、ファイル変更、成果物閲覧、pytest実行は行っていません。