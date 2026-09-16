## 前提の検算

本段は静的検査のみ。指定された射影資料はすべて読めた。ファイル変更・発行・pytest 実行は行っていない。以下の既存 file:line は現物の位置、新規ファイルの行番号は実装配置の目安である。

**空 batch は、通常の環境前提が満たされれば `design_not_feasible` で停止し、publication root を作らない。P3 の結論は正しい。**

| 順序 | 根拠 | 空 batch の挙動 |
|---|---|---|
| 0 | `p3_b4_prerun_issuer.py:755`、`:194` | root を正規化し、同 checkout の事前登録と一致検査。ここが先行する |
| 1 | `p3_b4_analysis_ledgers.py:479` → `:447` | `scheduled_attempts_sha256(())` が `_normalize_attempts(())` を呼ぶ。空 tuple は受理され、空配列を含む canonical payload を hash 化 |
| 2 | `p3_b4_prerun_issuer.py:374` | planned 空集合と scheduled 空集合は一致。不在検査対象もない |
| 3 | 同 `:457` | 固定名との衝突検査は対象 0 件 |
| 4 | 同 `:259` | `_ensure_new_publication_root` は `lstat` による検査だけ。親ディレクトリが存在し root が不在なら通過 |
| 5 | 同 `:787` | `secrets.token_bytes(32)` を 1 回呼ぶ。空 batch でも乱数生成は行う |
| 6 | `p3_b4_analysis_ledgers.py:670`、`:492` | schedule count は非負整数なので 0 を受理。空 batch の hash と照合して封印 registry をメモリ内で構築 |
| 7 | 同 `:595` | `_registry_rows` は attempt 0 件でも `registry-genesis` 1 行を作る。空 registry bytes ではない |
| 8 | 同 `:1050`、`:1071` | 完全性・seed・violation を確認後、`B4DesignNotFeasible(eligible_count=0, required_count=201)` を返す |
| 9 | `p3_b4_prerun_issuer.py:835` | 上記戻り値を `B4PrerunIssuerError` に変換して停止 |
| 未到達 | 同 `:878` → `:630` | `_publish_bundle` に到達しない。実際の `mkdir` は `:647` にあるため、root・registry・receipt の残骸は生じない |

ただし、事前登録不一致・既存 root・親不在・CSPRNG 失敗なら、それぞれの typed reason が先に返る。「空 batch なら環境によらず必ず同じ理由」とはしない。

**P3 の表示仕様には訂正が必要。** 発行器が外へ返す内容は次である。

- `reason.value`: `design_not_feasible`
- 例外メッセージの detail 部分: `fewer than 201 eligible scheduled attempts`
- `B4PrerunIssuerError`（`:100`）には **`.detail` 属性がない**。
- `eligible_count`／`required_count` は内部戻り値の属性で、発行器の例外には保存されない。

N1〜N6 の検算結果は以下。

| 前提 | 結果 |
|---|---|
| N1 | 正しい。201 適格行未満では封印 receipt を得られない。前 wave README の「封印発行は独立に閉じられる」は成立しない |
| N2 | 正しい。checkpoint の 5 field と WAL の genome／src_token から proposal document exact value は復元できない |
| N3 | base 4 行、sort 1 行、trigger 2 行、計 7 行すべて `success`。`rejected` 0 |
| N4 | `git check-ignore output/b4-prerun-publication` は rc=1。現物の `output/` は存在、publication root は不在。発行器 `:54` は自身の checkout を基準とする |
| N5 | 候補を成功行から作らない結論は採用。ただし理由 enum だけでは成功行の登録を禁止していない。台帳には `B4WhiteboardResult.SUCCESS` があり、適格性で除かれる。候補選別の根拠は本依頼と凍結述語 |
| N6 | 正しい。`results/<attempt_id>.json` は固定名予約を避けられる。ただし ID の安全性は別途必要 |

