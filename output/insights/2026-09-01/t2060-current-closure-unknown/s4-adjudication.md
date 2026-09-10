# 段 4 裁定 — [T-2060] D1245

基準 commit: `ac9a9ed7feb514fb19f419e4845eb809866d919f` (段 4 直前に local main を `--ff-only` で取り込み済み)。
裁定 inbox 再走査: `docs/decisions.md` の最新は D1317。D1245 を supersede する裁定は無い。
`docs/spool/` に未 fold の fragment は無い。worklog 最新 (1114) でも T-2060 は持ち越しで未実装。

## 1. 所見の裁定

### レンズ A (正しさ境界)

| ID | 判定 | 採否 | 裁定 |
|---|---|---|---|
| A-01 | refuted | — | プランどおりなら certified campaign の受理集合は広がらない。親も独立に確認した。 |
| A-02 | real | 不採用 (既裁定) | module global token による certified view の偽造可能性は **D1252 が明示的に裁定済み**で、「同一 process から偽造可能であり完全な権限隔離ではない限界を維持・明記する」とある。本 wave の新事実ではない。 |
| P-01 | real | **採用** | 正例の構造部分 (dirty closure でも歴史閲覧が成功する) は `test_historical_epoch_display_is_independent_of_live_closure_bytes` で**既に通っている**。新テストのその部分は回帰 pin であって新規性ではない。**worklog に正直に書く。** |
| P-02 | refuted | — | property は現行型に存在しないため、直接属性 assert なら無変更実装は `AttributeError` で赤。恒真ではない。 |
| P-03 | real | **採用** | 定数 property は閉包不在との因果を検査しない。**表示値の変異は kill ではなく診断感度 pin (DW-M08) へ別枠登録する。** |
| N-01 | refuted | — | 負例の向きは正しい。dirty bytes で `disk != HEAD blob` が必ず成立する。 |
| N-02 | real | **不採用 (nit)** | 「epoch gate が persisted COMMIT 検査より前」という時点は固定できない。しかし順序が入れ替わっても両経路とも拒否し、**受理集合も成果物の値も変わらない**。DW-G05 の成果物影響を 1 行で書けないため must-fix にしない。call-order sentinel と二重不正 fixture の新設は scope 外。 |
| M-02 | real | **採用** | 「capture/catch bypass」は二義的。**exact patch を事前登録する** (下記 M2)。 |
| M-03 | real | **採用** | P-03 と同じ。診断感度 pin へ。 |
| M-07 | real | **採用** | certified 昇格時の除去削除は fail-open ではなく liveness。別枠 (下記 L1)。 |
| F-01 | real | **採用** | 正例を 1 node に詰めない。構造・表示・report 投影・certified 負例を別 node へ分割する。 |
| F-02 | real | **採用** | 負例の「certified view は発行されない」は例外 assert の言い換え。削る。capture 内部は変異対象にしない。 |
| E-01 | refuted | — | 親の実測は正しい。ただし**「歴史 API 全体が現行 source を読まない」までは一般化しない** (前段 `_inspect_campaign` は現行 validator hash と現行 policy を読む)。 |
| E-02 | real | **採用 (親の訂正)** | 親の「現行閉包の可用性 = 24 path が HEAD と一致」は**過大一般化**。`capture_contract_loader_binding` は root 解決・Git top-level・no-follow/race・Git 実行・timeout・commit/blob 解決の失敗も同じ `ContractLoaderBindingError` に畳む。**`current-closure-unavailable` は drift 以外も表す。** |
| E-03 | refuted | — | `artifact_admission.py` は exact 24 path (line 57) に含まれる。親の実測は正しい。 |
| E-04 | real | **採用 (親の訂正)** | 親の「編集中は certified 経路のテストが赤」は**全 certified テストへの一般化として誤り**。`_committed_closure_repo` + `_REPO_ROOT` 差し替えの隔離 fixture は未 commit 編集中でも緑になりうる。**期待赤の一括分類を禁止し、赤は 1 件ずつ本文で判定する。** |
| E-05 | real (子は未検証) | **refuted (親の実測で)** | 子の射影外だったため確認できなかっただけである。親は `FROZEN_MANIFEST` の全 23 key を読み、いずれも `output/` 配下の成果物で閉包ソースを 1 件も含まないことを確認した。`p3_b4_closed_critic.py:636`・`p3_b4_raw_record_producer.py:660`・`test_t671_source_binding.py:31`・`test_s1_9pair_figure_provenance.py:49` はいずれも **live hash 計算**であり literal bytes pin ではない。durable manifest の再発行は不要。 |
| R-01 | real | **scope 外 → 裁定パッケージ** | 下記 §3。 |
| R-02 | real | **scope 外 → 裁定パッケージ** | 下記 §3。親も独立に確認した (`artifact_admission.py:1150-1152` の現行 policy 比較は purpose を問わず前段で拒否する)。 |

