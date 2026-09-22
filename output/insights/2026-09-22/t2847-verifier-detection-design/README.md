# verifier が何を検出し、何を判定しないか — 期待結果つき小履歴コーパスと CC 変異の検出期待表、既存資産の再利用範囲、大 trace の容量評価の計画、論文用の射程文 ([T-2847] の計算なし設計、2026-09-22)

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)。
wave `dev-wave-t2847-verifier-detection-design` (branch `worktree-dev-wave-t2847-verifier-detection-design`)、起点 local main `8fd2a2f5c` (開始 gate rc 0、2026-09-22 08:5x JST)、CCBench submodule `e9e477ca`。
job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-verifier-detection-design/` (brief・事実要約・Codex の prompt / 出力・待ち手)。
段 1〜6 の全文は `verbatim/` (段 3 は軽量版で省略、段 5 は実装なし。段 6 は read-only review 1 本 `s6-review.md` の NO-GO (must-fix 10・should 3) を全件採用して本文を直した。焦点再レビュー 1 巡目 `s6-focus-1.md` は NO-GO (前巡 13 件のうち closed 10・partial 3、新しい must-fix 1・should 4・nit 1) で、これも全件採用して直した。2 巡目 `s6-focus-2.md` は GO (前巡の partial 3 件と新規 6 件がすべて closed、新しい should 1・nit 1 も採用して直した))。一次資料は `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P0 (VLDB 方針 D2212)。

**性質の断り:** 本書は静的な調査 (source・記録・test を読む) による設計である。実 trace の取得・変異の build と実走・parser の改修・fixture の追加はしていない。表の「期待」は**実行結果ではない**。実行結果として引くのは、日付と出所を添えた既存の記録だけである。patch に対して実行した検査は、既存 patch 16 本が現行 pin に当たるかの `git apply --check` (作業ツリーを変えない、§5.1) だけで、ほかに資料の静的な走査と集計 (mocc の記録 JSON の集計、test file の文字列の走査、容量 wave の job log の抜き出し) を行った。

## 1. 依頼と結論

依頼 (ユーザー直接起動の `/dev-wave [T-2847]`、逐語は `verbatim/request-t2847.md`): verifier の検出力と容量を計算なしで設計する。期待結果つき小履歴コーパス (直列化可能・異常・abort・欠損 trace・初期値・同一 key 複数操作) と、意味の異なる CC 変異 20〜40 個の検出期待表を作る。既存の `patches/broken-*.patch` 16 本と verifier の再利用範囲、si の trace が v1 形式で現行 parser に拒否される制約も明記する。大 trace の容量評価の計画 ([T-2351] との関係) と、論文用の射程文も書く。実 trace の取得・変異の実走・parser 改修は含めない。

結論:

1. **現行 verifier の判定は 3 つの層 (依存グラフの巡回、trace の完全性、証拠面) と trace の外の commit 件数で決まる** (§2.1)。certified は「取引 1 件以上 ∧ 巡回なし ∧ 他の層がすべて成立」。abort した取引、取引内の中間の版、値そのもの、範囲読みの phantom、liveness は trace に現れず、**判定の外**である (§2.2)。末尾の取引の欠落は commit 件数の証人が無いと certified のまま通る (特性化 test あり)。
2. **小履歴コーパスは 6 カテゴリ 27 案** (§3)。期待はすべて辺・版・欠落箇所から手で導いた。内訳は、既存 fixture の意味を手で説明し直す 13 案と、追加候補 14 案。**追加候補のうち 10 案は test 内で作る合成 trace (`test_verifier.py`) が意味を被覆済み**で、fixture として置く候補に留まる (うち B06 は巡回としては被覆済みで、分類 `G1c` を独立の期待値として固定する assert だけが無い)。2 案は新しい trace ではなく説明の追加。**本書が調べた範囲 (fixture 22 件と、verifier を使う test file 13 本の全文字列リテラル) で同じ意味の test が無いのは 2 案** (F03 / F06 = 同じ取引が同じ key を 2 回読む。実 silo は 2 度目の読みを read set から返すので実 trace には出ない。read set の再利用を外した場合にも生じうる入力について、verifier の辺の生成を検査する合成入力で、CC の変更そのものを検出する案ではない) である。verifier 側の壊れ方をどの案が殺すかの対応表も付けた (§3.1)。
3. **CC 変異の検出期待表は 35 項目 (表の行は 32)** (§4)。うち 1 項目 (V36) は無改変の si で変異ではないので、**変異は 34、族にまとめて 26、正しさを保つ対照 4 を除くと 22 の変更機構**になる (依頼の 20〜40 を満たす)。期待の層は、巡回 4、integrity・証拠面 11、盲点 (宣言範囲の外) 13、si (現状は parse error) 3、正しさを保つ対照 4。盲点と対照を表に入れたのは、「検出しなかった = 正しい」と読ませず、誤検出の側も測るためである。
4. **既存 16 本の再利用範囲** (§5.1): 現行 pin にそのまま当たるのは silo の 11 本 (`git apply --check`、fuzz なし)。mocc の 4 本は計装 patch の上、trigger-misattr は trigger-gating 骨格の上でだけ当たる。write-intent の 4 本は当たるが、現行 pin には `I` の emitter が無いので「certified になりうる盲点」側に入る。**検出の型は thread 数と regime に依存する** (mocc の lockskip / early-unlock と hot regime の hot-update-unlock は 1 thread では X だけ、4 thread では version dup が併発し、lockskip と early-unlock は巡回も出す。hot-update-unlock は cold / default では hot 分岐に届かず certified)。
5. **si は現行 verifier でどの workload も検証できない** (§5.3)。emitter が 5 field の C 行 (v1) を出し、parser が拒否する。2026-06-18 の「無改変の si で 3,576 巡回」は当時の verifier の記録として残るが、現行の検出力の主張には使えない。v2 に上げても証拠面が無いので、巡回が出なければ certified ではなく indeterminate になり、使い道は検出に限られる。さらに update が read set から要素を消すので、同じ key を読んで書く lost update は巡回として残らない (§4.5)。
6. **容量は、巡回 0 の trace で balanced 10 s が 32.4 GiB・478 s、read-heavy 6 s が 81.2 GiB・896 s まで測ってある** (§6.1)。未測は巡回の多い大 trace・mocc の大 trace・read-heavy 10 s・TPC-C・trace を取る側の費用 (§6.2)。まず実験が要る長さを計算なしで決め、範囲外だけを測る。[T-2351] は「要る trace が 115 GiB か時間の上限を超える」と分かったときに発火する後段であり、P0 の前提ではない (§6.4)。時間窓ごとの独立検査は全体の検査と同等ではない (§6.5)。
7. **論文用の射程文を 3 つの長さで用意した** (§7): 「certified は、trace を有効にした build を有限回走らせて観測した空でない committed 取引の履歴について、依存グラフに巡回がなく、trace の完全性と証拠面の検査も通ったという判定であり、すべての実行での直列化可能性の証明ではない」。

## 2. 現行 verifier の判定の範囲 (main `8fd2a2f5c` の事実)

### 2.1 判定の組み立て

- **入力:** thread ごとの `trace_<thid>.log`。1 取引は `C <txid> <thid> <epoch> <tid> <read数> <write数>` で始まり `E <txid>` で閉じる (現行の「v2 frame」)。中に `R <txid> <key> <読んだ版の epoch> <tid>` と `W <txid> <key> <op> <epoch> <tid>` (書いた版 = その取引の commit スタンプ) が並ぶ。**読みは読んだ版を記録し、値は記録しない** (`external/ccbench/include/trace.hh` の schema 注記)。abort した取引は writePhase に届かないので trace に出ない (`orchestrator/verifier/model.py:328-329`)。
- **3 つの層:**
  1. **依存グラフの巡回。** key ごとに版を (epoch, tid) の辞書順に並べ、ww (次版の書き手へ)・wr (読んだ版の書き手から)・rw (読んだ版の直後版の書き手へ) を張る。巡回が 1 つでもあれば `non-serializable` (`model.py:511-512`)。
  2. **trace の完全性 (integrity)。** orphan read・同じ (key, 版) の二重生産・txid の重複と欠番・genesis 以下への commit・書いた版と commit の不一致・key の形式・frame の破れ (E 欠落、宣言件数の不一致) を数える (`model.py:450-467`)。
  3. **証拠面。** lock 被覆 (`X`)・write set の並べ替えでの保存 (`P`)・write intent (`I`) の違反行が 0 件であることと、protocol の source に emitter があること (`proof_surfaces.certification_gate_satisfied()`)。**source に要るのは `X` と `P` の emitter だけで、`I` の emitter は要らない** (`model.py:77-82`)。対象 protocol は `silo` / `si` / `mocc` (`model.py:37`)。
  4. 加えて、trace の外の commit 件数 (CCBench の counter) との一致 (commit 証人、`orchestrator/verifier/core.py:60-73`)。pipeline は必ず渡し (`ycsb_` 以外の binary は検証の前に拒否される。`orchestrator/campaign/pipeline.py:434-437`、commit 後に counter を無条件加算すると確認済みなのが YCSB だけ)、API と CLI (`--expected-commits`、`orchestrator/verifier/cli.py:65-74`) では任意である。**証人を渡さなければ、この条件は成立扱いになる** (`model.py:451-458`)。
