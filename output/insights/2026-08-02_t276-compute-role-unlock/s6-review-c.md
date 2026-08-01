判定は **NO-GO** です。親実測「request `877172`、関連 161 passed」は事実として受領しました。こちらでは pytest・実走を行わず、staged source の静的レビューだけで判定しています。

## 裁定履行の照合

| 裁定 | 判定 | 実装根拠 |
|---|---|---|
| §3.1 run 単位 admission、4 provider 同一 object | 充足 | admission は [_trial:1234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1234) で `_provider_set` 前に一度だけ解決され、[_provider_set:803](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:803) から同一 `transport_admission` を4回渡す。provider は再解決せず receipt を受け取るだけ（[provider:187](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:187)）。 |
| §3.2 CLI flag 全配線、既定 off | 充足 | CLI 定義 [_trial:1353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1353)、`main→run_trial` [_trial:1391](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1391)、`run_trial→_provider_set` [_trial:1284](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1284)、provider [_provider:107](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:107)。 |
| §3.3 receipt の開始・成功・invalid・init 伝播 | 充足（列挙された3経路まで） | 開始 [_trial:1244](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1244)、成功 [_provider:347](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:347)、invalid [_trial:727](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:727)、init [_trial:661](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:661)。terminal/fatal の穴は所見6。 |
| §3.4 compute + PBS witness | 充足 | site 拒否と非空 `PBS_JOBID` は [_transport:178](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:178)。`site_policy.py` は未変更。 |
| §3.5 consumer exact gate | 充足（実装） | exact key/type/contract/hash は [_trial:568](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:568)、成功 consumer で expected receipt と比較 [_trial:703](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:703)。positive control は不足。 |
| §3.6 異値・逆順 vector | 充足 | 異値 policy [_test:47](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:47)、逆順 policy [_test:63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:63)。両 endpoint は異値で、逆順 vector は実際に `https_proxy` が先。退化は解消済み。 |
| §3.7 B5 positive control 全列挙 | **未充足** | report と成功 attempt/journal の receipt 一致を検査する E2E がない。[_test:1026](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:1026) は手製 admission event と返却 report だけで、role attempt を生成しない。 |
| §3.8 plain runner | 充足 | `_run()` と `__main__` は [_test:1109](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:1109)。 |
| §3.9 主張限定・既定出力 | 実装面は充足 | transport field は provider [_provider:347](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:347)、report [_trial:931](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:931) とも opt-in 条件付き。6 staged file に MITM/CONNECT の過大主張はない。親担当 docs は本レビュー外。 |
| §7 従量 env deny、M16/P3 | **未充足** | deny 集合は TLS 7 key と proxy 8 keyだけ（[_transport:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:30)）。指定5 keyの存在検査、M16、P3 test はない。 |

## 所見 1 — 追記裁定 M16 が丸ごと未実装

深刻度: **BLOCKER**

根拠: `ANTHROPIC_API_KEY`、`ANTHROPIC_AUTH_TOKEN`、`ANTHROPIC_BASE_URL`、`CLAUDE_CODE_USE_BEDROCK`、`CLAUDE_CODE_USE_VERTEX` は deny 集合にも存在検査にもありません。現実装は PBS/TLS/proxy 検査後、そのまま admission を返します（[claude_transport.py:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:181)）。allowlist にないため child へは転送されませんが、「source に存在すれば空文字でも拒否」という裁定は満たしません。

放置した場合: これらの key が存在する run が `transport-admission-error` ではなく受理され、role attempt・report・試行台帳が生成されます。裁定上は certified 候補ゼロで止めるべき run が、T-277 後には候補生成・評価へ進み得ます。

推奨対応: 5 key の独立 deny 集合と専用 error code を追加し、空/非空を各 key で検査してください。policy read・provider 初期化・runner 呼出しがゼロであること、値 sentinel が error/report にないこと、M16 と P3 を独立 nodeid にしてください。

## 所見 2 — env 拒否より先に policy I/O を行い、継承 plan の fail-closed 順序に違反

深刻度: **MAJOR**

根拠: wrapper は site 判定後、直ちに policy を読み（[claude_transport.py:319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:319)）、PBS/TLS/proxy の存在検査は読み終えた bytes を evaluator に渡した後です（[同:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:181)）。継承 plan は TLS/proxy deny を policy read より前に置いています。テストも TLS/proxy/PBS を pure evaluator へ直接渡すだけで、wrapper の I/O 順序を検査しません（[test:283](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:283)）。