production 呼び出しは `orchestrator/campaign/` 内で定義以外 0 件だった。一方、test 内には support helper 以外にも直接呼び出しがある（`test_p3_b4_raw_record_producer.py:136` 等）。「唯一の既存呼び手」は test 全体の記述としては狭める必要がある。

driver 同定は、**loop 種別を示す `trial` の exact mapping を主とし、`search_config.axis` との対応を確認する**。ディレクトリ名の部分一致は使わない。

| `campaign.lock` の `trial` | `search_config.axis` | driver |
|---|---|---|
| `p3-s4-loop` | `silo-backoff-magnitude` | `base` |
| `p3-s5-sort-loop` | `silo-writeset-sort` | `sort` |
| `p3-s8a-trigger-loop` | `silo-backoff-trigger-gating` | `trigger` |

3 lock の値と、各 driver の設定生成位置（`p3_s4_loop.py:1486`、`p3_s4_loop_sort.py:316`、`p3_s4_loop_trigger_gating.py:610`）が対応する。axis 単独は探索軸の同定であり、その軸を扱う別種の campaign まで loop と認定する根拠にはしない。未知・不一致は入力解釈不能として報告する。

## 呼び手の形

P2 を採用し、追加は次の 2 ファイルとする。

| 新規ファイル・予定位置 | 内容 |
|---|---|
| `orchestrator/campaign/p3_b4_prerun_issue.py:1` | module 説明、import、trial と axis の小さな対応表 |
| 同 `:25` | campaign の JSON 読み取り、既存 checkpoint decoder による復元、候補選別 |
| 同 `:65` | 候補ごとの取得可能 field と出所欠落の集計 |
| 同 `:120` | batch をまとめ、欠落がなければ発行器を 1 回だけ呼ぶ関数 |
| 同 `:155` | `main(argv=None)`、JSON 出力、終了コード、`__main__` |
| `orchestrator/tests/test_p3_b4_prerun_issue.py:1` | 下記の焦点テスト |

行番号は author が確定後に変異 matrix へ実位置を記入する。発行器・台帳・事前登録・loop は変更しない。

CLI は次とする。

```text
python3 -m orchestrator.campaign.p3_b4_prerun_issue \
  --campaign-root ROOT_A ROOT_B ROOT_C
```

`--campaign-root` は必須、`nargs="+"`、`Path`。指定ディレクトリだけを読む。publication root・seed・真偽値・proposal hash を上書きする argv は設けない。

publication root は、呼び出し時に次で求める案を推奨する。

```python
issuer._REPOSITORY_ROOT / "output/b4-prerun-publication"
```

発行器の private 定数への限定的依存になるが、次の利点がある。

- import 済み発行器と同じ checkout を必ず参照する。
- `_preregistered_publication_root()` を直接呼ばず、事前登録 parser を複製しない。
- 最終的な名指しとの一致検査は既存発行器 `:194–223` が行う。事前登録が変われば拒否される。
- 既存 support と同様に `issuer._REPOSITORY_ROOT` の差替えだけで tmp 内を検証できる。

この値は import 時に別定数へコピーせず、実行時に読む。caller は `output/`、publication root、`results/` を作らない。

## field の組み方と fail-closed

以下で `C` は argv の campaign root、`D` は同 checkout の `docs/phase3-b4-reflux-ablation-preregistration.md` を指す。

whiteboard の `direction`／`magnitude` は planner の粗い射影、`delta_pct` は現物で null であり、proposal・workload・reference の代用にはならない。

