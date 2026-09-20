単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/docs/paper-story/2026-09-21.md (**レビュー対象の新版**、725,871 bytes / 5,199 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### \|^#### "` で節の位置を出し、`sed -n` で 80 行以内ずつ読め)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260921/brief-s1.md (親の段 1 brief と provisional 裁定 (P1)〜(P4)。新版が従うべき scope と不変条件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/docs/paper-story/README.md (**この wave で親が更新済み**、71,539 bytes。`git diff docs/paper-story/README.md` で差分 (版の履歴表 1 行、「最新 =」、訂正一覧の段落、stale 注記 5 件 → 0 件と移管先) を見よ。results 系列表は触っていない)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/docs/paper-story/results/2026-09-20-a1-balanced5-sized-attempt2-descriptive.md (A-1 attempt-0002 の単独稿、59,528 bytes。§0・§2.1・§2.3・§2.5・§2.7・§3 が新版の数値と限定の出所)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/t2792-a1-sized-attempt2/README.md (attempt-0002 の投入・時系列・受領証、28,104 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/t2304-pin-advance/README.md (ccbench pin 前進、19,674 bytes。§0〜§4・§7)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/t2807-b8-prerun/README.md (B-8 発効前試走、32,843 bytes。§1・§6・§7・§8)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/t2795-k2-pair-attempt/README.md (K2 pair 初投入の不成立、23,138 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/k2-loop-originals-lost-downstream/README.md (K2 原本消失の下流影響、32,888 bytes。§0・§2・§3・§4・§5)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/cleanup-backup-loss-record/README.md (F1034 の事故記録、8,254 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/t1871-nonenum-addendum/README.md ([T-1871] 追補 1、8,152 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/t2632-b4-evidence-provenance/README.md (B-4 の対応証拠 3 辺、46,656 bytes。§0〜§2・§7)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260921/output/insights/2026-09-20/fig13-b10-waiting-grid/README.md (fig13、18,308 bytes)

読んでよい (必要な節だけ) 資料: `output/insights/2026-09-20/t2153-witness-requested-us/README.md` (25,482 bytes)、`output/insights/2026-09-20/t2766-pairing-adopt/README.md` (28,171 bytes)、
`docs/paper-story/figures/README.md` (195,613 bytes — fig13 節は 1582 行〜末尾だけ)、前版 `docs/paper-story/2026-09-20b.md` (612,675 bytes / 4,578 行、差分照合用。全文 cat 禁止)、
公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/result.json` (`workloads[].statistics` だけ。`python3 -c` で key を取ってよい)。

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,852,661 bytes / 69,6xx 行、`docs/failures.md` は 2,808,144 bytes。**全文 `cat` してはならない。**
`grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。新版が引く D 番号のうち検算に要るのは D2184〜D2193 (69180 行〜末尾、`grep -n "^## D21[89][0-9]"`) —
とくに D2184 (pin 前進の射程限定)、D2186 (第 26 回 10 項。項 1・2・7 と索引外)、D2187 (K2 pair 不成立)、D2188 (pairing)、D2189 (witness)、D2190 (B-8 runner v5 と試走)、
D2193 (closure) — と、D2083 第 5 項 (`grep -n "^## D2083"`)、D2150 項 1、D2172 項 2・3・4、D2178、D2183。F1034 (`grep -n "^### F1034"`)。
worklog は `docs/worklog.md` (91,030 bytes、entry 1766〜1770 の本文は各見出しの直後 10〜40 行。`grep -n "^## 2026-09-2[01] (17"`) と archive
`docs/archive/worklog-phase3-0920-<n>.md` (entry 1747〜1765 は 1 entry 1 file (1759-1760 は 1 file)、本文は先頭 10〜60 行で残りは carry 行。`sed -n 1,60p`)。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が新版の本文を書いた。この wave は軽量版 (docs-only、実装面ゼロ) で、段 2 plan と段 3 敵対相談は省いた。
**お前は D2148 項 11 が定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」であり、
下の 2 レンズを 1 本で担う。**
親が実走した検査: `tools/check_docs.py` rc=0 (新版 + README 更新後)、本文が引く 8 桁 hash prefix 71 件を現物 (figures / results / 公開 leaf / policy の sha256、
一次資料本文の 64 hex、git object) と集合比較して全一致 (3 件は materials の現物 sha で個別確認: `c37fda1f` = round 3 の `layer3_report.json`、`f6dca3b9` = round 2 の同、
`41f52341` = `s3_mocc_template_proof.json`)、D 番号 246 種・T 番号 95 種・F 番号 22 種の見出し / 実在、repo 内 path 217 件の実在 (不在 6 件は `<env_tag>` 等の雛形と前版から
運んだ図の stem)、attempt-0002 の統計値 18 個 (result.json の mean / h / B / baseline_mean / sample_sd / planned_sigma × 3 workload、2 桁丸め) の逐語存在、公開 leaf 3 file の
sha256 (`b7e0518e…` / `98c35cca…` / `7ad34232…`) と fig13 の着地 bytes 3 値 (`018bd8e9…` / `8105d3dc…` / `e5ee8147…`) と fig8 / fig8b の provenance (`3ccdb0aa…` / `429b4028…`)
の現物再計算、基準 HEAD `285477c00` の gitlink `e9e477ca1b55348ab4530de0b1cf663ce4555290`・`pin.CURRENT_PIN = "e9e477c"`・`s8b_approved.CCBENCH_FULL_SHA`、pin の
`external/ccbench/cc/mocc/transaction.cc` に `izanagi_trace::` 呼出し 9 箇所 (emit_read / emit_write / key_to_hex / next_txid / stream) はあるが `emit_lock_violation` は
無く `patches/instr-mocc-lock-coverage.patch` 側にだけある (4 箇所) こと、`orchestrator/tests/test_between_run_floor.py` が新 pin で mocc の hook 証拠を True と pin して
いること、§7 の件数 (前半 100 / 後半 9 = 109、`- [ ]` 行 109)、README の stale 注記が 5 件 → 0 件。

新版の作り方: 前版 `2026-09-20b.md` を複製し、**最初に「前版」→「2026-09-20 版」(223 件)、「この版」→「前版」(253 件)、和文字直後の空白 (37 件) の機械置換を
当ててから**、冒頭・§0・§2 (g)・§10 を全面差替え、§7 の後半 13 項を前半へ移して後半 9 項を新設し、他節は箇所ごとに exact 1 回一致の置換で再導出した
(置換 script 9 本 + Edit 約 60 件)。**したがって本文中の「2026-09-20 版で X」「前版で X」は前版が「前版で X」「この版で X」と書いていた事実で、
「この版で X」は今回新しく書いた事実である。この 3 層がずれている箇所 (前版の出来事を「この版で」、この版の出来事を「前版で」、2026-09-20 版の出来事を
「前版で」) があれば must-fix。** 機械置換で構造語・工程語 (節見出し、「この節は前版から引き写していない」、「§10 の契約」、「前版の要求事項」等) が
誤変換された残りも探せ。

**親が段 1 で確定した型判定・書き方 (P2・P5・P6・P7) を攻撃せよ:** (P2) 親は「前版の執筆時点の誤りは 0 件」とした — README の stale 注記 5 件はいずれも
前版の起点 `fec4a8187` (2026-09-20 18:01 JST) より後の entry (1747 / 1751 / 1752 / 1754 / 1755) であり「当時は真」型、という判定。前版の見出し・括弧書きの
状態語 (例: §3 項目の見出し、§8 の【状態】、§4 の表) に、前版の執筆時点で既に偽だった文が残っていないか、一次資料 (D 本文・entry の日時) で検算せよ。
(P5) pin 前進の書き方 — 親は「pin に入ったのは mocc の read / write trace hook (D2083 第 5 項の『hook』)、X/P 計装 ([T-2294]、D1686) は patch のままで pin の source に
無く、素の pin の mocc は verifier で `indeterminate` のまま、D2083 第 5 項の between-run 再開の必要条件は mocc について満たされたが実測は未」と 2 つを分けて
書いた (第 1 幕の注記、§8 C-1)。一次資料 (D2083 項 5 の逐語、[T-2304] insight §3 の `test_between_run_floor` の反転、D2150 項 1 の射程、D2184) と食い違わないか。
(P6) B-8 — 「対象・定義・試走を認可し、試走が完走して発効束が揃った」までで「発効した」「取得した」とは書かない、仕分け (2) の限定明記は発効時 (D2186 項 1 (2))。
(P7) K2 — 「pair は投入されたが不成立」「候補 10 の再評価は昇格させない」「原本は消失したが値・判定・稿・図は不変で、変わるのは再検算できる強さ」、
再構成物を「原本」と呼ばない ([T-2815] §0・§2)。

**§10 の「段 6」小節 2 つは、お前のレビュー完了後に親が所見と裁定を書く。草稿の時点では「(…ここに記録する。草稿の時点では予定形…)」と書いてあり、
冒頭の「レビューを 1 本通す」「所見の裁定は §10 に置く」は予定形である。その完了形の先取りが無いことを確かめよ (完了形で書いてあれば must-fix)。**
README の版の履歴表の headline 末尾「前版の執筆時点の誤りは 0 件 (段 6 レビュー後に確定)」と訂正一覧の「(段 6 の敵対レビュー後に確定)」も同じ予定形である。

## レンズ A — 一次資料との照合、母集合、射程、件数

1. **数値・日付・判定を一次資料と照合せよ。** 少なくとも次を稿 / insight / D 本文 / archive entry で検算せよ:
   - A-1 attempt-0002 (entry 1755、稿): 時系列 (authorize-rerun 18:10:34 → submit 18:11:16 → job 13220 / 13221 / 13222 の終端 18:22:12 / 18:25:34 / 18:28:57 →
     complete 18:30:06 → materialize 18:30:21)、node (bnode035 / 039 / 040)、balanced の Pre-running 5 分 31 秒、bench-start barrier 18:18:44、bench 相の順序
     (balanced → read-heavy → write-heavy)、3 workload の mean / h / B / baseline 平均 / 標本 sd / 計画 sigma / 比 (1.207 / 0.872 / 1.081) / 分類 / breach、
     schedule receipt の一致 (root seed・group_bits・物理順)、driver 1 本 143 行追加・3 行削除、6 arm verifier 0 anomalies、稿の限定数 (L-A1S2-1〜13)、
     §2.7 の並記から書ける 3 命題 (a)(b)(c)、「A-1 の値」「再現」「安定」「3 本目」の禁止、認可 record は署名ではないこと、公開 leaf の sha256 3 値、
     `.complete.json` との一致、baseline no-backoff の cv (0.0323 / 0.0160 / 0.0089) と variant (0.0059 / 0.0062 / 0.0050)、write-heavy no-backoff の pair 0 =
     2,730,303、三軸語走査の事故 (F1013 再発) の記述。
   - pin 前進 (entry 1747、D2184、insight): 前提の人間 push 10:2x / fresh clone 13:17、間 4 commit の id、差分 141 行、commit `827682b60`、policy sha
     `949ddcc2…` → `db6bc9ea…`、変異 MUT-1 13 node / MUT-2 21 node、受入 pre-1 の赤 24 件の内訳 (11 / 2 / 11)、`LEGACY_REPORT_CCBENCH_PIN = "511c953"`、main 着地
     `6a3e15809` 19:03、F1033、据え置きの一覧、新事実 2 点、[T-2812]、clang 14 未確認、「mocc に hook 証拠が無い」前提の test 反転の記述。
   - 第 26 回 D2186: 10 項の要旨 (項 1 の (1)〜(7)、項 2 の (i)〜(iii)、項 3〜10)、提示時 main `482f19b88`、相談の反対 1 件と根拠訂正 5 点と索引漏れ 2 行の採用、
     「既裁定で索引不要」の不採用、「裁定は完了を意味しない」の文。新版 §0 の 3・§2 (e)・§8 B-8・§8 C-1 の記述が D 本文と一致するか。
   - B-8 試走 (entry 1766、D2190、insight §1・§6・§7): runner v5 の行数 2103 / sha256 `4ff6652a…`、selftest 166/166、job 6 本 (v3 / v4 / v5 各 2) 各 ≈ 36 秒、
     identity g_rl `b0f95b21…` / g_rt `a0219ce0…` の全桁、07-16 校正 `4608a96e…` は旧 pin `d706650c`、patch `31316713…`、事前登録 raw sha256 `6ccb18c7…` (51,974 bytes)、
     hard timeout 3 値 (3600 / 1800 / 3600)、解釈 (a)〜(f)、発効束の項目、1 行再提示の逐語、承認後の手順 4 段、不承認の選択肢 (b)(c)、親の誤り 3 点、限定 (発効して
     いない / 試走は identity と build だけ / 経路の未実走 / node ごとの別 build)。
   - K2 pair (entry 1754、D2187): job `13339.nqsv` / bnode032 / 74 秒 / submit-tree `6a3e15809` / `p3_s4_loop.PIN` 511c9538 / campaign `b24749ae` / median 811,956 / CV 0.98% /
     abort 9.16%、ClaimError の経路 (`_authorize_measurement` → `acquire_claim` の `O_EXCL`)、D464 / D553、修復方向と却下候補 5 つ、F1019 再発、B-5 (β) の同制約、
     「pair 試行における既知候補 10 の追加評価」、3 巡の値との差 (815,983 → 811,956)。
   - 原本消失 (F1034、entry 1759 / 1764、[T-2815] §0・§2・§3・§4): 19:25 JST、script の恒真ゲート (`-C` の順、`2>/dev/null || :`)、失った集合 (round 3 全部 /
     round 2 AO + lock / roundtrip 全部)、残存 (round 2 写し bytes 一致、`fc7acaca…`、round 3 loop_state `917ba3d3…` と AO `804c62c7…` / `66d3e737…` の再構成、WAL 内容同一
     canonical ref 5/5、digest 無し、roundtrip は sha256 まで)、pair 原本 5 file の複製 21:24 JST、4 巡目の設計 (射影)、択 A / B / C、B-6 (a)(b)(c)(d)・B-9 (c)・fig12 の
     対応表の限定文、材料レポートの sha (`f6dca3b9…` / `c37fda1f…`) と fresh rebuild 再実行不能の記述。
   - [T-1871] 追補 1 (entry 1752): sha256 `e544de19…` の凍結成果物 5 本 (s1 2 + s8b 3)、別 file 名、先例 (b10 erratum、D1789)、採らなかった 2 案、相談 real 5 / refuted 3、
     発効するのは語義改訂だけ。
   - B-4 3 辺 ([T-2632]、entry 1753): 3 campaign id、whiteboard 4 行 ↔ WAL 3 variant、辺 B の定義不在、辺 C の bootstrap 未定義、D2100 呼び手の lock v2 欠陥、
     裁定パッケージ 4 項と推奨 (α)、must-fix 3 件、観測後に消えた campaign dir。
   - fig13 (entry 1763、figures README): 着地 bytes 3 値、稿 sha `8dc6d695…`、権威 bytes 2 値 (`a4390603…` / `e237d17d…`)、境界を跨ぐ 4 cell の名指し、negative 点推定
     write-heavy μ 5 (−0.97%)、レビュー B の must-fix (FIGURE_CONVENTIONS §6)、refuted A-2、変異 19/19、判定 D1678 不変。
   - witness (D2189、entry 1758): 枝選択 21 → 22、対応集合 22 → 23、(4,4)/(0,4) green、`BACK_OFF=0` (3,3)/(0,3) red、変異 8/8 KILLED + 等価 1、静的反例の形。
   - pairing (D2188、entry 1756): 対差 145.8 / 86.3 / 57.3 秒、対率中央値 19.6%、閾値 10%、property 4 種、opt-out なし、junit +13 MB。
   - closure (D2193、entry 1770): 63 → 85、22 本、未収載 78 / 88、exact-63 の歴史収載。
   - 論文草稿 4 本 (entry 1749 / 1750 / 1757 / 1762): path、attempt-0002 / B-8 試走を反映していないという §5 の注記 (entry 順で検算)。
2. **母集合と射程。** 新版が「完走」「前進」「認可」「試走」「不成立」「消失」「着地」と書く箇所で、母集合が広すぎないか (例: attempt-0002 の完走を A-1 の値・
   再現と読ませていないか、pin 前進を certified 系列・探索解禁・証明面と読ませていないか、B-8 の試走を発効・取得と読ませていないか、pair の不成立を launcher の
   欠陥・防壁の誤りと読ませていないか、原本消失を主張の変更と読ませていないか、fig13 を B-10 の閉鎖と読ませていないか)。
3. **件数・量化。** 「すべて」「だけ」「N 件」「N 稿」「N 点」を原データから数え直せ。特に §0 の「13 点」「5 種類」「1 件だけ」、§2 (d) の「6 例」、§2 (e) の
   「8 つ」と第 26 回の要約、§2 (g) の「14 点」、§5 の「20 稿 (09-20 ×8)」、§7 の「100 + 9 = 109」、§9 の「3 つの種別」、冒頭の「24 エントリ」「D2184〜D2193」
   「5 件」「訂正 0 件」、「観測 4 件」「図 1 本」「単独稿 1 本」「草稿 4 本」。
4. **path と参照。** 本文が引く一次資料の path・D 番号・T 番号・F 番号・entry 番号が実在し、内容が本文の記述と合うか。行番号参照が無いことも確かめよ。
5. **凍結物の不変。** `git status --short` / `git diff --stat` で、変更が `docs/paper-story/2026-09-21.md` (新規、untracked) と `docs/paper-story/README.md` (4 節) だけで
   あること、前版・`results/`・`figures/`・`claim-evidence/`・`docs/paper-story-backoff/`・`docs/phase3.md` に差分が無いことを確かめよ。

## レンズ B — 主張の強さ、分類の一貫性、二重計上、前版との差分、先取り

6. **禁止句。** 「A-1 の値がある」「再現した」「安定した」「3 本目を投入できる」「B-10 を閉じた」「再現されたので飽和しない」「mocc は第 2 成功例」「床値が発効した
   ので oracle が走れる」「official 床値が科学的に有効」「人間が批准した holdout」「B-7 を (無限定に) 満たした」「B-8 を取得した」「発効した (B-8)」「全走 anomaly ゼロ」
   「信頼度 1−εⁿ」「pin 前進で certified 系列が開いた」「探索が解禁された」「mocc に証明面が入った」「旧系列を新 main から再開できる」「K2 で改善した」「対照が取れた」
   「pair が成立した」「4 巡目が走った」「B-5 の試走が走った」「原本を復元した」「WAL の bytes を再構成できる」に相当する表現 (短縮形・言い換えを含む) が本文の
   どこにも無いこと。B-10 の言い方が事前登録 §4.5 の固定表現に限られていること。「pin は前進した」と書く箇所に限定 (R/W hook のみ、X/P は patch、固定 checkout)
   が添えてあること。
7. **版名の 3 層の付け替え。** 上記「新版の作り方」のとおり。特に §5 の注記 (「2026-09-17 版の注記 / 2026-09-19 版の注記 / 2026-09-20 版の注記 / 前版の注記 /
   この版の注記」)、§7 の「〜版の更新 / 前版の更新 / この版の更新」「前版時点の事実 / この版時点の事実」、§8 の【状態】、§9 の「前版の 3 つ / 2026-09-20 版の 3 つ /
   この版の 3 つ」、§2 (e) の運用素材 4 群、§4 の「前版で図が 5 本増えた / この版で図が 1 本増えた」。
8. **分類の一貫性と二重計上。** §9 の 7 種の表で、同じ観測が 2 種に置かれていないか。この版で加わった attempt-0002 が第 4 種 (descriptive) と第 5 種 (6 arm の
   correctness) に正しく分かれ、K2 pair 試行の候補 10 が第 4 種 (throughput) と第 5 種 (correctness) に分かれ、pin 前進・B-8 試走・pair 不成立・原本消失・fig13 等が
   第 6 種であること。§0・§2・§6・§8 と食い違わないか。
9. **§6 と §8 の状態語。** 「言えること / 言えないこと」と A / B / C 群の【状態】が、§0 の 13 点および一次資料と食い違わないか。
   特に A-1・A-4・B-1・B-4・B-5・B-6・B-8・B-9・B-10・C-1 の状態語。「完走」と「充足」の区別、「前進」と「解禁」の区別、「試走」と「発効」の区別、
   「投入」と「成立」の区別が §0・§2・§6・§7・§8・§9 で一貫しているか。
10. **README の stale 注記 5 件との照合。** README の差分 (前の版の stale 注記 5 項目の逐語は `git diff docs/paper-story/README.md` の削除側) と、新版本文の
    取り込み先 (README の新しい移管先一覧) を表にせよ。取り込み漏れ・要約での意味の変化があれば must-fix。README の版の履歴表の新しい行の headline が本文と
    食い違わないか。
11. **先取り・scope。** 稼働中で未着地の wave の内容を書いていないか (着地済み正典は local main `285477c00`、entry 1770 まで)。新しい主張を足していないか。
    裁定を先取りしていないか (例: B-8 の発効・本走の結果、K2 の修復と 4 巡目の入力元の択、B-4 の carrier の択、A-1 の 3 本目、[T-2810] の解、W-4、B-5 試走の
    結果、fig9b、第 27 回 /rulings)。
12. **前版から消えた項目。** 前版 §5・§6・§7・§8 にあって新版に無い記述があれば列挙し、落としてよいか個別に判定せよ (§7 は 109 項で「落とした項目は無い」と
    書いてある)。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。規律 7。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。B-7 の充足は 4 語の限定付きでだけ書く。B-8 は取得と書かない。3 走行と A-1 の 2 attempt と B-7 fixed5 を
  pool しない (D1993 項 6)。2 attempt から何も計算しない。2 cohort を合成しない (D2157)。
- 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」「床値が発効したので oracle が走れる」とは書かない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。隣接 docs (results 稿・claim-evidence 稿・figures/) の訂正・図の再生成・
  新しい主張の追加も scope 外。英語稿・2 本目論文の版は作らない。

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当節 (§番号と小見出し)、一次資料の path または
D 番号、対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け**
(書けない所見は nit)。

## stale 注記 5 件の取り込み先

表 (README の項目 → 新版の節)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

新版をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
