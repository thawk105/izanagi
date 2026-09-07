# [T-2265] 反実仮想 ITT — seq 0 の位置除外を結果より先に凍結し、既存 12 成果物を再解析した

2026-09-08。branch `worktree-dev-wave-t2265-itt-seq0`。base main `c5754d1f4`。
前 wave の一次資料は `output/insights/2026-09-07_t2265-backoff-itt/README.md`。
**再測定はしていない。計算ノードへ 1 件も投入していない。**

## 0. この wave が主張すること・しないこと

**主張する:**

1. **除外規則を、改訂後の推定値を計算する前に凍結した。** 事前登録 v2
   (`docs/backoff-counterfactual-preregistration.md`、bytes の sha256
   `526d9384d8a8c62f82b132c41672aa2eff32722788ad06858c09f80185ca495a`) を
   commit `1c977a218` (docs のみ) で固定し、その**後で**解析器を合わせ (`1c482bf6f`)、
   その**後で**解析した。§1 に順序と、その順序が証明できる範囲の限界を書く。
2. **既存 12 成果物をそのまま解析した。** 新しい `analysis-result.json` の
   `inputs[].sha256` は、前 wave の同 field と **12 件すべて一致する**。bytes は 1 件も動いていない。
3. **主判定は `inconclusive` である。** これは事前登録した規則が発火した結果であり、規則どおりの
   帰結である (§3)。
4. **副次の 5 層 (workload x threads) は v2 で判定可能になった。** v1 ではこの 5 層も判定不能だった。
   ただしこれらは事前登録が「探索的な記述であり主判定を置き換えない」と定めた層である (§4)。

**主張しない:**

- **腕の効果の有無を主張しない。** 主判定は判定不能であり、等価とも、推奨方向が優越とも、
  反転方向が優越とも言えない。
- **本書 v2 を「完全に前向きな事前登録」と呼ばない。** 除外規則は v1 の主判定 `inconclusive` と
  欠測の内訳を**見た後に**選んでいる。名乗れるのは「outcome を部分的に開示した後に、改訂後の
  推定値を計算する前に凍結した、事前指定の再解析計画」までである。独立な前向き確認試験と
  同格に扱ってはならない (§5)。
- **性能結果ではない。** 測定は trace 有効 build の診断であり、絶対規律 1 に従い throughput の
  性能主張に使わない。
- **policy≠0 の cell は未認証である。** 正しさは主張していない。

## 1. 凍結の順序と、その証拠の限界

| # | commit | 内容 |
| --- | --- | --- |
| 1 | `1c977a2182fc93b7cb38a5f17e956c6df84c6371` | 事前登録 v2 の凍結 (**docs のみ**) |
| 2 | `1c482bf6f5ce6a16442131a89758aa146408f3e5` | 解析器を v2 へ |
| 3 | `3ad18303295a06f2c7014db843583e7c1873a1c8` | 副題 (`not_certified` 文言と行番号 pin) |
| 4 | `3f5edb7c70689bf20b5cdc25472b0edcda75dc73` | 変異が帰属する fixture へ作り直し |

解析はこの 4 commit がすべて存在した後に 1 回だけ実行した。

**証拠として言えること:**

- v2 文書の blob が解析器 commit と結果 commit の祖先にある。
- 解析器は v2 の sha256 を module 定数として pin し、渡された文書の実 sha と exact 比較する。
  結果 JSON の `preregistration.sha256` は `526d9384…` である。
- 12 成果物の bytes が前 wave から 1 件も動いていない (`inputs[].sha256` の全一致)。

**証拠として言えないこと:**

- **「別経路で先に v2 の推定値を計算していない」ことは証明できない。** commit の順序は内容の
  祖先関係を示すが、未計算の証明にはならない。前 wave が「`seq = 0` を除いた推定値は計算していない」
  と main へ着地させている (worklog entry 1328、前 insight §3) のは**証言**であって暗号学的証明ではない。
- remote への公開時刻で強めることはできるが、本 project は AI から push しないため採っていない。

## 2. 何を実装したか

