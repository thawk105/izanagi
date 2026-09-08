# [T-2437] 段 4 裁定 — plan v2 と変異事前登録

親が段 2 プランと段 3 の 2 レンズを裁定した結果。**この文書が段 5 以降の正本である。**
段 2 プランのうち本文書と食い違う箇所は本文書が勝つ。

裁定 inbox 再走査 (DW-S04): main は 2143a49c0 → b57e35426 へ進んだ。新規 D1836 / D1837 は
本 wave の主題と無関係で、編集面 5 file に差分なし。取り込みは段 6 の受入前に post-claim merge で行う。

---

## 1. scope の縮小 (最重要の裁定)

段 1 brief の完了判定「formal consumer が FC04/FC07/FC09 で受理し `P6Unavailable` に到達する」は
**取り下げる。** 両レンズが独立に到達不能を示し、親が現物で裏取りした。

| 到達不能の理由 | 根拠 (親が検算済み) |
|---|---|
| consumer は exact 33 record を要求するが、1 campaign run は 1 件しか作らない | `reflux_formal_consumer.py` の pair 検査、`test_reflux_formal_consumer.py:249-316` の helper が 33 root を明示生成 |
| ledger の evidence digest は seal 時に確定するが、fresh record は `secrets.token_hex(16)` の attempt ID、`os.urandom(32)` の nonce、`time.time()` の ts を含む | `pipeline.py:1694`、`wal.py` の frame writer、`reflux_formal_consumer.py:658-682` の exact digest 一致 |
| completeness が origin の物理 search config key を許さず、rejected build は `built_and_benched >= 1` を満たさない | `autonomous_trial_completeness.py:830-844, 4130-4136` (レンズ B が file:line 提示) |
| Layer3 renderer は WAL と whiteboard しか一次参照にしない | `layer3_report.py:234-266` |

**新しい完了判定 (これが本 wave の研究前進):**
> origin 発行 context を与えた `run_campaign()` を 1 本流すと、**実 verifier** が出した rejected の
> typed 結果と**実 terminal WAL** から、**実 `derive_physical_result` → `assemble_result_evidence_record`
> → `issue_result_evidence_record`** が result-evidence record を create-only で発行し、
> **実 `resolve_result_evidence()`** が発行済み record・projection・source を同じ bytes へ解決できる。
> context を与えない既定経路では 1 file も置かず、受理集合も変えない。

**名乗りの上限 (insight と worklog に必ずこの形で書く):**
> production package 内の issuer 配線と、fixture-origin scope での単一 member 発火可能性まで。
> 「8c origin 結線」「本番 projection が端から端まで通る」「producer が自由に生成した record を
> ledger 束縛 consumer が受理した」とは書かない。

## 2. 各配線の採否

| # | 裁定 | 理由 |
|---|---|---|
| S1 `EvalResult` の typed `VerifyResult` 保持 | **採用** | 実装する |
| S2 ordered WAL projection / execution provenance producer | **採用** | 実装する |
| S3 `run_campaign()` の issue 呼び出し | **採用** | 実装する |
| S4 `run_origin_trial` の production 呼び手 | **本 wave では実装せず、裁定パッケージでユーザーへ返す** | 下記 |

### S4 を実装しない理由 (DW-G04)

DW-G04 は「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ
実装する。書けなければ設計メモに留める」と定める。段 3 が実測で示したのは、公開呼び手を置いても
**issuer へ到達する経路が 1 本も無い**ことである。

- `p3_autonomous_workload_trial.py:5406-5411` — 現 `main()` は fixture provider の real build を拒否する。
- `p3_s4_loop_trigger_gating.py:788-794` — `--no-build` は `run_campaign()` の手前で戻る。
- `trial_registry.py:782` — registered manifest は exact `generations == 2` を要求する。
- 上記 1 節の completeness / ledger 循環。

**発火しない呼び手を置くことは「実装したふり」であり、規律 3 に反する。**
DW-S04 に従い、親は不採用にせず新事実を添えてユーザー再裁定へ返す (下記 §6)。

## 3. 不変条件の訂正 (レンズ B 所見 1 — 親が検算済み blocker)

段 1 brief の不変条件 2「既定経路の bytes を 1 bit も変えない」は **達成不能なので書き換える。**

