## precedence との整合

以下、行番号は変更前。略記は次のファイルを指す。

- **C**: [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2596-abort-not-runtime/orchestrator/campaign/s8b_floor_campaign.py)
- **T**: [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2596-abort-not-runtime/orchestrator/tests/test_s8b_floor_campaign.py)
- **S**: [s8b_floor_stats.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2596-abort-not-runtime/orchestrator/campaign/s8b_floor_stats.py)

**所見: refuted / scope 内 — 同一 session の pre-probe 競合と measure abort は両立しない。**

C:6262–6273 は競合時に `_finish_session` から return する。measure は呼ばれないため、今回の再送出を足しても、その session は従来どおり `competing_process` になる。

別 session で起きる場合は順序次第となる。

- 競合 session → abort session：先の競合 session 行は残り、後の abort session は start だけを残して campaign が停止する。
- abort session → 競合するはずだった session：後者は実行されない。

**所見: real / scope 内 — 「precedence を変えない」は session の理由表に限定すべき。**

旧実装では measure abort も C:6283 に捕まり、post-probe が競合を返せば C:6331 の `competing_process`、競合なしなら C:6334 の `launch_failure` になる。post-probe 自体が abort すれば元の abort 診断が置き換わる。

新実装は、この分類全体に進まず元の abort を送出する。閉表そのものと通常の起動失敗の順序は維持されるが、**abort と post-probe の競合・検査不能との優先関係は変わる**。

S:54–59 の閉表、S:192–206 の session 有効性判定に campaign abort を追加する必要はない。

**所見: real / scope 内 — β-7 の全称表現との不一致は残る。**

C:33–34 の「measure が例外を投げた経路でも必ず」と、post-probe を省く差分は文字どおりには一致しない。既存の `_SimulatedCrash` が既にこの文言を満たさないことは、明文化された例外規定の代わりにはならない。plan がこれを「解釈上の所見」として残した点は妥当。

## journal と consumer への波及

**所見: refuted / scope 内 — start のみの attempt は、新しい schema 破損ではない。**

C:6238–6245 で start を記録済み、C:6401 の session emit には到達せず、C:7955–7961 で `terminal/status=aborted` を追記する。campaign 全体には、それ以前の記録も残る。「journal が session-start 一行だけになる」という意味ではない。

consumer の追跡結果：

| consumer | 根拠と扱い |
|---|---|
| resume | C:7706 → `s8b_floor_contract.py:904–910`。aborted terminal を明示的に拒否する。**通常の crash resume には進まない。** |
| resume の session 突合 | C:8323、8355、8364–8370。start の正準性と「session に対応する start」を検査する。全 start に session があることは要求しない。 |
| checkpoint／liveness | `floor_job_checkpoint.py:1034–1041` が JSONL prefix を読む。`floor_liveness.py:606–610` → 同:334–383 は start を独立して検査し、対応 session を要求しない。最後の開始セルも取得できる。 |
| artifact verify | C:7964 以降の inspection／result 作成には到達しない。`s8b_holdout_freeze.py:1420` の結果入力は result ファイルを必要とする。既存結果の journal 突合は同:1596–1606 で session と attempt lifecycle を区別している。 |
| report | C:6898 の `_render_result_md` は result を入力とし、C:8033 の staging に至る前に abort する。今回の停止では result.json／result.md を生成しない。 |
| 結果候補の列挙 | `s8b_holdout_freeze.py:1854–1859` は result.json のない run をスキップする。 |

**所見: 不明 / scope 外 — 未特定の外部 report consumer 全体までは保証しない。**

上表の既存経路に破損は見つからない。探索した `scripts/` は存在しなかったため、その配下にあると仮定した consumer は確認対象に含めていない。

## retry 枠の会計

**所見: real / scope 内 — 「abort なら retry 枠を消費しない」は誤り。**

C:6123–6134 は `kind=retry` の **session-start** から使用済み ordinal を数える。session 完了行の有無は関係しない。

| 面 | 旧実装 | plan の差分後 |
|---|---|---|
| journal の試行行 | post-probe 成功後、launch または competing の session 行を作る | 当該 start は残り、当該 session 行は作らない |
| retry 枠 | admission が許可すれば C:6406–6423 の retry 消化へ進みうる | 停止以降の枠は使わない。ただし **既に開始した retry の枠は消費済みのまま** |
| terminal 診断 | 元の abort が session notes に吸収され、後続処理の成否で terminal が決まる | 元の abort の文字列を `aborted.reason` に記録して再送出 |

planned start は retry 枠を消費しない。負例の「最初の callback で abort」は、この planned 停止を検査する設計であり、消費済み retry 枠の扱いを直接実証するものではない。

また、retry の発行は C:6170–6188 の admission verdict に依存する。brief の「retry 枠を消費して継続」は可能な結果の説明であり、wrapper の全 abort について必ず成立する説明ではない。

## 新設テストの実効性

**所見: refuted / scope 内 — 負例は再送出を撤回すると恒真にはならない。**

`test_measure_campaign_abort_propagates_without_launch_failure` は、次の要求が効く。

- callback 到達と start 一件を要求し、事前 gate による空振りを除く。
- `caught.value is abort` により、後続 admission／inspection の別例外では代用できない。
- 当該 attempt の session 不在により、旧実装の誤分類を直接検出する。
- callback 後 probe ゼロにより、abort 後の post-probe 実行も検出する。

**所見: real / scope 内 — 正例単独は撤回変異でも通る。それは保持確認として正しい。**

plain `RuntimeError` の動作は修正前後で同じであるべきなので、正例が撤回変異を殺せないこと自体は欠陥ではない。正例の役割は再送出対象を広げすぎる変更の検出である。

