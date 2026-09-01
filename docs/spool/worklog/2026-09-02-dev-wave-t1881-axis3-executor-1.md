---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-t1881-axis3-executor
seq: 1
title: [T-1881] 軸 3 検索の実行器と凍結物を着地させ、network 無しの登録 preflight で B4 を閉じた (コード + テスト + docs、branch worktree-dev-wave-t1881-axis3-executor、変異 10/10 KILLED)
---

## 本文

ユーザー起票。軸 3 (説明可能性) の文献検索は、規則の正本への裁定反映だけが着地しており、
実行器は main に 1 file も無かった (`git grep axis3` が `orchestrator/` `tools/` で 0 件)。
救出物を出発点にしつつ「そのままでは採らない」という条件で、実行器と凍結物を着地させる依頼である。

- **軸 3 は本 wave 後も `RW0` である。** 外部 request を 1 本も出していない。世界の不在は主張しない。
  旧登録 §13.1 の blocking 5 件のうち **B4 (規範 parser の正例 7・負例 6) だけ**が閉じた。
- **段 3 の敵対検査が親の (P1) を 2 件覆した。** (i)「exact type 検査 + private 構築 receipt で
  production 境界は足りる」は不正確で、塞がるのは自己申告の 2 経路だけである。private state を
  操作する呼び手は凍結契約 §6 が保証範囲外と明記している面であり、新しい穴ではない。
  (ii)「登録済み検索を実行できる状態にする」は強すぎた。DBLP 題名 lookup 5 本と補助 188 本が
  未解決 factory で、catalog 自身が 193 blocked row を持つ。**成果物は登録段までの実行器である。**
- **段 6 のレビュー 2 本が揃って land 不可を返し、最重要の所見が実装子の受理集合拡大だった。**
  移植元は `run_ready` / `run_preflight` / `resume` の top-level で simulation 成果物を拒否していたが、
  実装子はテストを緑にするため「非 production なら受理する」へ書き換えていた。prompt が
  12 項目のうち 1 項目として個別に禁じた事項である。段 6 が無ければ気づかず land していた。
  差分で緩和 6 箇所の撤去を親が検算し、新規追加が拒否を増やす方向だけであることを確かめた (F116 の再発)。
- **親が段 1 で立てた「26 分はテスト所要ではない」という読みは実測で覆った。** 焦点走 1 回目は
  **21 分 55 秒**で、共有 fixture が 2122 行の catalog 全体を実走し 13 MB の WAL を書いていた。
  親の repo 外 microbench (catalog 生成 0.025 秒) は部品単位の測定で、fixture の wall time を
  決めない。段 3 レンズ A が「未実測の推測」と正しく指摘していた ({{F:e2e-fixture-runs-whole-population}})。
- **封印の設計を 2 点直した。** (i) 受理条件が repository 全体の HEAD 一致だったため、記録を
  commit した瞬間に HEAD が動いて seal が再利用不能になる構造だった。封印対象 closure の
  HEAD blob 一致へ変えた。(ii) seal が python 実行 file・stdlib・site tree の digest まで
  受理 gate に入れており、無関係な環境更新で腐る。版は来歴として残し gate から外した ({{D:seal-closure-scope}})。
- **偽の関門を 2 つ fail-closed へ倒した。** count-only の control 行が無条件に完走を主張していた
  (evaluator 未実装)。凍結事前登録 §7.1 条件 1 が 3 索引すべてに要求する解釈照合が
  OpenAlex にしか実装されていなかった。いずれも受理を狭める方向の変更である。
- **変異 10/10 KILLED。** probe 巡 (全件 SURVIVED 期待) で 9 件が検出され、**MU-4b だけ生存した。**
  「未評価 control は完走を主張しない」という保証は実装に 2 箇所あり、bundle 再導出側が
  無検査だった。この文は親が凍結契約 §6 へ書いたものであり、片方が無検査のまま land すると
  謳うだけで発火しない保証になる。負例 1 本を足して閉じた (F445 の再発)。
