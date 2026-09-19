# 段 4 裁定 — [{{T:mocc-witlight-arm-run}}] mocc 軽量 witness の実装と 4 arm 実走 (2026-09-19、親 = claude opus)

裁定 inbox の再走査: `docs/handoff/` は T-1998 (2026-08-28 中断、無関係) のみ。wave 開始後の main 前進 (peer 通知 657e1e5a7) は docs 系で本 wave の設計に影響しない (受入前に再読)。

## 1. 所見の裁定 (real / refuted、採否)

### plan (段 2) の補正 — 全件 real・採用
- P1: `#line` は W に不要 (`_cpp_normalize` が `-E -P -dD`、include 除去、`__LINE__` 不使用)。測定 patch 側に `#line 115 / 1136 / 1201 / 1208` を置く。
- P2: TLS vector は `izanagi_mocc_g2_enabled()` の有効分岐内で構築。off の保証は「TLS の構築・clear・reserve・push・decode・S 出力を実行しない。ポインタ初期化と分岐は残る」に限定。
- P3: smoke の H 行は witness file ごとに 1 行。S の `(txid,key,epoch,tid)` Counter が標準 trace の W と一致、各 identity 1 件、C の write 数合計と照合。
- P4: v5 は非 G2 走の raw を削除するため、smoke 限定の観測 wrapper (`smoke_capture.py`、v5 を import し verifier 起動境界で saved_trace / witness を複製してから実物へ委譲) を author 所有に 1 本足す。DW-O14 の「実物へ委譲する観測 wrapper」に該当し差し替えではない。本走では使わない。
- P5: `selftest` は subcommand。
- P6: 代替 (pin=W + runner v6) は不採用 (v5 の `pin != PIN` 条件が理由、discriminator 自体は pin 非制限)。

### レンズ A (観測意味論・identity)
- **A-MF1 (real・採用):** 合成 source (e9e477ca + X/P + witlight.patch) の TRACE=0 identity は本 wave の予定検査で担保されない。**裁定 = 本 wave では TRACE=0 binary 比較を実施せず、insight §2/§3 に「測定用合成 source は TRACE=1 専用の観測 build であり性能値には使用しない。W 単体の OID identity (2 本) と合成 source の binary identity は別」と明記する。** W の identity 2 本は省略しない。規律 1 は「性能計測は trace-disabled build」で守る (本 wave は性能値を出さない)。
- **A-MF2 (real・採用):** brief の「DW-G05: 放置時の成果物影響 = なし」を撤回。成果物 = k/m・CP・識別件数・insight の主張。所見ごとに「観測値・識別結果・主張への影響」を評価する (本裁定の各項に付す)。
- A-R1〜R4 (refuted): S 遅延で採取値は変わらない (decode は publish 直後、helper は保存値と `write_set_` の所有 key を使う)、E は別 stream、TLS 残留経路なし、INSERT/DELETE は on で abort。→ 設計変更なし。ただし異常終了時の prefix 非同一の限定は必須 (§3)。
- A-S1〜S4 (real・採用、insight の記述): off の未実測範囲 (旧 off binary との命令列・TLS 領域・cache 等)、窓短縮量の未実測 (残る処理の列挙)、`certified=true` / `observational_only=false` の限定と旧束縛保持の文言、trailer は実質寄与者 (author + manager) を記録。
- A-N1 (採用済): 運用事実の abort 参照を M:1059/1069 に訂正済。A-N2: R:548。

