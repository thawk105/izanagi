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

**最新 = `2026-09-14.md`。** 図は `figures/` に、2026-07-10 版の作成時に気づいた示唆は
`notes-2026-07-10.md` に分離。`figures/fig3_arc_status.png` は 2026-07-10 版（Phase 3 段 5 時点）の
現況図であり、2026-08-23 版以降の第 3 幕の記述とは一致しない（各版 §0 に明記）。

**この節は最新版の訂正だけを載せる。** 旧版が自分の前版をどこで訂正したかは、その旧版自身の
冒頭が持つ（凍結物なので、訂正の一覧も版と一緒に凍結されている）。

**2026-09-14 版が前版を訂正した箇所は 4 つ。** いずれも同版の該当節に理由がある。凍結物である
2026-09-05 版は書き換えていない。

1. §2 (c)・§2 (e)・§3 の項目 5・§5・§6・§7・§8 の B-3・§9 —「鍵はユーザーが生成したので D906 の
   性質は保たれており、D1638 が想定した限界は発生していない」と書いていた。**誤りである。**
   鍵対と発行主体の運用複製が置かれた `/work/1/SFC/tanab/dev-wave-authority/` (0700) の
   **所有 uid は AI の実行主体と同一**であり、D906 が要求する「候補および AI が書ける領域の外に
   置く」は満たしていない (D1829、2026-09-08)。**生成者の分離とアクセス権限の分離を取り違えていた。**
   さらに D1731 が選んだ実効層 (別 OS principal) も計算環境の管理権限を要し、ユーザーがそれを
   持たないため、**3 択すべてが閉じて「当面実装しない」と確定した。**
2. §0 の前進 6・§2 (c)・§8 の B-4 —「専用 driver が無いと測れないので、測定はまだ始まって
   いない」と書いていた。**この前提は前版の執筆時点で既に偽だった。** 当該 driver は 3 日前の
   2026-09-02 に D1453 で main へ着地している (D1694、2026-09-07)。D1641 第 4 項が命じた
   「新設」は「適合」と読む。**決定そのもの (欠測規則へ適合させてから測る) は維持されている。**
3. §0 の前進 2・§2 (f)・§8 の A-2 —「`BACK_OFF=1` (CCBench 内蔵の指数 backoff)」と書いていた。
   **機構名が誤りである。** CCBench pin `511c9538` の現物 (`include/backoff.hh` の `Backoff`
   クラス) は、スループット勾配を見て共有待機量を固定幅 100 で増減し 0〜1000 に収める**適応制御**で
   あって、指数的に増える機構ではない。`cmake/Options.cmake` の option 説明文だけが
   `exponential backoff on abort` と呼んでいる ([T-2338]、2026-09-07)。
   **D1645 の決定内容 (支持する命題を `BACK_OFF` の有効/無効へ書き換える) は変わらない。**
4. §2 第 1 幕・§6・§8 の A-2 — 旧 attempt の 4 cell の correctness certified の対象を、まとめて
   「内蔵指数 backoff 有効の build」と書いていた。**母集合が誤っている。** 旧 attempt
   `t2022-20260828c` の権威 bytes では `rr5-stock` と `rr50-stock` の genome が `BACK_OFF=0`
   (無 backoff) である。内蔵の適応 backoff が有効なのは adopted 2 cell だけで、stock 2 cell は
   無 backoff の build について certified だった。正しくは「4 cell とも certified。driver の
   source routing から導くと、stock は無 backoff、adopted は CCBench 内蔵の適応 backoff の
   build である」と役割別に書く。

## 最新スナップショット以後に確定したこと（stale 注記）

スナップショットは凍結物なので腐る。ここは腐らない入口として、最新版の記述が既に古くなった箇所を
指す。**矛盾があればここが指す一次資料が勝つ。**

