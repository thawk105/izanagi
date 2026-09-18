## 1. 永続面と envelope

**P1 は別ファイル専用 writer を harness 内に置く形で採用する。WAL writer の直接流用は不可。**

以下の行番号は現 checkout のもの。`C/` は `orchestrator/campaign/`、`T/` は `orchestrator/tests/` を表す。

- [layout.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/campaign/layout.py:207) の `wal_file` の直後に、`agent_outputs_file` property を追加する。戻り値は `os.path.join(self.runs_dir, "agent_outputs.jsonl")`。`ensure()` の既存 `runs_dir` 作成で足りる。
- WAL の record 型は `C/model.py:188` の `WalRecord`。`C/wal.py:380` が envelope の exact 5 key、392 が評価用 stage の白名簿を検査する。
- framing は `C/wal.py:437` の `_iter_binary_frames` と452の `iter_lines`。459で改行終端のない最終行を拒否する。**この reader は AO に再利用できる。**
- 追記経路は `C/wal.py:1587` の `log` →1407の `append` →1186の `_append_record`。1278で書込み先を `layout.wal_file` に固定し、1284で `flock`、1288で末尾検査、1330で short write を含む追記、1342で file、1360で runs directory を `fsync` する。
- これは排他された durable append であり、クラッシュ時に「必ず行全体か無書込みになる」保証ではない。部分行は残り得るため、次回読取り・追記で拒否する。

`parse_line` と `_record_to_line` は評価用 stage に閉じており、writer は commit receipt・admission にも結び付く。`wal_file` を差し替える adapter や WAL stage の拡張は採らない。A1 が `p3_s4_loop.py` 内に AO 専用の parse/read/append を置き、上記の排他・short write・fsync 手順を限定的に踏襲する。`wal.py` は編集しない。

payload は次で固定する。

```text
output          役割の構造化出力全文
input_sha256    実際に渡した役割入力射影の canonical SHA-256
provenance      mode、出力原本 path/raw SHA、入力原本 path/raw SHA
refs            明示的に渡された WAL source-ref の配列
digest_sha256   critic のみ必須。実際に渡した digest の raw-byte SHA-256
```

writer と renderer の両入口で、exact envelope、stage 3 種、型、非有限数、JSON duplicate key、空行、未終端行、不正 UTF-8、payload 必須 key を検査する。重複は以下を区別する。

1. envelope 全体の canonical hash の完全重複。
2. `stage + input_sha256 + canonical(output)` が同じ再取込み。時刻や provenance の変更だけで重複を回避させない。

追記は **同じ flock の内側で既存全行の検査・重複検査・append** を行う。壊れた既存 file を切り詰めたり、重複を黙って skip したりしない。

## 2. 書き手と CLI

[load_proposal_file:2254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/campaign/p3_s4_loop.py:2254) は現状、全文保存に必要な情報を戻していない。

- 2274で原文 bytes を読む。
- 2347で planner/coder を取り出す。
- 2350で K2 coder 出力を消費する。
- 2357で dataclass に縮約するため、`knowledge_use`、`classification`、`data_boundary_report` などを dataclass から復元することはできない。

**挿入案：**

- loader の既存戻り値3要素は維持する。任意の keyword-only capture 引数で、検査成功後に原文 bytes と `d["planner"]` / `d["coder"]` の全文を記録専用コンテキストへ渡す。loader 自身は追記しない。
- `main:2779` の loader 呼出しから `drive_iteration:2794` へ、このコンテキストと planner/coder それぞれの入力射影を渡す。
- `drive_iteration:2493` の入口停止 return の後、2498の `_run_one_iteration_resolved` の前に、planner/coder の2 event を live 追記する。入口停止なら追記しない。
- live 記録時点では評価 variant が未確定なので、両 event の `variant` は `null`。評価後に既存行を書き換えない。

役割入力は loader に存在しないため、**proposal 自身を hash して `input_sha256` と呼ぶ実装は禁止**。新しい live 記録用の任意引数 `--agent-inputs INPUTS.json` を設け、内容を `{planner: <実入力>, coder: <実入力>}` とする。指定時は両入力を必須にする。既存呼出しは記録なしの互換経路として維持する。この制約により「全 legacy caller が自動的に全文を記録する」とは主張できない。

