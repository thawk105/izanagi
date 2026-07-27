# [T-128] T-080 E2E fixture の scan 膨張と、全走 wall の checkout 依存

2026-07-27 / cygnus (96 core、共有ノード。他ユーザーの負荷あり) / branch
`worktree-dev-wave-t128-t080-scan` / 統合 commit `b08ce1a`

本 wave は「全走 wall の律速 node を短縮する」という [T-128] で始まったが、**段 1 の前提実測で
その前提が覆った**。以下は一次資料である。測定はすべて本 wave で親が実走した。

## 1. 前提が覆った経緯

worklog 2026-07-27 (20) は「全走 69〜106 秒、律速は
`test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` (46〜58 秒)」と記録していた。
本 wave の baseline 実測は次のとおりで、**wall も律速 node も一致しなかった**。

| 走 | 条件 | wall | 結果 |
|---|---|---|---|
| base1 | main checkout、`-n 32` | 300.65 秒 | 3089 passed / 13 skipped |
| base2 | 同上 (再現確認) | 321.34 秒 | 1 failed / 3088 passed |

durations 上位は `test_t080_*` の 8 node (各 137〜175 秒) が占め、[T-128] が名指しした node は
49.4 / 56.2 秒で **9 位**だった。

## 2. 全走 wall は checkout に依存する (本 wave 最大の知見)

**git worktree には ignored なファイルが存在しない。** `output/s1-build-cache/` は
`.gitignore` 対象なので、main checkout には 36,158 ファイル (1.8GB) あるが、
worktree には 0 ファイルである。

- 前 wave [T-120] の 69〜106 秒は **worktree で**測った値
- 本 wave の 300 / 321 秒は **main checkout で**測った値
- 差の原因は環境でも負荷でもなく checkout の違いである

この事実は本 wave の変異検査で偶然露出した。修正前の fixture を使う M4-old が 102.89 秒で、
修正後の M4-new (103.62 秒) とほぼ同じだったため、worktree では修正前でも膨張しないと分かった。

**帰結: 全走 wall を比較するときは、どの checkout で測ったかを必ず併記しなければならない。**
worktree での wall は、ignored な生成物が効く経路については系統的に楽観的である。

## 3. 律速の内訳 (probe による実測、いずれも main checkout を source とする)

使い捨て probe を 7 本使った (job tmp、tracked file は非改変)。

- fixture 構築 1 回 = **121.72 秒**。うち子 python プロセスが 115.21 秒、
  `output` の copytree が 3.14 秒、`git add -A` が 3.01 秒
- 子 python の段階内訳: `draft_receipt` 27.51 / `validate_draft` 27.32 /
  `finalize_receipt` 36.00 / `verify_receipt` 8.64 / `gate_check` 17.88 秒
- **git 呼び出しではない**: `draft_receipt` の 30.02 秒のうち subprocess は 1.72 秒
  ([T-117] の「git 呼び出し過多」型ではない)
- cProfile: `s8b_holdout_freeze.search_repository` → `_scan_one` →
  `re.Pattern.search` が **443,514 回で 22.926 秒** (1 回あたり約 52 マイクロ秒)
- 列挙 17,119 件のうち 14,608 件、scan 対象テキスト 16,423 件のうち 13,920 件が
  `output/s1-build-cache/` 由来

根: **fixture repo には実 repo の `.gitignore` が入らない**。fixture は実 repo の `output/` を
丸ごと複製してから `git add -A` するので、実 repo では ignored な生成物まで tracked になり、
production の `search_repository` の scan 対象に入っていた。build cache は campaign を
回すほど育つため、放置すれば全走は単調に悪化する。

## 4. 修正と、交絡のない効果測定

修正は `orchestrator/tests/test_s8b_oracle_driver.py` の 1 ファイル (production 0 byte)。
`output` の複製を「実 repo の Git が可視とみなす regular file」に限定し、可視判定は
production の `enumerate_repository_files` と同じ規則 (tracked は mode 100644/100755 のみ、
untracked は `--exclude-standard` の regular 非 symlink) にした。`.gitignore` を書き写さず
Git 自身に問うのは、判定を二重管理しないため。可視集合を process 内へ memo しないのは、
untracked の増減を隠して fixture が本番より狭くなるのを防ぐため。

効果は **同一 source (main checkout) に対して**測った。worktree で測ると 2 の理由で差が出ない。

| 指標 | 修正前 | 修正後 |
|---|---|---|
| fixture 構築 1 回 (receipt 発行あり) | 121.72 秒 | **22.13 秒** |
| 列挙 | 17,119 件 | **2,507 件** |
| scan 対象テキスト | 16,423 件 | **2,499 件** |
| うち build cache 由来 | 13,920 件 | **0 件** |

fixture の docstring が言う「1 回 15〜22 秒」に戻った。

