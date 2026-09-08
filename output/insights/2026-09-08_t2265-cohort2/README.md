# [T-2265] 独立 cohort で反実仮想 ITT の主判定が確定した — 推奨方向の実用優越

2026-09-08 起動、2026-09-09 測定完了。branch `worktree-dev-wave-t2265-cohort2`。base main `cc9bba523`。
cohort 1 の一次資料は `output/insights/2026-09-08_t2265-itt-seq0/README.md` と
`output/insights/2026-09-07_t2265-backoff-itt/README.md`。

## 0. この wave が主張すること・しないこと

**主張する。**

1. **凍結した事前登録の規則の下で、主判定が確定した。**
   `decision = recommended_direction_superior`、12 cluster 完備、判定を止める規則は 1 つも発火しなかった。
   効果は **+4.900%** (log `0.04783787625708289`)、**95% CI は [+3.316%, +6.509%]**、
   その下端が実用差の境界 `+3.0%` を上回る。
2. **0 commit 窓が構成上生じないことを実測で確認した。** cohort 2 の全走行 (pilot 18 run +
   確認集合 12 job x 18 run) で、記録された窓の `window_commits` は最小でも 10,000 であり、
   時間 cap は 1 度も発火していない。
3. **位置除外の後に残るすべての割当が後続窓を持つ。** 各 run に割当を持たない terminal event が
   ちょうど 1 件、必ず末尾に記録された。cohort 1 の §4 が持っていた「最後の更新は必ず落とす」という
   限定は cohort 2 には無い。
4. **事前登録を測定投入前に凍結した。** docs のみの commit `f3daa80db`、bytes の sha256
   `8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9`。
   この commit の時点で cohort 2 のデータは 1 bit も存在しない。

**主張しない。**

- **cohort 1 の主判定を確定させたとは言わない。** 窓構成を変えたので推定対象が変わっている (§1)。
  **cohort 1 の主判定は `inconclusive` のまま確定している。**
- **性能結果ではない。** trace 有効 build の診断であり、絶対規律 1 に従い throughput の性能主張に
  使わない。
- **正しさの主張ではない。** cohort 2 が使う 12 本の seed 別実行体は認証していない (§7)。
  判定を variant の採用根拠・fitness・選択結果へ昇格させてはならない (絶対規律 2)。
- **`+4.9%` に広い一般性があるとは言わない。** 単一環境・単一 protocol・単一 workload の主層に
  ついての局所効果である。

## 1. 推定対象が cohort 1 と同一でないこと (最重要の限定)

- cohort 1 の推定対象は「commit 数 10,000 到達か 10,240 µs 経過のどちらか早い方で閉じる**混合窓**」の
  上の局所 ITT。
- cohort 2 の推定対象は「commit 数 10,000 到達で閉じる窓」の上の局所 ITT。
  count で閉じる窓では `window_commits` がほぼ閾値に張り付き、`window_us` が処置の影響を受ける
  停止時間になる。**無効な outcome ではないが、cohort 1 とは別の outcome である。**

**なぜ同一の推定対象で決着させなかったか。** cohort 1 の主層では 12 run のうち 1 run が
`seq >= 1` の `window_commits = 0` で無効化された。同じ窓構成で測り直すと 12 run のどれかで
再発する確率は `1 - (11/12)^12 = 0.648` である。**同一の推定対象のままでは、事前登録した規則の下で
判定を安定して出せない。** 規則を緩めて 0 commit の窓を個別に落とす案は処置後 outcome による選択なので
採らなかった。残る道は、0 commit が構成上生じない窓構成を**結果を見る前に**固定することだけだった。

**したがって本試験は「cohort 1 を pilot とした、関連する新しい count-closed 推定対象に対する
前向き確認試験」である。** この位置づけは事前登録 §0.0 に凍結前から書いてある。

## 2. 凍結の順序と、その証拠の限界

| # | commit | 内容 |
| --- | --- | --- |
| 1 | `f3daa80db` | cohort 2 の事前登録の凍結 (**docs のみ**) |
| 2 | `18d68df5e` | 実装の統合 (段 5 の 4 unit) |
| 3 | `21b1c316f` | 段 6 の fix |
| 4 | `8b13d0335` | patch identity pin の追随 |
| 5 | `8bdf173cc` | local main の取り込み |