- **判定 (`model.py:502-520`):** 取引 0 件 → `indeterminate`。巡回あり → `non-serializable`。巡回なしで 2〜4 のどれかが不成立 → `indeterminate`。それ以外 → `serializable`。**certified = 取引 1 件以上 ∧ 巡回なし ∧ 2〜4 がすべて成立。**
- **報告:** 強連結成分 (SCC) を小さい順に並べ、各成分から最短の巡回を 1 本、既定で最大 20 本まで返す。`total_cycles` は成分の総数 (`orchestrator/verifier/dsg.py:826-849`、`core.py:28`, `:173-176`)。

### 2.2 事象ごとの見え方

**表の `indeterminate` は、巡回が無い場合の判定である。** integrity や証拠面の違反があっても、巡回が 1 つ残れば `non-serializable` が優先する (`model.py:505-515`)。

| 事象 | trace 上の見え方 | 現行の判定 | 根拠 |
|---|---|---|---|
| rw を含む巡回 (write skew・lost update・長い巡回) | 辺として見える | `non-serializable` (分類は G2) | `dsg.py:805-824`、fixture r1〜r9 |
| ww だけ / wr と ww だけの巡回 (G0 / G1c) | 版 = commit スタンプで、commit スタンプが読んだ版より大きい限り出ない | 出れば `non-serializable` (分類だけ G0 / G1c) | `dsg.py:807-818` の証明は「wr は commit 順に前向き」(Silo の TID 規則) を前提にする。この規則を壊す変更では wr が逆向きになりうる (§4) |
| abort した取引そのもの | 出ない | 判定の対象外 (設計どおり) | `model.py:328-329` |
| abort した取引の版を読んだ (G1a) | 書き手の C が無い版を読んだ R = orphan read | `indeterminate` | `dsg.py:655-661`、fixture `integrity_orphan` |
| 取引内の中間の版を読んだ (G1b) | 同じ取引の多重書きは 1 版に畳まれ、版スタンプが最終と同じなら区別できない | 判定なし | `dsg.py:362-367` (`sorted(set(vs))`) |
| 値だけが壊れ、版スタンプは正しい | 値は記録しない | 判定なし (lock 被覆 `X` が捕まえる経路はある) | trace.hh の schema、`X` は §2.1 の 3 |
| 範囲読みの phantom (述語の依存) | 範囲読みで返った record は通常の読みとして R に出る (silo は scan 結果ごとに `read_internal()` を呼ぶ、`cc/silo/transaction.cc:304-317`)。**出ないのは、範囲 (述語) そのものと、範囲内で返らなかった key への依存**である。現行 YCSB は範囲読みを呼ばない | 判定なし (宣言範囲の外) | `docs/isolation-phenomena.md` の「スコープ外」、fixture `p1_phantom_skew` (certified を固定) |
| 途中の取引が丸ごと欠ける | txid の欠番 (txid は commit 直前に密に採番) | `indeterminate` | `parse.py` の欠番計算、`core.py:78-83` の note |
| 末尾の取引が丸ごと欠ける | 欠番にならない | commit 証人があれば `indeterminate`、**無ければ certified になりうる** (残った履歴が空でなく、他の条件も満たすとき) | `orchestrator/tests/test_verifier.py:1252` (証人なしは偽の緑を特性化)、`:1265` (証人ありは indeterminate) |
| thread の trace file が丸ごと欠ける | 途中の txid を持つ file なら欠番。末尾の txid だけを持つ file なら欠番にならない | 欠番なら `indeterminate`。末尾だけの file の欠落は、commit 証人があれば `indeterminate`、**無ければ certified になりうる** (残った履歴が空でなく他の条件も満たすとき。§3 の D03) | `test_verifier.py:1312` (証人を渡し、欠番 0 のまま `indeterminate` になることを確認) |
| 取引の R/W/E の一部が欠ける | 宣言件数の不一致・E 欠落 | `indeterminate` | `test_verifier.py:1285` (`test_characterization_txn_tail_loss_is_indeterminate`) |
| 同じ (key, 版) を 2 取引が書く | version dup | `indeterminate` | fixture `m2_version_dup` |
| genesis (1,0) 以下への commit | genesis_commits | `indeterminate` (wr 辺は落とさない) | `dsg.py:345-356`、fixture `m1_commit_at_genesis` |
| lock 被覆・並べ替え保存・write intent の違反 | `X` / `P` / `I` 行 | `indeterminate` | fixture `m3` / `m4`、`patches/README.md` |
| 証拠面の emitter が source に無い protocol | — | 巡回なしでも `indeterminate` (certified にならない) | `model.py:450-467`、論文稿 2026-09-21c の「certified の意味」節 |
| 空の trace | — | `indeterminate` | `model.py:505-510` |
| 旧形式 (C 行 5 field = v1) | — | parse error | `orchestrator/verifier/parse.py:323-326` |
| liveness (deadlock・starvation・hang) | trace は止まる / 出ない | verifier の判定の外 (pipeline の timeout 等が別に扱う) | roadmap §3.1 |
| 観測しなかった実行 (他の seed・他の schedule・他の thread 数) | — | 判定の外 | roadmap §3.1 |
| trace を除いた性能 build の実行 | — | 判定の外 (規律 1 で別 build・別 run) | `CLAUDE.md` 規律 1、D14 |

### 2.3 protocol ごとの現状

| protocol | 現行 trace | 証拠面 | 現行 verifier で得られる判定 |
|---|---|---|---|
| silo | v2 frame (`cc/silo/transaction.cc:594-602`, `:698`) | `X`・`P` あり。`I` の emitter は現行 pin に無い (`patches/README.md` の write-intent 節、pin 前進は当時ユーザー裁定待ち) | certified まで届く |
| mocc | v2 frame (pin `e9e477ca` に trace hook あり) | `X`・`P` は `patches/instr-mocc-lock-coverage.patch` ([T-2294]、pin 候補は [T-2844]) を当てたときだけ | 素の pin では巡回なしでも `indeterminate`。計装を当てれば certified まで届く |
| si | **v1** (`cc/si/transaction.cc:539-552` が 5 field の C を出し、E 行が無い。epoch を 1 に固定、tid = cstamp) | なし | **parse error (どの workload でも検証できない)**。v2 に上げても証拠面が無いので上限は「巡回を検出する」までで、certified にはならない |

## 3. 期待結果つき小履歴コーパス (設計)

段 2 の Codex 起草 (`verbatim/s2-plan.md`) を段 4 で採用したもの。**期待 verdict は、辺と版と欠落箇所から手で導いた根拠で書き、verifier の出力を期待値にしない** (D799)。設計だけで、fixture も test も足していない。

**記法:** `g = (1,0)` (genesis)、`v_i = (1,i)`。`Ti@v : R(x,u), W(y)` は「取引 i が版 v で commit し、x の版 u を読み、y を書いた」。W の版はその取引の commit 版。txid は 0 から密に振り、C の宣言件数を実際の R/W 件数に合わせ、E を付ける (欠損の案だけが例外)。**期待は、明記した破損以外の integrity が正常で、silo の証拠面の条件を満たすことが前提**であり、手で導いた非巡回だけから certified を無条件に言わない。「既存」列は意味の被覆で、bytes の同一ではない。

