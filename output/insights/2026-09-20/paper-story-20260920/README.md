# 論文ストーリー 2026-09-20 版の全項目再導出 — wave 記録

`docs/paper-story/2026-09-20.md` を、2026-09-20 時点の正典全体から全項目再導出して追加した wave の
記録である。**新規計測はしていない。** 既存の版 9 本・`results/` 13 稿・`figures/`・`claim-evidence/`・
`docs/paper-story-backoff/` は 1 byte も変えていない。

- wave: `dev-wave-paper-story-20260920`、branch `worktree-dev-wave-paper-story-2026-09-20`、背景 job dbedeb61
- 起点: local main `b7f970dfa` (2026-09-20 07:04 JST、worklog entry 1711 までの fold を含む)。段 7 で local main `efb0dee78`
  (entry 1712 = [T-2789] の docs、`docs/paper-story/` に差分なし) を ff-only で取り込んでから README を更新した。
  **導出の起点は `b7f970dfa`。**
- 成果物: `docs/paper-story/2026-09-20.md` (新規、3,866 行) と `docs/paper-story/README.md` の 4 節の更新
  (版の履歴表へ 1 行、「最新 = `2026-09-20.md`」、訂正一覧を「1 件」へ、stale 注記 11 件を本文へ移管して 0 件へ)。実装面ゼロ。
- 依頼: 「論文ストーリー 2026-09-20 版を、着手直前の local main の着地済み正典全体から全項目再導出する (docs のみ)。前版
  `2026-09-19.md` (base `a99425b66`) 以後の着地 = 検証相 (entry 1702、D2160)・B-7 fixed5 三 workload (1705、D2162)・B-4 床値 w1
  完走 (1693)・mocc wave 2 (1701、D2159)・軽量 witness 4 arm (1696)・B-10 cohort 2 (1690、D2157)・K2 3 巡目 (1691)・B-5 事前登録
  v1 (1692)・T-2786 (1703) と、README の stale 注記全件。裁定待ち (T-2792 / T-2795 / T-2797 / T-2766) は未解決として書く。最初に
  `grep -n "前版\|この版"` を全走して版名へ置き換える。README は受入の owned-path に入れず、stale 注記の畳み込みは英語稿 wave の
  行が main に入った後に行う (競合は fail-closed)。段 6 は独立 read-only レビュー 1 本 + 焦点再レビュー (D2148 項 11)。規律 2 を
  緩めない。新規計測・gate・台帳の追加は scope 外」。**全項目の再導出であり、一項目の差分改訂ではない。**

## 1. 段 1 — brief と provisional 裁定

- 軽量版 (`DW-C00`): 段 2・3 を省き、段 5 は親の docs 編集、段 6 は read-only review 1 本 + 焦点再レビュー 1 本、変異 matrix は
  実装面ゼロで免除、受入は記録 commit 後の tip で 1 走。brief の逐語は `verbatim/brief-s1.md`。
- **(P1) 反映集合:** 依頼の 9 事実と README の stale 注記 11 件 (上記 9 + A-1 attempt-0002 の gate 拒否 D2156・chain land 2 度目の
  不成立・A-2 nodes=5 整合) を本文の該当節へ入れ、それ以外の着地 (軸 1 の後継記録 [T-2035]、意味 witness 登録簿 15 → 17 [T-2153]、
  SS2PL 非 inert [T-2737]、A-2 nodes=5 の policy 実装 [T-2489]、T-2778 / T-2790 / T-2766 の運用改善、テスト・コードの棚卸し) は
  §6 / §8 の状態語を変えるものだけ状態語の訂正として反映し、運用素材は §2 (e) / §5 に置いた。新しい主張は足していない。
- **(P2) 前版の執筆時点の誤り:** 親の導出中は 0 件 (A-2 policy の `nodes` が前版起点で 1、chain X1' が当時も今も main に無いことを
  実測)。**段 6 レビューが 1 件 (前版 §3 項目 3 の見出し「仮説層は未実装」) を見つけ、(P2) は覆った** (§4)。