取込み CLI は次を提案する。

```text
--record-agent-output {planner_proposed,coder_proposed,critic_attributed} FILE
--agent-campaign-dir DIR
--agent-input INPUT.json
[--agent-output-key {planner,coder}]
[--agent-variant WAL_VARIANT]
[--agent-digest DIGEST.txt]
[--agent-wal-ref wal:SHA256 ...]
```

`--agent-output-key` は proposal file 内の役割 object を選択する場合だけ使う。指定なしは role 出力 file 全体を使う。

`main:2595` の parse 直後に専用分岐し、以下と排他にする。

- `--run-iteration`、`--emit-planner-context`、`--no-build`、fixture `--value`
- build authority、worktree/build receipt、B4、knowledge、reflux、policy の実行用 option
- live 用 `--agent-inputs`

既定値との比較だけでは明示指定を識別できないため、option の指定有無で排他を検査する。取込み専用 option の単独使用も拒否する。

専用分岐は `C/p3_s4_loop.py:2667` の knowledge 解決、2676の build opt-in、2678の site 解決より前に return する。**login node で呼べる。** 評価経路の `_admit_env_contract` は変更しない。取込み時の `env_tag` は呼出しホストから作らず、対象 campaign の既存 WAL と lock から確認する。

親は入力・役割出力を用意してこの CLI を呼ぶだけであり、AO file の書き手は harness のままである。`ts` は取込み時刻と明記し、role 実行時刻を遡及して捏造しない。

未評価 proposal-3 は **`variant=null`** を採る。`diffq_variant_id:914` は検疫 reject 用で、920の説明と935の `diffq-` prefix がその意味を固定している。通常の未評価提案に流用すると、reject や評価済み variant と誤認させる。

## 3. 入力側防壁の分離

[planner_context_payload:1222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/campaign/p3_s4_loop.py:1222) の出力は現在、whiteboard・任意 knowledge_input・任意 policy_hint だけである。`project_whiteboard:1176`、`whiteboard_for_planner:1198` に file/layout 引数はない。

次を `T/test_p3_s4_loop.py:3081`、6396、6407付近へ追加する。

- 3関数の signature に AO・layout・path・記録コンテキストを追加していないこと。
- AO reader、`open`、`Path.open/read_text/read_bytes` を呼ぶと失敗する状態で、3関数を実行できること。
- 同じ state/cfg に対して、AO が不在・正常・壊れている場合で入力射影が不変であること。
- role 出力に機序テキストを入れて保存しても、whiteboard は既存5 field、planner context は既存 key 集合のままであること。
- AST で3関数と既存の直接 helper 呼出しを検査し、AO reader への新規依存を拒否する。実行検査と組にし、文字列不在だけを防壁としない。

**P4 の非 null delta は棄却する。** `C/p3_s4_loop.py:1315` は `_DELTA_PCT_LIVE = False`、1213で非 null を拒否し、1964の成功経路も明示的に `delta_pct=None` を渡す。`WhiteboardLeakError:1305` と復元時検査1381を維持する。2点測定できたことだけでこの防壁を開けてはならない。

## 4. renderer

[layer3_report.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/campaign/layer3_report.py:97) 以下を A2 が変更する。

| アンカー | 変更 |
|---|---|
| 97 `canonical_record_ref` | kind に `ao` を追加。canonical envelope 全体の SHA-256 |
| 141 `_read_wal` 近傍 | AO reader 呼出しと `Layer3ReportError` への変換 |
| 246 `_report_primary_refs` | `agent_outputs` の全 envelope を走査して AO hash を数える |
| 263 `_assert_bijection` | keyword-only `agent_outputs=()` を追加し、期待 multiset に AO を加える |
| 771〜806 | whiteboard と独立に AO の存在・通常 file・読取りを確認 |
| 874〜914 | AO 一次配置、critic 射影、provenance、双射引数を追加 |
| 12 | 「常に空」「版を上げるまで解除しない」の stale docstring を更新 |

**一次配置は、3 stage 全部を `agent_outputs` 配列へ envelope のまま置く。** `mechanism_hypotheses` は critic だけの二次 view とし、二重計数しない。