| 変更 | 中身 |
| --- | --- |
| 事前登録 v2 | §7 に位置除外を 1 つ追加。§4 の添字域を `i = 1, ..., m_r - 2` へ。§5 に検出力表の限定、§6 に時間 block の基準、§9 に sha の 2 分割と cohort 限定を追記 |
| 位置除外 | `_run_difference` が `analysis_events = events[1:]` から対・index・件数を組み直す。層別 membership の index も残存集合基準。`assignment_rate_all_events` は生の全 event のまま |
| 0 commit 判定 | 検査範囲を残存 event へ限定。**残存に 0 が 1 件でもあれば主判定全体を inconclusive にする規則は v1 から変えていない** |
| 事前登録 sha | 2 定数へ分割。成果物が記録しているべき値は **v1** (測定時点の事実、絶対規律 7)、渡された文書に要求する値は **v2** (解析規則の正本)。どちらも任意値を受理しない |
| version | `ANALYSIS_VERSION` を v2 へ。docstring に cohort 限定を明記 |
| 副題 | 診断成果物の `not_certified` を trace 有効の実態に合わせた。**性能側の文言は 1 byte も変えていない** |

**推定量は v1 と同一ではない。** 位置除外は走り出しの窓 `T[r,0]` だけでなく、最初の割当 `Z[r,0]` の
直接対比 `Y[r,0]` も落とす。v2 の推定対象は「初回更新を除き、後続 event を持つ更新の上で定義した
割当 ITT」である。除外が処置前だと言えるのは、**選択規則 (位置が先頭か) が outcome にも割当にも
依らず全 run から一律に 1 件を落とす**からであって、event 0 に処置が無いからではない。

## 3. 主判定 — 事前登録した規則により、なお inconclusive

解析結果の正本は `analysis-result.json`。

- `analysis_version` = `izanagi-backoff-counterfactual-analysis/v2`
- `preregistration.sha256` = `526d9384…` (v2)
- 主層 (policy 2 / write-heavy / 48 threads) の `cluster_count` = **12** (完備)
- `confirmatory_complete` = **False**、`reasons` = `['window_commits_zero']`、
  `decision` = **`inconclusive`**、`theta_log` = `null`

**前 wave と原因が変わった。** 前 wave は 0 commit event 57 件のうち 55 件が走り出しの `seq = 0` で
発火していた。位置除外でその 55 件は落ちたが、**主層 12 run のうち 1 run**
(seed `13467815584134101060`、binary `99edc30f…`) に `seq >= 1` の 0 commit が残っており、
そこで規則が発火した。残る 11 run は推定値を出している。

**事前登録 v2 §7 は、この事態の扱いを結果より先に定めていた** —「`seq >= 1` の 0 commit を落とす
改訂を、結果を見た後に行わない。v2 の解析で主判定が再び inconclusive になった場合、その結果を
そのまま報告し、同じ 12 成果物について本書を再改訂しない」。**そのとおりにした。**

## 4. 副次 (探索的。主判定を置き換えない)

事前登録 §6 が「すべて探索的な記述であり、主判定を置き換えない。多重比較の補正はしない」と
定めた層である。v1 ではこの 5 層も判定不能だったが、v2 で計算可能になった。

| 層 (policy 2) | `effect_percent` | 95% CI (%) |
| --- | ---: | --- |
| write-heavy 24 | +7.293 | [+5.572, +9.041] |
| balanced 24 | +10.268 | [+7.198, +13.427] |
| balanced 48 | +7.284 | [+6.425, +8.150] |
| read-heavy 24 | +4.242 | [+2.982, +5.517] |
| read-heavy 48 | +6.058 | [+4.131, +8.022] |

**主層を共有する副次 9 層** (`recommended_delta_sign` 3 / `both_actions_feasible` 2 /
時間 block 4) は、主層と同じ理由で判定不能である。解析器は subgroup membership を適用する**前に**
run 全体を 0 commit で scan するため、当該 subgroup がその窓を使わなくてもその run は無効になる。

## 5. この結果から読んではいけないもの

段 6 の敵対レビューが列挙したもので、親が採用した。

- **11 run で集約した推定値を出してはならない。** 事前登録の `theta` は 12 cluster の等重み平均で
  あり、欠落理由は outcome の 0 である。11 run の complete-case 選択は outcome 依存であり、
  12-run の推定対象を別の 11-run の推定対象へ無断で変えることになる。
- **副次 5 層を主判定の代用にしてはならない。** 5 点が全て正でも「効果があった」「主仮説を
  支持した」「6 regime に一般化できる」とは読めない。
- 「等価」「推奨方向が実用優越」「反転方向が実用優越」「効果なし」「検出力不足だから実質ゼロ」は
  いずれも書けない。
