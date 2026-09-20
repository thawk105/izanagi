単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/docs/paper-story/2026-09-20b.md (**レビュー対象の新版**、601,987 bytes / 4,508 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### \|^#### "` で節の位置を出し、`sed -n` で 80 行以内ずつ読め)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920b/brief-s1.md (親の段 1 brief と provisional 裁定 (P1)〜(P3)。新版が従うべき scope と不変条件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/t2724-ax-delegated/README.md (凍結 v2 g1 の承認 A / active pointer X を AI が作った wave、25,217 bytes。§5 が launch validation の不整合 2 件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/t2724-b10-pin-update/README.md (chain / X2 / G の main 着地、27,639 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md (B-7 の限定付き充足の入口転記、11,825 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md (A-1 rear gate の認可 record、21,239 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/t2795-pair-launcher/README.md (K2 同 job stock 対照の pair launcher、28,737 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/b8-longrun-verify-prereg/README.md (B-8 事前登録 v1、11,367 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/verifier-capacity/README.md (verifier 容量、18,525 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/t2791-mocc-upstream-report/README.md (mocc 上流報告案、9,591 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/output/insights/2026-09-20/t2793-fig8b-cohort2/README.md (fig8b、21,235 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/docs/paper-story/README.md (**この段では未更新**、67,476 bytes。「最新スナップショット以後に確定したこと」の stale 注記 3 件 (fig10・B-7 限定付き充足・fig12) と results 系列表が新版の必須反映集合。README の更新は親が段 7 で行う)

読んでよい (必要な節だけ) 資料: 新版の単独稿 6 本 `docs/paper-story/results/2026-09-20-{mocc-g2-observation-conditions,mocc-witlight-four-arm,k2-manual-loop-three-rounds,s1a-nine-pair-direct-comparison,b10-waiting-grid-formal,p24-static-backoff-sweep-linux-baremetal}.md` (35〜78 KB、冒頭の「判定しないこと / 限定」と §2 の表だけでよい)、`docs/paper-story/figures/README.md` (173,453 bytes — fig8b 節 828〜943 行、fig3b 節 1061〜1185 行、fig10 節 1186〜1327 行、fig11 節 1328〜1457 行、fig12 節 1458〜1580 行だけ)、前版 `docs/paper-story/2026-09-20.md` (488,927 bytes / 3,866 行、差分照合用。全文 cat 禁止)。

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,788,239 bytes / 69,178 行、`docs/failures.md` は 2,786,002 bytes。**全文 `cat` してはならない。**
`grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。新版が引く D 番号のうち検算に要るのは D2165〜D2183 (末尾 960 行、`grep -n "^## D21[678][0-9]"`)、
とくに D2166 (B-10 pin)、D2167 (chain + G の順序)、D2172 (第 24 回 13 項。項 1〜8 と索引外)、D2174 (第 25 回 7 項。項 1〜5)、D2175 (B-8 v1)、D2178 (A-1 rear gate)、
D2180 (A / X の AI 委任)、D2181 (verifier)、D2183 (K2 pair launcher) と、D1441 (2026-09-02、`grep -n "^## D1441"`)、D2044 項 3、D2120 項 2、D2148 項 13、D2156〜D2162。
worklog は `docs/worklog.md` (93,728 bytes、entry 1742〜1746 の本文は各見出しの直後 10〜40 行。`grep -n "^## 2026-09-20 (17"`) と archive
`docs/archive/worklog-phase3-0920-<n>.md` (entry 1713〜1741 は 1 entry 1 file、本文は先頭 10〜40 行で残りは carry 行。`sed -n 1,40p`)。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が新版の本文を書いた。この wave は軽量版 (docs-only、実装面ゼロ) で、段 2 plan と段 3 敵対相談は省いた。
**お前は D2148 項 11 が定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」であり、
下の 2 レンズを 1 本で担う。**
親が実走した検査: `tools/check_docs.py` rc=0、三軸語走査 (`s8b_holdout_freeze search`) は両 holdout とも hit 4 (official 床値 run dir 3 file + 候補 = chain 着地後の
設計どおりで、新版 file は hit に含まれない)、本文が引く repo 内 path 222 件の実在確認 (不在は相対断片と、attempt-0002 の期待公開先 1 件 = 未作成と本文が明記)、
D 番号 231 件・F 番号 17 件の見出し実在、`git diff --check` 0、NFC、§7 の件数 (前半 87 / 後半 13 = 100、`- [ ]` 行 100)、
`cc82edc8c` (X1')・`4d8fb93b7` (X2)・`229982652` (G)・`629690fdd` (merge)・`0e647f84c`・`4114cf51b`・`a3bf67a8c` (A、14:24:52)・`70e87c9c9` (X、14:25:30)・
`ca3907e57`・`864d7135e` (fig8b、08:05:55) が HEAD の祖先であること (rc=0)、`864d7135e` が前版起点 `b7f970dfa` と前版 fold `24bc8441b` (09:11:51) の祖先でないこと (rc=1)、
現行 gitlink `511c9538e4e8efa54b45cda62e72389ed3b706ec`、`tools/pegasus/b10_backoff_grid.sh` の `EXPECTED_FREEZE_TREES_SHA256` = `92099c87e935…`、
`output/s8b-freeze/approvals/7e1114…json` と `output/s8b-freeze/active/577537e2…json` の実在、D1441 の fold commit `89a551d0e` (2026-09-02 07:43) と
2026-09-02 版の着地 `b664df20c` (同 07:14)、results 系列 19 稿、`docs/paper-story/2026-0{9-05,9-14,9-17,9-19,9-20}.md` の 5 版に「定義の置き直しは未裁定」が各 2 箇所。

新版の作り方: 前版 `2026-09-20.md` を複製し、**最初に「前版」→「2026-09-19 版」(191 件)、「この版」→「前版」(178 件)、「本版」→「前版」(3 件) の機械置換を
当ててから**、冒頭・§0・§2 (g)・§10 を全面差替え、他節は箇所ごとに exact 1 回一致の置換で再導出した (置換 script 21 本 / 約 150 件)。
**したがって本文中の「2026-09-19 版で X」「前版で X」は前版が「前版で X」「この版で X」と書いていた事実で、「この版で X」は今回新しく書いた事実である。
この 3 層がずれている箇所 (前版の出来事を「この版で」、この版の出来事を「前版で」、2026-09-19 版の出来事を「前版で」) があれば must-fix。**
機械置換で構造語・工程語 (節見出し、「この節は前版から引き写していない」、「§10 の契約」等) が誤変換された残りも探せ。

**親が段 1 で確定した 2 つの型判定を攻撃せよ:** (a) 依頼が「事実誤認」と呼んだ前版 §4 の「第 2 cohort は fig8 に描かれていない」を、親は
「執筆時点では真で後続 (fig8b、10:36 以後に main 着地) が古くした」型として冒頭の訂正一覧に載せず本文更新にした。(b) 「『非列挙』の定義の
置き直しは未裁定」は D1441 (2026-09-02) で裁定済みなので前版の執筆時点の誤り (訂正 1) とし、「その定義の下で段階 B を再走した wave は無く軸は休眠」と
書いた。どちらも一次資料 (commit 日時、D1441 本文、D2158、次の一手) で検算し、誤っていれば must-fix。

**§10 の「段 6」小節 2 つは、お前のレビュー完了後に親が所見と裁定を書く。草稿の時点では「(草稿では予定形。)」と書いてあり、冒頭の
「レビューを 1 本通す」「所見と裁定は §10 に置く」は予定形である。その完了形の先取りが無いことを確かめよ (完了形で書いてあれば must-fix)。**

## レンズ A — 一次資料との照合、母集合、射程、件数

1. **数値・日付・判定を一次資料と照合せよ。** 少なくとも次を稿 / insight / D 本文 / archive entry で検算せよ:
   - g1 の発効 (D2166 / D2167 / D2180、entry 1716 / 1742): pin の旧値 `c405c742…` → G 込み `6a4ee1ef…` (20 file) → A / X 込み `92099c87…` (22 file)、merge `629690fdd`
     と main `0e647f84c` と `2361220d4`、初回列の拒否 (`landed-fold-owned-path` rc=26)、変異 3/3・負例 3 件、A / X の SHA と時刻と record の path、`_assert_user_commit` の
     新しい条件 (ちょうど 1 行、逐語 none または規約適合の構造化 trailer)、批准 loader の結果 (generation 1、sha `7e1114…`)、P3 gate-check の 2 件の不整合の名前
     (`journal-state-invalid` / `_JOURNAL_KEYS` の `reservation-preflight`、段階 6 lineage = result 導入集合 == {G} だが実導入は X1')、v1 path 不変 (既知 4 拒否)、
     held 6 node の期待値の書き換え、hook 不変、[T-2810]、「AI が自己承認した世代」の記録 (10:2x の控え) と論文での呼称が D2180 の対象外であること、
     D2120 項 2 (b) と D2174 項 4 を supersede したこと。
   - B-7 の限定付き充足 (D2174 項 3、entry 1731): 4 語の限定の逐語、D2044 項 3 の supersede、択 (b) 不採用、入口 3 か所、稿と fig10 の bytes 不変、
     caption の固定文の逐語、fig10 の着地 bytes 3 値と稿の SHA-256 `6585d446…`。
   - A-1 rear gate (D2178、entry 1736): 定数 `V3_SIZED_RERUN_AUTHORIZATIONS` の 6 要素、record の path と schema と key 集合、`authorize-rerun`、解除条件
     (一致 record かつ 候補 == base/attempt-0001)、不一致 9 種の拒否、公開先の兄弟 dir、追補の path、焦点走 1697 passed、投入の順序 4 段、author が pytest を
     実走できなかったこと、段 6 の must-fix が同一 (行番号 pin)。
   - K2 pair launcher (D2183、entry 1746): `--stock-control` の定義 (silo、BACK_OFF=1、BACKOFF_FIXED=-1、同 campaign、`--isolate-worktree` 必須)、成功条件
     (`certified-stock`、STOCK 性)、`non-stock-source`、job body env `IZANAGI_S4_STOCK_CONTROL`、候補の後に 1 回、`capability_resolver`、較正動作点 CLI と
     `--verify-performance`、変異 17/17 KILLED、焦点走 1746 passed / 1 skipped、orphan hold rc=16 の事故、「pair 成立は主張しない」「実 compiler での STOCK 成立は未測定」。
   - D2172 の 13 項 (項 1〜13 の決定の要旨) と D2174 の 7 項、両決定の「裁定は完了を意味しない」の文、D2172 の索引漏れ 3 行・誤引用の訂正 2 件・不採用 6 件、
     D2174 の validator 不受理 (F43 型)。新版 §0 の 3 と §2 (e) と §5 の記述が D 本文と一致するか。
   - B-8 v1 (D2175、entry 1733): 案 A / 案 B と verify 数 (24 / 48)、種の定義 (自己シード、CLI flag なし)、長時間 (≥ 6 s、校正 {6, 10}、3 s へ丸めない)、
     予算 ≤ 4 h / 対象、統計文 4 種、「取得と書ける条件」、runner 改版が要ること。
   - verifier 容量 (D2181、entry 1744): 原因 (edge worker の CoW、node 113〜119 GiB、SIGTERM 無視の pool 停滞 = F1032)、compare の数値 (bal10 478 s / 32.4 GiB、
     wh10 297 s / 15.2 GiB、bal6 275 s、rh6 896 s)、判定同一、fixture 22 件、焦点走 302 passed、read-heavy 10 s 未保全、裁定パッケージ 3 件。
   - 単独稿 6 本の題名・限定数・判定不変: p24 稿の未丸め 3 値と 3 campaign id と「区間推定も有意差判定も持たない」、S-1a 稿の「判定しないこと」6 点と
     マージン最大 −55.1%、K2 稿の「実施 3 回・実測還流 2 回・診断還流 1 回」、B-10 待ち方 grid 稿の「内側 32・境界上 4・外側 0」「host 未記録」「file 日付は起草日」、
     mocc 2 稿の限定 (0 件は不在証明でない、Fisher 0.500、検出力 0.105、TRACE=1 観測専用、pin 前進なし)。
   - 図 5 本: fig8b の cohort id 2 つ・block の役割と順序・着地 bytes (PNG `ddab2873…` / PDF `c5454544…` / provenance `429b4028…`)、fig10 / fig11 / fig12 / fig3b の
     着地 bytes 3 値ずつ、fig11 の abort 率 0.1547 / 0.145、fig12 に出る数 (20 / 25 / 20 / 10、job id)、fig3b が「2026-09-19 版の状態」であることと着地 test が無いこと。
   - mocc 追加実験の見送り (D2172 項 7) の択 (a)(b)(c) と再訪条件、上流報告案 ([T-2791]、entry 1739) の文数 `[S-01]`〜`[S-63]`、依頼文の事実誤り (`BACK_OFF=0` かつ
     witness off) の訂正、送信は人間。
   - 前版が「裁定待ち」と書いた 4 件の現在地: T-2792 (D2172 項 2 → D2178 実装、投入は未)、T-2795 (項 3 → D2183、投入は未)、T-2797 (項 4 段階裁定、試走認可・本走未)、
     T-2766 (項 1 採用裁定、採用 wave 未着地)。「裁定済み」と「実装・測定済み」を混同していないか。
2. **母集合と射程。** 新版が「発効」「充足」「着地」「認可」「解除」「実装」「完走」と書く箇所で、母集合が広すぎないか (例: g1 の発効を oracle 実走可能・床の科学的
   十分性・8b の前提充足と読ませていないか、B-7 の限定付き充足を採用・certified 昇格・性能主張と読ませていないか、rear gate の着地を投入済み・認可消費と読ませて
   いないか、launcher の着地を対照取得と読ませていないか、B-5 試走の認可を本走認可と読ませていないか、B-8 事前登録を取得と読ませていないか、fig8b を
   「再現された結果の図」と読ませていないか、verifier 容量改善を判定変更と読ませていないか)。
3. **件数・量化。** 「すべて」「だけ」「N 件」「N 稿」「N 点」を原データから数え直せ。特に §0 の「13 点」「4 種類」、§2 (e) の「6 つ + 7 つ + 7 つ」、
   §2 (g) の「14 点」、§5 の「19 稿」、§7 の「87 + 13 = 100」、§9 の「7 種」「この版は第 6 種だけ」、冒頭の「35 エントリ」「D2165〜D2183」「5 版」「4 か所」、
   「観測 4 件」「図 5 本」「単独稿 6 本」「裁定待ち 4 件」。
4. **path と参照。** 本文が引く一次資料の path・D 番号・T 番号・F 番号・entry 番号が実在し、内容が本文の記述と合うか。行番号参照が無いことも確かめよ。
5. **凍結物の不変。** `git status --short` / `git diff --stat` で、変更が `docs/paper-story/2026-09-20b.md` (新規、untracked) だけであること、前版・`results/`・
   `figures/`・`claim-evidence/`・`docs/paper-story-backoff/`・README に差分が無いことを確かめよ。

## レンズ B — 主張の強さ、分類の一貫性、二重計上、前版との差分、先取り

6. **禁止句。** 「A-1 の値がある」「A-1 の 2 本目が投入された」「B-10 を閉じた」「再現されたので飽和しない」「mocc は第 2 成功例」「床値が発効したので oracle が走れる」
   「official 床値が科学的に有効」「人間が批准した holdout」「B-7 を (無限定に) 満たした」「B-8 を取得した」「全走 anomaly ゼロ」「信頼度 1−εⁿ」「pin を前進させた」
   「K2 で改善した」「対照が取れた」「試走が走った」に相当する表現 (短縮形・言い換えを含む) が本文のどこにも無いこと。B-10 の言い方が事前登録 §4.5 の
   固定表現に限られていること。「凍結 v2 g1 が発効した」と書く箇所に限定 (配線下限の床、launch validation 未達、AI 自己承認の世代) が添えてあること。
7. **版名の 3 層の付け替え。** 上記「新版の作り方」のとおり。特に §5 の注記 (「2026-09-17 版の注記 / 2026-09-19 版の注記 / 前版の注記 / この版の注記」)、
   §7 の「〜版の更新 / 前版の更新 / この版の更新」「前版時点の事実 / この版時点の事実」、§8 の【状態】、§9 の「前版の 3 つ / この版の 3 つ」、§2 (e) の
   運用素材 3 群。
8. **分類の一貫性と二重計上。** §9 の 7 種の表で、同じ観測が 2 種に置かれていないか。この版で加わったもの (g1 発効・B-7 充足・rear gate・launcher・B-5 部品・
   B-8 v1・verifier・図・稿) がすべて第 6 種で、第 4 / 5 種に新しい観測を足していないこと。§0・§2・§6・§8 と食い違わないか。
9. **§6 と §8 の状態語。** 「言えること / 言えないこと」と A / B / C 群の【状態】が、§0 の 13 点および一次資料と食い違わないか。
   特に A-1・A-4・B-1・B-2・B-5・B-6・B-7・B-8・B-10・C-1 の状態語。「発効」と「走れる」の区別、「限定付き充足」と「採用」の区別、「着地」と「投入」の区別が
   §0・§2・§6・§7・§8・§9 で一貫しているか。
10. **README の stale 注記 3 件との照合。** README (未更新) の「最新スナップショット以後に確定したこと」3 項目 (fig10・B-7 限定付き充足・fig12) と、README の
    results 系列表にある 2026-09-20 の稿 6 本の行が、それぞれ新版本文のどの節に取り込まれているかを表にせよ。取り込み漏れ・要約での意味の変化があれば must-fix。
11. **先取り・scope。** 稼働中で未着地の wave の内容を書いていないか (着地済み正典は local main `fec4a8187`、entry 1746 まで。**注意: この worktree の
    親 repo の main は着手後に `482f19b88` へ進み gitlink が前進しているが、新版は起点 `fec4a8187` の状態を書く。「基準 HEAD の pin は `511c9538`」が
    正しい**)。新しい主張を足していないか。裁定を先取りしていないか (例: T-2810 の解、W-4 の承認、B-5 本走、attempt-0002 の投入結果、K2 pair の結果、
    採用 wave の結果、pin 前進の実施、論文での g1 批准の呼称)。
12. **前版から消えた項目。** 前版 §5・§6・§7・§8 にあって新版に無い記述があれば列挙し、落としてよいか個別に判定せよ (§7 は 100 項で「落とした項目は無い」と
    書いてある)。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。規律 7。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。B-7 の充足は 4 語の限定付きでだけ書く。B-8 は取得と書かない。3 走行と A-1 attempt-0001 と B-7 fixed5 を
  pool しない (D1993 項 6)。2 cohort を合成しない (D2157)。
- 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」「床値が発効したので oracle が走れる」とは書かない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。隣接 docs (results 稿・claim-evidence 稿・figures/) の訂正・図の再生成・
  新しい主張の追加も scope 外。README の更新は親が段 7 で行う (この段の scope 外)。英語稿・2 本目論文の版は作らない。

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当節 (§番号と小見出し)、一次資料の path または
D 番号、対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け**
(書けない所見は nit)。

## stale 注記 3 件と 2026-09-20 稿 6 本の取り込み先

表 (README の項目 → 新版の節)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

新版をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