| ID | カテゴリ | 履歴 | 手で導いた辺 | 期待 verdict と理由 | 既存の被覆 | 区分 |
|---|---|---|---|---|---|---|
| A01 | (a) 直列化可能 | T0@v1:W(x)；T1@v2:R(x,v1),W(y)；T2@v3:R(y,v2) | wr 0→1→2 | S。0,1,2 の順が直列順 | `g1_serial`、`g2_rmw_chain`、実逐次は `g6` | 再説明 |
| A02 | (a) | T0@v2:R(x,g)；T1@v1:W(x) | rw 0→1 だけ | S。commit スタンプの順とは逆でも 0,1 の順で直列化できる | `g4_rw_no_cycle` | 再説明 |
| A03 | (a) | T0@v1:R(x,g)；T1@v2:R(y,g) を別 thread file に | 辺なし | S。どの順でも直列化できる | `g3_readonly` | 再説明 (改名・再配置の対照の素材) |
| B01 | (b) write skew | T0@v1:R(y,g),W(x)；T1@v2:R(x,g),W(y) | rw 0→1、1→0 | N (G2)。どちらも相手より前に置く必要がある | `r1_write_skew`、実データは `r8` | 再説明 |
| B02 | (b) lost update | T0@v1:R(x,g),W(x)；T1@v2:R(x,g),W(x) | ww 0→1、rw 1→0 (T0 の自己 rw は除く) | N (G2) | `r2_lost_update` | 再説明 |
| B03 | (b) 長い巡回 | T0@v1:W(x),W(a)；T1@v2:R(a,v1),W(b)；T2@v3:R(b,v2),W(c)；T3@v4:R(c,v3),R(x,g) | wr 0→1→2→3、rw 3→0。短い巡回なし | N (G2)、最短の長さ 4 | `r9_dense_cycle4` (長さ 3 は `r3_cycle3`) | 再説明 (任意の長さへ同型に延ばせる) |
| B04 | (b) 非最新版の直後版 | T0@v1:W(x)；T1@v2:R(x,v1),W(y)；T2@v3:W(x),R(y,g)；T3@v4:W(x) | ww 0→2→3、wr 0→1、rw 1→2、2→1 | N (G2)、1↔2。rw を最新版 (T3) へ張ると巡回を失う | `r5_nonlatest_transitive`、混在は `r4_mixed_cycle` | 再説明 |
| B05 | (b) epoch を跨ぐ版順 | T0@(1,9):W(x)；T1@(2,1):W(x),R(y,g)；T2@(2,2):R(x,(1,9)),W(y) | ww 0→1、wr 0→2、rw 2→1、1→2 | N (G2)。epoch を捨てると x の版順が逆転し、2→1 を失う | `r6`、`r7` | 再説明 |
| B06 | (b) 分類の対照 (正常な実行では起きない) | T0@v1:R(y,v2),W(x)；T1@v2:R(x,v1),W(y) | wr 0→1、1→0。rw・ww なし | N、分類は **G1c**。互いに相手の commit 後の版を読んでおり、dirty read なしには起きない | inline `_ordinal_witness_trace()` (`test_verifier.py:2484-2530`、T1 と T8 が互いの書いた版を読む wr だけの 2-巡回で、巡回 `[1,8]` を期待)。分類 `G1c` の assert は無い (分類の枝は合成 `CycleEdge` の単体 test `test_classify_branches` だけ) | inline 被覆済み (巡回として)。分類を独立の期待値に固定する assert が追加候補 |
| C01 | (c) abort は見えない | 実行: A が x を書きかけて abort；T0@v1:R(x,g)。trace は T0 だけ | 辺なし | S。abort の書きは committed の履歴に入らない | trace は E01 / `g3` と同じ形 | 説明の追加 (abort の有無で同じ trace になることの説明で、新しい trace ではない) |
| C02 | (c) abort 版の読み | 実行: A が未 commit の版 u=(1,7) を作り abort；T0@v8:R(x,u)。A の C/W は無い | 書き手が居ないので wr を張れない | I (orphan)。巡回ではなく読んだ版の証拠の欠落 | `integrity_orphan` | 再説明 (abort 由来だという説明だけが新しい) |
| C03 | (c) 全部 abort | 空の trace file、commit 証人 0 | 節点なし | I。検証する取引が無い。空のグラフを certified にしない | inline `test_empty_trace_indeterminate_not_certified` (`test_verifier.py:336`) | inline 被覆済み (fixture 化の候補) |
| D01 | (d) 末尾の完全な取引の欠落 | 実行: T0@v1:W(x)、T1@v2:W(y)。trace は T0 だけ。証人「なし」と「2」の対 | 辺なし | 証人なしは S、証人 2 は I。txid 0 だけでは末尾の欠落を trace の中から推定できない | inline `:1252` (証人なしは certified) と `:1265` (証人ありは I) | inline 被覆済み |
| D02 | (d) 途中の欠番 | T0@v1:W(x)、T2@v3:W(z)。独立な T1 の frame を除く | 辺なし | I (missing txid)。証人なしでも 0 と 2 の間の穴が分かる | inline `test_missing_txid_gap_indeterminate` (`:716`) | inline 被覆済み |
| D03 | (d) thread file の欠落 | thread 0 に T0@v1:W(x)、thread 1 に T1@v2:W(y)。後者の file を丸ごと除く | 辺なし | 証人なしは S、証人 2 は I。file の欠落は常に欠番になるわけではない | inline `test_commit_count_witness_detects_removed_trace_file` (`:1312`、証人あり側)。証人なし側は D01 と同じ論理 | inline 被覆済み |
| D04 | (d) E 行の欠落 | T0@v1:W(x) の C / W は正しく、E だけを除く。証人 1 | 辺なし | I (framing)。件数は一致しても終端の保証が無い | inline `test_missing_end_is_indeterminate` (`:559`) | inline 被覆済み |
| D05 | (d) frame 内の末尾欠落 | T0 の C が W 2 件を宣言、W(x) の後の W(y) と E が失われる。証人 1 | 辺なし | I (framing)。commit 件数の証人だけでは R/W の完全性を保証しない | inline `test_characterization_txn_tail_loss_is_indeterminate` (`:1285`) | inline 被覆済み |
| D06 | (d) 証人の一致と不一致 | 完全な T0@v1:W(x)、T1@v2:W(y) に証人 2 / 3 を与える | 辺なし | 2 なら S、3 なら I。履歴の bytes が同じでも外の証拠で変わる | inline `:1326` (一致) と `:1484` (CLI で不一致) | inline 被覆済み |
| E01 | (e) genesis の読み | T0@v1:R(x,g) | 辺なし | S。初期値は書き手の居ない版として許される | `g3` など | 再説明 |
| E02 | (e) genesis への commit | T0@g:W(x)；T1@v1:R(x,g) | 書き手が居るので wr 0→1 | I (genesis commit)。wr を落とさないことも期待に含める | `m1_commit_at_genesis` | 再説明 |
| E03 | (e) 番兵より前の commit | T0@(0,9):W(x) | 辺なし | I (genesis commit)。(0,9) < (1,0) | inline `test_commit_below_genesis_indeterminate` (`:766`) | inline 被覆済み (境界値) |
| F01 | (f) 読み → 書き | T0@v1:R(x,g),W(x)；T1@v2:R(x,v1),W(x) | wr・ww 0→1、自己辺なし | S。逐次の read-modify-write | `g2_rmw_chain` | 再説明 |
| F02 | (f) 二重書き | T0@v1:W(x),W(x)；T1@v2:R(x,v1)。C の W 件数は 2 | wr 0→1。同じ取引の x は 1 版 | S。別取引の version dup ではない。中間値はこの表現に現れない | inline の容量 test (`test_verifier.py:3003-3008`、同じ取引の二重 W で version dup 0) | inline 被覆済み |
| F03 | (f) 二重読み (同じ版) | T0@v1:W(x)；T1@v2:R(x,v1),R(x,v1)。C の R 件数は 2 | wr 0→1 を 1 本 | S。制約は増えない | 無し (verifier を使う test file 13 本の全文字列リテラルの走査。fixture は `g5` の実データに偶発的にあるだけで独立根拠にしない)。実 silo は 2 度目の読みを read set から返す (S:211-215) ので実 trace には出ない | **未被覆** (合成入力。read set の再利用を外した場合にも生じうる入力で、verifier の辺の生成を検査する) |
| F04 | (f) 書き → 読み (自分の書き) | API 上は T0:W(x),自分の x を読む。trace は T0@v1:W(x) (自分の書きの読みは R にならない)；T1@v2:R(x,v1) | wr 0→1 | S。自分の書きの読みは取引間の依存ではない。返した値の正しさは分からない | trace は A01 型 (自分の書きの読みは R にならない) | 説明の追加 |
| F05 | (f) 別取引の同版書き | T0@v1:W(x)；T1@v1:W(x) | 版から書き手を一意に決められない | I (version dup)。F02 との違いは書き手が別取引であること | `m2_version_dup` | 再説明 (F02 との対が要点) |
| F06 | (f) 二重読み (違う版) | T0@v1:W(x)；T1@v2:W(x)；T2@v3:R(x,v1),R(x,v2) | ww 0→1、wr 0→2・1→2、rw 2→1 | N (G2)。T2 を T1 の前にも後にも置く必要がある | 無し (同じ走査で、二重読みは `test_verifier.py:3041-3045` の範囲外の版の境界 test だけ)。実 trace に出ないのは F03 と同じ | **未被覆** (合成入力) |

- F02 は parser と依存グラフの表現力を試す合成入力で、現行 silo が 2 度の update ごとに W 行を出すという主張ではない (silo は 2 度目の update を飛ばし、最終の write set を出す: S:529、:611-616)。
- **区分の集計 (27 案):** 再説明 13 (A01〜A03、B01〜B05、C02、E01、E02、F01、F05)、inline 被覆済み 10 (B06、C03、D01〜D06、E03、F02)、説明の追加 2 (C01、F04)、**未被覆 2 (F03、F06)**。
- 「inline 被覆済み」は、test の中で作る合成入力 (`_tmp_trace()` の文字列、helper で組み立てる文字列、C03 のように直接作る空 file) による test が同じ意味を押さえているもの。fixture dir として置くかどうかは実装のときに決める (置けば §5.2 の凍結一覧の更新が要る)。B06 は巡回としては被覆済みで、分類 `G1c` を独立に固定する assert だけが無い。
- 「未被覆」の 2 案は、本書の走査 (fixture 22 件と、verifier を使う test file 13 本の全文字列リテラルを隣接連結して C..E の frame 内の同じ取引・同じ key の R を探す。`test_verifier.py` の `_tmp_trace` 呼び出しは 62 箇所) で同じ意味の test が見つからなかったもの。走査の生出力は `raw/double-read-scan.txt` (走査 script は repo に入れず job dir に置いた)。文字列リテラルに現れない形 (実行時の計算だけで作る trace) の test までは調べていない。

### 3.1 verifier 側の壊れ方をどの案が殺すか