- trace 有効な診断系なので、throughput の性能改善、未計装 build への一般化、variant の採用根拠、
  直列性・正しさの証拠のいずれにも使えない。
- **同じ 12 件は完全に開示された。** `analysis-result.json` は 11 run の個別推定値を含む。
  今後この値を見て endpoint・窓・観測長・seed・層を選べば、その計画は data-informed であり、
  同じデータの再利用を独立確認とは呼べない。新規データによる追試は無効にならないが、
  これらを pilot 情報として見た事実の開示が要る。

## 6. 凍結した v2 文書の erratum (**文書は直していない**)

段 6 のレビューが v2 の文面に 4 件の瑕疵を見つけた。**いずれも結果を見た後の指摘なので、
文書を書き換えず erratum として記録する。** 書き換えれば sha256 が変わり、凍結の意味が壊れる。

1. **§0.1 冒頭の「指定した outcome を一度も観測していない時点で §1〜§9 を固定した」は v1 に
   ついてのみ真である。** 同節の項目 4 が v2 について観測済みと明記しているが、冒頭にその限定が
   書かれていない。
2. **§9 冒頭の「本書の bytes の sha256 を記録する」は二通りに読める。** v2 の bytes と読むと
   既存 12 件が全て不適格になる。**適用したのは後段の具体則** — 成果物へ要求するのは v1、
   渡された文書へ要求するのは v2 — であり、実装もそうなっている。
3. **§0 の「outcome の式は不変」は点ごとの式のことである。** 添字域と推定対象は変わっている
   (§4 自身が正しく認めている)。
4. **§1 の「`not_certified` の欠陥は本 wave では直さない」は、本 wave の commit `3ad183032` で
   古くなった。** 診断側の文言は直した。性能側は 1 byte も変えていない。

また、解析器 docstring の「12 件 cohort 専用」は **byte 単位の受理条件ではない。** 正確には
「v1 束縛・§2 の exact な 3 腕・§3 の exact な軸・§8.1 の 12 seed で走った cohort 向け」であり、
同じ契約を満たす合成成果物も受理する (テストがそうしている)。

## 7. 敵対レビューが見つけたもの

段 3 の相談 2 本と段 6 のレビュー 2 本。逐語は `verbatim/`。

- **段 3 (因果推論レンズ) が親の草稿の誤りを 2 件見つけた。** (a) 「推定対象を 1 字も変えていない」は
  誤り — §4 の添字域を書き直さないと文書内で §4 と §7 が食い違い、凍結した推定量が一意にならない。
  (b) 「`seq = 0` の event は処置と無関係」は言い過ぎ — event 0 は最初の割当 `Z[r,0]` を持つ。
  どちらも親が現物で検算して裁定に採用し、凍結前に文書へ反映した。
- **段 3 (実装規律レンズ)** が、成果物が記録している v1 sha と解析規則の v2 sha を同一視したままでは
  12 件すべてが不適格になることを、`_load_artifact` の行を引いて示した。
- **段 6 (実装規律レンズ) が、事前登録した変異 2 件が現 fixture では帰属しないことを実証した。**
  片方 (row pin を v2 固定にする変異) は**生存し、test が緑のままだった**。fixture を作り直した
  (§8)。
- **段 6 (因果推論レンズ)** が §5 と §6 の erratum、および結果の解釈の越権を列挙した。

## 8. 変異検査

probe -> 本走の 2 段。**probe は全件 SURVIVED で登録し、観測 node を集めてから本走で完全集合を
KILLED として登録した** (期待 node の推測を避けるため)。

**解析器側 (10 変異、runner = `test_backoff_counterfactual_analysis.py`)**

- probe (`mutation-probe-spec-a.json` / `mutation-probe-report-a.json`): baseline PASSED、
  **10 件すべてで赤が出た。生存 0。** 観測 node は 35 件。
- 本走 (`mutation-spec-a.json`、sha256 `7fd7a52b…` / `mutation-main-report-a.json`):
  **baseline PASSED、10/10 KILLED、期待 node と完全一致、MISMATCH 0・SURVIVED 0、harness rc=0。**
  repo head `3f5edb7c7`。

**副題側 (2 変異、runner = `test_t2187_adaptive_const_probe.py` + `test_ccbench_spawn_sites.py`)**

