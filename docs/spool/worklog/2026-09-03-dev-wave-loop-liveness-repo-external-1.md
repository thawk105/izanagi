---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-loop-liveness-repo-external
seq: 1
title: [新規] ループが止まる 3 実体を分離し、git 管理外への束縛 4 file を内容単位 guard で閉じた — 受入 5 分問題は解決せず律速を特定した (コード + docs + insight、branch worktree-dev-wave-loop-liveness-repo-external、変異 8/8 KILLED)
---

## 本文

- **ユーザー依頼:** 受入全走は 5 分以内でないと困る。いずれ進化探索ループも開発ループも回らなくなる。
  そのリスクを分析し、可能であれば解決してほしい。最近ホームディレクトリ下の古い AI セッションログを
  掃除したら全ての dev-wave がコケ続けた。git 管理外のファイルに izanagi のテストが依存していたのは衝撃的だった。
- **「回らなくなる」には 3 つの実体があり、性質が違う。** (1) テスト自体の所要 — 最悪の走で 297.5 秒 =
  **4.96 分**で既に 5 分の線に触れている。(2) 計算ノードのキュー待ち。(3) git 管理外ファイルへの依存。
  **本 wave が実装で閉じたのは (3) だけで、(1) は解決しない。** 詳細は
  `output/insights/2026-09-03_loop-liveness-repo-external/`。
- **(1) は段 9 の実走で確定した。最遅 shard-0 は 388.3 秒 = 6.47 分で、上限を 29% 超えている**
  (20135 passed / 92 skipped / 赤 0、`verdict=child-green`)。
- **親は律速を 2 度誤った。** duration ledger から「最長単体 140.0 秒が完全詰め 83.0 秒を上回るので
  並列度では下がらない」と論じたが、実測では shard-0 の最長単体は 153.1 秒、完全詰めは 130.1 秒で
  差は 23 秒しかなく、wall 388.3 秒との差 235 秒を説明できない。**支配的なのは file 単位の束縛**で、
  shard-0 の仕事量の 58% が `test_s8b_oracle_driver` (1881.4 秒) と
  `test_s8b_floor_campaign` (1764.9 秒) の 2 file に集中し、最長 3 件はすべて前者の中にある。
  さらに親は「[T-1933] が攻めたのは別 file」と書いたが、**攻めたのはまさにこの file だった。**
  ledger の値 (140.0 秒) と実測 (82.3 秒) も食い違っており、**hint を構造的結論の根拠にしたのが誤りである。**
- **(3) の全数は 5 file・3 root で、正しく防護されていたのは 1 file だけだった。**
  親は最初 `git grep` を `/home/` と `expanduser` に絞ったため `/work/` 配下の 2 系統を取り逃し、
  段 2 のプラン子と段 3 のレンズ B が独立に同じ 2 件を発見した。取り逃した 2 件は論文図
  `fig2c_b10_extended_backoff` の provenance を 22 file の sha256 で検証しており、外部 root が
  剪定されれば 2026-09-01 と同じく全 wave の受入が同時に落ちる。
- **字句走査は gate として成立しない。** `orchestrator/tests/*.py` の絶対 path らしき literal は
  1796 件あり、実在判定と system prefix 除外まで掛けて初めて 3 root へ絞れる。
  さらに `output_snapshot_ignores.py:91-111` は `git rev-parse --git-path info/exclude` と
  `git config --get core.excludesFile` の返り値を読むので、**どんな字句走査でも原理的に見つからない。**
  親が現物を確認したところ現在の寄与は 0 件で、危険なのは削除ではなく `output/` 始まりの規則の追加である。
- **登録簿と全走査メタ gate は作らなかった。** 段 3 の両レンズが独立に D335 違反と判定し、
  親も `O(file 数)` と実測した。決定的な先例として、既存の repo 全体走査
  `test_campaign_import_invariant.py` はまさにこの理由で恒久保留されている。
  `DW-G03` の独立 2 例も、レンズ B が git 履歴で dev-wave-jobs 系 2 file は同一作者・同日、
  B-10 系 2 file は同一 commit と示したため成立しなかった。局所修復に留めた。
- **既存の次の一手 [T-2242] の効果見積りは反証した。** 費用の 76% は `ast.parse` で `ast.walk` は 21%。
  prefilter を `ast.walk` の前に置く設計で取れるのは 0.629 秒であり、旧見積りの 2.7 秒は取れる量ではない。
  正しい置き場所は `ast.parse` の前で、そこへ置くと 1.718 秒 → 0.285 秒 (83.4% 削減) になる。
- **prefilter は生 source ではなく NFKC 正規化後に掛ける必要がある。** 段 3 のレンズ A が
  `layout.ｅxploration_campaign_layout(x)` (全角 e) の反例を出し、親が現物で検算した。
  Python は識別子を NFKC 正規化するので、生 source の判定は AST 発見の必要条件を満たさず、
  D872 決定 1 が禁じる「族から外す条件」になる。設計判断は {{D:lexical-prefilter-must-normalise-nfkc}}。