放置した場合: 禁止 env と missing/破損 policy が共存すると、試行台帳・report の fatal reason は `tls-override-present` 等でなく `policy-surface` / `policy-read` になります。certified 選択はいずれも停止しますが、台帳が恒久禁止違反を隠し、不要な filesystem I/Oも発生します。

推奨対応: source-env/PBS/TLS/proxy/M16 の pure preflight を policy read 前に実行してください。missing policy root と禁止 env を同時に与え、禁止 env の error codeと policy-reader 呼出しゼロを固定する test が必要です。

## 所見 3 — 成功 consumer と report↔attempt の positive control がない

深刻度: **MAJOR**

根拠: consumer test は malformed receipt 4件しか `_invoke()` へ渡しません（[test:943](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:943)）。valid receipt を受理する検査は `_validate_transport_receipt()` の直接呼出しだけです（[test:597](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:597)）。report test も fatal error を事前投入して workload loop を通らず、attempt と report の receipt を比較しません。

したがって、`_invoke()` が valid receipt を無条件で invalid 化する実装、または成功 event から validation 後に receipt を落とす実装でも、該当 negative test は検出しません。現コード自体の成功経路は正しく実装されています（[_trial:699](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:699)）。

放置した場合: 成功すべき role が `invalid` となり report が `partial` になる、または成功 attempt だけ transport identity を失い、試行台帳・report の certified 候補生成経路を帰属できなくなります。

推奨対応: independent literal receipt を返す provider で成功 `_invoke()` を実行し、provider 呼出し1回、`status=valid`、journal の `provenance.transport_receipt`、report root/cell の同値を一つずつ検査してください。reject-all を殺す正例と malformed 負例は別 nodeid に分離すべきです。

## 所見 4 — P1 と「実 subprocess shim」が production を拘束していない

深刻度: **MAJOR**

根拠:

- default-off test は、`run_trial` 内に名前が完全一致する `admit_claude_transport()` が1個あり、特定形の `if` 内にあることだけを AST で見ます（[test:1086](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:1086)）。alias/helper経由や追加の無条件 site/policy call が共存しても検出しません。
- 「real subprocess shim」は production provider を一度も生成せず、production の `admission.env_dict()` をそのまま無関係な Python subprocess の `env=` に渡します（[test:880](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:880)）。provider の real-runner 分岐だけが ambient env を漏らす破壊は残ります。
- import surface test も列挙した call 名だけを探す AST 検査です（[test:261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:261)）。

現実装の default path は静的には正しいです。admission は flag 条件内だけ（[_trial:1234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1234)）、provider の env/provenance追加も条件内だけです。

放置した場合: P1 が壊れて default 経路で site/policy I/Oが起きる、または child env が変わっても新 test が検出しない可能性があります。既定 journal/report が欠落・partial 化し、既存試行台帳の値が変わります。

推奨対応: production providerの `executable=` に環境を観測してvalid envelopeを返す実 shimを渡し、既定 `subprocess.run` 経路を実際に通してください。`run_trial` には admission resolver の正規注入 seamを設け、flag省略時の呼出し回数ゼロを実測してください。

DW-O14については、site test の手動差替え（[test:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:223)）は `finally` で復元され、wrapperに既存resolver seamがないため、それ自体を blockerとは判定しません。一方、fake factory seamだけでM10を証明した扱いにはできません。

## 所見 5 — M5/M10/M12 の nodeid 別 kill 主張が成立しない

深刻度: **MAJOR**

根拠:

- M10 test は `FakeProvider` が受け取った object identityしか見ません（[test:720](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:720)）。実 provider内で site/policy を再評価する、または4回再評価して元objectを渡し続ける変異はこのnodeidを生存します。
- M12 testは静的symlinkを pre-open `lstat` が拒否します。`O_NOFOLLOW` を削除（[transport:281](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:281)）、またはopen後のregular-file gateを削除（[同:287](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:287)）しても、現在のfixtureはpre-open gateで止まり、nodeidは検出しません。
- M5 mapped nodeはleafだけを呼びます。provider側の env 配線（[provider:199](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:199)）でHTTPSへHTTP値を複製する変異は、そのnodeid単独では検出しません。別provider testは検出し得ますが、impl.mdの対応表は正しくありません。

放置した場合: 同一generationの4 roleが異なるpolicy/site snapshotを使い、proposal・試行台帳が混成されます。TOCTOU symlink/非regular差替えは別policyを受理させ、endpoint/policy SHAとrole出力を変えます。HTTPS値複製は将来endpoint分離時にrouteを変えます。

推奨対応: 各変異を正確な file:line anchorへ再登録してください。M10は resolver呼出し回数1と実provider4個のreceipt object identity、M12はpost-lstat inode差替え・open後非regular、M5はleafとprovider配線を別変異に分けるべきです。