前版 (2026-09-05 版) に対して積んでいた 2 項目 — A-2 の走行が有効にしていた機構が
「内蔵指数 backoff」ではなく「CCBench 内蔵の適応 backoff」であること (2026-09-07 追記、[T-2338])、
B-10「機序説明の帯域外への拡張」の測定が進んだこと (2026-09-09 追記、2026-09-10 に静的 1000 µs の
正式標本の取得を反映) — は、**いずれも 2026-09-14 版が本文へ取り込んだのでここから外した。**
前者は同版 §2 (f) と冒頭の訂正 3、後者は同版 §8 の B-10 と §6 が持つ。

**同じく、前版に対して積んでいた「A-2 の新 attempt を本節はまだ評価していない」という保留も
外した。** 2026-09-14 版が §8 の A-2 でその評価を行い、**D1645 の解除条件 (「正しい identity で
取り直した attempt が出るまで」) を attempt `t2364-20260907b` が満たすと判定した。**
**なお、その保留の段落は「同稿の下の results 系列の表への登録も未了」と書いていたが、
これは書かれた時点で既に偽だった** — 下の results 系列の表は 2026-09-07 の稿と 2026-09-09 の
英語稿の両方を登録している。**この食い違いも本改訂で解消した。**

**現在この節に積んでいる項目は 3 件である。** 2026-09-14 版は同日の local main
(`af3762d62`、/rulings 全件 第 18 回の裁定 D1986〜D1988 を含む) から導出している。
**ただし本 README が同版について「執筆時点で腐っている箇所は無い」と書いたのは誤りだった** —
下の項目 2 が指す箇所は、**同版が書かれた時点で既に偽**である。後日状況が変わったのではなく、
執筆時点の誤りを後から見つけた訂正である。前版の driver 不在の前提について、同じ形の訂正が
先例としてある (上の「2026-09-14 版が前版を訂正した箇所は 4 つ」の 2)。
**次に正典が動いたら、その項目をここへ積む。**
**項目が積まれること自体は、新しい日付の版を作る要求にはならない** (D1858)。

- **B-2 — `delta_min` の保持群ラベルの追補を実施した (2026-09-16)。** 2026-09-14 版 §8 の B-2 は
  「**追補は未実施**」と書いている。D1986 項 2 に従い、決定側の記述を追補で正した — 正典は
  `docs/decisions.md` の「D1640 の保持群ラベルを H1 = rr80、H2 = rr20 と訂正し、他の決定内容は
  維持する」。**凍結側 (`s8b_holdout_freeze.HOLDOUTS` / `trial_registry.HOLDOUT_BINDINGS` と
  `output/s8b-freeze/holdout_freeze.json`) は 1 byte も変えていない。**
  同版が「受理集合を広げる向き」と書いた箇所は、**過小な境界を与えられた側の holdout についての
  説明**として読む — 他方の境界は過大になるので、両 holdout を合わせた受理集合が単純に広がるとは
  言えない。どちらが過小になるかは rr80 と rr20 の参照値の大小に依存し、その参照測定は未取得である。
  追補は参照測定の投入・値の記入・実装着手のいずれも新たに認可しない。

**2. 層3 の事実層は bench-first screening campaign を 2026-08-25 から対象にしている
(2026-09-16 追記)。** 2026-09-14 版は §1 (何のプロジェクトか)、§2 の第 3 幕、§3 (新規性の主張)、
§6 の「言えること」、§7 の「前版から引き継ぐ項目」、§8 の「B. その主張をするなら必要になるもの」
の B-9 — **計 6 箇所で、bench-first screening campaign を層3 の対象外あるいは未対応として
扱っている。6 箇所とも同版が書かれた時点で既に偽だった。**

対応は 2026-08-25 の [T-1291] で着地している。**描画を可能にしたのは schema の 2 段の変更であって
renderer ではない** — `b8318b956` が `screening` / `screening_disabled` を排他制約つき optional
property として足し (producer 側に 17 key の runtime 閉包検査を同時に置いた)、`ed251424d` が
`settled` を boolean と null の 2 型へ広げた。`schema_version` は D828 に従い据え置いた。
`ed251424d` の commit message 自身が「名指し artifact … が build_report を最後まで通ることを
親が実測で確認した (runs 2 行、うち 1 行が screening true)」と記録している。
2026-09-16 にその材料レポートを
`output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/reports/layer3_report.json` へ保存した。

