# [T-2182] 段 4 loop の評価経路が build まで通り、凍結 pin と verifier の非互換が露出した (2026-09-09)

wave: `dev-wave-t2182-k2-eval-run` / branch `worktree-dev-wave-t2182-k2-eval-run`
基点 main: `7f17e1c63`。**実装面の差分ゼロ** (実測と記録だけの wave)。

## 一行で

**前 wave の配線は効いた。K2 の知識入力は評価経路で消費され、候補の build と WAL の provenance へ
反映された。** 完了条件は 09-02 の 1/4 から **3/4** へ進み、残る 1 件 (gate の terminal verdict) で
止まっている。止めているのは環境でも配線でもなく、段 4 loop が literal 保持している CCBench の
凍結 pin と、現行 verifier が要求する trace 形式の版の食い違いである。**評価経路が build へ
到達したことで初めて露出した。**

途中、production の K2 consumer が規律 6 で 1 本を止めた。**gate は正しく働いており、緩めていない。**
原因は送り手側にあり (izanagi 自身が書いた設計説明が知識源に混ざっていた)、知識 source を
測定記録だけに絞って通した。

## 実測 1 — fixture 経路 (job `988516.nqsv`)

固定 SHA の専用 checkout (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2182-k2-eval-run/submit-tree`、
main HEAD `7f17e1c63`、CCBench は `p3_s4_loop.PIN` 028f34d、superproject tracked clean) から、
README §7 の tagged qsub command で fixture 経路を 1 本投入した。third-party は同 checkout へ
`fetch_third_party.py hydrate` で offline 供給した。

| 項目 | 値 |
|---|---|
| Created / Started / Ended | 22:51:21 / 22:59:16 / 23:00:07 (JST、2026-09-09)、Elapse 55S |
| `driver_rc` | **0** (2026-09-08 の job `983020.nqsv` は 1) |
| campaign | `p3-s4-loop-s4-autonomous-1145eb11`、variant `8a84a7b00103`、`env_tag=pegasus` |
| 段 4 loop の判定 | 5 件すべて PASS、停止判定 `stop=False reason=continue` |
| 結果 | `0 committed / 1 aborted / 0 skipped (of 1)` |

WAL は 3 レコードを記録した。

- `build_start` — `src_token=4a826c66bc5d883c7b3875adb429beec1c8260b92f3ad7a19544ff5af020ff71`、
  build_admission は `class=coder-authored` / `authority_kind=cli-opt-in`、source evidence に
  `ccbench_commit=028f34d`、`genome_sha256=05ac9ab3…`、`source_bytes_sha256=04d21706…`、
  `tracked_paths=["cmake/Options.cmake","include/backoff.hh"]`。
- `build_done` — trace 実行体 `cf94503330a15b40`、perf 実行体 `3f1db7e3a3cd5f39` (どちらも
  `cached=false`)。**perf の configure argv に `-DFETCHCONTENT_BASE_DIR=` と
  `-DFETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST}=` が入っている** — 前 wave
  (`9a32ef5ca`) が足した offline 配線が実際に効いた直接の証拠である。
- `abort` — `reason=trace-parse-error`、
  `ParseError: trace_0.log:1: trace v1 C record is not supported; expected 7 fields including read/write counts`。

**停止点は前進した。** 2026-09-02 の 6 回目 (3 依存すべて offline) と 2026-09-08 の job 983020 は
どちらも condition gate の supply arm (`preprocess-failed`) で止まっていた。本走ではその関門を越え、
gate も build も通り、**correctness 検証の入口で初めて止まった**。

### evidence の所在

`evidence/attempt-0001/` (fixture)、`evidence/attempt-0002/` (K2、consumer 停止)、
`evidence/attempt-0003/` (K2、build 到達) に `compute-result.json` / `reservation.json` と、
build へ到達した 2 本については `masstree-prebuild-receipt.json` を置いた。

**campaign WAL・受領証・`job.stdout` / `job.stderr` は repo へ複製していない** — WAL と
exploration campaigns は `guard_bash` の防護対象で、`cp` も `cat` のリダイレクトも機械的に
拒否される (本 wave で実測)。原文は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2182-k2-eval-run/` の下に残る:

