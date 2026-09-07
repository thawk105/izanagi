## 受理集合の実測

公開 API の受理集合は次のように変わった。ここで「受理」は `ValueError` にならず解析結果を返すことを指し、主判定が `inconclusive` かどうかとは分ける。

| 文書 sha | artifact の top / row sha | 変更前 | 変更後 | 判定 |
|---|---|---:|---:|---|
| v1 | v1 / v1 | 受理 | 文書 gate で拒否 | 過剰拒否。旧 API の正例が消えた |
| v2 | v1 / v1 | 文書 gate で拒否 | 受理 | 新規受理。v2 が意図した cohort 再解析 |
| v2 | v2 / v2 | 文書 gate で拒否 | top gate で拒否 | 新 producer の正当な成果物だが、意図的に対象外 |
| v1 | v2 / v2 | artifact または文書 gate で拒否 | 文書 gate で拒否 | 拒否のまま |
| v2 | v1 / v2、または v2 / v1 | 文書 gate で拒否 | top または row gate で拒否 | 混在は受理されない |
| 任意の別 sha | 任意 | 拒否 | 拒否 | 弱体化なし |

変更後の文書 gate は v2 固定である一方、top と row はそれぞれ v1 固定である。[analyze_counterfactual](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:567>)、[_load_artifact](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:308>)、[_validate_row](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:236>)。したがって、artifact JSON への射影では新しい不当入力は受理されていない。公開引数の組としてだけ、`(v1 artifact, v2 document)` が新たに受理された。

private API 単体では `_load_artifact(..., expected_hash=...)` と `_validate_row(..., expected_hash=...)` が廃止されたため、任意の呼出側指定 hash に top と row を合わせた artifact は受理できなくなった。公開 API は変更前から v1 文書 hash しか渡せなかったので、この縮小は公開受理集合には追加影響しない。

`_run_difference` の判定集合は次のとおり変わった。[位置除外と zero scan](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:382>)

- `seq = 0` だけが 0 commit: 変更前は `window_commits_zero`、変更後は scan 対象外。残存 arm と CI が揃えば確認的判定へ進む。
- `seq >= 1` に 0 commit: 変更前後とも `window_commits_zero`。membership でその対を除いても、scan は `selected` ではなく全 `analysis_events` にかかる。
- 一方の arm が `seq = 0` にしかない: 変更前は推定可能、変更後は `missing_assignment_arm`。これは位置除外に伴う意図した確認可能集合の縮小である。
- 全 commit 正かつ残存両 arm あり: 受理のままだが、`Y[r,0]` が消え、層別 index と時間 block が再基底される。

producer/consumer 側は次の三分岐である。

- performance producer は従来の `NOT_CERTIFIED` を返す。
- diagnostic producer は新しい `DIAGNOSTIC_NOT_CERTIFIED` を返す。
- exact counterfactual 軸だけは、現在の文書を毎回 hash して `counterfactual_preregistration` を付ける。したがって今後の producer は v2 束縛 artifact を出す。[metadata 分岐](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:2761>)、[文書 hash](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:842>)

`_performance_artifact_identity` は schema v2/v3、`kind = performance-only-probe`、旧 performance 文言、指定された全体 SHA のすべてを引き続き要求するため、意味上の受理集合は変わっていない。[identity gate](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:1747>)。diagnostic 文言を書いた performance artifact は拒否される。

一方、解析器の top-level expected dict は `not_certified` を含まず、`_matches_exact` は expected にある key だけを見る。[部分一致](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:114>)。従って diagnostic artifact の `not_certified` が旧文言、新文言、欠落、別文字列のどれでも解析器は受理する。これは変更前からの不変な広さであり、commit 3 が新たに弱めた経路ではない。

## 恒真テスト

実質的に新設された test は 5 本である。rename された既存 2 本は数えていない。

- `test_seq_zero_is_excluded_before_pairing_and_membership_is_rebased`
- `test_seq_ge_one_zero_commit_remains_inconclusive_under_v2`
- `test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory`
- `test_artifacts_remain_bound_to_literal_v1_preregistration_sha`
- `test_not_certified_text_is_mode_specific_without_changing_performance_identity`

明確な恒真または循環部分は二つある。