実測: `campaign_lock.py:48-59` の `CONTRACT_LOADER_RELATIVE_PATHS` (exact 63 path の enforcement
source closure) に **`orchestrator/campaign/loop.py` と `orchestrator/campaign/pipeline.py` が含まれる。**
この 2 file を編集すると campaign lock の digest が変わり、そこから派生する commit receipt と
Layer3 report digest も変わる。これは source closure の設計どおりの帰結であり、本 wave 固有の欠陥ではない。

**訂正後の不変条件 2:**
> 既定 (originless) 経路の**受理集合と意味**を変えない。context 未指定の campaign へ file を 1 つも
> 置かず、WAL の frame 集合・stage・payload key を増やさない。検査は literal SHA golden ではなく
> **非揮発 field 集合の比較**で行う (設計 §12 要件 5)。lock digest の変化は source closure の
> 設計どおりの帰結として insight に明記し、「bytes 不変」とは書かない。

**運用上の帰結 (段 5・6 で必ず効く):** `loop.py` / `pipeline.py` / `ident.py` / `wal.py` は
contract loader 束縛のため、**未 commit のままだと焦点走が contract-loader-drift で全赤になる。**
実装子の赤をこの型と取り違えない。親は焦点走の前にこれらを commit する。

## 4. 所見の裁定 (real / refuted、採否、scope)

### レンズ A

| 所見 | 判定 | 採否 | 成果物影響 (DW-G05) |
|---|---|---|---|
| public fixture E2E が `P6Unavailable` へ到達不能 (blocker) | **real** | scope 縮小で採用 (§1) | 放置すると、到達しない主張を insight に書き成果物の名乗りが偽になる |
| identity-error / 既存 terminal skip が issuer を迂回 (must-fix) | **real** | **採用** | 放置すると terminal のある attempt が record 無しで通り、台帳の member が欠ける |
| issue 失敗が公開 wrapper の例外処理を壊す (must-fix) | **real** | **採用 (S3 の範囲で)** | 放置すると `AttributeError` で report が中途半端になり試行の判定が欠測になる |
| `site=OTHER` で execution receipt 条件が恒偽 (must-fix) | **real** | **採用** | 放置すると発行条件が常に偽で、機構が恒偽の飾りになる (規律 3) |
| source は live WAL でなく immutable prefix snapshot (nit) | **real** | **採用** | 放置すると後続 append で source ref の digest が壊れ解決不能になる |
| 親 brief の誤り 1〜6 | **すべて real** | **採用** | §1・§3・§5 に反映 |

### レンズ B

| 所見 | 判定 | 採否 | 成果物影響 (DW-G05) |
|---|---|---|---|
| originless の literal bytes 不変が成立しない (blocker) | **real** (親が検算) | **採用** (§3) | 放置すると証明できない不変条件を受入基準にして wave が止まる |
| `EvalResult` consumer 棚卸し不足 (must-fix) | **real** | **採用** — 列挙を段 5 へ渡す | 放置すると所有外 caller の回帰を見落とす |
| completeness の search-config gate と rejected population gate (blocker) | **real** | **scope 外** → 裁定パッケージ (§6) | 本 wave の名乗りを §1 に制限することで閉じる |
| `generations == 1` が registered origin を全拒否 (blocker) | **real** (親が検算: `trial_registry.py:782`) | **plan から削除** | 放置すると正例が preflight で落ち、issuer に一度も到達しない |
| completeness と renderer 抜きで「結線した」と名乗れない (blocker) | **real** | **採用** (§1 の名乗り上限) | 放置すると材料レポートが record を参照しないまま「結線」を主張する |
| B1 content-addressed path は受理集合を変えない (nit) | **real** | **採用** — 新 prefix でよい | — |
| B2 生成順に反例なし (nit) | **real** | 採用 | — |
| B3 fresh record と pre-sealed ledger の循環は実在 (blocker) | **real** | **採用** (§1 の名乗り上限) | 放置すると「自由生成 record が受理された」という偽の主張になる |
| E2E 正例が前 wave より弱い (must-fix) | **real** | **採用** (§5 の正例定義) | 放置すると前 wave の証明を薄めた test を新規性として記録する |
| 所有 path 素集合、fragment は親所有 (nit) | **real** | 採用 | — |
| 変異事前登録が実装前予測の形でない (must-fix) | **real** | **採用** (§7 で親が表を確定) | 放置すると KILLED が狙った gate の実効性を示さない |
| 単位 D に本題外 surface (must-fix) | **real** | **採用** — 単位 D は §2 で削除 | — |

### refuted / 反例なしと確認したもの (段 6 で再燃させない)

