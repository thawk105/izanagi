# docs/paper-story/ — 論文ストーリーの横断合成

論文で「何を新規性として主張し、どういうストーリーで語るか」の横断合成を集約するディレクトリ。
`docs/roadmap-history/` や `docs/related-work/` と同じく、**凍結スナップショットを時点ごとに束ねる**構成。

## このディレクトリの位置づけ

- 各スナップショットは**特定時点の凍結物**（新規計測ゼロ・その時点の正典からの導出）。**書いた後は更新しない。**
  内容を更新したいときは上書きせず、新しい日付のスナップショットを追加する。
  ただし**新しい日付の版は、その日付時点の正典全体からの導出でなければならない。**
  一項目だけを直した差分改訂を新しい日付の版として置くと、更新しなかった項目の stale が
  「その日付時点でそう主張した」という新しい嘘に変わる。一項目の決着を届けたいだけなら、
  版を足さずに本 README の「最新スナップショット以後に確定したこと」で指す。
- **図 (`figures/`) も同じ凍結物である。** 複数の版が同じ path を共有するので、誤りが見つかっても
  上書きしない。後継図は別 filename で、再現可能な生成器を伴うときだけ作る。
- 日付なしの入口はこの `README.md`（ポインタは腐らない・スナップショットは腐る、の原則）。
- **正典（矛盾があればこちらが勝つ）:** `docs/roadmap.md` §8（ポジショニング）・`docs/decisions.md`（設計判断）・
  `docs/worklog.md`（時系列）・`docs/phase3.md` + `docs/phase3-main-experiment.md`（Phase 3 完了定義・事前登録）。
  本ディレクトリの文書はそれらの導出物。

## 版の履歴

| 日付 | ファイル | 時点 | headline |
|---|---|---|---|
| 2026-07-03 | `2026-07-03.md` | Phase 2 完了・Phase 3 kickoff 進行中 | 否定的結果 + 空間外合成（P2-4/P2-5） |
| 2026-07-10 | `2026-07-10.md` | Phase 3 段 5 完了（sort 軸 iteration 1 が実 LLM で E2E certified） | 同上（Phase 3 進捗を反映、図つき） |
| 2026-08-23 | `2026-08-23.md` | 縮小主張 S' が headline 不成立で確定（2026-07-16）した後。8b descriptor・層3 事実層 v2・8c bounded MVP・床値 protocol まで機構は進行、新 protocol による床値の実測は未取得 | 同上（第 3 幕を「機構は深化し性能主張は後退した」として再記述。未取得証拠の一覧を A/B/C の 3 群で付す） |
| 2026-08-26 | `2026-08-26.md` | A-3（P2-4 利得値）決着・後継図 fig2b 成立・A-1 探索走と反復数事前登録の凍結・A-2 driver とコスト実測・床値 pilot の 12 セル完走・8c 正式系列の閂の再特徴づけ（D930）の後 | 同上（科学的主張は前版から動かず、「あと何が要るか」の地図だけが変わった、として §6 と §8 を全面再導出。§9 の分類に「限定付きで取れた観測」を追加） |
| 2026-09-02 | `2026-09-02.md` | A-2 が正式 protocol を outer `reject` で完走した後。論文採用値の別 boot 再取得（D1100）・A-1 の estimand 揃え直し（D1262）・床値 official が起動不能であることの確定（D1396）・完了証明層の C10 開放・B-10 拡張格子と balanced profile・MoCC G2 再現率・軸 1 本検索の実行まで | **性能主張の側に、現行環境で正式に測って負けた点が 1 つ生まれた。** 第 2 幕の否定的結果と肯定的結果の対比を主軸に据える結論は前版から不変。§9 の要約を 3 文から 4 文へ拡張 |
| 2026-09-05 | `2026-09-05.md` | 説明可能性 (軸 3) の核を D1598 で 3 点へ書き直し、A-2 結果節 (`results/` 系列) と図 5 が凍結された翌日に、その走行の adopted cell が採用静的 backoff を build していなかったこと (F707 再発。D1645 で取り直しまで論文素材から外す) が確定した後。A-1 pilot 事前登録の発効・A-5 の Pegasus 不充足 (D1525)・A-6 の `indeterminate`・床値の量の確定 (D1639 / D1641)・人間手番の AI 委任 (D1638) と予算承認・鍵配置の実施 (1278)・B-10 balanced 完走と read-heavy 試し打ち成功・調整済み adaptive の正しさ認証・2 本目の論文系列の新設 (D1637) まで | **差別化の核は「対象がトランザクション CC・action vocabulary そのものの拡張・正しさゲートを毎反復」の 3 点で書く。忠実性・proof chain・試行 provenance は補助。** 前版が「現行環境で正式に測って負けた 1 点」と数えた A-2 は、採用構成についての判定ではなかった。採用構成を現行環境の正式 protocol で測った判定は無い。第 2 幕主軸の結論は不変。§9 の第 4 文を書き換え |
| 2026-09-14 | `2026-09-14.md` | 採用構成を現行環境の正式 protocol で測った判定が 3 workload とも出た後。A-2 の取り直し attempt が `observed-positive` (2026-09-07)・A-6 が完走して `reject` (2026-09-08)・balanced の stock-inline 対が `accepted` (2026-09-14)・A-1 の pilot 完走と反復数の確定 (n=30) と本走認可の据え置き (D1986 項5)・走行間ばらつきの下限が 3 workload 揃ったこと・official 床値 campaign の史上初の実投入 (未 land)・B-10 待ち方 grid の閉鎖 (D1678)・静的 tail 本走 driver の着地 (本走未投入)・文献調査 2 軸の停止 (D1760 / D1931)・mocc への証明面計装 (T-2294)・D1936 と D1986 の一括裁定まで | **前版が「採用構成を現行環境の正式 protocol で測った判定は 1 件も無い」と書いた空白が埋まった。** A-2 protocol (write-heavy と balanced の連言) は `observed-positive`、A-6 protocol (read-heavy) は `reject`、balanced の別の事前登録の対比較は `accepted` で、**符号は旧環境と 3 workload とも一致した — ただし再現判定ではない。** 但し書き 2 (性能 workload そのものでの採用静的 backoff の certification) は限定 4 つ付きで外れた。第 2 幕主軸の結論と S' 不成立は不変。B-1 (既知軸最良の超越) も不成立のまま |
| 2026-09-17 | `2026-09-17.md` | official 床値 campaign が初めて計測段を越えて完走し floor 案の実値が出た (2026-09-16、両 holdout とも配線下限 0.03 × stock 中央値、未発効)・B-10 静的 backoff 右 tail の本走が完走して集団判定が出た (2026-09-15、`not-observed-in-any-workload`)・B-7 の 3 走行材料がそろったが要件充足へは昇格しない (D2044 項3)・rr5 の accepted 較正で silo 3 workload セルが揃い非 silo 4 対の within-run floor が用途限定で登録された (D2083)・B-4 の材料 (記述統計追補 D2016、binary record と配置 D2069、`perf_config` の 3 項目と 3 cell と較正選別規則 D2088〜D2090) が増えたが A-5 の値待ちで実施不可のまま・D1640 の追補 (D2049)・fig7・identity 走査境界の到達実測 (T-2630、修正は裁定待ち)・K2 ループの 1 巡 (T-2588、既評価値の再提案)・A-1 認可据え置きの再確認 (D2044 項8)・D2044 (39 項) の一括裁定・8c manifest schema の `n` (D2071 / D2072)・ライセンス D1992 まで (local main `fa24e6ea8` から導出) | **前版が「未取得・未投入」と書いた 2 つの測定 (official 床値、右 tail 本走) が完走したが、どちらも肯定的 headline 主張を増やしていない。** 床値は配線下限で決まった未発効の案、右 tail は「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」という記述的な結末。正しさの identity 層に上限が 1 つ実測で加わり、exact claim の限定は D1993 の 4 つ + 1 つ。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版を 3 か所で訂正した (執筆時点で偽だったもの) |
| 2026-09-19 | `2026-09-19.md` | A-1 balanced5 sized 本走の attempt-0001 が D2120 項 3 の 1 attempt 認可で投入され 3 workload とも完走した後 (2026-09-18、登録済み解析は 3 本とも `resolved-above-floor`、符号 +/+/−、非認証 lane のまま。単独稿と fig9)・stock mocc の G2 signal の 非 certifying 観測 3 件 (T-2774 witness off でだけ再現 2/40・3/40・2/40、T-2779 通常 5/120・診断 0/120・backoff 2/120、T-2780 discriminator の finalization 到達。D2148 項 13 = 上流報告まで)・Silo 固定スコープの解除 (D2114) と mocc 第 2 例の準備 (機械実証の設計 D2134 と wave 1 D2147、pin 前進の承認 D2150 項 1 = 未実施)・official 床値の g1 床としての採用裁定 (D2120 項 2) と g1 候補の実体化 (保存 branch) と chain land の不成立 (entry 1640) と A-3 整合 (D2154。chain 未取り込み・未発効)・B-4 spec 3 本の凍結 (D2138) と窓 job の資材 (D2145) と `PerfConfig` の出所 (D2146。実測未開始)・identity 層の上限の修正 (T-2731、D2108。残る限界は明記)・K2 2 巡目 (T-2746、事後承認 D2148 項 2) と機序仮説層 v3 の初適用 (D2143) と critic 診断の型付き入力経路 (T-2783、D2155。3 巡目未実走)・fig8 の成立・A-6 と T-1998 の単独稿・軸 1 の再開と限定付き閉鎖 (D2095 / D2120 項 14 / D2150 項 4)・一括裁定 4 回 (D2104 / D2120 / D2150 / D2148) まで (local main `a99425b66` から導出) | **前版が「本走未投入・認可据え置き」と書いた A-1 が非認証 lane の attempt-0001 として完走したが、「A-1 の値がある」とは書けず、肯定的 headline 主張は増えていない。** mocc は観測 3 件が出たが根因未同定・非 certifying で「第 2 成功例」ではない。床値は採用が裁定されたが未発効、B-10 は図が成立しても閉じていない。exact claim の限定は D1993 の 4 つ + identity の 1 つ (範囲は修正後に狭まった)。第 2 幕主軸の結論・S' 不成立・B-1 不成立は不変。前版の執筆時点の誤りは 0 件 |