```text
mechanism_hypotheses item:
  variant
  attribution       = payload.output.attribution の逐語
  source_ref        = ao:<envelope canonical SHA-256>
  refs              = payload.refs のそのままの値
  digest_sha256     = payload.digest_sha256
```

数値、verdict、WAL ref を attribution の文章から抽出・推定しない。全文は一次配置に残る。view は独立に作り直した期待射影と比較し、存在する別 AO ref への付替え、critic view の欠落・重複、attribution の改変も拒否する。

`refs` は実在する対象 campaign の一次 WAL ref と照合する。critic の `variant` は対応する WAL variant を要求する。planner/coder の `null` は評価済みを意味しない。

不在時は次を新 renderer が必ず出す。

```json
{
  "agent_outputs": [],
  "mechanism_hypotheses": [],
  "mechanism_hypotheses_provenance": "absent"
}
```

存在時 provenance は `"agent_outputs"`。空 file と不在を区別する。dangling symlink、読取り失敗、途中不正行を不在扱いしない。AO の読取り時 bytes hash と `artifact_refs` 発行時 hash も照合し、途中追記された別 snapshot を混在させない。

P3 は**親の自由な節切りを採らず、harness の決定論的な節抽出**を推す。旧 critic 原本は `verbatim/critic-1.md:8,16,34,66,105,116` にあり、実際には4節だけではない。数字に依存せず attribution/recommend/avoid/uncertainty の見出しを一意に識別し、その節の文字列を保存する。追加節は `raw_markdown` 全文に残す。欠落・重複見出しは拒否し、要約で補わない。

## 5. schema と旧 artifact

[layer3_schema.json:283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/campaign/layer3_schema.json:283) に次を加える。

- `verifications.items.properties.commit_witness`：object。`commit_counts` / `batch_commit_counts` は integer または null。
- `proof_surfaces`：object。`protocol` は string または null、`X/P/I` は `evidence-present` / `evidence-absent` / `unavailable`。
- どちらも `verifications.items.required` には追加しない。

根拠は実 producer の `C/pipeline.py:575`、633〜642、型の365〜366、`orchestrator/verifier/model.py:58,84`。`C/layer3_report.py:512` の `_view_row` で消さない。D829 と一致する。

その他の位置は次のとおり。

- 348：`mechanism_hypotheses.maxItems:0` を前節の items 定義へ置換。空配列は許す。
- 348付近：`agent_outputs` と `mechanism_hypotheses_provenance` を optional property として追加。
- 291：source-ref pattern を `^(wal|wb|ao):[0-9a-f]{64}$` へ拡張。
- 350以降：AO envelope/payload と `ao_ref` の definitions を追加。
- 27の top-level `required` と29の v3 const は維持する。新 item 内の必須 key は定義する。

[D828.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2746-k2-loop-round2/rulings/D828.md:3) の逐語は「`schema_version` を上げない。`required` も変更しない。」である。今回の optional 追加と空配列制約の緩和にもこの方針を適用する。ただし、D828 が明示した対象は `runs.items.properties` であり、今回全体を逐語で直接認可しているとまでは扱わない。

`git grep -l '"layer3-material-report/v' -- output` から得た report 8件を実際に読み、次を確認した。各 JSON の起点は `:1`。

| 保存済み artifact | 版・現物 |
|---|---|
| `output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json` | v1、MH=[]、`aborts`・`whiteboard_provenance`・admission がない |
| `p3-s8a-trigger-sweep-{balanced,read-heavy,write-heavy}-sweep-*` の6件 | v2、MH=[]、新2区画なし |
| `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/reports/layer3_report.json` | v3、MH=[]、新2区画なし |

**「既存 v1/v2/v3 全体が新 schema でも妥当」は確定できず、v1 については現状と矛盾する。** `C/layer3_report.py:307` にあるのは v2 reader の導出だけである。v1 は版 const と必須項目・構造が既に異なる。`T/test_layer3_report.py:1656` も明示的に v1 の runs-item だけを対象とし、全文の可読性を保証しない。

v2/v3 の今回追加部分は optional なので、読んだ既存形を排除しない。完全な schema validation は未確認。v1 reader 新設は本 scope に含めず、既存不一致として親へ返す。