- 実測 1 の WAL: `submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-1145eb11/runs/wal.jsonl`
- 実測 2 の受領証: 同 `…-50963aec/knowledge_manifest_receipt.json`
- 実測 3 の WAL: 同 `…-1bebed32/runs/wal.jsonl` (`knowledge_provenance` を含む)
- job 出力: `evidence/attempt-000{1,2,3}/job.stdout`、同 `job.stderr`

## 実測 2 — K2 経路 (job `988634.nqsv`)

同じ専用 checkout から、README §7 の K2 正例の形で 5 環境変数
(`IZANAGI_S4_PROPOSAL_PATH` / `IZANAGI_S4_KNOWLEDGE_MANIFEST` / `IZANAGI_S4_CODER_ROLE` /
`IZANAGI_S4_KNOWLEDGE_CLASSIFICATION` / `IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM`) を通して 1 本投入した。

| 項目 | 値 |
|---|---|
| Created / Started / Ended | 23:12:07 (09-09) / 00:16:26 / 00:16:53 (09-10)、Elapse 32S |
| queue 待ち | 約 64 分 (gen_S が全 job QUE の混雑) |
| `driver_rc` | 1 |
| 到達 | prologue → 事前構築 → `_assert_single_tenant()` → `assert_pinned_clean` → **manifest 解決 → 受領証 → campaign identity** |
| 停止 | `load_proposal_file` → `_consume_k2_coder_output` (`p3_s4_loop.py:2156`) |
| 停止理由 | `ValueError: coder-v4-autonomous-k2 が instruction-like content を申告した` |

**K2 の知識入力は job 内の production 経路で消費された。**

- 受領証 `campaigns/p3-s4-loop-s4-autonomous-50963aec/knowledge_manifest_receipt.json` が
  計算ノードで生成された。`knowledge_manifest_sha256 = 6d8674228…` は 09-02 の run card と同一で、
  source 2 件が `git-blob-at-commit-path` で `verified`、`claim_boundary` は
  `classification=reproduction_or_selection` / `de_novo_claim=false`。
  **09-02 の受領証は login node で作ったものだった。今回は production job 内で作られている。**
- campaign identity は `50963aec` で、同じ workload・同じ fixture 値の fixture 走行 `1145eb11` と
  異なる。**manifest digest が identity へ焼かれたことの直接の証拠**である。
- **`_assert_single_tenant()` が計算ノードで通った。** 09-02 と 09-08 の insight が
  「計算ノードで未実測」と留保していた項目である。

**止めたのは production の K2 consumer である。** `_consume_k2_coder_output` は role 出力の
`data_boundary_report.instruction_like_content_detected` が `True` なら無条件に `ValueError` を投げる。
coder-v4-autonomous-k2 は knowledge source の campaign.lock にある `spec_content`
(「coder が勝ち筋値を見ずに backoff 値を合成」等 3 種) を、**外部データ側から自分の参照範囲を狭める
働きかけ = 信頼境界の逆転**として退けたうえで、その事実を申告していた。

**これは gate の誤作動ではない。規律 6 の機構が設計どおり発火した実測である。**
原因は送り手側にある — `campaign.lock` の `spec_content` は izanagi 自身が書いた設計説明だが、
K2 の知識源として role へ渡ると「指示に見える成果物を未信頼入力側へ置いた」ことになる。
gate は緩めず、**知識 source の側を測定記録だけに絞って改めて通す** (実測 3)。

## 実測 3 — K2 経路、送り手側を是正した後 (job `988687.nqsv`)

**gate は 1 行も触れていない。** 知識 source を、coder 自身が「測定記録の JSON 行のみ」と報告した
`runs/wal.jsonl` 1 件へ絞った manifest (digest
`396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e`) を作り、planner と coder を
正規に取り直して投入した。

