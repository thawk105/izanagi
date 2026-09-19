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

**最新 = `2026-09-17.md`。** 図は `figures/` に、2026-07-10 版の作成時に気づいた示唆は
`notes-2026-07-10.md` に分離。`figures/fig3_arc_status.png` は 2026-07-10 版（Phase 3 段 5 時点）の
現況図であり、2026-08-23 版以降の第 3 幕の記述とは一致しない（各版 §0 に明記）。

**この節は最新版の訂正だけを載せる。** 旧版が自分の前版をどこで訂正したかは、その旧版自身の
冒頭が持つ（凍結物なので、訂正の一覧も版と一緒に凍結されている）。

**2026-09-17 版が前版 (2026-09-14 版) を訂正した箇所は 3 つ。** いずれも同版の冒頭と該当節に理由がある。
**3 つとも、前版が書かれた 2026-09-14 の時点で既に偽だった記述である** (後日状況が変わったのではない)。
凍結物である 2026-09-14 版は書き換えていない。前版が自分の前版 (2026-09-05 版) を訂正した 4 か所は、
2026-09-14 版自身の冒頭が持つ。

1. §1・§2 第 3 幕 (c)・§3 の項目 3・§6・§7・§8 の B-9 — 計 6 箇所で、bench-first screening campaign を
   層3 の対象外あるいは未対応として扱っていた。**誤りである。** 対応は 2026-08-25 の [T-1291] で
   schema の 2 段の変更 (`b8318b956` / `ed251424d`) により着地しており、2026-08-26 版から 4 版続けて
   運ばれた (F1 の再発、entry 1539)。**B-9 という項目は閉じていない** — 残る 2 項は「裁定で停止」と
   「発効条件待ち」である。
2. §0 の前進 7・§2 (c)・§5・§6・§7・§8 の A-4 — official 床値 campaign の史上初の実投入を
   「2026-09-11」と書いていた。**日付が誤りである。** 一次記録
   (`output/insights/2026-09-09/t1851-unit-c3b-floor-range/README.md`) は request `988501.nqsv` の投入を
   **2026-09-09 22:09 JST** と記録している。通過した gate・停止した gate の記述は正しかった。
3. 冒頭の「取り込まなかったもの」・§0 の前進 7・§2 (c)・§2 (g)・§6・§7・§8 の A-4・§9 —
   「D1341 により意図的に land されていない [T-1851] の実装単位群」と書いていた。**前版の執筆時点で
   既に偽だった。** D2 単位の統合 commit `ce2769c32` (2026-09-10) は前版の起点 `af3762d62` の祖先であり、
   entry 1450 (2026-09-11) が一括 land を記録している。**D1341 の裁定そのものは有効である。** 誤ったのは、
   過去の worklog の「land しない」を現況へ転写したことである。

前版が B-2 の `delta_min` について「受理集合を広げる向き」と書いた箇所は、誤りとは断定しない。
D2049 が定めるとおり、逆対応の逐語適用は片側の境界を過小に、他方を過大にするので、両 holdout を合わせた
受理集合が単純に広がるとは言えない。2026-09-17 版は「片側についての説明」として限定して書く。

## 最新スナップショット以後に確定したこと（stale 注記）

スナップショットは凍結物なので腐る。ここは腐らない入口として、最新版の記述が既に古くなった箇所を
指す。**矛盾があればここが指す一次資料が勝つ。**

**現在この節に積んでいる項目は 3 件である。**

- **Silo 固定スコープの解除 — 合成対象を Silo に限定する方針は現在の方針ではない (2026-09-17、同版の導出後
  に確定)。** 同版 §1 の「2026-07-27 のユーザー裁定でスコープは Silo ベースに固定されている」と、§8 C-1 の
  理由にある「2026-07-27 裁定で Silo ベースに固定した以上」は、2026-09-17 の改訂 (一次資料 = `docs/phase3.md`
  の「2026-09-17 改訂」節と、そこが指す `output/insights/2026-09-17/cross-protocol-scope-release/README.md`)
  により**現在の方針ではない**。**C-1 を将来スコープとする結論は維持する** (狙う増分主張は「指定した二つの
  CC 実装で合成・評価手順を実証した」に限り、その第 2 例の証拠と C-1 の protocol 横断 stock 最良比較は別項)。
  変わったのは方針と準備の着手だけであり、**事実は変わっていない**: 非 Silo (mocc / tictoc / cicada) の性能比較は
  0 件、認定較正は mocc / tictoc の rr50・rr95 各 2 件で cicada は 0 件 (較正は物差しであって性能選定ではない)、
  mocc の証明面計装は現行 pin の祖先ではない、pin 前進は未承認 (D1603 の材料 3 点が揃った時点で [T-167] の
  再承認として提示)、mocc を変異探索面へ入れるには D579 の独立実証が要る。したがって **§6 の「広げた」「選定が
  成立した」とする主張の禁止、および §7 の空間登録や較正を拡張実証と扱わない規則は、証拠の現況に基づくため
  引き続き有効である。**

