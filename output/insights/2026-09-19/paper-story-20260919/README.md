# 論文ストーリー 2026-09-19 版の全項目再導出 — wave 記録

`docs/paper-story/2026-09-19.md` を、2026-09-19 時点の正典全体から全項目再導出して追加した wave の
記録である。**新規計測はしていない。** 既存の版 8 本・`results/` 10 稿・`figures/`・`claim-evidence/`・
`docs/paper-story-backoff/` は 1 byte も変えていない。

- wave: `dev-wave-paper-story-20260919`、branch `worktree-dev-wave-paper-story-2026-09-19`、背景 job 4e4cd114
- 起点: local main `a99425b66` (2026-09-19 21:41 JST、worklog entry 1685 までの fold を含む)。wave 中に main の取り込みは
  していない (land 時の受入と land が取り込む)。**導出の起点は `a99425b66`。**
- 成果物: `docs/paper-story/2026-09-19.md` (新規、3,325 行 / 394,236 bytes) と `docs/paper-story/README.md` の 3 節の更新
  (版の履歴表へ 1 行、訂正一覧を「0 件」へ、stale 注記 3 件を本文へ移管して 0 件へ)。実装面ゼロ。
- 依頼: 「docs/paper-story/ の次版 (実行日の日付) を書く。前版 2026-09-17.md 以後に一次資料で確定した事実だけを反映する
  (8 事実を名指し)。README の版規則に従う。§6 と §8 の A/B 群の状態語を一次資料へ再照合し、『A-1 の値がある』『B-10 を閉じた』
  『mocc は第 2 成功例』とは書かない。D2148 項 11 に従い段 6 の read-only 独立レビュー 1 本を残す。実装面差分ゼロ。scope 外 =
  新しい主張の追加・図の再生成・results 稿の改稿」

## 1. 段 1 — brief と反映集合の裁定

- 軽量版 (`DW-C00`): 段 2・3 を省き、段 5 は親の docs 編集、段 6 は read-only review 1 本 + 焦点再レビュー 1 本、変異 matrix は
  実装面ゼロで免除、受入は記録 commit 後の tip で 1 走。brief の逐語は `verbatim/brief-s1.md`。
- **(P1) 反映集合:** 依頼の 8 事実を必須反映集合とし、それ以外で §6 / §8 の状態語を変える着地事実 (B-4 spec 凍結 D2138 と job body
  D2145 と PerfConfig D2146、[T-2731] の F1016 修正 D2108、K2 2 巡目 [T-2746] と D2148 項 2、pin 前進の承認 D2150 項 1、Silo
  スコープ解除 D2114、軸 1 の再開 D2095 と限定閉鎖 D2120 項 14 / D2150 項 4、層3 v3 の初適用 D2143、TicToc baseline D2127、mocc
  機械実証 D2134 / D2147、A-2 nodes=5 裁定 D2148 項 5、[T-2489]、[T-1878]、[T-2321]、[T-2758]) は状態語の訂正として反映し、
  新しい主張は足さない。段 6 の 2 本は (P1) を攻撃せず、反映の範囲そのものへの所見は無かった。
- **(P2) 前版の執筆時点の誤り:** 0 件。[T-2590] の実装 commit `ad83b108b` が前版起点 `fa24e6ea8` の祖先でないことを
  `git merge-base --is-ancestor` (rc=1) で実測し、前版の「着地済み正典は無い」が当時真だったことを確かめた。
- 裁定 inbox の再走査 (段 4 直前): `2026-09-19-a1-sized-attempt-0002-authorization.md` (ユーザー裁定、台帳未記録、稼働中 wave) を
  確認したが、着地済み正典に無いので版へ書かない (前版 §7 の「稼働中で未着地の wave の内容を版へ書かない」)。

## 2. 依頼が挙げた 8 事実の一次資料と実測値