- **(P3) B-8 の仕分け:** 検証相 (D2160) は対象 (採用候補 2 genome、S-1 の最終候補ではない)・種 (数値 seed 未記録)・長さ (extime 3 s)
  が要件と違うので B-8 は未取得のまま、§8 exact claim (正しさ) の注記と B-8 に「関連する追加検証」として併記。
- **(P4) B-7 fixed5 の置き場:** certification 経路を descriptive に使った別 study instance として §2 (f) の第 5 と B-7 の材料に置き、
  正式 protocol の判定にも要件充足 (D2044 項 3 維持) にも数えず、§9 の 4 文は変えない。
- 英語稿 wave はユーザーが 2026-09-20 07:08 JST に却下していた (memory `single-paper-no-english-drafts-now`) ので、依頼の
  「英語稿 wave の行が main に入った後」は空条件として扱い、README の畳み込みは段 7 で当時の local main を取り込んでから当てた。
- 裁定 inbox の再走査: `2026-09-19-k2-loop-round3-same-job-stock-control.md` (2026-09-20 00:03 JST) は entry 1691 の insight が持つ
  裁定パッケージ ([T-2795]) と同内容で、版には「裁定待ち」として書いた。稼働中で未着地の wave (fig10 / fig8b / chain land 3 度目など
  peer 13 session) の内容は書いていない。

## 2. 依頼が挙げた 9 事実と stale 注記の一次資料と実測値