測定はこの 5 commit がすべて存在した後に投入した。成果物の `repo_head` は
`8bdf173cc81e5371db7b7bcddb8bdcbb5aeff235`、`counterfactual_preregistration` は
`8b4127f4…` である。

**証拠として言えること。** 事前登録の blob が実装 commit と結果より前にあり、
その時点で cohort 2 のデータは存在しなかった。解析器は事前登録の sha256 を module 定数として pin し、
渡された文書の実 sha と exact 比較する。

**証拠として言えないこと。** commit の順序は内容の祖先関係を示すが、「別経路で先に計算していない」
ことの証明にはならない。ただし cohort 2 は本 wave が初めて測ったデータなので、
**凍結前に計算しようがなかった**点は cohort 1 v2 より強い。

## 3. 生死確認 (pilot) — 凍結後、確認集合より前

事前登録 §0.1 の定めに従い、**pilot は別 namespace へ出力し、確認集合から永久に除外した。**

- job `985845.nqsv`、出力 `izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2-pilot/`、
  seed `14481721328008317845`、`repo_head 8bdf173cc`。
- **見た項目 (全開示):** schema 版、事前登録 sha、`extime_s`、`stage`、`rep_index`、`reps_per_job`、
  `step_policy_seed`、`repo_head`、`throughput_scope`、`headline_eligible`、`job_total_seconds`、
  patch identity、18 run それぞれの event 数・terminal の位置・`seq` 連続性・
  `window_commits` の最小値・trigger の内訳・`trace_summary` の 4 値・terminal の
  `window_us` / `window_commits` / `assigned_invert` / `trigger`。
  **theta / D[r] / CI / decision は計算していない。**
- **結果:** 18 run すべてで `window_commits` の最小値は 10,000 以上、trigger は `count` のみ +
  terminal 1 件 (時間 cap は 0 件)、terminal は必ず末尾、`seq` は 0 から連続、
  `assigned_invert = -1`、summary は `updates = retained = 通常 event 数`・`dropped = 0`・
  `flushes = 1`。**機構は仕様どおりに動いた。**
- 主層 (`cw-as-dyn-c2-p2` write-heavy 48t) の event 数は 1048。job 所要は 192.7 秒。
- 解析器の `_load_artifact` がこの成果物を受理することも確かめた (割当整合性検査を含む)。
  **推定値は計算していない。**
- 逐語は `verbatim/pilot-structure.txt`。

## 4. 確認集合の測定

- **12 job を同時投入した** (`985851`〜`985862`)。固定 12 seed は事前登録 §8.1 の逐語。
  出力は `izanagi-job-evidence/dynamic-backoff/trace/t2265-cohort2/` の 12 file。
- 投入元は固定 SHA `8bdf173cc` の detached submit-tree。tracked-clean、submodule pinned-clean、
  canonical root から qsub した。
- **build cache の取り合いは起きない。** t2187 の driver は共有 cache の claim を使わず、
  `isolated_checkout` が `$TMPDIR` へ `git clone --shared` する node ローカルの木を建てる。
  したがって 12 本を 1 度に投げてよい (cohort 1 は 12 本を直列に投げていた)。
- **12 job すべてが完走し、12 成果物が揃った。** 途中解析はしていない。結果を見てから job を
  足していない。

## 5. 主判定

解析結果の正本は `analysis-result.json` (`analysis_version =
izanagi-backoff-counterfactual-cohort2-analysis/v1`)。

| 量 | 値 |
| --- | --- |
| `decision` | **`recommended_direction_superior`** |
| `confirmatory_complete` | `True` |
| `reasons` | `[]` (判定を止める規則は 1 つも発火せず) |
| `cluster_count` | 12 (完備) |
| `theta_log` | `0.04783787625708289` |
| `effect_percent` | **`+4.900057363838283`** |
| `cluster_sd` | `0.023952998889712838` |
| `standard_error` | `0.006914635178437258` |
| 95% CI (log) | `[0.03261886656594313, 0.06305688594822265]` |
| 95% CI (%) | **`[+3.3157, +6.5087]`** |
| 90% CI (%) | `[+3.6055, +6.2108]` |
| `tost_equivalent` | `False` |
| `recommended_practical_superiority` | `True` |
| `inverted_practical_superiority` | `False` |
| 等価域 (%) | `[-2.9126, +3.0000]` |