**最新 = `2026-09-19.md`。** 図は `figures/` に、2026-07-10 版の作成時に気づいた示唆は
`notes-2026-07-10.md` に分離。`figures/fig3_arc_status.png` は 2026-07-10 版（Phase 3 段 5 時点）の
現況図であり、2026-08-23 版以降の第 3 幕の記述とは一致しない（各版 §0 に明記）。

**この節は最新版の訂正だけを載せる。** 旧版が自分の前版をどこで訂正したかは、その旧版自身の
冒頭が持つ（凍結物なので、訂正の一覧も版と一緒に凍結されている）。

**2026-09-19 版が前版 (2026-09-17 版) を訂正した箇所は 0 件である。** 同版の導出 (§0〜§10 の全項目を正典から
独立に導き直す) で、前版の記述が執筆時点で既に偽だったものは見つからなかった。前版の記述で古くなったものはすべて
「当時は真で、後続の前進が古くした」型であり、同版の本文で現在地へ更新した — その代表 3 件は、この節の下に積んでいた
stale 注記 (Silo 固定スコープの解除、fig8 の成立、A-1 attempt-0001 の完走) である。**0 件は誤りが無いことの証明ではない**
(下の「積んでいる項目の少なさは…」を参照)。前版が自分の前版 (2026-09-14 版) を訂正した 3 か所 (層3 screening の対象範囲、
official 初投入日 2026-09-09、D1341 未 land の誤認) は、前版自身の冒頭が持つ。

B-2 の `delta_min` について 2026-09-14 版が「受理集合を広げる向き」と書いた箇所は、引き続き誤りとは断定しない。
D2049 が定めるとおり、逆対応の逐語適用は片側の境界を過小に、他方を過大にするので、両 holdout を合わせた
受理集合が単純に広がるとは言えない。2026-09-17 版と 2026-09-19 版は「片側についての説明」として限定して書く。

## 最新スナップショット以後に確定したこと（stale 注記）

スナップショットは凍結物なので腐る。ここは腐らない入口として、最新版の記述が既に古くなった箇所を
指す。**矛盾があればここが指す一次資料が勝つ。**

**現在この節に積んでいる項目は 11 件である。** いずれも 2026-09-19 版の導出起点 (local main `a99425b66`、2026-09-19 21:41 JST)
より後、同日夜〜翌 2026-09-20 未明に local main へ着地した事実で、同版の記述は執筆時点では真であり、後続で古くなった型である。
同版は凍結物なので書き換えず、ここで指す一次資料が勝つ。**着地の順は同版が作られた wave の受入待ちの間であり、同版の
段 6 レビューはこれらを読んでいない。**

- **A-1 sized attempt-0002 は 1 attempt 認可されたが、既存 submit 経路の gate で qsub 前に拒否され投入されなかった (2026-09-19、
  entry 1687、D2156)。** 同版 §8 の A-1 (「再投入・再認可はユーザー手番で判定されていない」「再投入は行われていない」) と §0 の前進 1・
  §6・§7 の同趣旨は、執筆時点では真であった。ユーザー裁定 (2026-09-19) が「独立再現として 1 attempt を認可、非認証 lane を維持、
  落ちたら再投入せず止める」と定め、投入前照合 21 項目はすべて成立したが、submit は 22:05:30→22:05:36 JST に rc 2、stderr
  `paper-story A-1 refused: prior attempt reached the bench barrier; group rerun is prohibited` (`_assert_no_prior_v3_bench_start`、
  規律 2 由来の防壁、commit `abff80d1b`) で停止した。**測定値は無く、attempt-0002 の results 稿・2 attempt の並記・図は存在しない。**
  gate は緩めず、同じ study の 2 本目をどの経路で投入可能にするかは裁定パッケージ (択 1〜3) として返された。一次資料 =
  `output/insights/2026-09-19/a1-sized-attempt2/README.md`。**同版の「A-1 の値がある」とは書かない扱いと、L-A1S-4 (単一 attempt を
  反復間の安定性へ一般化しない) はそのまま残る。**
