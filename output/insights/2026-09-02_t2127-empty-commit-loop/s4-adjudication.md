# [T-2127] 段 4 裁定 — プラン v2、変異事前登録

親が段 2 プラン、段 3 レンズ A / B、親自身の実測を突き合わせて裁定した。
所見はすべて real / refuted と採否を明記する。

## 0. 裁定の要旨

方向 (P1「admission では一律拒否せず、全称保証と存在保証を分ける」) は 3 者一致で維持する。
**ただしプランはそのままでは実装に出せない。** 受理集合を広げる箇所が 1 つ、
恒真な配線が 3 つ、既存テストの取りこぼしが 3 群ある。

配線は **6 箇所 → 2 箇所**へ縮小する。

## 1. 欠陥の言い方を訂正する (A-01 real・採用)

「commit 0 件で loop が空走する」こと自体は欠陥ではない。
「存在する全 commit の証拠が妥当」という**全称命題は 0 件でも真**である。

**欠陥は、その全称保証を「certified commit が存在する」という存在保証として読む
consumer 契約の曖昧さにある。** 起票の表現「証拠なしに certified view が発行される」は
不正確であり、worklog と insight ではこの訂正した言い方を使う。

閉じ方は「全称保証 (view 型) と存在保証 (新 helper) を別の名前に分ける」ことである。

## 2. 成果物影響 — 実際に値が変わる唯一の箇所 (`DW-G05`)

**`layer3_report.build_accepted_report` は、1 件も commit されず 1 件も検証されていない
campaign から `certifying_input: True` の Layer3 report を発行できる。**

同関数が要求するのは acceptance receipt の certifying、trial 一致、
`admission_status=admitted`、decision 不変、epoch E1 だけで、
`layer3_report.py:695-770` のどこも commit の存在を要求しない。

**これは親の推測ではない。既存の passing test が現に固定している** —
`orchestrator/tests/test_layer3_report.py:1825-1845` は
`build_start` 1 件だけ (commit 0 件・verify_done 0 件) の campaign に対して
`report["certifying_input"] is True` と epoch `E1` を assert する。

A-02 は「`build_accepted_report` は production caller の無い future entrypoint だと
コード自身が宣言している」と指摘する。**real として採用する。**
ただし本 wave では実装する。理由は 2 つ。
(a) 直接呼べる producer であり、既存テストが commit 0 件での発行を現に固定している。
(b) `DW-G04` が求める「発火条件を満たす既存 artifact path」を、
    この既存テストの fixture が満たしている。

## 3. must-fix

### MF-1 (A-03 real・採用) — 証拠の母集合を狭めてはならない

`require_persisted_certified_commit` は `artifact_admission.py:676-680` で
`records[:commit_index]` を証拠の母集合とし、`:737-741` で
`receipt_evidence != wal_evidence` の**完全一致**を要求する。

プランは `s1_report` へ success segment だけ、`s8b_oracle_report` へ window だけを渡すと
書く (`s2-plan.md:38,40`)。**母集合を狭めると、receipt に載っていない余分な verify が
`wal_evidence` から消え、いま拒否されている入力が通る。** 受理集合の拡大であり、
brief の不変条件に反する。

**裁定:** 共通 helper は「証拠探索に使う全 records」と「検査対象の commit 選択」を
**別の引数**にする。全 caller は従来どおり campaign 全体の records を証拠母集合として渡す。
狭めてよいのは commit の選択だけである。
S6 / S8A / `backoff_repro` / `p3_s4_loop` の「対象 variant の record 列を渡す」も同じ理由で不可。

### MF-2 (A-13 / B-05 real・採用) — constructor の call site を全部直す

`CertifiedCampaignView` に default なし必須 field を足すと、token を使った直接構築が全部落ちる。
プランは `test_artifact_admission.py` の token test しか挙げていない。

追加で直す:
- `orchestrator/tests/commit_receipt_support.py:185-204`
- `orchestrator/tests/test_t1286_commit_receipt.py:431-438`
- `orchestrator/tests/test_t1286_commit_receipt.py:531-535`

count は固定値で置かず、**その fixture の records から計算した値**を渡す。

### MF-3 (親の実測・採用) — `test_layer3_report.py` の 4 件

親が等価 probe を当てて実測した。baseline 180 passed / 0 failed に対し **4 件が赤**になる。