### レンズ B (実験設計・収集)
- **B-M1 (real・採用):** 変異 matrix の免除は「outer repo の製品実装差分ゼロの範囲」に限る。W・測定 patch・smoke wrapper の挙動検査は免除しない → §5 に限定登録 (位置・入力・期待拒否・他層 mask)。
- **B-M2 (real・採用):** smoke の技術的合格集合を結果前に固定 → §4。rc=0 と「整合した G2 の rc=1」を合格候補、on の rc=1 は discriminator の正常完了と証拠を要求し `supported` / `contradicted` の別で再試行しない。blocker / 入力拒否は原因を記録して保留。規律 2 の reject は不変。
- **B-M3 (real・採用、方法は限定):** S の identity Counter は第 5 値 (保存 producer) を被覆しない。runtime の不一致注入は同 source の synthetic build を要し認可外 → (a) author が採取→vector→出力の data flow を行番号で自己申告、(b) 段 6 レビュー A が独立に同じ 3 行 (decode → push → 添字読出し → helper 引数 → `<< stored_producer`) を引用して確認、(c) smoke の on arm 全 S で「第 5 値 == 第 2 値 (writer txid)」を正例として記録 (不一致が出れば消さず既存 blocker として保存)、(d) insight に「保存値の pass-through は静的確認であり runtime 注入では検証していない」と限定を書く。
- **B-M4 (real・採用):** 4 投入元の開始条件を固定 → §4 末尾。`check-base-dirs.sh` (outer HEAD・index の gitlink・submodule HEAD・pin 解決・pin type・orphan hold・clean) に base git dir を足し、各 launch 直前に `ps` で同一 worktree からの稼働 dispatch 0 件を実測。smoke の終端確認 (`.done` + result + accounting) 後に本走へ使う。
- B-should (採用): 4 JSON は `jq -S 'sort_by(.name)'` で順序除外比較、欠測後は実現した位置頻度を分ける、bundle は自己完結 (prerequisite 無し) + fetch 後 ref が W を指すことを撤去前に確認、率の名称は「G2 signal 検出率」、cycle 正の非 G2 は k だけでなく CP/Fisher も訂正値で。
- B-refuted: 検出力表・回転・JSON sha・別 build の runner 改修必要性・「on で G2 が出なければ失敗」はいずれも不成立。
- B-nit: O:12 の位置表現 (round 13〜15 は「開始 arm」の説明)、小数率と分数の表記。
- B-不確実: 「≥56 の根拠 = T-2774 段 3 レンズ B」の帰属は逐語未確認 (0.119 × K=56 = 0.8116 の数値整合は確認)。insight では「T-2774 段 3 レンズ B の計算 (率 0.119 の条件付き)」と書く。

### 親 brief への異議 — 採用
- B:18 の「成果物影響なし」撤回 (A-MF2 / B)。B:17 の包括免除撤回 (B-M1)。B:8 の「決定的結果」を「識別到達点 (呼出成功・正常完了・識別成功を別に数える)」へ (B)。B:15 の `--selftest` → `selftest` (plan/B)。P2(a) の「X/P 文脈が必ず衝突」は今回の W では不成立 (A) — pin 条件が採用理由として残る。P3 の `#line` 必須説撤回 (plan/A)。P4 は旧 off binary との実行同一性を含意しない (A/plan)。

## 2. 設計の確定 (plan v2)

1. **W** (= `5b02546f`、初版 `e0905b3d` を段 6 レビュー A MF2 で message だけ amend、tree 不変) = plan §2 の diff 逐語 (`#line` 無し、include 不変、`#if TRACE` 内のみ)。branch `izanagi-t1943-mocc-g2-witlight`、親 e9e477ca、touch = `cc/mocc/transaction.cc`。commit は親が wave worktree の submodule で一時 worktree を切って `commit -F` (message = plan §2 の文案 + trailer: `AI-Agent: product=codex; model=gpt-6-astra; reasoning=<起動器 receipt の値>; role=author` と `AI-Agent: product=claude; model=claude-opus-5-1m; reasoning=xhigh; role=manager`)。
2. **測定 patch** `witlight.patch` = A (e9e477ca + X/P) → B′ (W + X/P + `#line` 4 か所) の diff。同内容性 = 両辺から `^#line` 行を除いた bytes の `cmp` 一致。
3. **arm** 4 本 = plan §4 逐語 (`e9-witlight-wit` / `-nowit` / `-wit-bo1` / `-nowit-bo1`、全 arm pin e9e477ca + [X/P, witlight.patch]、`observational_only: false`)。node k の JSON は k−1 回転、4 file の sha を記録。
4. **runner** = v5 無変更 (sha 7907a545…)。smoke だけ wrapper 経由。wrapper の契約 (B): 元の `command` を保存し verifier 起動を正確に識別して一度だけ委譲、argv / cwd / timeout / env / 返値・例外を改変しない、複製失敗を黙って成功にしない、run 単位で保存し複製集合・bytes・sha と保存成功数を残す、import した v5 の `__file__` を変えない (R:483〜487 の runner sha は v5 本体のまま)、wrapper sha と使用事実を別に束縛し smoke を「v5 単体実行」と記録しない、本走では使わない。
5. **投入** = smoke 1 node (node1 JSON、`--rounds 1`、4 走) → 本走 4 node (W1〜W4、`--rounds 15`、60 走/node)、generic dispatch walltime 02:30:00。**rounds は launcher 引数で固定 (15)、結果を見て増減しない。**

