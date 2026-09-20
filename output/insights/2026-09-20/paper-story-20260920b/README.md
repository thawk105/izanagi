# 論文ストーリー 2026-09-20 第 2 版 (`2026-09-20b.md`) の全項目再導出 — wave 記録

`docs/paper-story/2026-09-20b.md` を、2026-09-20 18:01 JST 時点の正典全体から全項目再導出して追加した wave の
記録である。**新規計測はしていない。** 既存の版 10 本・`results/` 19 稿・`figures/`・`claim-evidence/`・
`docs/paper-story-backoff/` は 1 byte も変えていない。

- wave: `dev-wave-paper-story-20260920b`、branch `worktree-dev-wave-paper-story-20260920b`、背景 job 88c7f91a
- 起点: local main `fec4a818741e5464fffcd11e4b094c125dfe5280` (2026-09-20 18:01 JST、worklog entry 1746 までの fold を含む)。
  **導出の起点は `fec4a8187`。** 段 7 で local main (段 6 完了時点) を固定 SHA で取り込んでから README を更新した。
- 成果物: `docs/paper-story/2026-09-20b.md` (新規、4,569 行) と `docs/paper-story/README.md` の 4 節の更新
  (版の履歴表へ 1 行、「最新 = `2026-09-20b.md`」、訂正一覧を「1 件」へ、stale 注記 3 件を本文へ移管し、着手後に着地した
  ccbench pin 前進を 1 件積み、受入の claim 前に着地した 4 件 (T-1871 追補、第 26 回裁定 D2186 の B-8 段階認可、K2 pair 初投入、A-1 attempt-0002
  完走) を積んだ = 計 5 件)。実装面ゼロ。
- 依頼: 「論文ストーリー次版 `docs/paper-story/<着手日>.md` を正典全体から全項目再導出する (docs-only)。着手直前の local main から
  fresh worktree。現行版 2026-09-20 以後に着地した results 稿 5 本 (mocc-g2 観測条件、mocc-witlight 4 arm、K2 手動 loop 3 巡、S-1a 9 対、
  B-10 待ち方 grid 正式走) と着地していれば p24 静的 sweep 稿、図 5 本 (fig8b、fig10、fig11、fig12、fig3b) を反映し、現行版の事実誤認
  2 点 — §4「第 2 cohort は fig8 に描かれていない」と §8 B-1「非列挙の定義の置き直しは未裁定」(D1441 が裁定済み) — を訂正する。
  採用する資料の締切は着手時の local main に固定し、p24・A-1 attempt-0002 の完了を待たない。最初に時点語を機械置換してから節を書き、
  見出し・括弧書きの状態語も D 本文へ再照合する。README は受入の owned-path に入れず、表行は段 7 で main を取り込んでから当てる。
  §10 は草稿では予定形。英語稿・2 本目論文の版は作らない。gate・検査・台帳の追加は scope 外」。**全項目の再導出であり、一項目の
  差分改訂ではない。**

## 1. 段 1 — brief と provisional 裁定

- 軽量版 (`DW-C00`): 段 2・3 を省き、段 5 は親の docs 編集、段 6 は read-only review 1 本 + 焦点再レビュー 1 本、変異 matrix は
  実装面ゼロで免除、受入は記録 commit 後の tip で 1 走。brief の逐語は `verbatim/brief-s1.md`。開始 gate (`check_wave_startup.py --mode
  fresh --external-handoff`) は rc=0 (`verbatim/startup-gate.log`)。条件表 08 / 09 / 10 / 11 / 13 はいずれも不成立。
- **(P1) 版名:** 着手日が現行版と同じ 2026-09-20 なので `2026-09-20b.md` (同日 2 版目)。README の「新しい日付のスナップショットを
  追加する」規則を「新しい版を別 file で追加する」として適用し、版の履歴表の日付欄は「2026-09-20 (第 2 版)」。
