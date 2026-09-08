# result-evidence の producer を production の実行結果へ配線し、発行の関門を認証済み受領証へ束縛した — 受理側が端から端まで通ることは示さない

**種別:** 配線 (issuer)。dev-wave `dev-wave-t2437-record-issuer` (2026-09-09)。
設計判断は {{D:result-evidence-production-issuer}}。起点は D1809 の「production issuer への配線は
本決定に含めない」と [T-2437]。

**名乗りの上限。** 閉じたのは **production package 内の issuer 配線**と、
**fixture-origin scope での単一 member の発火可能性**までである。
「8c origin を結線した」「本番の projection が端から端まで通る」
「producer が自由に生成した record を ledger 束縛 consumer が受理した」とは書かない。
理由は §2 と §7 に実測で示す。

## 1. 依頼 4 項目のうち 3 項目を実装し、1 項目を裁定へ返した

| # | 依頼の項目 | 結果 |
| --- | --- | --- |
| S1 | `EvalResult` への `VerifyResult` 保持 | 実装した |
| S2 | ordered WAL projection producer | 実装した |
| S3 | `run_campaign()` 最終化点での issue 呼び出し | 実装した (発火点は per-result) |
| S4 | `run_origin_trial` の production 呼び手 | **実装せず裁定へ返した (DW-G04)** |

**S4 を実装しない理由。** 公開呼び手を置いても issuer へ到達する経路が 1 本も無いことを段 3 が実測した。
`p3_autonomous_workload_trial.py:5406-5411` の `main()` は fixture provider の real build を拒否し、
`p3_s4_loop_trigger_gating.py:788-794` の `--no-build` は `run_campaign()` の手前で戻り、
`trial_registry.py:782` は registered manifest に exact `generations == 2` を要求する。
**発火しない呼び手を置くことは「実装したふり」であり規律 3 に反する。**

## 2. 当初の完了判定は到達不能だったので取り下げた

段 1 brief は「formal consumer が FC04/FC07/FC09 で受理し `P6Unavailable` に到達する」を完了判定に
置いた。段 3 の 2 レンズが独立に到達不能を示し、親が現物で裏取りした。

| 到達不能の理由 | 根拠 |
| --- | --- |
| consumer は exact 33 record を要求するが 1 campaign run は 1 件しか作らない | `test_reflux_formal_consumer.py:249-316` の helper が 33 root を明示生成して初めて成立する |
| ledger の evidence digest は seal 時に確定するが、fresh record は `secrets.token_hex(16)` の attempt ID、`os.urandom(32)` の nonce、`time.time()` の ts を含む | `reflux_formal_consumer.py:658-682` が sealed member digest と exact 一致を要求する |
| completeness が origin の物理 search config key を許さず、rejected build は `built_and_benched >= 1` を満たさない | `autonomous_trial_completeness.py:830-844, 4130-4136` |
| Layer3 renderer は WAL と whiteboard しか一次参照にしない | `layer3_report.py:234-266` |

**循環の中身。** 受理側が要求する digest は実行前に確定しているのに、新しく作る record には毎回変わる
値が入る。したがって「先に答えを知っている fixture」でしか通らず、
**「producer が自由に作った record を consumer が受理した」という主張は原理的に立たない。**

**差し替えた完了判定 (本 wave が実際に示したこと):**
> origin 発行 context を与えた `run_campaign()` を 1 本流すと、**実 verifier** が出した rejected の
> typed 結果と**実 terminal WAL** から、**実 `derive_physical_result` →
> `assemble_result_evidence_record` → `issue_result_evidence_record`** が record を create-only で
> 発行し、**実 `resolve_result_evidence()`** が発行済み record・projection・source を
> 同じ bytes へ解決する。context を与えない既定経路では 1 file も置かない。

## 3. 実装した配線

### S1 `pipeline.py` — typed `VerifyResult` の保持

`EvalResult` へ `build_attempt_id` と `verify_result` を末尾追加した。
**typed 値を保持するのは local verifier 由来の rejected repetition だけ**で、accepted と
remote fan-out は必ず `None` にする。`_abort` は `type(x) is VerifyResult` の exact 型だけを受ける。
`_admit_verify_fanout_result` の全 return は `verify_result=None` を明示し、
**自己申告の wire payload から typed 値を再構成する経路を作らない。**

