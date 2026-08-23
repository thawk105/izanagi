---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-real-silo-fixture
seq: 1
title: 実 Silo サンプル不在で常時 skip していた規律2 の地面を、実 emitter 由来の追跡 fixture で復活させた (コード+テスト+docs、branch worktree-dev-wave-real-silo-fixture、変異matrix = 新HEAD KILLED 6/SURVIVED 1(事前登録の等価変異)/MISMATCH 0、旧HEAD SURVIVED 3/3)
---

## 本文

- ユーザーが (a) 実サンプルの再生成と共有 path 配置 / (b) 判定既知の縮小 fixture /
  (c) テスト削除 の 3 択を証拠つきで裁定せよと指示した。親は **(b) を採ったが、
  手製ではなく実 emitter が吐いた bytes の commit-stamp prefix** とした。
  (a) を却下した理由は、66MB を共有 path へ置いても skip が消えるのはこの機体だけで、
  fresh clone では依然 skip になり `orchestrator/tests/README.md` が問題にしている
  「fresh clone で load-bearing テストが空虚に緑」というカバレッジ蒸発が閉じないこと。
  (c) は規律2 の実データ地面の代替が無いため却下した (実 trace を verifier にかける経路は
  `tools/pegasus/mocc_trace_pilot.sh` にもあるが、受入 suite の外の手動 dispatch である)。
- 不在は 28/28 (main checkout + 全 27 worktree) で実測した。疑似スキップ (print + return) の
  違反は無く、`skiputil.skip()` の正しい形だった。
- 素材は再生成せずに済んだ。repo 外に [T-816] の emitter probe が吐いた実 Silo trace
  (`ycsb_silo` を `-DCCBENCH_TRACE=1` で build して 1 秒実行、244,971 commit / 66MB) が現存し、
  親が verifier にかけて certified serializable / integrity clean / anomaly 0 を
  10.72 秒 / peak RSS 965,544 kB で得た。producer の clone HEAD は `511c9538`。
- **親自身の前提が敵対相談で 3 件覆された。** (1) 「fixture の bytes は親が配置する」は
  D95 決定 (2) 違反 (`orchestrator/` 配下の非 Markdown は実装面、test-only も例外にしない)。
  実装子が作る形へ改めた。(2) 「C 行は 6 token」は誤りで parser は正確に 7 field を要求する。
  (3) 「実データ地面を作る」の射程が過大だった (下記 epoch 穴)。
- **最も重い所見は epoch 跨ぎ依存の穴だった。** 既存 13 fixture はすべて単一 epoch で
  epoch 跨ぎ read が 0 件であり、版を `tid` だけで並べる回帰が既存 suite を素通りしていた。
  相談子の対案 (epoch 跨ぎまで切り出す) は**採らなかった** — 実測で bytes が 9.2 倍
  (315,890 → 2,921,008) になる一方、得られるのは偶然の被覆で、狙った回帰を撃つ設計ではない。
  代わりに手製の positive control 2 本 (ww 側と rw 直後版側) を足し、実効性は変異で裏取りした。
- **段 6 の焦点再レビューが NO-GO を返し、親の裁定の論理が 1 つ崩れた。** 親は
  「辺の型組合せ別の組数を exact に固定すれば ww 全落ちを撃てる」と裁定していたが、
  `DSG._reasons()` は adj に既に入っている辺に対して型を再計算するため、
  `_add_ww_edges()` が辺を追加したかとは独立だった。この fixture では ww の 2,996 組が
  すべて wr と同じ `(src,dst)` に重なるので、ww 生成器を止めても観測出力が変わらない。
  **合成 fixture の新設ではなく、docs の誇張を撤回して限界を明記する形で閉じた** —
  閾値が恣意的 (101 txn の fixture は閾値 100 以下しか捕まえない) で、この穴は本 wave が
  作ったものではなく、テストが常時 skip だった時点から存在した先行の限界だからである。
  詳細は {{F:derived-value-pin-is-not-generator-gate}}。
- **変異で両方を実測した。** 無条件の ww 停止 (MUT-5a) は手製 fixture 4 node に KILLED、
  規模条件付き (MUT-5b) は事前登録どおり SURVIVED。ww 生成器そのものは手製 fixture 側で
  確かに gate されており、大規模側だけが未被覆であることが機械で確定した。
- **DW-M08 の新旧両走で純増検出力を示した。** MUT-1 (版順序が epoch 無視) /
  MUT-2a (rw 辺を規模条件で脱落) / MUT-2b (read 辺を全停止) は
  新 HEAD `47a457e4` で 3 件とも KILLED、変更前 HEAD `4cbaf041` で 3 件とも SURVIVED
  (どちらも baseline PASSED、MISMATCH 0)。