- **(P2) 依頼が「事実誤認」と呼んだ 2 点の型判定 (段 1 で実測):** (a) fig8 の文 — fig8b の commit `864d7135e` は 08:05:55 JST の author
  commit で、前版の起点 `b7f970dfa` にも前版の fold `24bc8441b` (09:11:51) にも含まれない (`git merge-base --is-ancestor` rc=1)、main への
  着地は 10:36 以後 → **執筆時点では真で後続が古くした型**。冒頭の訂正一覧には載せず本文更新にした (README の stale 注記にも積まれて
  いなかったので併せて吸収)。(b) 「非列挙」未裁定 — D1441 の fold は 2026-09-02 07:43 (`89a551d0e`)、2026-09-02 版の fold は同 04:42:32
  (`45994d900`、導入 commit `ad88a391c` 04:22:41。親の初稿の「07:14 `b664df20c`」は別 wave の merge で、段 6 レビューが訂正) なので同版は当時真、2026-09-05 / 09-14 / 09-17 / 09-19 / 09-20 の 5 版 (各 2 箇所) は**執筆時点の誤り**。前版は §8 B-5 で
  D1441 を引いており版内で矛盾していた。冒頭の訂正 1 として 4 か所を直し、「その定義の下で段階 B を再走した wave は無く軸は休眠」
  (D52、D2158) と書いた。**親の初稿は「実装残件として起票された項目も無い」と書いたが、次の一手には [T-1871] (D1441 の 4 点を事前登録の
  追補として置く、裁定済み・実装待ち) が carry stub として残っていた** (語で走査して stub の本文 entry 1184 を遡らなかった。段 6 の 2 レビューも
  拾わず、レビュー 10 は「全履歴の不在は証明していない」と限定)。受入の claim 前に peer の着地通知 (entry 1752 = 追補の着地) から知り、
  版の 5 箇所 (冒頭・§2 (b)・§3 項目 2・§8 B-1・§10 (P2)) を「[T-1871] が起点時点で残っていた」へ直した (`r26.py`、5 件)。F1 再発 (near-miss) として
  failures fragment に追記。
- **(P3) 反映集合:** 依頼名指しの稿 6 本・図 5 本、README の stale 注記 3 件 (fig10・B-7 限定付き充足・fig12)、§6 / §8 の状態語を動かす
  裁定・実装 (g1 の発効 D2166 / D2167 / D2180、B-7 D2174 項 3、A-1 rear gate D2178、K2 pair launcher D2183、B-5 段階裁定 D2172 項 4、
  B-8 事前登録 D2175、fig8b D2173、mocc 追加実験の見送り D2172 項 7、受入 pairing の採用裁定 D2172 項 1) を本文へ入れ、それ以外の着地
  (D2165 / D2168〜D2171 / D2176 / D2177 / D2179 / D2181 / D2182、[T-2789] / [T-2791] / [T-2796] など) は §2 (e) / §5 の運用素材と状態語の
  訂正だけに留めた。新しい主張は足していない。
- **(P4) g1 の発効の書き方:** 「凍結 v2 g1 が発効した」とは書き、「床値が発効したので oracle が走れる」「official 床値が科学的に有効」
  「人間が批准した holdout」とは書かない。発効の意味を「配線下限で決まった床を持つ世代が AI 委任の A / X で active になった。批准
  loader は成功、full launch validation は既存不整合 2 件で `allowed: false` ([T-2810])、W-4 / W-5 は未」と限定した。
- **(P5) B-7 の限定付き充足の書き方:** 4 語の限定 (単一 attempt・descriptive・非認証・反復間安定性は未判定) を必ず添え、報告要件の
  充足であって採用・認証・性能主張ではないと併記し、§9 の 4 文へ入れない。
- 稼働中で未着地の wave の内容は書いていない。段 5 の途中で peer wave (`dev-wave-t2304-pin-advance`) から「main は `482f19b88` へ
  進んだ (gitlink e9e477ca)」「land が rc=27 で一時停止」「landed main `6a3e15809` (19:03 JST)」の通知 3 通を受けたが、peer 通知は
  local main 再読の契機にだけ使い、起点は動かさなかった (依頼が締切を着手時 main に固定)。pin 前進は段 7 で README の stale 注記へ
  1 項として積む (peer と合意)。受入の claim 前 (門番待ち中、20:53〜21:0x JST) に peer から A-1 attempt-0002 完走の着地通知を受け、main を再読して
  entry 1751〜1755 (第 26 回裁定 D2186、T-1871 追補、T-2632、K2 pair 初投入 D2187、attempt-0002) を確認し、版の状態語を動かす 4 件を stale 注記へ
  積んだ (版本文は起点の状態のまま。取り込みは受入の post-claim merge に任せる)。

## 2. 依頼が挙げた事実と状態語を動かす裁定の一次資料と実測値