- **親の前提が 2 つ破れた。** brief の `(P3)` (字句 marker は必要条件) と `(P2)` (`DW-G03` の独立 2 例)。
  どちらも段 3 が破り、段 4 の裁定で取り込んだ。
- **親の手順違反が 4 件あった。** 焦点走と実装子の同時投入、provenance 監査と変異 harness の同時投入
  (いずれも `DW-O26`)、中断走の `.done` を退避せず再投入 (`DW-O01`)、変異走行中の repo 編集 (`DW-M05`)。
  4 件とも既存契約が明示していた内容の適用漏れで、いずれも機構が fail-closed で止めたため
  誤った緑は出ていない。損失は時間だけである。失敗は
  {{F:lexical-prefilter-breaks-on-nfkc}}、{{F:external-binding-census-missed-work-prefix}}、
  {{F:concurrent-dispatch-starves-implementer}}、{{F:naive-parametrise-would-delete-the-check}}、
  {{F:stale-done-marker-fakes-completion}}、{{F:parent-edited-repo-during-mutation-run}}。
- **計算ノードの混雑がこの wave の全工程を律速した。** 焦点走はキュー待ち 35 分に対し実行 51.2 秒。
  同時刻に実行中 0 本・待ち 10 本を観測した。**5 分上限は単走の所要としてだけでなく、
  ノード占有が列の回転率を決める量としても読むべきである。**
- 設計判断は {{D:external-input-guard-by-content}}、{{D:lexical-prefilter-must-normalise-nfkc}}、
  {{D:external-binding-census-stays-manual}}。

## 次の一手差分

### 完了

- [T-2242] 効果見積りを実測で反証し、正しい置き場所 (`ast.parse` の前、NFKC 正規化後) で実装した。
  remaining: none
  base: e6872c4fff27d75b8a7c1ac09446cb3502c1822e97a9fb8d1ac5bd8966baca44

### 新規

- {{T:acceptance-shard0-heavy-file-redistribution}} **P1・新規**: 受入全走の最遅 shard を 5 分以内へ入れる。
  段 9 の実走 (20135 passed / 92 skipped / 赤 0) で最遅 shard-0 は **388.3 秒 = 6.47 分**、上限を 29% 超えた。
  律速は最長単体 node ではない (最長 153.1 秒、48 worker 完全詰め 130.1 秒、差は 23 秒)。
  shard-0 の仕事量 6243.4 秒のうち `test_s8b_oracle_driver` が 1881.4 秒、
  `test_s8b_floor_campaign` が 1764.9 秒で **2 file が 58% を占め**、最長 3 件
  (153.1 / 148.6 / 145.0 秒) はすべて前者の中にある。`tools/acceptance_shards.py` の割付は
  file 単位なので分割されない。**3 度目を試みる前に、なぜ 145〜153 秒かかるのかを先に測る**
  (build か直列性検査か外部 command か)。[T-1933] が同 file へ cache 共有と grouping で 2 度失敗している。
- {{T:external-binding-census-gate-ruling}} **P2・新規**: repo 外束縛の全数走査 gate を新設してよいかの
  ユーザー裁定。字句 prefilter 付きで 345 file 中 16 file を parse し 0.610 秒、collection ではなく
  1 走 1 回なので 48 worker x 3 shard には掛からない。ただし構造は `O(file 数)` で、
  既存の同型テストは D335 により恒久保留されている。与えないなら全数性は今後も人手の走査に依存する。
- {{T:dynamic-git-ignore-binding}} **P2・新規**: `orchestrator/tests/output_snapshot_ignores.py:91-111` の
  動的 git ignore 依存。`git rev-parse --git-path info/exclude` と `core.excludesFile` の返り値を読むため
  字句走査では検出できない。現在の寄与は 0 件だが、`output/` 始まりで `**` を含まない規則を
  追加すると output snapshot 比較が静かに変わる。consumer は `test_s8b_oracle_driver.py`、
  `test_s8b_floor_campaign.py`、`test_real_repo_serialization.py`。
- {{T:campaign-modules-without-test-coverage}} **P3・新規**: `orchestrator/campaign/` の 186 module のうち
  `p2_5.py`、`s6_amendment_20260713_fence.py`、`s6_proposal_rounds_power.py` の 3 本が
  test suite から一度も名指しされていない。本 wave の prefilter 導入前は
  `test_p3_exploration_namespace.py` の 187 file 全 parse がこれらを parse する唯一の実行体だった。
- {{T:campaign-driver-discovery-slope}} **P3・新規**: prefilter 後も `_discover_campaign_drivers` は
  全 glob と `read_text` を行うので `O(total source bytes)` の傾きが残る。条件付き線形外挿では
  約 1,280 file (現在 187) で prefilter 後の費用が現在の prefilter 前へ戻る。構造ごと消すには
  発見結果の固定か `_DRIVER_CONTRACTS` の単一正本化が要るが、どちらも D872 決定 1 と衝突する。