**所見: refuted / scope 内 — 対象機構を stub しただけのテストではない。**

T:815–853 は実体の `_run_campaign_core` を呼ぶ。C:7926、7938 の実 admission wrapper と実 `_Runner._run_session` を通す。autouse fixture は source evidence・materialization・binary receipt 発行・toolchain を置換するが、対象 except、`assert_cell_holdout_admission`、`consume_attempt_ticket` は置換していない。

ただし、直接注入するのは admission 通過後の callback abort である。**wrapper 内の三つの拒否条件それぞれの到達性を検証したとは報告できない。**

## 既存テストの洗い直し

**所見: real / scope 内 — plan は measure 例外の一覧と、CampaignAbort 期待テスト全体の一覧を分ける必要がある。**

接頭辞はすべて `orchestrator/tests/test_s8b_floor_campaign.py::`。

plan に個別列挙されていない、直接 `CampaignAbort` を期待する既存 nodeid：

```text
test_measure_run_cmd_projection_removes_runtime_root_and_rejects_missing_token
test_measure_run_cmd_rejects_shape_opposite_to_recorded_preflight
test_official_perf_mode_rejects_only_explicit_available_receipt
test_assemble_manifest_has_independent_official_available_gate
test_official_result_rejects_perf_preflight_receipt_fail_closed
test_runner_requires_exact_holdout_admission_mapping
test_probe_unexecutable_or_inconsistent_aborts_campaign
test_certified_cut6_existing_marker_competing_probe_aborts_without_result
test_cut6_replay_rejects_truthy_non_bool_verdict
test_live_admission_runtime_exact_keys_fail_closed
test_binary_receipt_mismatch_aborts
test_certified_campaign_rejects_unissued_consumption_marker
```

これらは run_cmd 射影、preflight、live admission、probe、binary receipt、cut6 または certified 側の abort であり、**非 certified の measure callback が CampaignAbort を直接投げる既存テストではない**。今回の except より外側なので、静的には期待値変更を要しない。

**所見: refuted / scope 内 — 対象 measure の既存例外に、追加の漏れは見つからない。**

- plain `RuntimeError` の `raise_for` 利用は `test_post_probe_runs_on_launch_error_and_competing_takes_precedence`。このテストは launch_failure を最終期待値にせず、競合優先を要求する。
- measure に `TimeoutExpired` を投げさせる既存例は見つからない。T:9924 は probe timeout。
- plan の `_SimulatedCrash` callback 一覧と `Cut10Crash` の指摘は整合する。
- `launch_failure` の他の文字列 hit には protocol の閉表入力が含まれ、measure の起動失敗を期待するテストとは区別が必要。

pytest は実走していない。

## 親の実測の検算

**所見: real / scope 内 — 継承と対象箇所は合うが、アンカーの意味を一部限定すべき。**

| アンカー | 検算 |
|---|---|
| A1 | 一致。C:360 は `FloorCampaignError(RuntimeError)`。 |
| A2 | 一致。C:408 は `CampaignAbort(FloorCampaignError)`。 |
| A3 | C:6283–6284 は一致。「唯一」は **この measure 呼出しを包む except** の意味に限定する。非 certified 経路全体の except が一つという意味ではない。 |
| A4 | 代入は C:6334。条件 `elif measure_error is not None` は **C:6333**。表の範囲は条件行を一行落としている。 |
| A5 | 一致。raise は C:5983、5988、6002。 |
| A6 | 一致。wrapper 作成 C:7926、runner への結線 C:7938。 |
| A7 | 構造は一致。launcher:1400 は例外捕捉、1401 は failure evidence 作成、1404 は finally。対象 except を通らない直接の根拠は **C:6259 の分岐 return**。 |
| A8 | runner:963、1184 は **捕捉節**。plain RuntimeError の送出根拠は同:967、1188。起動失敗を従来どおり捕捉する必要性は支持される。 |

## 変異の帰属

**所見: real / scope 内 — `except RuntimeError: raise` への拡張は、既存テストにも捕まる。**

T:9885 の `test_post_probe_runs_on_launch_error_and_competing_takes_precedence` が既に plain RuntimeError を通す。新設位置が T:9912 の後なので、通常のファイル順・fail-fast 実行では既存テストが先に失敗する。

したがって、**全走が赤になった事実だけでは、新設正例の検出力に帰属できない**。新設正例を個別指定した変異結果なら、その正例による検出として扱える。

**所見: refuted / scope 内 — 他の二候補は先行 gate に必ず遮られる変異ではない。**

- 再送出削除：callback に到達した後の例外処理を変える。負例の同一オブジェクト・session 不在要求に帰属できる。
- 再送出前の `strict_probe` 追加：正常 probe を返す設定なら、その追加呼出しを負例のカウンタが検出する。

plan が除外した freeze・binary・admission 入力の事前破壊は、先行 gate に捕まるため対象差分の証明にならない。`FloorCampaignError` への拡張も、この二本では殺せないという plan の評価どおり。

## 総括

**所見: real / scope 内 — 局所二行修正と二本のテストは、静的には成立する。説明の修正が必要。**

親へ返す主要点は次の四つ。

1. pre-probe 競合と measure abort は同一 session では両立しない。
2. aborted terminal が残れば resume は拒否される。消費済み retry 枠は返却されない。
3. 負例が撤回変異を検出し、正例は plain RuntimeError の動作保持を検証する。
4. RuntimeError 拡張変異の全走失敗は、既存テストの検出と区別して帰属する。

既存 consumer の破損、既存期待値を変える必要性は確認できなかった。β-7 の全称表現との不一致は解釈上の未解消点として残る。コード編集・commit・pytest 実走は行っていない。