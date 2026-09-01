# [T-434] cap-lift 受領証と consumer 結線 — 設計 v3 (実装不可の確定と裁定パッケージ)

```
status: PROPOSED_UNRATIFIED        # 裁定パッケージを返す。ユーザー裁定を経ていない
machine_effect: NONE               # 本 wave の実装面の差分ゼロ。機械受理集合・凍結 bytes・proof chain 不変
supersedes-premises-of: output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md
```

本書は 2026-08-04 の設計 v2 を置き換えるものではなく、**v2 が前提にしていた事実のうち失効した
ものを実測で確定し、実装可能性の判定をやり直したもの**である。v2 の骨格 (小 receipt + witness
分離、exact-pin、receipt からだけの cap 導出、同一 envelope の投影) は維持する。

## 0. 結論

**本 wave では実装しない。** 理由は独立に 3 本あり、1 本でも成立すれば実装は不可である。

1. 受領証の受理枝が発火不能で、正例を実体の差し替え無しに置けない。
2. 正式系列では受領証があっても上限が開かない (registered manifest が `generations` を整数 2 に固定)。
3. 発効 topology だけで受理枝を開くと、D121 / D150 / D156 が置いた前提条件を迂回する。

D841 とは矛盾しない。D841 が定めたのは「実装するなら受領証と consumer 結線を同じ変更単位に
する」であって実装時期ではない。受領証だけを先に作る形も採らない。

## 1. 設計 v2 の前提のうち失効したもの (実測 2026-09-01、main `265aa16e3` 時点)

| v2 の前提 | 現況 | 根拠 |
|---|---|---|
| `MAX_APPROVED_GENERATIONS = 1` は不変 | **2** である。D410 (2026-08-15) が D114 の上限 1 を 2 へ引き上げた | `orchestrator/campaign/p3_autonomous_workload_trial.py:144` |
| 択一 5 = 層 3 を v4 へ上げ top-level envelope を必須にする | 版上げは D828 (2026-08-25) が禁じている。`runs.items.properties` へ optional を足す変更で `schema_version` を上げない | D828 |
| 前提条件の充足は P 別の独立評価器が typed evidence から再導出する | この設計選択は裁定済み択一 1〜10 に含まれない。v2 本文の設計判断である | design-v2 §1、択一表 |
| 充足しているのは P10 のみ | P1 は D160 が充足を記録している。条件評価の実装も存在する | D160、`orchestrator/campaign/reflux_formal_consumer.py` |

**v2 §2 の「受領証が無ければ実効 cap = literal 1」をそのまま実装してはならない。** 現行で通っている
2 世代運転を止める、未裁定の受理集合縮小になる。受領証が支配するのは
**現行の承認済み定数を超える引き上げ** (`3..MAX_GENERATIONS`) である。

## 2. 実装不可の根拠 (それぞれ現物で確認済み)

### 2.1 受理枝が発火せず、正例を誠実に置けない

前提条件 10 件の合接は **P6 の 1 件だけで閉じる**。D156 が採用した意味的充足契約 v1 は
admission 結線まで含む end-to-end calibration と独立検査者 attestation、認定記録を要求するが、
その実体が repo に無い。`reflux_formal_consumer.py` は他条件を評価したうえで
`FormalReasonCode.P6_UNAVAILABLE` (:108, :934, :1034) と `P6Unavailable` 型 (:248) で明示的に停止する。

したがって受領証を発行しても受理されない。受理枝を発火させる正例を書こうとすると、
評価器・封印型・定数のいずれかを差し替えることになり、機構の正例が依存先を stub しない
という要求と両立しない。

**「参照検索が 0 件だから実装も 0 件」は誤った推論である。** 本 wave の親は当初
「`D121` を参照する実装が 0 件」から「P1〜P9 の評価器が 0 件」を導いたが、これは段 3 の
2 レンズが独立に反証した。不在は識別子の検索ではなく性質で測る。

### 2.2 正式系列では受領証があっても上限が開かない

registered 起動の manifest は `generations` を **整数 2 だけ**受理する
(`orchestrator/campaign/trial_registry.py:771` — `must be the integer 2`)。実行時の値と manifest
宣言値の一致は campaign identity 導出より前に要求される
(`orchestrator/campaign/p3_autonomous_workload_trial.py:1258`)。

