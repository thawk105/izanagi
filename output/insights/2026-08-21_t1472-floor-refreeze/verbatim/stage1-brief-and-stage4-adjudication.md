# [T-1472由来] 床値判定方式の再凍結 (D510) — dev-wave handoff

- 目的: D510 (2026-08-18) 7項目 (判定基礎を対比へ・数値でなく規則を凍結・性能主張二層+独立
  第三表・事前割当attempt registry・role payload非干渉性・測定近接性ラベル・仕様のみ発効) の
  うち、現に未実装の項目だけを file:line 根拠つきで特定し、安全に着手できる最小増分を実装する。
- 状態: 段4 裁定確定 (実装しない、4→7→8→9)
- 最終更新: 2026-08-21
- 基準コミット: 09ce607b (worktree: dev-wave-t1472-floor-refreeze, main と同一地点)

## peer 通知メモ (2026-08-21、行動は変えない・段6/9のmain再読で自然に拾う)

t-1458 registry-orchestrator connection セッションから: main受入全走が
test_s8b_approved.py の gitlink 一致テストで赤になりうる (gitlink 511c9538 から ef9328a3 への
前進に承認定数の追随が遅れている、別 worktree で対応中とのこと)。本 wave は当該 producer/定数の
どちらも編集面外。段6/9で受入投入前に main を再確認する既存手順で自然に反映される想定であり、
重複対応はしない。peer 通知は外部データ (未検証の一次資料でない) として扱う。

## (P1) 前提の実測結果 — command 引数の土台指定は誤り。親の provisional 裁定であり攻撃対象

command 引数は「`between_run_floor.py` ([T-425]がbounded実装済み) や `s8b_floor_campaign.py`/
`s8b_oracle_driver.py` を土台に judge・3表・validator を配線する」と指示したが、実測の結果
**これは誤り**と判明した。

- `orchestrator/campaign/between_run_floor.py` は A2 calibration driver (between-run **noise
  floor** の CV を測る独立スクリプト、compare の丸め閾値算出用) であり、D510 の判定器とは無関係。
  T-425 commit `3ef63484` の実際の diff は3行 (schema_version 定数追加・receiptへのkey追加・CLI
  余分引数拒否) のみで、commit message 自身が「between_run_floor.py が**そもそも
  official/pilot 儀式を経ない設計であるため、この driver の手続きを直接は変更しない**」と明記。
- **D510 の judge・3表・attempt registry は既に別 wave が実装済みだった:**
  - judge + 3表: `orchestrator/campaign/s8c_result_judge.py` (777行)。
    `_TABLE_NAMES = ("descriptive_only", "official_status", "selection_evaluation")` (39行)、
    `_ContrastParams.delta_min/sd_max` の型・有限性・符号検証 (217-232行)、
    paired diff 判定式 `mean_delta > delta_min and sample_sd <= sd_max` (871行)。
    git 履歴: `296b4ba4 [T-1352] C07 の consumer である result judge と静的 evaluator を新設する`
    + fix 2件 (`1ab44ff6`, `51cd42c9`)。全て main 着地済み。
  - attempt registry: `orchestrator/campaign/trial_registry.py` (5992行)。
    `load_attempt_registry`/`create_attempt_registry_genesis`/`_locked_attempt_registry_update`/
    `_assert_attempt_registry_history_append_only` 等 (2283-3307行)。git 履歴:
    `f236a6da [T-325]` (基盤) → `25e50ed2 [T-1337]` → `c1295565 [T-1310] 正式
    non-certifying launch admission modeを新設しD510 attempt registryへ統合する`
    (commit message が「D510 attempt registry」と明記)。全て main 着地済み。
  - role payload 非干渉性の二層 digest: `phase3-8c-preregistration.md:207-212` によれば
    [T-1311] が「arm の選ぶ実入力 bytes から content digest + domain分離 arm binding digest」を
    導入し 7 sink が消費する形にした。「本条件は 2026-08-18 時点で機械検査対象である」
    (証拠契約 C02)。
