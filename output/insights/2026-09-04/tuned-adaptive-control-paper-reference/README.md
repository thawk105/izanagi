# 調整済み adaptive の実対照を論文側の台帳へ結んだ ([T-2186] / [T-2239])

**種別:** 台帳の是正記録。**新規計測なし・新規作図なし・既存図の bytes 変更なし。**
本文書は測定原典ではない。数値の出所はすべて
`output/insights/2026-09-02_cicada-adaptive-three-constants.md` と D1505 / D1506 であり、
本文書は数値を新しく作らない。

## 何をしたか

D1506 は「backoff 機構の性能比較は、無 backoff と調整済み adaptive の 2 本を基準線に置く」と
定めた。前 wave ([T-2186]) はこの裁定を repo 全体へ行き渡らせたが、**その基準線を実際に描いた図が
論文側の台帳のどこにも登録されていなかった。** 本 wave はその 1 点を閉じた。

変更は 2 file だけである。

- `docs/paper-story/figures/README.md` — 図の一覧の直後へ「調整済み adaptive の実対照
  (論文図へ未昇格)」節を新設し、現物 3 file への解決可能な相対リンク、同じ軸に並ぶ系列の名指し、
  旧 `linux-baremetal` 図と畳んではならない理由、未認証境界、昇格の必要条件を書いた。
- `docs/paper-story/README.md` — (1) 未認証の数値を含む段落の冒頭へ、その段落の数値が
  未認証の trace-disabled 観測値であることを隣接させた。(2)「今後の基準線」へ、現物は上の節から
  辿ること、`fig2b` / `fig2c` を調整済み adaptive の対照として代用しないこと、
  この参照が閉じるのは「並べて名指しする」ところまでであることを足した。

## 起動時に判明した、carry と引数の前提を覆す事実

1. **調整済み adaptive の定数は D1475 の値ではない。** wave 引数は D1475 を正本と指したが、
   D1475 の「刻み 0.5 µs / 上限 50 µs」は後続の D1505 / D1506 が置き換えている。現行は
   **刻み 1 µs / 更新間隔 2560 µs / 上限 1000 µs** であり、律速は刻みではなく更新間隔である。
2. **[T-2186] の差し替え 10 単位は既に着地していた。** 本 wave の段 2 が 5 系統の検索式で
   独立に再走査し、未差し替えの単位は 0 件、成果物を変える新しい残余も 0 件だった。
3. **[T-2239] の「同じ図に並べる」は、既に描かれた図が存在した。**
   `output/insights/2026-09-02_cicada-adaptive-three-constants-figures/t2187_stage2_thread_axis`
   が、無 backoff (`none`)、CCBench 既定 3 定数の adaptive (`s100-u10`、陽性対照)、
   調整済み adaptive (`s1-u2560`)、調整候補 2 本を、3 workload x 8 スレッド数 (6〜48)、
   7 反復、t 分布の 95% 信頼区間つきで同じ軸へ描いていた。単一環境である。
   **carry が言う「新規計測が要る」は、旧 `linux-baremetal` の図へ線を足す場合に限った話であり、
   carry は書かれた時点で正確だった。** 変わったのは、別環境で完結した対照図が既にあったため
   本 wave では新規計測が不要だったことだけである。
4. **carry の前提条件 (1) はこの経路に当たらない。** `test_backoff_figure_provenance.py` の
   `BASELINE_BY_GENOME` 拡張は、[T-2186] の段 4 が既に不採用と裁定していた。加えて本 wave が
   参照する図の生成器 `tools/plotting/plot_t2187_adaptive_consts.py` は、既定セル以外へ
   そのセル名 (`s1-u2560`) を label として付け、既定セルがちょうど 1 つ存在することを構造的に
   要求する (`_series_order` / `_series_label`)。**carry が恐れた誤 label 事故は、この経路では
   構造的に起こらない。**
5. **carry の前提条件 (2) は未了のままである。** 調整済みの値は trace-disabled のみで
   直列性の検査を通していない。検査は [T-2189] の担当で、本 wave の走行中も別 wave が動いていた。

## 段 4 で確定した 3 つの択一

- **対照図を `docs/paper-story/figures/` へ昇格させない。** 根拠は 3 つで、(i) copy 先の bytes は
  元 provenance が束縛する出力ではないので証拠の鎖が切れる、(ii) 新しい paper figure を検査する
  consumer が存在しない (既存 consumer は `fig2b` / `fig2c` / `fig4` の basename を個別に固定し、
  directory 全体を見る consumer は無い)、(iii) 既存の PNG / PDF / provenance は凍結物である。
  **未認証であることは昇格を許さない必要条件として残るが、単独の根拠にはしない。**
- **`tools/plotting/FIGURE_CONVENTIONS.md` を変更しない。** 規約は「何を描くべきか」を定め、
  個々の図の所在は図の台帳が持つ、という責務分離が既に成立している。
- **`BASELINE_BY_GENOME` を変更しない。** ただし前 wave の理由「3 定数を出す producer が
  実在しない」は広すぎた。`tools/pegasus/probes/t2187_adaptive_const_probe.py` は 3 定数を
  genome へ出す。正しい理由は「その producer は別 schema へ出すので、**この v2 consumer surface
  には producer がいない**」ことと、既存 3 campaign の WAL に 3 定数の出現が 0 件であることである。

## 敵対相談が親の brief を訂正した 4 点

段 3 の 2 レンズは、親が段 1 で書いた前提のうち 4 つを実体で覆した。いずれも採用した。

1. **「論文側から図へ到達できない」は事実より強い。** 実際には
   `docs/paper-story/README.md` -> 一次資料の insight -> insight 本文に埋め込まれた図、という
   2 段の経路が既にあった。**正しい欠陥は「図の台帳に調整済み対照が 1 行も登録されておらず、
   基準線を定める段落からその図を直接選べない」ことである。** 台帳だけを読む執筆者は、
   登録済みの `fig2b` / `fig2c` を引く。
