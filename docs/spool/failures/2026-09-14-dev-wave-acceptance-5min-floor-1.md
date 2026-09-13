---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-acceptance-5min-floor
seq: 1
---

## 新規

### {{F:single-run-perf-claim}}. 受入 1 走の前後比較で短縮を主張しかけ、同時刻の対照 44 走に否定された [測定の交絡] [誤前提]

- 事象: t080 の base を worker 間で共有する変更を入れ、受入全走を 1 回走らせて最遅 shard の
  wall が 438.5 秒 → 361.9 秒になったと親が報告した。その後、同じコードでもう 1 走したところ
  562.3 秒であった。同時刻 (03:47〜07:28) に走っていた**旧コードの受入 44 走**を集計すると、
  最遅 shard の wall は中央値 368.6 秒 / 最小 319.4 秒 / 最大 735.0 秒であり、
  **新コードの 2 走 (361.9 / 562.3) はどちらもこの分布の内側**である。改善は検出できない。
  基準に選んだ 438.5 秒は、旧コードの中央値 368.6 秒より遅い 1 走であった。
- 根本原因: 受入 wall は同居する他 wave の走行数に影響される (同時走行数との相関係数 0.381、
  n=46)。単一走どうしの差を機構の効果と読むと、負荷のばらつきを効果と取り違える。
  親は変更が構造として正しい (lustre 全件読み出しが 11 回 → 1 回) ことを確かめた時点で、
  wall にも出るはずだと先回りした。**構造の正しさは wall の短縮を含意しない。**
  実際、build は 1 回 20〜24 秒で node 全体は約 260 秒であり、11 回を 1 回にしても
  1 node あたり 20 秒 (約 8%) でばらつきに埋もれる。
- 恒久対応: 共有計算機で受入 wall の前後比較をするときは、**同時刻に走っている他 wave の
  受入成果物を対照に取る。** 対照は `/work/1/SFC/tanab/.izanagi-acceptance-shards/*/shard-*/junit.xml`
  の `<testsuite>` 属性から作れる (本 wave の集計 script は
  `output/insights/2026-09-14_acceptance-5min-floor/` に逐語で残す)。
  D1714 が既に「最長の単体テスト 1 本を犯人として名指ししない」と定めており、
  本件はその同族である — **1 走の差を効果と名指ししない。**
- 再発検知: 報告に「変更前 X 秒 → 変更後 Y 秒」と書く時点で、対照の走数と分布を併記できるかを
  問う。併記できないなら、その主張はまだ成立していない。

### {{F:subreaper-zombie-window}}. supervisor を subreaper 化したらゾンビの窓が残存数の計数に拾われ、44 走緑だった正しさテストが赤になった [誤前提] [テスト代表性]

- 事象: 計算ノード job が pytest 完了後に終わらない事象を直すため、
  `tools/pegasus/dispatch_compute.py` の supervisor を `prctl` で subreaper にし、
  直接の子の終了後に残存子孫を回収する処理を入れた。実走で孫 6 本の取り残しを実際に回収できた。
  しかし受入全走で
  `orchestrator/tests/test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` が
  赤になった。同 test は 2026-09-14 03:47〜07:28 の受入 44 走すべてで緑である。
  失敗本文は `assert receipt["attempts"][0]["process_group_residual"] == 0` に対する `1 == 0`。
- 根本原因: subreaper を置くと、孤児は init ではなく supervisor へ付け替わる。
  init は常時 `wait` しているため実質即座にゾンビを消すが、supervisor は直接の子が終わるまで
  `wait` しないため、死んだ子孫がゾンビとして `/proc` に残る。
  `tools/codex_worker_launch.py` の残存数の計数は `/proc/<pid>/stat` の PGID 一致で加算し、
  **state が `Z` でも除外しない。** そのためゾンビが残存として数えられる。
  supervisor の待機を `waitpid(-1, 0)` へ変えて継続回収する版では焦点走 1247 件が緑になったが、
  **受入全走の負荷下では再び赤になった。** 回収までの窓は subreaper を置く限り消えない。
- 恒久対応: 絶対規律 2 に従い、subreaper 化と子孫回収を**撤去した**
  (commit `52e8fe7cf`)。診断の `IZANAGI_DISPATCH_JOB_TRACE` だけ残し、
  result 公開前後の各段 (`result-file-fsync-start` / `-complete`、`result-published`、
  `result-dir-fsync-start` / `-complete`、`result-write-return`、`job-return`、
  `job-run-returned`) を job の stderr へ時刻つきで出す。次に job が終わらなくなったとき、
  どの段で止まったかはこの痕跡で特定できる。
  **計数側 (`_group_member_count` が `Z` を除外するか) を直す案は受理集合を変えるため
  採らず、ユーザー裁定へ返した。**
- 再発検知: reparenting を変える変更 (subreaper、PID namespace、`setsid` の追加) を入れるときは、
  `/proc` の走査で生死や残存を判定している consumer を先に列挙する。
  本件では `tools/codex_worker_launch.py` の残存数計数と `tools/dev_waves/worker.py` の
  同型の走査がそれに当たる。**焦点走が緑でも受入全走で赤になりうる** — 負荷が窓を広げるため、
  焦点走の緑を根拠に閉じない。

