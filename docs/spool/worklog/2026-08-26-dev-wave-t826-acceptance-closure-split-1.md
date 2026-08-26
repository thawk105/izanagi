---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t826-acceptance-closure-split
seq: 1
title: 受入全走の shard 数を受入経路で 3 にし pytest wall を 43.6% 縮めた — 主目標は 7 時間前に別 wave が land 済みだった (コード + docs、branch worktree-dev-wave-t826-acceptance-closure-split、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「受入全走の高速化。計算ジョブの待ち時間は考慮しなくてよい。並列化・ボトルネック改善・
  分散ジョブ化を進める」。queue 待ちを目標から外す点は 2026-08-23 のユーザー裁定と同じ扱い。
- **親 brief の主目標は、wave 開始の 7 時間前に別 wave が land 済みだった。** 親は
  「`real-repo` 排他鎖 222.68 秒の細分化」を scope 1 に置いたが、段 2 の plan 子が
  「現行コードは既に大半の直列化を外している」と指摘し、親が `git log -S` で裏取りしたところ
  当日 13:19 の commit で実装済みだった。親が引用した 222.68 秒は**その commit の前**の tip の
  計測値で、`git merge-base --is-ancestor` で祖先関係を確認した。段 1 の前提実測に
  「main の直近 commit を機構名で引く」手順が無かったことが原因である。
- **親は現 tip で 2 走を取り直した。** 実装差分ゼロのまま `IZANAGI_ACCEPTANCE_SHARDS` だけを
  2 と 3 に切り替え、受入ではなく計測として投入した。D713 の 4 層で記録する。

  | 層 | K=2 | K=3 |
  |---|---|---|
  | pytest wall (最遅 shard) | 285.52 秒 | 160.92 秒 |
  | 最遅 worker | 211.99 秒 | 101.70 秒 |
  | 当該 shard の `W/48` | 203.9 秒 | 94.7 秒 |
  | 残差 (wall − 最遅 worker) | 73.53 秒 | 59.22 秒 |
  | 直列総仕事量 (全 shard) | 16609.9 秒 | 10830.1 秒 |
  | 結果 | 1 failed (非帰属) / 17390 passed | 17391 passed |

- **K=2 → K=3 で 124.60 秒 (43.6%) 縮む。** D1019 の走間ばらつき実績 32.27 秒の 3.9 倍で、
  ノイズでは説明できない。**直列総仕事量そのものも 1.53 倍縮んだ** — worker 数は
  どちらも 48 で同じなので、node あたり総負荷の低下による競合の減少である。
- **K=3 で既に単体テストの床に達している。** 最長単体は K=2 で 165.17 秒
  (`test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications`)、
  K=3 で 100.32 秒 (`test_s8b_oracle_driver.py` の t080 系)。K=3 の wall は
  最長単体 + 残差 でほぼ説明できる。重い単体は 3 file に集中しており、K=2 走の file 別合計は
  `test_s8b_floor_campaign.py` 1926.1 秒、`test_s8b_oracle_driver.py` 1738.7 秒、
  `test_t126_pegasus_tools.py` 1107.9 秒だった。上位 15 node で総和の 12.8%。
- **既定値は変えられなかった。** 既定 K は `tools/run_tests.py` の 1 行だが、D838 (ユーザー裁定)
  が受入の実行器を tested main の blob へ束縛しており、当該 file を直す wave は受入を通せない。
  実際 D838 以降その file は 1 度も変更されていない。**代わりに D724 が残した明示指定の経路を
  受入経路だけで使う**設計にした。設計判断は {{D:acceptance-shard-three}}。
- **親の live 実測が「機構が一度も発火しない」実装を捕まえた。** 段 5 の実装は
  `from orchestrator.campaign import site_policy` を関数内で行っていたが、
  `python3 tools/dev_wave_wait.py` という実際の起動形では `sys.path[0]` が `<repo>/tools` になり
  cwd が入らないため `ModuleNotFoundError` になる。親が同じ `sys.path` を再現して
  `_acceptance_launcher_environment()` を直接呼び、戻り値が `None` であることを確かめた。
  **追加テスト 5 本はいずれも `site_policy` を monkeypatch しており、pytest では repo root が
  `sys.path` にあるため production の解決経路を 1 度も通らず偽緑だった。**
- **段 6 の 2 レンズは独立に同じ最重所見を返した。** 「明示 K=3 は login admission の配置判定を
  迂回するので、queue が使えないとき従来ローカル実行できた受入が rc=16 で終端する」。
  実装子自身が `qstat -Q preflight rc=1` を実際に踏んでいた。fix で
  `queue_state.dispatch_possible()` が `ENA=ENA` かつ `STS=ACT` を観測したときだけ注入する形にし、
  観測不能・例外・契約外の戻り値では注入しない (run_tests は可用側へ倒すが本注入は逆へ倒す)。
- **レンズが指摘した偽緑 2 件は変異で裏が取れた。** 修正前は `m02` (定数を `"3"` から `"2"` へ)
  も `m09` (repo root の `sys.path` 追加を消す) も検出できなかった。修正後は m02 を 4 node、
  m09 を 1 node が殺す。m09 を殺すのは fix で足した「script 実行と同じ `sys.path` を持つ
  subprocess を起動する」検査 1 本だけで、他 8 本は素通りする。
- **段 3 の 2 レンズは scope 外の real 所見を出した。** `real-repo` の排他閉包は今も閉じておらず、
  (i) `test_t810_coordinator.py` が無 lock で linked-worktree registry を読み前 wave で実際に
  偽赤 (rc=1) を起こした、(ii) 登録外の session fixture 2 本が実親 repo の object database へ
  候補 commit を書く、(iii) lock key が Git common-dir でなく worktree root の realpath から
  導かれる、の 3 点を file:line で示した。**本 wave では実装せず裁定パッケージへ送る。**
  閉包が確定していない排他を差し替えないという D358 の原則は、この点については今も成立する。
- **親 brief の provisional 裁定 6 件のうち 5 件が refuted だった。** 段 2 plan と段 3 の 2 レンズが
  独立に同じ向きで反証し、親は全件を受け入れた。特に「残差は K で縮まない固定費」は
  実測で 73.53 → 59.22 秒と動き、一次資料自身が「定数として扱ってはならない」と書いていた。
- codex 子の工数: 6 本 (plan 1 / consult 2 / author 1 / review 2 / fix 1)。いずれも
  `gpt-5.6-sol` / `reasoning=xhigh`、rc=0、`check_codex_output.py` rc=0。
- 一次資料は `output/insights/2026-08-26_t826-acceptance-shard-k3/`。

## 次の一手差分

### 更新

- [T-1589] **P3・更新**: 負荷に応じて K を動的に選ぶ案。**2026-08-26 の実測で「K を増やす方向は
  当面効かない」は失効した。** 排他鎖の細分化後に測ると K=2 → K=3 で pytest wall が
  285.52 → 160.92 秒 (43.6% 減) になり、直列総仕事量も 1.53 倍縮む。ただし K=3 で
  最長単体テスト (100.32 秒) + 残差 (59.22 秒) の床に達しており、K の受理値も `{1,2,3}` に
  閉じている。**動的 K を作る前に、単体テストの短縮と固定費の削減が先である。**
  base: b567824f1101ce629b32fae18e0759924d6e1dc43c9d80416c049a5a6de80bd3

### 新規

- {{T:acceptance-default-shards-three}} **P1・新規・ユーザー裁定待ち**: 受入の既定 shard 数を
  2 から 3 へ上げるか。実測で 43.6% 短縮。実装は `tools/run_tests.py` の 1 行だが、
  D838 (ユーザー裁定) により当該 file を直す wave は受入を通せない。本 wave は受入経路だけで
  同じ効果を得る回避策を入れたので、焦点走とその他の経路は K=2 のままである。
  どう land させるか (D838 の例外を作るか、別の権威経路を用意するか) はユーザー判断が要る。
- {{T:acceptance-longest-test}} **P1・新規**: 受入の床を決めている最長単体テストを短くする。
  K=3 到達後の wall 160.92 秒は最長単体 100.32 秒 + 残差 59.22 秒でほぼ説明できる。
  重い node は `test_s8b_oracle_driver.py` の t080 系と `test_s8b_floor_campaign.py` に集中し、
  K=2 走の上位 15 node で総和の 12.8% を占める。**規律 2 により削除・skip・selection の縮小は
  対象外**で、同じ受理集合を保ったまま速くする道だけを採る。
- {{T:acceptance-fixed-cost}} **P2・新規**: 受入の残差 (wall − 最遅 worker) を削る。
  K=2 で 73.53 秒、K=3 で 59.22 秒。K を上げても縮まないため、K=3 到達後は wall の 36.8% を
  占める。内訳 (collection、worker 起動、prewarm、finalization) を分けて測るところから。
- {{T:dev-wave-docs-budget-full}} **P2・新規・ユーザー裁定待ち**: dev-wave reference の byte 予算に
  余白がゼロで、実測した手順の穴を 1 行も書けない。本 wave は 4 件を候補にしたが、
  L1.5 の footprint が 9566 byte 予算に対し 9705 byte になり、2 行の追記すら通らなかった。
  候補は (i) 引用する計測値がその機構を変えた commit より前でないか機構名の `git log -S` で
  確かめる (本 wave の主目標が 7 時間前に land 済みだった)、(ii) 受入の実行器と launcher は
  tested main の blob 束縛で変更した wave は受入を通せない (D838)、(iii) 変異 harness は
  untracked file も拒否し spec/out を checkout 内に置けない、(iv) `dev_wave_codex.py` の
  path 引数は絶対 path 必須で `--dry-run` も job-id directory を作る。
  **予算値の変更は自己改善の範囲外**と契約が定めるので裁定へ送る。

- {{T:real-repo-closure-not-closed}} **P1・新規**: `real-repo` 排他閉包の残る穴を閉じる。
  段 3 の 2 レンズが file:line で示した 3 点 — 無 lock の linked-worktree registry reader
  (前 wave で実際に偽赤を起こした)、登録外 session fixture 2 本による実親 repo object 書込み、
  lock key が Git common-dir でなく worktree root 由来であること。
  **偽赤の実例があるので分割の話とは独立に価値がある。**