- **B-10 静的 backoff 右 tail 09-15 正式 cohort の論文図 fig8 が成立した — 同版と results 稿の「図は無い」は
  当時は真であり、後続で古くなった記述である (2026-09-17、同版の導出後に成立)。** 同版 §4 の表の行
  「B-10 右 tail 09-15 cohort の図 (未作成)」(同じ趣旨の「図は無い (§4)」は §0 の前進 2 と §8 の B-10 に、
  「未作成の予定仕様」は §10 の段 3 にもある) と、results 稿 `results/2026-09-16-b10-static-tail-not-observed.md`
  §0.3 の「09-15 cohort を描いた図は存在しない」および §3 限定 11「論文図は無い」は、執筆時点では真であった。
  2026-09-17 に [T-2647] の wave が同版 §4 の予定仕様どおりの図を作り、local main に着地した (一次資料 =
  `output/insights/2026-09-17/t2647-b10-tail-fig8/README.md`、実装 commit `4636181a9`、段 6 fix `ce39429d5`)。
  本体系列 `figures/fig8_b10_static_tail_not_observed.{png,pdf,provenance.json}` (着地 bytes の SHA-256: PNG
  `24eab2e8…`、PDF `11071b72…`、provenance JSON `3ccdb0aa…`)、生成器 `tools/plotting/plot_b10_static_tail_formal.py`。
  caption・proof chain・入力 3 file の SHA-256 束縛の正本は `figures/README.md` の fig8 節。図は group
  `b10-backoff-grid-20260915T061814Z-545445` (集団判定 `not-observed-in-any-workload`) の**記述図**であり、
  `fig2c` の続きではなく、2 本目の論文と共用しない (D1637)。**言い方は事前登録 §4.5 の固定表現に限る** —
  言えるのは「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」までであり、
  「飽和しない」「飽和点が存在しない」とは書かない。**図の成立で変わらないこと:** `performance_certified: false`
  は動いていない (性能認証ではなく、この図を variant 採用の根拠にしない — 絶対規律 2)。B-10 も [T-2647] も
  閉じていない。D2104 項 7 (B-10 右 tail の再現 cohort は今は走らせない) も解除されていない — 同項は理由の
  一つに「結果を使う下流 (論文図) が未成立」を挙げるが、決定は優先順位の判断であり、**D2120 項 16 (2026-09-17)
  が「図の成立で理由の一部は変わったが、主経路 (K2 / A-1) 優先の理由が残るので保留を維持する。図の成立は追加
  測定の必要性を示さない」と裁定した。** 走らせるなら D2050 の地位明記を満たす別 wave を新規に起票する
  (同項)。当時の実行全体の独立監査も未実施のままである。同版と results 稿の当該記述は凍結物なので書き換えず、
  下の移管先 3 の「§4 (図は無い)」も同版の内容の説明として正しいので変えない。

