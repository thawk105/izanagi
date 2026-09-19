単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/docs/paper-story/2026-09-19.md (**レビュー対象の新版**、376,604 bytes / 3,212 行 — **全文 `cat` しないこと**。`grep -n "^## \|^### \|^#### "` で節の位置を出し、`sed -n` で 80 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/docs/paper-story/README.md (**レビュー対象。版の履歴表・訂正一覧・stale 注記の 3 節が更新された**、34,775 bytes)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260919/brief-s1.md (親の段 1 brief と段 4 の provisional 裁定 (P1)(P2)。新版が従うべき scope と不変条件)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md (A-1 attempt-0001 の単独稿、45,418 bytes。新版の A-1 の数値の出所)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md (mocc 観測 1)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/output/insights/2026-09-18/t2779-mocc-g2-observation-conditions/README.md (mocc 観測 2)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/output/insights/2026-09-18/t2780-mocc-pilot-discriminator/README.md (mocc 観測 3)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/README.md (g1 候補の生成)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md (chain land の不成立)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/output/insights/2026-09-19/t2783-critic-input/README.md (critic 診断の型付き入力経路)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/docs/paper-story/figures/README.md (fig8 節・fig9 節。`grep -n "^# "` で位置を出して該当節だけ読め)

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は 5,628,115 bytes / 67,860 行、`docs/failures.md` は 2,755,772 bytes、
前版 `docs/paper-story/2026-09-17.md` は 309,527 bytes、worklog の archive は `docs/archive/worklog-phase3-09*.md` に 1 エントリ 1 file
(各 600〜700 行、本文は先頭 10〜40 行で残りは carry 行)。**全文 `cat` してはならない。**
`grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。`wc -c` / `wc -l` は許す。
新版が引く D 番号のうち検算に要るのは D2104 (項 2)、D2108、D2114、D2120 (項 1〜4・7・14〜16)、D2127、D2134、D2138、D2143、D2145、D2146、
D2147、D2148 (項 1〜3・5・11・13)、D2150 (項 1・2・4)、D2153、D2154、D2155 である。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が新版の本文と README の 3 節を書いた。この wave は軽量版 (docs-only、実装面ゼロ) で、段 2 plan と
段 3 敵対相談は省いた。**お前は D2148 項 11 が定める「一次資料から事実を再抽出する docs-only wave の段 6 read-only
独立レビュー 1 本」であり、下の 2 レンズを 1 本で担う。**
親が実走した検査: `tools/check_docs.py` rc=0、三軸語走査 (`s8b_holdout_freeze search`) rc=0 (両 holdout の
conjunction hit 0、陽性対照 217)、本文が引く `output/insights/` 26 path の実在確認、§7 の件数 (前半 67 / 後半 9 = 76)、
§0 の 13 点、§2 (g) の 11 点、`ad83b108b` が前版起点 `fa24e6ea8` の祖先でないこと (rc=1)、`0b4fbd7a6` (B-4 spec 凍結) が
HEAD の祖先であること、`cc82edc8c` (chain X1') が HEAD の祖先でないこと、現行 ccbench pin `511c9538`、A-2 policy の
`scheduler.nodes` が 1 のまま、`SATISFIABLE_CONDITION_IDS == {"C10"}`。

新版の作り方: 前版 `2026-09-17.md` を起点に、冒頭・§0・§2 (g)・§9・§10 を全面差替え、他節は箇所ごとに再導出した
(置換 123 件 + 後処理 20 件)。**§10 の「段 6」小節は、お前のレビュー完了後に親が所見と裁定を書く。草稿の時点では
「これから通す」と書いてあり、その完了形の先取りが無いことを確かめよ (完了形で書いてあれば must-fix)。**

## レンズ A — 一次資料との照合、母集合、射程、件数

1. **数値・日付・判定を一次資料と照合せよ。** 少なくとも次を権威 bytes / insight / D 本文で検算せよ:
   - A-1 attempt-0001: job ID と host、対差平均 3 値・h・B・baseline 平均・分類・`variance_plan_breach`、6 arm の verify
     (certified / anomalies 0 / legacy)、`formal=false` / `promotion_prohibited=true` / `result_authority`、
     `measurement_source_commit` `d2ebef7a4`、submit / materialize の時刻、result.json の sha256 `372f199e…`、fig9 の着地 bytes
     の SHA-256 (figures/README.md)、限定 20 件、認可の形 (D2120 項 3、1 attempt・落ちたら止める)。
   - mocc 観測 3 件: T-2774 の 5 arm の検出数 (2/40・3/40・2/40・0/40・0/40)、cycle 7 件の形、Fisher 0.128〜0.247、Q1 の格下げ、
     discriminator 発火 0、段 3 が親 brief を覆した 3 点; T-2779 の 5/120・0/120・2/120 と Fisher 0.0299507441 / 0.2230864755、
     360 走; T-2780 の job `5905.nqsv`、Elapse 127 秒、`no-g2`、D2153; D2148 項 13 の逐語。
   - official 床値 / g1: 候補 path と sha256 `7e111406…` (20,737 bytes)、X1' `cc82edc8c` / X2 `4d8fb93b7`、保存 branch 名、
     D2097 / D2098、D2120 項 2 の (a)〜(f)、entry 1640 の「非 hold 45 node」と oracle gate、D2154 の内容 (委譲の発火条件・
     維持するもの・到達範囲)、D2148 項 1。
   - B-4: 凍結 commit `0b4fbd7a6`、窓 w1 / w2 の UTC 範囲、n = 62、campaign_id 形、`--validate-only` 3 本 rc=0 (D2138)、
     D2145 の 1 job = 1 spec × (1 窓 | finalize)、D2146 / D2150 項 2 の PerfConfig 3 種、「実測は始まっていない」
     (spec の directory に窓の出力が無いこと)。
   - identity: D2104 項 2 の (a)、F1021、D2108 の空入力 prefix、8/8 byte 一致、再変異の結果 (M3b / M6 / M4 / M4b、M3a、M0)、
     D2120 項 7 の限界 2 つ。
   - K2: T-2746 の attempt-0001 `4947` / attempt-0002 `4954`、variant `3dec27291054`、687,508.5 tps、CV 1.0068%、commits / aborts、
     proposal-3 = 20、critic の候補 10、D2148 項 2、D2143 の内容、T-2783 / D2155 の内容 (6 field、K2・非 B-4・reflux on、
     3 巡目未投入)。
   - Silo スコープ解除 (D2114) の射程 (発話が含まないもの)、pin 前進の承認 (D2150 項 1 の (i)〜(iv))、T-2756 の材料
     (e9e477ca の位置、D297 検査の結果、134 file)、T-2772 の完了判定 3 点と数値、T-2760 / D2127。
   - 軸 1: D2095、5 窓目の 5/5 不一致、6 窓目の Q6-SY2025 / Q6-SY2026、D2120 項 14、D2150 項 4、61 + 16 = 77 leaf、78 leaf。
   - fig8: 実装 `4636181a9`・fix `ce39429d5`、着地 bytes の SHA-256 3 件、D2120 項 16。
   - 単独稿: A-6 稿の限定 12 件、T-1998 稿の限定 20 件と 10 項目の 3 区分、results 系列 10 稿。
   - T-2489: 所要、検査 24 件、`finish-group` まで、D2148 項 5、policy の nodes=1。
   - 一括裁定 4 回の D 番号・回次・項数・日付。
2. **母集合と射程。** 新版が「certified」「accepted」「completed」「そろった」「再現」「解除」「承認」と書く箇所で、母集合が
   広すぎないか (例: A-1 attempt-0001 の descriptive 出力を「A-1 の値」「再現」と読ませていないか、mocc の観測を根因・
   第 2 成功例と読ませていないか、pin 前進の承認を実施と読ませていないか、g1 床の採用裁定を発効と読ませていないか、
   B-4 spec 凍結を実験の開始と読ませていないか、T-2731 の修正を identity の完全証明と読ませていないか)。
3. **件数・量化。** 「すべて」「だけ」「N 件」「N 稿」「N 点」を原データから数え直せ。特に §0 の「13 点」、§2 (e) の
   「6 つ」、§2 (g) の「11 点」、§5 の「10 稿」、§7 の「76 項」、§9 の「7 種」、冒頭の「104 エントリ」「D2091〜D2155」。
4. **path と参照。** 本文が引く一次資料の path・D 番号・T 番号・F 番号・entry 番号が実在し、内容が本文の記述と合うか。
   行番号参照が無いことも確かめよ (basename / 節名参照が規則)。
5. **凍結物の不変。** `git status --short` / `git diff --stat` で、変更が `docs/paper-story/README.md` (更新) と
   `docs/paper-story/2026-09-19.md` (新規) の 2 file だけであること、前版・`results/`・`figures/`・`claim-evidence/`・
   `docs/paper-story-backoff/` に差分が無いことを確かめよ。

## レンズ B — 主張の強さ、分類の一貫性、二重計上、前版との差分、先取り

6. **禁止句。** 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」に相当する表現 (短縮形・言い換えを含む) が
   本文のどこにも無いこと。B-10 の言い方が事前登録 §4.5 の固定表現「この事前登録の述語では、表現可能域である 9999 マイクロ秒
   までに飽和を観測しなかった」に限られていること。
7. **前版由来の記述の付け替え。** 前版で「この版で…」と書かれた事実 (fig7 の着地、右 tail の完走、床値の初完走、T-2630 の実測、
   K2 の 1 巡、D2044 など) が新版でも「この版で」のまま残っていないか。残っていれば must-fix (新版で新しく起きたことと
   混同させる)。逆に、新版で新しく起きたことが「前版で」と書かれていないか。
8. **分類の一貫性と二重計上。** §9 の 7 種の表で、同じ観測が 2 種に置かれていないか。A-1 attempt-0001 (第 4 種)、その
   correctness (第 5 種)、mocc 観測 (第 4 種)、mocc wave 1 の stock 対照 (第 5 種) と工程 (第 6 種)、g1 候補・A-3 (第 6 種) の
   置き方が §0・§2・§6・§8 と食い違わないか。
9. **§6 と §8 の状態語。** 「言えること / 言えないこと」と A / B / C 群の【状態】が、§0 の 13 点および一次資料と食い違わないか。
   特に A-1・A-4・B-4・B-6・B-9・B-10・C-1・C-4 の状態語。
10. **README の 3 節。** 版の履歴表の新行、訂正一覧 (0 件と書いた根拠)、stale 注記 (3 件 → 0 件、移管先 3 つ) が新版の本文と
    食い違わないか。results 系列の表 (10 行)・claim-evidence 節・恒久 erratum 節が壊れていないか。
11. **先取り・scope。** 稼働中で未着地の wave の内容を書いていないか (着地済み正典は local main `a99425b66`)。新しい主張を
    足していないか (brief の (P1))。裁定を先取りしていないか (例: A-1 の再認可、pin 前進の実施、chain の取り込み、B-4 の実走)。
12. **前版から消えた項目。** 前版 §5・§6・§7・§8 にあって新版に無い記述があれば列挙し、落としてよいか個別に判定せよ。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物は 1 byte も変えない。旧 attempt の判定を取り消さない。protocol status は成否宣告ではない (D12)。規律 7。
- B-10 の言い方は事前登録 §4.5 の固定表現に限る。B-7 は充足と書かない。3 走行と A-1 attempt-0001 を pool しない (D1993 項 6)。
- 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」とは書かない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。隣接 docs (results 稿・claim-evidence 稿・figures/) の訂正・図の
  再生成・新しい主張の追加も scope 外。

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当節 (§番号と小見出し)、一次資料の path または
D 番号、対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・分類・参照がどう変わるかを 1 行で書け**
(書けない所見は nit)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。数値群・参照群を列挙せよ。

## GO / NO-GO

新版をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