- 12 run すべてが推定値を出した (`reason` が `null`)。run 別の効果は **+0.649% から +10.162%**、
  1 run あたりの outcome 対は 906 から 1071。
- 無作為化の検査 (割当前の量): 12 run の実測割当比は `0.4873` から `0.5309`。
  事前登録どおり、この検査の結果で run を除外していない。

**余裕は薄い。** 95% CI の下端 `+3.3157%` に対し境界は `+3.0%` で、差は約 0.32 ポイントしかない。
**「大きな効果が確実にある」とは読めない。** 事前登録した規則が「実用優越」と呼ぶ閾値を、
わずかに超えたということである。

### 5.1 この結果から読んではいけないもの

段 3 の因果推論レンズが列挙し、親が採用した。

- 「cohort 1 の主仮説または主判定を確認した」— **推定対象が違う** (§1)。
- 「controller の向きは commit 速度を +4.9% 変える」を trace 無効 build へ一般化すること。
- 「policy 0 と policy 1 の run 全体の性能差」への読み替え。持ち越しは測っていない。
- 「全 workload・thread・個々の窓で +3% 以上の差がある」— 主層 1 つについての平均である。
- 「割当整合性検査 (LCG) により無交絡の因果効果が証明された」— この検査は割当が実装どおり記録された
  ことを示すだけで、事前固定 LCG が物理過程と同期しないという as-if 仮定は未検証のままである。
- 「効果があるので variant として採用してよい」— 未認証であり絶対規律 2 に反する。

## 6. 副次 (探索的。主判定を置き換えない)

事前登録 §6 が「すべて探索的な記述であり、主判定を置き換えない。多重比較の補正はしない」と定めた層。

- 残る 5 つの (workload, threads): `+3.378%` から `+9.113%` (すべて正)。
- `recommended_delta_sign` 別: `+3.416%` と `+8.545%`。1 層は片方の割当が無く `missing_assignment_arm`。
- `both_actions_feasible` 別: `+3.884%`。1 層は `missing_assignment_arm`。
- 時間 block 別 (4 分割): `+8.570%`、`+4.881%`、`+4.095%`、`+2.215%`。

**これらの符号を主判定の確認・救済・一般化に使わない。** 層別変数は現在の割当より前に確定するが、
先行する割当の影響を受けた状態なので、層内の対比を因果効果として解釈しない。

## 7. 直列性認証の射程 (実装したこと・していないこと)

**実装した。** `--mode certify` の受理形へ cohort 2 の policy≠0 cell 2 本を足した。
raw allowlist、parsed membership、cell 別 extime、claim、namespace、row、group、PBS の全箇所を
exact な閉表にし、cap を 1 だけ変えた literal で拒否されることを検査した。
旧 `tuned` / `cw-as-dyn` の extime 3 束縛は 1 文字も変えていない。

**実測した (2026-09-09)。** cohort 2 の policy≠0 cell 2 本について認証を走らせ、
**どちらも 24/24 が certified serializable、anomaly 0 件**で group receipt が `complete = true` に
なった。

| cell | attempt | group receipt | sha256 | 結果 |
| --- | --- | --- | --- | --- |
| `cw-as-dyn-c2-p1` | `c2p1-a1` | `izanagi-job-evidence/dynamic-backoff/certify/c2-p1-a1/group-receipt.json` | `7a575651e3214a07e5c44f48b925602c0bd1553a82c9e42d8f9040c9542f66f5` | expected 24 / terminal 24 / **certified 24** |
| `cw-as-dyn-c2-p2` | `c2p2-a1` | `izanagi-job-evidence/dynamic-backoff/certify/c2-p2-a1/group-receipt.json` | `8c4dbe50a06ad1696e9352a58bfa7b4c9b02033d0860e1f391e6b217557c6d95` | expected 24 / terminal 24 / **certified 24** |