- `test_accepted_report_requires_e1_and_records_epoch`
- `test_certified_report_omits_current_verifier_conformance`
- `test_render_accepted_persists_certifying_report`
- `test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`

**プランのテスト変更一覧は `test_layer3_report.py` を 1 行も挙げていない。**
4 件は削除せず、fixture へ正当な commit + verify_done + receipt を足して
「commit のある campaign なら certifying report が出る」を保つ。
別途「commit 0 件では出ない」を新 node として足す。

### MF-4 (B-09 real・採用) — 2 命題を独立に壊せるようにする

プランの 2 test は、どちらも production admission から view を作るため、
admission だけを壊す変異で**両方**落ちる。分割が見かけだけになる。

**裁定:** helper 側の test は production admission に依存させず、
private construction で作った zero-count の exact view を使う。
次の 2 変異が別々に効くことを段 6 で示す。
- admission だけを zero-commit reject にする → 第 1 test だけ落ちる
- helper だけを zero-commit accept にする → helper test だけ落ちる

## 4. 配線を 6 箇所 → 2 箇所へ縮小する

`DW-G05`「足りる既存策があるなら足さない」と `DW-M01`「同じ入力を拒否する層が前後に無いこと」で判定した。
親の反実仮想と A-06 / B-02 が独立に一致した。

| 箇所 | 判定 | 理由 |
|---|---|---|
| `backoff_sweep_report.py` | **足さない** | `:77-79` の `if not static: skip` を抜けた時点で commit >= 1 が含意される。helper に到達しない |
| `backoff_overthrottle.py` | **足さない** | `:150-159` `require_complete_bindings` が空集合と非空 expected の不一致で先に raise |
| `backoff_extended_sweep_report.py` | **足さない** | `:509-510` `len(perf_statuses) != 1` が先に raise |
| `autonomous_trial_completeness` certifying chain | **足さない** | A-07 real。producer は常に non-certifying report を作り、chain validator は先行の `certifying_input` 不一致で先に拒否する。`DW-G04` の「発火条件を満たす既存 artifact path」を書けない |
| `replay.load_landscape` | **足す** | view 取得直後で commit 投影より前。先に落ちる層が無い。かつ `search_baselines.py` と `guided.py` という**名前検索に現れない間接 consumer 2 file** をここ 1 本で覆える |
| `layer3_report.build_accepted_report` | **足す** | 節 2 のとおり。commit の存在を要求する層が前後に無い |

外した 4 箇所には代替の回帰 test を**足さない**。既存 gate の回帰 pin は本 wave の主題外であり、
`DW-G05` の「示せない must-fix は nit/backlog」に当たる。

## 5. 件数 field が証明すること・しないこと (A-05 real・採用)

`__post_init__` の「件数 == snapshot 内 commit 件数」は records から導出できる値の二重導出であり、
**独立した証拠検査ではない**。また「caller は件数を渡せない」は誤りで、
`_CERTIFIED_VIEW_TOKEN` は module 属性として参照でき、既存テストが直接構築している
(D1252 も同一 process からの偽造可能性を明記)。

**裁定:** 件数 field は**共通入口の投影であって検証の証拠ではない**。
- 証明する: 誤った件数を発行できない。consumer が件数を信頼してよい。
- 証明しない: その commit が実際に検査を通ったこと。

docstring・worklog・insight にこの区別を明記し、「件数があるから検証済み」と読ませない。
実際の防壁は (a) 走査 loop が共通 helper 1 本であること と (b) 非ゼロを要求する 2 箇所である。
D1252 の token 強化は scope 外のまま。

## 6. consumer 閉包の確定 (B-01 / A-12 real・採用)

- direct helper caller: **9 file** (外部 8 + 定義元 1)。プランの「不明な 1 file」は存在しない。
  親の初回記載「10」が誤りだった。
- 名前検索の和集合: **22 file**。
- 意味的 consumer: **+1 = 23 file**。`orchestrator/verifier/commit_receipt.py:387-438` の
  `admit_replay_evidence()` が関数内 import で `CertifiedCampaignView` を受ける。
  **新 helper は不要** — `artifact_admission.py:97-113` の exact source 述語が
  `stage == STAGE_COMMIT` を要求し非ゼロを含意する。照合表には載せる。