accepted で typed 値を保持しないのは意図した非対称である。D1809 の accepted 条件は
projection terminal の `commit` と `verify_configs` の exact 一致で閉じており、
任意 1 pass の値を残す方が「全 pass 通過」という事実を誤縮約する (段 3 レンズ A)。

### S2 `reflux_result_evidence.py` — projection と provenance の producer

- `wal.ordered_attempt_frames()` (`wal.py:1671`) の実 offset を**再利用する**。physical offset reader を
  再実装しない。**親 brief はこの部品の存在を見落としており、段 2 が指摘した。**
- source は **terminal 時点の `wal.jsonl[0:byte_end]` の immutable prefix snapshot**。
  live WAL を指すと後続 append で whole-file digest が壊れる (段 3 レンズ A が両案を比較して判定)。
  projection の `byte_start`/`byte_end` は元 WAL の実 offset を保つ。
- 新 module は作らない。`test_reflux_formal_consumer.py:32-48` の `WAVE_PRODUCTION_FILES` が
  production source を exact 15 file の閉集合に固定しており、新 module はその外へ出る。
- derive と assemble を**先に memory 上で通し**、通ってからだけ
  source → projection → provenance → record の順で create-only 発行する。
  拒否時は **file を 1 件も作らない。**

### S3 `loop.py` — per-result の issue 呼び出し

発火点は `s.results.append(r)` の直前。**campaign 末尾ではない** — 複数 genome では
「どの評価の証拠か」が一意に決まらない (段 2 が親 brief の誤りとして指摘)。
identity-skip / identity-error / terminal-skip / eval-exception の 4 経路も発行の判断を通し、
terminal はあるが typed 結果が無い場合と attempt が一意でない場合は**明示的に拒否する。**
issuer の例外は abort へ変換せず伝播させ、`CampaignSummary` を返さない。

## 4. 段 6 で見つかった「緑だが守れていない」3 型

本 wave で最も価値があったのはここである。**3 回とも、テストは緑のまま関門が空だった。**

| # | 見つけた者 | 内容 | 直し方 |
| --- | --- | --- | --- |
| P1 | 親の焦点走 | `_issue_campaign_result_evidence(...)` の 4 呼び出し点が引数を無条件評価する。Python は呼び出し前に引数を評価するので helper 冒頭の早期 return では防げず、**既定経路が従来読まなかった属性を読む。**既存 3 node が `AttributeError` で赤 | 4 呼び出し点を guard で囲み、属性アクセスで例外を投げる番人 object の負例を足した |
| P2 | 段 6 レンズ A と B が独立に | issuer が受領証の**真正性を検証していない。**`type(x) is dict` と `contract_sha256` 一致だけを見ており、条件に合う任意の dict が通る。repo には権威ある `execution_guard.receipt_matches_contract()` が既にあったのに参照 0 件 | issuer から権威検証器を呼ぶ。中心正例も合成受領証をやめ、実 required attestation 経路で駆動する |
| R1 | 焦点再レビュー | P2 を直した後も、**検証の分岐を呼び手が自己申告できた。**required 契約から作った v1 receipt に `attestation_mode="none"` の札を付けると `receipt_matches_contract` が `True` を返す (再レビューが述語を実際に評価して確認) | issuer が解決済み契約そのものを受け取り、`env_tag` / `attestation_mode` / digest を**契約から読む** |

**P1 の教訓は一般性がある。**「使わないときは何もしない」を helper 内の早期 return で書くと、
呼び出し側の引数評価は防げない。既定経路の不変を守るには **call site を囲む**必要がある。

## 5. 不変条件のうち、達成不能と判明して書き換えたもの

段 1 brief は「既定 (originless) 経路の bytes を 1 bit も変えない」を不変条件に置いたが、
**達成不能である。** `campaign_lock.py:48-59` の `CONTRACT_LOADER_RELATIVE_PATHS`
(exact 63 path の enforcement source closure) に `loop.py` と `pipeline.py` が含まれ、
編集すると campaign lock の digest と、そこから派生する commit receipt・Layer3 report digest が変わる。
これは source closure の設計どおりの帰結であり、本 wave 固有の欠陥ではない。