束縛は performance 成果物 `dynamic-backoff/perf/stage1-rep0-0_985871.nqsv.json`
(sha `ed7fb0dce88201c87a9d04b23bc1a59d3f00a66a378b05cf756a04687af8ca45`)、verifier identity manifest
`verifier-identity-c2a1.json` (sha `d5c12d4c03997784ee1f5bb23e387cab1b39ddfb40d47d73139047f31316c020`、
module 10)、`repo_head 8bdf173cc`。1 job の実所要は約 3.5 分だった。

**それでも射程は限られる。** 認証が対象にできたのは**既定 seed の実行体と 48 スレッド**だけである。
policy 2 の実行体は seed を compile 時 define で埋め込むので、**cohort 2 が使う 12 本の seed 別
実行体の認証ではなく、24 スレッド条件の認証でもない。** 全 binary の認証には 312 job が要る。
**「cohort 2 を認証した」と書いてはならない。**

## 8. 段 3 と段 6 の敵対検証が見つけたもの

### 8.1 段 3 (プラン起草の前と後)

- **因果推論レンズが、親 brief の完了判定を覆した。** 窓構成を変えると推定対象が変わるので、
  この cohort は cohort 1 の主判定を確定させない。§1 と事前登録 §0.0 はこの指摘の結果である。
- 同レンズが、terminal 非閉鎖を outcome に基づく置換・除外にしてはならないこと、
  pilot を確認集合から永久に除外して開示すること、`R = 12` の検出力を条件付きでしか書けないこと、
  LCG 検査を「無作為化の検証」と呼んではならないことを指摘した。すべて事前登録へ入れた。
- **実装規律レンズが、段 2 プランの terminal 設計が実行不能であることを示した。**
  プランは `common/runner.hh` を patch 対象へ足す設計だったが、
  `orchestrator/campaign/source_digest.py` の allowlist は 4 file しか許さず、
  driver は patch 適用後に allowlist 外の tracked 改変を拒否する。**この設計では build 前に必ず止まり、
  成果物が 1 件も出ない。** patch C を 2 file に閉じる設計へ裁定し直した。
- 同レンズが、巨大 cap では `clocks_per_us_ * cap_us` が 64 bit を溢れて cap が即発火することを
  示した。**親 brief の「cap を大きくするだけでよい」は、この値域では誤りだった。**
  比較を除算へ変えた (正整数では厳密に同値)。
- 同レンズが、12 job 同時投入で build cache の claim が衝突するという親の説明が実経路と違うことを
  示した (t2187 は legacy API を job 別 scratch で使う)。**親の「1 本先行 + 11 本」の段取りは不要だった。**

### 8.2 段 6 (実装後)

- **レビュー 2 本が独立に同じ最重要欠陥を指摘し、親の焦点走がそれを実測した。**
  patch C が raw trace の版を無条件に上げたため、terminal を無効にした走行
  (cohort 1 と legacy の全診断走行) が producer の parser に拒否されていた。
  **放置すれば既存の受理集合が縮み、かつ事前登録が定める terminal 非閉鎖の `inconclusive` 経路が
  到達不能だった。** raw trace は terminal 0 件または末尾 1 件を受理する形へ直した。
- terminal define の必須契約が `#if BACKOFF_TRACE` の外にあり、trace 無効を含む全 build が
  新 define を要求していた (絶対規律 1 の分離が計装の外へ漏れていた)。内側へ移した。
- terminal 記録後に制御器・LCG・割当が run 終了まで止まっていた。事前登録に無い挙動なので、
  記録したその呼び出しだけ更新を止める形へ直した。
- cohort 1 の成果物 metadata 分岐が新しい terminal 軸を見ておらず、near-miss を受理しえた。閉じた。
- cohort 2 解析器が patch stack の集約 sha を検査していなかった。exact 検査を足した。
- 逐語は `verbatim/`。

## 9. scope 外と裁定したもの (ユーザーへの裁定パッケージ)

1. **published group receipt の再受理が exact でない。** 再検査が `certified_requests` だけを見て、
   件数・claim limitations・未認証 marker・各 row の状態・`trace_dir` を確認せず、
   その `trace_dir` を `shutil.rmtree` へ渡す。**本 wave が作った欠陥ではない。**
   本 wave は受理形を 2 cell から 4 cell へ広げたので**露出は増える**。
   修正は防壁の強化であり、ユーザーの「仮想リスク向けの gate 追加は scope 外」に当たるため裁定へ返す。