| 項目 | 値 |
|---|---|
| Created / Started / Ended | 00:24:09 / 00:24:17 / 00:25:07 (JST、2026-09-10)、Elapse 54S (queue 待ち 8 秒 — 混雑が解けていた) |
| `driver_rc` | **0** |
| campaign | `p3-s4-loop-s4-autonomous-1bebed32`、variant `8a84a7b00103`、`env_tag=pegasus` |
| 経路 | 段 4b iteration (`--run-iteration` の proposal 駆動) |
| 結果 | `ran=True outcome=aborted variant=8a84a7b00103 iteration=1`、停止判定 `continue` |

**K2 の proposal から build が作られ、WAL に知識 provenance が束縛された。**

`build_start` の payload は候補と知識を同一レコードで束縛している。

- 候補側: `genome=silo|BACKOFF_FIXED=20,…`、
  `src_token=4a826c66bc5d883c7b3875adb429beec1c8260b92f3ad7a19544ff5af020ff71`、
  `build_admission.class=coder-authored`、`source.ccbench_commit=028f34d`、
  `tracked_paths=["cmake/Options.cmake","include/backoff.hh"]`。
- 知識側: **`knowledge_provenance = {knowledge_level: "K2",
  knowledge_manifest_sha256: "396cd559…", sources: [{repo_artifact, commit 2fa13a26…,
  path output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl,
  sha256 2163b794…}]}`**。

`build_done` は trace 実行体 `8bf01d1ba2f883ac` / perf 実行体 `9ab9565b07d39448` を記録し
(どちらも `cached=false`)、configure argv には offline の 4 つの `-DFETCHCONTENT_*` が入っている。
`abort` は実測 1 と同じ `trace-parse-error` である。

**variant は実測 1 (fixture) と同一の `8a84a7b00103`、`src_token` も同一である。**
coder が合成した値 20 が fixture の既定値と一致したためで、K2 が fixture と違う候補を作ったことには
ならない。ただし campaign identity は `1bebed32` で fixture の `1145eb11` とも、source 2 件版の
`50963aec` とも異なる — **知識 manifest の digest が identity に効いていることの 3 点目の確認**である。
build path も campaign ごとに分かれるため、同じ `src_token` でも trace 実行体の hash は
`cf94503330a15b40` (実測 1) と `8bf01d1ba2f883ac` (実測 3) で異なる。

## 完了条件の達成状況 (09-02 の 4 条件に対して)

| # | 条件 | 09-02 | 本 wave | 根拠 |
|---|---|---|---|---|
| 1 | 知識 manifest の受領証 | 達成 (login) | **達成 (計算ノードの production job 内)** | `campaigns/…-50963aec/knowledge_manifest_receipt.json`、source が `git-blob-at-commit-path` で `verified` |
| 2 | 候補との provenance 束縛 | 未達成 | **達成** | WAL `build_start` の `knowledge_provenance` が候補 (`src_token`) と manifest digest・source の commit/path/sha256 を同一レコードで束縛 |
| 3 | stock と異なる identity | 未達成 | **達成** | `src_token=4a826c66…` が確定。ただし fixture 走行と同一 variant である |
| 4 | 既存 gate の terminal verdict | 未達成 | **未達成** | `trace-parse-error` で correctness 検証へ入れない (PIN と verifier の版不一致) |

**09-02 の 1/4 から 3/4 へ進んだ。残る 1 件は環境でも配線でもなく、凍結 pin と検証側の版の問題である。**

## 停止点の原因 (現物で裏取り)

| 対象 | 現物 | 値 |
|---|---|---|
| 段 4 loop が literal 保持する pin | `orchestrator/campaign/p3_s4_loop.py:111` | `PIN = "028f34d"` (2026-07-06) |
| 現行 pin の正本 | `orchestrator/campaign/pin.py:28` | `CURRENT_PIN = "511c953"` |
| trace v2 を入れた commit | CCBench `511c9538` | 2026-08-11、[T-816]・FN-2 |
| verifier の受理集合 | `orchestrator/verifier/parse.py:322-326` | C レコードが 5 フィールド (v1) なら `ParseError`、7 フィールド (v2) だけ受理 |
| v1 拒否の正例 | `orchestrator/tests/test_verifier.py:467` | **拒否は登録済みの意図的な設計** |