| 事実 | 一次資料 | 版に書いた状態語 |
|---|---|---|
| chain / X2 / G の main 着地 (D2166、entry 1716) | `output/insights/2026-09-20/t2724-b10-pin-update/README.md` | pin `c405c742…` → `6a4ee1ef…` (20 file)、初回列は `landed-fold-owned-path` rc=26 で組み直し、merge `629690fdd` → main `0e647f84c`、X1' / X2 / G は main の祖先、変異 3/3 KILLED・負例 3 件、旧測定の解釈は不変 |
| 承認 A / active pointer X の AI 委任 (D2180、entry 1742) | `output/insights/2026-09-20/t2724-ax-delegated/README.md` | A `a3bf67a8c` (14:24:52) / X `70e87c9c9` (14:25:30)、`_assert_user_commit` = 非 merge・trailer ちょうど 1 行・H ancestry (実装 `4114cf51b`)、批准 loader 成功 (generation 1、`7e1114…`)、P3 gate-check は `journal-state-invalid` (`_JOURNAL_KEYS` に `reservation-preflight` 無し) + 段階 6 lineage で `allowed: false` → [T-2810]、B-10 pin は A / X 込み `92099c87…` (`ca3907e57`)、「AI が自己承認した世代」の呼称は D2180 の対象外 |
| B-7 の限定付き充足 (D2174 項 3、entry 1731) | `output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md`、`output/insights/2026-09-20/t2610-b7-fixed5-fig10/README.md` | 4 語の限定、D2044 項 3 を supersede、択 (b) 不採用、入口 3 か所、稿と fig10 の bytes 不変、caption "not a B-7 satisfaction decision (D2044 item 3)" は着地時点の記録 |
| A-1 rear gate の認可 record (D2178、entry 1736) | `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md`、同 `t2792-a1-sized-preregistration-amendment/README.md` | 定数 `V3_SIZED_RERUN_AUTHORIZATIONS` 1 件 × exact record × 先行 attempt-0001、不一致 9 種は拒否、公開先は兄弟 dir、焦点走 1697 passed、投入は未 |
| K2 pair launcher (D2183、entry 1746) | `output/insights/2026-09-20/t2795-pair-launcher/README.md` | `--stock-control`・同 campaign・成功条件に STOCK 性・`IZANAGI_S4_STOCK_CONTROL`・resolver で fail-closed、変異 17/17 KILLED、pair は 1 job も未投入 |
| 一括裁定 2 回 (D2172 13 項、D2174 7 項) | `docs/decisions.md` の D2172 / D2174 | 4 件の裁定待ちが解消 (T-2792 択 1 / T-2795 択 (i)+(iv) / T-2797 段階 (A) / T-2766 択 (a))、mocc 追加実験見送り、派生値 pin 維持、fixture 移送とゾンビ除外見送り、「裁定は完了を意味しない」 |
| B-8 事前登録 v1 (D2175、entry 1733) | `output/insights/2026-09-20/b8-longrun-verify-prereg/README.md`、`docs/b8-final-candidate-longrun-verify-preregistration.md` | 案 A / B、自己シード、≥ 6 s を校正で決め 3 s へ丸めない、≤ 4 h / 対象、統計文 4 種は書かない、未発効 |
| verifier 容量 (D2181、entry 1744) | `output/insights/2026-09-20/verifier-capacity/README.md` | CoW / pool 停滞 (F1032)、bal10 478 s / 32.4 GiB、wh10 297 s / 15.2 GiB、判定は bytes 同一、read-heavy 10 s 未保全 |
| fig8b (D2173、entry 1728) | `output/insights/2026-09-20/t2793-fig8b-cohort2/README.md`、`figures/README.md` fig8b 節 | 縦 2 block、役割と順序は定数、PNG `ddab2873…` / PDF `c5454454…` / provenance `429b4028…`、合成しない |
| fig10 / fig11 / fig12 / fig3b | `figures/README.md` の各節 | 着地 bytes 3 値ずつ、fig3b は 2026-09-19 版の状態 (着地 test 無し) |
| 単独稿 6 本 | `docs/paper-story/results/2026-09-20-*.md` (verify-phase を除く 6 本) | 判定は不変、限定を先頭に置く、p24 未丸め 3 値は A-3 と一致、B-10 待ち方 grid 稿の日付は起草日 |
| mocc 追加実験の見送り・上流報告案 (D2172 項 7、entry 1739) | `output/insights/2026-09-20/t2791-mocc-upstream-report/README.md` | 見送りは費用対効果・択は残る、報告案 `[S-01]`〜`[S-63]`、AI は送信しない |

## 3. 版の作り方