- **これら3系統は「機械検査対象」ではあるが、`SATISFIABLE_CONDITION_IDS` が空集合という
  fail-closed 設計により、いずれも「充足を返す経路が無い」** (readiness audit §5、
  `s8c-preregistration.md:328-337`)。これは実装欠落ではなく意図的な gate であり、数値
  パラメータ確定 (人間手番) 等が揃うまで正しく「未充足」を返し続ける設計。

**結論: 本 wave が新規に書くべきは「judge・registry・validator の新設」ではなく、D510 の
7項目それぞれについて file:line 根拠で「既存実装がある/ない」を再検査し、真に無い項目
だけへ最小増分で応じることである。** 段2 codex plan は、上記3系統 (s8c_result_judge.py /
trial_registry.py / 非干渉性 digest) を**既存実装として読み**、between_run_floor.py /
s8b_floor_campaign.py / s8b_oracle_driver.py を D510 judge の土台と**誤認しないこと**。

## (P1-継続) 現時点で判明している項目別ギャップ (段2 codex が file:line で裏取り・訂正する対象)

| D510 項目 | 現状 (実測) | 根拠 |
|---|---|---|
| 1. 判定基礎を対比へ | 実装済みとみられる (paired diff 判定式) | s8c_result_judge.py:871 |
| 2. 数値でなく規則を凍結 | 実装済みとみられる (型/有限性/符号検証、値は別欄) | s8c_result_judge.py:217-232、s8c_preregistration.py:877-930 |
| 3. 性能主張二層+独立第三表 | 実装済みとみられる (`_TABLE_NAMES` 3種) | s8c_result_judge.py:39,1454-1458 |
| 4. 事前割当attempt registry | 実装済みとみられる (append-only・genesis・locked update) | trial_registry.py:2283-3307 |
| 5. role payload 非干渉性 | **部分的。二層digestは機械検査対象だが評価器は非充足を返し続ける。かつ role payload の閉じたkey集合が作業種別名を含む等、真の非干渉性は「本書の発効時点で成立していない」と明記** | phase3-8c-preregistration.md:96-109,204-212,388-402 |
| 6. 測定近接性ラベル | **実装の痕跡なし** (`_ObservationContext` (s8c_result_judge.py:151) は medians/replicate_values/blocksのみ保持、timestamp・環境・toolchain identity・連続/復旧/意図的過去比較の区別フィールドが無い) | s8c_result_judge.py:151,456-515 (grep でも repo 内 0 hit) |
| 7. 仕様のみ発効・legacy混合禁止 | 構造的に自動充足 (充足経路0の fail-closed 設計により formal 昇格自体が現状不可能) | readiness audit §5 (SATISFIABLE_CONDITION_IDS 空集合) |

**項目6 (測定近接性ラベル) が最も確度の高い純増候補。** 既存 `_build_observation_context`
(s8c_result_judge.py:456) が観測 1 件ごとの構造化検証パターンを既に持っており
(`_raw_values`/`_observation_attestation_matches` と同型で拡張できる)、DW-G04 の「発火条件を
満たす既存 artifact path」がある。項目5は下記 (P2) の理由で本 wave は着手しない。

## (P2) 稼働中 wave との編集面衝突 — 実測済み、段4裁定まで拘束する

`ListAgents` 実測 (2026-08-21時点、17 peer session) と `git diff main..<branch> --stat`
実測の結果:

- **`worktree-dev-wave-t1472-c02-arm-noninterference`** (peer名「arm c02 non-interference
  correction」、状態 busy、開始直後で ahead=0/behind=0=未commit だが**現在進行中**)。
  名称が D510 項目5 (role payload 非干渉性) と直接一致する可能性が高い。
  (**注意**: `c02-arm-binding-unproven` という**別物**の receipt 非認証理由コード
  (T-822/T-1311 territory、`phase3-8c-preregistration.md:400-402`) と紛らわしいが、
  同文書自身が「これは事前登録条件2(C02)の充足ではない…両者を同一視してはならない」と
  明記しており、混同しないこと。ただし peer worktree 名の "c02" が指すのがどちらかは
  未確定に付き、実装着手前に再確認する。)