| `B4ScheduledAttemptInput` の field | 出所／構成規則 | 現物からの可否 |
|---|---|---|
| `schema_version` | `p3_b4_analysis_ledgers.B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION` | 構成可能 |
| `attempt_id` | whiteboard iteration は `C/loop_state.json:whiteboard[i].iteration`。B-4 attempt への対応規約はない | **出所なし** |
| `registry_ordinal` | caller が明示入力順、各 whiteboard 配列順で候補を全件列挙した順番 | 構成可能。今回固定する順序規則であり、元の wall-clock 順とは主張しない |
| `block_id` | B-4 block への割当 artifact／規約がない | **出所なし** |
| `driver` | `C/campaign.lock:trial` と `search_config.axis` | 上表で構成可能 |
| `reason` | 完全な行を新たに予定 batch に加える操作なら `SCHEDULED` | caller の操作として構成可能。欠落を `CORRUPT` 等に読み替えない |
| `whiteboard_result` | `C/loop_state.json:whiteboard[i].result` | `rejected` の exact 値だけ採用 |
| `digest_red_classes` | `C/runs/wal.jsonl:stage=abort,payload.reason,payload.verify,payload.diff_quarantine` と候補への結合 | **出所なし**。候補と WAL の結合キーが checkpoint にない |
| `workload` | 候補に結合された workload と、D §5 が名指す校正済み PerfConfig | **出所なし**。lock の records／threads、digest の表示名では不足 |
| `calibrated_workload_member` | D `:163` の artifact path/hash、その校正 workload と候補 workload の所属照合 | **出所なし**。欄は未記入 |
| `initial_proposal_sha256` | 候補に結合された proposal document の canonical hash | **出所なし**。whiteboard／WAL に document がない |
| `bootstrap_member` | 事前固定した bootstrap 集合と当該 initial proposal の所属証拠 | **出所なし**。後述の理由で P1 は採らない |
| `reference_tps` | D `:588` の規則で一意に定まる祖先 certified snapshot の session throughput receipt | **出所なし** |
| `reference_snapshot_hash` | 上記で選定された snapshot の hash | **出所なし** |
| `reference_receipt_hash` | 上記 throughput receipt の hash | **出所なし** |
| `reference_is_unique` | 祖先関係、同着の不存在、PerfConfig／env_tag の一致による参照点特定 | **出所なし**。D `:163`、`:165` が未記入で、候補との祖先結合もない |
| `arm_digest_received` | precursor 生成時にどの digest を受けたかの実行記録 | **出所なし**。lock の `reflux="on"` は個別 iteration の受領証拠ではない |

digest の読み方自体は既存コードで確認できる。

- verify-red: `orchestrator/critic/digest.py:787`、abort の `payload.verify`。
- liveness／other: 同 `:822`、abort の `payload.reason`。
- diff-quarantine: `p3_s4_loop.py:938`、abort の `payload.reason="diff-quarantine"` と `payload.diff_quarantine`。
- screening は適格な 4 クラスに代入しない。

`rejected` の生成経路が diff-quarantine であることと、候補行に結合した digest 証拠が得られることは別である。WAL の時刻順・variant 順・iteration 番号の偶然の一致では結合しない。既存 digest reader にも prefix 容認の限定があるため、その出力を新たな正式証明として転用しない。

proposal hash は `p3_s4_loop.py:503` の処理と一致する必要がある。同処理は `b4_closed_critic_receipt_sha256` を除去して canonical JSON を hash 化する。genome hash／src_token／raw file hash への置換は不可。

**P1 は現状のままでは採らない。** 発行器が受け取る batch は非適格・失敗 attempt も含む台帳であり、「batch に入れた」だけでは事前固定 bootstrap 集合への所属証拠にならない。将来の publication の存在を要求する循環にもせず、現時点では「事前固定集合と proposal の対応証拠がない」と報告する。親が P1 を採る場合は、何を bootstrap 集合としていつ固定するのかを明示してから author へ渡す必要がある。

処理順は次に固定する。

1. 指定 campaign の checkpoint と lock を読み、`result == "rejected"` だけを候補にする。
2. 全候補の欠落を集計する。最初の field だけで報告を打ち切らない。
3. 欠落が 1 つでもあれば `reason="scheduled_input_sources_missing"` の JSON を stdout へ出して rc=2。発行器は 0 回。
4. 候補 0 件なら `scheduled_inputs=()`、`planned_result_artifacts=()` で発行器を 1 回呼ぶ。
5. 発行器の例外は `reason.value` と、`str(exc)` から既知の `reason + ": "` 接頭辞を除いた `detail` を JSON 化して rc=2。
6. 成功時だけ receipt の 3 field と `manifest_row_count=len(publication.manifest.rows)` を出して rc=0。