さらに受領証が束縛すべき origin binding は registered-effective 経路でしか発行されない。
manifest を持たない unregistered exploratory 経路は 3 世代の候補経路だが、
origin binding を再導出できない。

よって受領証の実受理集合は、P6 を解決しても空のままである。これを開くには
8c 事前登録と manifest schema の generation 契約を receipt 条件付き `3..10` へ改訂する
新しい裁定が要る。その locus は T-435 の変更単位と重なる。

### 2.3 topology だけで開くと前提条件を迂回する

人間発効 commit の形式検査 (非 merge・親が承認対象・create-only・`AI-Agent: none` 逐語 1 本) だけで
cap を開く v1 は実装可能である。しかしそれは D121 決定 (7) が固定した前提条件 10 件、
D150 決定 (4) の「申請側の宣言は入力にすぎず状態語を申請側に選ばせない」、
D156 の認定記録要求を迂回する。承認ゲートを緩める向きであり、本 wave では採らない。

## 3. consumer 閉包の確定 (実装時に結線する面)

設計 v2 の 6 面と段 2 プランの 7 面は、いずれも不足していた。実測で確定した閉包は次のとおり。

1. **producer の 3 入口** — `main` (:5064)、`run_trial` (:4397)、`_run_workload` (:3717) が
   副作用の前に同じ純関数を通る。
2. **journal `run-start`** — 新 event を増やさず envelope を足す。event 閉集合
   (`autonomous_trial_completeness.py:47`) は不変。
3. **supervisor report** — 正常系の構築 (:3524) だけでなく **`_budget_indeterminate_report` (:1881)**
   も generation budget を持ち、run-start より前に返りうる。段 2 プランはこれを落としていた。
4. **completeness の独立再検証** — `run-envelope` (:2289) と `campaign-chain` (:4829) の
   2 箇所が `producer.MAX_APPROVED_GENERATIONS` を読む。producer の validator を呼ばずに再検査する。
5. **層 3** — run 行への複製ではなく top-level 1 箇所。`search_config` は既に top-level の
   `workload` へ投影されるため、SHA の束縛は自動的に材料レポートへ入る。
6. **`trial_registry` の manifest generation 契約 (:771)** — 段 2 プランが数えていなかった面。
   ここを通らない限り正式系列の受理集合は動かない。
7. **runbook の多世代コマンド節** — D882 が T-435 のために予約した「承認上限の主張文」の外側。

**条件 11 (事前登録の証拠契約と評価器) は閉包から外す。** C11 は受領証の runtime consumer では
ない — 定数と 3 入口を AST で見るだけで、成功末尾も `EVIDENCE_UNDEFINED` である。加えて D882
決定 (3) が `required_evidence` と評価器を変えないと定め、却下選択肢で「機構を足すのは確定した
変更単位を超える。必要なら独立の裁定として起こす」と明記している。証拠契約の内容 hash は
`orchestrator/tests/test_s8c_preregistration_core.py:1195-1198` が literal で凍結している。

## 4. 実装前に解かねばならない設計の穴 (段 3 の 2 レンズが提起、親が現物確認)

- **申請束縛の preimage が未定義で循環する。** campaign identity は受領証 SHA を含み、
  origin binding は campaign identity を含む。除外規則を domain-separated に定義し、
  全 consumer が同じ除外を pin しない限り、同じ受領証が別の運転構成を承認しうる。
- **定数だけの引き上げが manifestless exploratory 経路に残る。** 条件 11 は offline の
  変異検出器であって実行時 gate ではない。受領証無しの実効 cap は producer と completeness の
  双方で literal 2 として実行時に検査する必要がある。
- **hardened git 面が HEAD 捕捉にしか掛かっていない。** replace refs / grafts / shallow の拒否、
  config 無効化、環境 allowlist を、全 git 呼出しへ共通適用する 1 つの helper に閉じる。
- **層 3 を編集すると `meta.generator.sha256` が変わる。** 生成器 file の hash は
  `layer3_report.py:651` で自身から取られ、fresh rebuild 比較
  (`autonomous_trial_completeness.py:4700-4720`) は `generated_from_head` しか正規化しない。
  永続化済みの材料レポートが campaign-chain で不一致へ転じうるため、互換規則を先に設計する。