## 3. 事前登録 (結果を見る前に確定)

(plan §5 文案を採用、B の修正を反映)

> 本走は 4 block × 15 round × 4 arm、各 arm 計画数 60。smoke と過去 wave は分母へ含めず、結果による追加・補充・早期打切りをしない。cell は 3 秒・48 thread・10,000 records・rratio 50・rmw 0・max_ope 10・zipf 0.9。
> 主表示 = arm 別 k (G2 signal 走数)、m (有効 verdict 数 = v5 の定義、indeterminate を含み failure を含めない)、k/m (「G2 signal 検出率」と呼ぶ)、Clopper-Pearson 両側 95%、`decisive_m`・failure・未収載数を併記。cycle 正の非 G2 現象が混在した場合は k だけでなく CP / Fisher も訂正した G2 件数で計算する。分母が欠測で 60 を割った場合の Fisher は実 2×2 表で再計算する。計画数・保存済み N・failure・indeterminate を併記。indeterminate を「G2 なし」と書かない。親は全正例の verifier JSON の `phenomenon` を照合し、非 G2 の cycle があれば分ける。
> 主比較 = BACK_OFF=0 の `e9-witlight-wit` 対 `e9-witlight-nowit`、on 側が低い方向の片側 Fisher (参考値)。副比較 = BACK_OFF=1 の on/off。family 全体の効果をどちらか 1 つの p<.05 で宣言しない。block 別件数を併記。CP/Fisher は独立・同率 Bernoulli の参考値で node 内相関・順序・時間変動をモデル化しない。固定時間の走あたり検出率であり同じ commit 数への曝露比較ではない。
> 検出力 (K=60、片側 α=.05): off 0.0417 対 on 0 → 0.105、0.058 → 0.268、0.119 → 0.856、部分抑制 0.0417 対 0.014 → 0.050。on=0 のとき off ≥5 で p<.05。**認可枠 60 を超えない。検出力はこの上限として明記する。**
> 実用上の到達点 = on arm に G2 ≥1 件が出て discriminator の入力へ到達すること。呼出成功と `supported` / `contradicted` による識別成功を別に数え、blocker / 入力拒否だけなら識別達成としない。到達点は率差の有意性・根因・認証を意味しない。
> T-2779 の通常 arm 5/120 は旧 witness source・別 block・別日の参考値として併記し合算しない。旧 heavyweight on arm を含まないため、軽量化の改善量を因果的に推定しない。
> 問い (ii): on arm の G2 各件に走単位の結論表 (rc/status、conclusion、blockers 原名、comparisons 件数) と comparisons 全件の表 (G:607〜615 の field)。結果別の主張上限は plan §6 の表。`witness-post-store-token-mismatch` は S の blocker で `contradicted` に読み替えない。off arm の G2 は `not-run (witness-off)`。

## 4. 欠測規則・smoke 合格条件