欠落報告には候補の `campaign_root`、whiteboard index、iteration、field 名、参照した artifact path/key、欠落の説明を含める。未定義 artifact の架空ファイル名は作らず、例えば bootstrap の場合は `artifact_path: null` として必要な証拠を説明する。

現物の候補では上表の 12 field が未解決になる。欠落を false／None／空文字で埋めて台帳型へ渡さない。本 wave で非空 batch の出所を新設する計画は含めない。

## planned result path

P4 の配置規則を採用する。

```text
<publication_root>/results/<attempt_id>.json
```

発行器 `:457` の予約は root 自体、および次の 5 名とその配下である。

- `scheduled-attempt-registry.jsonl`
- `analysis-manifest.json`
- `prerun-issuer-receipt.json`
- `.prerun-issuer-receipt.tmp`
- `raw-record-rejections.jsonl`

`results/` は衝突しない。`_inspect_result_leaf_absent`（`:226`）は途中の未存在 component で通過するため、事前の `results/` 作成は不要。既存 leaf、symlink component、非 directory component は発行器が拒否する。

ただし、台帳の `_is_text` は path-safe ID を保証しない。一般の attempt ID に `/` や `..` が含まれてよいとはしない。

本 wave では attempt ID 規約を新設しないので、非空候補はその欠落段階で停止する。将来 campaign ID + iteration を採用する場合も、任意の directory basename を無検査で連結せず、canonical campaign identity、iteration の整数域、衝突、単一 path component であることを規約として決める必要がある。P4 は配置案の採用であり、非空経路の実行可能性を意味しない。

## test

新規 `orchestrator/tests/test_p3_b4_prerun_issue.py` に以下を置く。既存 test の期待値は変更しない。

| node 候補 | 内容 |
|---|---|
| `test_success_only_calls_empty_issuer_once_without_publication` | 正しい lock と全 `success` checkpoint の fixture。support の `preregistered_publication_root` を利用し、発行器 `_REPOSITORY_ROOT` を tmp へ向ける。実発行器を wraps で数え、空 tuple 2 本・呼出し 1 回・rc=2・exact reason/detail・root 不在を確認 |
| `test_rejected_reports_all_missing_sources_without_issuer` | `rejected` 1 行の fixture。発行器を spy にし、12 field の欠落一覧、path/key、rc=2、呼出し 0 回を確認。真偽値 3 field と `arm_digest_received` の欠落も個別に assert |
| `test_fail_is_not_a_rejected_candidate` | `fail` 行を含めても候補 0 件となることを確認 |
| `test_publication_root_override_is_not_an_argument` | `--publication-root` を拒否し、発行器を呼ばないことを確認 |
| `test_issuer_success_serializes_receipt_and_returns_zero` | 発行器の戻り値だけを stub 化し、成功 JSON と rc=0 を検証。fixture 201 行の実発行はしない |

最初の test は 3 driver の lock を一緒に与え、campaign ごとに発行器を呼んでしまう変異も検出する。cwd を別 tmp に変えても、issuer の checkout root を使うことを確認する。

全 test は小さい JSON と in-process 呼び出しで構成し、build・計測・201 行 fixture 発行を追加しない。実装後の実行は `tools/run_tests.py` 経由とし、5 分受入上限への影響は実測で確認する。本段では未実行。

## 変異 matrix の事前登録候補

対象行は前述の新規配置目安。author 完了後に実 line へ置換する。