「殺す」= 手で決めた期待と、壊した verifier の結果が食い違うこと。verdict が同じでも分類や辺を期待に含めないと殺せないものを分けた。新しい gate・検査の提案ではなく、コーパスの識別力の整理である。

| verifier 側の壊れ方 | 殺す案 | 識別点 | 限界・既存の被覆 |
|---|---|---|---|
| 常に serializable | B01〜B03 | 手で導いた巡回がある | 実データは `r8` |
| 常に non-serializable | A01〜A03 | 直列順がある、または辺が無い | 実データは `g6` |
| 分類器が常に G2 | B06 | 巡回の辺が wr だけ = G1c。**分類まで比べる必要がある** | 正常な YCSB の trace だけでは区別できない。同型の既存 trace (`_ordinal_witness_trace`) は巡回だけを assert し分類を見ない |
| 版比較が epoch を無視 | B05 | tid だけで並べると巡回が消える | `r6` / `r7` |
| 長さ 4 以上の巡回を無視 | B03 | 短い巡回の無い長さ 4 | **現在は `r9_dense_cycle4` が被覆** (D799 の時点では未被覆。D1455) |
| framing violation を常に 0 | D04 | 件数は合い、E だけが無い | D05 は複数の framing 理由を併発させる |
| fixture の hash / dir 名で結果を返す | A01・B01 などの未登録の同型表現 (key の改名、txid の置換、thread 配置の変更) | 手で導いたグラフは同型で保たれる | **有限のコーパスでは任意の lookup 実装を原理的に排除できない** |
| rw を直後版でなく最新版へ張る | B04 | 1→2 が 1→3 に置き換わると巡回が消える | `r5` |
| rw があれば即 non-serializable | A02 | rw 1 本で巡回なし | `g4` |
| rw / ww / wr の生成を落とす | B01 / B02 / B03 | それぞれの辺が巡回の唯一の閉じ手 | `r1` / `r2` |
| commit 証人を無視する | D01、D06 | 同じ prefix に外の件数の差だけを与える | inline `:1265`、`:1326`、`:1484` |
| 欠番を無視する | D02 | 独立な key なので orphan も巡回も出ない | inline `:716` (fixture dir には無い) |
| orphan を genesis 扱いする | C02 | (1,7) の書き手が居ない (g とは違う) | `integrity_orphan` |
| 書き手の居ない読みを全部 orphan にする | E01 | g は初期版として許される | genesis 読みを持つ既存の緑 |
| 同じ取引の多重書きを別版 / version dup にする | F02 と F05 の対 | F02 は書き手 1、F05 は書き手 2 | `m2` と inline `:3003-3008` (二重 W で version dup 0) |
| 二重読みで辺を重複して数える | F03 | 制約は 0→1 の 1 本 | 辺の集合まで期待に含める必要。未被覆 |
| 二重読みの後の方だけを残す | F06 | 古い版の読みの rw 2→1 を失うと偽の緑 | 未被覆 |
| genesis への commit を許す / g を読めば書き手の探索を省く | E02、E03 | 番兵以下の commit、実在する wr 0→1 | verdict だけでは殺せず、辺も比べる |
| 空の trace を認証する | C03 | 取引 0 件 | inline `:336` |
| X / P を無視する | (コーパス外) V03〜V06、V13〜V16 の 1 thread の走 | 巡回 0 で証拠面の違反だけが残る | `m3` / `m4` |
| 値の破損・中間値・phantom・liveness を緑にする | (殺さない) | 読み書きの版の射影が同じなら区別できない | **verifier の欠陥ではない** (§2.2、§4.3) |

注: 現行の `test_capacity_all_fixture_results_match_frozen_baseline` は trace を持つ fixture dir の集合を 22 件に固定する (§5.2)。上の案を fixture dir として足すなら凍結一覧の更新が同じ変更に要る。

## 4. 意味の異なる CC 変異の検出期待表

段 2 の Codex 起草 (`verbatim/s2-plan.md`、C01〜C34) を段 4 で裁定したもの (`verbatim/s4-ruling.md`)。**V 番号は起草の C 番号と同じ** (C01 → V01)。裁定で V30 (si の GC、期待を書けない) を外し、V35 (変異) と V36 (無改変の si、変異ではない) を足した。段 6 レビュー (`verbatim/s6-review.md`) の所見で si の 3 行を §4.5 に分け、期待を条件付きに直した。

**読み方:**

- source の略号: **S** = `external/ccbench/cc/silo/transaction.cc`、**M** = `cc/mocc/transaction.cc`、**SI** = `cc/si/transaction.cc` (pin `e9e477ca`、patch 適用前の行)。
- verdict: **S** = serializable (certified を含む)、**N** = non-serializable、**I** = indeterminate、**E** = parse error。
- **巡回と integrity 違反が同時にあると N が優先する** (`model.py:511-514`)。「X なら I」「orphan なら I」は巡回が無いときの話である。
- 「schedule 依存」= 異常を許す変更でも、有限の走で必ず起きるとは限らない。起きなければ、silo と計装つき mocc では S のまま、証拠面の無い si と素の pin の mocc では I。
- M の行は `patches/instr-mocc-lock-coverage.patch` を重ねた build が前提 (素の pin の mocc は巡回なしでも I)。
- 帰属は「その変更だけを戻した source と比べる」で確かめる (並行走の schedule まで同じになるという意味ではない)。
- **すべて静的な推定で、実行結果ではない。** 既存の記録は §5.1 を指す。

### 4.1 巡回 (G2) を作る見込みの変更

| V | protocol | 既存 / 新規 | 変更 | 外す機構 | source | 期待 | 発生条件 | 注記 |
|---|---|---|---|---|---|---|---|---|
| V01 | silo | 既存 `broken-silo-norw-validation` | 読み集合の版が変わっていても abort しない | 古い読みのままの commit の防止 | S:453-460 | N (巡回)。起きなければ S | 2 thread 以上で共有 key を読み書き。schedule 依存 | 記録は §5.1 (2026-06-18 に 1,310 巡回) |
| V02 | silo | 既存 `broken-silo-highkey-validation` | V01 を key id ≥ 1000 に限る | V01 と同じ (到達条件だけ違う) | S:453-460 | N。対象 key に競合が届かなければ S | 1000 以上の key に競合が届くこと | V01 と同族。記録は §5.1 (100 万 key・48 thread・3 s で 5 巡回、200 tuple では S) |
| V17 | silo | 新規 | validation 条件 3 (他者が lock 中の読み key なら abort) を外し、版の一致検査は残す | 他者の未公開の書きと validation の競合の排除 | S:465-473 | N。起きなければ S | 2 thread 以上。互いに相手の書く key を読み、自分の別 key を lock し、双方が公開前に検証する schedule | X / P は正常のまま起きうる |
| V18 | silo | 新規 | commit TID を読み集合の最大 (`max_rset_`) だけから作り、書く key の現版 (`max_wset_`) を外す | 書く key の版が単調に増えること | S:566-567 | 版が逆転して巡回が出れば N、同じ版になれば I (version dup)、起きなければ S | `rmw=false`、別 worker の履歴差で古い版より小さい TID が出る schedule | 単一理由ではない。巡回は「版順の証拠が壊れた」ことの帰結で、実値の履歴が非直列化だった証明ではない |

### 4.2 巡回を作らず integrity・証拠面で I に倒れる見込みの変更