**次の 3 つを分けて読む。**

1. **記録済み 7 件について生成当時に成立した双射** — 歴史的事実であり不変。
   `claim-evidence/2026-08-26.md` の C11 が挙げる「7 件」は当時の保存件数であって誤記ではない。
   内訳は trigger 系の sweep 6 件と loop autonomous 1 件である。
2. **現行 producer で描画できる campaign 集合** — 1 と一致しない。D170 (2026-08-05) により
   歴史枝の trigger 軸 campaign は `legacy-unclassified` となり、新しい raw view の発行と
   そこから新規に材料レポートを起こすことが拒否される。既存 7 件はこれに当たる。
   6f169f90 は `campaign.lock` に `search_config.axis` を持たない backoff-sweep なので射程外である。
3. **本追記の時点で材料レポートを保存している 8 件** — 1 に 6f169f90 を足したもの。

**保存した 1 件は歴史閲覧用途の非 certifying 材料であり、現行の認証適合は `unknown` である**
(`admission_decision.admission_status` = `historical-not-reclassified`、
`admission_decision.classification` = `historical-pre-admission-schema`、
`certifying_input` = `false`、verifier epoch = `E0`。**top-level に `admission_status` /
`classification` という key は存在しない**)。**「admitted」と書かない。**
**任意の screening campaign について完全とも書かない。**

**B-9 は閉じていない。** 3 項のうち残る 2 つの状態は次のとおりである。

- **値の改変に対する深い一致検査** — 2026-08-03 のユーザー裁定 (択 (b)) が `layer3_report` 本体の
  強化を**実施しないと決めている**。強化は新 verifier 経由だけとし、本体側へ着手するには
  択 (a) の再裁定が要る。**未着手ではなく、裁定で止まっている。**
  verifier 経由 (`--campaign-output-root` の fresh rebuild 深い一致) は実装済みである。
  項目の正本は `docs/phase3.md` の見送り台帳。
- **機序仮説層 (v3)** — 設計凍結のみで未実装。発効条件は
  `output/insights/2026-07-16_layer3-mechanism-wiring-design.md` が定める
  「次に agent 出力が生まれる loop 再走と同時」であり、要求する永続面
  `runs/agent_outputs.jsonl` は repo 内に 1 件も無い。残件として起票した。

`output/reports/layer3_paper_evidence_dossier.md` (2026-08-21) の「screening 非互換の扱い」節が
「この非互換のため、両 campaign とも `reports/` ディレクトリ自体が存在しない」と書く点も、
**6f169f90 については偽になった** (`8ff95955` については変わらない — 同 campaign は
ccbench commit 不一致の build-error で screening / bench に到達していない)。
同 dossier は日付入りの凍結資料なので訂正しない。

経緯と実測の正本は `output/insights/2026-09-16/layer3-screening-currency/` である。

**3. B-10 の静的 backoff 右 tail は、本走が完走して集団判定が出た (2026-09-16 追記)。**
2026-09-15 (JST) に group `b10-backoff-grid-20260915T061814Z-545445` が完走した。
**2026-09-14 版は 5 箇所で、この本走を未投入として扱っている** — §0 の前進 9
(「本走は未投入である」「残る blocker は投入経路の配線 1 件になった」)、§2 (g) の項 7
(「静的 tail は本走 driver まで来たが未投入」)、§8 の B-10 の 2 文
(「右側の探索 3 点 … 本格格子は未投入である」「本走は未投入であり、残る blocker は投入経路の
配線 1 件である」)、§9 の「運用上の証拠」欄 (「静的 tail 本走 driver の実装と投入前条件 5 件の
充足 (本走は未投入)」)。**5 箇所とも同版が書かれた 2026-09-14 時点では真であり、
現在地としての案内が古くなったものである。執筆時点の誤りではない。**