| 変異 | 対象 | 期待 KILLED node |
|---|---|---|
| `== "rejected"` を `!= "success"` に変更 | issue module `:25` の候補選別 | `test_fail_is_not_a_rejected_candidate` |
| 欠落があっても発行器を呼ぶ | 同 `:120` の欠落分岐 | `test_rejected_reports_all_missing_sources_without_issuer` |
| 真偽値 3 field を根拠なしに True で補完し、欠落報告から除く | 同 `:65` の field 解決 | 同上。rc だけでなく field 集合を検証する |
| `arm_digest_received` を無条件 False にする | 同 `:65` | 同上 |
| campaign ごとに発行器を呼ぶ | 同 `:120` | `test_success_only_calls_empty_issuer_once_without_publication` |
| root を cwd 基準に変更 | 同 `:120` | 同上 |
| publication root を argv から受理 | 同 `:155` | `test_publication_root_override_is_not_an_argument` |
| 拒否時も rc=0 | 同 `:155` | 最初の 2 node |
| 空候補なら発行器を呼ばず成功扱い | 同 `:120` | `test_success_only_calls_empty_issuer_once_without_publication` |
| `exc.detail` を参照 | 同 `:155` | 同上 |
| 成功時 receipt field／manifest row count を欠落・誤出力 | 同 `:155` | `test_issuer_success_serializes_receipt_and_returns_zero` |

未到達の代入だけを変える変異は、他の欠落に隠れて surviving になり得る。「True 固定」は field 解決結果または欠落一覧を変える位置に置く。KILLED は期待であり、実測結果ではない。

## 焦点テスト集合

`rg -n` による再帰検索で、以下を確認した。

直接・間接の発行器 consumer として、まず新規 test と次の 4 ファイルを焦点集合にする。

| ファイル | 根拠位置 |
|---|---|
| `orchestrator/tests/test_p3_b4_prerun_issuer.py` | `:14` import、`:496` 不足時停止、`:697` root 配下 result 許可 |
| `orchestrator/tests/test_p3_b4_raw_record_producer.py` | `:31` import、`:136` 発行 |
| `orchestrator/tests/test_p3_b4_material_report.py` | `:399` support 経由で発行 |
| `orchestrator/tests/test_p3_b4_producer_auth_experiment.py` | `:367` subprocess 内 import、`:796` issuer patch 対象 |

`p3_b4_producer_auth_experiment.py:457` 以降の発行器に対する 3 本の exact patch 錨は no-touch のまま保持する。

新 module が走査対象になる既存検査は以下。これらの期待集合を増減して通す計画にはしない。

| 検査ファイル／走査位置 | 新 module に対する関係 |
|---|---|
| `test_p3_exploration_namespace.py:138` | campaign driver 発見。新 caller は campaign root creator ではないため driver registry に追加しない |
| `test_p3_build_authority_cli.py:1222` | manual build module 列挙 |
| `test_p3_b4_analysis_path.py:303` | `evaluate_analysis` production caller 列挙 |
| `test_s8b_floor_campaign.py:1722`, `:8028` | use_perf／build 等の production site 列挙 |
| `test_s8b_floor_stats.py:1621` | floor verifier caller 集合 |
| `test_s8b_ratified_freeze.py:2672` | loader 外の `RatifiedFreeze` 構築禁止 |
| `test_s8b_oracle_manifest_contract.py:49` | oracle loader／verifier consumer 集合 |
| `test_s8b_oracle_report.py:5816` | observations builder caller 集合 |
| `test_p3_s4_loop.py:2206` | backoff materialization 入口列挙 |
| `test_t1286_commit_receipt.py:802`, `:819` | commit writer／verification capability issuer 集合 |
| `test_t338_submission_gate_unit5.py:494` | receipt publish call-site 検査 |
| `test_ccbench_spawn_sites.py:423`, `:473`, `:579` | process／run_once／calibration issuer site 列挙 |
| `test_s1_known_axes_freeze.py:641`, `test_reflux_ir.py:293` | production から test golden 参照禁止 |
| `test_login_headroom.py:1630` | budget 定数の定義箇所 |
| `test_pegasus_dispatch_compute.py:2249` | qdel caller 集合 |

補助検査は `tools/check_subprocess_bytecode_guard.py:64` の Python 全体走査、`tools/scan_env_coincidence.py:142` の指定 root 直下走査。後者は campaign root を対象に実行した場合に新 module を含む。

