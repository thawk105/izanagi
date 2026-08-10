---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t510-ruleops-git-budget
seq: 1
title: ruleops の git timeout を作業量比例の上限付き予算へ変えた ([T-510]) — 律速の同定は親 brief が誤っており、一次資料と実測で 2 経路へ訂正した (コード + docs、受入 2 走とも rc=0 (7912 passed / 20 skipped / 446.41 秒)、変異 16/16 KILLED・SURVIVED 0、branch worktree-dev-wave-t510-ruleops-git-budget)
---

## 本文

- **ユーザー裁定に基づく実装 wave。** 依頼逐語は「[T-510] を裁定どおり (a) で実装してください。
  tools/ruleops.py の GIT_TIMEOUT_SECONDS = 20 固定が履歴長に依存せず全 subcommand へ掛かり、
  受入全走を独立 3 回赤にしました。[T-553] の作業量比例予算とは別設計との裁定です。ruleops の
  重い呼び出しの特性 (stdin なし) に合わせた予算化を実装してください」。設計判断は
  {{D:ruleops-git-timeout-budget}}、失敗は {{F:parametrize-id-breaks-node-extraction}}、
  および F1 と F155 の再発。

- **本 wave の最も重要な結果は、親 brief の中心的主張 2 件が一次資料と実測で refuted された
  ことである。** 親は worklog の裁定要約にあった逐語だけを根拠に「観測された赤 3 件はすべて
  `git log timeout` であり、律速は full-history pickaxe (無負荷 7.084〜7.919 秒 / 2,402 commit)
  だけである」と結論した。`docs/failures.md` の一次資料は違った。[T-639] は
  `git cat-file timeout`、[T-648] の `git log timeout` は `inventory` 経路であり、
  `build_inventory` は `_pickaxe` を呼ばない。**段 3 の敵対レンズ 2 本が独立にこれを指摘した。**
  F1 の再発として台帳へ送る。

- **訂正後の実測が、欠陥の性質そのものを変えた。** 実際に落ちた 2 経路の無負荷実測は
  `cat-file --batch` が **0.609 秒 / 6,494 要求 / 99,981,192 bytes**、path 限定 `log` が
  **0.437 秒 / 2,402 commit** である。20 秒での打ち切りは **33〜46 倍の尾部事象**を意味する。
  すなわち欠陥は裁定文が指した「履歴長への非追随」だけでなく、**固定値が無負荷 1 秒未満の
  呼び出しに対してすら尾部を吸収できないこと**であった。作業量比例予算はこの両方を同時に直す —
  作業量で課金することで余裕がそれぞれ 171 倍・238 倍になる。裁定 (a) の方向は正しいままである。

- **D172 は同じ定数を「変えない」と決めていた。** ただし解除条件「原因が理由行付きで特定できてから
  独立に裁定する」を自ら明記しており、理由行付き 3 回の再発とユーザー裁定でこれを満たす。
  迂回ではなく解除条件に沿った supersede として {{D:ruleops-git-timeout-budget}} に書いた。

- **依頼のうち「受入全走を安定な緑へ戻す」は本 wave 単独では達成されない。** 段 3 の 2 レンズが
  独立に指摘し、親が実測で確定した。`tools/run_tests.py` の `_preflight_ruleops` は
  `ruleops check` を **`timeout=60`** で打ち切り、`test_ruleops.py` 自身も
  `assert elapsed < 60` を持つ。`check` は候補ごとに `_pickaxe` を呼び、テストは
  signal token union の上限 6 に届く最大 package を実際に作る。親の実測に基づく見積りは
  **6 x 7.084 + 6 x 0.370 + 約 1 = 約 46 秒 / 60 秒 (余裕 1.3 倍)** で、pickaxe は
  約 17.7 ms/commit で伸びるため残り約 790 commit である。直近 7 日の増加速度 (183 commit/日)
  なら約 5 日、直近 30 日 (71.7 commit/日) なら約 11 日で**フレークでなく決定論的に赤**になる。
  **内部予算をいくら上げても直らない。** 本番 ledger は候補 0 件で `check` は 0.253 秒であり、
  本番 preflight は無風である。危険なのはテストが合成する最大 package だけである。
  緩和策 (token 数削減 / pickaxe の履歴範囲限定 / preflight の分割 / 60 秒定数の引き上げ) は
  設計択一を含むため scope 外とし、下記 {{T:ruleops-preflight-60s-ceiling}} で裁定へ返す。