- 欠測 (a) 保存済み / (b) 開始証拠あり未収載 / (c) 未開始確認済み / (d) 状態不明。主解析は (a)。補充しない。dispatcher 成功・runner 完了・各走成功を分けて確認 (`.done`、result、accounting)。
- **smoke の技術的合格集合 (結果前に固定、B-M2):** 前提 = 4 走とも benchmark rc=0、build 4 arm 成功、raw 完全 (wrapper 複製の集合・bytes・sha が保存成功数と一致)、verifier JSON 整合、binding 一致 (runner sha 7907a545…、arms JSON sha、X/P sha e9e65b78…、witlight.patch sha、source sha 4 arm 同一、bo1 だけ `BACK_OFF=1`、wrapper sha を別束縛)。この前提の下で verifier **rc=0** と **整合した G2 の rc=1** (現象名 G2・cycle 正・trace-manifest あり。on arm なら discriminator が正常完了し `supported` / `contradicted` / blocker のいずれかを出す) を合格。on の rc=1 で blocker / 入力拒否なら原因を記録して技術的受入を保留 (再試行しない)。rc=3 (indeterminate)・build / 計器故障・witness file 欠落は不合格。**結果を見て smoke を繰り返さない。** on arm の witness 検査: H = 各 file 先頭に正確に 1 行、S の identity (txid,key,epoch,tid) Counter = 標準 trace の W (2,3,5,6 列) Counter、各 identity 1 件、C の write 数合計と一致、全 S で第 5 値 == 第 2 値 (B-M3 (c))、L/R 対応、空集合どうしの一致は合格にしない (commit・write・witness の実在)。
- **4 投入元の開始条件 (B-M4):** launch 直前に (1) `check-base-dirs.sh` (outer HEAD = a99425b66、index gitlink = 511c9538、submodule HEAD = 511c9538、pin e9e477ca 解決・type commit、orphan hold 0、dirty 0、base git dir = `.git/worktrees/<wt>/modules/external/ccbench` または `.git/worktrees/witlight-nodeN/modules/…`)、(2) `ps -eo args | grep -F <worktree path> | grep dispatch_compute` が 0 件、(3) smoke は wave worktree から、本走 W1 は smoke の終端確認後に同 worktree から、W2〜W4 は node2〜4 から。同一投入元への並行 dispatch を禁止。

## 5. 変異・検査の登録 (DW-M01、B-M1 で限定)

免除根拠 (1 行): **outer repo の製品実装 matrix は差分ゼロ (gitlink 不変、patches/ 不変、runner 無変更、insight + spool のみ) の範囲に限って免除し、W・測定 patch・smoke wrapper の挙動検査は免除しない。** 親が実走し、結果は insight §7。各項は単一理由性 (他層 mask 無し) を実装後に確認する。

| # | 対象・位置 | 入力 | 期待 | mask する層 |
|---|---|---|---|---|
| V1 | W の include 契約 | `--old 511c9538 --new W` / `--old e9e477ca --new W` | rc=0 (正例、先に緑) | なし |
| V2 | 同上の負例 | W に `#include <vector>` を `#if TRACE` 内に 1 行足した一時 commit W′ (別 scratch、W へ混入させない) | checker rc=1、stderr に `include 行文字列（順序込み）が不一致` | なし (include 比較は preprocess 比較より前、checker 537〜555) |
| V3 | 同内容性 cmp | (e9e477ca + X/P + witlight.patch) 対 (e9e477ca + W.patch + X/P)、`^#line` 除去 | 一致 (正例) | なし |
| V4 | 同上の負例 | witlight.patch の `#line` 除去後に残る `+` 行 1 byte を変えた写し (適用可能なもの) | cmp 不一致 (適用失敗・sha 不一致だけで赤にしない) | なし |
| V5 | smoke wrapper の観測義務 | verifier argv でだけ複製、他の argv では複製しない (author の最小確認)、複製失敗を成功扱いしない | 期待どおり | なし |
| V6 | smoke on arm の S 件数・identity・第 5 値 | 実走 witness file | S = W Counter、各 1 件、第 5 値 == 第 2 値 (正例検査、変異ではない) | なし |
| V7 | 保存値 pass-through | 静的 (author 自己申告 + レビュー A の独立引用) | data flow 3 行の一致 | runtime 注入は未実施 (限定を insight に書く) |

受入全走は免除しない。

## 6. 段 5 / 6 の分割

- 段 5 author 1 本 (worktree `.codex/worktrees/witlight-author`、所有 = `tools/t_witlight/` 直下の新規 file のみ、submodule 非接触)。
- 段 6 review A (W の正しさ・identity・同内容性・provenance) / B (JSON・回転・define・smoke 証拠・実走数・rc/phenomenon・欠測・CP/Fisher・識別表)。