**訂正後:** 既定経路の**受理集合と意味**を変えない。context 未指定の campaign へ file を 1 つも置かず、
WAL の frame 集合・stage・payload key を増やさない。検査は literal SHA golden ではなく
**非揮発 field 集合の比較**で行う (設計 §12 要件 5)。

## 6. 変異 matrix — 閉包内の file は変異で帰属できない

probe 走 (全件 SURVIVED 登録で観測 node を集める) → 本走の 2 段。runner は
`tools/run_tests.py --force-dispatch` で 3 test file。spec と台帳は `mutation/`。

| 走 | HEAD | baseline | 結果 |
| --- | --- | --- | --- |
| probe (14 変異) | b0b1d079d | PASSED | 13 MISMATCH / 1 SURVIVED |
| 本走 (6 変異) | b0b1d079d | PASSED | **KILLED 5 / 5、期待 node 完全一致、MISMATCH 0**、登録 SURVIVED 1 |

### probe が明らかにした構造的制約 (本 wave の主要な副産物)

**`loop.py` と `pipeline.py` への変異は帰属できない。**この 2 file は campaign lock の
enforcement source closure に含まれるため、1 文字でも変えると
`contract-loader-drift: disk bytes が HEAD blob と不一致` が**先に発火し、
campaign を構築する全 test が落ちる。**probe で観測した内訳:

| 変異先 | 観測された落ちた node 数 |
| --- | --- |
| `loop.py` / `pipeline.py` (閉包内) の 8 変異 | 8〜10 node (すべて drift 由来) |
| `reflux_result_evidence.py` (閉包外) の 6 変異 | 0〜4 node (狙った負例だけ) |

DW-M01 は「同じ入力を拒否する層が前後にも内側にも無く赤理由が一つに絞れることを確認し、
できなければ登録せず実効 gate へ再照準する」と定める。drift 層がすべてを mask するため、
**閉包内 8 変異は登録しなかった。**期待 node に drift 由来の赤を含めれば形式上は KILLED になるが、
それは**偽の KILLED を台帳へ残す**ことであり、段 6 レンズ B が事前に警告した失敗型そのものである。

この制約は本 wave 固有ではなく、**enforcement source closure に載る全 file に当てはまる。**
S1 と S3 の関門の実効性は、変異ではなく**負例そのもの** (`test_reflux_campaign_issuer.py` と
`test_pipeline_verify_result_retention.py` の拒否 node 群) が担保する。

### 本走で KILLED した 5 件

| 変異 | 無効化した述語 | 落ちた node |
| --- | --- | --- |
| m5 | projection の `byte_start` を 0 固定 | `test_campaign_producer_preserves_nonzero_offset_for_second_attempt` (1) |
| m7 | 受領証の真正性検証 (`receipt_matches_contract` を通さない) | receipt 不在 / required+v1 / schema / env_tag の 4 node |
| m7b | 文脈の env_tag・認証強度が契約と一致することの検査 | `refuses_unauthenticated_receipt_before_writes[attestation_mode]` (1) |
| m7c | required 契約での較正裏取り要求 | `refuses_required_contract_without_verified_calibration` (1) |
| m13 | record の置き場が context の宣言と一致することの検査 | `refuses_wrong_expected_record_path_before_writes` (1) |

### 登録 SURVIVED 1 件は実測に基づく

**m4 (source prefix snapshot の bytes が frames と一致することの検査を外す) は SURVIVED。**
この検査は「frame 読み取りと snapshot 読み取りの間に WAL が書き換わった」競合だけを守る。
現行の test 群はこの競合を誘発できず、誘発するには新しい注入 seam が要る。
**検査自体は恒真ではない** (競合が起きれば発火する) が、**負例で pin されていない。**
初回 probe の結果は erratum として `mutation/mutation-probe-out.json` に残す (DW-M02)。

## 7. 実走した検査

- 焦点走 (DW-O26 の参照関係で 36 file を列挙、計算ノード dispatch):
  - 統合 commit 73fb00075: 3726 passed / 10 skipped / 赤 0
  - fix 後 62913330a: 3742 passed / 10 skipped / 赤 0
  - fix2 後 b0b1d079d: **3749 passed / 10 skipped / 赤 0** (188.61s)