generator SHA の閉包は次のとおり。

- `C/layer3_report.py:882` が自己 file hash を埋めるため、新規 report の SHA は必ず変わる。
- 保存済み generator SHA は `89aa98e8…`、`705508de…`、`abe0529d…`。全文 SHA の `git grep` 一致は上記8 artifact のみで、旧 SHA を literal pin する test・台帳は見つからなかった。
- 現行 file SHA は `a5f66ea5…`。`orchestrator/`、`tools/`、`docs/`、`output/s8b-freeze/` の exact 検索は一致なし。
- **動的な影響はある。** `C/autonomous_trial_completeness.py:4652` は fresh report を作り、4687〜4721の比較射影は `generated_from_head` だけを除去し、generator SHA を残す。旧 report と現行再生成との一致は保証できない。新 optional 区画にも旧側の補完はない。
- 既存 artifact を再生成・更新して帳尻を合わせない。この consumer の互換拡張は所有外であり、本 wave が解決済みとは扱わない。

D830 対応として、verification payload の key は `C/pipeline.py:633` と実 producer emit から導出し、`_view_row` 後の集合が schema に収まることを検査する。手書き key 定数だけの一致で閉じない。

## 6. 既存 pin の閉包

[T/test_t126_pegasus_tools.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/tests/test_t126_pegasus_tools.py:463) などから、保持すべき箇所は以下。

| pin 元 | 保持する現物 |
|---|---|
| `test_official_perf_closure.py:57,246` | renderer の対象集合登録と `_validate_schema` → `validate_perf_observation` 呼出し。`C/layer3_report.py:324` を保持 |
| `test_t126_pegasus_tools.py:463` | `C/layer3_report.py:764` の `_reject_qualification_ancestry(...)` の改行・字下げを含む exact 文字列 |
| 同471、476 | 同800の `if _contains_qualification_lineage(lock):`、843の records 版 |
| `test_campaign.py:5397,5479` | `p3_s4_loop.py` の `run_campaign` 呼出しは1個。現物1946の呼出しと authority/use-class kwargs を保持 |
| `test_ccbench_spawn_sites.py:135` | renderer `_git_head` の subprocess site は1個。現物193〜195を保持し、新規 spawn を増やさない |
| `test_layer3_report.py:439` | 独立 schema fixture の `mechanism_hypotheses: []`。既存空形の正例として維持 |
| 同1820 | schema v3 const と既存 runs required の固定 |

これらは大部分が物理行番号自体の pin ではなく、文字列・AST 呼出し・件数の pin である。上方への追加で行番号が移動することと、保護対象の内容を変えることを区別する。

[hooks/guard_write.py:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/hooks/guard_write.py:58) は68で `parts[1] == "runs"` を判定し、leaf 名を限定していない。既存の official/exploration campaign root 配下なら AO も対象になるため、**hooks 変更は不要**。ただし、これだけで全ツール経路や別 submit-tree への実効発火を証明したとはしない。

## 7. テストと変異候補

[T/test_layer3_report.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/tests/test_layer3_report.py:211) の `_campaign`、804の `_record`、808の `_bench` を renderer fixture に再利用する。

A1 は `T/test_p3_s4_loop.py:6145` の `_tmp_layout`、546の proposal fixture、7056の public drive、7354の K2 loader 正例を基礎にする。記録機構自体は stub せず、実 writer の bytes を読む。

| 最小テスト群 | 固定する条件 |
|---|---|
| live 正例 | 完全な入力・出力を渡し、planner/coder 2行、mode=live、全文・入力hash一致 |
| live 停止 | `stopped-before` ならAOを作らない |
| CLI 正例 | 3 stage の取込み、mode=ingested、原文hash一致、WAL不変 |
| login / 排他 | site/build/evaluation 関数を呼ぶと失敗する条件でCLIが完了。実行用 option 混在は拒否 |
| framing / stage | 未知stage、blank、途中不正JSON、未終端最終行、nested duplicate keyを拒否 |
| 重複 / I/O | 同じ出力の再取込み、short write、fsync失敗、壊れた既存fileへの追記を検査 |
| 不在 provenance | AO不在で空2区画+absent。空fileはpresent。読取り失敗は拒否 |
| 双射 | 3 stage 全てを数え、削除・重複・等件数置換を拒否 |
| critic view | 帰属逐語、参照・digest一致。view欠落・改変・別event参照を拒否 |
| 入力分離 | §3の実行・signature・AST検査 |
| schema互換 | 439の旧fixture、2501のv2、2575の旧v3を維持。verification新2keyは実producer由来で追加 |