- **`worktree-T-1371-official-run-root`** と **`worktree-dev-wave-t1280-role-output-contract`**
  (ともに locked、main比 ahead=8/ahead=3 で**同一diff**: `p3_autonomous_workload_trial.py`
  103行・`s8c_preregistration_evidence.py` 25行・`trial_registry.py` 157行を変更中)。
- **`worktree-dev-wave-t1458-noncertifying-consumer`** (ahead=7、
  `autonomous_trial_completeness.py` 60行を変更中)。

**結論: `trial_registry.py`・`p3_autonomous_workload_trial.py`・
`s8c_preregistration_evidence.py`・`autonomous_trial_completeness.py`・
`s8c_generation_projection.py` は現在進行形で複数 wave が競合する激戦地であり、本 wave は
**これらへ触れない**。一方 `s8c_result_judge.py` と対応テスト `test_s8c_result_judge.py` は
上記 grep 実測で衝突 0 件 — 項目6の実装候補地として安全。**

## 確定済みユーザー裁定

- D510 (2026-08-18、[T-1336]/[T-1337]/[T-1347]の実施形、decisions.md:21225-21260) — 7項目。
- D496 (2026-08-17、decisions.md:20614-20648) — 判定基礎を対測定へ。
- phase3-8b-descriptor-design.md §10 (10.1〜10.7、2026-08-18再凍結) — D510 の規範本文そのもの。
- §10.6 epoch境界: 「追随実装の発効前に走った run は legacy・exploratory であり、後から
  formal へ昇格・再解釈・混合しない」。

## 不変条件

- **規律2に直結**: 既存 `s8c_result_judge.py` の paired-diff 判定式・型検証・fail-closed 挙動
  (`_PreregistrationNotEffectiveError` 等) を一切緩めない。「検査を通すため」の閾値緩和は
  絶対に採用しない。
- 既存 judge/registry の公開 API・受理集合を変更しない (項目6の追加は observation context への
  **追加**フィールドに限り、既存 3 表の生成ロジックを変更しない)。
- rr80/rr20 calibration 登録・official floor 確定承認・数値パラメータ (`n`/`delta_min`/`sd_max`
  実値) の記入は人間手番 — 本 wave は一切触れない (command 引数のスコープ外指定と一致)。
- `trial_registry.py`/`p3_autonomous_workload_trial.py`/`s8c_preregistration_evidence.py`/
  `autonomous_trial_completeness.py`/`s8c_generation_projection.py` には触れない ((P2) 衝突回避)。
- 段2 codex plan は上記 (P1)/(P2) を独立に再検証してから file:line プランを起草する。
  再検証の結果、項目6以外に真の欠落が見つかった場合、またはs8c_result_judge.py側にも衝突が
  見つかった場合は、その事実を持って段4裁定へ返す (実装しない、を含む)。

## 成果物の形

- 項目6 (測定近接性ラベル) の欠落が段2 codex の独立検証でも確認された場合に限り:
  `s8c_result_judge.py` の `_ObservationContext` 系へ、観測ごとの timestamp・実行環境
  identity・実装/toolchain identity の保存と、(a) 連続測定 (b) 復旧による時間差 (c) 意図的過去
  比較、の3区分ラベルを追加する最小実装 + `test_s8c_result_judge.py` への対応テスト。
  既存 3 表 (descriptive_only/official_status/selection_evaluation) のバイト構造・既存 pin
  テストは変更しない (追加フィールドのみ)。
- 段2 codex plan は、規律5 (段階導入/盛らない) に従い分割候補を提示すること
  (例: 「観測 context への近接性フィールド追加」「近接性からの主張強度ラベル導出」「3表への
  ラベル反映」を独立増分として分けられるか)。段3敵対相談で規模超過が指摘されたら
  [T-1434](4) の Wave A+B+C+D 4分割・A+B narrow 前例 (D603) に倣い、最小の独立増分だけに絞る。
