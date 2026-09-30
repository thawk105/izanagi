# [T-2273] [T-2560] 共有 base builder の可視 output 複製元を session 局所の写しへ — 隣接対 3 対の実受入で land 条件を満たさず、実装は land しない (2026-09-26)

wave `dev-wave-t2273-shard0-local-copy`。実装 branch `worktree-t2273-shard0-local-copy` (tip `5c51e958e` = 実装 `eb65d322f` + main `620a6bb13` の取り込み、**local main へは入れない**)、記録 branch `record-t2273-shard0-local-copy`。
依頼の逐語は `verbatim/T-2273-origin.md`、段 1 brief・段 4 / 6 裁定・Codex 子の prompt と出力は `verbatim/`、走ごとの集計は `analysis/`、変異は `mutation/`、infra 分類は `runs/`。

## 結論 (最初に読む)

1. **事前登録の land 条件 (段 4 裁定「計測の事前登録」5): 満たさない。** 有効 3 対の shard-0 W_0 の対差は +19.111 / +19.679 / −4.341 秒、対率は 5.2 % / 5.7 % / −1.2 %。「3 対すべて Δ > 0」と「対率中央値 ≥ 10 %」の両方を外した (対差中央値 19.111 秒、対率中央値 5.2 %)。**性能改善としては land しない。** D357 の 1 走比較としても 3 対とも 10 % 未満 = 「変化なし」。
2. **5 分目標 (別判定): 未達。** B の W_max 3 走の中央値 348.387 秒 > 300 秒。
3. **第 4 回診断の −123.9 秒は再現しなかった。** 診断の対照 X は写しを計測前に用意 (staging 43.9 秒は別欄) していたのに対し、本実装は session で最初に builder に入った worker が Lustre から写しを 1 回作り、他の builder はその完成を flock で待つ。診断の結論 3 (複製は CPU でなく待ちが支配、self CPU/壁 0.11) と段 3 の反例 (T-2786 §4、5 本同時の copy は 30〜35 秒) を合わせると、**「同時 8 本の複製」を「直列 1 本の複製 + 待ち」に置き換えても、その 1 本の Lustre 複製の所要が依存 builder の構築時間に残る**ことと整合する。実受入には builder 内の計器が無く、写し生成 1 回の所要は**測っていない** (段 4 裁定 A3 で計器追加は scope 外とした)。原因は断定しない。
4. **正しさの側は閉じている。** 全件性の検査 2 か所 (D2044 項 15) と複製関数本体は 1 byte も変えず、写しは実関数を実 repo に 1 回呼んで作る。新規正例 1 本と既存実 builder 検査への観測 assert 1 つで、事前登録の変異 M1〜M5 が全件 KILLED (期待 node と完全一致、P0 SURVIVED、基準走 PASSED)。焦点走 (変更 test file 全体 + inventory 4 群) は 716 passed / 9 skipped。
5. **次の一手の候補 (設計択一、未実装):** (a) 写しを builder より前 (collection 中、pre ≈ 64 秒の窓) に作る = 診断の対照 X の形に近い。過去の依頼で「未実測の prewarm は先行実装しない」とされた型なので、効果の見込みを先に測る必要がある。(b) 律速を発行 subprocess (診断 X で依存 builder の 79.4 秒、CPU 支配、内訳未測定) へ移す。(c) 本実装を「改善なし・悪化なし」の中立な整理として land する — 事前登録は性能改善としての land だけを定めていたので、これは新しい裁定になる。どれもユーザー裁定の対象として worklog に置く。

## 1. 依頼と不変条件

依頼 (逐語 `verbatim/T-2273-origin.md`): 受入 shard-0 の律速 (t080 共有 base の builder による Lustre の output/ 可視集合の複製) を、複製元を計算ノード局所の写しに差し替えて解く。写しを作る時期・担い手・未 commit の可視 file の扱いを設計し、D2068 の却下 3 案に触れず、全件性の検査 2 か所を維持し、Codex author で実装し、隣接対の実受入で効果を測ってから land する。性能主張は同時刻の対照で。規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。

守ったこと: `_copy_git_visible_output`・`_git_visible_output_paths`・全件性検査 2 か所 (`test_t080_output_copy_visibility_matches_production_enumeration` 内) は不変。複製される集合・object store・index は不変 (D2068 の whitelist / alternates / 独立 index に当たらない)。gate・台帳・一般化は足していない。

## 2. 実装 (branch に保存、land しない)

`orchestrator/tests/test_s8b_oracle_driver.py` の 1 file、+100 / −2 (Codex author、子 branch `author-t2273lc-impl` の `48c441a0f` を所有 path 限定 patch で `eb65d322f` へ統合)。

