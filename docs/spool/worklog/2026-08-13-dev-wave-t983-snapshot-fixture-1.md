---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t983-snapshot-fixture
seq: 1
title: 受入の最長 node を 79.77 秒から 53.08 秒へ下げた — benchmark_snapshots の case 非依存な封印を 1 回に畳み、受理集合は bytes で不変を実証した (コード + docs、branch worktree-dev-wave-t983-snapshot-fixture)
---

## 本文

- ユーザー依頼「受入全走のボトルネック改善。リワードハック禁止」(2026-08-13 00:47 JST)。
  同一依頼の wave `dev-wave-acceptance-critpath` が既に稼働中だったため、追加依頼
  「そのセッションがやっていないボトルネック改善をやってください」(01:00 JST) を受けて
  lane を分けた。向こうは `@real-repo` 直列鎖と `conftest.py`、本 wave は
  `benchmark_snapshots` fixture の重複構築で、編集面は素集合。
- **律速は 1 つの module fixture に集中していた。** `orchestrator/tests/test_codex_reasoning_ab.py`
  の `benchmark_snapshots` が `build_snapshot` を POS/NEG で 2 回呼び、そのたびに
  `_seal_git_object_closure` (snapshot + 3 submodule の計 4 repo に対する `git repack -Ad`) を
  実行していた。cProfile で封印が 1 case 32.204 秒中 22.271 秒 (69%)。
  **この封印は case 非依存**で、case 固有の書き込みは封印より後にしかない。
- **効果 (同一 worktree・同一コマンド・各条件 3 走の中央値、計算ノード)。**
  最長 node `test_supervisor_launches_pair_and_scrubs_git_environment` が
  **79.77 → 53.08 秒 (−26.69 秒、−33%)**、module 焦点走 wall が **81.97 → 55.34 秒**。
  before のばらつきは 80.28〜83.79 秒 (±2%) で、改善幅はその 8 倍以上。
  **テストを 202 → 209 本に増やした上での短縮**である。
- **受理集合を変えていないことを bytes で実証した。** 改修前コードで作った基準 snapshot と
  新経路の snapshot を `_metadata_manifest` 全行で突き合わせ、POS 5,280 行 / NEG 5,283 行の
  path 集合が完全一致、内容差は `.git/index` の 4 件のみ。これは stat cache (inode/ctime) 由来で
  別 directory 間では原理的に一致せず、`git ls-files --stage` 3,198 行の意味比較で同一を確認した。
- **段 4 で「旧との bytes 一致」を恒常テストの責務から外した。** 段 3 レンズ A が
  「新旧とも同じ helper を使うので共通汚染が恒真に一致する」と反証したため。真に独立な比較は
  追加の封印 1 回 (約 27.6 秒) を恒常テストへ持ち込み、その node が新しい最長 node になって
  wave の目的を打ち消す。よって bytes 一致は親が 1 回だけ実測して本エントリへ記録し、
  恒常テストは本改修が新たに持ち込むリスク (base 不変性・複製忠実性・再配置健全性・
  clean copy の正 verify) だけを守る形にした ({{D:shared-base-equivalence-split}})。
- **段 6 の敵対レビュー 2 本がともに NO-GO を返し、must-fix 5 件を閉じた。**
  最大の指摘は **公開 `build_snapshot` の実行被覆が 2 回から 0 回へ落ちていた**こと
  (改修前 fixture は公開関数を呼んでいたが、改修後は private helper 直呼びになった)。
  spy テストで閉じた。他に非 skip 合成テストの穴 4 件 (**恒真 assert `len(...) == 3`** を含む)、
  再帰 preflight の負例が深さ 1 のみ、index 意味比較に flags が無い、
  `includeIf gitdir:` で derived 側だけ絶対 `core.worktree` が活性化する経路。
- **親が自分の主張を 3 件撤回した。**
  1. 「封印は `build_snapshot` の 92%」— home ファイルシステム上の外れ値。
     local `/tmp` の 69.2% を採用する (計算ノードの 1 case 31.7 秒と整合する方)。
  2. 「本 wave は今日の wall を動かさない」— 並行 wave の 7 走実測 (wall ≈ 最長 node + 27〜41 秒、
     最長 node は全条件で本 wave の対象) が覆した。
  3. 「wall が約 24 秒下がる」— 過大。段 3 レンズ B の方法論指摘を受け、
     直接実測量 (最長 node) を主軸にし、wall は受入実測で確認する形へ改めた。