provenance は `tools/check_ai_provenance.py:75`、`:1583`、`:1599` により新 module と test の双方が実装面となり、D95 の Codex author 帰属が必要。commit 後に既存 provenance checker を実行する。

`tools/check_docs.py` と `tools/check_codex_agents.py` の検索では、新 campaign module 名の登録が必要な固定列挙は見つからなかった。通常の完了検査として両 checker を実行する。広い AST 走査は該当 node または受入全走で確認し、新規 test のために重い既存ファイル全体を重複実行しない。

## 親が実発行を 1 回試みる手順

author 実装と必要な確認が済んだ後、親が wave worktree から次を **1 回**実行する。以下は手順案であり、本段では実行していない。

```bash
cd /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-prerun-issue-caller

b4_job_dir=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-prerun-issue-caller

if python3 -m orchestrator.campaign.p3_b4_prerun_issue \
  --campaign-root \
  output/campaigns/p3-s4-loop-s4-autonomous-0b53a387 \
  output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d \
  output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5 \
  > "$b4_job_dir/prerun-issue.stdout.json" \
  2> "$b4_job_dir/prerun-issue.stderr.txt"
then
  b4_issue_rc=0
else
  b4_issue_rc=$?
fi
printf '%s\n' "$b4_issue_rc" > "$b4_job_dir/prerun-issue.rc.txt"
```

保存先が既存なら上書きせず、未使用名を先に選ぶ。再発行で採り直さない。

現物が変わらなければ、候補 0、空 batch 発行 1 回、rc=2、次の reason/detail になる。

```json
{
  "reason": "design_not_feasible",
  "detail": "fewer than 201 eligible scheduled attempts",
  "candidate_count": 0
}
```

実装する JSON には campaign 別の観測件数も含め、欠けている入力として「`rejected` precursor が 0 件」を明記する。候補がないので、架空の候補に対する 12 field 欠落は作らない。

root は `<worktree>/output/b4-prerun-publication`。実行後に root が不在であることを確認し、stdout・stderr・rc、使用 checkout／commit、観測件数を親の記録へ保全する。insight には生 JSON と本計画の不足 field 表を根拠として残し、「発行器まで到達して拒否された」と「封印発行成功」を区別する。

## リスクと未確定点

- **今回閉じられるのは production 呼び出し経路と不足入力の可視化。** 201 適格行の調達、封印 receipt 取得、実走可能性は閉じない。
- **P1 は親の裁定対象として残る。** publication 不在だけを所属否定の理由にすると循環する。一方、任意の batch 登録だけで True にするのも事前固定集合の証明にならない。本案は証拠未解決として停止する。
- **identity 規約は未決定のままとする。** `rejected` が現れた段階で、B-4 attempt／block と元 campaign iteration の対応、proposal document、WAL attempt、祖先 snapshot の結合が必要。carrier 新設は本 wave に含めない。
- **driver 同定と採用資格は別。** 現行 §5 の選択 driver は base。将来 sort／trigger に赤が現れても base へ読み替えず、無断で母集合に混ぜない。今回それらは他の出所欠落とともに停止する。
- **digest 非汚染も未証明。** `reflux="on"` を False の根拠にも、全 iteration が受領した証拠にも使わない。
- **順序規約には将来の意味がある。** argv 順と whiteboard 配列順を固定し、201 超過時に結果を見て並べ替える用途へ使わない。
- 非空 batch が今は構成不能である点を module の説明に明記する。未存在の入力形式、汎用 resolver、互換層を追加して成功経路を装わない。

## 総括

P2・P3・P4 を採用し、P1 は「batch 所属だけでは根拠不足」として採らない案を推奨する。

追加は caller module と test の 2 本。現物では空 batch を発行器へ 1 回渡し、`design_not_feasible`・非 0・root 残骸なしを確認する。`rejected` 行が現れた場合は、出所欠落 field を全件報告して発行器を呼ばない。201・凍結契約・既存発行器を変更しない。