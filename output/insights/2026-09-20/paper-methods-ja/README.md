# 本体論文 (日本語) 方法節と実装対応メモの再導出 (2026-09-20 版) — wave 記録

- wave: `worktree-dev-wave-paper-methods-ja-2026-09-20` (背景 job 898e8185、job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-2026-09-20/`)
- 起点 local main: `fec4a8187` (2026-09-20 18:05 JST に fresh worktree、開始 gate `check_wave_startup.py --mode fresh` rc=0、main 乖離 0)。
  段 6 review の後 (18:39 JST) に、peer 通知を契機に読み直した local main `482f19b88` ([T-2304] pin 前進の着地) を自 commit 0 の状態で
  `--ff-only` で取り込み、submodule を `e9e477ca` へ揃え、pin に触れる記述を再照合した (§6)
- 成果物: [`methods.md`](methods.md) (方法節草稿、6 節) と [`implementation.md`](implementation.md) (実装対応メモ。対応表 19 行 +
  09-10 以後の機構 15 行 + 読み分け 13 行)。行数は凍結時の bytes で数える (焦点再レビュー時点で 237 / 162 行)。
  **実装面の差分 0** (docs-only、新規 dir 1 つ)。前稿 `output/insights/2026-09-10/paper-methods-ja/` (entry 1430) は 1 byte も変えていない。
- 依頼の逐語 (dev-wave 引数): 「本体論文 (日本語) の方法節と実装対応メモを再導出する (docs-only、軽量版 DW-C00、台帳 ID 未起票の
  新規執筆依頼)。前稿 `output/insights/2026-09-10/paper-methods-ja/{methods,implementation}.md` (entry 1430) は 09-10 以後の手順 (A-1 sized
  policy v3 と 1 attempt 認可の投入経路、A-2 / A-6 certification の receipt 束縛、B-10 静的右 tail・待ち方 grid の事前登録と driver、
  採用候補 2 genome の検証相、K2 手動 loop の型付き critic 診断 D2155、mocc の trace-hook と witness、床値 pair protocol v3) を反映して
  いない。着手直前の local main から fresh worktree。入力 = 論文ストーリー最新版 §2 第 3 幕・§5・§8、該当 docs (事前登録・runbook・
  該当 D)、現行実装 (`orchestrator/campaign/`、`orchestrator/verifier/`)。成果物 = `output/insights/<日付>/paper-methods-ja/{methods,implementation}.md`
  (前稿は上書きしない)。実装済みの機構と各実験で実際に使った機構を区別し、certified の意味 (指定した検証構成と判定器の意味論に
  照らした受理) を story §6 に揃える。英訳・新規実験は scope 外。仮想リスク向けの gate・検査・台帳の追加は scope 外。」

## 0. この wave が主張すること・しないこと

- 主張する: 2 本の稿が local main `fec4a8187` の実装と、指定した一次資料 (story 2026-09-20 版 §2 第 3 幕・§5・§6・§8、該当 D、
  該当 worklog entry、該当 insight README) に対応していること。「実装済み」と「使用」の区別が実装対応メモの表に機械可読な粒度
  (関数名・entry 番号・attempt id・request id) で書かれていること。
- しない: 新しい測定・合成・判定。既存の certified 記録・事前登録・凍結物・story・README の変更。英訳。gate・検査・台帳の追加。
  方法節への性能値・図の転載 (前稿の裁定を継承)。

## 1. 段 1 brief (親、18:08 JST。逐語は `verbatim/s1-brief.md` = handoff の段 1 節 12 行。レビュー子へ渡した job dir の `brief-s1.md` には同じ 12 行の後に段 5 の進捗 6 行が続く)

- 研究前進: 完了判定 = (1) 09-10 以後の 7 機構が「実装済み」と「使用」を区別して書かれ、(2) certified の意味が story §6 と一致し、
  (3) 段 6 read-only review が GO。
- scope: docs-only、新規 file = 本 dir の 3 file。段 2・3 省略 (設計択一なし・正しさ防壁に触れない・受理集合不変)、段 6 は D2148 項 11
  により read-only review 1 本 (2 レンズを 1 本で担う)。
- (P1) 前稿の 6 節構成を保つ。(P2) 「現行実装」の基準は `fec4a8187`。story 2026-09-20 版 (main `b7f970dfa` 基準) 以後の着地は
  「実装済み・story 未反映」と明記し、稼働中の兄弟 wave の結果は数えない。
- 条件再評価: DW-O08 / O09 / O10 = 非該当 (新規 path。`paper-methods-ja` と `insights/2026-09-20/` の pin・目録は test に不在を grep で
  確認)、O13 = 非該当、O11 = 削除なし。

## 2. 稿の作り方

1. 入力の読み込み: story 2026-09-20 版の §2 第 3 幕 (行 607〜1325)・§5・§6・§8 (exact claim、A 群、B 群、C-1) を全文読んだ。
   09-10 以後の該当 worklog entry を見出し検索で特定し、本文を読んだ: 1636 / 1687 / 1736 (A-1)、1702 (検証相)、1705 (同一候補
   3 workload)、1684 / 1691 / 1746 (K2)、1666 / 1701 / 1696 (mocc)、1639 / 1661 / 1693 (床値 pair)、1690 / 1737 (B-10)、1744 / 1745
   (verifier 容量・意味 witness)、1742 (凍結 v2 g1 の発効)。該当 D は見出し検索で本文を読んだ (D2155、D2172、D2174 項 3、D2178、D2181、
   D2183 ほか)。
2. 実装アンカーの照合: 前稿の対応表の全関数を `grep -n "^def \|^class "` で現行 main に確認した (全件存続)。新機構は module の
   関数一覧・定数・policy JSON の field・docstring から拾った。
3. 執筆: methods.md は前稿の 6 節構成を保ち、各節へ新機構を足した (§1 = certified の定義と Silo 固定解除、§2 = K2 型付き診断と
   stock 対照口と identity の限界、§3 = 検証相・verifier 容量・fan-out・mocc trace-hook / witness、§4 = 条件関門・床値 pair protocol v3、
   §5 = certification の受領証束縛と outer status・A-1 の lane と gate と認可 record、§6 = B-10 事前登録 2 本・B-5 / B-8 事前登録 v1・
   機序仮説層 v3)。implementation.md は前稿の対応表を再照合した行と、09-10 以後の機構の「実装済み / 使用 / 未使用」表、読み分け表、
   境界節を持つ。
4. 親の自己点検 (段 6 前): 稿が引く worklog entry 19 件と D 番号の見出し実在 (親の grep は 3〜4 桁だけを拾い 36 件、レビューが
   D52 を含めて 37 件と数え直した。fix 後は D1257・D1408 が加わり 39 種、entry 19 種 = 焦点再レビューの数え直し)、repo 内 path の
   実在、hex 4 件の現物照合、`tools/check_docs.py` rc=0、`git status` が新規 dir 1 つだけ。

## 3. 前稿から変えた点 (一次資料で確かめたもの)

| 前稿の記述 | 新稿 | 根拠 |
|---|---|---|
| critic の拒否還流 3 関数 (`load_rejections` 等) を `p3_s4_loop.py` に帰属 | 所在は `orchestrator/critic/digest.py` | `grep -rn "def load_rejections"` |
| 層3 の `mechanism_hypotheses` は「空の予約区画で未実装」 | 機序仮説層 v3 は K2 2 巡目で初適用、critic 帰属記録の決定論射影 (`_mechanism_view`) | D2143、`layer3_report.py` |
| certified の定義 (指定された検証構成と判定器の意味論に照らした受理) | 同じ定義に「build された bytes についての判定で、要求構成の build を含意しない」「性能の判定ではない」を足した | story 2026-09-20 版 §6 |
| Silo 1 protocol に限る (暗黙) | Silo 固定は D2114 で解除、mocc は段階 A の機械実証まで (探索未解禁) | D2114、D2159 |
| B-4 の限界記述 (writer は create-only、report の 4 分類は未実効、launcher は単一 arm) | 「記述統計限定、適格な赤 precursor 0 件、`design_not_feasible`」と床値 pair w1 の位置づけへ置き換え | D2016、[T-2632]、entry 1693 |

## 4. 親が一次資料で確かめて直した点 (執筆中)

- verify fan-out: policy 3 本の `scheduler.nodes` は 5 だが、A-2 / A-6 の取得済み attempt は 1 node で走った (story §2 (e) 項 5、entry 1686)。
  同一候補 3 workload 測定は 5 node。
- 検証相は条件関門を通していない (insight `verify-phase-adopted-backoff/README.md` に関門の記録なし、identity は `resolve_evidence` の束縛)。
- certification の outer status の判定順は `collect_results` の分岐順 (anomaly → source reject → indeterminate → performance-indeterminate →
  effects 不足 → 全正 → reject)。
- K2 の両 role 組立ては `k2_next_generation_inputs` (`p3_s4_loop.py`)。
- 凍結 v2 g1 は entry 1742 (D2180) で承認 A と active pointer X が着地し発効済み。story 2026-09-20 版の「未発効」はこの時点で古い。
  official 経路の launch validation の既存不整合 2 件は未達のまま。

## 5. 段 6 独立レビュー (read-only、1 本、2 レンズ) と親の対応

- 起動: 18:27 JST、`tools/dev_wave_codex.py --stage review --sandbox read-only`、`gpt-6-astra` / `medium` (docs 権威)、job-id `review-1`、
  model_calls 33、`outcome=accepted` / `stop_reason=completed`、`check_codex_output.py` rc=0。prompt の逐語は `verbatim/s6-review-prompt.md`、
  出力の逐語は `verbatim/s6-review.md` (原本 21,431 bytes、sha256 `191ab63ac5070d12…`。行末空白 2 行を除く可逆最小正規化後 21,427 bytes、
  sha256 `06d91182f04ace5d…`。可視文字不変、原本は job dir `codex/review-out.md`)。
- 結果: **NO-GO、must-fix 4 / should-fix 3 / refuted 2 (レビュー自身が親の記述を支持した懸念)**。全件 real と裁定し反映した。

| # | 所見 | 裁定 | 対応 |
|---|---|---|---|
| 1 | K2 の stock 対照を「無 backoff」と誤記 (実装は `BACK_OFF=1, BACKOFF_FIXED=-1` の内蔵適応 backoff、D2183) | real / must-fix | methods §2 を「CCBench 内蔵の適応 backoff … 対照は無 backoff ではない」へ |
| 2 | admission record (成果物に残る) と、参照先の supply / meaning record 本体 (残らない) の取り違え | real / must-fix | methods §4 と implementation の A-2 行を「admission record と `record_ids` は残り、元 record の本体は残らない」へ。現物 `condition-gate-rr5.admissions.jsonl` で確認 |
| 3 | 前稿の B-4 実装限界 3 点 (writer create-only、report §7.1 の 4 分類未実効、launcher 単一 arm) と正式選択への接続未完を根拠なく削除 | real / must-fix | implementation 境界節と methods §6 へ復記。現行 code (`p3_b4_raw_record_producer.py` の `O_EXCL`、`p3_b4_material_report.py` の `section_7_1_four_classifications_operationalized: False`、`p3_b4_launcher.py` の `--arm`) で存続を確認 |
| 4 | MoCC の pin 前進を「未解禁」と書いた (D2150 項 1 で承認済み) | real / must-fix | 「探索・正式な軸採用は未解禁、pin 前進は承認済み」へ。その後 [T-2304] の着地を取り込み「実施済み」まで更新 (§6) |
| 5 | B-10 report の実行日 (2026-09-05) と記録・D1678 の裁定日 (2026-09-07) の混同 | real / should-fix | implementation の B-10 grid 行を「実行 2026-09-05、記録と裁定 2026-09-07」へ (`t1905-b10-report/README.md` §0 で確認) |
| 6 | 「使用欄に無い機能は走っていない」は全称が強すぎる (nodes=5 probe `t2489-20260918a` が fan-out を実走) | real / should-fix | 冒頭を「未掲載だけを未使用の根拠とせず、未投入・未使用は各行に明記」へ。A-2 行に probe の注記 |
| 7 | 限定 (ii) (correctness 側の実 argv は独立に記録されず、workload の束縛は campaign lock と pipeline constructor) が未明示 | real / should-fix | methods §5 と読み分け表の cell certified 行へ追記 (`certification.json` の `workload_argv_observation` 4 cell で確認) |
| 8 | g1 を「未発効」へ戻す必要はない | refuted (現文維持) | 変更なし |
| 9 | 検証相を packed verifier の使用実績へ数えていない | refuted (現文維持) | 変更なし |

- レビューが一致を確認した範囲 (逐語 §「照合して一致を確認した範囲」): certification の取得済み bytes 3 attempt、検証相の判定集合 24 + 6、
  A-1 の 3 分類と lane、K2 3 巡目、mocc の 4 arm と wave 2、床値 pair w1、B-10 cohort 2、B-7 と g1 の状態語、D 37 種・entry 19 種の実在、
  path 48 件の実在、行番号参照なし、`git status` が新規 dir 1 つだけ。

## 6. pin 前進 ([T-2304]) の取り込み (review 後)

- 18:30 JST に peer session (`ccbench pin advancement t-2304`) から「main が `482f19b88` へ進み pin が `e9e477ca` へ前進、land は turn registry の
  dead ticket で当面 rc=27」の通知。通知は local main 再読の契機にだけ使い、`git show main:orchestrator/campaign/pin.py` (`e9e477c`)・
  main 上の fragment `docs/spool/worklog/2026-09-20-dev-wave-t2304-pin-advance-1.md`・`output/insights/2026-09-20/t2304-pin-advance/README.md`
  §1・§4 で実測した。
- review-1 の完了後に `git merge --ff-only main` (自 commit 0、`fec4a8187` → `482f19b88`)、`dev_wave_submodule_init.py` rc=0、submodule
  `e9e477ca`。稿の pin に触れる記述を再照合して直した: 基準 SHA、methods §1 (前進の実施と「探索の解禁を含まない」)、§2 (pin が動かす
  identity の層と動かさない層、旧系列は固定 checkout から走る)、§3 (X / P 計装は pin の tree に無く patch で当てる。G2 witness
  (`IZANAGI_MOCC_G2_WITNESS`) は `e9e477ca` の `#if TRACE` 内に含まれ、軽量 witness は hook branch)、implementation の MoCC 2 行と
  「story 未反映の着地」(新 main で fail-closed になる経路 = `p3_s4_loop.py` の独立 full OID `511c9538`、`resolve_current_floor_protocol()`)。
- 現物で確かめた点: submodule (pin `e9e477ca`) の `cc/mocc/transaction.cc` に witness の環境変数 `getenv` 参照 3 箇所 (有効化 1、出力先 2。
  親の初回 grep は marker 文字列の行を含めて 4 行と数えた)、`patches/instr-mocc-lock-coverage.patch`
  は同 file への 66 行の追加 hunk、`p3_s4_loop.py` の `PIN = "511c9538…"` と `assert_pinned_clean(fixed_sub, PIN)`、`axis_mocc_temperature.py` の
  `PIN = pin.CURRENT_PIN` / `PROOF_PIN = e9e477ca…`。

## 7. 段 6 焦点再レビュー (read-only、1 本) と親の対応

- 起動: 18:46 JST、`--stage focus`、job-id `focus-1`、model_calls 11、`outcome=accepted` / `stop_reason=completed`、`check_codex_output.py` rc=0。
  prompt は `verbatim/s6-focus-prompt.md`、出力は `verbatim/s6-focus.md` (8,753 bytes、sha256 `1fadb73aa6e243c1…`、行末空白なし = 原本と同一 bytes)。
- 対応表: 所見 1〜7 は **closed 7 / partial 0 / regressed 0**、8・9 は refuted 維持で現文が保たれていることを確認。pin 前進の反映 9 項目は
  すべて「一致」(基準 SHA、§1 の実施と非解禁、§2 の identity の層、旧系列の固定 checkout、§3 の X / P 計装と G2 witness、witness 2 種の区別、
  implementation の MoCC 2 行、fail-closed 経路、探索解禁への昇格なし)。
- 判定: **GO** (新規 must-fix なし)。nit 2 件を親が直した — (1) implementation の「正本の優先関係」と機構表見出しの旧基準 `fec4a8187` を
  `482f19b88` へ、温度述語行の「探索用 `PIN` 不変」を「参照式 `PIN = pin.CURRENT_PIN` は不変、指す commit は前進に追随」へ (起草時の基準を
  記す冒頭の括弧書きはそのまま)。(2) 本 README の行数表記を凍結時の値へ、witness の環境変数参照を `getenv` 3 箇所へ、D 番号の件数を
  「修正後 39 種 (D1257・D1408 が加わった)、entry 19 種」へ。
- 焦点再レビューが数え直した現稿の件数: D 39 種、entry 19 種、implementation の表 19 / 15 / 13 行、methods 6 節。