- 中心正例 `test_reflux_campaign_issuer.py` 単独: 7 passed (fix 前)、fix2 後は 15 node
- AI provenance 全史監査: 9057 件、新規違反なし
- 変異本走: KILLED 5 / 5、期待 node 完全一致
- **子はどの段でも `tools/run_tests.py` を通せなかった** (sandbox の `qstat -Q` preflight で rc=16)。
  実走はすべて親が行った。**子の実走は親の全走を代替しない** — P1 の回帰は、
  子の環境で走れなかった 3 node を親が commit 後に走らせて初めて出た。

## 8. 中心正例が通した実 callee と、唯一の stub

```
run_campaign → 実 _authorize_measurement → 実 calibration loader → 実 v2 receipt builder
  → 実 pipeline.evaluate → 実 verify_trace_dir (synthetic Silo source 束縛下、r9_dense_cycle4)
  → 実 WAL → 実 receipt_matches_contract → 実 produce_ordered_wal_projection
  → 実 derive_physical_result → 実 assemble_result_evidence_record
  → 実 create-only issuer → 実 resolve_result_evidence
```

**stub は CCBench 実行ファイルの起動 (`trace_runner` seam) だけである。**
ほかに環境 seam が 2 つある: tmp output root を許す `_has_git_ancestor` と、
物理 attestation probe の観測値を deterministic profile へ差し替えるもの。
後者は receipt の**生成・比較・検証本体を実 callee のまま**残す。

## 9. 残る限界

- 閉じたのは issuer 配線まで。受理側が端から端まで通ることは §2 の循環により本 wave では示せない。
- `run_origin_trial` の production 呼び手 (S4) は未実装。裁定パッケージへ返した。
- completeness の origin 分岐と材料レポート renderer は scope 外のまま。
  設計 §12 は「この 2 層に触れずに『結線した』と名乗ってはならない」と明記しており、本 wave は名乗らない。
- terminal 後に issuer が失敗すると、terminal WAL と部分 content artifact が残り record が無い。
  consumer は FC01 で拒否する (fail-closed) が、**自動で ledger tombstone へ接続する経路は無い。**
- 発行は `attestation_mode` が `required` の site に事実上限定される。
  `none` の site では実 `_authorize_measurement()` が receipt を作らないため発行拒否になる。
- **enforcement source closure に載る file は変異で帰属できない** (§6)。この制約は本 wave の
  S1・S3 だけでなく、同じ closure に載る全 file の将来の wave にも当てはまる。
- 段 3 が指摘した恒真な検査 2 件 (`derive_physical_result` の mixed-attempt 拒否、
  `result_to_dict()` 由来の派生値検査) は、既存 API の意味であって本 wave が足した防護ではない。

## 10. 段 8 — 自己改善は 3 件とも本文編集をせず候補記録に留めた

| 候補 | 実測 | 裁定 |
| --- | --- | --- |
| `tools/run_tests.py` の file 引数は repo 相対 path でないと無言で 0 件収集 rc=5 になる (`_normalize_args` が repo root 基準の存在検査に失敗して絶対 path 化しない) | 親が 1 回踏み、dispatch 1 本を無駄にした | **見送り。**統合先の `DW-O26` は 946/1000 bytes で 1 行は収まるが、**節全体が `tools/check_docs.py` の exact 契約に pin されている。**追記には checker の編集 = 実装面の変更と Codex author 子が要り、2 分の損失に対して不釣り合い |
| `DW-S05-A` の「gate 実測値の NOTE が非 0 なら anchor を読み直す」は、midflight gate が隔離 worktree で必ず「main より N commit 遅れ」を NOTE に出すため常に発火する | 3 回とも発火。親は anchor を読み直して問題なしを確認した | **見送り。**手順としては機能した。親の読解が狭かった可能性を排除できない |
| `EnterWorktree` 失敗 (symlink cwd) からの回復手順が `docs/dev-wave/` に無い | 1 件 | **見送り。**memory に既にあり、そこから回復できた。同じ内容を複数の行き先へ複製しない (自己改善契約) |

**この 3 件から出た一般的な観察。** `docs/dev-wave/` の reference 節は
**byte 予算 (L2 節は 1000 bytes) に加えて節全体の exact pin を持つ。**
1 行の明確化でも「予算に収まるか」だけでは足りず、pin を持つ checker の編集が要る。
事故を伴わない明確化は、この二重の関門に対して割に合わないことが多い。