| 事実 | 一次資料 | 版に書いた状態語 |
|---|---|---|
| official 床値の実値と未発効 | `output/insights/2026-09-16/t2698-official-floor-resubmit/README.md`、`output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/README.md`、`output/insights/2026-09-18/t2724-freeze-g1-chain-land/README.md`、D2120 項 2、D2154 | rr20 = 35,817.945 / rr80 = 46,065.78 (配線下限 0.03 × stock 中央値)、g1 の床としての採用は裁定済み、g1 候補は保存 branch (sha256 `7e111406…`)、chain は main に未取り込み (`cc82edc8c` は HEAD の祖先でない、rc=1)、A / X は人間手番、未発効 |
| A-1 attempt-0001 の descriptive 結果 | `output/insights/2026-09-13/paper-story-a1-balanced5-sized/result.json` (`372f199e…`)、`results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`、`figures/README.md` fig9 節 | 3 workload とも `resolved-above-floor`、対差平均 +1,591,948.5 / +448,830.17 / −576,749.77 tps、`formal=false` / `promotion_prohibited=true`、「A-1 の値がある」とは書かない |
| mocc の観測 3 件 | `output/insights/2026-09-18/t2774-mocc-torn-read-probe/README.md`、`…/t2779-mocc-g2-observation-conditions/README.md`、`…/t2780-mocc-pilot-discriminator/README.md`、D2148 項 13、D2153 | 5 arm 鎖 2/40・3/40・2/40・0/40・0/40 (先頭 2 arm は X/P 無し)、通常 5/120・診断 0/120・backoff 2/120 (Fisher 0.0300 / 0.2231)、discriminator の finalization 到達 `no-g2`。いずれも非 certifying、根因未同定、「第 2 成功例」ではない |
| [T-2724] A-3 整合 | `output/insights/2026-09-18/t2724-t080-defer-active-v2/README.md`、D2154、entry 1683 | 層 2 の zero-hit 判定を直前の active v2 full validation へ委譲、chain / X2 / G の取り込みは別 wave |
| [T-2783] critic 診断の型付き入力接続 | `output/insights/2026-09-19/t2783-critic-input/README.md`、D2155、entry 1684 | `k2_critic_diagnosis` の exact 6 field、K2・非 B-4・reflux on 限定、3 巡目未実走 |
| B-10 fig8 | `figures/README.md` fig8 節、`output/insights/2026-09-17/t2647-b10-tail-fig8/README.md`、D2120 項 16 | 実在物 (PNG `24eab2e8…`・PDF `11071b72…` は provenance `outputs[].sha256`、provenance `3ccdb0aa…` は現物の SHA-256 を再計算)、B-10 は閉じない、再現 cohort の保留維持 |
| [T-1998] accepted 稿 | `results/2026-09-18-t1998-balanced-stock-inline-accepted.md`、entry 1669 | 単独稿、限定 20 件、未照合 10 項目の 3 区分、値と判定は不変 |
| A-6 reject 稿 | `results/2026-09-18-a6-certification-reject.md`、entry 1662 | 単独稿、限定 12 件、outer `reject` −5.7841% は不変 |

## 3. 版の作り方

- 前版 `2026-09-17.md` を起点に、冒頭・§0・§2 (g)・§9・§10 を全面差替え、他節は箇所ごとに exact 1 回一致の置換で再導出した
  (置換 123 件 + 後処理 20 件、job dir の `apply.py` / `post1.py`)。§7 は前版の後半 9 項を前半末尾へ移し (67 項)、新しく 9 項を
  足した (計 76 項)。§0 は 13 点、§2 (g) は 11 点。
- **前版由来の文の「前版」「この版で」「冒頭の訂正 N」は 1 版ずれるので付け替えが要る。** 親がレビュー起動前に 20 件、起動後に
  31 件 (job dir の写しに当てて子の完了後に反映)、レビューがさらに 8 件 + 1 件を拾った (§4)。この型は前版 wave の §10 (所見 7)
  でも出ている。
- README は 4 段の script (`readme_update.py`) で更新した: 版の履歴表の新行、「最新 = `2026-09-19.md`」、訂正一覧を「0 件」へ、
  stale 注記 3 件を 0 件へ移管 (移管先を 3 項で明記)。

## 4. 段 6 — read-only レビュー 1 本と焦点再レビュー 1 本

- **1 本目** (Codex `gpt-6-astra`、effort medium、read-only、22:34〜22:43 JST、30 model call、CLI reported tokens 385,086、
  wall 539 秒): **NO-GO**、所見 9 件 (must-fix 8・should-fix 1)。逐語は `verbatim/prompt-review.md` と `verbatim/review-out.md`。
  親が一次資料で検算した結果 **9 件すべて real、refuted 0**。最重要は (1) [T-2731] の修正を「受理集合を広げも狭めもしない」と
  書いた誤り (D2108 は「狭まる向き」を明記)、(8) [T-2774] の 5 arm を「`e9e477ca` + X/P 計装 patch」でまとめた誤り (先頭 2 arm は
  X/P 無し)、(3)(4) 前版由来の時点表現と訂正対象の版。fix は `post3.py` (22 件) + 1 箇所 (job dir の写しに当てて反映)。
- **焦点再レビュー** (同 model、22:51〜22:54 JST、12 model call、CLI reported tokens 116,563、wall 171 秒): 所見ごとの
  closed / partial / regressed 表 — **closed 6 (1・4・5・6・7・9)、partial 2 (3・8)、regressed 1 (2)**、新規 should-fix 1、NO-GO。
  逐語は `verbatim/prompt-focus.md` と `verbatim/focus-out.md`。親の裁定: 3 件とも real。(2) は §10 の完了形で、本節を書くことで
  しか閉じられない (草稿と凍結版が同一 file なので構造的に 1 巡遅れる — 版の §10 に契約として明記)。(8) は §6 の見出し文
  1 文を 5 arm 鎖の形へ直し一次資料 §5.1 の表と再照合。新規 1 は §7 コーパス駆動の項を「前版の更新 / この版の更新」へ分けた
  (`post4.py`)。**3 巡目は起動していない** (`DW-O16`: 残る 2 件は完了形と 1 文の言い換えで、親が `grep` と一次資料の表で
  裏取りして閉じた)。