| 事実 | 一次資料 | 版に書いた状態語 |
|---|---|---|
| 採用候補 2 genome の検証相 (D2160) | `docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md`、`output/insights/2026-09-20/verify-phase-adopted-backoff/README.md`、D2160 | fixed-5 `678b7203…` (= T-1998 v1) / fixed-10 `16c29935…`、校正 10868〜10873 → extime 3 s、本走 11268〜11279、判定集合 30 = 24 + 6 で anomaly 0、pass ×2、未完走 2 件 / 候補 (SIGKILL / hard timeout 3600 s) は verdict なし、本走実消費 6316 / 6134 S、S-1 (iv 付属) の準用であって充足ではない、B-8 の取得ではない、既存 certified 記録は昇格も降格もしない、S-1 追記は凍結束縛で繰延べ |
| B-7 fixed5 三 workload (D2162) | `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`、`output/insights/2026-09-19_t1998-b7-fixed5-three-workload/certification.json` | attempt `b7f5-20260919a`、request 10807〜10809、source `c18a80967`、effects `+0.6789675418265144` / `+0.12671651401806727` / `−0.11378696258180376`、床値 0.9536 / 0.7250 / 0.2228%、rr95 だけ床値超の退行、outer `reject` (論理積)、6 cell certified、要件充足は判定しない (D2044 項 3)、既存材料とプールしない |
| B-10 第 2 cohort (D2157) | `docs/paper-story/results/2026-09-19-b10-static-tail-cohort2.md`、`output/insights/2026-09-19/b10-tail-cohort2/README.md` | 事前登録追記 `8737cacb4` (22:01 JST)、attempt 1 (10743〜10745) は rc=2 で測定なし、attempt 2 = group `b10-backoff-grid-20260919T131526Z-2235286` (10752〜10754)、`not-observed-in-any-workload`、18 区間 `declining`、120 記録 certified、合成しない、fig8 は cohort 1 のみ、限定 16 |
| A-1 attempt-0002 (D2156) | `output/insights/2026-09-19/a1-sized-attempt2/README.md` §1・§7、D2156 | 1 attempt 認可 → 投入前照合 21 項目成立 → submit 22:05:30〜36 JST rc 2 (`_assert_no_prior_v3_bench_start`、`abff80d1b`) → 副作用なし、測定値なし、次の投入には改めて認可が要る (項 3)、択 1〜3 は [T-2792] 裁定待ち |
| B-4 床値 w1 (entry 1693) | `output/insights/2026-09-19/t2288-floor-pair-w1/README.md` | H `2ba400087`、10711 / 10712 / 10713、3 窓 complete (124 / 124、62 / 62、drop 0)、所要 4178 / 4141 / 4602 秒、8 変数 6 / 1 / 1、signal は trap の観測記録なし、窓 JSONL untracked、集約・採用・§5 記入は未、ablation 実施不可 |
| K2 3 巡目 (entry 1691) | `output/insights/2026-09-19/k2-loop-round3/README.md` | 診断経路 D2155 初実走、coder-4 `value=10`、job `10761.nqsv` (69 秒) certified・anomalies 0、815,983 tps (CV 0.16%)、`continue`、critic-3 帰属不能 3 巡連続、同 job stock 対照未達 ([T-2795] 裁定待ち)、非同時刻 3 走で改善を読まない |
| 軽量 witness 4 arm (entry 1696) | `output/insights/2026-09-19/mocc-witlight-arm-run/README.md` | W `5b02546f` (branch `izanagi-t1943-mocc-g2-witlight`、上流未公開)、on 0/60・0/60、off 1/60・1/60、Fisher 0.500、検出力 0.105、discriminator 未発火、TRACE=1 観測専用、観測 4 件目 (非 certifying) |
| mocc wave 2 (D2159) | `output/insights/2026-09-19/t2773-mocc-template-wave2/README.md`、D2159 | template 接続、30 check all_pass (`11161.nqsv`、352 秒)、OFF = stock identity `6454d9f3…` / ON-B `41f52341…`、12 走 certified、n=1 A1' / A2' reject・B' pass、16/16 KILLED、探索・pin 前進・軸採用は未解禁、binary 同一は主張しない |
| B-5 事前登録 v1 (D2158) | `docs/b5-generator-contrast-preregistration.md`、`output/insights/2026-09-19/b5-generator-contrast-prereg/README.md` | B = 10 / A = 30、候補集合 1..1000 µs、1,773 論理 session、未発効、本走・生成器実装は未認可 ([T-2797] 裁定待ち) |
| T-2786 (entry 1703) | `output/insights/2026-09-19/t2786-base-decomposition-recovery/README.md` | A 395.7 / L 709.4 / P 405.4 秒、L は 3/3 悪化、P 変化なし、計器欠陥 2 件 (F649 再発) を修正してから測定、採用候補なし (運用素材) |
| chain land 2 度目 (entry 1688) | `output/insights/2026-09-19/t2724-chain-land-2/README.md` | 三軸走査 hit 4/4 (設計どおり)、焦点走 8 file 1,211 passed / 0 failed、受入赤 1 node (`test_b10_freeze_tree_bytes_match_the_wave_local_gate`、digest `c405c742…` → `6a4ee1ef…`)、保存 branch `t2724-chain-land-2-saved` (`0a799da6c`)、A-4 は未発効のまま |
| A-2 nodes=5 (entry 1686) | `output/insights/2026-09-19/t2489-a2-nodes5-local-lock/README.md` | policy `nodes: 5` (A-2 / A-6 / B-7 の 3 policy)、node-local lock 候補は不採用 (`9137.nqsv`)、新 attempt なし |

## 3. 版の作り方

- 前版 `2026-09-19.md` を複製し、**最初に「前版」→「2026-09-17 版」(160 件)、「この版」→「前版」(155 件)、「本版」→「前版」(2 件)
  の機械置換を当てた** (job dir `map1.py`)。これで前版由来の文の時点語が 1 版ずれる型 (F1 再発) を構造的に避け、残る構造語・工程語
  (節見出し、「この節は前版から引き写していない」、「前版で再確認」など) は親の自己点検で 9 件 + 空白抜け 9 件を付け替えた
  (`r18.py` / `r19.py` / `r20.py`)。