2. **cohort 2 の図を実際に描くには、観測長 6 秒の performance 成果物が 6〜7 本要る。**
   本 wave はそれを測っていない。ユーザーの残件は「図が新 cell と新 event 項目を理解する改修」で
   あり、解析・identity・event 項目の理解までを本 wave の成果とした。
3. **trace ring の容量 (65,536) に到達すると `seq` と summary の契約が壊れる。**
   ただし fail-closed で拒否されるので誤った値は成果物にならない。cohort 2 の実測 event 数は
   1,000 前後で容量の 1.6% であり到達しない。

## 10. 親の記録の訂正

- 段 4 裁定の「terminal は 1 秒の余裕で必ず入る」は不正確だった。**terminal は期限経過に加えて
  count 閾値到達も要求する。** 実測では全 run で到達した。
- 段 4 裁定の「既存 cell の挙動は変わらない」は `clocks_per_us_ > 0` のときだけ正しい。
  0 のとき旧式は即時発火、新式は永久 false になる。実運用では 0 にならない。
- 段 4 裁定は 3 unit としたが、実際は **unit D を足して 4 unit** になった
  (新しい CMake define の条件レジストリ登録が A/B/C の所有外だった)。
- 認証 job 数は **48** (2 cell x 3 workload x 8 slot)。裁定の「49」は誤りだった。

## 11. 変異検査

probe -> 本走の 2 段。**probe は全件 SURVIVED で登録し、観測 node を集めてから本走で完全集合を
KILLED として登録した** (期待 node の推測を避けるため)。runner は
`test_backoff_counterfactual_cohort2_analysis.py` + `test_t2187_adaptive_const_probe.py` +
`test_dynamic_backoff_transitions.py`。

**本走: baseline PASSED、7/7 KILLED、生存 0・MISMATCH 0・期待 node 完全一致。**
spec は `mutation-spec.json` (sha256 `51e8a65b…`)、報告は `mutation-report.json`。
probe は `mutation-probe-spec.json` / `mutation-probe-report.json`。

| 変異 | 変異箇所 | 殺した node 数 |
| --- | --- | ---: |
| `m1-drop-positional-exclusion` | 解析器の `analysis_events = events[1:]` | 2 |
| `m2b-lcg-check-disabled` | 割当整合性検査の比較 | 1 |
| `m3-zero-scan-excludes-terminal` | 0 commit 走査から terminal を外す | 1 |
| `m4-allow-multiple-terminals` | terminal の一意性検査 | 1 |
| `m6b-terminal-sentinel-not-enforced` | terminal sentinel 契約の `_fail` | 5 |
| `m7-cap-comparison-overflows` | patch C の cap 比較を乗算へ戻す | 2 |
| `m8-parser-rejects-zero-terminal` | parser が terminal 0 件を拒否する | 3 |

### 11.1 probe が暴いたこと (erratum。初回結果を消さずに残す)

- **1 回目の probe で `m6` (terminal sentinel 契約) が生存した。** この契約を破る成果物を与える
  テストが 1 つも無く、**歯の無い gate** だった。fix-5 で 5 field それぞれの負例を足し、
  2 回目の probe で 5 node を殺すことを確認してから本登録した。
  **変異検査が無ければ、この gate は「あるだけ」で着地していた。**
- **1 回目の `m2` (LCG の加算定数を 1 変える) は 7 node を落とし、赤理由が 1 つに絞れなかった。**
  定数が fixture の生成にも効くためである。`DW-M01` に従い**登録せず、実効 gate へ再照準した** —
  比較そのものを無効化する `m2b` は 1 node だけを落とす。
- **`m4` と `m5` (terminal が末尾でない形を許す) は同じ node で落ちる冗長 gate だった。**
  `DW-M03` に従い `m4` だけを本登録し、`m5` は単独変異の証拠から外した。
- **`m7` は patch file 自体を変えるので、その sha を pin する
  `test_cohort2_literal_pins_are_independent_of_fixture_helpers` も道連れで落ちる。**
  これは pin される file を変異させる以上避けられない。帰属の決め手は
  `test_count_window_cap_comparison_is_overflow_safe` である。