`028f34d` は `511c9538` の祖先で、間に 2 commit ある。**PIN のビルドは trace v1 しか出さず、
verifier は v2 だけを受理する。** したがって段 4 loop の評価経路は、この pin のままでは
どの候補も correctness verdict を得られない。

`p3_s4_loop.py` のコメントは pin を「段4/D38 時点で凍結した pin (当時の submodule HEAD、現行 pin の
正本は `pin.CURRENT_PIN` だが**歴史的 campaign 凍結のため literal 保持**)」と説明している。
凍結そのものは規律 7 の通り正当だが、その後 verifier の意味論が変わり、**凍結側と検証側が
非互換になっていた**。09-02 も 09-08 も gate の手前で止まっていたため、この食い違いは
一度も露出していなかった。

## 裁定パッケージ (ユーザー裁定・本 wave では実装しない)

| 案 | 内容 | 評価 |
|---|---|---|
| A | `p3_s4_loop.PIN` を `pin.CURRENT_PIN` (511c953) へ上げる | 凍結条件の変更。D38 の再裁定が要る。`ccbench_commit` は campaign identity に入るので、過去 campaign との識別子の連続性は切れる |
| B | verifier を v1 対応にする | **採らない**。read/write 件数という検証情報を落とす方向であり、絶対規律 2 (正しさゲートを緩める変異を許さない) に反する |
| C | 現状維持 | 段 4 loop は terminal verdict を永久に得られない |

親の見立ては A だが、**凍結条件の変更はユーザー裁定の対象**なので実装せず返す。

## K2 materials を production の入口で作った範囲と、作れなかった範囲

**作れた**: 知識 manifest の解決と権威射影。`knowledge_manifest.load_and_resolve_manifest` と
`planner_projection` は site 契約に依存しないので login node で呼べる。得られた digest は
**`6d8674228d05e591a67047c4a098e077f427cb7dd6fdfa3b82d20da2000db406` で 09-02 の run card と一致**し、
知識 source 2 件 (campaign.lock 401 bytes / runs/wal.jsonl 6687 bytes) が解決された。

**作れなかった**: driver の `--emit-planner-context` は login node で
`ExecutionGuardError: 計測用 env bytes は site='PEGASUS_LOGIN' では生成できない` に落ちる。
`_admit_env_contract` は [T-2231] (`91c2b6a69`) が入れたもので、`main()` は
`--emit-planner-context` 経路でも無条件に呼ぶ。site は hostname `bnode[0-9]+` だけで決まり、
env による上書き経路は無い (`site_policy.classify_site` が「env は分類条件にしない」と明記)。

この締め付けは理にかなっている — `_campaign_cfg_for_site` は site の env tag を campaign identity へ
焼くので、login で導出した identity は計算ノードのものと一致しない ([T-2231] の段 2 plan が
「これを外すと compute の planner context と実 iteration が別 campaign_id になる」と述べている)。

**したがって本 wave が login で作ったのは role への入力射影だけである。** campaign identity と
知識受領証は job 内の driver が production 経路で作る。**「計算ノードで planner context を出力する」
経路は現在も存在しない** — `p3_s4_loop_pegasus.sh` は driver を `--run-iteration` / `--value` でしか
起動しない。必要になれば既存 job body の拡張で足りる (新規 Pegasus 実行体を作らなければ F660 に
掛からない。`tools/pegasus/admission_registry.json` は path 単位の class 登録で bytes を pin しない)。

## role の応答 (逐語は `verbatim/`)

- **planner-v4**: `direction=decrease` / `magnitude=medium`。09-02 と同じ方向である。
- **coder-v4-autonomous-k2**: `value=20`、`double now_backoff = 20;`、
  `classification=known_result_conditioned_derivative`、`confidence=medium`。