- accepted で `verify_result=None` にすることは正しさの穴ではない (レンズ A、A2)。全 pass 成功は
  capability と receipt を全件束ねた COMMIT で成立する。任意 1 件の typed 値を残す方が誤縮約。
- production 形の rejected abort は死んでいない。`pipeline.py:649-665` の diagnostic と
  `derive_physical_result` の rejected 条件は同じ `result_to_dict()` 由来で bytes 一致しうる。
- remote fan-out から typed 値を再構成する計画は無い。
- 複数 repetition / pass の選択順は一意 (最初の abort を即 return)。
- 実装単位の所有 path は素集合。
- 新 content path prefix は凍結 gate・path pin・住所 lint に触れない (fixed-string 検索 0 件)。

### 親が独自に確定した pin 閉包の分類 (F39)

`p3_s4_loop_trigger_gating.py` の sha256 `1c6a55d4...be7fd1` と `wal.py` の sha256 は
`output/insights/2026-08-27_t1769-b4-wiring-probe/t2341-eligibility/{base,sort,trigger}.json` に exact 出現する。
**分類 = 歴史記録。** `docs/phase3-b4-reflux-ablation-preregistration.md:320-327` の合格述語は
JSON と sidecar の実在・sidecar 一致・argv 一致・`repository_head` 祖先性・`result.passed` だけを
要求し、**現行 source の hash 一致を要求しない。** `driver_sha256` を現行 source と照合する live
consumer は `s8b_oracle_n_pilot.py:592` だけで、対象 driver が別である。
よって編集は凍結を破らない (規律 7)。この分類を insight に残す。
なお本 wave は §2 の裁定により `p3_s4_loop_trigger_gating.py` を編集しない。

## 5. plan v2 — 段 5 の実装単位

### 単位 A — `pipeline.py` の typed 保持

所有: `orchestrator/campaign/pipeline.py`、新規 `orchestrator/tests/test_pipeline_verify_result_retention.py`

- `EvalResult` へ `build_attempt_id: str = ""` と `verify_result: Optional[VerifyResult] = None` を末尾追加。
- `_RepetitionExecutionOutcome` へ `verify_result: Optional[VerifyResult] = None` を追加し、
  local verifier の戻り値を載せる。
- `_abort` へ keyword-only `verify_result` を足し、非 `None` は `type(x) is VerifyResult` を要求。
- `_project_repetition_outcome` は abort のときだけ `verify_result` を渡す。accepted は `None` のまま。
- `_admit_verify_fanout_result` の全 return は `verify_result=None`。wire payload から復元しない。
- pre-build abort と通常経路の `EvalResult` に `build_attempt_id` を設定する。
- **段 3 の指摘により削る:** repetition ごとの二重 reset は入れない。`res.verify_result` の初期化は
  `_project_repetition_outcome` の入口 1 箇所だけにする (2 箇所は相互 mask する)。

### 単位 B — `reflux_result_evidence.py` の producer

所有: `orchestrator/campaign/reflux_result_evidence.py`、`orchestrator/tests/test_reflux_result_evidence.py`

- 新 module を作らない (15-file 閉集合 `test_reflux_formal_consumer.py:32-48` を破らないため)。
- `wal.ordered_attempt_frames()` (`wal.py:1671`) を**再利用する。再実装しない。**
- 追加する公開面: `ResultEvidenceIssuanceContext`、`produce_ordered_wal_projection`、
  `issue_campaign_result_evidence`。
- source blob は **terminal 時点の `wal.jsonl[0:byte_end]` の immutable prefix snapshot**。
  live WAL を直接指さない (後続 append で whole-file digest が壊れる)。
  成果物名・code comment・insight で「terminal 時点の source-WAL prefix snapshot」と名乗る。
- 3 種の content path は content-addressed:
  `<physical>/reports/reflux-result-evidence-content/v1/{source-wal,ordered-wal,execution-provenance}/<sha256>.{jsonl,json,json}`
- 書込みは `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW` + 全 bytes write + file fsync + parent fsync +
  read-back exact 一致。`FileExistsError` は成功にしない。`os.replace()` を使わない。
- 発行順: derive と assemble を**先に memory 上で通し**、その後 source → projection → provenance → record。
- **execution receipt (レンズ A の恒偽指摘への裁定):** `attestation_mode == "none"` の site では
  execution receipt が存在しない (`loop.py:180-193`、`env_contract.py:299`)。
  **自己申告 digest で埋めてはならない (規律 3)。receipt が無ければ `ResultEvidenceIssuanceRefused` で
  発行を拒否する。** この限界を insight に「発行は attestation ありの site に限る」と明記する。