双射負例は `T/test_layer3_report.py:1567` の等件数置換、framing は3599以降、重複は3718、不在は1861の構成を踏襲する。hook 判定の正例を足す場合も所有内 test から既存関数を呼び、hooks 本体は変えない。

段6の変異 matrix は少なくとも次の10述語を対象にする。

1. 未知 stage の白名簿検査を外すと赤。
2. 未終端行を黙って捨てると赤。
3. 時刻を変えた再取込みを許すと赤。
4. planner/coder を一次配置から落とすと赤。
5. critic を一次配置と view で二重計数すると赤。
6. input 側 expected Counter を report 側から作ると、等件数置換で赤。
7. attribution または source_ref を別 critic の値へ替えると赤。
8. AO不在の provenance を present にすると赤。
9. 入力 builder が AO を読むと赤。
10. K2 coder の外側 metadata を落とす、または `input_sha256` を proposal hash に替えると赤。

**本段では pytest・build・計測を実行していない。緑の報告はない。**

## 8. A の実測を B へ取り込む順序

**A の job は現行 main のまま1回だけ走らせ、B 着地後の harness を別コード位置から起動して submit-tree の campaign へ取込む。評価済み submit-tree のソースを後から差し替えない。**

対象は指定どおり、

```text
<submit-tree>/output/exploration/campaigns/
p3-s4-loop-s4-autonomous-409e13f8/
```

である。render 口は [C/layer3_report.py:1084](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2746-k2-loop-round2/orchestrator/campaign/layer3_report.py:1084)。

手順は次とする。

1. **A の terminal を確認する。** `continue` の場合だけ critic-2、planner-3、coder-3 を各1回起動し、proposal-3 保存で止める。
2. 役割起動時の完全入力を保存する。新しい入力から過去の入力hashを作らない。
3. B のCLIで以下5 event を順に取込む。
4. AO を閉じた後に renderer を実行し、新規材料レポートを insight に保存する。

| 順 | stage / 出力 file | `input_sha256` の計算元 | variant |
|---|---|---|---|
| 1 | planner_proposed / 既存 `materials/proposal-2.json` の planner | 1巡目の `materials/planner-input-2.json`。実際の追加指示があればそれも含む完全射影 | 今回評価のWAL variant |
| 2 | coder_proposed / 同 coder全文 | **coder-2へ実際に渡した完全入力** | 同上 |
| 3 | critic_attributed / 新規 `verbatim/critic-2.md` 原本 | critic-2へ渡した digest・付記を含む入力JSON | 同上 |
| 4 | planner_proposed / 新規 `materials/proposal-3.json` の planner | 新規 `materials/planner-input-3.json` の完全射影 | null |
| 5 | coder_proposed / 同 coder全文 | 新規 `materials/coder-input-3.json` の完全射影 | null |

既存 proposal は `output/insights/2026-09-16/t2588-k2-loop-roundtrip/materials/proposal-2.json:1` を読んだ。coder の外側 metadata を含めて保存する。

**coder-2 の完全入力 file は未確認。** 旧 repo materials と旧 job materials の列挙では独立した coder input を見つけられなかった。planner input・knowledge input・leakproof文書を推測で連結して「実入力」としてはいけない。親の role 起動原文から回収できなければ、必須 `input_sha256` を満たす2番の取込みは未完了として残る。

critic の `digest_sha256` は campaign の `s4_loop_digest.txt` の実bytesから計算する。`refs` は今回読んだ WAL record から機械的に canonical ref を作り、critic の文章から採掘しない。

render はB側コードで次の形とする。

```text
python3 -m orchestrator.campaign.layer3_report \
  <campaign-dir> <insight>/layer3_report.json \
  --output-root <submit-tree>/output
```

**期待件数 `WAL + whiteboard 2 + AO 5` は、現行経路からは導出できない。**