- 両レビューが「未完」と自ら書いた範囲 (全 3,325 行の逐語照合、全 T / F / entry 参照の内容照合、§5〜§8 の置換箇所の意味上の
  脱落の網羅確認) は、この版でも検証済みとは扱わない。

## 5. 検査

- `python3 tools/check_docs.py`: 違反なし (README 更新後、fix 後、§10 確定後の 3 回)。
- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: rc=0、両 holdout の conjunction hit 0、陽性対照 217
  (README 更新後)。記録 commit 前に insight verbatim を含めて再走 (結果は worklog fragment)。
- 引用 path の実在確認: `output/insights/` 26 path すべて存在。`git merge-base --is-ancestor`: `0b4fbd7a6` (B-4 spec 凍結) rc=0、
  `4636181a9` (fig8) rc=0、`4bd962643` ([T-2783]) rc=0、`cc82edc8c` (chain X1') rc=1、`ad83b108b` → `fa24e6ea8` rc=1。
  現行 ccbench gitlink `511c9538`。A-2 policy `scheduler.nodes` = 1。`SATISFIABLE_CONDITION_IDS == {"C10"}`。
- verbatim 5 file は NFC、U+0300〜U+036F なし。
- 記録 commit 後の焦点走 (DW-S07): paper-story を読む test 6 file (`test_plot_b10_static_tail_formal` / `test_plot_a1_sized_paired` /
  `test_plot_a2_certification` / `test_s1_9pair_figure_provenance` / `test_check_docs` / `test_s8b_repo_scan_invariant`) を正規 runner で
  計算ノードへ dispatch し **747 passed / 4 skipped、rc=0** (23:05〜23:06 JST)。login の bounded local での 1 回目は MemoryMax 到達と、
  走行中に親が failures fragment を書いて tree digest が変わったことで rc=16 (親の手順ミス。走行中は作業ツリーに書かない) — 結果を
  捨てて tree を固定したまま再走した。
- 受入全走は記録 commit 後の最終 tip で 1 走 (結果は land の受領証。この README の作成時点では未実施)。

## 6. 工数

- codex 子 2 本 (review 1、focus 1、全段 `gpt-6-astra` / medium)。author / fix 子は 0 (実装面ゼロ)。
- 親: 前版全 10 節の読了、entry 1582〜1685 の見出しと主要 25 エントリの本文、D2104〜D2155 の見出しと 6 本の本文、A-1 単独稿全文、
  fig8 / fig9 節、mocc 3 件の insight 冒頭、path 実在確認 26 件、SHA / 祖先性の実測 8 件、`check_docs` 3 回、三軸語走査 2 回。

## 7. 言わないこと

- この版が新しい主張を足したこと (足していない)。図の再生成・results 稿の改稿 (していない)。
- 「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」「床値が発効した」「pin を前進させた」。
- 稼働中で未着地の wave の内容 (書いていない)。

## 8. 逐語の可逆最小正規化 (DW-S07)

`verbatim/` のレビュー出力 2 file は markdown の行末空白 (改行記法) を含み `git diff --check` に抵触するため、行末の空白だけを除いた
(可視文字不変)。原文 sha256 は launcher receipt (`artifacts/dev-wave-paper-story-20260919/<job>/receipt.json` の `output_sha256`) と一致する。

- `review-out.md`: 原文 sha256 `92f249f659f8c5b4e8cc77f01aa0a55ab9902ed90be4ec55e0bb22745b128793` (12266 bytes、job dir `codex/review-out.md`) → 正規化後 sha256 `9cb7c2304d5c62ca0e7c3980e851fbffd7055a4d0273b8fd722f08fa2206d216` (12153 bytes)。除去した行末空白 (行番号, 空白数): [(4, 3), (6, 3), (8, 3), (10, 3), (14, 3), (16, 3), (18, 3), (20, 3), (24, 3), (37, 3), (39, 3), (43, 3), (45, 3), (47, 3), (49, 3), (53, 3), (55, 3), (57, 3), (59, 3), (63, 3), (65, 3), (67, 3), (69, 3), (73, 3), (75, 3), (77, 3), (79, 3), (83, 3), (85, 3), (87, 3), (89, 3), (93, 3), (95, 3), (97, 3), (99, 3), (131, 2), (132, 2), (133, 2), (134, 2)]。復元法: 各行の末尾へ同数の U+0020 を戻す (可視文字は不変)。
- `focus-out.md`: 原文 sha256 `8e2b1e73f01af1914acabbba7ed1d32702aa8b1dcb9116d8c3c64704e232eb77` (5125 bytes、job dir `codex/focus-out.md`) → 正規化後 sha256 `923d63be05f0e2cf48ce437a550645e7e3f1409f1ea5ade2b703ef5663620e30` (5107 bytes)。除去した行末空白 (行番号, 空白数): [(19, 2), (20, 2), (21, 2), (32, 2), (33, 2), (34, 2), (35, 2), (36, 2), (37, 2)]。復元法: 各行の末尾へ同数の U+0020 を戻す (可視文字は不変)。
