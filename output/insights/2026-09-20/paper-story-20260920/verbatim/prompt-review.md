単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/docs/paper-story/2026-09-20.md (**レビュー対象の新版**、476,676 bytes / 3,796 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### \|^#### "` で節の位置を出し、`sed -n` で 80 行以内ずつ読め)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920/brief-s1.md (親の段 1 brief と provisional 裁定 (P1)〜(P4)。新版が従うべき scope と不変条件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md (検証相の単独稿、17,652 bytes。新版の検証相の数値の出所)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md (同一候補 fixed 5 µs の 3 workload 測定の単独稿、29,297 bytes)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md (B-10 第 2 cohort の単独稿、45,072 bytes。§2.1・§2.3・§2.6 と §3 の限定 16 件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/output/insights/2026-09-19/a1-sized-attempt2/README.md (A-1 attempt-0002 の gate 拒否と裁定パッケージ §7)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/output/insights/2026-09-19/t2288-floor-pair-w1/README.md (B-4 床値 w1 の実投入と完走)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/output/insights/2026-09-19/k2-loop-round3/README.md (K2 3 巡目)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/output/insights/2026-09-19/mocc-witlight-arm-run/README.md (mocc 軽量 witness 4 arm)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/output/insights/2026-09-19/t2773-mocc-template-wave2/README.md (mocc 機械実証 wave 2)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/output/insights/2026-09-19/t2724-chain-land-2/README.md (chain land 2 度目の不成立)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-20/docs/paper-story/README.md (**この段では未更新**。stale 注記 11 件が新版の必須反映集合。README の更新は親が段 7 で行う。新版本文が README の stale 注記 11 件を本文へ取り込めているかを照合せよ)

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,675,671 bytes / 68,222 行、`docs/failures.md` は 2,768,454 bytes、
前版 `docs/paper-story/2026-09-19.md` は 394,236 bytes / 3,325 行、worklog の archive は `docs/archive/worklog-phase3-09*.md` に
1 エントリ 1 file (各 600〜700 行、本文は先頭 10〜40 行で残りは carry 行。entry 1686〜1691 は `worklog-phase3-0919-<n>.md`、
1692〜1705 は `worklog-phase3-0920-<n>.md`、1706〜1711 は `docs/worklog.md` の本文)。**全文 `cat` してはならない。**
`grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。`wc -c` / `wc -l` は許す。
新版が引く D 番号のうち検算に要るのは D2156、D2157、D2158、D2159、D2160、D2161、D2162、D2163、D2164 (いずれも
`grep -n "^## D21[56][0-9]"` で位置が出る。decisions.md の末尾 400 行に全部ある) と、D2044 項 3、D2050、D2120 項 16、D2134 項 8〜9、
D2148 項 3・5・11、D2155 である。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が新版の本文を書いた。この wave は軽量版 (docs-only、実装面ゼロ) で、段 2 plan と段 3 敵対相談は省いた。
**お前は D2148 項 11 が定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」であり、
下の 2 レンズを 1 本で担う。**
親が実走した検査: `tools/check_docs.py` rc=0、三軸語走査 (`s8b_holdout_freeze search`) rc=0 (両 holdout の conjunction hit 0)、
本文が引く repo 内 path 161 件の実在確認 (不在 3 = g1 候補 2 file は保存 branch 上で main に無いと本文が明記、図 stem 1)、
D 番号 211 件・F 番号 15 件の見出し実在、`git diff --check` 0、NFC、§7 の件数 (前半 76 / 後半 11 = 87、`- [ ]` 行 87)、
`cc82edc8c` (chain X1') と `4d8fb93b7` (X2) と `0eabe67ba` (T-2766 impl) と `229982652` (G) が HEAD の祖先でないこと (rc=1)、
`0b4fbd7a6` (B-4 spec 凍結)・`8737cacb4` (B-10 事前登録追記)・`c18a80967` (B-7 fixed5 実装)・`abff80d1b` (A-1 gate) が HEAD の
祖先であること (rc=0)、現行 ccbench pin `511c9538`、A-2 / A-6 / B-7 の 3 policy の `scheduler.nodes` が 5、
`SATISFIABLE_CONDITION_IDS == {"C10"}`、前版起点 `a99425b66` での A-2 policy の nodes が 1 (前版の記述が当時真)。

新版の作り方: 前版 `2026-09-19.md` を複製し、**最初に「前版」→「2026-09-17 版」、「この版」→「前版」の機械置換 (160 + 155 件) を
当ててから**、冒頭・§0・§2 (g)・§9 冒頭・§10 を全面差替え、他節は箇所ごとに exact 1 回一致の置換で再導出した (置換 20 script /
約 150 件)。**したがって本文中の「2026-09-17 版で X」「前版で X」は前版が「前版で X」「この版で X」と書いていた事実で、
「この版で X」は 2026-09-20 に新しく書いた事実である。この 3 層がずれている箇所 (前版の出来事を「この版で」、この版の出来事を
「前版で」、2026-09-17 版の出来事を「前版で」) があれば must-fix。** 機械置換で構造語・工程語 (節見出し、「この節は前版から
引き写していない」等) が誤変換された残りも探せ。

**§10 の「段 6」小節 2 つは、お前のレビュー完了後に親が所見と裁定を書く。草稿の時点では「(凍結版で記録する。草稿の時点では
未実施。)」と書いてあり、冒頭の「レビューを 1 本通す」「所見の裁定は §10 に置く」は予定形である。その完了形の先取りが無いことを
確かめよ (完了形で書いてあれば must-fix)。**

## レンズ A — 一次資料との照合、母集合、射程、件数

1. **数値・日付・判定を一次資料と照合せよ。** 少なくとも次を稿 / insight / D 本文 / archive entry で検算せよ:
   - 検証相 (D2160、entry 1702、稿 2026-09-20): 候補 2 genome の定義と identity sha (fixed-5 `678b7203…` = T-1998 v1 一致、fixed-10
     `16c29935…`)、校正 6 job (request 10868〜10873) の投入・終了時刻、適格集合 {3,6}/{3,6}/{3} と extime 3 s、本走 12 job (11268〜11279)
     の時刻、判定集合 30 = 24 + 6、anomaly 0、pass ×2、未完走 2 件 / 候補の種類 (balanced SIGKILL `killed_unknown`、write-heavy hard
     timeout 3600 s)、本走実消費 6316 / 6134 S、校正実消費 6462 / 6339 S、限定 9 件、A-2 の src_token との不一致理由 (`91a5bfca3`)、
     S-1 追記の繰延べの理由 (`known_axes_freeze.json` の source sha256)、trace 3,072 file 213.3 GB → 48.9 GB、18 job の binary が別 build。
   - B-7 fixed5 (D2162、entry 1705、稿 2026-09-19): study 名、attempt id、request 3 件、source `c18a80967`、6 cell の median と 5 標本、
     effects 3 値 (全桁)、床値 3 値、判定 (rr95 だけ退行)、outer `reject`、`a4_noise_floor_status`、abort 率 6 値、6 cell certified、
     adopted の `source_bytes_sha256` = T-1998 target、限定 14 件、図なし、判定規則 (§1.4) が結果前固定であること。
   - B-10 cohort 2 (D2157、entry 1690、稿 2026-09-19): commit `8737cacb4` の時刻、attempt 1 の失敗 (job 10743〜10745、rc=2 の理由)、
     attempt 2 の group id と job 10752〜10754、verdict、18 区間、`failures`、120 記録、CV < 0.6%、throughput の 1000 → 9999 の 6 値
     (5 反復平均)、限定 16 件、§2.6 の表、「再現されたので飽和しない」を禁じる追記の項番。
   - A-1 attempt-0002 (D2156、entry 1687): 投入前照合 21 項目、submit の時刻 22:05:30 → 22:05:36 JST、rc 2、stderr の逐語、gate 名と
     commit `abff80d1b`、副作用なし、択 1〜3 と推奨、相談 C の訂正 4 点、[T-2792]。
   - B-4 w1 (entry 1693): H `2ba400087`、job 10711〜10713 と node、8 秒、124 / 124・248 / 248・62 / 62・drop 0、所要 4178 / 4141 / 4602、
     8 変数の 6 / 1 / 1 の区分、signal の言い方、窓 JSONL untracked、w2 の窓。
   - K2 3 巡目 (entry 1691): critic-2 の sha `d2b2ab77…`、planner-4 / coder-4 の出力、job 10761 (bnode020、69 秒)、523,120 / 122,211、
     815,983 tps、CV 0.16%、abort 率 9.07%、`continue`、critic-3 帰属不能 3 巡連続、`source_refs` 9、stock 対照未達の理由、[T-2795]。
   - 軽量 witness (entry 1696): W `5b02546f` と branch 名、4 arm の検出数、Fisher 0.500、検出力 0.105、commit 数 86%、96 file / 603 MB、
     測定 build の構成 (pin e9e477ca + X/P + 測定 patch、TRACE=1 観測専用)、identity checker 2 本 `match`。
   - mocc wave 2 (D2159、entry 1701): template patch 名 2 つ、30 check、`11161.nqsv` / 352 秒、identity 2 値 (`6454d9f3…` / `41f52341…`)、
     論理行列 543 / 548、offset 19 + 35×6、12 走 certified、verifier wall 52.9 秒、n=1 の 3 判定、変異 16/16、`ERR` の `__LINE__` 差 (1193 → 1228)、
     D2159 の項 2・3・7・8・9 と「主張しないこと」。
   - B-5 事前登録 v1 (D2158、entry 1692): B = 10、A = 30、候補集合 1..1000、score、判定順、1,773 論理 session、未発効、[T-2797]。
   - chain land 2 度目 (entry 1688): merge 2 本の SHA、三軸走査 hit 4、焦点走 8 file 1211 passed / 12 skipped、受入赤 1 node の名前と digest
     2 値 (`c405c742…` → `6a4ee1ef…`)、保存 branch `t2724-chain-land-2-saved` = `0a799da6c`、レンズ A / B の択、F30 再発。
   - A-2 nodes=5 (entry 1686): request `9137.nqsv`、bnode082 / 083、時刻、候補不採用の理由、policy nodes 5。
   - 軸 1 後継記録 (entry 1689): 78 leaf の区分 A 8 / B 53 / C 3 / D 6 / E 2 / F 5 / G 1、`Q3` 37 / `Q6` 37 の内訳、表題の訂正。
   - T-2786 (entry 1703): A 395.7 / L 709.4 / P 405.4 秒、L 3/3 悪化、P 変化なし、F649 再発。
   - 裁定待ち 4 件 (T-2792 / T-2795 / T-2797 / T-2766) が「未解決」として書かれ、裁定済みのように書かれていないこと。
2. **母集合と射程。** 新版が「certified」「pass」「anomaly 0」「完走」「再現」「解除」「承認」「実装」と書く箇所で、母集合が広すぎないか
   (例: 検証相を S-1 の充足・B-8 の取得・「全走 anomaly ゼロ」と読ませていないか、B-7 fixed5 の outer `reject` を「3 workload とも退行」・
   要件充足・正式判定と読ませていないか、第 2 cohort を「再現されたので飽和しない」・合成 verdict と読ませていないか、attempt-0002 の
   gate 拒否を「認可消費」「再投入不能」と読ませていないか、w1 完走を床値確定・ablation 開始と読ませていないか、K2 3 巡目を「効いた」と
   読ませていないか、wave 2 の緑を探索解禁と読ませていないか、witlight の 0/60 を観測者効果の除去と読ませていないか)。
3. **件数・量化。** 「すべて」「だけ」「N 件」「N 稿」「N 点」を原データから数え直せ。特に §0 の「13 点」、§2 (e) の「6 つ + 7 つ」、
   §2 (g) の「14 点」、§5 の「13 稿」、§7 の「76 + 11 = 87」、§9 の「7 種」、冒頭の「26 エントリ」「D2156〜D2164」「11 件」、
   「観測 4 件」、「4 度 certified」「3 巡」。
4. **path と参照。** 本文が引く一次資料の path・D 番号・T 番号・F 番号・entry 番号が実在し、内容が本文の記述と合うか。行番号参照が
   無いことも確かめよ (basename / 節名参照が規則)。
5. **凍結物の不変。** `git status --short` / `git diff --stat` で、変更が `docs/paper-story/2026-09-20.md` (新規、untracked) だけで
   あること、前版・`results/`・`figures/`・`claim-evidence/`・`docs/paper-story-backoff/`・README に差分が無いことを確かめよ。

## レンズ B — 主張の強さ、分類の一貫性、二重計上、前版との差分、先取り

6. **禁止句。** 「A-1 の値がある」「B-10 を閉じた」「再現されたので飽和しない」「mocc は第 2 成功例」「床値が発効した」「B-7 を
   充足した」「B-8 を取得した」「全走 anomaly ゼロ」「信頼度 1−εⁿ」「pin を前進させた」「K2 で改善した」に相当する表現 (短縮形・言い換え
   を含む) が本文のどこにも無いこと。B-10 の言い方が事前登録 §4.5 の固定表現に限られていること。
7. **版名の 3 層の付け替え。** 上記「新版の作り方」のとおり。特に §5 の注記 (「2026-09-17 版の注記 / 前版の注記 / この版の注記」)、
   §7 の「2026-09-17 版の更新 / 前版の更新 / この版の更新」、§8 の【状態】、§9 の「前版の 3 つ / この版の 3 つ」。
8. **分類の一貫性と二重計上。** §9 の 7 種の表で、同じ観測が 2 種に置かれていないか。検証相 (第 5 種)、B-7 fixed5 の median 比 (第 4 種)
   とその correctness (第 5 種)、第 2 cohort の verdict (第 4 種) と 120 記録 (第 5 種)、witlight (第 4 種)、wave 2 の 12 走 (第 5 種) と工程
   (第 6 種)、attempt-0002・w1・K2 3 巡目・B-5 v1・nodes=5・軸 1 記録 (第 6 種) の置き方が §0・§2・§6・§8 と食い違わないか。
9. **§6 と §8 の状態語。** 「言えること / 言えないこと」と A / B / C 群の【状態】が、§0 の 13 点および一次資料と食い違わないか。
   特に A-1・A-2・A-4・B-4・B-5・B-6・B-7・B-8・B-10・C-1・C-4 の状態語。B-8 の仕分け (P3) と B-7 fixed5 の置き場 (P4) の論理が
   §0・§2 (f)・§6・§8・§9 で一貫しているか。
10. **README の stale 注記 11 件との照合。** README (未更新) の「最新スナップショット以後に確定したこと」11 項目が、それぞれ新版本文の
    どの節に取り込まれているかを表にせよ。取り込み漏れ・要約での意味の変化があれば must-fix。
11. **先取り・scope。** 稼働中で未着地の wave の内容を書いていないか (着地済み正典は local main `b7f970dfa`、entry 1711 まで)。新しい主張を
    足していないか (brief の (P1))。裁定を先取りしていないか (例: A-1 2 本目の投入経路、K2 stock 対照の経路、B-5 本走、T-2766 採否、
    pin 前進の実施、chain の取り込み、B-10 pin 更新)。
12. **前版から消えた項目。** 前版 §5・§6・§7・§8 にあって新版に無い記述があれば列挙し、落としてよいか個別に判定せよ
    (§7 は 87 項で「落とした項目は無い」と書いてある)。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。規律 7。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。B-7 は充足と書かない。B-8 は取得と書かない。3 走行と A-1 attempt-0001 と B-7 fixed5 を
  pool しない (D1993 項 6)。2 cohort を合成しない (D2157)。
- 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」「床値が発効した」とは書かない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。隣接 docs (results 稿・claim-evidence 稿・figures/) の訂正・図の再生成・
  新しい主張の追加も scope 外。README の更新は親が段 7 で行う (この段の scope 外)。

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当節 (§番号と小見出し)、一次資料の path または
D 番号、対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け**
(書けない所見は nit)。

## stale 注記 11 件の取り込み先

表 (README の項目 → 新版の節)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

新版をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