2. **親が brief に書いた検索コマンドは archive を除いておらず、示した件数と一致しない。**
   archive を含めると 1 件 (過去の worklog archive)、除くと 0 件である。結論は変わらないが、
   コマンドと数値が食い違っていた。
3. **「[T-2186] 完了済み、carry は stale」は完了の射程を混同していた。** 着地していたのは
   10 単位の差し替えであって、論文側への導線は未了だった。carry を stale と呼ぶのは誤りである。
4. **「3 定数 producer が実在しない」は一般化しすぎだった** (上記のとおり)。

**節名や basename だけでは到達経路が閉じない**という指摘も採用し、新節は PNG / PDF / provenance
それぞれへの相対リンクを張った (3 本とも解決することを機械確認した)。

**未認証の数値と但し書きが離れている**という指摘も採用し、数値を含む段落の冒頭へ但し書きを移した。

**「昇格条件は correctness 検査の決着」は十分条件として読める**という指摘も採用し、
**必要条件であって十分条件ではない**と書いた。

## 正直な限界

- **調整済みの値は認証されていない。** trace-disabled の性能測定のみで、直列性の検査を
  通していない。**variant 採用の根拠にも certified な性能結論にも使えない** (絶対規律 2)。
  正しさの検査は [T-2189] の担当であり、本 wave はそれを前進させていない。
- **論文図への昇格は行っていない。** 昇格には correctness の決着が必要だが、それだけでは足りない。
  現 provenance が束縛する出力 path は repo 外にあり、論文図の場所へ置いた copy を検査する
  consumer も存在しない。昇格そのものは別途決着させる。
- **旧 `linux-baremetal` の図に調整済みの線を足すことは、依然としてできない。**
  当時の campaign にそのセルが無く、足すには新規計測が要る。本 wave は行っていない。
- **本 wave は実装面 (コード・テスト・実行可能 script・機械設定) を 1 行も変えていない。**
  したがって変異 matrix は免除した (DW-S04 の実装面差分ゼロ)。

## 裁定パッケージ候補 (ユーザー手番)

段 3 の規律レンズが、プランにも親 brief にも無い実在の残余を 1 件見つけた。**本 wave では
変更していない。**

`orchestrator/campaign/paper_story_a1_paired.py` の `submit --study-id` は、既定で旧 study を
選ぶ。その旧 policy `paper_story_a1_paired.v2.json` の contrast は `static10` 対 `adaptive` で、
`adaptive` は既定 adaptive (`BACK_OFF=1, BACKOFF_FIXED=-1`) である。job body
`tools/pegasus/paper_story_a1_paired.sh` も旧 study を既定にし、
`orchestrator/tests/test_paper_story_a1_job_contract.py` がこれを固定している。

**現時点で規律違反ではない。** 同 policy は `formal=false` / `promotion_prohibited=true` /
`result_authority=exploratory` を宣言しており、D1506 は既定 adaptive を測ること自体を禁じていない。
しかし「既定で選ばれる実行経路の contrast が既定 adaptive を適応側に置いている」状態は残る。
既定を変えるかどうかは凍結 policy と互換経路の別裁定であり、ユーザーの手番とする。

## 走査と検査の結果

段 2 の独立再走査で使った検索式は 5 系統 (identity 503 行 / 154 file、constants 348 / 105、
baseline 147 / 38、mechanism claim 59 / 27、figure reference 17 / 5)。段 3 の規律レンズは
さらに 13 系統を独立に走らせた。**成果物を変える新しい残余は 0 件だった。**

旧 campaign report 3 件 (`backoff-sweep-silo-{write-heavy,balanced,read-heavy}-*` の
`reports/*.md` 各 27 行目) に、既定 adaptive 対静的最良を「直接証拠」と述べる旧正文が残っている。
これらは `output/insights/2026-08-25_paper-story-a3-gain-unification/README.md` が
SHA-256 で束縛した過去の記録であり、**触らないのが正しい** (規律 7)。

親が本記録の commit 前に実走した検査は次のとおり。

- `python3 tools/check_docs.py` — 違反なし (D88 の placeholder gate は
  `output/insights/*.md` も対象なので、本記録と逐語 5 本を置いた後に再走した)。
- `orchestrator/tests/test_s1_9pair_figure_provenance.py` — 27 passed。
  `docs/paper-story/figures/README.md` は `fig4` の caption 正文一致を pin されており
  (path でも SHA でもなく本文を key にする pin)、追記でこれが動いていないことを確認した。
- 三軸 conjunction の走査 — `python3 -m orchestrator.campaign.s8b_holdout_freeze search`
  (書き込みなし) で `rr80` / `rr20` ともに `conjunction_hits` が 0 件、
  `positive_control` の `hit_count` が 145 件。**陽性対照が発火しているので空振りの緑ではない。**

**この走査について 1 つ記録しておく。** 権威テスト
`orchestrator/tests/test_s8b_repo_scan_invariant.py` を焦点走したところ、
**passed ではなく 1 skipped** だった。同テストは成長 hold
(`hold_axis=tracked_files`、`correctness_gate=true`、`release_condition=explicit-user-command-only`)
に入っており、`IZANAGI_RUN_GROWTH_HELD_TESTS=explicit-user-command` を明示しない走行では走らない。
hold の解除はユーザーの明示命令を要するので**解除していない。** 代わりに、同テストが検索 pattern を
取得している production 側の CLI を直接走らせた。**したがって本 wave が実走したのは走査そのもので
あって、hold されたテストではない。**

受入全走は本記録の commit の後に、land の前提として実走する。
