# [T-2743] B-2 delta_min の接続確認 — 事前登録の holdout 別パラメータと判定器の対比パラメータは現行 main で未接続 (既裁定 D1481 / D1326 の状態のまま。新しい裁定は不要)

authority: none / default_effect: no-state-change (read-only 確認の記録。可変状態の正本は worklog 末尾と現行 phase doc)

- wave branch: `worktree-dev-wave-b2-delta-min-connection`
- 基準 commit: `b4631a92e` (local main、entry 1596 の fold。wave 開始時は `abc7085ae` で、本文が引く code / docs はどちらの commit でも同じ bytes。**本文の行番号はすべて `b4631a92e` の現物**)
- 起点: D2104 (第 20 回 /rulings 全件、2026-09-17) 項 12 (a) 「事前登録の holdout 別パラメータと判定器の対比パラメータの接続確認は、検査を足さずに現物で行う (AI 手番)」= T-2743。同 (b) 「参照 artifact の照合の新設は採らない」は本 wave が守る境界
- 正本: D2049 (保持群ラベルの訂正 H1 = rr80 / H2 = rr20) と worklog entry 1533 (`docs/archive/worklog-phase3-0916-1533.md`) の裁定パッケージ
- 実装面の差分: **ゼロ** (本 wave は insight と worklog fragment だけ)。凍結側・判定器・事前登録の bytes は 1 byte も変えていない
- job dir (prompt・log・receipt・受入 receipt の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b2-delta-min-connection/` (wave 中の作業 dir `~/.claude/jobs/7ac023ae/tmp/dev-wave-b2-delta-min-connection/` の複製を段 9 後に置く。子成果物の逐語は本 dir の `verbatim/`)

## 問いと結論

**問い:** D1640 / D2049 が定める「holdout ごとに `delta_min = 0.03 × R_h`、H1 = rr80、H2 = rr20」という値は、判定器
`orchestrator/campaign/s8c_result_judge.py` の対比パラメータへ現物で届くか。D2049 は「判定器が受け取る対比パラメータは
現状 1 組で、holdout ごとに別の `delta_min` を渡す接続は確認していない」と書いて残件にしていた。

**結論:** 現行ソースでは、事前登録 §5 が H1 / H2 別の対比パラメータ block を要求する一方、`judge()` は holdout 軸のない
対比パラメータ object を 1 組だけ受け取り、formal・generation の両経路で比較に到達した各 holdout に**同じ `delta_min` と
`sd_max`** を適用する。後述の静的探索範囲では、§5 の登録値を判定器の object へ変換して `judge()` へ渡す production
接続は見つからず、`judge()` 自体に production の呼び手が無い (D649 のまま)。
**所見の型は「holdout 別値の未接続」である。** H1 に rr20 の値が渡る逆割当も、それによる誤受理も確認していない
(§5 は未記入、C07 は充足を許されず、本 wave は測定を投入していない)。単一値を将来接続しても D1640 / D2049 とは一般に
同値にならない (後述の設計メモ)。

**この状態は既裁定が既に把握し、設計の方向と着手順を確定している。** 分断の事実は worklog entry 1147 (T-1875、2026-09-01)
と T-1874 の裁定パッケージが記録し、**D1481 (2026-09-02、ユーザー裁定) が「判定側を holdout 別へ広げる。読み取り側を
単一値へ寄せる案は採らない」と設計の方向を確定**、**D1326 (2026-09-01) が着手を完了証明層の着地後**と定めている。
本 wave の確認はこれらを覆す新事実を出していない。**よって本 wave から新しく裁定へ返す事項は無い。**
項 12 (b) の照合 gate は不採用のまま変更なし。

## 本 wave の純増 (何が新しいか)

1. 現行 main での file:line 確認。先行の記録 (T-1874 の README、entry 1147) は行番号の drift を自ら注記しており、D2049 は
   「確認していない」と書いていた。本 wave がその確認を現物で閉じる。
2. H1 / H2 という**ラベルが各層のどこで workload (rr80 / rr20) に束縛されるか**の 2 本の鎖 (次々節)。D2049 の訂正が D1481 の
   実装後にどこで効き、どこが機械照合されないか (= 項 12 (b) が新設を却下した照合の位置) を示す。
3. D1481 の実装 wave が扱うことになる副次項目の列挙 (裁定不要の設計メモ)。
4. 参考: 8b §10.2 / 8c §4 の現状説明のうち部分的に古い 1 文 (本 wave では直さない)。

## 対応表 (現行 main の現物)

Python file は特記しない限り `orchestrator/campaign/` 配下。

| # | 主体 | 現物 file:line | 読み |
|---|---|---|---|
| 1 | 判定器 params の型 | `s8c_result_judge.py:129-143` `_ContrastParams(n, delta_min, sd_max, unit, direction, source_binding)` (frozen dataclass、docstring「The only parameter object accepted by `judge`」) | **1 組。holdout 軸を持たない** |
| 2 | 判定器 params の検証 | `:293-314` `_validate_contrast_params` — exact type、`n` は int ≥ 2、`delta_min` 有限・正、`sd_max` 有限・非負、`unit == "throughput_tps"` (`:44`)、`direction == "on_minus_off"` (`:45`)、`source_binding` 非空 | 単位・向きを定数と照合する主体は判定器 (D2049 の「照合するのは判定器の側」と一致) |
| 3 | formal 経路の適用 | `:1978` で検証 → `:2010-2012` で `_evaluate_contrast` へ → `:1434` `for holdout_id in holdouts:` → `:1550` `mean_delta > float(params.delta_min) and sample_sd <= float(params.sd_max)` | **H1 と H2 に同じ `delta_min` / `sd_max`** |
| 4 | generation 経路の適用 | `:1973-1975` で検証・分岐 → `_judge_generation` (`:1748`) → `:1900-1907` で同じ `_evaluate_contrast` へ | formal と同じ 1 組を渡す |
| 5 | 判定器の holdout の知識 | formal: `:353,379-384` manifest の cells から `holdout_id` を集め、**異なる文字列ラベルがちょうど 2 つ** × 3 arm を要求 (`:344-345` 6 cell、`:361-366` 重複拒否)。generation: `:665-690` で `holdout_id` と `workload` 文字列を受け、`:893-900` で観測 record の `workload` / `holdout` / `arm` と**manifest 内の文字列**を照合 | ラベルは manifest 由来。**判定器は rr80 / rr20 と H1 / H2 の正規対応を持たない**。判定器だけでは「同一 workload の別名 2 ラベル」を排除しない (それを塞ぐのは registry 側: `trial_registry.py:780-781,795-799` が manifest の **trials** の holdout を閉集合 H1/H2 と直積で検査し、`:1672-1688` が各 runtime report の cell の workload を凍結束縛と照合する) |
| 6 | 判定器の反復数 | `:388-392` `_validate_complete_block(manifest, cells, n)` は manifest に `n` があれば `params.n` との一致を要求し、`:400-442` で全 cell の反復集合を共通 `n` で検査する。`:1880-1882` (generation) と `:1992` (formal) が `params.n` を渡す | **`n` も 1 組**。holdout 別の `n` を受けない (D2071 と整合) |
| 7 | 判定器の `source_binding` | `:1626-1628` manifest の `source_binding` と `params.source_binding` の**文字列一致**のみ | §5 の値や参照 artifact を読み戻す接続ではない |
| 8 | 事前登録の欄名 | `s8c_preregistration.py:135-137` `SECTION5_ITERATION_CONTRAST_FIELD` = 「反復単位対比の判定パラメータ (H1 / H2: n・平均差の下限・差の標本 SD の上限)」 | 欄名が holdout 別を宣言 |
| 9 | 事前登録の validator | `:891-961` `_validate_iteration_contrast_parameters` — root keys は exact `{"H1","H2"}` (`:909,915`)、各 block は exact `{delta_min, direction, n, sd_max, unit}` (`:910,925`)、`n` int ≥ 2 (`:931-935`)、`delta_min` 有限・正 (`:936-943`)、`sd_max` 有限・非負 (`:944-951`)、`unit` / `direction` は非空文字列 (`:952-961`)。呼び出しは記入済み欄に対して `:835-837`。結果は `contract.section5_value_violations` (`:212,1062`) | **holdout 別 block。値の割り当て (どの `R_h` から算出したか)・係数 0.03・測定条件・H1/H2 間の関係は見ない**。単位・向きの定数一致も見ない (D2049 と一致) |
| 10 | 事前登録の現物 | `docs/phase3-8c-preregistration.md:208` 欄は「未記入」。`:176-180` 記入は 8b §10.2 の解除条件成立まで禁止。`:248-256` §6 条件 7 は「H1 / H2 について §5 に記入 + 完全 block + judge と 3 表 + validator の production 到達」 | 値は未記入。条件 7 は未充足 = 未発効 (契約どおり) |
| 11 | 充足許可集合 | `s8c_preregistration_evidence.py:3336` `SATISFIABLE_CONDITION_IDS = frozenset({"C10"})`、許可外の SATISFIED は `:3446-3453` で ERROR。C07 (judge consumer) は `:3037-3078` の静的 AST 検査で、judge を import も実行もしない | C07 は充足を許されない。D649 の「gate 閉」が現行でも維持。ただし `judge()` 自身は C07 の発効状態を照会しない (`:1959-2013`) ので、gate 閉は「関数が SATISFIED を返せない」証明ではない |
| 12 | §5 → 判定器の橋 | `_ContrastParams(` の生成元は `orchestrator/tests/test_s8c_result_judge.py:104,573` のみ。`SECTION5_ITERATION_CONTRAST_FIELD` の production 出現は `s8c_preregistration.py:135,903,968` (定義・違反報告の欄名・validator 登録) のみ。`s8c_result_judge` の production import は 0 件 (検索範囲は「再現手順」) | **§5 の H1/H2 block を判定器の object へ変換する経路も、`judge()` の production 呼び手も、探索範囲では見つからない** |
| 13 | 凍結側の権威 | `s8b_holdout_freeze.py:101-104` `HOLDOUTS = {"rr80": H1, "rr20": H2}`、`trial_registry.py:83-107` `HOLDOUT_BINDINGS` は同 dict から導出 (`H1 → workload rr80`)、`:780-781,795-801` manifest の trials は H1/H2 × 3 arm かつ全 trial で `n` が同一、`:1672-1688` runtime report の cell は trial の holdout から引いた凍結 workload と一致、`output/s8b-freeze/holdout_freeze.json` は rr80 → `candidate_id: H1` / rr20 → `H2`、`docs/phase3-8b-descriptor-design.md:115-116` の表も同じ | D2049 の訂正どおり。本 wave で触らない |
| 14 | D1640 の逐語 | `docs/decisions.md:50294-50310` 「H1 = rr20、H2 = rr80」のまま。D2049 (`:62723-62786`) が追補で訂正し遡及改変しない | 規律 7 どおり |

## ラベルの束縛 — 2 本の鎖が文字列 "H1" / "H2" で出会う

**鎖 A (権威の導出、実在する):** 凍結 producer → registry。judge はこの鎖を呼ばない。

```
s8b_holdout_freeze.HOLDOUTS (:101-104)  rr80 → candidate_id "H1"、rr20 → "H2"     ← 凍結の権威 (成果物 holdout_freeze.json も同じ)
  ▼ 導出 (trial_registry.py:83-107)
trial_registry.HOLDOUT_BINDINGS  "H1" → workload rr80、"H2" → rr20
  ▼ 検査 (trial_registry.py:780-781,795-799 / 1672-1688)
manifest の trials は閉集合 H1/H2 × on/off/swapped の直積、各 runtime report の cell の workload は trial の holdout から引いた凍結束縛と一致
```

**鎖 B (値の適用、空隙がある):** §5 → [空隙] → judge params → judge の holdout ループ → manifest の cells。

```
§5 の root key "H1" / "H2" の block            ← 人間/AI が値を記入する (D1640: その holdout 自身の R_h × 0.03)
  │  validator (:891-961) は型・有限性・符号・非空だけを見る。**どの R_h から算出したかは見ない**
  ▼
[空隙] §5 → judge params の変換と production 呼び手 (未実装。D1481 が「判定側を holdout 別へ広げる」方向を確定、D1326 で着手は完了証明層の後)
  ▼
judge params (現行は holdout 軸なし 1 組。D1481 の実装後は "H1" / "H2" ごとの値)
  ▼
judge の holdout ループ (:1434) は manifest の cells の holdout_id (正規の manifest なら文字列 "H1" / "H2"。judge 自体は異なる 2 文字列しか要求しない) で引く
```

- 2 本の鎖は文字列 "H1" / "H2" でだけ結ばれる。judge は鎖 A を呼ばず (`:342-385,641-691` は manifest の文字列だけを見る)、
  鎖 A は §5 の値を見ない。
- **D2049 の訂正 (H1 = rr80) が効く場所は鎖 B の先頭、§5 に値を記入する手番だけである。** 鎖 A は凍結から機械的に
  導出されるので、registry の導出・検査範囲では下流で逆転が起きる余地は無い。
- **機械照合されないのは鎖 B の先頭の 1 段 (「"H1" の値は rr80 の R_h から算出したか」)** である。これが D2049 の「どちらの主体も、
  各値が指定された holdout の stock 参照から算出されたことは照合しない」であり、項 12 (b) が新設を却下した照合の位置である。
  F965 の再発検知が目視 (段 1 で凍結 producer と逐語照合) のままなのはこのため。
- 現行では空隙の段で鎖 B が切れているので、先頭の記入も (8b §10.2・8c §4 により) 禁止されたままである。
- 将来、呼び手が H1 の値だけを 1 組の `delta_min` に入れて両 holdout に適用する形で接続すれば、それは「未接続」でも
  「逆接続」でもなく「H1 由来値の共通適用」であり、H2 自身の参照を使う D2049 の契約に反する。D1481 はこの形を却下している。

## 既存被覆との関係 (何が既知で、本 wave が何を足したか)

| 既存の記録 | 何を言っているか | 本 wave との関係 |
|---|---|---|
| worklog entry 1147 (T-1875、2026-09-01) 停止理由 3 | 「§5 parser は H1/H2 の 2 根 key、judge は単一の `_ContrastParams` を 6 cell 全体へ適用。H 別の値を渡す経路が無い。この欠陥は T-1874 の完了条件に属する」 | 分断の事実は既知。本 wave は現行 main での file:line 確認を足した |
| T-1874 裁定パッケージ (`output/insights/2026-08-28/t1874-s8c-section5-consumer/README.md`) 質問 2 | 「`_ContrastParams` の holdout 別 mapping 化と、§5 で両 holdout 同値を要求する規範変更のどちらを採るか」 | D1481 が前者の方向を採り後者を却下 (下記) |
| D1481 (2026-09-02、ユーザー裁定) 決定 2 | 「判定パラメータの分断は、判定側を holdout 別へ広げる方向で確定する。読み取り側を単一値へ寄せる案は採らない。確定するのは設計択だけであり、実装の着手は D1326 のとおり」 | **設計の方向は裁定済み。本 wave は再提示しない**。D1481 は方向を確定したのであって `_ContrastParams` の具体的な改変方法までは指定していない |
| D1326 (2026-09-01、ユーザー裁定) | 「§5 値 gate の結線は完了証明層 (D1026) の実装後に着手する。4 点 (report producer の解釈、holdout 別 params、性能行と生値の発行者、出力先と受領証の束縛) は相互依存」 | 着手順は裁定済み。T-1875 の carry (2026-09-14 実測) では完了証明層 12 条件中の充足は C10 の 1 件 |
| T-1875 insight (`output/insights/2026-09-14_t1875-delta-min-gate/README.md`) 前提 2 | §10.2 の検証 consumer (`_validate_iteration_contrast_parameters`) が production の parse 経路から到達し、負例 6 件が別々の理由コードで発火する (実測) | validator の実在と発火は既知。本 wave は validator が**見ないもの**を対応表 9 行目で明示した |
| D2049 (2026-09-16) 「主張しないこと」 | 「判定器が受け取る対比パラメータは現状 1 組で、holdout ごとに別の `delta_min` を渡す接続は確認していない」 | **本 wave が確認を閉じた: 接続は無い (未接続型)** |
| D649 (2026-08-22) | `judge()` に production caller が無く gate は閉じたまま | 現行でも維持 (対応表 11・12 行目) |
| D2104 項 12 (2026-09-17) | (a) 接続確認は検査を足さず現物で (= T-2743)、(b) 参照 artifact の照合は新設しない | (a) を本 wave で閉じる。(b) は変更なし |
| D2071 (2026-09-16) / T-1957 insight (`output/insights/2026-09-16/t1957-manifest-replicates/README.md` §2.1) | 「8c trial manifest の `n` は 6 cell すべてで同一。holdout ごとに異なる `n` は受理しない」。§5 が `n` を H1 / H2 の 2 欄で持つのは記入の単位であって許可ではない | 設計メモの `n` はこの裁定のまま (後続 wave の設計択に戻さない)。段 6 レビュー B が親の初稿の誤りを指摘し訂正した |
| T-1874 README「拒否された近道」 | 「H1/H2 が同値だと未裁定のまま仮定する」「judge を 2 回呼び private `_JudgeResult` を独自合成する」を再提案しない | 段 2 plan と段 3 が挙げた「完全 manifest を異なる params で二重評価して部分結果を再集約する」代替は、この近道と同型であり本 wave は候補にしない (判定器がそれを禁じていない、という事実の記録に留める) |

## 裁定へ返す事項

**無し。** 理由: (i) 接続の設計の方向は D1481 で確定済み、(ii) 着手順は D1326 で確定済み、(iii) 参照 artifact の照合 gate は
D2104 項 12 (b) で不採用、(iv) 本 wave の確認は上記を覆す新事実 (例: 既に接続が実装されていた、逆割当が実在した、docs が
「judge は holdout 別を受ける」と誤記していた) を出していない。8c §6 条件 7 の文言 (「H1 / H2 について §5 に記入」+ judge)
は D1481 の方向と整合しており、条件 7 が未充足なのは D649 が確定した gate 閉の一形態である。

T-2743 (項 12 (a) の確認手番) を閉じる条件は、(1) 対象 commit と探索範囲、(2) 登録形状・受口・適用先・接続探索の対応表、
(3) 「未接続」とその限界、(4) D1481 / D1326 への後続の引き継ぎ、(5) (b) は不採用で変更なし、の記録であり、接続の実装は
求められていない。本文書がその 5 点を持つ。

## D1481 の実装 wave が扱う副次項目 (裁定不要の設計メモ。本 wave は実装しない — DW-G04)

- `delta_min` だけでなく **`sd_max` / `unit` / `direction` / `n` も §5 では holdout 別 block** にある。このうち **`n` は D2071
  (2026-09-16) が「6 cell すべてで同一。holdout ごとに異なる `n` は受理しない」と確定済み**で、§5 の H1 / H2 欄は記入の単位であって
  両者が異なってよい許可ではない (割れたときは狭い側へ倒す)。判定器の 1 組の `n` (`:388-392`、manifest に `n` があれば一致を要求)
  と `trial_registry` (`:800-801` 全 trial で `n` 同一) はこの裁定と整合している。holdout 別 mapping 化は **D2071 の全 cell 共通
  `n` を維持したまま**、`delta_min` / `sd_max` / `unit` / `direction` を holdout 別に受ける形で結線する。`n` を holdout 別に
  許す案は却下済みで、後続 wave の設計択ではない。
- `unit` / `direction` は判定器の定数 (`:44-45`) と照合される。holdout 別 block の各値がともに定数と一致することを
  `_validate_contrast_params` 相当で検査する形になる。
- `source_binding` (`:1626-1628`) は文字列一致のみ。§5 の発効 digest との束縛は T-1874 の 4 点 (D1326) に含まれ、「fresh 発効
  digest から両方を生成する」近道は拒否済み。
- 単一値への集約が D1640 と同値でない理由 (条件付き導出、実測ではない): H1 / H2 の境界を `d1 < d2` とし共通値を `d1` にすると、
  H2 について `d1 < mean_delta ≤ d2` の範囲が新たに `:1550` の閾値条件を通る。他条件を固定すれば受理集合を広げうる。
  逆に共通値を `d2` にすると H1 側が狭まる。どちらも D1640 の「その holdout 自身の `R_h`」と一般には一致しない。
- 登録値の取得箇所は現状 `s8c_preregistration.py:835-837` (validator の呼び出し) だが、将来の呼び手の設置先が確定したわけではない。

## 参考 — docs の現状説明のうち部分的に古い 1 文 (本 wave では直さない)

8b §10.2 (`docs/phase3-8b-descriptor-design.md:476-478`) と 8c §4 (`docs/phase3-8c-preregistration.md:178-180`) は「この制約の
現在の担保は『欄が空であること』だけである。8c の発効判定は欄が記入済みかどうかしか見ず、値の型・単位・範囲は検証しない」と書く。

- 「発効判定は値を検証しない」は現行でも正しい: 発効の連言 `effective = validation ∧ decider_version ∧ all_filled ∧ all_satisfied`
  (`s8c_preregistration.py:2061-2065`) は `section5_value_violations` を含まない。違反の消費者は test だけ
  (`orchestrator/tests/test_s8c_preregistration_core.py`、`test_s8c_preregistration_invariant.py:674` の living doc invariant)。
- 「担保は欄が空であることだけ」は部分的に古い: validator (`:891-961`) と living doc の invariant test が実在し、不正な値を
  記入すれば test が赤になる。ただし発効判定そのものは値を見ないので、「検証されない値で発効を通す」という警告の実体は残る。
- 訂正は 8b / 8c 各文書の改訂契約 (§8 再凍結・§11 改訂) に従う別 wave の担当。T-1875 insight の「既存 docs の陳腐化 1 件 (参考)」と同じ扱い。

## 再現手順 (検索範囲を含む)

worktree root (`b4631a92e`) で、submodule `external/` を除く tracked file を対象に:

```bash
git grep -n "_ContrastParams" -- ':!external'
#   → 生成 (call) は orchestrator/tests/test_s8c_result_judge.py:104,573 のみ。他は判定器自身の定義・注釈・型検査 (s8c_result_judge.py)、
#     同 test file の型注釈、docs/archive と output/insights の記述
git grep -ln "s8c_result_judge" -- ':!external' ':!docs' ':!output' ':!orchestrator/tests'
#   → orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json のみ (C07 の静的検査対象 path、import ではない)
git grep -ln "SECTION5_ITERATION_CONTRAST_FIELD" -- ':!external'
#   → orchestrator/campaign/s8c_preregistration.py、orchestrator/tests/test_s8c_preregistration_invariant.py、output/insights の 1 件
git grep -n "\.judge(\|\bjudge(" -- 'orchestrator/*.py' 'tools/*.py' ':!orchestrator/tests'
#   → 呼び出しは b10_backoff_shape_sweep.py:4014 (同 file :2174 の別 judge) と tools/pegasus/probes/t316_sandbox_backend_probe.py:2628
#     (sandbox verdict 関数) の 2 件、他は `def judge` の定義 2 件。s8c_result_judge.judge の呼び手は 0 件
git grep -n "section5_value_violations" -- ':!external' ':!output' ':!docs'
#   → s8c_preregistration.py:212,1062 (定義・構築)、test 2 file (test_s8c_preregistration_core.py、test_s8c_preregistration_invariant.py)、
#     acceptance_duration_ledger.json の test 名のみ。発効判定 (:2061-2065) には現れない
```

段 2 plan 子は `rg -n --hidden -g '*.py' -g '!.git' -g '!**/tests/**' -g '!**/test_*.py' 's8c_result_judge|_ContrastParams|\bjudge\s*\(|SECTION5_ITERATION_CONTRAST_FIELD' .` で、
段 3 の 2 本も root 全体の hidden を含む検索で、独立に同じ結果を得た。

## 限界 (主張しないこと)

- 静的検索の結論である。ignore 対象・動的に生成されるコード・repo 外の呼び手まで不存在を証明したものではない。
- 「誤受理の実証」ではない。C07 は充足を許されず (対応表 11)、§5 は未記入 (対応表 10)、本 wave は参照測定も判定も走らせていない。
  測定履歴全体について「起きていない」と断定するものでもない。
- 本 wave は値の記入・参照測定の投入・接続の実装・照合 gate の新設のいずれも認可しない。

## 段 2・3・4・6 の子成果物と工数

- `verbatim/s1-brief.md` (親 brief。06:53 JST の追補で P2 の「裁定事項」を D1481 既裁定へ訂正)
- `verbatim/s2-plan.md` (read-only plan、独立導出。親表の行番号 3 件を補正: `:1434`、`:129-143`、`:903`)
- `verbatim/s3-consult-sol.md` (正しさ境界) / `verbatim/s3-consult-luna.md` (整合・実効性)
- `verbatim/s4-ruling.md` (段 4 裁定: 採用事項の一覧、末尾に段 6 所見の閉包表と焦点再レビューの判定)
- `verbatim/s6-review-a.md` (正しさ境界: must-fix 0 / nit 3 / GO)、`verbatim/s6-review-b.md` (整合・fragment: must-fix 1 (D2071) / nit 2 / NO-GO → 親が修正)、
  `verbatim/s6-focus-1.md` (焦点再レビュー: closed 4 / partial 2 / regressed 0、段 7 へ GO)
- 工数 (receipt 実測、`artifacts/dev-wave-b2-delta-min-connection/*/receipt.json`): codex 子 6 本、全段 `gpt-6-astra` / `medium`、
  計 43 call / 2,078,623 token / 992 秒 — plan 9 call / 441,343 / 301 秒、consult sol 8 / 419,058 / 190 秒、consult luna 8 / 377,444 / 188 秒、
  review A 7 / 336,137 / 117 秒、review B 7 / 372,911 / 109 秒、focus 4 / 131,730 / 88 秒。
- 受入全走: 記録 commit を含む最終 tip に対して 1 回投入。結果の正本は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-b2-delta-min-connection/`
  の `acceptance-receipt-*.json` と land 結果 JSON (本文書は tested tip に含まれるため結果を持たない)。