## 5. 受理集合は変わらない (実測)

除外の前後で `search_repository` の report が完全一致した。

- 陽性対照の hit 件数: 55 (両方)
- holdout 2 件の conjunction hit: いずれも 0 件 (両方)
- 軸別 hit: 読み書き比 0 / 偏り 115 / read-modify-write 100 (両方)

つまり **除外した 13,920 件のテキストに、holdout 三軸のどの軸の hit も 1 件も無かった**。
陽性対照の供給元は `output/` ではなく required 集合として明示コピーされる path なので、
今回の filter では落ちない。

## 6. 敵対レビュー (codex `gpt-5.6-sol`, reasoning=high、read-only)

5 本回した。段 3 相当 2 本 (A: 検出力と受理集合 / B: 診断の妥当性と取りこぼし)、
段 6 の 2 本 (C: control の検出力 / D: 実装の正しさと作法)、段 6 の焦点再レビュー 1 本 (E)。

| # | 所見 | 出所 | 裁定 | 対応 |
|---|---|---|---|---|
| 1 | 列挙集合の乖離を独立に検出する assert がない | A・B 一致 | real | control テスト新設 |
| 2 | process 内 memo が後発の可視 file を落とす | A・B 一致 | real | memo 廃止 |
| 3 | tracked mode / symlink 判定が本番と不一致 | A・B 一致 | real | 本番と同じ mode filter |
| 4 | 親の「全走 300 秒の主因」は過大表現。妥当な予測は約 210 秒 | B | **real** | 記録を「critical tail を約 90 秒押し上げる原因」に是正 |
| 5 | 本番に 1 発行 13 scan・1 file 9 regex の重複 (固有 regex は 5 本で足りる) | B | real | scope 外 → [T-122] へ合流 |
| 6 | 他に同型の「実 repo 丸ごと複製 + `add -A`」は無い (copytree は tests 11 箇所・本番 0) | B | real | 対処不要 |
| 7 | **control が実コピー経路を通らず、祖先集合を壊す変異が生存する** | C・D 一致 | real | fix 1 |
| 8 | 欠落・型変更した tracked path を fixture が黙って落とす (本番は拒否する) | D | real | fix 2 |
| 9 | ambient Git 設定で本番側だけ偽赤になりうる / `assert` 依存の fail-closed / stderr 消失 / 理由コメント欠落 | C・D | real (nit) | すべて採用 |

段 6 の C・D は**いずれも NO-GO** を返し、fix 後の焦点再レビュー E が 6 所見すべて closed と
判定して GO とした。E の新規所見は nit 1 件 (symlink 非対応環境で control が構築段階で落ちうる)
のみで、この repo の既存テストにも無条件 symlink fixture が多数あるため must-fix にしていない。

**所見 4 は親自身の一般化に対する指摘である。** `DW-S03` が「親の実測値とその一般化も
明示的にレンズへ入れる」と定めており、その契約が実際に機能した例として記録する。

## 7. 変異検査 (統合 commit 後に本走、`DW-O19`)

harness は行の完全一致 anchor・一意性検査・内容比較による復元・flock 単一走行を持つ
(F40 の教訓を測定用ハーネスにも適用した)。

| 変異 | 内容 | 判定 | 観測 node |
|---|---|---|---|
| M1 | 可視判定の mode 絞り込みを外す (広い方向) | KILLED | control 1 件のみ |
| M2 | untracked non-ignored の収集を落とす (狭い方向) | KILLED | control 1 件のみ |
| M3 | ignore callback の祖先ディレクトリ合成を落とす | KILLED | control 1 件のみ |
| M4-new | 本番 gate (holdout hit の拒否) を壊す・修正後 fixture | KILLED | 該当 defect node 1 件のみ |
| M4-old | 同じ本番変異・**変更前 HEAD の fixture** | KILLED | 該当 defect node 1 件のみ |

M4 の新旧両走が `DW-M08` の要求に対応する。**scan corpus を 6.6 倍縮めても、既存 gate が
検出する node と理由は変わらない**ことの実証である。M1〜M3 は新 control だけが検出する差分で、
広い方向・狭い方向・祖先経路の 3 方向を押さえている。

## 8. 残る課題

- 修正後の全走 wall (main checkout) は、local main へ取り込んだ後に測る。worktree で測っても
  2 の理由で修正前と差が出ないため、取り込み前には確定できない
- 次の律速候補は `test_slow_oracle_prepared_cell_pipeline_uses_real_build_v2` (実 build を
  2 回通す node)。これは元々の [T-128] scope であり、新 ID で引き継ぐ
- base2 で 1 件だけ出た `test_dev_waves_integration.py` の flake は本 wave の変更と無関係で、
  負荷ピーク (load average 17) 時に出た。受入全走で再現を見る