- 冒頭・§0・§2 (g)・§9 冒頭・§10 を全面差替え (`sec-head.md` / `sec-g.md` / `sec-10-draft.md`)、他節は箇所ごとに exact 1 回一致の
  置換 (`r1.py`〜`r17.py`、fail-closed の applier、計 約 150 件) で再導出した。§7 は前版の後半 9 項を前半末尾へ移し (76 項)、
  この版で 11 項を足した (計 87 項)。§0 は 13 点、§2 (g) は 14 点、§2 (e) の運用素材はこの版で 7 つ。
- README は段 7 で `readme_update.py` (4 段、exact 一致・fail-closed) で更新した。

## 4. 段 6 — read-only レビュー 1 本と焦点再レビュー 1 本

- **1 本目** (Codex `gpt-6-astra`、effort medium、read-only、07:58:59〜08:08:11 JST、32 model call、wall 550 秒): **NO-GO**、所見 3 件
  (must-fix 2・nit 1)。逐語は `verbatim/prompt-review.md` と `verbatim/review-out.md`。親が一次資料で検算した結果 **3 件すべて real、
  refuted 0**。(1) A-1 の「再投入・再認可は未判定」という前版由来の旧文が attempt-0002 の 1 attempt 認可 (D2156) と矛盾 → 「充足・
  formal 化は未判定 / attempt-0002 は認可されたが gate で停止 / 次の投入には改めて認可が要る ([T-2792] 裁定待ち)」へ 7 箇所を分けた。
  (2) **前版 §3 項目 3 の見出し「仮説層は未実装」は前版の執筆時点で既に偽** — D2143 (2026-09-18) は前版の起点 `a99425b66` に含まれ、
  前版の本文自身は「K2 2 巡目で初適用」と書いていた (2026-09-17 版から付け替えられずに残った見出し)。冒頭の訂正 1 として一覧へ移し、
  §1・§3 の「1 巡分」を「2 巡分」へ、§0 の括弧書き・§7・§10 段 1 (P2 は覆った) を改めた。(3) §0 の「4 種類」→「5 種類」。fix は
  `r21.py` (置換 17 件)。
- **焦点再レビュー** (同 model、08:14:02〜08:17:29 JST、13 model call、wall 206 秒): 所見ごとの closed / partial / regressed 表 —
  **closed 3 / partial 0 / regressed 0**、新規所見 3 (should-fix 1 = §10 の焦点再レビュー完了の先取り 1 文、nit 2 = 「8 箇所」→ 7・
  「前版は第 2 cohort の地位に触れなかった」の言い換え)、**GO**。逐語は `verbatim/prompt-focus.md` と `verbatim/focus-out.md`。
  親の裁定: 3 件とも real。should-fix は §10 の焦点小節を書くことで閉じ (草稿と凍結版が同一 file なので構造的に 1 巡遅れる型の
  4 度目)、nit 2 件は `r22.py` (置換 3 件)。**3 巡目は起動していない** (`DW-O16`)。
- 両レビューが「未完」と自ら書いた範囲 (全 3,866 行の逐語照合、全 T / F / entry 参照の内容照合) は、この版でも検証済みとは扱わない。
- 親の手順: レビュー子が worktree を読んでいる間、親は worktree の docs に触れず、fix は job dir の script として作り、子の完了後に
  worktree へ当てた。

## 5. 検査

- `python3 tools/check_docs.py`: 違反なし (草稿完成時、fix 後、README 更新後)。
- 三軸語走査 `python3 -m orchestrator.campaign.s8b_holdout_freeze search`: 草稿完成時 rc=0 (両 holdout の conjunction hit 0)。
  記録 commit 前に insight verbatim を含めて再走 (結果は worklog fragment と commit message)。