- **`_run_workload` の scope が generation を束縛しない。** registered の manifest 2 と
  receipt-backed 3 を混在させる余地が残る。scope 封印に generation と受領証 SHA を含める。

## 5. 既存機構の再利用 (実装時の必須条件)

段 3 の 2 レンズが独立に「新規実装は重複」と判定した。次を共有部品へ抽出して再利用する。

- **人間発効 commit の topology 検査** — `orchestrator/campaign/s8b_ratified_freeze.py` の
  `_raw_ai_agent_lines` (:518) / `_parsed_ai_agent_values` (:528) / `_is_none_commit` (:546) /
  `_assert_user_commit` (:558) / `_assert_candidate_commit` (:573)。
  `AI-Agent: none` を raw 行ちょうど 1 本と parse 値の二重で判定する形が既にある。
  ただし `_assert_user_commit` 単独では親がちょうど 1 つであることを保証しないため、
  親一致は cap policy 側で足す。
- **受領証の解析・封印** — `orchestrator/campaign/s8c_acceptance_receipt.py` の
  canonical bytes (:172)、重複 key 拒否 (:233)、`_exact_keys` (:259)、
  sha256 / commit / posix path validator、HEAD blob 読取 (:658)、git env allowlist (:95)、
  封印型 `VerifiedAcceptanceReceipt` (:152)。
- producer と completeness で 2 つの parser を持たない。schema 固有の field 判定だけを新設する。

**層 3 の既存 `acceptance_receipt` 結線は「正例が発火する先例」としては数えない。**
`layer3_report.build_accepted_report` (:682) は `certifying is True` を要求する一方、
`s8c_acceptance_receipt.py:422` は `certifying is not False` を構造的に拒否する。
同関数の docstring 自身が「この checkout に certified-selection consumer は存在しない。
fail-closed な将来の入口であって結線済みの証拠ではない」と書いている。

## 6. 変異事前登録の候補 (今回は登録しない)

実装面の差分がゼロのため変異 matrix は免除される。段 2 プランが起草した負例 22 件・正例 7 件は
実装 wave のための候補として残す。**正例のうち「実 evaluator が裏付ける cap=3 の受領証で
3 世代が通る」は、現時点では実行可能と記録しない。**

負例の骨子: 受領証 SHA の欠落・偽 SHA・別 filename、重複 key / 未知 key / 非 canonical bytes、
`approved_max_generations` が 2 または 11 または bool、cap=3 で 4 世代、対象 revision の差し替え、
発効 commit の merge 化・親違い・別 file の同時変更、`AI-Agent: none` の欠落・重複・表記揺れ、
受領証の削除後再導入、witness の drift、前提条件の 1 件が非充足、
P6 が未実装、定数だけの引き上げ、3 入口のいずれかからの検証呼出し削除、
journal と report の片側 envelope 欠落、`search_config` の SHA 欠落、
層 3 の envelope 欠落、completeness を producer の validator 呼出しへ差し替える変異。

正例の骨子: 受領証無しの 1 世代と 2 世代 (現行受理集合の縮小を殺す)、
古い層 3 文書に envelope が無いこと (後方互換の破壊を殺す)。

## 7. ユーザーへ返す裁定パッケージ

- **択 A (推奨): WAIT を維持し、解除条件を確定する。** 解除条件は
  (i) P6 の意味的充足契約の実装と実認定記録、
  (ii) registered manifest と 8c 事前登録の generation 契約を受領証条件付き `3..10` へ改訂する裁定
  (T-435 の変更単位との順序を含む)、
  (iii) 本書 §4 の設計の穴 5 件の解消。
  これらが揃った後、§3 の閉包と §5 の再利用方針で単一変更単位として実装する。
- **択 B: 前提条件の機械再導出要求を外し、人間発効 commit を状態判定の権威にする。**
  受理枝は発火可能になるが、D121 決定 (7) / D150 決定 (4) / D156 の明示 supersede が要る。
  択 B だけでは §2.2 の registered 側 exact `G=2` は解けないため、(ii) も同時に必要である。
- **択 C: 到達不能を承知で fail-closed な将来の入口として land する。**
  repo に先例はある (§5 の層 3 accepted branch)。ただしその先例の正例は封印型と検証器の
  差し替えで作られており、実体を stub しない正例という要求とは両立しない。
  採るなら「正例を持たない入口を land してよいか」を明示的に裁定する必要がある。