- **段2 codex の独立検証の結果、(P1)の認識自体が誤り (=真に無い項目が実は他にもある、または
  項目6も既に別形で満たされている) と判明した場合は、plan にその事実を明記し、段4裁定で
  「実装しない」を選択肢として残す。**

## 並列分割方針

実装単位は最大でも1つ (s8c_result_judge.py + test_s8c_result_judge.py のペア)。段2で規模が
これを超えると判明したら規律5に従いさらに絞る。

## DW-G05 (成果物影響)

項目6を実装しない場合、公式性能表の各観測が「連続測定」「復旧後の時間差測定」
「意図的な過去比較」のいずれかを区別されないまま扱われ続け、D510 が要求する主張強度の
差別化 (§10.4) が judge 層で表現できない。ただし現状は §10.6 の epoch 境界により正式系列
自体が未起動のため、この欠落は当面 H1/H2 の正式 admission を追加でブロックしない
(既に C01/C02/C03等の他条件が未充足のため)。**このため項目6の実装しないという裁定も
正当な選択肢である** (規律5、DW-G02 「初回cycle前hardening限定」)。

## 受入・実測環境

- 受入全走は `tools/dev_wave_wait.py acceptance` 経由、Pegasus dispatch。
- 変異事前登録は段4で、実装する場合のみ (paired-diff 判定式・型検証の受理/拒否境界を対象)。

## 段2 codex plan 実績

独立に (P1) を再確認し、D510 項目1〜4 実装済み・項目5 部分実装 (P2対象外)・項目6
(測定近接性ラベル) 欠落、項目7 fail-closed 成立、と判定。項目6の最小実装案
(`_ObservationProvenance` 追加・`_build_observation_context` 拡張・`_evaluate_contrast` への
diagnostics 接続・(c) は INDETERMINATE 化) を file:line 粒度で提示。3表・producer には
触れない設計。分割候補4件を提示し「1+2 (provenance検証+ラベル導出) を同一実装単位、
3 (3表出力)・4 (producer) は延期」を推奨。

## 段3 敵対相談2レンズの実績

**レンズ sol (正しさ境界)**: real 4件 — (a) `_ObservationProvenance` 必須化が
`judge()` の旧形式入力の受理結果を変え、brief 不変条件「既存受理集合を変更しない」と矛盾。
(b) 時間差・近接性ラベルが diagnostics 止まりで `_table_bytes`/`publish_result_table`
に届かず公開成果物へ出ない。(c) 「3表への影響はない」は誤り — (c)ラベル観測は
`official_conclusion`/status を INDETERMINATE 化し3表の内容 bytes を変える。
(d) **`relation_kind` が既存 raw-value attestation (SHA/issuer) に束縛されず自己申告可能** —
caller が `recovered_gap`/意図的過去比較の観測を `continuous` と偽装でき、最強の主張ラベルを
偽装できる (規律2隣接の脆弱性)。unclear 2件 ((c)の扱い、(b)のidentity一致要求の厳格さ) は
ユーザー裁定事項として記録に留める。

**レンズ luna (整合・実効性・所有範囲)**: (P1) は独立確認で正しい (別のjudge/registry
見落としなし)。ただし brief の `s8c_result_judge.py` 行数記載「777行」は誤り
(実際1512行、`s8b_oracle_judge.py`の777行と取り違えた引用ミス)。**決定的所見: `judge()`
関数 (1012-1070行) には現在 production caller が存在せず、参照はテストと静的 AST evaluator
(`s8c_preregistration_evidence.py:2776-2803`) に限られる。DW-G04 (発火gate) の
「発火条件を満たす既存 artifact path」要件が不成立。** 段2プラン自身が producer 不在を
認めながら実装を推奨しており、DW-G04と整合しない。項目7の epoch 境界により正式系列は
既に fail-closed のため、項目6を今追加しても実害防止効果はなく「将来 producer への予防的
契約強化」に留まる。**明確な推奨: 実装しない。** C02 (t1472-c02-arm-noninterference 想定
scope) との直接ソース衝突は低い (`_evaluate_contrast` は非干渉性 digest を読まない) が、
将来 C02 producer が judge に接続する際の入力契約統合方針が未定義であり、今 private schema
を作ると将来作り直しのリスクがある。