- **親が peer へ渡した根拠 1 件も誤りだった。** 「`test_p3_s4_loop*` が実 `external/ccbench` に
  patch を apply/revert する」と通報したが、現行実装は `patchharness.applied` を
  `contextlib.nullcontext()` へ差し替えており実 ccbench に書かない
  (`orchestrator/tests/test_p3_s4_loop.py:1856-1857` ほか)。[T-990]/[T-991] wave へ訂正を送った。
  `conftest.py:167` のコメントと実装の食い違いは同 wave の lane。
- **閉包漏れの所見を [T-990] へ渡した。** `benchmark_snapshots` の消費 node は実 repo と
  実 `external/ccbench` を読むが `REAL_REPO_SERIAL_NODES` に無い。当初「重い 3 件」と伝えたが、
  先方の指摘どおり**閉包としては消費 node 17 件全部が対象**である (module scope の fixture は
  worker 内で最初に走った消費 node が setup を払い、どれが最初かは静的に決まらない)。
- **測定規律の失敗を 1 件記録する。** fix 後の単走が 73.42 秒で、実装前の単走 60.55 秒より
  遅かったため「fix が +13 秒の劣化を入れた」と読みかけた。反復を取ると 55.26 / 55.34 秒で、
  73.42 は cold cache の外れ値だった。**1 走の差を実装効果へ帰属させる直前だった**
  ({{F:single-run-cold-cache-misattribution}})。
- **通知の先行を 5 回以上観測した。** 背景 task の完了通知が producer 生存中に届く事象が
  段 3・段 6・変異 round 1〜3 で起きた。毎回 `.done` + 成果物 + producer 死の
  3 点照合で防いだ。1 回は未完成の成果物で裁定に入りかけた。
  併せて `tools/dev_wave_wait.py producer` 以外の待ち (`tail --pid`、`while kill -0`) も
  producer 生存中に返る事象が複数回あり、**待ちの戻りを完了の証拠にしてはならない**。
- **親が JST 時刻を実測せずに書き、2 度訂正した** (F1 の再発)。
  1 度目は handoff・段 4 裁定・peer 宛 3 通で約 1 時間 20 分ずれ、2 度目は進捗報告で
  約 1 時間半ずれた。並行 wave は時刻で突き合わせるため、**報告に時刻を書く前に
  必ず `date` を実行する**。訂正は peer へも送った。
- **変異は 3 round を要した。** round 1 は期待 node が collection に無く停止 (fix が負例を
  parametrize して node 名が変わったため)。round 2 は `--force-dispatch` の stdout 省略で
  失敗 node を抽出できず 1 件 PARSE_ERROR となり、直接 pytest を runner にして解消。
  期待 node の予測が 2 件外れたため観測集合で再登録し、round 3 で完全一致を確定させた
  ({{D:mutation-expected-nodes-from-observation}})。**最終結果は負例 8/8 KILLED・正例 1 SURVIVED。**

## 次の一手差分

### carry

- [T-979]
- [T-980]
- [T-981]
- [T-982]

### 新規

- {{T:snapshot-fixture-worker-sharing}} **P3・新規**: `benchmark_snapshots` の worker 跨ぎ共有は
  本 wave で scope 外とした (並行 wave の因果実験 F が「node 秒 -31% で wall 不変」を示しており、
  CPU だけの節約は wall を動かさないため)。現状 k=3 worker が各 39.6 秒級の base を独立に構築する。
  将来 wall がここで律速するなら再検討する。**全 consumer の同一 worker 固め (xdist_group) は
  wall を悪化させる**ことを親が計算で確認済み (並列な重複を直列化するため)。
- {{T:snapshot-index-extension-comparison}} **P3・新規**: 新設の index 意味比較は
  mode/OID/stage/path/flags を見るが index extensions を見ない (docstring に明記済み)。
  extensions まで比較するなら stat cache だけを正規化した bytes 比較が要る。
- {{T:mutation-node-extraction-under-dispatch}} **P2・新規**: 変異 harness の失敗 node 抽出が
  `--force-dispatch` 経由では壊れる。dispatch が子 stdout の中間を省略するため、
  失敗が多い変異で `PARSE_ERROR` になる (本 wave の N6)。回避策は直接 pytest を runner にすること。
  harness 側で「省略された stdout を検出したら fail-closed で別経路を促す」方が安全。