1. `test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory` の v1 側

   test 自身が全 artifact の対象 event を 0 にし、その同じ JSON を読み直して `any(window_commits == 0)` を test-local に計算している。[書換え](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:320>)、[local predicate](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:326>)。

   これは次だけを検査する。

   - fixture の対象 row に実際に 0 が書かれたこと。
   - v1 の規則として想定した「生 event 全体に 0 がある」というデータ述語が真であること。

   次は検査していない。

   - v1 実装がその述語を使っていたこと。
   - v1 実装が `reason = window_commits_zero` を返したこと。
   - v1 の `decision` が `inconclusive` だったこと。
   - v1 実装を変更・破壊した場合の回帰。

   v2 側は現行 `analyze_counterfactual` を呼び、`confirmatory_complete` と `equivalent` を逐語で検査しているため実効である。[v2 assertion](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:335>)。

2. `test_not_certified_text_is_mode_specific_without_changing_performance_identity` の identity 側

   mode-specific な二つの文字列 assertion は test-local literal なので実効である。[literal assertion](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2053>)。

   ただし後半は test が手書きした artifact の hash を、その場で `expected_sha256` と期待 dict の両方へ戻している。[self-derived identity](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2066>)。これは旧 artifact が consumer に読める正例でしかなく、production `main` の performance 出力 bytes や SHA が不変であることを検査していない。

   実際、変更前は payload の key 順が `schema_version, kind, not_certified`、変更後は spread された `schema_version, not_certified` の後に `kind` が来る。[現在の payload](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3304>)。`json.dump` は sort していないため、同じ値でも全体 bytes と SHA は変わる。[書出し](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3520>)。不変なのは文言と consumer の意味上の受理集合であって、全体 identity hash ではない。

補足すると、rebasing test の `changed["estimate_log"] == result["estimate_log"]` は production 出力同士の比較だが、両方が別途 test-local の `expected_estimate` と比較されているため、test 全体は恒真ではない。[独立期待値](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:225>)。

新設 test の v1/v2 SHA と analysis version は test-local literal であり、module 定数から期待値を取ってはいない。[test-local SHA](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:21>)、[version literal](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:302>)。

## 変異事前登録の検証

12 行すべてについて、期待 node 名は現物に実在する。逐語 anchor の存在数はすべて 1 件である。同じ anchor を別変異として使う M4/M5 と M9a/M9b は、それぞれ source 上の同じ一意箇所を指す。

| 変異 | 現物からコピーした逐語 anchor | 期待 node | 判定 |
|---|---|---|---|
| M1 | `analysis_events = events[1:]` | `test_seq_zero_is_excluded_before_pairing_and_membership_is_rebased` | 成立。全 commit 正で zero gate と分離 |
| M2 | `outcome_count = len(analysis_events) - 1` | 同上 | 成立。membership の count literal で赤 |
| M3 | `zip(analysis_events, analysis_events[1:])` | 同上 | 成立。raw enumerate の index 1 が期待 0 と衝突 |
| M4 | `if any(event["window_commits"] == 0 for event in analysis_events):` | `test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory` | 成立。seq0 の 0 が primary を inconclusive にする |
| M5a | 同上 | `test_seq_ge_one_zero_commit_remains_inconclusive_under_v2` | 成立。0 は末尾、直前 pair は membership 外で算術例外なし |
| M5b | 同上 | 同上 | 成立。検査削除でも両 arm が残り、数値結果へ進む |
| M6 | `if preregistration_sha256 != ANALYSIS_PREREGISTRATION_SHA256_V2:` | `test_analysis_preregistration_file_is_bound_to_literal_v2_sha256` | 成立。未変更 v2 文書の正例呼出しが赤 |
| M7a | `"counterfactual_preregistration": MEASUREMENT_PREREGISTRATION_SHA256_V1,` | `test_artifacts_remain_bound_to_literal_v1_preregistration_sha` | 不成立。現 fixture は gate を分離できていない |
| M7b | `!= MEASUREMENT_PREREGISTRATION_SHA256_V1` | 同上 | 一部不成立。widening は殺すが v2 固定 mutant が生存 |
| M8 | `ANALYSIS_VERSION = "izanagi-backoff-counterfactual-analysis/v2"` | `test_public_analysis_pairs_next_window_and_uses_equal_run_clusters` | 成立。出力を逐語 `/v2` と比較 |
| M9a | `DIAGNOSTIC_NOT_CERTIFIED if backoff_trace else NOT_CERTIFIED` | `test_not_certified_text_is_mode_specific_without_changing_performance_identity` | 成立。diagnostic literal だけが赤 |
| M9b | 同上 | 同上 | 成立。performance literal だけが赤 |

anchor の現物位置は、M1〜M5 が [_run_difference](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:382>)、M6 が [文書 gate](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:582>)、M7a が [top pin](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:326>)、M7b が [row pin](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:262>)、M8 が [version](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/campaign/backoff_counterfactual_analysis.py:18>)、M9 が [mode ternary](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:2775>) である。