- **敵対レビューを 5 本回し、すべて NO-GO を返した。** 段 3 が 2 本 (sol/luna x max)、段 6 が
  2 本 (sol/luna x high) と焦点再レビュー 1 本。fix を **3 巡**した。設計を変えた決め手は次である。
  - 定数の導出を別 module の 0.0086 秒/要求の流用から、**本 module 自身の打ち切り観測**へ変えた
    (段 3 レンズ B、Major)。流用元は `--batch-check` (header のみ) で、本 module が使う
    `--batch` (本文込み) とは protocol が違う。`PER_REQUEST` は 0.013 になった。
  - timeout の detail に **mode label 7 種と実予算**を載せた (段 6 レンズ C、Major)。
    4 種類の `log` が同一 detail になるため、D172 が要求した「理由行で原因を確定する」を
    満たしていなかった。**本 wave の親がまさにこれで律速を誤認しており**、自分の失敗を
    直接閉じる修正である。
  - **点の追加では clamp 変異が原理的に閉じない** (焦点再レビュー、Major)。3,000 / 8,000 の点を
    足しても `N >= 3000` の clamp は全件緑を通過する。workload に `min`/`max` が無いことを
    `ast` で検査して class ごと閉じた。CAP が単一 literal であることの `ast` 検査も同型である。

- **実測で refuted した所見が 3 件ある。** (i)「元 repo の値を clone へ移せない」— テストと同じ
  `git clone -q --no-local` を作って測ると **7.084 秒**で、元 repo の 6.977〜7.919 秒と同等だった。
  (ii)「bootstrap の commit 列挙が新しい固定 20 秒ボトルネックになる」— 実測 0.034 秒 / 98 KB で
  BASE に対し 588 倍の余裕。(iii)「commit 数に対して 16% 超線形」— 同一測定のばらつきが
  6.977〜7.919 秒あり、超線形性は確立していない。

- **変異は 4 走目で完走した。** 1 走目は {{F:parametrize-id-breaks-node-extraction}} で M09 中断
  (台帳は erratum として保存)。2・3 走目は F155 の再発で baseline が取れず、
  memory の recipe どおり `--force-dispatch` を明示して解決した。最終走は baseline PASSED、
  **16/16 KILLED、SURVIVED 0、MISMATCH 0**。M15 (reason 改変) と M16 (detail から予算を落とす) は
  `DW-M03` に従い診断のみの変異として `category: positive` に分離した。
  期待 node 集合のうち M09〜M16 は 1 走目の観測ではなく**推論で導出**しており、
  それが実走で完全一致した。変異走行では real-repo テスト 1 件を `-k` で除いている
  (1 走 70 秒のほぼ全てを占め、どの変異も対象にしていないため。意図的な絞り込みである)。

- **受入全走は 2 走ともいきなり完全な緑だった。** 1 走目は
  `7881 passed / 20 skipped / 0 failed / rc=0` (request `899755.nqsv`、503.73 秒、tip `b1637998`)。
  **1 走目の直後に main が `dce4ae4f` へ進んだため、取り込んで 2 走目を測り直した** —
  `7912 passed / 20 skipped / 0 failed / rc=0` (446.41 秒、tip `b2664435`)。
  F57 族の `git-timeout` はどちらにも出ていない。
  **ただし 2 回の緑は「稀な尾部事象が来ても落ちない」ことの証拠ではない。** 本 wave が示せたのは
  予算化して赤が増えていないことと、観測された 2 経路の余裕が 33〜46 倍から 171〜238 倍へ
  上がったことまでである。

- **受入を測った tip は `b2664435` で、land する tip はその上に本記録の docs-only commit を
  1 つ載せたものである。** 記録が受入値を含む以上、厳密一致は記録 commit ごとの再走を要する
  無限後退になるため、台帳の慣行に従って差分の性質をここに明示する。
  最終 tip では実 repo の docs を読むテスト 2 file を実走した ([T-648] の免除証拠規則)。