| V | protocol | 既存 / 新規 | 変更 | 外す機構 | source | 期待の層 | 期待 | 発生条件 | 注記 |
|---|---|---|---|---|---|---|---|---|---|
| V03 | silo | 既存 `broken-silo-lockskip-validation` | 非 INSERT の write lock 取得を飛ばす | 書き手の lock 獲得の被覆 | S:158-191、X は :628-631 | X | 1 thread は I、巡回が併発すれば N | 1 thread でも update 1 回で発火 | 1 thread なら単一理由 |
| V13 | mocc | 既存 `broken-mocc-lockskip-validation` | validation の writer lock を飛ばす | V03 と同じ | M:990-1000 | X。4 thread では version dup と巡回も | 1 thread は I、4 thread は N (記録) | 計装つき build | V03 と同族。4 thread では単一理由でない (§5.1) |
| V04 | silo | 既存 `broken-silo-early-unlock-validation` | payload 更新の前に lock を外す | 公開までの lock 保持 | S:641-660 | X (保持破れ) | I、巡回が併発すれば N | 非 INSERT の書き。1 thread で可 | 入口の X は 0、保持の X だけ |
| V15 | mocc | 既存 `broken-mocc-early-unlock` | 入口検査の後に外し、公開の直前に再取得 | V04 と同じ | M:1158-1196 付近 | X。4 thread では version dup と巡回も | 1 thread は I、4 thread は N (記録) | 計装つき build | V04 と同族。4 thread では単一理由でない |
| V16 | mocc | 既存 `broken-mocc-hot-update-unlock` | hot の update 経路で早期 lock を外す | hot 経路の lock 保持 | M:459、1069、1195 付近 | X。4 thread の hot では version dup も | hot は I (巡回 0)、cold / default は S (記録) | `rratio=0, rmw=false, max_ope=1` で温度閾値 0 のときだけ届く | V04 と同族 (経路違い)。単一理由は 1 thread の hot だけ |
| V05 | silo | 既存 `broken-silo-permutation-erase` | 並べ替えの直後に 1 要素を落とす | write set の要素数の保存 | S:408-432 | P (size-changed) | I | 非空の write set。1 thread で可 | |
| V14 | mocc | 既存 `broken-mocc-permutation-erase` | 同上 | 同上 | M:990-991 | P | I (記録: 全 6 走で巡回 0) | 計装つき build | V05 と同族 |
| V06 | silo | 既存 `broken-silo-permutation-swap` | 1 要素の record pointer を別要素で上書き | record pointer の multiset の保存 | S:408-432 | P (rcdptr-set-changed) | I | 異なる 2 要素以上。同じ pointer の二重 lock で abort / 停止もありうる | size だけ見る検査では捕まらない側 |
| V19 | silo | 新規 | commit スタンプを非 genesis の固定値にする (lock / latest の bit 処理は残す) | 版の一意性 | S:579-582 | version dup | I、巡回が併発すれば N | 1 thread、同じ key への blind write を 2 取引。競合不要 | 小さい履歴なら単一理由 |
| V20 | silo | 新規 | tuple に公開する版だけを、C / W 行に出した版と違う未使用の値にする | trace の版と実際に読まれる版の一致 | S:660、:606-616 | orphan | I、巡回が併発すれば N | 1 thread の「書き → 別取引の読み」で可 | C と W は一致したまま |
| V21 | silo | 新規 | 最後の取引だけ、validation の後に writePhase を呼ばず成功を返す | commit 成功と trace / 適用の対応 | S:706-709 | commit 証人 | 証人ありは I、**証人なしは残りの prefix が S になりうる** | 最後の成功取引、先行の完全な取引 1 件以上 | §2.2 の末尾欠落と同じ型 |

### 4.3 宣言範囲の外・trace に現れないため緑のまま通る見込みの変更 (盲点)

これらは verifier の欠陥ではなく、判定の宣言範囲 (§2.2) の外である。論文ではこの行を「検出しなかった = 正しい」と読ませないために併記する。

| V | protocol | 既存 / 新規 | 変更 | 外す機構 | source | 期待 | 発生条件 | 注記 |
|---|---|---|---|---|---|---|---|---|
| V07 | silo | 既存 `broken-silo-sort-nonswo` | 比較を `&a != &b` にする (反対称性を破る) | 並べ替えの strict weak ordering | S:408 | **結果を固定できない (未定義動作)**。完走して他の違反が無い空でない prefix は S になりうる。write set が壊れれば P で I (巡回が併発すれば N)、空なら I、hang なら verdict 無し | write set 16 要素以上 (`max_ope ≥ 16`) で hang (記録) | timeout を巡回の検出に数えない |
| V08 | silo | 既存 `broken-silo-trigger-misattr` | lock 競合の abort を node validation と誤記録 | abort 要因の記録の正確さ | S:160-164 付近 (骨格の追加後) | S | 骨格と集計計装、lock 競合 | 正しさは無傷。構造ゼロ検査だけが赤 (記録)。「緑であるべき」側でもある |
| V09〜V12 | silo | 既存 `broken-silo-write-intent-{erase,forge,opswap,ptrswap}` | validation の後・lock の前に write set を改竄 (喪失・捏造・op 改変・pointer 交換) | 呼び出し側が意図した書きと write set の一致 | S:435-437 付近 | **現行 pin では S になりうる** (`I` の emitter が無い)。`I` のある branch の記録は I | 1 thread・単発の書きで分離できる | §5.1。`I` の emitter の着地が前提 |
| V22 | silo | 新規 | read の再確認で 2 度目の TID を無条件に採り、payload を取り直さない | payload と読んだ版の整合 | S:263-277 | 不整合な値だけなら S。別の依存異常が重なれば N | 2 thread 以上、payload の複写と再読の間に更新 | trace は版しか見ないので帰属できない |
| V23 | silo | 新規 | 書き込む payload の一部を誤った値にする (版・lock・読み書き集合は保つ) | 書く値の正しさ | S:658-660 | S | 1 thread・単一 update で可 | 値は trace に出ない |
| V24 | silo | 新規 | node map の検証 (phantom 防止) を外す | 範囲読みの構造変化の検出 | S:477-485、:298-302、:733-740 | S (現行 YCSB は範囲読みも insert も無いので機構に届かない) | 範囲操作が要る | YCSB で無発火でも安全の証明にならない。TPC-C 段 2 の設計 §6.2 が正本 |
| V25 | mocc | 新規 | 正準順への復元 (解放と CLL の除去) を飛ばし、逆順の lock を持ったまま追加で取る | deadlock を避ける lock 順 | M:834-888 | 完走した prefix は S、空なら I。停止自体に verdict は無い | 計装つき、hot、2 thread 以上、`max_ope ≥ 2`、逆順のアクセス | X は「要る lock が無い」を見る検査で、相互待ちは見ない |
| V26 | silo | 新規 | 自分の書いた key を読むとき、write buffer でなく旧 tuple の payload を返す | read-your-writes | S:216-219 | S | 1 thread、同じ key の書き → 読み、`max_ope ≥ 2` | 取引間の依存グラフは同じ。取引内の意味だけ壊れる |
| V27 | silo | 新規 | 同じ key への 2 度目の update を扱う枝で、buffer の内容を誤って扱う | 取引内の多重書きの値 | S:529、:547、:611-616 | S | 同じ key を複数回 update | 現行 silo は 2 度目の update を `searchWriteSet` で飛ばす (S:529)。外に出るのは 1 版だけ |
| V35 | silo | 新規 (裁定 R4、要確認) | commit TID を書き集合の最大 (`max_wset_`) だけから作り、読み集合の最大を外す | 「commit TID は読んだ版より大きい」という Silo の TID 規則 (recovery の直列順) | S:566-567 | S の見込み (書く key の版の一意性と validation の版比較は保たれる) | 別 worker が書いた新しい版を読んで、それより小さい TID で commit する schedule | 直列化可能性の外の規則。`dsg.py:807-818` の分類の前提 (wr は commit 順に前向き) が崩れるので、他の異常と重なると巡回が G1c と分類されうる (verdict は同じ) |

### 4.4 正しさを壊さない対照 (緑であるべき)

誤検出の側を測るための行。これが N / I になれば verifier か計装の誤りを疑う。

| V | protocol | 変更 | 変えるもの | source | 期待 | 条件 | 独立の根拠 |
|---|---|---|---|---|---|---|---|
| V31 | silo | abort 後の backoff 呼び出しを 1 回から 2 回へ | 再試行の間隔だけ | S:27-47 | S | `BACK_OFF` 有効、abort がある非空の走 | CC の判定経路を通らない |
| V32 | silo | write set の並べ順を全 worker 共通の逆向きの全順序へ | lock を取る順だけ | S:408、:145-193 | S、X / P は 0 | 異なる 2 key 以上 | 要素と strict weak ordering を保つ |
| V33 | silo | validation の前に、特定の入力の取引を保守的に abort | commit を許す集合を狭める | S:383、:437-438、:27-40 | S | 一部の取引は commit する条件 (全部 abort すると空 trace で I) | abort を増やしても commit 経路の lock と validation は同じなので、commit した取引の履歴の直列化可能性は保たれる |
| V34 | mocc | 温度述語 4 箇所を `!(temp < threshold)` の形へ等価変形 | 述語の書き方だけ | M:296、:459、:566、:970 | 計装つきは S、素の pin は I | 閾値の境界を含む | 値ごとの真偽が同じ |

### 4.5 si の行 (現状は parse error、v2 化後の期待は条件付き)

si は現行の parser が v1 trace を拒否するので、3 行とも現状の期待は **E** で、現行の検出力に数えない。v2 化後も si には証拠面が無いので、**巡回が出なければ S ではなく I** になる (`model.py:450-467`, `:505-515`)。さらに si の update / delete は同じ key の read set 要素を消すので (SI:239-247, :361-365)、同じ key を読んでから書く取引の R は trace に残らない。

| V | 既存 / 新規 | 変更 | 外す機構 | source | 現状 | v2 化後の期待 | 条件と注記 |
|---|---|---|---|---|---|---|---|
| V36 | 無改変 (裁定 R3)。**変異ではない** | 無改変の si (snapshot isolation は write skew を許す) | 直列化可能性 (分離水準が弱い) | SI:614-616 (`verify_exclusion_or_abort` は SSN の anti-dependency 検査をしない no-op) | E | 残った R / W が巡回を作る schedule なら N、巡回が無ければ I | 読みと書きが別 key の write skew (`rmw=false` の高競合、2026-06-18 の条件) なら R が残る。2026-06-18 に 3,576 巡回 (当時の verifier、§5.3) |
| V29 | 新規 | 版の first-updater-wins の abort を外す | snapshot 後の競合上書きの拒否 | SI:198-206 | E | **典型的な lost update (同じ key を読んで更新) は巡回にならず I**。2 取引の R が update で消え、W 2 件の ww 1 本だけが残る | N を期待するには、残る R から巡回を手で導ける別の履歴が要る (未設計) |
| V28 | 新規 | 版の選択で aborted / inflight の除外を外す | commit 済みの版だけを読む可視性 | SI:153-165 | E | abort が確定し、読んだ版が非 genesis で、同じ (key, 版) の書き手が trace に無く、その R が後の update で消されない場合だけ orphan で I。inflight の版が後で commit すれば orphan として現れない経路がある | si は読んだ版の番号を値で保存せず、commit 時に version pointer から cstamp を取り直す (SI:164, :541-544)。盲点とも検出とも言い切れない |