- **担い手・時期:** `_T080SharedBases.copy_visible_output(source_root, destination)`。xdist session の共有置き場 (`tempfile.gettempdir()` = 計算ノードの /tmp) の下に source_root ごとの写しを、flock 下で**最初に来た builder が 1 回だけ**作る (完成 marker `ready.json` を pending → rename、marker の無い残骸は消して作り直す、`get()` と同型)。完成後は lock を離して `shutil.copytree` (copy2) で各 builder の root/output へ複製する。
- **未 commit の可視 file:** 写しは作業木から実関数で作るので、modified tracked / untracked の可視 file は現行と同じく含まれる。違いは読む時点が builder ごと → session で 1 回になる点だけ (docstring に明記、段 4 裁定 A1)。
- **session 間の再利用はしない** (最後の worker が共有置き場ごと消す)。xdist session の無い単独走は従来の直接複製。
- builder (`_build_t080_stub_free_e2e_repo`) は共有 session 下なら `copy_visible_output(ROOT, root / "output")`、そうでなければ従来どおり。
- test: 新規 `test_t080_shared_base_visible_output_uses_one_snapshot` (小さい git repo と test 局所の bases、実関数の呼出し 1 回・写し後の変更が届かない・直接複製と集合 / bytes / mtime が一致)。既存 `test_t080_shared_base_builds_real_builder_once_across_processes` に「写しメソッドの呼出し回数 == builder の呼出し回数」を追加。既存の期待値は不変。

## 3. 段 2〜6

- 段 2 plan (`verbatim/s2-plan-*`)、段 3 相談 2 本 (レンズ A 正しさ・整合、レンズ B 過剰・削除と計測設計、どちらも修正後 GO)。段 4 裁定 (`verbatim/s4-ruling.md`): A2 / B1 (builder の複製元を観測する正例) と A6 / B5 (測ってから land、land 条件の事前登録) を採用。A1 (snapshot で拒否経路が消えうる) は「意味の差として real、受理集合の変化としては refuted」とし gate を足さず docstring で明記。
- 段 6 レビュー 2 本 (`verbatim/s6-review-*`): A1 / B1 = B の新規 node 1 件で probe の collection 完全一致が全対を無効にする → 事前登録を erratum E1 (A/B 差 = 新規 1 件ちょうど、共通 node の 3 shard 割付は完全一致) で訂正し probe を Codex fix。A2 = M5 の kill 理由の書き方 → E2 で訂正 (実関数呼出し 0 回)。焦点再レビュー 1 本は修正後 GO (`verbatim/s6-focus-1-out.md`)。
- E1 の前提確認 (系列投入前、2026-09-23 21:02:44 JST): A / B 両 tree の login collect-only (3 shard) で、shard-0 は A 4,325 / B 4,326 件 (差 = 新規 1 件)、shard-1 (10,247)・shard-2 (13,162) は完全一致。

## 4. 変異 (`mutation/`)

独立 clone (D1009) の固定 commit `5c51e958e`、`tools/mutation_worktree.py --runner-mode dispatch`。期待 node は login の pytest が hook で拒否されるため、初回 dispatch probe (全件 SURVIVED 期待) で観測し、final で登録した。spec は builder 系 (P0・M1、2 node) と新規 test 系 (P0・M2〜M5、新規 test 1 node) に分けた (M2 を実 builder に通すと ignored を含む output/ 全体を複製しうるため)。

| ID | 変異 | 最初に落ちた assert (probe の本文) | final |
|---|---|---|---|
| P0 | docstring 1 語 | — | SURVIVED |
| M1 | builder が共有時も実 repo から直接複製 | 写しメソッド 0 回 ≠ builder 1 回 (`test_t080_shared_base_builds_real_builder_once_across_processes`) | KILLED |
| M2 | 写しでなく source の output から複製 | 2 回目の複製に写し生成後の変更 bytes (新規 test) | KILLED |
| M3 | 完成 marker を書かない | 実関数の呼出し 2 回 (新規 test) | KILLED |
| M4 | 写し → destination を `copy_function=shutil.copy` | mtime 不一致 (新規 test) | KILLED |
| M5 | 実関数の代わりに全件 copytree で写しを作る | 実関数の呼出し 0 回 (新規 test、erratum E2) | KILLED |

1 回目の probe 投入は spec の外側 timeout 1,800 秒が dispatch の待機契約 (queue 3,600 + 猶予 600 秒) より短く harness が起動前に rc=2 で止めた (未実行)。4,500 秒に直して再投入した。

## 5. 隣接対の実受入

測定形 (段 4 事前登録 + E1): A = `620a6bb13` (測定開始時の local main、clean worktree `t2273lc-base-a`)、B = `5c51e958e` (A + 実装 1 file、wave 木)。`IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` の直接投入、順序 A,B / B,A / A,B、門番 = 他 session の受入 leader ≤ 1 ∧ load1 ≤ 60。温めは両 tree で collect-only を 1 回 (2026-09-23)。集計器 `t2273lc_ab_analyze.py` (Codex author、逐語 `verbatim/probe-source.md`)。測定中に自分の他 job は走らせていない。

**投入 10 走、うち infra 由来の失敗 3 走、有効 3 対。** 条件別の失敗件数: A 2 (01-A、02-A)、B 1 (04-B)。