- **A-1 balanced5 sized 本走の attempt-0001 が投入され、3 workload とも完走した — 同版の「本走未投入・認可据え置き」は
  執筆時点では真であり、後続で古くなった記述である (2026-09-18、同版の導出後に成立)。** 同版 §8 の A-1 項の見出し
  「【未取得。pilot 完走・反復数確定・本走 policy 凍結 (非認証 lane)・本走未投入・認可据え置き (D2044 項8 で再確認)】」と
  同項の「基準 HEAD の時点で、その実装が閉じたことを記録する着地済みの正典は無い」(同じ趣旨の「本走未投入」は §0 の
  前進 10、§2 (g) の要点 2、§6 の「A-1 の本走は未投入である」、§9 表の「未取得」列にもあり、§2 第 2 幕と §6 の
  「取れていないのは A-1 が定める配置と推定対象による測定である」も同じ現況を指す) は、執筆時点では真であった。2026-09-17 の D2120 項 3
  (ユーザー裁定) が既存 submit 経路で 1 attempt を認可し (D2044 項 8 の据え置き条件「試験運転専用の分岐を外す実装が閉じた
  時点で改めて諮る」は entry 1590、commit `ad83b108b` で成立)、[T-1505] の wave が 2026-09-18 に attempt-0001 を投入、
  3 workload とも `valid=true` / `errors=[]` で完走した (job `4939` write-heavy / `4940` balanced / `4941` read-heavy、各 30 対、
  `measurement_source_commit` = local main `d2ebef7a4`、submit 06:30 → materialize 06:45 JST、再投入なし)。一次資料 =
  `output/insights/2026-09-18/t1505-a1-sized-attempt1/README.md` (時系列・受領証・分類・言わないこと) と公開 leaf
  `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (README.md / receipt.json / result.json / .complete.json)。
  登録済み解析 (policy `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`) の分類は 3 workload とも
  `resolved-above-floor` (B = baseline 平均の 3 %)、対差平均 (variant − baseline) の符号は write-heavy 正 / balanced 正 /
  read-heavy 負、`variance_plan_breach` は 3 本とも false。6 arm の verifier は既存 verifier のまま 0 anomalies (規律 2 の
  判定であり、性能の判定ではない)。**attempt の完走で変わらないこと:** result.json / receipt.json とも `formal=false` /
  `promotion_prohibited=true` (result.json の `authority` は schema v3 の固定値 `exploratory`、policy の `result_authority` は
  `sized-preregistered-descriptive-only`) の**非認証 lane のまま**であり、同項の「『A-1 が動き始めた』『A-1 の設計は固まった』
  とは書けるが、『A-1 の値がある』とは書けない」という区別は本 attempt の記録では動かしていない — この非認証 lane の結果を
  どう位置づけるかは裁定に属し (一次資料 §6)、A-1 の充足・formal 化・昇格、再投入、本走の再認可はいずれも判定されて
  おらず、認可はユーザー手番のままである (D2044 項 8)。descriptive 出力を headline 値・workload 横断の結論・C1 の再現判定に
  しない (符号が C1 の旧環境値と 3 workload とも一致することは再現判定ではない。D1993 / `L23` の区別は維持)。同版 §7 の
  チェック項目「A-1 の study を『A-3 の値の対測定による追試』と呼ばない」と「T-1998 の `accepted` を A-1 の完了・A-5 の
  充足と読まない」は有効なままである。claim-evidence 系列 `claim-evidence/2026-08-26.md` の A-1 行 (§4 の表、「未取得
  (0 件)」) は、当時の凍結 policy v2 (`static10 − adaptive`、`formal=false`) を前提とした 2026-08-26 時点の凍結物であり、
  D1262 の estimand 揃え直し (`fixed10 / fixed5 / fixed2 − no-backoff`) 以後の study と本 attempt を反映していない。
  同行は書き換えず、本 attempt の記録は上の一次資料を見る。同版・claim-evidence 稿の当該記述は凍結物なので書き換えない。
  **本 attempt の単独 results 稿と記述図 (2026-09-18):** `results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` (一次資料全体から作った統制稿、限定 20 件) と `figures/fig9_a1_balanced5_sized_attempt1.{png,pdf,provenance.json}` (生成器 `tools/plotting/plot_a1_sized_paired.py`、3 workload の対差平均 ± h と床 ±B の記述図) が着地した。稿も図も descriptive であり、上の「変わらないこと」(非認証 lane・充足/formal 化/再認可の未判定・headline 値/横断結論/C1 再現判定にしない) はすべて維持される。
  **attempt-0002 は投入されていない (2026-09-19):** ユーザー裁定 (2026-09-19) が独立再現として 1 attempt を認可したが、既存 submit 経路は qsub の前に `prior attempt reached the bench barrier; group rerun is prohibited` (driver の `_assert_no_prior_v3_bench_start`、規律 2 由来の防壁、commit `abff80d1b`) で拒否した。測定値は無く、attempt-0002 の results 稿・2 attempt の並記・図は存在しない。裁定に従い再投入せず止めた。一次資料と裁定パッケージ (同 study の 2 本目をどの経路で投入可能にするか、択 1〜3) は `output/insights/2026-09-19/a1-sized-attempt2/README.md` (§1〜§2、§7)。上の「変わらないこと」と L-A1S-4 (単一 attempt を反復間の安定性へ一般化しない) はそのまま残る。

2026-09-17 版は同日 02:10 JST の local main
(`fa24e6ea8`、[T-2630] と [T-2288] の記録の fold を含む) から導出している。前版 (2026-09-14 版) に対して積んでいた
3 項目は、いずれも 2026-09-17 版が本文へ取り込んだのでここから外した。移管先は次のとおりである。

1. **B-2 — `delta_min` の保持群ラベルの追補 (D2049、2026-09-16 実施)** → 同版 §0 の前進 6、§8 の B-2、
   §5 の [T-1875] の項。片側の境界の説明に限定し、連言全体の受理集合が広がるとは書かない。
2. **層3 の事実層は bench-first screening campaign を 2026-08-25 から対象にしている (entry 1539)** →
   同版の冒頭の訂正 1、§1、§2 (c)、§3 の項目 3、§6、§8 の B-9。記録済み 7 件の双射・現行 producer で描画できる
   集合・材料レポートを保存している 8 件の 3 つを分けて書く。保存した 1 件は非 certifying の歴史閲覧材料。
3. **B-10 の静的 backoff 右 tail の本走が完走して集団判定が出た (2026-09-15)** → 同版 §0 の前進 2、
   §2 (g) 項 9、§3 の項目 4、§4 (図は無い)、§6、§8 の B-10、§9 の第 4 種。言い方は事前登録 §4.5 の固定表現に
   限り、`performance_certified: false`、当時の実行全体の独立監査は未実施。前版の 5 箇所 (当時は真) は
   現在地の案内として更新した。

**積んでいる項目の少なさは「最新版に誤りが無い」という保証ではない。** 2026-09-17 版自身が、前版が
執筆時点で既に偽だった記述を 3 件 (上の訂正一覧) 見つけている。同じ型の誤りが最新版にもありうる。
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