## 所見 6 — 通常 timeout は閉じるが、terminal/fatal/cleanup outcome は receipt 閉包外

深刻度: **MAJOR**

根拠:

- 通常の subprocess timeout は providerで `PredictionRunnerError` となり（[provider:265](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:265)）、`_invoke()` の invalid eventへ receiptが付くため、ここは閉じています。
- ただし `_invoke()` の例外処理中に payload/envelope artifact の `read_bytes()` が失敗すると（[_trial:713](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:713)）、invalid event作成前に脱出します。
- その後の `supervisor-error` event/cellにはreceiptがありません（[_trial:873](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:873)）。
- wall-budget eventにもreceiptがなく（[_trial:849](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:849)）、workload内部のbudget終了はevent自体がありません（[_trial:989](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:989)）。
- provider cleanup失敗はobject内へ保存するだけ（[provider:227](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:227)）で、report作成後のfinally（[_trial:1323](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1323)）から台帳へ反映されません。

root reportにはreceiptが残りますが、該当terminal event自身は自己完結しません。

放置した場合: journalのfatal行だけを読むconsumerはtransport identityを失います。cleanup失敗でも `report.status=complete` のままとなり、試行台帳が実際の終了状態と食い違います。

推奨対応: opt-in時は `supervisor-error`、両wall-budget、`run-finish`にも同じvalidated receiptを付けてください。artifact収集失敗を本来のinvalid記録から分離し、cleanup結果はterminal report確定前に回収・記録してください。

## 所見 7 — 拒否テストの診断・単一理由性が不統一

深刻度: **MINOR**

根拠: leaf拒否は共通helperで structured code と sentinel 不在を確認しており強いです（[test:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:110)）。一方、receipt/provider拒否は任意の `AutonomousTrialError` / `PredictionRunnerError` だけを見る箇所があり（[test:624](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:624)、[test:856](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:856)）、runner呼出しゼロを固定しません。

またM11はinvalidとinitの独立2箇所、M12はsymlink/regular/size/read/open、M13はleafとtrial redactionを同じnodeへ寄せています。先頭assertで止まるため、DW-M03上「どの変異理由を殺したか」が一意になりません。M12のregular-file gate削除はFIFO openへ進み、timeout隔離なしではhangにもなり得ます。

放置した場合: 拒否自体は維持してもerror codeが別理由へ退化し、試行台帳の原因分類が変わります。mutation台帳は一つの失敗nodeを複数gateの証拠として過大計上します。

推奨対応: invalid/init、pre-open/post-open、leaf/trial redactionを別nodeid・別変異へ分割し、error code、呼出し回数、sentinel不在を各々固定してください。

## 24 test の恒真性監査

| # | test | 判定 |
|---:|---|---|
| 1 | `committed_policy_matches...` | 有効。raw bytes・SHA・registryは独立literal。 |
| 2 | `accepts_committed_literal...` | 有効。ただしdeployment vector単独は同値endpoint。#3/#4が補う。 |
| 3 | `accepts_distinct_http_https...` | 有効。異値は退化していない。 |
| 4 | `reverse_endpoint_key_order...` | 有効。実際に逆順でliteral digest比較。 |
| 5 | `rejects_non_compute...orders_io` | M1には有効。manual monkeypatch＋限定ASTで一般的な再評価禁止には不十分。 |
| 6 | `transport_import_surface...` | 部分的。列挙call名以外のalias/helper/import side effectを見逃す。 |
| 7 | `rejects_pbs_job...` | 有効。error code確認あり。 |
| 8 | `rejects_each_tls_override...` | 有効。独立7 key、空/非空、code、sentinel。 |
| 9 | `rejects_each_unadmitted_proxy...` | 有効。独立8 key、code、sentinel。 |
| 10 | `rejects_missing_non_string_and_drifted...` | 部分的。missing/typeは両key、値drift/sentinelはHTTP側だけ。 |
| 11 | `rejects_source_and_policy_input_types` | 有効。 |
| 12 | `rejects_malformed_duplicate...` | 有効だが多数の独立gateを一nodeへ集約。 |
| 13 | `rejects_every_policy_uri...` | 有効。列挙されたURI禁止形とsentinelを固定。 |
| 14 | `policy_surface_rejects...` | 部分的。post-lstat swap、open後nonregular、short-readを検査しない。 |
| 15 | `trial_receipt_gate_rejects...` | 部分的。direct valid＋負例はあるが、consumer成功経路ではない。 |
| 16 | `cli_flag_default_and...wiring` | exact M8/M9 deletionには有効。AST-onlyで実効動作は保証しない。 |
| 17 | `provider_set_passes_one...` | 部分的。FakeProviderの引数identityだけでM10を殺せない。 |
| 18 | `projected_provider_default_and_opt_in...` | 有効。runner引数を独立literal exact mappingと比較。 |
| 19 | `projected_provider_rejects_flag_types...` | 部分的。例外型とsentinelだけでrunner回数を見ない。 |
| 20 | `real_subprocess_shim...` | **productionに対して恒真**。providerを通らず、admission戻り値を直接envへ使用。 |
| 21 | `invoke_consumer_rejects...` | 部分的。負例のみ。reject-allと成功receipt脱落を見逃す。 |
| 22 | `invalid_attempt_and_provider_init...` | 実装伝播には有効だが、M11/M13を一nodeに重ね単一理由でない。 |
| 23 | `opt_in_report_and_opt_out...` | 部分的。手製journal＋fatal reportだけ。成功attemptとの一致・byte不変なし。 |
| 24 | `opt_out_source_contains_no...` | 不十分。特定名のguarded callが存在することしか証明しない。 |