### {{F:fixture-input-drift-26x}}. fixture の docstring が前提にしたコピー元規模が 26 倍に膨れ、その前提で設計された memo が無効化されていた [ドリフト] [誤前提]

- 事象: `orchestrator/tests/test_s8b_oracle_driver.py` の `_t080_stub_free_e2e_repo` は
  docstring に「36MB / 2300 ファイルの copytree ... で 1 回 15〜22 秒」と書いている
  (2026-07-26 の commit `6d3f2d21a` 時点の実測)。**2026-09-14 のコピー元は tracked blob だけで
  22,988 件 / 639,898,207 bytes** であり、件数 11.0 倍・bytes 26.2 倍である
  (`output/insights` 18,199 件 / 396.2 MB、`output/env` 3,246 件 / 195.4 MB)。
  docstring は当時のまま残っていた。同 file の 855 行には、2026-07-27 に別の肥大
  (ignored な s1-build-cache) で 15〜22 秒が 121.7 秒へ膨らんだ記録があり、**同じ型が
  tracked 側で再発していた。**
- 根本原因: fixture が複製するのは「Git から見える `output/` 全件」であり、
  この集合は wave が insight を積むたびに増える。**成果物の追記が、無関係に見える
  テストの所要へ直結する経路**が設計に入っていた。さらに process 内 memo は
  worker ごとに base を組み直すため、xdist で 11 node が別 worker に載ると 1 度も当たらない
  (shard-0 の実行窓 313.609 秒に対し当該 node の所要が 287.973〜310.177 秒であり、
  最小 2 件の和 357.761 秒が窓を超えることから確定した)。1 走あたり build 11 回。
- 恒久対応: base を pytest session の worker 間で 1 回だけ組む形へ変えた
  (commit `11226808a`)。**複製する bytes と全件性は 1 byte も変えていない** —
  同 file の 1302 行・1328 行が全件性そのものを検査しており、絞ると正しく赤になる。
  あわせて fixture が作る repo (git init 6 箇所と submodule 追加 1 箇所) で自動 gc を
  無効化した。背景 gc が後始末の削除と競合して `gc.pid` の消失で落ちていた。
  **ただしこの変更に wall 短縮は観測されていない** ({{F:single-run-perf-claim}})。
- 再発検知: 「N MB / M ファイル」「1 回 X 秒」を書いた docstring は、その数字が測られた
  commit を併記する。本件の 855 行のコメントは `[T-128] 実測 2026-07-27` と書いており、
  この形は正しい。`_copy_git_visible_output` のように**成長する集合を丸ごと入力にする
  fixture** は、成長側の台帳 (`output/`) と同じ wave で見る。

### {{F:land-lock-provenance-starvation}}. land の共通 lock 待ち窓を lock 外の provenance 監査が食い潰し、6 wave が 1 時間 26 分 main を進められなかった [資源競合] [手順漏れ]

- 事象: 2026-09-14 05:43:32 の `640e5d431` を最後に、main が 07:09:45 まで
  **1 時間 26 分**進まなかった。直前は 05:10 / 05:11 / 05:16 / 05:25 / 05:29 / 05:43 と
  数分おきに進んでいた。同時刻に `tools/dev_wave_land.py` が **8 本**走っていた
  (経過 37〜382 秒)。1 つの wave は 12 回以上再投入し、毎回
  `status=lock-busy` / `phase=post-provenance` / `retryable_same_request=true`、
  `waited_s` 3.8〜136.1 秒、`window_elapsed_s` 272.6〜620.1 秒、`limit_s` 180.000 であった。
- 根本原因: `tools/dev_wave_land.py:65` の `_LAND_LOCK_WAIT_SECONDS = 180.0` に対し、
  `_audit_provenance_history` は docstring が明記するとおり **lock の外で** wave tip の
  全史 provenance 監査を走らせる。窓の起点が lock 待ち開始ではなく操作開始側にあるため、
  監査で窓を使い切り、lock が空くのを待てない。監査の所要は数分級である
  (本 wave の親が login node で同じ `check_ai_provenance.py` の全史監査を走らせ、
  9766 件 / 観測ピーク 665,911,296 bytes で 120 秒超を要した)。
  さらに `_ProvenanceReceipt` は invocation 内のメモリにしか存在せず disk に残らないため、
  **着地 tip を固定したまま再投入しても毎回フルの監査が走り直す。** 全員が同じ形なら、
  誰も lock を取れないまま全員が窓を溶かす。
- 恒久対応: **未実施。** 本 wave では直していない。`dev_wave_land.py` は同時に 8 session が
  使う生命線であり、走行中に挙動を変えると全員を巻き込む。また窓の時計の定義は
  D254 と `DW-O25` が定めた「監査を lock の外で走らせる」設計そのものであり、
  親が自律で動かせる範囲を越える。**ユーザー裁定へ返した。**
  直し方の候補は 2 つで、(a) 窓の起点を lock 待ち開始へ移す、
  (b) 同一 tip・同一 checker blob の監査結果を disk の受領証として再利用する。
- 再発検知: main の先端 commit 時刻と現在時刻の差。30 分以上開いていて `dev_wave_land.py` が
  複数走っていれば本件である。`status=lock-busy` かつ `waited_s << limit_s` かつ
  `window_elapsed_s > limit_s` の組が署名になる。