- 引用 path の実在確認 (`check_paths.py`): 161 件、不在 3 = g1 候補 2 file (保存 branch 上で main に無いと本文が明記) と図 stem 1。
  D 番号 211 件・F 番号 15 件の見出し実在 (`check_refs.py`)。`git diff --check` 0、NFC、U+0300〜U+036F なし。
- 祖先性の実測: `cc82edc8c` (X1')・`4d8fb93b7` (X2)・`0eabe67ba` (T-2766 impl)・`229982652` (G) は HEAD の祖先でない (rc=1)、
  `0b4fbd7a6` (B-4 spec 凍結)・`8737cacb4` (B-10 追記)・`c18a80967` (B-7 実装)・`abff80d1b` (A-1 gate) は祖先 (rc=0)。
  現行 ccbench gitlink `511c9538`。A-2 / A-6 / B-7 policy の `scheduler.nodes` = 5 (前版起点 `a99425b66` では A-2 が 1 = 前版の記述どおり)。
  `SATISFIABLE_CONDITION_IDS == {"C10"}`。
- 記録 commit 後の焦点走 (`DW-S07`): paper-story を読む test 6 file を計算ノードへ dispatch (結果は worklog fragment)。
- 受入全走は記録 commit 後の最終 tip で 1 走 (結果は land の受領証。この README の作成時点では未実施)。

## 6. 工数

- codex 子 2 本 (review 1、focus 1、全段 `gpt-6-astra` / medium)。author / fix 子は 0 (実装面ゼロ)。
- 親: 前版全 10 節の読了 (3,325 行)、entry 1686〜1711 の本文 26 件、D2156〜D2164 の本文、results 稿 3 本の該当節、insight 13 本の冒頭、
  path 実在確認 161 件、SHA / 祖先性の実測 9 件、`check_docs` 3 回、三軸語走査 2 回。

## 7. 言わないこと

- この版が新しい主張を足したこと (足していない)。図の再生成・results 稿の改稿 (していない)。
- 「A-1 の値がある」「B-10 を閉じた」「再現されたので飽和しない」「mocc は第 2 成功例」「床値が発効した」「B-7 を充足した」
  「B-8 を取得した」「全走 anomaly ゼロ」「信頼度 1−εⁿ」「pin を前進させた」「K2 で改善した」。
- 稼働中で未着地の wave の内容 (書いていない)。裁定待ち 4 件の採否 (先取りしていない)。

## 8. 逐語の可逆最小正規化 (DW-S07)

`verbatim/` のレビュー出力 2 file は markdown の行末空白 (改行記法) を含み `git diff --check` に抵触するため、行末の空白だけを
除いた (可視文字不変)。原文 sha256 は launcher receipt (`artifacts/dev-wave-paper-story-20260920/<job>/receipt.json` の
`output_sha256`) と一致する。他 3 file (brief・prompt 2 本) は行末空白が無く bytes 不変。

- `review-out.md`: 原文 sha256 `107728f3119a158f9455c402d3a07506c888748fe9e100dce1a46b850da4c197` (11,634 bytes) → 正規化後
  `950d9eca4273543a` で始まる sha256 (11,619 bytes)。除去した行末空白 (行番号, 空白数): [(7, 2), (16, 2), (17, 2), (18, 2), (92, 2),
  (93, 2), (94, 2), (95, 2)]。復元法: 各行の末尾へ同数の U+0020 を戻す (可視文字は不変)。
- `focus-out.md`: 原文 sha256 `48ccd8e6dcc4439578102fc07d5d06a0e0b7d916cd8b60fe0008e1cd589da792` (5,332 bytes) → 正規化後
  `3e828826b9b3105d` で始まる sha256 (5,313 bytes)。除去した行末空白: [(13, 2), (14, 2), (17, 2), (18, 2), (21, 2), (22, 2), (43, 2),
  (44, 2), (45, 2), (46, 2)]。復元法: 同上。
- 全 file の sha256・bytes・除去位置の JSON は job dir `verbatim-normalization.json`。
