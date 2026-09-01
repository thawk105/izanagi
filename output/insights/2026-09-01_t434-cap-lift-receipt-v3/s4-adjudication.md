# [T-434] 段 4 裁定 — cap-lift 受領証と consumer 結線

基準: main `08a17b3b3`。段 2 プラン + 段 3 レンズ A / B (must-fix 各 7 件)。
親はすべての所見を現物で照合した。

## 裁定 0 — 本 wave は実装しない (`4→7→8→9`)

**理由 (3 本とも独立に成立する。1 本でも成立すれば実装は不可)。**

1. **受理枝が発火不能で、正例を実体の差し替え無しに置けない。**
   P6 の意味的充足契約 (D156) は認定記録を要求するが、その実体が repo に無い。
   `reflux_formal_consumer.py` は他条件を評価したうえで `P6_UNAVAILABLE` (:108, :934, :1034) で
   明示的に停止する。合接はこの 1 件だけで閉じる。
2. **正式系列では受領証があっても上限が開かない。** registered manifest は
   `generations` を「整数 2」だけ受理し (`trial_registry.py:771`)、実行時値と manifest 宣言値の
   一致が要求される (`p3_autonomous_workload_trial.py:1258`)。3 世代を registered 経路へ通すには
   8c 事前登録と manifest schema の改訂が要り、それは T-435 の所有と新規ユーザー裁定の領域である。
3. **topology だけで受理枝を開くと前提条件を迂回する。** 人間発効 commit の形式検査だけで
   cap を開く v1 は実装可能だが、D121 決定 (7) が固定した前提条件 10 件、
   D150 決定 (4) の「状態語を申請側に選ばせない」、D156 の end-to-end calibration と
   認定記録要求を迂回する。これは正しさ・承認ゲートを緩める向きであり採らない。

**D841 とは矛盾しない。** D841 が定めたのは「実装するなら受領証と consumer 結線を同じ変更単位に
する」であって、実装時期ではない。受領証だけ先に作る形も採らない。本裁定は「今は実装しない」であり、
D841 の不可分性要求はそのまま維持される (レンズ A の所見 9 に従い、NO-GO の根拠を D841 から
D150 / D156 / positive control 不在へ置き換えた)。

**DW-G04 にも合致する。** 発火条件を満たす既存 artifact path も計測 ID も brief に書けないため、
本設計は設計メモに留める。

## 裁定 1 — 親の実測の訂正 (real と認めた反証)

| 親の主張 | 判定 | 現物 |
|---|---|---|
| N1 上限は 2 | **real** | `p3_autonomous_workload_trial.py:144` |
| N2 層 3 の版は据え置き | **real** | D828、`layer3_schema.json` top-level に optional 先例 |
| N3 C11 が第 7 の consumer | **refuted** | C11 は静的 AST 検査で成功末尾も `EVIDENCE_UNDEFINED`。runtime consumer ではない |
| M6 P1〜P9 の評価器 0 件 | **refuted (過剰一般化)** | P1 は D160 が充足を記録。`reflux_formal_consumer.py` に評価実装あり。塞いでいるのは P6 |
| M3 g11 は T-435 が発行 | **stale** | `condition-freeze.v1.g11.json` は実在し `ruling_reference` は D1066 |
| M4 層 3 の既存受領証結線は先例 | **限定付き** | `build_accepted_report` は `certifying=true` 必須、parser は `certifying=false` 強制。docstring 自身が「結線済みの証拠ではない」と書く |

「参照検索が 0 件」から「実装が 0 件」を導いたのが誤りの型である。不在は性質で測る。

## 裁定 2 — scope から外すもの

- **C11 (事前登録の証拠契約と評価器) を T-434 の scope から外す。** D882 決定 (3) が
  `required_evidence` と評価器を変えないと定め、却下選択肢で「機構を足すのは変更単位を超える。
  必要なら独立の裁定として起こす」と明記している。契約 file は
  `test_s8c_preregistration_core.py:1195-1198` が内容 hash を literal で凍結している。
- **runbook の承認上限の主張文を書き換えない。** D882 が T-435 の変更単位として予約している。
- **`docs/phase3-8c-preregistration.md` を編集しない。** 同上。

## 裁定 3 — 実装する場合に必要な consumer 閉包 (今回は実装しないが、設計として確定する)

段 2 プランの 7 面は不足していた。実測で確定した閉包は次のとおり。