- **段 8 自己改善は候補 3 件、`docs/dev-wave/**` への採用 0 件。**
  (候補 1) `DW-S01` の一次資料条項へ failures 台帳を足す — F1 再発の恒久対応。
  **実際に編集して `check_docs` が赤になり revert した。** L1 unique footprint が
  10656 bytes で予算 10625 bytes を **31 bytes 超過**する。意味等価な縮約先が無いため、
  恒久対応は memory `primary-source-includes-failures-ledger` を新設して閉じ、
  doc への統合は候補として返す。**これは worklog (342) 候補 2、worklog (352) 候補 1 に続く
  独立 3 例目**であり、dev-wave docs の自己改善が構造的に入らない状態が続いている。
  (候補 2) 変異 runner の `--force-dispatch` — **規則の欠落ではなく既存規則の不遵守**だった。
  memory `mutation-runner-dispatch-recipe` は本文に当該 argv を明記しており、親が索引行だけを
  読んで本文を開かなかった。契約に従い文書は変更せず、同 memory の索引行に要点を出す更新だけ行った。
  (候補 3) 「外側 (呼び出し側) の締切が編集面の外にある場合、brief で棚卸しする」 —
  本 wave の 60 秒天井の見落としが 1 例目であり、`DW-G03` の独立 2 例に達しないため起票しない。

## 次の一手差分

### 完了

- [T-510] `tools/ruleops.py` の固定 git timeout を subcommand 別の作業量比例予算へ置き換えた。
  受入 2 走とも rc=0 (最終 7912 passed / 20 skipped)、変異 16/16 KILLED。律速の同定が親 brief の誤りであった
  こと、および「受入全走を安定な緑へ戻す」が本 wave 単独では達成されないことは本文の留保に記録した。
  remaining: none
  base: 44cb961a1f668300ab7baa6673d4a4d166286ca96c74220ecd566f0b33ba7324

### 新規

- {{T:ruleops-preflight-60s-ceiling}} **P1・ユーザー裁定待ち**: 最大 package の
  `_preflight_ruleops` が外側 60 秒の約 77% に達しており、pickaxe が約 17.7 ms/commit で伸びるため
  **5〜11 日で決定論的に赤**になる。`tools/run_tests.py` の `timeout=60` と
  `test_ruleops.py` の `assert elapsed < 60` の両方が関わり、内部予算では直らない。
  選択肢は (a) signal token 上限を下げて pickaxe 本数を減らす、(b) pickaxe の履歴範囲を
  receipt epoch などへ限定する、(c) preflight を分割して 1 呼び出しあたりの締切を分ける、
  (d) 外側 60 秒とテストの 60 秒定数を引き上げる、(e) 現状維持。
  本番 ledger は候補 0 件なので本番 preflight は 0.253 秒で無風である。

- {{T:ruleops-cap-is-per-call-only}} **P3・新規**: `CAP` は 1 回の git 呼び出しの絶対上限であって
  1 走行の累積上限ではない。`MAX_CANDIDATES` x `MAX_EVIDENCE_ITEMS` で receipt range log は
  最大 256 回になりうる。本番 ledger は候補 0 件で発火しないため `DW-G02` に従い送った。
  走行全体の deadline をどこに置くかは設計択一を含む。

- {{T:ruleops-default-controls-swallows-git-timeout}} **P3・新規**: `_default_controls` の
  `except (OSError, RuleOpsError): pass` が `git-timeout` を含めて握り潰す。本 wave が作った
  欠陥ではなく既存挙動で、予算化とは独立に閉じるべきである。段 3 レンズ A が real と指摘した。

- {{T:ruleops-batch-blob-memory-bound}} **P3・新規**: `cat-file --batch` の予算は要求数だけで
  返却 blob bytes を見ておらず、予算を伸ばした分だけ単一 `bytes` へ蓄積する時間も伸びる。
  現状は 6,494 要求 / 95 MiB の実測で収まっているが、上限ではない。batch 分割は read protocol の
  再設計を含むため `DW-G02` に従い送った。段 6 レンズ C が real と指摘した。