- さらに `load_landscape` 経由の間接 consumer 2 file
  (`search_baselines.py`、`guided.py`)。節 4 の replay 配線で覆う。

**「22 file で全数」と書いてはならない。**

## 7. 記録するが実装しない (real だが scope 外)

### 自己 SHA による成果物 bytes の変化 (B-04 / A-11 real・採用、実装しない)

`artifact_admission.py:1039` は自分自身の SHA を `validator_sha256` として decision に入れ、
`layer3_report.py:651` は自分自身の SHA を `meta.generator.sha256` に入れる。
`autonomous_trial_completeness._layer3_comparison_projection` は
`generated_from_head` しか除かないため、両 file を編集すると保存済み v3 report と
fresh rebuild が byte 不一致になりうる。プランの「bytes は変わらない」は誤りである。

**親の実測でこの wave の blocker ではないと判定した。**
repo 内の保存済み Layer3 report 7 件の `meta.generator.sha256` は `705508de…` /
`89aa98e8…` であるのに対し、現在の `layer3_report.py` は `362fb98f…` で**既にずれている**。
`admission_decision.validator_sha256` は 7 件とも field 自体が無い。
つまりこれは本 wave が持ち込む破れではなく、**両 file を編集するあらゆる wave に共通する
既存の設計性質**である。互換層の新設は要求外であり `DW-G05` で却下する。
事実を worklog へ記録し、段 6 の受入全走で赤が出たら再裁定する。

### B-07 (real・採用、実装しない)

`p3_s4_loop.py` も B4 projection closure の member である。ただし MF-1 により
`p3_s4_loop.py` の変更自体を取りやめるため、この波及は消える。
`artifact_admission.py` と `layer3_report.py` の projection SHA 変化は残る。
`docs/phase3-b4-reflux-ablation-preregistration.md` の該当欄は未記入で、停止 pin は無い。
段 6 で `projection_sha256(base|sort|trigger)` の実装前後を記録するだけとする。

### A-09 (real・採用、表現を訂正)

「既存 certified 成果物の値は変わらない」は、tracked corpus に E1 certified campaign が
そもそも無いため、ほぼ空集合についての結論である。
**worklog では「tracked repository corpus では未発火」と限定して書く。**
外部 `output_root` の全数把握は本 wave では行わない (`DW-G05`)。

### A-10 / B-12 (real・採用、表現を訂正)

126 は「一律 admission gate 案を却下する証拠」にだけ使う。
**P1 実装で赤くなる node 数の上界ではない** (必須 field 追加、test support 追従など
probe に含まれない変更面があるため 126 を超えうる)。
実装後は件数比較でなく、各 node の**最初の拒否述語**で分類する。

## 8. refuted / 不採用

- **プランの「production 不明 1 file」** — refuted。親の再測定で 9 file が全数。
- **プランの S1 / S8B / S6 / S8A / backoff_repro / p3_s4_loop の共通化** — MF-1 により不採用。
  共通化するのは `_require_admitted_campaign` 内の loop だけとし、
  外部 caller は現状のまま残す。「production の直接呼出を定義元だけにする」という
  プランの静的条件も**取り下げる**。D1246 の要求は「1 つの共通 admission helper へ通す」であり、
  `require_persisted_certified_commit` が既にその helper である。
- **A-14 の型 / docstring 契約更新** — 採用 (節 5 に統合)。
  「future-only producer を実在 consumer に数えるか」の裁定パッケージ化は**不要**。
  節 2 のとおり既存テストが発火条件を満たしており、`DW-G04` を通る。

## 9. プラン v2 (実装する内容の全体)

1. `orchestrator/campaign/artifact_admission.py`
   - `admit_persisted_certified_commits(records, *, campaign_lock_sha256) -> int` を新設。
     `records` を走査し `stage == STAGE_COMMIT` の各 record へ既存
     `require_persisted_certified_commit(records, record, ...)` を**同じ母集合 `records` で**適用し、
     検査を通った件数を exact `int` で返す。0 件は `0` を返し拒否しない。
   - `_require_admitted_campaign` の手書き loop (`:1268-1275`) をこの 1 呼出へ置換する。
   - `CertifiedCampaignView` に必須 keyword field
     `persisted_certified_commit_count: int` を足す。
     `__post_init__` で exact `int` (bool 不可)、`>= 0`、snapshot 内 commit 件数と一致を検査する。
   - `require_certified_commit_evidence(view) -> CertifiedCampaignView` を新設。
     `require_certified_campaign_view` で exact 型を検査し、件数 0 を
     `ArtifactAdmissionError` で拒否する。
   - `CertifiedCampaignView` の docstring に「commit の存在は保証しない。
     存在保証は `require_certified_commit_evidence` だけが与える」と書く。