M7a の問題は、`all_v2_paths` という名前に反して最初の artifact しか変更せず、その artifact は top と全 row の両方を v2 にしていることだ。[現 fixture](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:433>)。top を v2 固定へ変異すると top は通るが、未変異の row gate が落ち、期待した top error と違うという理由で赤になる。top pin 単独の帰属ではない。

成立する形は、12 artifact すべての top を v2、全 row を v1 のままにすること。この入力なら top-v2 固定と v1/v2 widening のどちらも全 artifact の top を通し、row gate は一切落ちない。なお `{v1, v2}` を top expected dict の値へそのまま代入すると、`_matches_exact` の型同一性により string 対 set で全拒否になる。widening mutant は top gate 全体を membership 判定へ書き換える必要がある。

M7b の v2 固定 mutant では、現 `one_v2_row` fixture の対象 row より先に多数の v1 row が現れ、同じ row mismatch で落ちるため test は緑のままである。[現 one-row fixture](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:448>)。

成立する形は、12 artifact の top をすべて v1 のまま、全 artifact の全 18 row を v2 にすること。これで row-v2 固定 mutant と v1/v2 widening mutant はどちらも解析完了まで進み、期待した row rejection が消えるため、変異だけに帰属して赤になる。

## 行番号 pin の閉包

`tools/pegasus/probes/t2187_adaptive_const_probe.py` については次の集計になった。

- 行番号 literal: 4 箇所、論理 pin は 2 件。
  - `3019` が ledger 本体と exact expected set に各 1 箇所。
  - `3387` が ledger 本体と exact expected set に各 1 箇所。
- その他の行番号 pin: 0。
- byte offset pin: 0。
- hard-coded whole-file SHA-256 pin: 0。
- 動的な whole-file hash 計算: 2 箇所。これは現在の `DRIVER.read_bytes()` を都度 hash するため、焼き込み pin ではない。[動的 hash の例](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2364>)

現物の sink は [3019](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3019>) と [3387](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/tools/pegasus/probes/t2187_adaptive_const_probe.py:3387>)。4 literal は [_DEFERRED_GATE_MEMBERS](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_ccbench_spawn_sites.py:912>) と [expected set](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_ccbench_spawn_sites.py:2676>) に閉じている。

現ファイルの SHA-256 は `c3d812851881e85410a559f7879f3d26c8923e91b4c9340f76a652cbbe9ceda7` で、repo 内の hard-coded 一致は 0 件だった。

`orchestrator/campaign/backoff_counterfactual_analysis.py` は次のとおり。

- 行番号 pin: 0。
- byte offset pin: 0。
- hard-coded whole-file SHA-256 pin: 0。
- 現 SHA-256 `9883892bae84e8f4dc9206d8635f02bbec8cb420313df8ea5f3ba6b8277a745a` の repo 内一致: 0。
- consumer は module import であり、source line や file hash には束縛していない。[import](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:15>)

12 成果物 JSON と `output/**` は検索対象として開いていない。

## 受入の赤経路

新規 test file は 0。3 commit の file status はすべて `M` で、`A`、`new file mode`、`/dev/null` はない。全差分の test file は既存の [test_backoff_counterfactual_analysis.py](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/wave.diff:280>)、[test_ccbench_spawn_sites.py](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/wave.diff:542>)、[test_t2187_adaptive_const_probe.py](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-itt-seq0/s6/wave.diff:578>) だけである。

plain runner 契約は静的に満たす。

- meta-test は各 `test_*.py` に実効 `__main__` harness または allowlist を要求する。[要求](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_plain_runner_coverage.py:60>)
- analysis test は `_run` と `__main__` を持つ。[harness](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_backoff_counterfactual_analysis.py:669>)
- probe test も持つ。[harness](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_t2187_adaptive_const_probe.py:2629>)
- spawn-site test も持つ。[harness](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_ccbench_spawn_sites.py:3519>)

duration ledger は schema 上は整合している。`schema_version=1`、`unit=seconds`、`nodeid_count=19521`、mapping 実件数も 19521 だった。[ledger footer](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/acceptance_duration_ledger.json:19525>)。この invariant は [ledger test](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_update_acceptance_duration_ledger.py:306>) と一致する。

ただし新設 5 node は ledger に 1 件もない。これは schema 違反ではなく、未知 cost として既知 cost の 96 番目相当へ配置される。[unknown cost](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/conftest.py:1615>)。受入の pass/fail 集合は変えないが、loadgroup の配布順と所要時間見積もりは変わる。全収集に対する 90% coverage gate は存在するが、pytest collect を禁止されているため今回の静的レビューでは実測していない。[coverage gate](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-itt-seq0/orchestrator/tests/test_acceptance_schedule_order.py:704>)。