- **B-10 静的右 tail の第 2 cohort (独立再現) が完走し、集団判定が出た (2026-09-19、entry 1690、D2157)。** 同版 §8 の B-10
  (「第 2 cohort の地位は未決 (D2050) で再現 cohort の保留は維持 (D2120 項 16)」)、§4 の Fig 8 の注意 (「再現 cohort の保留は維持」)、
  §6・§7・§9 の同趣旨は、執筆時点では真であった。ユーザー決定 (2026-09-19) 「第 2 cohort は独立再現。cohort 1 の verdict を主として
  保持し、cohort 2 の verdict は再現欄に併記。合成しない」を結果を見る前に事前登録 `docs/b10-backoff-static-tail-preregistration.md`
  の末尾追記 (commit `8737cacb4`、22:01 JST) で固定し (D2050 の充足)、group `b10-backoff-grid-20260919T131526Z-2235286`
  (job `10752` / `10753` / `10754`) の集団 `verdict` は `not-observed-in-any-workload` (3 workload とも `not-observed`、18 区間すべて
  `declining`、`failures` 空、正しさ 120 記録 certified・anomaly 0)。**cohort 1 と同じ verdict だが合成せず、言い方は事前登録 §4.5 の
  固定表現に限り、「再現されたので飽和しない」とは書かない。`performance_certified: false` のまま。** 統制稿は
  `results/2026-09-19-b10-static-tail-cohort2.md` (限定 16 件、図は無い — fig8 は cohort 1 の図で、再現欄の追加は別 wave)、一次資料は
  `output/insights/2026-09-19/b10-tail-cohort2/README.md`。**B-10 は閉じていない。**
- **K2 手動 loop の 3 巡目が critic-2 診断入りで実走された (2026-09-19、entry 1691)。** 同版 §0 の前進 9・§2 (c)・§6・§8 の B-6
  (「3 巡目は未実走」「実受領・採用・効果は別の実走で確認する」) は執筆時点では真であった。ユーザー決定 (2026-09-19) 「候補の生成 1 回・
  評価 1 本・同 job の stock 対照 1 本、再投入なし」の縮小走行で、D2155 の診断経路が初めて実走し、critic-2 逐語 → 6 field →
  planner-4 (decrease / large) / coder-4 (`value=10` = 診断の候補値と同じ、既知値列挙外) → job `10761.nqsv` (Elapse 69 秒) が
  serializable / certified / anomalies 0、median 815,983 tps (CV 0.16%)、停止判定 `continue`。critic-3 は帰属不能 (3 巡連続)。
  **診断は既知値 20 / 25 を開示するので「値を見せていない」とは書かず、非同時刻の 3 走 (20 / 25 / 10) は改善・退行の根拠にしない。
  同 job の stock 対照は未達 (縮小走行)。** 一次資料 = `output/insights/2026-09-19/k2-loop-round3/README.md`。
- **B-4 床値 (floor-pair) の w1 が凍結 spec 3 本で実投入され、3 job とも terminal complete で完走した (2026-09-19〜20、entry 1693、
  [T-2288] (b))。** 同版 §2 (c)・§8 の B-4 (「測定そのものは基準 HEAD の時点で始まっていない」) は執筆時点では真であった。実行 HEAD
  `2ba400087` の detached checkout から rr95 `10711.nqsv` / rr50 `10712.nqsv` / rr5 `10713.nqsv` を投入し、初回実配送の証拠 (8 変数・
  walltime・signal・到達段・receipt) を記録した。**w2 と finalize は後続 wave であり、集約発行・採用裁定・§5 記入は行われていない。
  ablation (B-4 本体) は適格な赤 precursor 0 件のまま実施不可である。** 一次資料 = `output/insights/2026-09-19/t2288-floor-pair-w1/README.md`。