### 4.6 数え方と、実走で確かめること

- **ID は 35 項目** (V01〜V29、V31〜V36。V09〜V12 を 1 行にまとめたので表の行は 32)。うち **V36 は無改変の si で変異ではない**ので、**変異は 34** (既存 16 + 新規 18)。同族は V01/V02、V03/V13、V04/V15/V16、V05/V14、V09〜V12 で、**族にまとめると 26**、うち「正しさを保つ対照」4 を除く **22 が正しさ (または宣言範囲外の規則) を変える機構**である。依頼の「意味の異なる変異 20〜40」はこの 22 で満たす。
- 期待の層ごと (ID で数える): 巡回 4 (V01, V02, V17, V18)、integrity・証拠面 11 (V03〜V06, V13〜V16, V19〜V21)、盲点 13 (V07〜V12, V22〜V27, V35)、si (現状 E) 3 (V28, V29, V36)、対照 4。
- **前提の違い:** 既存 patch のうち現行 pin に文面がそのまま当たるのは silo の 11 本 (§5.1。build と発火は未確認)。新規の silo 行は patch を書けば同じ前提で走る。mocc の行は計装 patch の上に重ねる。si の 3 行 (V28, V29, V36) は emitter の v2 化が先 (§5.3)。V08 は trigger-gating 骨格の上でだけ当たり、V09〜V12 は当たっても現行 pin では `I` が出ない。
- **実走で確かめる対象は「期待」と「結果」の食い違い**であり、次の 4 つを分けて記録する: (1) 期待どおりに検出、(2) 期待した層と違う層で検出 (例: X を期待して巡回)、(3) 起きなかった (schedule 依存の未発生。silo と計装つき mocc では S のまま、si と素の pin の mocc では証拠面が無いので I)、(4) 誤検出 (対照が N / I)。(3) を「検出力が無い」と書かず、条件を上げた再走と分けて数える。
- 多 thread・本番に近い規模の走では、1 つの変更が複数の層を同時に発火させる (§5.1 の mocc)。単一理由を示したい行は 1 thread・小規模の条件を別に置く。

## 5. 既存資産の再利用範囲

### 5.1 既存の壊した CC patch 16 本

`git apply --check` (fuzz なし、作業ツリーを変えない) を pin `e9e477ca` に対して 2026-09-22 09:25 JST に実行した。生出力は `raw/apply-check-e9e477ca.txt`。

| patch | 素の pin に当たるか | 前提 | 記録済みの結果 (実行結果、日付つき) | 再利用の仕方 |
|---|---|---|---|---|
| `broken-silo-norw-validation` (読み集合の再検証の abort を外す) | 当たる (offset 67 行) | なし | 2026-06-18 (commit `0ffb2a3c2`): `rmw=true, zipf 0.9, 50 tuple, max_ope 5, 4 thread, 1 s` で 1,310 巡回・non-serializable、外すと certified (`patches/README.md` の「実証 (2026-06-18, clean ablation)」)。fixture `r8_silo_broken_norw` の元 | 巡回層の正例としてそのまま (§4 の V01) |
| `broken-silo-highkey-validation` (同じ abort を key id ≥ 1000 のときだけ外す) | 当たる (offset 67 行) | なし | 2026-07-06: `100 万 key, 48 thread, zipf 0.9, 読み 50%, rmw=false, max_ope 10, 3 s` で G2 5 本・non-serializable、200 tuple 構成では certified (D36、同 README) | 「規模と条件で検出が変わる」例として (V02) |
| `broken-silo-lockskip-validation` (lockWriteSet の write lock 取得を外す) | 当たる | なし | 2026-07-06 (`s3_lock_coverage.json`): 1 thread で巡回 0・`X` あり・indeterminate | 証拠面 `X` の正例 (V03) |
| `broken-silo-early-unlock-validation` (書き込み前に lock を外す) | 当たる (offset 56 行) | なし | 同上: `X` (保持破れ) だけ | 同上 (V04) |
| `broken-silo-permutation-erase` / `-swap` (並べ替え後に要素を落とす / 差し替える) | 当たる (offset 1 行) | なし | `s5_permutation_coverage.json`: `P` (size-changed / rcdptr-set-changed) で indeterminate | 証拠面 `P` の正例 (V05, V06) |
| `broken-silo-sort-nonswo` (反対称性を破る comparator) | 当たる | `SORT_VARIANT` 枠 | 16 要素以上で introsort が hang (release / ASan、同 README)。verdict の話ではない | 判定でなく「未定義動作を crash / hang で捕まえる」正例。検出表では 盲点の行 (V07) |
| `broken-silo-trigger-misattr` (abort 要因の誤記録) | **当たらない** | trigger-gating 軸の骨格 (`BACKOFF_TRIGGER_GATING` 枝) と集計計装 `patches/instr-silo-backoff-trigger-gating-tally.patch` | 2026-07-10 (`s8a_trigger_gating_coverage.json`): 直列化可能性は無傷で verifier は緑、構造ゼロ検査だけが赤 | 「正しいので緑であるべき」対照 (V08) |
| `broken-silo-write-intent-{erase,forge,opswap,ptrswap}` (validation 後に write set を改竄) | 当たる (offset −51 行) | **`I` の emitter (izanagi-trace 枝) が現行 pin に無い** | 2026-07-29 (`t152_write_intent_coverage.json`、`I` emitter のある branch): 巡回 0 のまま `I` だけで indeterminate | 現行 pin では `I` が出ないので、要素の喪失・捏造は「書きが少ない / 多いだけの直列化可能な履歴」として certified になりうる (T-152 が閉じようとした死角)。§4 の V09〜V12 |
| `broken-mocc-lockskip-validation` | **当たらない** | `patches/instr-mocc-lock-coverage.patch` の上に重ねる (記録 JSON の `patches` 欄) | 2026-09-18 記録 (`output/env/pegasus/calibration/s3_mocc_mutation_proof.json`、pin `e9e477ca`、200 tuple・zipf 0.9・読み 0%・rmw・max_ope 5・1 s): 1 thread は `X` だけで indeterminate、4 thread は巡回 587 / 3,882 / 3,622 (hot / cold / default) に `X` と version dup (3,564 / 21,954 / 20,668) が併発して non-serializable | 単一理由でない例 (V13) |
| `broken-mocc-early-unlock` | **当たらない** | 同上 | 同 JSON: 1 thread は `X` だけ、4 thread は巡回 3,636 / 1,556 / 1,437 に `X` と version dup (17,866 / 8,807 / 8,324) が併発 | 同上 (V15) |
| `broken-mocc-permutation-erase` | **当たらない** | 同上 | 同 JSON: 全 6 走で巡回 0・`P` だけで indeterminate | 証拠面 `P` の正例 (V14) |
| `broken-mocc-hot-update-unlock` | **当たらない** | 同上。発火は blind update (`rmw=false, max_ope=1`) で hot 分岐に入るときだけ | 同 JSON: hot の 1 thread は `X` だけで indeterminate、hot の 4 thread は巡回 0 のまま `X` と version dup 67,777 で indeterminate、cold / default は certified (hot 分岐に届かない) | 「発火条件が揃わないと緑」の例 (V16) |

注: 2026-09-21 の [T-2844] 記録 (worklog entry 1818) は「single の負例 3 本は所定の X / P だけで indeterminate」と書くが、これは 1 thread の話である。4 thread では lockskip・early-unlock・hot-update-unlock (hot) のすべてで version dup が併発し、lockskip と early-unlock は巡回も出す (上の JSON。version dup は各 run の検証結果の `integrity.version_dups`)。**検出の型は thread 数と regime を添えて書く。**

### 5.2 既存 fixture 22 件と verifier の test

- **fixture:** 緑 8 (g1〜g7、p1)・赤 9 (r1〜r9、全部 G2)・indeterminate 5 (integrity_orphan、m1〜m4)。実 emitter 由来は g5 / g6 / r8 の 3 件。一覧と説明は `orchestrator/tests/fixtures/README.md`。
- **独立性 (D799):** 期待値が verifier の外で決まるのは g6 (1 thread なので巡回し得ない) と r8 (G2 が少なくとも 1 本あることを verifier を使わない監査で確認) だけで、他の実データ fixture の期待値は verifier 自身の出力である。この対が殺すのは「常に緑」「常に赤」の 2 つの定数実装だけで、「分類器が常に G2」「版比較が epoch を無視」「長さ 4 以上の巡回を無視」「framing violation を常に 0」「fixture の hash で結果を返す」は通す (D799 決定 2)。このうち長さ 4 以上の巡回は、後に D1455 (2026-09-02) の `r9_dense_cycle4` が被覆した。
- **inline の合成 trace:** `test_verifier.py` の `_tmp_trace()` (60 箇所超の呼び出し) による test が parse・frame・integrity・証拠面の境界を押さえる。欠損系 (末尾欠落・R/W/E 欠落・file 欠落) はここにだけある。
- **凍結一覧:** `test_verifier.py:2893` (`test_capacity_all_fixture_results_match_frozen_baseline`) は 22 件の結果 hash を凍結し、**trace を持つ fixture dir の集合がこの 22 件と一致することも assert する**。§3 のコーパスを fixture dir として足すなら、この一覧の更新が同じ変更に要る (inline の合成 trace として足すなら要らない)。
- **property-based・乱数生成の履歴 test は無い** (`hypothesis` の import なし)。
- **再利用の仕方:** §3 のコーパスは既存 22 件と inline test を「被覆済み」として数え、新しい検査対象は「未被覆」の 2 案と B06 の分類の assert だけにする (§3 の表の「区分」列)。