`C/p3_s4_loop.py:2483` は対象 layout に checkpoint がなければ新規 state を作り、2495で1回増やす。新規 submit-tree で1評価なら campaign-local whiteboard は通常1件である。2件になる既存テスト7056も、同じ layout に public drive を2回呼んでいる。

したがって本巡の式は、

```text
source_refs 件数 = renderer が採用した WAL record 数
                + 実際の loop_state.whiteboard 件数
                + 5
```

通常は **`W + 1 + 5`**。生WALに trigger binding record があれば `C/layer3_report.py:159` で一次射影対象から外れるため、単なる物理行数とも区別する。`W` の実数は本巡実走前のため未確認。

旧 whiteboard の複製・合成、delta gate の変更で `+2` に合わせる案は採らない。実際に継承済み checkpoint が存在するなら、その原本と由来を別途確認する必要がある。

P4 の残りは次のように修正する。

- `current_perf` / `leading_indicators` は今回の `bench_done` に基づく。
- whiteboard と `last_delta_pct` は現物から取り、現行の delta は null を維持する。
- `prior_critic_reverse` は親の解釈として保存し、critic診断が生成入力へ機械還流したとは書かない。
- `orchestrator/calibrator/runner.py:803` は偶数repsの中央2件から abort率・latency を集約する。旧「速い側」の説明を再利用しない。
- `orchestrator/critic/digest.py:65` の列は throughput/abort/LLC/IPC。latency は列にない。欠測を補完しない。

## 契約

A1/A2 の独立実装用境界を以下に固定する。配置根拠は `C/p3_s4_loop.py:2254`、`C/layer3_report.py:97,246,263`。

| 項目 | 固定内容 |
|---|---|
| A1所有 | `p3_s4_loop.py`、`layout.py`、`test_p3_s4_loop.py` |
| A2所有 | `layer3_report.py`、`layer3_schema.json`、`test_layer3_report.py` |
| 共通reader | A1提供 `read_agent_outputs(layout) -> list[dict]`。存在判定は呼出側、存在fileの不正は例外 |
| 共通例外 | A1提供 `AgentOutputError(ValueError)`。A2は `Layer3ReportError` に包む |
| envelope | exact `{ts, stage, variant, env_tag, payload}` |
| stage | `planner_proposed` / `coder_proposed` / `critic_attributed` のみ |
| variant | planner/coderは string または null。criticは対象WALのstring |
| payload共通必須 | `output`、`input_sha256`、`provenance`、`refs` |
| provenance必須 | `mode`=`live\|ingested`、`source_path`、`source_sha256`、`input_path`、`input_file_sha256` |
| critic追加必須 | `digest_sha256`。output は `raw_markdown` / `attribution` / `recommend` / `avoid` / `uncertainty` |
| output保持 | planner/coderはrole object全文。K2外側metadataを削らない |
| canonical | UTF-8、`sort_keys=True`、`ensure_ascii=False`、`separators=(",", ":")`、非有限数拒否 |
| input hash | 実役割入力JSON全体のcanonical bytes。raw file hashと区別 |
| source-ref | `ao:` + envelope全体canonical SHA-256。payload内refsは `wal:` |
| 一次配置 | report `agent_outputs` に3stage全てをenvelopeのまま保存 |
| 二次view | criticだけを `mechanism_hypotheses` に決定論射影 |
| 不在表示 | `mechanism_hypotheses_provenance="absent"`。存在時 `"agent_outputs"` |
| schema | v3据え置き。新top-level propertyはoptional、新rendererは常に発行 |

## 総括

P1は専用 writer と早期 return の取込み口、P2はv3据え置き、P3は原文を保持した harness の決定論抽出を推す。P4の「非 null delta」「新規 campaign の whiteboard 2件」は現物に反するため棄却する。

親へ返す未解決点は、**coder-2実入力の回収、v1全文可読性の既存不一致、旧 report と fresh consumer 比較への波及**。編集・commit・push・pytest・計測は行っていない。

メモリ内 schema 検証は自動 PreToolUse 検査に拒否された。対象は保護 campaign の JSON を読む heredoc で、理由は「保護パスと不透明構文の同居は分類不能」。完全な schema 検証結果は未確認としている。