- probe (`mutation-probe-spec-b.json` / `mutation-probe-report-b.json`): baseline PASSED、
  2 件とも赤・生存 0。
- 本走 (`mutation-spec-b.json`、sha256 `f35e4f1a…` / `mutation-main-report-b.json`):
  **baseline PASSED、2/2 KILLED、期待 node と完全一致、MISMATCH 0・SURVIVED 0、harness rc=0。**
  repo head `3f5edb7c7`。
  **1 回目の投入は親が走行中に repo へ insight を書いたため untracked 検出で中止した (rc=2)。**
  成果物を repo 外へ退避し、`--out` と `--wrapper-attempt` を変えて再投入した (F106 の再発)。

**合計 12 変異、12 KILLED、生存 0、MISMATCH 0。**

### 8.1 冗長 gate の明記 (DW-M03)

**M6 / M7a / M7b は同じ 8 node で落ちる。** 事前登録 sha を取り違えるとどの経路でも公開 API の
fixture が読めなくなるため、node 集合だけではどの pin が壊れたかを区別できない。
**帰属の決め手は node 集合ではなく、段 6 の fix 子が各 gate を単独で通過させて当てた実測である** —
top pin だけを v2 固定にすると `test_artifacts_remain_bound_to_literal_v1_preregistration_sha` の
top 側 `pytest.raises` が `DID NOT RAISE ValueError` で赤になり、row pin だけを v2 固定にすると
同 test の row 側が同じ形で赤になる。この 2 つは、fixture を作り直す前は**どちらも帰属せず、
row 側は変異が生存していた**。

## 8.1.1 解析の呼出し

解析器は公開 CLI を持たない (offline 専用、公開面は関数 1 本)。その設計を変えないため、親は
repo の外へ置いた 1 回限りの呼出しから公開面を呼んだ。**呼出しの内容は次のとおりで、
実行可能ファイルとしては repo へ入れていない** (実装面は Codex `role=author` が書くという
D95 の境界を親が越えないため)。

```python
from pathlib import Path
from orchestrator.campaign.backoff_counterfactual_analysis import analyze_counterfactual

EVIDENCE = Path("/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt")
paths = sorted(EVIDENCE.glob("stage2-rep0-*.nqsv.json"))   # 12 件
result = analyze_counterfactual(
    list(paths),
    Path("<wave worktree>/docs/backoff-counterfactual-preregistration.md"),
)
```

`PYTHONPATH` は wave worktree、cwd も wave worktree。結果をそのまま `analysis-result.json` へ
書き出した。

## 8.2 受入全走

`tools/dev_wave_wait.py acceptance` 経由。tested main `a916458d8`、tested tip `aa4f601a3`
(local main の post-claim merge を含む)。**verdict `child-green`、child rc=0、
21,612 passed / 68 skipped、赤 0・flake 0。**

main 取り込みでは両親がともに `orchestrator/tests/test_ccbench_spawn_sites.py` を触っている
(main 側は `paper_story_a1_paired.py` の campaign sink を 7146 -> 7209、wave 側は
`t2187_adaptive_const_probe.py` の buildcache sink を 3013 -> 3019 と 3382 -> 3387)。
競合は 0 件だが、Codex `role=author` が合成を 6 項目で監査してから merge message を書いた —
両側の更新が同居していること、各値がそれぞれの現物の呼出し位置と一致すること、ledger の 8 entry と
`owner` / `sink_kind` / `sink_scope` / `reason` が base から不変であること、他 4 file の pin が
壊れていないこと、定義側と exact expected set が同値であること。

**この受入の後に本記録の commit を足したので、land 直前に受入を取り直している。**

## 9. 次の一手

- **主判定を確定させるには新しい cohort が要る。** 残った 1 件の 0 commit が、実現系の一時停止か、
  窓の切り方の性質かは、成果物からは区別できない。観測長と窓構成を固定した独立 cohort で、
  v2 の規則を**その cohort の outcome を見る前に**当てるのが筋である。同じ 12 件について v2 を
  再改訂する話にはしない (§7 が禁じている)。
- 全ての割当に後続窓を保証する trace の延長 (事前登録 §4 の限定を外すため)。
- policy 腕の trace 無効な性能測定 (巡回順の block 設計 + 独自の事前登録)。
- policy≠0 の cell の直列性認証。
- 割当列が seed の LCG と一致するかを解析器が検査していない (v1 から不変。本 wave の変更面外)。