### 5.3 si の v1 制約

- **事実:** si の emitter は `izanagi_trace::emit_commit` (5 field の C 行) を使い、E 行を出さない (`external/ccbench/cc/si/transaction.cc:539-552`)。silo は trace v2 化のときに自前で 7 field の C 行と E 行を書くよう切り替え、`emit_commit` は si 用の v1 helper として残した (`cc/silo/transaction.cc:594-600` のコメント: trace.hh が当時の編集面の外だったため)。parser は 5 field の C 行を `trace v1 C record is not supported` で拒否する (`parse.py:323-326`、v2 専用化は commit `fb5e74a17`、2026-08-12、[T-816])。
- **帰結:** 現行の pipeline では si の trace はどの workload でも parse error になり、検出の正例として使えない。
- **過去の記録の扱い (規律 7):** 「無改変の si で 3,576 巡回」(2026-06-18、`docs/phase1.md` の Approach B、`rmw=false` の高競合 workload、当時の verifier は v1 を受理) は当時その道具で得た事実であり、無効にならない。ただし**現行の verifier では再現できない**ので、論文で検出力の実証として引くときは日付と当時の trace 形式を添え、現行の検出力の主張には §4 の新しい走 (si を使うなら emitter の v2 化の後) を使う。論文稿 2026-09-21c の「検出力を二重に実証」の段落はこの断りをまだ持たない (本 wave は論文稿を編集しない)。
- **v2 に上げても残る制約:** si には証拠面 (`X` / `P`) が無いので certified にはならず、使い道は「非直列化の検出」に限られる。加えて si の update / delete は read set から当該要素を消す (`cc/si/transaction.cc:239-247`, `:361-365`、TPC-C 設計 §3.4) ので、同じ取引で同じ key を読んでから書くと、その R 行が trace から消え、その R が作る rw 辺が落ちうる。YCSB では `rmw=true` の書きはすべてこの形で、`rmw=false` でも zipf で同じ key が 1 取引に重なれば起きる。落ちる方向は検出を弱める側 (偽の緑の側) で、どれだけ落ちるかは測っていない。
- **直す場所:** si の `transaction.cc` と `include/trace.hh` はどちらも coder の編集面 (`hooks/guard_write.py:44-45` の `EVOLVE_BLOCK_SOURCES` = `include/backoff.hh`・silo / mocc の `transaction.cc`) の外で、D16 の `izanagi-trace` 枝に Codex author が commit し、pin 前進 (人間の push) を経る。[T-2854] (TPC-C の v3 frame) の設計は si を「任意の実装単位 (12)・検出専用」にしている (`output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §5.2、§7.1)。YCSB の si を v2 に上げる作業はそこに相乗りできる。

## 6. 大 trace の容量評価の計画

### 6.1 既に測ってあること (2026-09-20、`output/insights/2026-09-20/verifier-capacity/README.md` §4、改修版 verifier = D2181)

| trace (保全済み、S-1 系列の fixed backoff) | 取引数 / 辺数 | verify 本体の wall | node の記憶量の山 | 判定 |
|---|---|---|---|---|
| write-heavy 10 s | 8.32M / 85.0M | 297 s | 15.2 GiB | serializable |
| balanced 10 s | 14.75M / 215.1M | 478 s | 32.4 GiB | serializable |
| read-heavy 6 s | 32.75M / 594.8M | 896 s | 81.2 GiB | serializable |

- 他に 3 s / 6 s の 11 本も完走している (同 §4)。完了条件は node 128 GiB のうち 115 GiB 以内・3,600 s 以内 (同 §4 の裁定 D-1)。
- job 単位の実測 (同 wave の job dir、旧版と新版を同じ job で順に走らせた compare): balanced 10 s = 1,224 s、write-heavy 10 s = 805 s、read-heavy 6 s = 1,868 s (生の抜き出しは `raw/verifier-capacity-job-elapse.txt`)。compare は旧版と新版の両方を含むので、新版だけを走らせる job の費用とは違う。同じ抜き出しの profile job (`P-*`) は旧版の profile で、失敗を観測した走 (例: `P-wh10` = 2,717 s は旧版が worker の OOM で停滞した走) と完走の参照走 (bal6・rh6・wh3、worker 数を減らした走など) を含み、compare とも条件が違う。
- 依頼文の「balanced 10 秒で 32 GiB、read-heavy 6 秒で約 81 GiB、ノード上限約 115 GiB」はこの表の値である。

### 6.2 まだ測っていないこと

| # | 何が未測か | なぜ効くか | 前提 |
|---|---|---|---|
| U1 | **巡回の多い大きな trace** (上の表は全部 serializable) | §4 の検出の走は non-serializable の trace を作る。巡回が多い・巨大な強連結成分がある場合の SCC 計算と最短巡回探索の時間・記憶量が分からない。落ちても候補は certified にならない (fail-closed) ので安全は崩れないが、検出表の「non-serializable」を書けなくなる | 本番に近い構成で壊した CC を走らせた trace (現存しない) |
| U2 | **mocc の大きな trace** (計装 patch を当てた build) | 第 2 protocol ([T-2849]、[T-2844]) の検証費用。壊した走では `X` 行が百万行級になる (§5.1 の JSON) ので parse の費用も効く | 計装 patch つき build の本番構成 trace (現存しない) |
| U3 | **read-heavy 10 s** | 入力 trace が無い (同 insight §6)。辺 1.2B 見込みで、今の隣接構造 (`set` / tuple) のままだと 115 GiB を超える見込み (同 §6、§7) | 実験がこの長さを要する場合だけ |
| U4 | **TPC-C の trace** | [T-2854] の v3 frame の着地後。容量の試算は TPC-C 設計 §7.3 (100 万 commit あたり段 1 約 1.37 GB、全 5 取引約 3.15 GB) | v3 の実装 |
| U5 | **trace を取る側の費用** (trace-enabled build の走・書き出し・圧縮保全の job 時間) | 検証の前段の費用。本書が調べた記録には job 単位の値が無い | 最初の 1 本で測る |

### 6.3 進め方

1. **(計算なし) 要る長さを先に決める。** VLDB の実験 (P1 の関数単位の候補、P2 の比較基盤、P3 の反復、P4 の留保条件、TPC-C) が検証する trace の workload・protocol・長さを列挙し、6.1 の実測範囲 (write-heavy / balanced は 10 s まで、read-heavy は 6 s まで、silo、巡回 0) に入るものと入らないものに分ける。入るものは新しく測らない。
2. **範囲外で、実験が実際に要るものだけを測る。** 候補は U1 (壊した silo を本番に近い構成の balanced / write-heavy で各 1 本)、U2 (P2 が mocc を使うと決まったら 3 workload)、U3 (要る場合だけ)。記録は 6.1 と同じ probe (容量 wave の job dir の `probe/verifier_profile_probe.py`) の phase ごとの wall と記憶量に、成分の数・最大成分の大きさ・報告した巡回の数を足す。
3. **見積り:** verify 本体は 6.1 の wall からの換算 (balanced 10 s で約 0.13 node 時間、read-heavy 6 s で約 0.25 node 時間) を目安にする。これは verify 本体だけの値で、job の Elapse (trace の復元・build・待ちを含む) ではない。U5 (取る側) の単価は記録に無いので、最初の 1 本の job Elapse で測ってから残りを見積もる。同じタスクの build・再試行と開発の検査 (受入・焦点走・変異) を含む合計が 2 node 時間以上になるなら、投入前に内訳を示してユーザーの確認を取る (D2212 項 4。開発の検査も数えることと、見積りを job Elapse の実測で出すことは D2219 項 1)。**本書は投入の承認ではない。**

### 6.4 [T-2351] との関係

- [T-2351] は検証の後段 (replay と SCC) の隣接構造を縮める実装項目である (bucket 化した set 再生 + CSR、txid を直接 index にした Tarjan など。候補は容量 insight §7)。
- 本計画はその**発火条件を決める側**にある。6.3 の 1 で「要る長さ」が 6.1 の範囲に収まれば [T-2351] は P0 の前提にならない。U3 のように要る trace が 115 GiB または時間の上限を超えると測られた (または見込みが確かめられた) ときに、[T-2351] を実装するか、実験の長さを 6 s に絞るかを選ぶ。
- U1 で巡回の多い trace の SCC 段が律速と分かった場合も [T-2351] の候補 (Tarjan の index 化) が効く。逆に [T-2351] を先に実装しても、U1 / U2 / U5 は測らないと分からない。

### 6.5 分割して検査する場合の条件

- **時間窓ごとに独立に検査して結果の「かつ」を取るのは、全体の検査と同等ではない。** rw 辺は commit 順を逆向きに走り (§2.2)、読み手がどれだけ遅れて commit するかに上限が無いので、巡回は窓の境界をまたぎうる。窓ごとの検査は境界をまたぐ辺を落とし、偽の緑を出す。
- key で分割するのも同じ理由で不可 (巡回は複数の key をまたぐ)。
- **同等になるのは、全体のグラフの巡回の有無を保つ形**である (例: 全辺を保ったまま辺を外部記憶へ書き出して強連結成分を求める、窓をまたぐ辺をすべて持ち越して窓の間で成分を統合する、巡回の有無を変えないと示せる縮約)。**certified には、これに加えて全体に対する integrity と commit 証人の検査が要る** (分割した部分ごとの integrity は全体の integrity を意味しない)。
- **片側だけ使える近道:** 部分グラフで見つかった巡回が全体の巡回を意味するのは、**部分の各辺が全体の辺か、全体の空でない有向経路に対応するとき**である (例: 直後版が部分に無いために遠い上書き手へ張った rw は、全体では直後版への rw と ww の連鎖で表せる)。取引を抜いて部分を組み直す場合は、版の順序を保つだけでは足りず、各 (key, 版) の書き手が全体と同じ 1 取引に決まることも要る。反例: 全体が `T0@v1:W(x)`、`T1@v1:W(x),R(y,v2)`、`T2@v2:W(y),R(x,v1)` のとき、全体では先に登録された T0 が x の版 v1 の書き手になり辺は `0→2→1` (巡回なし、ただし version dup で indeterminate)。T0 を抜くと書き手が T1 に変わり `1↔2` の巡回ができる (`dsg.py:353-367`, `:641-679`)。この条件の下でだけ、分割した検査は「赤」を確定でき、「緑」は確定できない。

## 7. 論文用の射程文

論文稿 2026-09-21c の「certified の意味」節 (YCSB の点読み・点書きに限った、観測できた trace 上の直列化可能性。述語・phantom、公平性・starvation、観測されなかった実行は保証しない) と矛盾しない形で、長さ別に置く。

**短文 (要旨・序論):**

> certified は、trace を有効にした build を有限回走らせて観測した空でない committed 取引の履歴について、依存グラフに巡回がなく、trace の完全性と証拠面の検査も通ったという判定であり、すべての実行での直列化可能性の証明ではない (現状は YCSB の点読み・点書きに限る)。

**方法節 (4 文):**

> verifier は、trace を有効にした別 build を有限の時間・thread 数・seed で走らせ、その間に commit された取引の点読み・点書き (読んだ版と書いた版) から依存グラフ (Adya) を作り、巡回を探す。巡回があれば non-serializable、commit された取引が 1 件以上あり、巡回がなく、trace の完全性 (欠落・重複・版の不整合) と証拠面 (lock 被覆・write set の保存) の検査も通れば certified、取引が 0 件か、どちらかの検査を確かめられなければ indeterminate とする。certified は観測した履歴についての判定で、観測しなかった実行と schedule、範囲読みの phantom、取引内の中間の値や値そのもの、deadlock や starvation は判定しない。性能は trace を除いた別 build で測るので、certified はその build の実行を直接検査したものではない。

**妥当性への脅威の節 (箇条):**

- 有限の観測: 巡回を作る schedule が走の間に起きなければ見逃す。検出は競合の強さ・thread 数・走の長さに依存する (§5.1 の highkey は本番に近い構成の 3 s で 5 巡回、mocc の lockskip / early-unlock は 1 thread で巡回 0)。
- trace の忠実さ: 判定は emitter が記録した版を信じる。値の破損や取引内の中間の値は版スタンプに現れない (§2.2)。lock 被覆 (`X`) と write set の保存 (`P`) はその一部を補う。
- 宣言範囲: 範囲読み・insert / delete の意味・TPC-C は現行の検査の外 (TPC-C は [T-2854] の拡張で段階的に入れる)。
- 観測者効果: trace を入れた build と性能 build は別 binary であり、trace の除去は規律 1 と D14 の検査で確かめる。trace を入れると interleaving が変わりうる。

**使わない言い方と置き換え:**

| 使わない | 置き換え |
|---|---|
| 正しさを証明した / 安全を保証した | 空でない観測履歴について、巡回がなく完全性と証拠面の条件も満たし、certified と判定された (巡回が無いだけでは certified ではない) |
| すべての実行で直列化可能 | この条件の有限走で観測した履歴が直列化可能 |
| verifier を通った = 正しい CC | この条件で certified だった |
| 検出しなかった = 壊れていない | この条件の走では検出しなかった (§4 の盲点行を併記) |
| si で 3,576 件を検出 (時制なし) | 2026-06-18 の verifier (v1 を受理) で 3,576 巡回を検出した。現行の pipeline では si は検証できない |

## 8. 実行へ進むときの段取りと計算の確認

本 wave は新しい T を起票しない。以下は [T-2847] の残り (完了条件の「検出表・容量の実測表」) を進めるときの順序の案である。

1. **小履歴コーパスの実装** (§3 の「未被覆」2 案と B06 の分類の assert。inline 被覆済みの 10 案を fixture として置くかは同じ変更で決める)。Codex author が test を書く (D95)。inline の合成 trace なら §5.2 の凍結一覧は不変。計算は開発の検査 (焦点走・受入・変異) だけ。
2. **変異の実走** (§4)。既存 16 本は既存の driver (`orchestrator/campaign/s2_verify_calibration.py`・`s3_lock_coverage.py`・`s5_permutation_coverage.py`・`s3_mocc_mutation_proof.py`・`t152_write_intent_coverage.py`) で走らせる。新規の変異は out-of-tree の patch (D16 の第 3 類) として Codex author が書く。変異ごとに build が要るので費用は build が支配的になる見込み。参考の実測: [T-2844] の compute 1 走 (stock 2 走 + 負例 4 走、14 check) は 1 node で Elapse 132 s (worklog entry 1818。build がこの job に含まれるかは本書では確かめていない)。
3. **容量の実測** (§6.3)。
4. **si の v2 化** (§5.3)。[T-2854] の実装単位 (12) に相乗りする。

1〜3 はいずれも、同じタスクで投げる job の合計 (開発の検査を含む) が 2 node 時間以上になるなら投入前に内訳を示してユーザーの確認を取る (D2212 項 4、D2219 項 1)。

**P1 (関数単位のコード空間) との関係:** D2214 の軸 `silo-function-policy` (条件付き採用) の v1 は、LLM に abort 後の待機・lock 競合時の retry / abort・commit 後の状態更新の方策だけを開き、validation・lock・TID 生成・writePhase・trace は骨格に残す。D2214 項 2 の安全の主張は条件付きで、「メモリ安全・外部干渉なし・契約に適合した方策が正常に返る限り、方策の選択は固定骨格の直列化可能性の条件を弱めない」までである。この条件の下では、§4 の層で言えば v1 の候補が作りうる変化は「正しさを保つ対照」(V31・V33 型) と「盲点」のうち liveness (V25 型の停止・飢餓) の側で、§4.1・§4.2 の機構は骨格に残る (条件が破れた場合、例えばメモリ破壊は別の話で、本書は扱わない)。D2214 項 2 も「v1 は LLM が壊した CC 論理を verifier が捕らえることを実証しない」と書く。**LLM が生成した候補を verifier が捕まえた記録 (差分分析 §0 の不在) を作るには、例えば §4.1・§4.2 のように、固定骨格が守っている条件を候補が変えられる空間が要る** (§4.1・§4.2 の列挙は必要な機構の網羅ではない)。

## 9. 限界・言わないこと

- 表の「期待」はすべて静的な推定で、実行結果ではない。特に「発生条件」は source を読んだ推定であり、有限の走で本当に起きるかは走らせないと分からない。
- 既存の記録は、日付・構成・当時の verifier / pin を添えて引いた。現行コードとの差だけを理由に無効とはしない (規律 7)。逆に、現行で再現できないものを現行の検出力として書かない。
- 適用検査 (§5.1) は patch の文面が当たるかだけを見た。build が通るか・macro を定義したときに意図どおり発火するかは見ていない。
- 本書は verifier・fixture・論文稿・roadmap を変更しない。gate・検査・台帳は足さない。
- TPC-C の正例・負例は `output/insights/2026-09-21/tpcc-trace-certification-design/README.md` §6 を正本とし、ここでは再設計しない。
- si の GC (公開境界の更新) を壊す変更は、GC の内部を読んでおらず期待を書けないので表から外した (起草の C30)。
- 「取引内の中間の版を他の取引が読む」を現行 YCSB source の 1 か所の変更で確実に作り、しかも X / P を発火させない案は見つかっていない (起草の未確認点)。V27 と F02 は「中間値が trace に現れない」ことの対照に留まる。