集団 verdict は `not-observed-in-any-workload` で、3 workload すべてが `not-observed`、
各 6 区間・計 18 区間すべてが `declining`、局所平坦区間は 0 だった。**言い方は
`docs/b10-backoff-static-tail-preregistration.md` §4.5 が固定している** —
「この事前登録の述語では、表現可能域である 9999 マイクロ秒までに飽和を観測しなかった」であり、
**「飽和しない」「飽和点が存在しない」とは書かない。** 同 §3 が併記を要求する throughput の
費用も同じ格子で取れており、1250 から 9999 マイクロ秒の間に 3 workload とも半分以下へ下がる。
判定・格子・費用の表と証拠の対応は
`output/insights/2026-09-16/t2647-b10-tail-downstream.md` の §1・§3・§4 が持つ。

原成果物は `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/` の
`t2500-backoff-static-tail-formal.json` / `.dat` / `-complete.json`、投入と再導出の一次資料は
`output/insights/2026-09-16/b10-tail-formal-submit/README.md` である。同資料は 2026-09-16 の
本番 CLI による再導出で 3 成果物すべてが 09-15 の成果物と byte 単位で一致したと報告する。
**これは当時の実行全体 (ビルド、resume 操作、失敗 attempt の履歴) を独立に監査したという意味では
ない。その監査は未実施である。** `performance_certified: false` は動いていない。
ここにある性能値を根拠に variant を採用してはならない (絶対規律 2)。

**次の 4 つは古くなっていない。訂正の対象に含めない。** (i) §8 の「今も未測なのは
901〜998 マイクロ秒の帯である」— D2027 がこの帯を測らないと裁定しており、今も未測である。
(ii) §8 の「v2 を入力した場合の判定は未測定である」— 09-15 は
`t2500-backoff-static-tail-formal-report/v1` という別系列の判定であり、旧 consumer へ
schema v2 を入力した場合の判定ではない。(iii) D1936 項36 の据え置き — v2 への consumer 移行と
追加 tail 測定は今も進めない。(iv) 上の版履歴表にある「本走未投入」— その版がいつの時点の
ものかを述べた歴史的記述である。

**既存の図はこの cohort を描いていない。** `figures/fig2c_b10_extended_backoff` が描くのは
group `b10-backoff-grid-20260826T234647Z-783837` の拡張格子 (0〜1000 マイクロ秒) であり、
生成器 `tools/plotting/plot_b10_extended_backoff.py` はその group id を定数で持つ。
**09-15 の右 tail を描いた図として引かない。** 本追記では図を新規作成・昇格していない。
2 本目 cohort の地位 (再現か置換か) は D2050 が持ち、本追記は触れない。
本注記は判定の所在と射程を渡すものであり、[T-2647] や B-10 の閉鎖ではない。

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

**この系列の規則。**

- **append-only。書いた後は更新しない。** 版と同じ凍結物である。
- **新しい日付を足すときは、入力 5 節（最新版の §3 / §6 / §7 / §8 / §9）全体から作り直す。**
  一項目だけを直した差分改訂を新しい日付として置かない（版と同じ理由 — 更新しなかった項目の
  stale が「その日付時点でそう主張した」という新しい嘘に変わる）。
- **「版の履歴」表には登録しない。** これは版ではない。どちらが全面再導出された版かは
  ディレクトリで判別する。
- **数値・日付・判定の出所は一次資料だけとする。** 版の記述を数値の出所にしない。
- 版と同じく `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外である。

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
- 版と同じく `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外である。

## 運用ルール（check_docs.py との関係）

- 本ディレクトリの文書は追記型の凍結記録なので `tools/check_docs.py` の `LIVING_DOCS`（現況主張 lint）対象外。
- 他文書からは**ファイル名（basename）で参照**する（行番号参照は禁止・節名参照にする、check_docs.py 準拠）。