- **coder の初回出力は `proposal.confidence` を欠いており K2 schema の 5 key を満たさなかった。**
  親は値を代筆せず role 本人へ差し戻し、本人が `medium` を付けて返した。自己申告フィールドを
  親が埋めれば、それは role の申告ではなくなる。
- **規律 6 の報告で 2 つの role の判断が分かれた。** coder は
  `data_boundary_report.instruction_like_content_detected = true` を返し、knowledge source の
  campaign.lock にある「coder が勝ち筋値を見ずに backoff 値を合成」等 3 種の記述を、
  **外部データ側から自分の参照範囲を狭めるよう働きかける形 = 信頼境界の逆転**として退けたと
  報告した。planner は同じ source を「過去 campaign の設定記録であって指示ではない」として
  異常扱いしなかった。**09-02 の両 role はどちらも「指示めいた文字列は無い」と報告している。**
  同じ bytes に対する規律 6 の判断が走行ごとに揺れることの実例である。
- 親は login で production の検査を 2 つ通してから投入した:
  `backoff_hole_grammar.validate_backoff_preflight` が `double now_backoff = 20;` を受理すること、
  `assert_closed_proposal_schema(..., coder_contract=CODER_CONTRACT_K2)` が proposal を受理すること。
- driver は proposal の `classification` を読み捨てる (`p3_s4_loop.py:2152-2154` の `del`)。
  呼び手宣言 (`--knowledge-classification`) との照合はしないので、role の自己申告
  (`known_result_conditioned_derivative`) と呼び手宣言 (`reproduction_or_selection`) のずれは
  拒否要因にならない。**受領証に残るのは呼び手宣言だけである。**

## 主張しないこと

- **K2 の知識が候補の性能に効いたとは主張しない。** 本 wave は 1 本も terminal verdict を得ておらず、
  throughput は 1 度も測っていない。
- **role が知識を使ったことの因果は主張しない。** `knowledge_use` は role 自身の申告である。
- **K2 が fixture と違う候補を作ったとは主張しない。** 実測 3 の variant と `src_token` は実測 1 と
  同一である。coder が合成した 20 が fixture の既定値と一致した。
- **fixture 経路の結果を K2 の結果として読まない。** 実測 1 は `--value` の fixture 経路であり、
  K2 の manifest も proposal も通していない。
- **PIN を上げれば通ると実測したわけではない。** 版の前後関係と verifier の受理集合から
  「v1 は必ず拒否される」ことが言えるだけである。
- **実測 3 の知識は実測 2 の知識と同じではない。** source を 1 件へ絞ったため、coder が実測 2 で
  「探索条件が本 iteration と同一だと判断する根拠」に使った campaign.lock は入力から外れている。
  実測 3 の planner は不確かさとして「条件が本 workload と一致する保証を入力から確認できない」と
  自ら報告している。**知識源を絞ることには代償がある。**
- **規律 6 の判断が安定しているとは主張しない。** 同じ campaign.lock に対し、09-02 の 2 role は
  どちらも「指示めいた文字列なし」、本 wave の coder は「あり」と判断した。走行ごとに揺れる。

## 次の wave への出発点

1. **PIN と verifier の版の裁定** (上の A/B/C)。これが決まらないと段 4 loop は terminal verdict を
   得られず、完了条件 4 は永久に未達のままである。**本 wave で最優先の持ち越しである。**
2. **知識源に設計説明を混ぜない送り手側の規律。** `campaign.lock` の `spec_content` のような
   自由文フィールドを K2 の知識源に含めると、role が正しく警戒して走行が止まる。
   knowledge manifest を作る側が「測定記録だけを指す」規律を持つか、`spec_content` を
   指示に読めない書き方にするかの選択がある。**gate 側で解決してはならない。**
3. **計算ノードで planner context を出力する経路。** 現状 `p3_s4_loop_pegasus.sh` には無い。
   本 wave は harness 関数を login で直接呼んで代替したが、[T-2231] の設計意図
   (compute の planner context と実 iteration の campaign_id を揃える) は満たしていない。
   必要になれば既存 job body の拡張で足りる (新規 Pegasus 実行体を作らなければ F660 に掛からない)。