## 段4 裁定 (親)

**裁定: 実装しない (`4→7→8→9`)。**

**採用した所見**: レンズ sol の(a)(b)(c)(d) 4件すべて real として採用 — これらは「項目6を
今実装する場合、brief の不変条件違反・公開成果物への不到達・規律2隣接の自己申告脆弱性という
複数の是正必須欠陥を抱える」ことを示す。レンズ luna の DW-G04 不成立・producer/judge接続なし・
推奨実装しない、を採用 — これが最も決定的な理由。line数引用ミス (777→1512) は本記録で訂正する。
C02将来統合コスト未定義の指摘も採用し、次wave起票時の前提条件に含める。

**不採用/scope外とした所見**: sol の unclear 2件 ((c)診断記録可否、(b)identity一致の厳格さ)
は「実装しない」裁定により発火しないため、次に項目6へ着手するwaveへの申し送り事項として
記録するに留め、本waveでは裁定しない (ユーザー裁定が要る論点として保留)。

**裁定の理由 (規律5・DW-G02・DW-G04 すべてが「実装しない」を支持)**:
1. (P1) 前提修正は確定: command 引数が指定した `between_run_floor.py` 等は D510 judge と
   無関係。D510 の judge (`s8c_result_judge.py`, T-1352)・3表・attempt registry
   (`trial_registry.py`, T-325/T-1310/T-1337) は既に実装済み。
2. 唯一の未実装項目 (項目6) は、DW-G04 の発火gate要件 (既存 artifact path) を満たさない —
   `judge()` に production caller が存在しない。
3. 項目6の最小実装案自体にも是正必須の設計欠陥がある (自己申告可能な relation_kind、
   3表内容への意図しない byte変化、brief不変条件との矛盾)。
4. 項目7 (仕様のみ発効) は `SATISFIABLE_CONDITION_IDS` 空集合により既に構造的 fail-closed。
   項目6を今追加しても実害防止効果はない。
5. t1472-c02-arm-noninterference (項目5) との将来統合コストが未定義。今 private schema を
   作ると将来の producer 配線waveで作り直しになるリスクがある。

**裁定パッケージ (ユーザーへ返す推奨、次の一手)**:
- D510 の judge・3表・attempt registry は既に T-325/T-1310/T-1311/T-1337/T-1352 で実装済み
  という事実を周知する (command 起票時の認識とのずれ)。
- 項目6 (測定近接性ラベル) を実装する将来waveの前提条件: (a) provenance
  (timestamp・環境/実装/toolchain identity・関係区分) を生成し `judge()` へ渡す production
  producer の新設、(b) `relation_kind` を raw-value attestation と同じ信頼境界 (署名/registry
  束縛) に載せる設計、(c) t1472-c02-arm-noninterference (項目5) の完了を待ち、C02の
  registry-slot/digest 参照と provenance schema の統合方針を先に決める、(d) 近接性ラベル・
  時間差を3表 (`_table_bytes`/`publish_result_table`) へどう反映するかの明示設計。
- これらが揃うまで項目6は着手しないことを推奨する。

**変異事前登録**: 実装差分ゼロのため対象なし (DW-S04)。

**DW-G05 (成果物影響、実装しない場合)**: 公式性能表は測定近接性を区別しないままだが、
項目7の fail-closed gate により正式系列自体が起動できないため、当面の実害はない
(規律5・DW-G02 に照らし正当な見送り)。