### 単位 C — `loop.py` の issuer 呼び出し

所有: `orchestrator/campaign/loop.py`、新規 `orchestrator/tests/test_reflux_campaign_issuer.py`

- `run_campaign` へ keyword-only `result_evidence_context: Optional[...] = None` を追加。既存 caller は無変更。
- context 非 `None` のとき最初の durable write 前に、exact 型・`len(genomes) == 1`・
  `balanced_schedule is None`・evidence root の実在と包含を要求する。
- **発火点は per-result** (`s.results.append(r)` の直前)。campaign 末尾ではない (複数 genome で一意でない)。
- **段 3 の must-fix を閉じる:** identity-error 経路 (`loop.py:522-539`) と既存 terminal の skip 経路
  (`loop.py:544-550`)、eval-exception 経路 (`loop.py:631-654`) も **issue の判断を通す。**
  terminal はあるが typed 結果が無い / attempt が一意でない場合は
  `ResultEvidenceIssuanceRefused` で**明示的に拒否**し、黙って素通りさせない。
- issue 例外を `eval-exception` abort へ変換しない。既に terminal のある attempt へ二重 abort を書かない。
- **段 3 の must-fix を閉じる:** 例外を上位へ投げる前に、`_complete_origin_runtime()` が
  zero issued path で二次例外にならないことを確認する。単位 C の範囲で閉じられないなら
  「issue 失敗時は campaign を失敗させるが、上位 wrapper の挙動は本 wave の scope 外」と
  test の docstring に明記し、insight へ限界として書く。

### 段 5 で編集しない (裁定)

`p3_autonomous_workload_trial.py`、`p3_s4_loop_trigger_gating.py`、`reflux_origin_fixture_builder.py`、
`test_p3_autonomous_workload_trial.py`、`test_reflux_formal_consumer.py`。単位 D は §2 で削除した。

### 正例 (実体を名指しする — F649)

**単位 C の正例が本 wave の中心である。**
- 実 `run_campaign()` を 1 genome・origin context 付きで駆動する。
- verifier は**実 `verify_trace_dir`** を synthetic Silo source 束縛下で走らせる
  (前 wave の insight §5 と同じ形)。`r9_dense_cycle4` を使う。
- trace の生成だけ `trace_runner` seam でその fixture trace dir を返す。
  **これが唯一の stub であり、insight に明記する。** verifier・deriver・assembler・issuer・WAL・
  resolver はすべて実 callee。
- 発行された record を実 `resolve_result_evidence()` で解決し、source interval bytes 一致まで検査する。
- 前 wave の `test_synthetic_silo_source_producer_passes_formal_consumer_contract` は**編集しない。**
  本 wave の正例はそれを置き換えず、別の命題 (issuer hook の発火) を証明する。

### 負例

- context 未指定の同一駆動で、campaign root の file 集合が変更前と一致し、WAL の stage 集合と
  payload key 集合が一致する (literal digest ではなく非揮発 field 比較)。
- execution receipt 不在 → 発行拒否。
- remote fan-out 由来の rejected (typed 値なし) → 発行拒否。
- 複数 genome / balanced → context 提示時に拒否。
- attempt frame が非連続 → 発行前に拒否し、file を 1 件も作らない。
- 既存 path への衝突 (`FileExistsError`) → 発行失敗。

## 6. 裁定パッケージ (ユーザーへ返す — 本 wave では実装しない)

1. **S4 `run_origin_trial` の production 呼び手。** 依頼文の 4 項目のうち 1 件。実測で、公開呼び手を
   置いても issuer へ到達する経路が無い (本文書 §2)。到達させるには (a) `main()` の fixture provider
   real build 拒否の解除、(b) `--no-build` 経路の変更、(c) `generations == 2` 制約との整合、
   (d) completeness の origin 分岐、の 4 件が要る。いずれも本 wave の scope 外。
   **本 wave は S1〜S3 を完了させ、S4 だけを返す。**
2. **completeness の origin 分岐。** 物理 search config の `origin_campaign_run` key、
   rejected build の `built_and_benched >= 1` population gate。origin trial の report が完了しない。
3. **材料レポート renderer が ledger と result-evidence を一次参照しない。**
   これを閉じない限り「8c 結線」とは名乗れない (設計 §12 の明文)。
4. **terminal 後の issuer 失敗を ledger tombstone へ接続するか。** 現状は terminal WAL と部分 content
   artifact が残り record が無く、consumer は FC01。自動 tombstone 経路は無い。