### レンズ B (裁定整合と実効性)

| ID | 判定 | 採否 | 裁定 |
|---|---|---|---|
| B-01 | real | **一部採用 → 裁定パッケージ** | 下記 §3。 |
| B-02 | real | **採用** | replay の purpose 付け替えは `require_certified_campaign_view` の exact 型で止まり、wrapper まで緩めれば保存済み COMMIT 検査と証拠 capability を同時に失う。**規律 2 に触れるため実装しない。** |
| B-03 | refuted | — | certified 側の禁止条件は仮想リスク gate ではなく、新 field が `additionalProperties:false` の下で certified 契約まで広げてしまうのを打ち消す補償条件。**本題に必要な意味互換性の検査**と判定する。 |
| B-04 | refuted | — | optional かつ certified 側だけ禁止なら、保存済み v2/v3 report は 1 件も読めなくならない。 |
| B-05 | refuted | — | 表示は成果物へ実際に届く。DW-G05 はゼロ影響ではない。 |
| B-06 | real | **scope 外 → 裁定パッケージ** | 下記 §3。 |
| B-07 | refuted | — | oracle の exact key 集合と reason enum は不変。 |
| B-08 | real | **採用** | 焦点走へ replay 系 test を足す。replay を変更しなくても `artifact_admission` の直接 consumer である。 |

### 親自身の追加所見 (どちらの子も出していない)

| ID | 判定 | 採否 | 裁定 |
|---|---|---|---|
| PA-01 | real | **採用 (scope 外の根拠)** | S-1 の purpose を素朴に歴史側へ替えると、`current-closure-unavailable` だけでなく **`E0 / v1-authority-absent` の拒否まで同時に落ちる** (`artifact_admission.py:961-962` は certified 分岐の内側)。付け替えは 1 行では済まない。 |
| PA-02 | real | **採用 (scope 外の根拠)** | `s8b_oracle_report.py:562-575` にも同型の lock-only certified epoch gate があり、`certified_eligible` を通じて oracle 判定へ入る。**歴史閲覧と現行認証の線引きは消費者ごとの設計判断であり、S-1 単独では閉じない。** |
| PA-03 | real | **採用 (実装制約)** | `test_s1_report.py:538-544` と `test_layer3_report.py:1360-1368` はどちらも epoch 投影の **exact dict 比較**である。既存期待値を変えずに新 field を足せるのは **Layer 3 の top-level だけ**である。 |

## 2. プラン v2 (実装する範囲)

**scope の線引き:** D1245 は *purpose の分け方* を定める裁定である。**どの消費者がどの purpose を宣言するか**は
消費者ごとの設計判断で、certified 成果物の受理集合を変える。ユーザーは
「現行認証に必要な意味互換性は fail-closed のまま維持してください — ここを緩めるのは裁定の内容ではありません」
と明示した。よって本 wave は **purpose の分離の実体と表示**までを実装し、**消費者の再分類は行わない**。

1. `orchestrator/campaign/artifact_admission.py` — `HistoricalCampaignView` に read-only property
   `current_verifier_conformance` を追加し、exact `"unknown"` を返す。
   `CampaignVerifierEpoch`、`CertifiedCampaignView`、中央 gate、reason enum は**変更しない**。
2. `orchestrator/campaign/layer3_report.py` — 歴史 `build_report` で
   **top-level の optional field** `current_verifier_conformance` として投影する。
   nested `campaign_verifier_epoch` は変更しない (PA-03)。
3. `orchestrator/campaign/layer3_schema.json` — top-level `properties` へ
   `"current_verifier_conformance": {"const": "unknown"}` を追加。**top-level `required` には追加しない。**
   `certifying_input=true` のとき同 key を禁止する既存 conditional を拡張する。
4. `orchestrator/campaign/layer3_report.py` — certified 昇格 (`build_accepted_report`) で
   歴史専用の top-level field を除去してから certified 検証へ渡す。