- **freeze v2 g1 の chain を main へ運ぶ 2 度目の試みも land せず、記録だけが land した (2026-09-19、entry 1688)。** 同版 §8 の A-4
  (「chain は main に未取り込み、A / X は人間手番、未発効」) は**今も真**であり、ここに積むのは理由が変わった点である — 保存枝
  chain (X1' / X2) と G を merge した木 (三軸走査 hit 4/4 = 設計どおり、焦点走 8 file 0 failed) の受入全走が、B-10 の freeze-tree
  byte pin 1 node (`test_b10_freeze_tree_bytes_match_the_wave_local_gate`) で赤になり、pin 更新は D2120 (b) の射程外として merge 済み
  状態を branch `t2724-chain-land-2-saved` (`0a799da6c`) に保存した。一次資料 = `output/insights/2026-09-19/t2724-chain-land-2/README.md`。
- **mocc の軽量 witness を hook branch に実装し 4 arm × 60 走を実測した (2026-09-19〜20、entry 1696)。** 同版の「観測 3 件」に
  4 件目が加わる。on 0/60・0/60、off 1/60・1/60、discriminator 未発火。非 certifying で、昇格・pin 前進・変異探索は認可されていない
  (ユーザー決定 2026-09-19)。測定は pin `e9e477ca` + [X/P、測定 patch] で TRACE=1 観測専用 (合成 source の TRACE=0 identity は未担保)。
  認可枠 60/arm の検出力は 0.105 で上限として明記。一次資料 = `output/insights/2026-09-19/mocc-witlight-arm-run/README.md`。
  **同版の「根因は未同定」「mocc は第 2 成功例とは書かない」は変わらない。**
- **[T-2773] mocc の auditor-live 相当の機械実証 wave 2 が実走された (2026-09-20、entry 1701、D2159)。** 同版 §8 の C-1
  (「後続は 2 wave」「wave 1 … 正式 template は含まず」) は執筆時点では真であった。ユーザー決定 (2026-09-19) が「mocc 温度述語軸の
  オンボーディング段階 A を承認し wave 2 を認可する。探索および pin 前進は認可しない」と定め、温度述語 template (1 helper・1 hole・
  4 callsite・OFF 原文保存) を `e9e477ca` へ接続し、compute (`11161.nqsv`) で 30 check all_pass、OFF = stock は実 resolver の正規化前処理
  identity で一致・ON-B は別 identity、n=1 の fresh `auditor` 子の判定 (A1' reject / A2' reject / B' pass) を取った。**探索・pin 前進は
  未解禁のまま。** 一次資料 = `output/insights/2026-09-19/t2773-mocc-template-wave2/README.md`。
- **B-5 生成器対照 (K2 loop / ランダム変異 / 機械 sweep) の事前登録 v1 が作られた (2026-09-20、entry 1692、D2158)。** 同版 §8 の
  B-5 (「設計は 3 アームで書かれ、非拘束の設計メモに留めてある (D1012)」) は執筆時点では真であった。`docs/b5-generator-contrast-preregistration.md`
  (v1、**未発効**) が固定 backoff hole の内で 3 生成器を同一評価数で比べる主張の形・評価数予算・score・判定順を結果を見る前に固定した。
  **本走・生成器の実装・D1409 の条件変更は認可されておらず、B-5 の対照は依然として未取得である。** 一次資料 =
  `output/insights/2026-09-19/b5-generator-contrast-prereg/README.md`。
- **A-2 認証系列の `scheduler.nodes=5` が policy に整合された (2026-09-19、entry 1686、[T-2489])。** 同版 §0 の前進 12・§7
  (「基準 HEAD の A-2 policy は `nodes: 1` のまま」「D2148 項 5 の採用裁定は未実装」) は執筆時点では真であった。policy 1 key・literal pin・
  host / nodefile / qsub fixture が同時に整合され、node-local lock の局所候補は計算ノード 2 台の実測 (`9137.nqsv`) で同一ノード内の
  既存排他を失うため**不採用**となった。**A-2 の新しい attempt は走っておらず、A-2 の判定 (`observed-positive`) は動いていない。**
  一次資料 = `output/insights/2026-09-19/t2489-a2-nodes5-local-lock/README.md`。
- **採用候補 fixed 5 µs / fixed 10 µs の検証相 (独立 8 反復 × 3 workload の trace 検証) が走り、両候補とも 24 枠 anomaly ゼロだった — 同版 §8 の B-8「種を変えた長時間実行による最終候補の検証 —【未取得。変化なし】」に関連する追加検証が得られた (2026-09-19〜20、同版の導出後に成立)。B-8 自体を取得済みと書き換えるかは次版で仕分ける。** 2026-09-19 のユーザー裁定により、S-1 事前登録 (iv 付属) の対象 (系側 gate 構成) を採用候補 2 genome へ変え、同節の反復数 (8 × 3 workload)・校正規則 ({3, 6, 10} s、verifier wall ≤ 600 s の最大値)・判定規則 (全件 anomaly ゼロで pass) を**準用**した追加検証を Pegasus gen_S で走らせた (一次資料 = `output/insights/2026-09-20/verify-phase-adopted-backoff/README.md`、単独 results 稿 = `results/2026-09-20-verify-phase-adopted-backoff.md`)。校正で両候補とも extime 3 s に確定し、本走 24 枠 + 校正完走 6 verdict = 30 verify / 候補が すべて `serializable`・certified・anomaly 0 (校正 10 s の未完走 2 件 / 候補は verdict を持たず開示のみ)。**変わらないこと:** これは操作的事実であって 1−εⁿ の確率主張ではなく、性能値を含まず (規律 1)、A-2 / A-6 / [T-1998] の性能判定と既存 certified 記録は昇格も降格もしない (規律 7)。S-1 事前登録本文への「確定値の日付付き追記」は凍結束縛 (`output/s1-freeze/known_axes_freeze.json` の source sha256) により未履行の繰延べであり、同版の「独立した検証相を持たない」という S-1 最終報告の記述も S-1 自身については真のまま。B-8 を「取得済み」と書けるかは、当該 item の要件本文 (種を変えた長時間実行) に対し本検証相 (自己シードの独立反復、extime 3 s) が何を満たし何を満たさないかを次版で仕分ける。fixed-10 の source bytes は A-2 当時と patch 改訂 `91a5bfca3` 分だけ異なる (identity は現行 source に束縛)。
- **同一候補 fixed 5 µs を 3 workload で同一 attempt・同時期に測り、各 workload の同 campaign 内 stock 対照との対差を D1639 の
  between-run 床値と比べた B-7 の材料稿が着地した (2026-09-19、`results/2026-09-19-b7-fixed5-three-workload-regression.md`)。** 同版 §8 の
  B-7 (「材料は事後の併記であって、同一 variant の横断比較と床値超の判定を供給していない」) は執筆時点では真であった。study
  `paper-story-b7-fixed5-regression`、attempt `b7f5-20260919a` (request `10807` / `10808` / `10809`、source `c18a80967`、6 cell × 5 標本、
  限定 14 件、図は無い) は、A-2 / A-6 と同じ certification 経路を descriptive に使った別 study instance で、判定規則 (対差 < −床値 で
  退行、床値 = JSON 全桁) は結果を見る前に固定された (ユーザー裁定 2026-09-19)。機構の outer status は `reject` (3 workload の論理積、
  read-heavy の負の効果の帰結)、稿の床値判定は write-heavy +67.8968% / balanced +12.6717% は退行なし、**read-heavy −11.3787% は床値
  (−0.2228%) 超の退行**。correctness は別の trace-enabled 走行で 6 cell とも certified・anomaly 0 (性能の判定ではない)。
  **B-7 の要件充足は判定しない (D2044 項 3)。既存材料 (2026-09-16 稿、workload 別採用値 10 / 5 / 2 µs) とは表を分けて併記し、プールしない。
  certification の昇格でも有意差判定でもない。** 一次資料は同稿が指す権威 bytes。

2026-09-19 版は同日 21:41 JST の local main
(`a99425b66`、worklog entry 1685 までの fold を含む) から導出している。前版 (2026-09-17 版) に対して積んでいた
3 項目は、いずれも 2026-09-19 版が本文へ取り込んだのでここから外した。移管先は次のとおりである。

1. **Silo 固定スコープの解除 (D2114、2026-09-17)** → 同版 §0 の前進 3、§1 (スコープの段落)、§2 (b) 項 1、§6 の
   「言えること」と「言えないこと」、§7、§8 の C-1。方針と準備の着手だけが変わり、事実 (非 Silo の性能比較 0 件、
   pin `511c9538`) は変わっていないと書き、「広げた」「選定が成立した」「mocc は第 2 成功例」とは書かない。
2. **B-10 静的 backoff 右 tail 09-15 正式 cohort の論文図 fig8 (2026-09-17)** → 同版 §0 の前進 5、§2 第 2 幕の機序の項、
   §3 の項目 4、§4 (表の Fig 8 行と「Fig 8 について守ること」)、§6、§8 の B-10、§9 の第 4 種。言い方は事前登録 §4.5 の
   固定表現に限り、`performance_certified: false`、図の成立で B-10 は閉じず再現 cohort の保留は維持 (D2120 項 16)。
   前版と results 稿の「図は無い」は当時は真として書き換えない。
3. **A-1 balanced5 sized 本走の attempt-0001 の完走 (2026-09-18) と単独稿・fig9** → 同版 §0 の前進 1、§2 第 2 幕の
   測定契約の項、§2 (f) の第 4、§3 の項目 4、§4 (表の Fig 9 行と「Fig 9 について守ること」)、§6、§7、§8 の exact claim と
   A-1、§9 の第 4 種。非認証 lane の descriptive 出力として置き、「A-1 の値がある」とは書かず、A-1 の充足・formal 化・
   再投入・再認可は未判定 (ユーザー手番、D2044 項 8 / D2120 項 3) と書く。claim-evidence 稿の A-1 行は凍結物として不変。

**積んでいる項目の数は「最新版に誤りが有る」ことも「無い」ことも保証しない。** 上の 9 件はいずれも「当時は真で後続が古くした」型であり、執筆時点の誤りではない。2026-09-19 版は前版の執筆時点の誤りを 0 件と判定したが、2026-09-17 版が自分の前版に
執筆時点で既に偽だった記述を 3 件 (前版の冒頭) 見つけた型の誤りは、最新版にもありうる。
**次に正典が動いたら、その項目をここへ積む。**
**項目が積まれること自体は、新しい日付の版を作る要求にはならない** (D1858)。

**恒久の erratum は別の場所にある。**
`figures/fig2_backoff_mechanism.png` の baseline 誤 label（横破線に `stock adaptive backoff` と
書いてあるが、その値は無 backoff）と後継図 `figures/fig2b_backoff_sweep_3workload` への
乗り換え指示は、腐らない入口として `figures/README.md` が持つ。**旧図と、旧図を載せた
2026-07-10 版・2026-08-23 版のキャプションは凍結物なので訂正しない。**
**論文で P2-4 の図を使うときは後継図を使い、旧図を使わない。**

`figures/fig5_a2_certification_reject` の測定条件 erratum も同じく `figures/README.md` の fig5 節が持つ
(2026-09-07、D1645)。図が実際に比較したのは採用静的 backoff ではなく `BACK_OFF` の有効/無効であり、
**論文の A-2 の結論にも図にも使わない。** 図と provenance の bytes、キャプション正文は
凍結物なので訂正しない。
**取り直した attempt は 2026-09-07 に取れた (`t2364-20260907b`、outer `observed-positive`) が、
この制限は解除されない** — 下の追補が定めるとおり期限なしである。**新 attempt の図は
`fig6_a2_certification_observed_positive` であり、`fig5` の後継図ではない。**

**旧 fig5 の用途制限への追補 (2026-09-11、D1936項21・T-2521)。** 上記の D1645 に由来する
「取り直しまで」「正しい identity で取り直した attempt」という期限は、当該旧図には適用しない。
**採用静的 backoff に関する A-2 の結論・図として使えない制限は期限なしである。** 新 attempt の取得は、
旧図が比較した `BACK_OFF` の有効/無効を変えない。旧図の利用範囲は訂正済みの当時の測定対象と判定に
限る。詳細は `figures/README.md` の「追補 — 旧 fig5 の用途制限に期限を設けない」を正本とする。
旧画像・provenance JSON・統計・凍結稿・キャプション正文は保持する。

## 読み方

- 論文執筆・ポジショニング検討のときに読む。日常セッションのブートには不要（ブートコスト規律 D35）。
- 各版の §（過大主張チェックリスト）は執筆フェーズで消し込み式に運用してよい唯一の例外。
- **旧 Phase 3 主実験（phase3.md 後続段 6）は 2026-07-16 に完了し、縮小主張 S' は不成立で
  確定した。** 「主実験が成立すれば headline がそちらへ移る」という以前の見通しは、
  そのままでは使えない（正本 = `output/reports/s_prime_final_report.md`、
  および最新版の §2 第 3 幕 (a) と §6）。新しい headline 候補が実際に成立したときは、
  その時点で新しい日付のスナップショットを追加する。

## claim-evidence 系列（`claim-evidence/` サブディレクトリ）

**版とは別系列の、執筆者向けの作業表を置く場所。** 版が「その時点で何を語るか」を書くのに対し、
こちらは「主張 1 件ごとに、何を書けて、何がそれを弱めているか」を並べる。
版と混ぜないために **filename ではなくディレクトリで分ける。**

| 日付 | ファイル | 内容 |
|---|---|---|
| 2026-08-26 | `claim-evidence/2026-08-26.md` | claim-evidence matrix（科学的主張 / 運用・方法論の証拠 / 文献 guardrail の 3 表）、限定レジストリ `L01`〜`L28`、limitations 節の日本語統制稿 |

**T-1998 単独稿の読解上の追補 (2026-09-18、回収時の独立監査):**
`2026-09-18-t1998-balanced-stock-inline-accepted.md` §0.1 の「投入は 1 回だけ」「2 本目の試行は存在しない」は、
指定 receipt と 2026-09-13 / 09-15 の wave 記録から確認した 1 試行を指す。他の投入の不存在を網羅的に
保証するものではない。事前登録 §7 は投入回数の規則であり、不存在の証拠ではない。凍結稿・測定値・consumer 判定は保持する。

**この系列の規則。**

- **append-only。書いた後は更新しない。** 版と同じ凍結物である。
- **新しい日付を足すときは、入力 5 節（最新版の §3 / §6 / §7 / §8 / §9）全体から作り直す。**
  一項目だけを直した差分改訂を新しい日付として置かない（版と同じ理由 — 更新しなかった項目の
  stale が「その日付時点でそう主張した」という新しい嘘に変わる）。
- **「版の履歴」表には登録しない。** これは版ではない。どちらが全面再導出された版かは
  ディレクトリで判別する。
- **数値・日付・判定の出所は一次資料だけとする。** 版の記述を数値の出所にしない。
- 版と同じく `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外である。

**C14a の所在調査の追記 (2026-09-18、[T-1878])。** 2026-08-26 稿は変更せず、今回の探索結果をここに記録する。claim-evidence matrix の
新稿ではない (一項目だけを直した新しい日付の稿は規則 2 が禁じる)。矛盾があれば下で指す一次資料が勝つ。

- **C14a の `[権威 bytes]` は 2026-09-18 時点でも未特定 — 探索した範囲での未特定であり、全体での不在の断定ではない。**
  2026-08-26 稿の C14a 行 (mocc trace-hook TRACE=1 pilot、PBS `934607.nqsv`、outer `2efe6282`) が `[権威 bytes]` を「未特定」と書いた件を、
  pilot の insight 5 群が名指す job dir 9 件、`/work/1/SFC/tanab/izanagi-job-evidence/` 配下、`tools/pegasus/mocc_trace_pilot.sh` の出力先に
  限って探索した結果、raw `verifier.json` もその sha256 も特定できなかった。当時の script の出力先は投入 worktree
  (`dev-wave-t755-mocc-trace-execution`) 配下の `output/env/pegasus/mocc-trace/job-staging/$PBS_JOBID/` (request 934607 の実表記は
  `934607.nqsv` か `0:934607.nqsv`) で、同 worktree は現在存在しない。探索時点の全 ref から辿れる履歴に同 path を触る commit は無く、
  evidence dir と名指し job dir (50 MiB 以下の全 file の本文と path 名) にも raw も退避物も特定できなかった。当時の receipt 生成処理は
  `verifier.json` を名前で指すだけで sha256 を束縛していなかった。消失の経緯と過去の保存履歴は確定していない。insight に埋め込まれた
  JSON block は raw の逐語ではない (当時の verifier `--json` が出す `trace_dir` など 3 key を欠く) ので、その sha256 を `[権威 bytes]` の
  代わりに書くこともできない。一次資料 = `output/insights/2026-09-18/t1878-mocc-trace-pilot-raw-artifact/README.md` (探索範囲・方法・
  結果と、探索していない範囲)。**変わらないこと:** C14a の判定値 (`serializable` / `certified` 真 / anomaly 0) と `[導出索引]` は
  2026-08-26 稿のままで、C14a を引くときは「raw artifact 未特定 (insight 転記のみ)」の限定を外さない。2026-08-26 の pair wave の
  TRACE=1 leg (`0:949961.nqsv` / `0:949963.nqsv`) には raw と sha256 があるが、別 request の観測であり C14a の行に流用しない。

## results 系列（`results/` サブディレクトリ）

**版とも claim-evidence とも別の、結果 1 件ごとの結果節の材料を置く場所。** 版が「その時点で何を語るか」、
claim-evidence が「主張ごとに何を書けて何が弱めているか」を書くのに対し、こちらは
**完走した 1 つの protocol / campaign の結果を、論文の結果節・表・図・限定の形へ落とした統制稿**を置く
（一次資料に束縛した執筆者向け統制稿。D12 が定める機械射影の材料レポートではなく、投稿本文でもない）。
版と混ぜないために **ディレクトリで分ける** (D1013 と同じ理由)。

| 日付 | ファイル | 対象 | protocol status |
|---|---|---|---|
| 2026-09-04 | `results/2026-09-04-a2-certification-reject.md` | A-2 正式 certification (attempt `t2022-20260828c`、write-heavy / balanced の exact 4 cell、図 5、限定 11 件) | outer `reject`。correctness は別の trace-enabled run で 4 cell とも certified (性能の判定ではない)。**測定条件の記述に誤りがあり、2026-09-07 の稿が改めた (下記)。執筆材料には使わない** |
| 2026-09-07 | `results/2026-09-07-a2-certification-reject.md` | 同じ attempt `t2022-20260828c` を一次資料全体から作り直した改訂稿。**測ったのは採用静的 backoff ではなく CCBench 内蔵 backoff の有効/無効** (`BACK_OFF=1` 対 `0`) である。限定 15 件 (D1645、F707 の再発) | outer `reject` は不変。**同じ attempt の執筆材料にはこの稿を使う。**2026-09-04 の稿は append-only の履歴として残る |
| 2026-09-07 | `results/2026-09-07-a2-certification-observed-positive.md` | D1644 の pin + patch 束縛 `src_token` で identity を計算する driver で取り直した**別の attempt** `t2364-20260907b` (write-heavy / balanced の exact 4 cell、図 6、限定 6 件)。上の 2 行とは測っている条件が違い、前後比較として読んではならない (絶対規律 7) | outer `observed-positive`。correctness は別の trace-enabled run で 4 cell とも certified (性能の判定ではない)。**この attempt の執筆材料にはこの稿を使う** |
| 2026-09-09 | `results/2026-09-09-a2-certification-observed-positive-en.md` | 直上の 2026-09-07 observed-positive 稿の**英語稿**。同じ attempt `t2364-20260907b` について、事実命題を足さず一次資料へ再照合して英語で書き直したもの ([T-2329]) | outer `observed-positive` (直上の稿と同一)。日本語稿を改めるものではなく、どちらも凍結物として残る |
| 2026-09-14 | `results/2026-09-14-b7-all-workload-regression.md` | 見送り台帳の項目 B-7 (全 workload の退行込み報告) の材料。現行環境・正式 protocol で判定の出ている 3 workload の 6 cell を、**2 つの attempt に分かれた記録のまま横断で併記する** (`t2364-20260907b` の rr5 / rr50 と `a6-20260908b` の rr95、生標本 6 cell、限定 11 件)。単位は失敗条件 (e) が報告を求める「全 workload」の集合。**2 attempt を統括する単一の正式実験は存在しない** | 単一の outer status を持たない。所属 attempt の status をそのまま併記する (rr5 / rr50 は `observed-positive`、rr95 は `reject`)。**B-7 の充足も床値超の退行も判定せず、D1645 の解除は 2026-09-14 版の判定を引き写すだけである** |
| 2026-09-16 | `results/2026-09-16-b7-three-run-materials.md` | 同じく見送り台帳の項目 B-7 の材料。**直上の 2026-09-14 稿が対象外とした [T-1998] の balanced stock-inline 対を加え、3 走行・4 対比較・8 arm を一次資料から作り直して併記する** (`t2364-20260907b` の rr5 / rr50、`a6-20260908b` の rr95、別事前登録 v1 の balanced 対、生標本 8 arm、限定 20 件)。**直上の稿を改めるものではない** — 同稿は 2 attempt・6 cell の材料として有効なまま残る。3 走行を 1 file に収めたのは編集判断であり、系列の規則がそれを要求しているわけではない | 単一の outer status を持たない。所属する走行の出力をそのまま併記する (rr5 / rr50 は A-2 outer の `observed-positive`、rr95 は A-6 outer の `reject`、[T-1998] は consumer の `accepted`。producer 側の `complete` とは別)。**D1993 項 6 に従い 3 走行をプールせず、B-7 の充足も床値超の退行も判定しない。A-1 が定める横断実験の代わりにもしない** |
| 2026-09-16 | `results/2026-09-16-b10-static-tail-not-observed.md` | 見送り台帳の項目 B-10 (機序説明の帯域外への拡張) のうち、静的 backoff 右 tail の本走 1 cohort (group `b10-backoff-grid-20260915T061814Z-545445`、`run_kind` `t2500-tail-formal`、事前登録 `docs/b10-backoff-static-tail-preregistration.md` の commit `cad6f46d8` に束縛、3 workload × 8 点 = 24 cell、性能 120 rep・正しさ 120 記録、生標本 24 cell、限定 15 件)。**言い方は事前登録 §4.5 の固定表現に限る** — 「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」。「飽和しない」「飽和点が存在しない」とは書かない。図は無い (`fig2c` は別 cohort)。**この cohort の執筆材料にはこの稿を使う** | 集団 `verdict` は `not-observed-in-any-workload` (3 workload とも `not-observed`、18 区間すべて `declining`、局所平坦区間 0、`failures` 空)。correctness は trace-enabled の別走行で 120 記録とも certified・anomaly 0 (性能の判定ではない)。**`performance_certified: false` のままで、性能値を採用根拠にしない。機序・9999 マイクロ秒より右・他 cohort との関係は書かない** |
| 2026-09-18 | `results/2026-09-18-a6-certification-reject.md` | A-6 read-heavy 正式 certification (attempt `a6-20260908b`、request `982234.nqsv`、2026-09-08、rr95 の exact 2 cell = stock `BACK_OFF=0` 対 採用静的 backoff 2 µs、生標本 2 cell、限定 12 件、図は無い)。**1 attempt の一次資料全体 (権威 bytes・raw manifest・WAL・受領証・裁定) から作った単独稿**で、同じ rr95 の値を併記する横断稿 (2026-09-14 / 2026-09-16 の B-7 稿) を出所にしない ([T-2611])。B-10 read-heavy 本走 3 block との同符号・同程度は近接条件の別実行による履歴的照合であって再現ではなく、反復 attempt は行わない ([T-2430])。実行基盤測定の −4.876% は attempt に数えない (D1870)。限定は D1993 項 3 の (i)〜(iv) に identity 層の (v) ([T-2630]、D2108) を加えた 5 つを含む | outer `reject` (効果 −5.7841%、`a4_noise_floor_status` は `open`、有意差判定なし)。correctness は別の trace-enabled 走行で 2 cell とも certified (性能の判定ではない)。**性能の `reject` は正しさ証拠の欠落ではない (D1993 項 2)。この attempt の執筆材料にはこの稿を使う** |
| 2026-09-18 | `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` | A-1 balanced5 sized 本走 attempt-0001 (study `paper-story-a1-20260901-balanced5-sized-v1`、job `4939` / `4940` / `4941`、2026-09-18、source `d2ebef7a4`、3 workload × 30 対 × 2 arm = 生標本 180、限定 20 件、図 9)。**1 attempt の一次資料全体 (公開 leaf の result.json / receipt.json / .complete.json、campaign WAL 3 本、事前登録、policy v3、裁定) から作った単独稿**で、stale 注記・記録 insight・版を数値の出所にしない ([T-2611] / [T-2674] の型)。登録済み解析の descriptive 出力 (対差平均 ± h と床 ±B の分類) を書き写す。**A-1 の充足・formal 化・再投入・再認可は判定しない** (認可はユーザー手番、D2044 項 8)。図 9 は本稿を `caption_source` として束縛するので、稿は provenance の sha256 を持たない (F36、正本は `figures/README.md` の fig9 節) | 単一の outer status を持たない非認証 lane (`formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only`)。登録済み解析の分類は 3 workload とも `resolved-above-floor` (対差平均の符号 write-heavy 正 / balanced 正 / read-heavy 負、`variance_plan_breach` false ×3)。correctness は別の trace-enabled verify で 6 arm とも certified・anomaly 0 (性能の判定ではない)。**headline 値・workload 横断の結論・C1 の再現判定にせず、単一 attempt を反復間の安定性へ一般化しない。この attempt の執筆材料にはこの稿を使う** |
| 2026-09-18 | `results/2026-09-18-t1998-balanced-stock-inline-accepted.md` | [T-1998] balanced の stock-inline 対 (無 backoff 対 静的 fixed 5 µs) の**単独稿**。事前登録 `docs/t1998-balanced-stock-inline-preregistration.md` v1 の下の 1 試行 (job `995755.nqsv`、測定 2026-09-13、認証 2026-09-14、着地後 main での再解析 2026-09-15) を、2026-09-16 の横断稿から引き継がず一次資料 (権威 bytes・campaign lock と WAL・事前登録・裁定) から作り直した ([T-2674]、D2120 項 15 の型)。生標本 2 arm、限定 20 件。成果物に無い情報・束縛の範囲・本稿で未照合の対応は §4 に区別して明記。図は無い | consumer の **`accepted`** (reason `preregistered-balanced-stock-inline-pair`、ratio 1.1122537536191646、improvement_percent 11.225375361916456)。producer 側の `complete` とは別の出力。**各 arm 5 標本の median 比であって A-1 の対差平均ではなく、A-2 / A-6 とプールせず (D1993 項 6)、B-7 の要件充足でもない (D2044 項 3)。有意差判定でも区間推定でもない。** correctness は campaign WAL の `verify_done` で 2 arm とも `serializable` / `certified` / anomaly 0 (legacy 条件 1 回ずつ。性能の判定ではない) |
| 2026-09-19 | `results/2026-09-19-b10-static-tail-cohort2.md` | 見送り台帳の項目 B-10 (機序説明の帯域外への拡張) の静的 backoff 右 tail について、**主結果 (2026-09-16 稿の cohort 1) に対する独立再現 = 第 2 cohort** (group `b10-backoff-grid-20260919T131526Z-2235286`、`run_kind` `t2500-tail-formal`、job `10752` / `10753` / `10754`、2026-09-19、事前登録の 2026-09-19 追記込み commit `8737cacb4` に束縛、3 workload × 8 点 = 24 cell、性能 120 rep・正しさ 120 記録、生標本 24 cell、限定 16 件)。地位は結果を見る前に事前登録追記 (D2050 の充足、ユーザー決定 2026-09-19) で固定: cohort 1 の verdict を主として保持し、第 2 cohort の verdict は再現欄 (同稿 §2.6) に併記、**合成しない**。投入時に失敗した attempt 1 (依存 source 不在、測定なし) を §1.5 に開示。file 名は結果前に中立名で固定。**2026-09-16 稿を改めるものではない**。図は無い (fig8 は cohort 1 の図。再現欄の追加は生成器の改変を要し別 wave) | 集団 `verdict` は `not-observed-in-any-workload` (3 workload とも `not-observed`、18 区間すべて `declining`、局所平坦区間 0、`failures` 空)。cohort 1 と同じ verdict だが、**言い方は事前登録 §4.5 の固定表現に限り「再現されたので飽和しない」とは書かない**。correctness は trace-enabled の別走行で 120 記録とも certified・anomaly 0 (性能の判定ではない)。**`performance_certified: false` のままで、性能値を採用根拠にしない。2 cohort の統合 verdict・プール推定・またぐ有意水準は作らない** |
| 2026-09-19 | `results/2026-09-19-b7-fixed5-three-workload-regression.md` | 見送り台帳の項目 B-7 の材料。**同一候補 (静的 backoff fixed 5 µs = T-1998 事前登録の採用 arm と同じ genome・同じ source bytes digest) を 3 workload で同一 attempt・同時期に測り、各 workload の同 campaign 内 stock 対照との対差を D1639 の between-run 床値と比べた単独稿** (study `paper-story-b7-fixed5-regression`、attempt `b7f5-20260919a`、request `10807` / `10808` / `10809`、2026-09-19、source `c18a80967`、6 cell × 5 標本、限定 14 件、図は無い)。A-2 / A-6 と同じ certification 経路を descriptive に使った別 study instance で、既存 2 policy は不変。既存材料 (2026-09-16 稿、workload 別採用値 10 / 5 / 2 µs) とは表を分けて併記し、プールしない。**判定規則 (対差 < −床値 で退行、床値 = JSON 全桁) は結果を見る前に固定** (ユーザー裁定 2026-09-19) | 機構の outer status は `reject` (3 workload の論理積、read-heavy の負の効果の帰結)、`a4_noise_floor_status` は `open`。稿の床値判定: write-heavy +67.8968% / balanced +12.6717% は退行なし、**read-heavy −11.3787% は床値 (−0.2228%) 超の退行**。correctness は別の trace-enabled 走行で 6 cell とも certified・anomaly 0 (性能の判定ではない)。**B-7 の要件充足は判定しない (D2044 項 3)。certification の昇格でも有意差判定でもない。この attempt の執筆材料にはこの稿を使う** |
| 2026-09-20 | `results/2026-09-20-verify-phase-adopted-backoff.md` | 採用候補 2 genome — fixed 5 µs (T-1998 v1 target = A-2 rr50 採用値) と fixed 10 µs (A-2 rr5 採用値) — の**検証相** (trace-enabled build、write-heavy / balanced / read-heavy 各 8 独立反復、extime 3 s、計 48 verify + 校正 18 記録 (実走 16)、Pegasus gen_S、2026-09-19〜20)。S-1 事前登録 (iv 付属) の充足ではなく、2026-09-19 のユーザー裁定で対象を変え同節の反復数・校正規則・判定規則を**準用**した追加検証。identity は現行 patch の source digest に束縛 (fixed-5 は T-1998 v1 と bytes 一致、fixed-10 は A-2 と同 genome だが source bytes は `91a5bfca3` 分だけ異なる)。限定 9 件。図は無い。**この検証相の執筆材料にはこの稿を使う** | 候補ごとに runner の機械判定 **`pass`** (判定集合 30 verify = 本走 24 + 校正完走 6、全件 `serializable`・certified・anomaly 0。校正 10 s の未完走 2 件は verdict を持たず開示のみ)。操作的事実であって 1−εⁿ の確率主張ではなく、性能値を含まない (規律 1)。A-2 / T-1998 / A-6 の certified 記録の昇格・降格はしない (規律 7) |
| 2026-09-20 | `results/2026-09-20-mocc-g2-observation-conditions.md` | stock mocc の G2 signal の**観測条件の分離** ([T-2779]、runner v5 `t2779_probe.py` の非 certifying 観測 1 試行 = 段 4 裁定で結果を見る前に固定した単一の観測 protocol の完走、witness off に固定した 3 arm = 通常 X/P 計装 / 診断 patch / `BACK_OFF=1` × 4 block (request `5894` / `5895` / `5897` / `5898`、2026-09-18) × 30 round = 各 arm 120 走、固定 cell 3 s・48 thread・10,000 record・rratio 50・zipf 0.9、producer = hook branch 先端 `e9e477ca` + X/P 計装 patch (D1686)、TRACE=1 観測専用、限定 18 件、図は無い)。**1 試行の一次資料全体 (job dir の 4 block `result.json`・360 走の run / verifier JSON・G2 7 走の trace-manifest と生 trace 336 file・段 4 裁定 = 事前登録・dispatch の NQSV 要約、insight の `summary.json`) から作った単独稿**で、横断稿・版を数値の出所にしない ([T-2611] / [T-2674] の型)。限定を先頭に置く: 非 certifying・TRACE=1 観測専用・pin 前進なし (D2150 項 1 は承認済み未実施、D2159 は認可しない)・頻度差から `BACK_OFF=1` の抑制効果や正しさを結論しない・G2 signal の再現を根因確定としない (D2148 項 13 = [T-2791] の限定)。witness 軽量化の静的設計とその後の実走は本稿の対象外 | 単一の outer status を持たない非 certifying 観測。runner の機械集計 (`summary.json`) は **通常 5/120 (CP 95% [1.3665%, 9.4559%])・診断 0/120 ([0%, 3.0273%])・`BACK_OFF=1` 2/120 ([0.2025%, 5.8909%])**、介入側が低下する方向の片側 Fisher (未調整) は診断 0.0299507441 / backoff 0.2230864755。事前登録の言い方は前者「固定条件で 2 変更を束ねた介入と検出率低下が整合する」まで、後者「この標本・条件では低下を検出できない」まで。family 全体の有意性・G2 不在・根因同定は主張しない。7 件の signal は全件 G2・長さ 2・両辺 rw、生 trace 保全済み、discriminator は全走 `not-run` (witness off)。certified 昇格・pin 前進・変異探索・規律 2 の即 reject 契約は不変 |
| 2026-09-20 | `results/2026-09-20-mocc-witlight-four-arm.md` | stock mocc の軽量 witness (hook commit W `5b02546f`、branch `izanagi-t1943-mocc-g2-witlight`、`e9e477ca` の子、GitHub 未 push) を実装した wave の**本走 4 arm (witness on / off × BACK_OFF 0 / 1) × 各 60 走** (4 block = request `10827` / `10828` / `10835` / `10837`、2026-09-19 22:35〜23:02 JST、pin `e9e477ca` + [X/P、測定 patch] の TRACE=1 観測専用 build、smoke 4 走は分母外、限定 11 件、図は無い)。**1 wave の一次資料全体 (job dir の走ごとの JSON・集計・会計・事前登録・検査 log・hook commit の git object、記録 insight の逐語) から作った単独稿** ([T-2611] / [T-2674] の型) で、README 追補 (entry 1696)・worklog・版を数値の出所にしない。書くのは「この診断で何を識別できたか」(同稿 §2.8): 4 arm の完全収載、on 0/60 ×2、off 1/60 ×2 (G2・長さ 2・両辺 rw)、discriminator 未発火 (問い (ii) は識別対象 0 件で未到達)、W の TRACE=0 preprocess identity、smoke 正例の witness 文法、曝露量 on/off 0.864 / 0.845。検出力 0.105 は off 率 0.0417 ([T-2779] 通常 arm) 対 0 の完全抑制・片側 α=.05・K=60 の条件付き計算で上限として明記 (「80%」は率 0.119 の条件付き計算)。smoke 合格集合は結果前固定。mocc の稿はこれが最初 | 単一の protocol status を持たない**非 certifying の観測記録**。主比較 (BACK_OFF=0) も副比較 (BACK_OFF=1) も on 0/60 対 off 1/60、片側 Fisher 未調整 **p=0.500**、discriminator 発火 0 件。**p=0.500 と on 側 0 件を同等性・効果なし・G2 不在の証明にしない。TRACE=1 観測専用 (合成 source の TRACE=0 identity は未担保)。certified 昇格・pin 前進・変異探索は認可されていない (ユーザー決定 2026-09-19)。commit 数の比は曝露量であって性能主張ではない (規律 1)。[T-1892] / [T-2774] / [T-2779] と合算しない (規律 7)。個別 verifier の `certified=true` 238 件は認証ではない** |

**この系列の規則。**

- **append-only。書いた後は更新しない。** 版と同じ凍結物である。誤りが見つかったら新しい日付の file を足し、旧 file は残す。
- **1 file = 1 結果 (1 protocol または 1 campaign 群の完走)。** 新しい日付を足すときは、その結果の一次資料全体
  (権威 bytes・raw manifest・WAL・裁定) から作り直す。一項目だけを直した差分改訂を新しい日付として置かない。
- **「版の履歴」表には登録しない。** これは版ではない。
- **数値・日付・判定の出所は一次資料だけとする。** 版や claim-evidence の記述を数値の出所にしない。
  図を伴うときは `figures/` の凍結物と provenance JSON を指し、図の値と表の値は同じ生値から同じ計算で出す。
- **protocol status (`reject` 等) は protocol の出力として書き、研究としての成功・失敗・新規性の宣告へ拡張しない** (D12)。
  性能・別走行の正しさ・旧系列との関係の段を 1 文へ畳まない (最新版 §7 の区別の規律)。
- この系列の文書は**執筆者向けの統制稿**であり、D12 が定める機械射影の材料レポートではない。数値は図の provenance JSON から転記し、
  転記元の SHA-256 を文書に書く。散文は執筆者の判断を含む。
  ただし `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` は、図9が本稿を `caption_source` として束縛するため、
  数値と転記元の SHA-256 を公開 leaf の `result.json` から得る個別の扱いとする。自己参照を避けて図の provenance の SHA-256 は
  `figures/README.md` の fig9 節に置き、図と稿の値の対応は `test_plot_a1_sized_paired.py` で検査する (F36)。
- 版と同じく `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外である。

## 運用ルール（check_docs.py との関係）

- 本ディレクトリの文書は追記型の凍結記録なので `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外。
- 他文書からは**ファイル名（basename）で参照**する（行番号参照は禁止・節名参照にする、check_docs.py 準拠）。