1. producer の 3 入口と共通純関数 (`_validate_generation_budget` の前段)
2. journal `run-start` の envelope
3. supervisor report — **正常系だけでなく `_budget_indeterminate_report` (:1881) も**
4. completeness の独立再検証 (`run-envelope` :2289 / `campaign-chain` :4829)
5. 層 3 — ただし run 行への複製ではなく top-level 1 箇所
6. **`trial_registry` の manifest generation 契約 (:771)** — プランが数えていなかった面
7. runbook の多世代コマンド節 (D882 予約文の外)

C11 は consumer ではないので閉包から外す。

## 裁定 4 — 実装前に解かねばならない設計の穴 (real、今回は設計として記録する)

- **申請束縛の preimage が未定義で循環する。** campaign ID は receipt SHA を含み、
  origin binding は campaign ID を含む。除外規則を domain-separated に定義し、
  全 consumer で同じ除外を pin しないと、同じ受領証が別の運転構成を承認する。
- **定数だけの引き上げが manifestless exploratory 経路に残る。** C11 は offline の変異検出器で
  あって実行時 gate ではない。receipt 無しの実効 cap は producer と completeness の双方で
  literal 2 として実行時に検査する必要がある。
- **hardened git 面が HEAD 捕捉にしか掛かっていない。** 全 git 呼出しを 1 つの helper へ閉じ、
  replace/grafts/shallow 拒否・config 無効化・環境 allowlist を共通適用する。
- **層 3 を編集すると `meta.generator.sha256` が変わる。** fresh rebuild 比較はこの field を
  正規化しない (`autonomous_trial_completeness.py:4700-4720` は `generated_from_head` だけ pop する)。
  既存の永続化済み材料レポートが campaign-chain で不一致へ転じうる。互換規則を先に設計する。
- **`_run_workload` の scope は generation を束縛しない。** registered の manifest 2 と
  receipt-backed 3 を混在させる余地が残る。scope 封印に generation と受領証 SHA を含める。

## 裁定 5 — 既存機構の再利用 (実装時の必須条件)

新規に書かず、次を共有部品へ抽出して再利用する。両レンズが独立に must-fix とした。

- 人間発効 commit の topology 検査: `s8b_ratified_freeze.py` の
  `_raw_ai_agent_lines` / `_parsed_ai_agent_values` / `_is_none_commit` / `_assert_user_commit`。
  ただし `_assert_user_commit` 単独では親がちょうど 1 つであることを保証しないため、
  親一致は cap policy 側で足す。
- canonical bytes・重複 key 拒否・exact key・sha256/commit validator・HEAD blob 読取・
  git env allowlist・封印型: `s8c_acceptance_receipt.py`。
- producer と completeness で 2 つの parser を持たない。schema 固有の field 判定だけを新設する。

## 裁定 6 — ユーザーへ返す裁定パッケージ

本 wave は次の 3 択をユーザー裁定へ返す。親は代行しない。

- **択 A (親の推奨): WAIT を維持し、解除条件を確定する。** 解除条件は
  (i) P6 の意味的充足契約の実装と実 accreditation record、
  (ii) registered manifest / 8c 事前登録の generation 契約を receipt 条件付き `3..10` へ改訂する裁定
  (T-435 の変更単位との順序を含む)、
  (iii) 裁定 4 の設計の穴 5 件の解消。
  これらが揃った後、裁定 3 の閉包と裁定 5 の再利用方針で単一変更単位として実装する。
- **択 B: 前提条件の機械再導出要求を外し、人間発効 commit を状態判定の権威にする。**
  受理枝は発火可能になるが、D121 決定 (7) / D150 決定 (4) / D156 の明示 supersede が要る。
  かつ択 B だけでは registered の exact `G=2` は解けないため、(ii) も同時に必要である。
- **択 C: 到達不能を承知で fail-closed な将来の入口として land する。**
  repo には先例がある (`layer3_report.build_accepted_report` は自ら
  「結線済みの証拠ではない」と書いて land されている)。ただしその先例の正例は
  `SimpleNamespace(certifying=True)` と verifier の差し替えで作られており
  (`test_layer3_report.py:264-270` ほか)、実体を stub しない正例という本 wave の要求とは両立しない。
  採るなら「正例を持たない入口を land してよいか」を明示的に裁定する必要がある。

## 変異事前登録 (DW-M01)

実装面の差分がゼロのため変異 matrix は免除される (DW-S04)。受入全走は免除しない。
段 2 プランが起草した負例 22 件・正例 7 件は、実装 wave のための事前登録候補として
設計メモへ逐語で残す。今回は登録せず、実行可能とも記録しない。