5. テスト (F-01 に従い node を分割する)。
   - (a) 構造回帰 pin: 実 fixture repo の閉包を未 commit で汚した状態で、`HISTORICAL_RAW` が
     exact `HistoricalCampaignView` を返し E1 が保たれ拒否が上がらない。
     **これは現行実装でも通る (P-01)。回帰 pin であって新規性ではない。**
   - (b) 表示 pin: 同じ状態で `view.current_verifier_conformance == "unknown"`。
     **直接属性アクセスで書く。`getattr(..., "unknown")` と `.get(..., "unknown")` を禁止する。**
   - (c) 負例: 同じ状態で `CERTIFIED_ACCEPTANCE` が exact `CampaignVerifierEpochRejected`
     (`epoch_state == "E1-stale"`、`reason_code == "current-closure-unavailable"`) を上げる。
     「certified view は発行されない」の冗長 assert は書かない (F-02)。
   - (d) 歴史 Layer 3 report が top-level `"unknown"` を持つ。
   - (e) 新 field を欠く保存済み v2/v3 report が `_validate_schema` を通る。
   - (f) certified report は同 field を持たない。well-formed certified report へ注入すると schema が拒否する。

   (a)〜(c) の fixture は `_committed_closure_repo` と `_REPO_ROOT` 差し替えを使い、
   **`capture_contract_loader_binding` そのものを差し替えない** (機構を通る正例・負例、F649)。

**gate の禁止 (署名で書く、DW-S04):**

- 禁止: `certifying_input == true` である Layer 3 report は、top-level key
  `current_verifier_conformance` を持ってはならない。
- 通る正例: `certifying_input == true` かつ同 key が不在の well-formed certified report は
  schema を通る (= 現行の certified report そのもの。テスト (f) の前半)。

**DW-O13 (gate 入力の実在):** 述語の入力は Layer 3 report の top-level key の有無である。
producer が出しうる値は `"unknown"` の 1 種だけで、歴史 report は必ず出し certified report は必ず出さない。
到達可能性は producer 側の実装で決まり、テスト (d)(f) が両方向を実測する。

## 3. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

### RP-1. 過去の測定を読む消費者の purpose 再分類 (B-01 / R-01 / B-06)

**問題。** 中央 gate は D1245 のとおり分かれているが、過去の測定を実際に読む次の消費者は
`CERTIFIED_ACCEPTANCE` を宣言しているため、現行閉包が読めないと過去の測定が返らない。

- `orchestrator/campaign/replay.py:179` `load_landscape` → `guided.py:204,225,252`、`search_baselines.py:304`
- `orchestrator/campaign/s1_report.py:302-310` (S-1 直接比較 report の epoch gate)
- `orchestrator/campaign/s8b_oracle_report.py:562-575` (oracle observations の epoch 証拠、PA-02)

**分かっていること。**
- S-1 は可用性 gate と保存済み COMMIT 証拠検査 (`s1_report.py:352`) が**別関数**なので、
  可用性だけを歴史側へ移しても記録された証明の鎖は失われない。**ただし PA-01 のとおり
  E0 拒否も同時に落ちるため、S-1 側で明示的に維持する必要がある。**
- replay は `require_certified_campaign_view` の exact 型と replay 証拠 capability に束縛され、
  purpose だけ替えても動かない。緩めれば規律 2 に触れる (B-02)。
- oracle は `certified_eligible` を判定する面であり、現行認証に近い。

**設計択一。**
- (A) S-1 だけ可用性を歴史側へ移し (E0 拒否は維持)、`current_verifier_conformance` を投影する。
  小さく安全だが、**S-1 の `certified_gate` の受理集合が広がる** (作業ツリーが汚れていても通る)。
- (B) 記録 commit・保存済み受領証は検査するが現行閉包を要求しない **第三の purpose**
  (historical-certified) を新設し、replay・S-1・oracle を順に移す。効果は大きいが新機構である。
- (C) 現状維持とし、D1245 は「purpose 分離の実体と表示」で完了とする。

**親の推奨: (A) を次 wave で、(B) は作らない。** 理由は、(A) が既存構造だけで閉じ、
規律 2 の防壁 (記録された certification 証拠) を 1 つも外さないためである。(B) は
ユーザーが scope 外と指定した「一般化・互換層」に当たる。**ただし (A) は certified と名の付く
gate の受理集合を広げるため、親の一存では実施しない。**

### RP-2. 歴史閲覧に残る現行 policy 依存 (R-02)

`artifact_admission.py:1150-1152` は `_inspect_campaign` の中で campaign lock の `build_admission` を
**現行 policy** と比較し、不一致なら purpose を問わず拒否する。過去に正当だった v2 campaign は、
policy の版が上がると歴史閲覧でも読めなくなる。これは `current-closure-unavailable` とは別の識別子であり
D1245 の射程外だが、**絶対規律 7 の同じ趣旨に触れる。**
親の推奨: 別 T として起票し、「現行の正しさ主張に必要な意味互換性」に当たるかを裁定する。

### RP-3. certified view 発行 token (A-02)