- 変異 harness の落とし穴を 2 件実測した。改行を変える byte 変異 (`\n` → `\r\n`) は
  `注入 read-back が不一致` で harness 全体が中止する (registered 7 / recorded 6)。
  行末空白へ差し替えたら正常に KILLED した。また `--runner-mode local` は
  runner (`tools/run_tests.py`) 自身の自動 dispatch を止めず、baseline 1 走の
  `duration_s=340.4` の大半が PBS の queue 待ちだった (テスト本体は 2.70 秒)。
  `tools/mutation_worktree.py` は source repo の `git status` bytes を 2 観測点で束縛するため、
  走行中に親が主 tree を触ってはならないことにも気づいた (今回は編集を止めたので事故なし)。
  **3 件とも統合先が予算満杯で入らなかった** ため {{T:devwave-mutation-docs-budget}} へ回した。
- 並行セッションからの通達 2 件を一次資料で裏取りした。D678 / D679 / D681 / D688 は
  `docs/decisions.md` に実在した。**D689 を「不在」と一度誤認した** — 原因は worktree の
  checkout (base 83e2a8f5) を grep したことで、main の blob を見ると 27204 行に実在する。
  D689 / D690 とも実装は未着地で、main の `tools/dev_wave_wait.py` には `receipt-main-moved` が
  1 箇所、`_RED_CHECKER_PATH` が 4 箇所残っている。運用は現行挙動を前提にした。
  もう 1 件は発信元自身の訂正で、`test_growth_test_holds_contract.py` の赤は main 由来ではなく
  `FORCE_COLOR` / `COLORTERM` を持つセッションから走らせたときだけ出るものだった。
  **本セッションにも両変数が実在する**ことを確認した (worktree が隔離するのは tree であって
  環境ではない)。
- 子の工数: plan 1 / consult 2 / author 1 / review 2 / fix 1 / focus 1 の計 8 本、
  いずれも `gpt-5.6-sol` / effort xhigh。実装子と fix 子の焦点 pytest は
  Pegasus dispatch の `qstat -Q` 失敗 (rc=16、`child_started=false`) で未実走に終わり、
  親が実走した。
- 親の実測: 焦点走 86 passed / 2.25 秒 / rc=0 (skip 0)、`check_docs.py` rc=0 違反なし、
  全史 `check_ai_provenance.py` rc=0 (5,114 件・新規違反なし)、
  追跡 fixture 単体の verify 0.09 秒 / peak RSS 22,000 kB。

## 次の一手差分

### 新規

- {{T:devwave-mutation-docs-budget}} **P2・ユーザー裁定待ち**: 変異まわりで実測した手順事実 3 件が
  統合先の予算満杯で入らない。(i) 改行を変える byte 変異は注入 read-back 不一致で harness が
  中止する → `DW-M04` (節は 404/1000 bytes だが L1.5 集約が 9,566/9,566 で満杯、+160 bytes で
  9,726 となり赤)。(ii) `--runner-mode local` は runner の dispatch を止めない → `DW-M05` /
  `DW-M07` (後者は 977/1000)。(iii) `mutation_worktree.py` 走行中に主 tree を触ってはならない
  → `DW-O19` (997/1000)。自己改善契約は予算のための安全義務の削除・弱化を禁じ、予算値を上げる
  変更は独立審査対象とするため、実装せず裁定へ返す。
- {{T:verifier-independent-oracle}} **P2・ユーザー裁定待ち**: 追跡した実データ fixture の期待値は
  検査対象である verifier 自身の出力であり、golden regression であって独立証明ではない
  (`fixtures/README.md` に明記済み)。独立性を上げる案は (a) 1 thread の自明直列 trace を併設、
  (b) verifier と実装を共有しない checker を保存、(c) broken-Silo の実 emitter 赤 fixture を対に置く、
  の 3 つ。本 wave では scope 外として実装しなかった。
- {{T:ww-generator-scale-coverage}} **P3・新規**: ww 生成器の大規模側が未被覆である
  ({{F:derived-value-pin-is-not-generator-gate}} の残余)。閉じるには 100 txn 超で
  ww が load-bearing (blind write で wr が重ならない) な合成 fixture が要る。
  あわせて、追跡外の大規模実 sample `output/runs/silo-sample` を
  「常設の content-addressed artifact + 明示 opt-in」へ移すかも同時に裁定する。