受入全走で本 wave に帰属しうる赤経路は次である。

- v2 文書 bytes と literal SHA がずれれば、全 public analysis test が文書 gate で赤になる。現物 SHA は `526d...95a` で実装・test literal と一致した。
- 位置除外、zero scan、row/top pin、version のいずれかがずれれば analysis test file の対応 node が赤になる。ただし M7b v2 固定だけは前節のとおり赤にならない。
- probe の performance または diagnostic literal がずれれば mode-specific test が赤になる。performance literal は plotting consumer とも一致している。
- sink 行が 3019/3387 からずれれば `test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink` が赤になり、deferred 分類を失えば `test_define_sink_cross_product_has_no_unreviewed_ungated_member` も赤になりうる。
- harness が消えれば `test_every_test_file_is_self_runnable_or_allowlisted` が赤になる。
- ledger schema/count が壊れれば ledger invariant test、全収集 coverage が 90% 未満なら schedule-order test が赤になる。

pytest は実走していないため、以上は静的に閉じた経路であり「緑」とは判定しない。

## commit 粒度と provenance

3 commit の分割自体は妥当である。

- `1c977a218`: docs だけを先に凍結。解析器・結果より祖先に置く目的と一致する。
- `1c482bf6f`: 解析器とその test を同一 commit。実装面の author trailer は `product=codex; model=gpt-5.6-sol; reasoning=xhigh; role=author`、Claude は `role=manager` であり、Codex author 契約に合う。
- `3ad183032`: 副題の producer、対応 test、そこから派生した spawn-site pin を同一 commit。主題とは別 commit だが、派生修正を同じ commit に閉じており粒度は適切。Codex author と Claude manager の provenance もある。
- docs-only commit は `product=claude; role=author; scope=docs` で、実装面の Codex author を偽っていない。

commit graph は `1c977a218 -> 1c482bf6f -> 3ad183032` の直線で、現在 HEAD は `3ad183032`、worktree は clean だった。HEAD より後の commit はない。

ただし、射影資料には「どの SHA を tested tip として受入全走したか」という receipt がない。従って land 契約は条件付きである。

- tested tip が `3ad183032` なら、以後を純粋 main merge だけに限定でき、契約に適合する。
- tested tip が `1c482bf6f` 以前なら、commit 3 は tested tip 後の非 merge 実装 commit なので不適合。`3ad183032` を tested tip とする再検査が必要になる。

provenance checker 自体は実走していないため、trailers の現物確認以上は主張しない。

## 総括

- **must-fix: M7b の「row pin を v2 固定」変異が現 test を生存する。**  
  影響: valid な v1 row をすべて拒否し、top=v1・全 row=v2 を受理するよう受理集合が反転しても、変異行列は緑を返す。

- **must-fix: M7a は downstream row gate または別 artifact の top gate で赤になり、単一理由性を満たさない。**  
  影響: top-level pin の弱体化を殺したように見えても、実際に `(全 top=v2, 全 row=v1)` を拒否できるかという top 受理集合の証拠にならない。

- **real: `test_not_certified_text_is_mode_specific_without_changing_performance_identity` の identity 部分は self-hash である。**  
  影響: performance 文言の値と意味上の受理集合は固定するが、production JSON の key 順変更で全体 SHA とそれを参照する `performance_artifact_sha256` が変わることを検出しない。

- **real: `test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory` の v1 側は fixture 述語しか見ていない。**  
  影響: 現行 v2 の値は検査するが、「v1 decision が inconclusive だった」という参照主張は実装回帰 test として保護されない。

- **real・意図どおり: 公開 API は `(v1 artifact, v1 document)` を失い、`(v1 artifact, v2 document)` を得た。**  
  影響: artifact 射影は狭いままだが、引数組の受理集合は不変ではない。

- **real・意図どおり: 現 producer の exact counterfactual artifact は v2 束縛になり、本解析器から拒否される。**  
  影響: 将来成果物の `counterfactual_preregistration` 値は v2 となり、本解析器での再利用可能集合には入らない。

- **real: 新設 5 node は duration ledger に未登録。**  
  影響:解析値と pass/fail 集合は変えないが、5 node の所要見積もりが未知 cost となり、受入の配布順が変わる。

- **未解決: tested tip を示す receipt が射影にない。**  
  影響: tested tip が `3ad183032` でなければ、commit 3 が land 契約上の非 merge 変更となり、その tip の受入状態を参照できない。