5. **`attestation_mode=none` の site での execution receipt 契約。** 本 wave は発行拒否に倒したが、
   Pegasus 以外で発行したいなら認証済み receipt の定義が要る。自己申告 digest は規律 3 に反する。

## 7. 変異事前登録 (DW-M01 — 実装前に確定)

段 3 が指摘した mask・等価・過剰決定を避けた形で登録する。
**期待 node 集合は段 5 の実装後・段 6 の変異走行前に、実 nodeid で確定して台帳へ書く。**
本節は「無効化する述語」と「期待外 node 0」を先に固定する。

| ID | 位置 | 無効化する述語 | 期待する赤の型 | mask 回避の根拠 |
|---|---|---|---|---|
| M1 | 単位 A `_project_repetition_outcome` | abort のとき `verify_result` を渡す | rejected 発行が typed 値なしで拒否される正例が緑になる | 他層に typed 保持は無い |
| M2 | 単位 A `_abort` の `type(x) is VerifyResult` | typed 値の exact 型検査 | wire dict を渡す負例が通る | 同上 |
| M3 | 単位 A fan-out の `verify_result=None` を wire から復元する形へ | fan-out 拒否 | fan-out rejected の発行拒否負例 | 復元経路は他に無い |
| M4 | 単位 B source snapshot を live WAL 参照へ | prefix snapshot の immutability | 後続 append 後の解決失敗負例 | resolver は digest しか見ないので producer 側の単独理由 |
| M5 | 単位 B `byte_start` を 0 固定 | 区間の起点 | **2 番目以降の attempt**を正例に使う node | 1 番目だと等価変異になる (段 3 の指摘) |
| M6 | 単位 B write 前検査の除去 (derive/assemble を後段へ移す) | 「発行前に拒否し file を 0 件にする」 | 拒否時に file 集合が 0 件であることを検査する node | resolver が後で落としても file が残る差で帰属する |
| M7 | 単位 B execution receipt 不在時の拒否 | receipt 必須 | receipt 不在の発行拒否負例 | 他層に receipt 検査は無い |
| M8 | 単位 C context 未指定時の分岐 | originless で 1 file も置かない | originless の file 集合一致負例 | 分岐は 1 箇所 |
| M9 | 単位 C identity-error / skip 経路の明示拒否 | 「terminal はあるが typed 無し」の拒否 | 該当経路の拒否負例 | 段 3 が指摘した迂回そのもの |
| M10 | 単位 C `len(genomes) == 1` と balanced 拒否 | 単一 attempt 前提 | 複数 genome / balanced の拒否負例 | 前提検査は 1 箇所 |
| M11 | 単位 C issue 例外の伝播を握り潰す形へ | fail-closed | issue 失敗時に campaign が成功で返らない負例 | 例外経路は 1 箇所 |

**登録しない (段 3 の指摘により単独理由にならない):**
- truncated final frame — `wal.ordered_attempt_frames()` (`wal.py:1688-1694`) が先に拒否する。
- 「全 frame の attempt 一致」— 同 API が該当 attempt だけを選ぶので通常入力では恒真。
- terminal / attempt / projection schema 検査 — 既存 `derive_physical_result` に mask される。
- pre-build / identity-error / eval-exception への attempt ID 追加 — 別の拒否理由で先に落ちる過剰決定。

## 8. 段 5 実装子へ渡す追加の実測 (段 3 が集めたもの)

`EvalResult` を読む production consumer (新 field は末尾既定値なので既存 caller を壊さないが、
回帰面として渡す): `loop.py:660-667`、`p2_2.py:384-391`、`backoff_sweep.py:309-317,420-430`、
`sanity_silo.py:68`、`p3_kickoff.py:171-173`、`p3_s4_red.py:211-223`、`s6_sort_sweep.py:419`、
`s8a_trigger_sweep.py:521`、`p3_s4_loop.py:1709-1715`、`p3_s4_loop_sort.py:419-425`、
`p3_s4_loop_trigger_gating.py:830-858`、`paper_story_a2_certification.py:3237-3239,3430,3625-3630`、
`backoff_repro.py:175-182`、`demo.py:62`、`s1_direct_comparison.py:956-969`、
`screening_driver.py:506-521,638`。
repository-wide の `asdict` / `vars` / `__dict__` / JSON 化検索で `EvalResult` 全体を serialize する
production 経路は**無い** (段 3 レンズ B の静的検査)。