| 走 | 条件 | 投入 → 完了 (JST) | 結果 | 分類 |
|---|---|---|---|---|
| 01-A | A | 09-23 23:35 → 23:51 | rc=16 | infra: shard-2 の job 21564 が queue 待ち上限超過 (child 未起動)、shard-0・1 の hold を 09-26 に qstat 不在確認後に解除 |
| 02-A | A | 09-26 10:12 → 10:19 | rc=16 | infra: shard-0 の worker が早期 memo 待ち (`real_repo_receipt_memo`、上限 120 秒) を超過、no tests ran |
| 03-A | A | 09-26 10:21 → 10:31 | 完走 (W_0 427.783) | 対 1 の相方 04-B が失敗したため対から外れた |
| 04-B | B | 09-26 10:31 → 10:44 | rc=16 | infra: shard-2 が collection 完了時の早期 memo 待ちを超過 (test 実行前、本実装の経路外)。hold の 2 job は 10:59 に終端を確認して解除 |
| 05-A / 06-B | 対 1 | 11:00 → 11:40 | 有効 | |
| 07-B / 08-A | 対 2 | 11:41 → 12:20 | 有効 | |
| 09-A / 10-B | 対 3 | 12:20 → 12:59 | 有効 | |

時刻は `series.log` の launch と rc の行。memo 待ち超過は 2026-09-22 以降の受入 66 session のうち本 wave の 2 走だけで、条件 (A/B) によらず 09-26 午前に集中した。

| 対 | W_0 A | W_0 B | Δ = A − B | r | O_max A / B | L A / B | 依存 builder を待つ node (`delegated…[missing]`) A / B |
|---|---:|---:|---:|---:|---|---|---|
| 1 (05-A / 06-B) | 367.498 | 348.387 | +19.111 | 5.2 % | 292.981 / 272.250 | 270.133 / 251.443 | 259.108 / 239.874 |
| 2 (08-A / 07-B) | 344.833 | 325.154 | +19.679 | 5.7 % | 270.367 / 250.699 | 252.920 / 250.698 | 241.566 / (最大占有 worker に現れず) |
| 3 (09-A / 10-B) | 353.559 | 357.900 | −4.341 | −1.2 % | 278.627 / 283.506 | 261.753 / 264.877 | 249.973 / 253.788 |

- 対差の中央値 19.111 秒、対率の中央値 5.2 %、条件別中央値 A 353.559 / B 348.387 (差 5.172 秒、3 つは別量)。
- 有効 6 走とも最遅 shard は shard-0 (W_max = W_0)。pre は 64.3〜65.9 秒、post 10.03〜10.07 秒で条件差は見えない。L の node は全走 `test_t080_failed_launch_preserves_receipt_refusal` (gw40)。
- 第 4 回診断の走 (R1 / A2 の W_0 429.4〜454.6、pre 128.8〜130.2) とは pre が約 2 倍違い、絶対値を比べない。

## 6. 計算量

事前に示した見積り約 2.2 node 時間 (対を infra で取り直すごとに +0.5) にユーザーが「3 対で投入」と回答 (2026-09-23)。実績: 受入系列 29 shard job の Elapse 合計 8,333 秒 = 2.31 node 時間 (失敗走を含む)、焦点走 1 回 303 秒。変異 (probe 2 系列 + final 2 系列) は harness の外側所要の合計 4,557 秒、温め 2 回は外側 13 分で、どちらも queue 待ちを含む上限 (job Elapse は受領証に途中値しか残らず未集計)。記録の受入 1 回が別に加わる。

## 7. 限界・言わないこと

- 3 対は同一 node・同一 allocation ではない (固定 2 tree の隣接逐次投入)。3/3 の不一致も有意差判定ではない。
- 写し生成 1 回の所要、依存 builder の内訳は実受入に計器が無く測っていない。結論 3 は整合の指摘で、原因の同定ではない。
- 早期 memo 待ちの超過の原因 (計算ノード・Lustre・他 job) は分解していない。
- B の shard-0 は新規 test 1 件を余分に含む (E1)。その JUnit time は B の有効 3 走で 0.014 / 0.014 / 0.027 秒。

## 8. この dir の中身

`verbatim/` 依頼・brief・段 4 / 6 裁定・Codex 子の prompt と出力・開始 gate・probe 逐語 (`probe-source.md`)、`analysis/analysis.md` 走表と対表 (集計器の出力そのまま)、`analysis/analysis-compact.json` 集計 JSON の要約 (全文 48MB は job dir)、`runs/` infra 分類 3 件・投入台帳・計測 tip、`mutation/` final の spec と結果。job dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-local-copy/` (repo 外)。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が実装の保存先として名指す branch `worktree-t2273-shard0-local-copy` (tip `5c51e958e`、実装 `eb65d322f`) は、D2242 決定 1 の「残す」を改める新しい決定の下で 2026-09-30 の掃除 wave が削除する。branch 束 bundle `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/backup/branches.bundle` から復元できる。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