**既に D1252 が裁定済み**であり、本 wave の新事実ではない。再提起しない。参考として記す。

## 4. 変異事前登録 (DW-M01 / M03 / M08)

すべて実装前に登録する。位置ごとに「同じ入力を拒否する層が前後に無い」ことを確認した。

### 境界変異 (kill として数える — 受理集合か fail-closed 挙動が期待方向へ変わる)

| ID | 位置 | exact 変異 | 期待 | 単一理由性の確認 |
|---|---|---|---|---|
| M1 | `artifact_admission._require_verifier_epoch_for_purpose` の `HISTORICAL_RAW` early return | `if purpose is CampaignReadPurpose.HISTORICAL_RAW: return recorded.diagnostic` の 2 行を削除する | KILLED | 前段の記録閉包検査は commit blob だけを読み working tree を読まない (`contract_loader_binding.py:386-401`)。後段の `HistoricalCampaignView` は記録 E1 を受けるだけ。削除時にだけ歴史経路が live capture へ落ちる。 |
| M2 | 同関数の certified 分岐 | `try: capture_contract_loader_binding() except ... raise` の **try/except 全体を削除**し `return recorded.diagnostic` だけ残す (capture を一切呼ばない) | KILLED | 現行閉包を読む層は前後に無い。catch だけを消す変異は raw 例外で拒否されたままになり受理集合が変わらないため、**登録するのは全体削除の 1 形だけ**とする (M-02)。 |
| C1 | `layer3_schema.json` top-level `required` | 新 field を `required` へ追加する | KILLED | 保存済み report fixture は他の schema 条件をすべて満たす。赤理由は「optional field が無い」だけ。過剰拒否方向の受理集合変化。 |
| C2 | `layer3_schema.json` の `certifying_input=true` 禁止条件 | 新 field の禁止句を削除する | KILLED | 注入する certified report は receipt・admission・E1 を満たす。赤理由は禁止条件の fail-open だけ。 |

### 診断感度 pin (kill として数えない、DW-M08 別枠)

| ID | 位置 | exact 変異 | 期待 |
|---|---|---|---|
| D1 | `HistoricalCampaignView.current_verifier_conformance` | 戻り値を `"unknown"` 以外へ変える | 表示 pin が赤。受理集合は不変 (P-03 / M-03)。 |
| D2 | `layer3_report.build_report` の top-level 投影 | 投影行を削除する | 歴史 report 正例が赤。schema は optional なので拒否しない。 |

### liveness 変異 (別枠、M-07)

| ID | 位置 | exact 変異 | 期待 |
|---|---|---|---|
| L1 | `layer3_report.build_accepted_report` の field 除去 | 除去行を削除する | 正常な certified report の生成が後段 schema で落ちる。安全側の fail-open ではない。 |

**過剰拒否の正例 (DW-M01)。** C1 は受理集合を縮小する方向の変異なので、
承認外の過剰拒否を捕まえる正例として **テスト (e)** (新 field を欠く保存済み v2/v3 report が通る) を
登録する。

## 5. 実装子への期待赤の事前指定 (DW-S05-C)

親 docs は未 land である。**期待赤を一括分類しない (E-04)。**

- `orchestrator/campaign/artifact_admission.py` を未 commit で編集している間、**実 repo root を
  使う** certified 経路だけが `current-closure-unavailable` で赤になりうる。
- 隔離 fixture (`_committed_closure_repo` + `_REPO_ROOT` 差し替え) を使うテストは
  **未 commit 編集中でも緑である**。これらの赤は回帰として報告する。
- 判定は赤の assertion 本文と差分実体で行い、署名の見た目一致で環境要因に当てない。

## 6. 焦点走の file 集合 (DW-O26 / B-08)

変更する production file を参照する consumer test を参照関係で引く。

- `orchestrator/tests/test_artifact_admission.py` (変更 test file。単独走も行う)
- `orchestrator/tests/test_layer3_report.py` (変更 test file。単独走も行う)
- `orchestrator/tests/test_layer3_admission_diagnosis.py`
- `orchestrator/tests/test_t671_source_binding.py`
- `orchestrator/tests/test_s1_report.py`
- `orchestrator/tests/test_critic.py`
- `orchestrator/tests/test_bench_first_real_wal.py` (replay 系、B-08)
- `orchestrator/tests/test_guided.py` (replay 系、B-08)
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_s8b_oracle_report.py`
- `orchestrator/tests/test_s1_9pair_figure_provenance.py`
- `orchestrator/tests/test_campaign_lock_codec.py`

新規 test file は作らない (既存 2 file へ追加する) ため、file 集合を走査する一覧検査は発火しない。