期待値を実行時 `os.environ`、production denylist/定数、policy loaderから生成する test は見当たりません。問題は production 戻り値をそのまま subprocess 入力に使う #20 と、production経路を実行せずsource形だけを見る #6/#16/#24です。

## M1〜M15 の静的 kill 判定

| 変異 | 判定 | 理由 |
|---|---|---|
| M1 | KILL | direct非compute vectorとwrapperのerror codeが検出。 |
| M2 | KILL | 各TLS keyの存在を独立に投入。 |
| M3 | KILL | 未受理8 keyを独立に投入。 |
| M4 | KILL | exact値検査を緩めるとdrift vectorが受理側へ変わる。 |
| M5 | **nodeid単独では条件付きSURVIVE** | leafで複製するanchorなら検出。provider env層で複製するとmapped nodeは非到達。 |
| M6 | KILL | reverse key vectorのliteral digestが変わる。 |
| M7 | KILL | missing/empty/type vectorが受理側へ変わる。 |
| M8 | KILL | signatureとargparse defaultをliteral `False` で検査。 |
| M9 | KILL | main・run_trial・factoryのkeyword欠落をASTで検出。 |
| M10 | **SURVIVE** | real provider内の再評価や、結果を捨てる追加再評価はFakeProvider identity testに見えない。 |
| M11 | KILL（証拠は過剰決定） | receipt削除でassertに到達するが、invalidとinitを独立に証明できない。 |
| M12 | **SURVIVE** | `O_NOFOLLOW` またはopen後regular gateだけの削除は現fixtureで検出されない。 |
| M13 | KILL（単一理由性弱い） | leaf driftとtrial redactorの双方にsentinel検査。ただし異なる層を混載。 |
| M14 | KILL | exact gate全削除ではmalformed receiptがvalid側へ進む。ただしreject-allは別途生存。 |
| M15 | KILL | registry全体を独立literalで比較。 |

impl.md の nodeid 対応表について、kill主張を受理できないのは **M10、M12**、およびanchor未指定のため層によって生存する **M5** です。

## 受理集合・既定経路・snapshot の最終判定

受理の過大拡大は M16 の5 keyだけを確認しました。追加された `providers is None` 制約やexact receipt gateは、owned projected providerだけを解禁するfail-closed制約として裁定範囲内です。M16以外に明確な過剰受理・過剰拒否は見つけていません。

flag省略時の productionコードには、静的には出力変更経路を見つけませんでした。

- admission/site/policy I/Oは `if allow_...` 内だけ。
- child argvは既存列のまま（[provider:202](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:202)）。
- base env構築は従来どおりで、proxy追加はopt-in内だけ。
- 17-key provenance、journal、reportへのreceipt追加は条件付き。
- `transport_receipt=None` 時のerror redactorは元の `str(exc)` と同値（[_trial:640](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:640)）。

run単位snapshotも現コード自体は成立しています。`os.environ` snapshot、site/policy解決、receipt生成は一度だけで、4 providerは同じfrozen admission/receipt objectを受け取ります。途中再評価するproduction callはありません。ただし、その不変性をM10 testが実効的に拘束していません。

## 総括

**NO-GO**

最重要3件:

1. **BLOCKER:** 追記裁定の従量env deny、M16、P3が未実装。
2. **MAJOR:** M10/M12（および層未指定のM5）のkill主張が成立せず、変異台帳を信用できない。
3. **MAJOR:** 成功consumer、report↔attempt、fatal/cleanup outcomeのreceipt閉包が未固定で、試行台帳のtransport帰属が欠け得る。