2. `orchestrator/campaign/replay.py` — `load_landscape` の view 取得直後
   (`:184-187`) に `require_certified_commit_evidence` を通す。
3. `orchestrator/campaign/layer3_report.py` — `build_accepted_report` の
   certified view 取得箇所 (`:742-748`) を `require_certified_commit_evidence` へ通す。
4. テスト — MF-2、MF-3、MF-4 の全件。`test_artifact_admission.py` の
   `test_persisted_commit_gate_accepts[no-commit-campaign]` は削除も改名もしない。
5. `orchestrator/tests/acceptance_duration_ledger.json` — 実装後に collect した
   **新規 node 全件**を実測 duration で add-only 追加する (B-08 real・採用)。推定値は書かない。

**編集しない:** `certified_writer_admission.py`、`certified_writer_preflight.py`
(本欠陥の閉包外。全文検索で `artifact_admission` 参照 0 件)。
epoch gate、overlay ledger、token 発行、exact 型拒否、`p3_s4_loop.py`、
外部 8 consumer の helper 呼出。

## 10. 変異事前登録 (`DW-M01`)

各変異は「同じ入力を拒否する層が前後に無く、無効化時の赤理由が一つに絞れる」ことを
コードで確認した。位置は実装後の最終 commit で anchor を再検証する (`DW-M07`)。

| ID | 位置 | 変異内容 | 期待 kill node (完全集合は段 6 で確定) |
|---|---|---|---|
| M1 | 新 `admit_persisted_certified_commits` | 内側の `require_persisted_certified_commit` 呼出を除去し件数だけ増やす | `test_persisted_commit_gate_rejects[*]` |
| M2a | 同上 | `stage == STAGE_COMMIT` の filter を外し全 record へ単数 helper を適用 | 先行 `TypeError` で落ちる。期待理由は「COMMIT 以外を渡した型拒否」 |
| M2b | 同上 | filter は残し件数だけ全 record 数にする | view の件数整合検査 |
| M3 | `_require_admitted_campaign` | 走査結果を無視し件数へ定数 1 を渡す | 既存 no-commit admission node + 件数整合検査 |
| M4 | `CertifiedCampaignView.__post_init__` | 件数の exact int 検査を削除 | `True` を渡す private construction test |
| M5 | 同上 | 件数と snapshot commit 件数の一致検査を削除 | 偽造 count の private construction test |
| M6 | `require_certified_commit_evidence` | 拒否条件を `count < 0` へ弱化 | helper 単体の zero-count test |
| M7 | `replay.load_landscape` | helper 呼出を除去 | commit 0 件 E1 landscape の consumer test |
| M8 | `layer3_report.build_accepted_report` | helper 呼出を除去 | commit 0 件で `certifying_input=True` が出る新 test |
| M9 | `_require_admitted_campaign` | 非ゼロ条件を admission 層へ移動 | 既存 no-commit admission node、wiring probe の diff reject、P3 rejection 往復 |

**登録しない変異と理由:**
- helper を無条件成功にするだけ — 自明。
- 保存済み commit 0 件の 2 campaign を使う変異 — 上流 epoch gate が先に拒否する
  (親が実測: `state=E0 reason=v1-authority-absent`)。
- v2 authority を除去する変異 — 同上。
- epoch / overlay / token / exact 型拒否を変える変異 — scope 外。
- 外した 4 配線に対する変異 — 節 4 のとおり先行 gate が落とすため、単一理由性を満たさない。

**過剰拒否の正例 (`DW-M01` の「受理集合を縮小する wave」条項):**
commit 1 件以上を持つ正規 E1 campaign が、`load_landscape` と
`build_accepted_report` の両方を従来どおり通ることを正例として登録する。

## 11. 分割方針 (B-10 real・採用)

**単一 author 子。** producer kernel (共通 helper、件数 field、要求 helper) と
consumer adapter (replay、layer3_report、test support、ledger) は
新 API と constructor 契約を共有し、並行に独立実装できない。