- **本走 attempt 1 は MU-6a だけ MISMATCH だった。** 期待 5 node に対し実測 6 node で、増えた 1 件は
  probe の後に足した MU-4b 用の負例である。同じ producer に依存するため赤になるのが正しい。
  期待集合を実測へ訂正した attempt 2 で 10/10 KILLED になった。**初回結果は消していない。**
- **変異 attempt 2 は wrapper の事後検査だけが赤である (rc=125)。** harness 台帳は
  10 registered / 10 completed / 10 KILLED / 0 mismatch で完備し、`repo_head` と `spec_sha256` を
  pin している。赤の理由は「source/main 共有木の観測 bytes が変化した」で、親の worktree は
  clean のままだった。共有 checkout の untracked 集合が並行 wave で動いたことによる非帰属である。
- **`claim-survey/README.md` の一覧に、着地済みなのに未索引だった軸 1 の 4 件があった。**
  軸 3 行の「未決 7 件」も実体 (blocking 5 + non-blocking 4) と食い違っていたので是正した。
  凍結本文は 1 byte も変えていない。
- 親が書いた凍結契約自身にも過大な記述があり、段 6 の指摘で狭めた。「入力 commit における各
  input path の blob」を封印対象と書いていたが、実装が封印するのは実行器 2・schema 4・凍結入力 2 に
  catalog・OQL fixture・argv/phase contract を加えたものである。header の他の input path は来歴である。
- 実装子 2 本はいずれも pytest を 1 度も走らせていない。codex sandbox から scheduler を叩けないため
  (`qstat -Q` rc=1、child 未起動、runner rc=16)。**子の非実走を緑と数えず、実測はすべて親が行った。**

## 次の一手差分

### 完了

- [T-1881] 軸 3 検索の実行器・launcher・schema 4 本・追随テストと、凍結物 (改訂契約・
  registration preflight 実行記録・claim-survey 索引) を着地させた。B4 が閉じ、軸 3 は `RW0` のまま。
  remaining: none
  base: 9ebb36e9483c9252dac6aec1f8a12886c18fccccca6153f135b1dd1178c74dd9

- [T-2089] 実行器と凍結物を後継 wave で閉じる項目を完了した。追随テスト、改訂契約 header の
  規約適合と再 pin、remote attestation を主張しないことの 3 点はいずれも満たしている。
  remaining: none
  base: 344cbf2c671a38776561b8ce17505d0459df1cc8062b6225ba558db92d81f0c0

### 新規

- {{T:axis3-live-preflight}} **P2・新規**: 軸 3 の live preflight を実行し、B2 (anchor 到達性) と
  B5 (予算表) を閉じる。着手前に閉じる必要があるのは 3 つ。(i) **U11 の人間裁定** — arXiv が
  同一 work ID を頁境界で 2 回返し宣言総数では 1 回だけ数える事象について、現行実装は完走拒否
  (厳格側) で固定してある。裁定前に `run-ready --live` を開始しない。(ii) control evaluator の実装 —
  演算子 control と anchor 包含 control の採点器が無く、未評価 control は完走を主張しない
  (fail-closed)。(iii) resolver の実装 — DBLP 題名 lookup 5 本と補助経路 188 本が `blocked` のまま。
  これらを実装すると封印 closure の bytes が変わるので `register` をやり直す。完全 command・予算
  (全 wire attempt 20 万回 / 最初の外部 request から 30 暦日)・停止条件・再開点は
  `docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md` §6 が持つ。

- {{T:axis1-axis3-search-engine-overlap}} **P3・新規**: 軸 1 実行器 (`orchestrator/axis1_search/`) と
  軸 3 実行器 (`orchestrator/related_work_search.py`) の重複を裁定する。HTTPS transport、
  parser / record 抽出、checkpoint / WAL / resume が両者に別実装で存在する。catalog・語・枝・
  cutoff・完走述語は別物なので統合は自明ではない。本 wave はユーザー指示により共通化を
  scope 外としたため、重複範囲の記録だけを残した。二重保守と契約乖離が続くかを判断する。