- 前版 `2026-09-20.md` を複製し、**最初に「前版」→「2026-09-19 版」(191 件)、「この版」→「前版」(178 件)、「本版」→「前版」(3 件)
  の機械置換を当てた** (job dir `map1.py`)。冒頭・§0・§2 (g)・§10 を全面差替え (`sec-head.md` / `sec-0.md` / `sec-g.md` /
  `sec-10-draft.md`、marker 行に束縛した `splice.py`)、他節は箇所ごとに exact 1 回一致・all-or-nothing の置換 (`r1.py`〜`r21.py`、
  `apply.py`、計 186 件) で再導出した。§7 は前版の後半 11 項を前半末尾へ移し (87 項)、この版で 13 項を足した (計 100 項)。§0 は 13 点、
  §2 (g) は 14 点、§2 (e) の運用素材はこの版で 7 つ、§5 の「この版で加わったもの」は 15 項。
- 親の自己点検 (置換後): 「未発効」「人間手番」「裁定待ち」「図は無い」「繰延べ」「〜でも前版でも」を grep して時点語と状態語を
  付け替え (r18〜r21、計 16 件)、空白抜け 2 件を直した。
- README は段 7 で `readme_update.py` (exact 一致・fail-closed) で更新した。

## 4. 段 6 — read-only レビュー 1 本と焦点再レビュー 1 本

- **1 本目** (Codex `gpt-6-astra`、effort medium、read-only、19:06〜19:14 JST、26 model call、wall 510 秒): **NO-GO**、所見 10 件
  (must-fix 6・should-fix 2・refuted 2)。逐語は `verbatim/prompt-review.md` と `verbatim/review-out.md` (receipt の `output_sha256`
  `5305240d…`、行末空白の可逆正規化は `verbatim/verbatim-normalization.json`)。親が一次資料で検算した結果 **real 8、refuted 2**
  (refuted 2 件はレビューが親の型判定 (fig8b = 後続型、非列挙 = D1441 で裁定済み) を攻撃候補として立て、自ら祖先性と D 本文で再実測して
  refuted と裁定したもの。親も同じ)。real の内訳: (1) S-1a 単独稿の限定件数 16 → 19 (cohort2 稿の 16 を写した転記誤り、3 か所)、
  (2) fig8b の PDF SHA-256 の転記誤り `c5454544…` → `c5454454…` (16 桁の目視で写した。前 wave の教訓「転記 SHA は集合比較で検査する」の
  再発 — job dir の `check_hashes.py` で版の 8 桁 prefix 43 件を figures / results / provenance の現物と集合比較し、残り 28 件一致を確認)、
  (3) 2026-09-02 版の着地時刻 (「07:14 `b664df20c`」は別 wave の merge。導入 `ad88a391c` 04:22:41、fold `45994d900` 04:42:32 へ。型判定は
  不変)、(4) §0 第 3 幕と §2 (g) の「B-5 の試走を投入可能にする経路 / 機構」の先取り (共有部品の一部が着地、試走に要る実装は残る、へ。
  「機構 3 件」→「機構 2 件と投入へ近づける部品 1 件」)、(5) §0 項 12 の版名の 3 層 (claim-evidence 稿の導出元「前版 (2026-09-19 版)」→
  「論文ストーリー 2026-09-19 版」)、(6) §2 (e) 項 6 の「非 wire integrity」の「非」の脱落、(7) §7 の verifier 禁止句の射程 (実装 bytes の
  変更まで否定していた)、(8) §4 共通段落の「専用テストが守る」の一般化 (fig3b は着地 test 無し)。fix は `r22.py` (置換 15 件)。
- **焦点再レビュー** (同 model、19:20〜19:24 JST、13 model call、wall 230 秒): 所見ごとの closed / partial / regressed 表 — **closed 10 /
  partial 0 / regressed 0**、派生値 (§0 13 点、§7 100 項、19 稿、限定 19 件、5 版、4 か所) を独立に再計数、`r22.py` の 15 置換が旧文一致 0・
  新文一致 1、§10 の記録がレビュー出力と一致、焦点小節が予定形。**新規 must-fix 1 件で NO-GO** — §7 の前版由来の項目「同一候補 fixed 5 µs …
  B-7 の要件充足と書かない … (D2044 項 3 維持)。恒久」が supersede 済みの旧裁定を恒久規律にしており §6 / §8 / §9 と矛盾。親の裁定 real、
  `r24.py` (置換 3 件) + exact claim の材料稿の文 1 件で、「測定 / 稿自身を充足判定と読まない。後続の D2174 項 3 が限定付き充足を裁定し
  D2044 項 3 を supersede した」へ揃えた。逐語は `verbatim/prompt-focus.md` と `verbatim/focus-out.md` (`output_sha256` `358ceb26…`)。
  **3 巡目は起動していない** (`DW-O16` の上限内。残る所見は 1 件で対案どおりに直し、`check_docs` と path / D / F の実在検査を再走して
  閉じた)。§10 の焦点小節は親が完了形で書き、冒頭と §10 導入を完了形へ改めた (`r25.py`)。
- 両レビューが「未完」と自ら書いた範囲 (全参照本文の意味の網羅照合、全文の意味単位の脱落、段階 B の全履歴にわたる不在証明) は、この版
  でも検証済みとは扱わない。
- 親の手順: レビュー子が worktree を読んでいる間、親は worktree の docs に触れず、fix は job dir の script として作り、子の完了後に
  worktree へ当てた。焦点再レビューの間も同じ。

## 5. 検査

- `python3 tools/check_docs.py`: 違反なし (草稿完成時、fix 後、README 更新後)。
- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: 両 holdout とも hit 4 (official 床値 run dir 3 file + 候補 =
  chain 着地後の設計どおり、D2120 項 2 (a)(d))。新版 file は hit に含まれない。
- 引用 path の実在確認 (`check_paths.py`): 223 件、不在は相対断片 13 件と attempt-0002 の期待公開先 1 件 (未作成と本文が明記) と本 insight の
  `verbatim/` (作成前の走査。作成後は実在)。転記 SHA の集合比較 (`check_hashes.py`): 8 桁 prefix 43 件のうち 29 件が figures / results /
  provenance の現物と一致、残り 14 件は commit sha・identity・較正 / 凍結の digest。
  D 番号 231 件・F 番号 17 件の見出し実在。`git diff --check` 0、NFC、U+0300〜U+036F なし。
- 祖先性の実測 (`ancestry.py`): X1' `cc82edc8c`・X2 `4d8fb93b7`・G `229982652`・merge `629690fdd`・`0e647f84c`・`4114cf51b`・
  A `a3bf67a8c`・X `70e87c9c9`・`ca3907e57`・fig8b `864d7135e`・`2361220d4` は HEAD の祖先 (rc=0)。fig8b は前版起点 `b7f970dfa` と
  前版 fold `24bc8441b` の祖先でない (rc=1)。現行 gitlink `511c9538e4e8…`、`EXPECTED_FREEZE_TREES_SHA256` = `92099c87e935…`、
  A / X の record file が実在。D1441 の fold `89a551d0e` (2026-09-02 07:43) と 2026-09-02 版の fold `45994d900` (同 04:42。導入 `ad88a391c` 04:22)。
- 記録 commit の直前に paper-story を読む test 9 file を計算ノードへ dispatch した焦点走の結果と、記録 commit 後の受入全走は worklog fragment
  と land の受領証に記す (この README の作成時点では未実施)。

## 6. 工数

- codex 子 2 本 (review 1 = 26 call / 510 秒、focus 1 = 13 call / 230 秒、全段 `gpt-6-astra` / medium)。author / fix 子は 0 (実装面ゼロ)。
- 親: 前版全 10 節の読了 (3,866 行)、entry 1712〜1746 の見出し 35 件と本文 12 件、D2165〜D2183 の本文 (D2172 / D2174 / D2178 / D2180 /
  D2183 / D2175 / D2167 / D2166 は全文)、D1441、results 稿 6 本の冒頭、figures README の 5 節、insight 12 本の冒頭、memory 6 本、
  path 実在確認 223 件、祖先性 / 日時の実測 33 件、`check_docs` 5 回、三軸語走査 1 回、SHA prefix の集合比較 2 回。
- wave 全体: 18:01 JST 着手 → 段 6 GO 19:2x → 段 7 記録 (README 更新は main `800178b39` を ff-only で取り込んだ後)。受入・land の時刻は
  worklog fragment と land の受領証が持つ。

## 7. 言わないこと

- この版が新しい主張を足したこと (足していない)。図の再生成・results 稿の改稿 (していない)。
- 「A-1 の値がある」「A-1 の 2 本目が投入された」「B-10 を閉じた」「再現されたので飽和しない」「mocc は第 2 成功例」「床値が発効した
  ので oracle が走れる」「official 床値が科学的に有効」「B-7 を無限定に満たした」「B-8 を取得した」「全走 anomaly ゼロ」「信頼度
  1−εⁿ」「pin を前進させた (基準 HEAD 時点)」「K2 で改善した」「対照が取れた」。
- 稼働中で未着地の wave の内容 (書いていない)。T-2810・W-4・B-5 本走・attempt-0002 の投入結果・K2 pair の結果の先取り (していない)。
