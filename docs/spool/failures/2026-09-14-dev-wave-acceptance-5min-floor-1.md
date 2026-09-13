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

### {{F:slowest-shard-premise-9-runs}}. 最遅 shard の identity を 9 走で決めた決定が、112 走の集計で覆った [誤前提] [観測]

- 事象: D1918 (2026-09-10) は「受入全走の**最遅 shard** は shard-2 であり、その最大 worker 占有は
  xdist group `p3-b4-material-report` を 1 worker が背負う区間である」と記録し、
  `test_t080_*` 群は最遅 shard の床ではないと明記した。根拠は 2026-09-09 の **9 走**である。
  本 wave が 2026-09-10〜09-14 の **112 走** (3 shard の `junit.xml` がそろうもの) を集計したところ、
  **最遅 shard は shard-0 が 103 走 (92%)**、shard-2 は 7 走、shard-1 は 2 走であった。
  D1918 が根拠にした 09-10 当日だけを見ても shard-0 が 57 走で最遅である。
  最遅 shard の wall が 300 秒を超えたのは 106/112 走 = 94.6%、中央値 345.2 秒。
- 根本原因: 標本が小さい。9 走では shard の identity が安定して決まらない。
  受入 wall は同居する他 wave の走行数に影響され (同時走行数との相関係数 0.381、n=46)、
  同じ shard でも 319.4〜735.0 秒の幅で動く。**その幅の中で 3 つの shard の順位が入れ替わる。**
  D1918 自身は「主張は『観測 9 走で shard-2 が一度も 300 秒を切らなかった』に留める」と
  正しく限定していたが、決定の題と本文が「最遅 shard は shard-2 である」と断定形になっており、
  後続はそちらを読む。
- 恒久対応: **最遅 shard の identity を根拠に着手対象を決めるときは、固定窓の走数を併記する。**
  本 wave の集計方法は `output/insights/2026-09-14_acceptance-5min-floor/README.md` §11 に
  文章で残した (集計 script は所在を問わず Python が実装面なので repo へ入れない)。
  D1918 の決定本体 (次の短縮対象は最大 worker 占有) は覆っていない — 覆ったのは
  「どの shard か」の部分だけである。
- 再発検知: 「最遅 shard は X である」と書く時点で、何走を数えたかを問う。
  10 走未満なら identity を断定しない。

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

- 事象: 2026-09-14 05:43:32 の `640e5d431` を最後に、main が **2 時間 30 分以上**進まなかった
  (08:15 時点でも同じ tip)。直前は 05:10 / 05:11 / 05:16 / 05:25 / 05:29 / 05:43 と
  数分おきに進んでいた。同時刻に `tools/dev_wave_land.py` が最大 **12 本**走っていた。
  参加していた 7 wave の実測を合わせると次のとおり。

  | wave | land 呼び出し | 内訳 |
  |---|---|---|
  | `dev-wave-t2067-efg-residual` | 20 回 | `stale-main` 1、残り `lock-busy` |
  | `dev-wave-t758-docs-corrections` | 22 回 | 全て `lock-busy`、途中 `rc=29` 2 回 |
  | `dev-wave-t2547-b4-descriptive-erratum` | 14 回 | `stale-main` rc=10 が 1、`rejected` rc=29 が 1、`lock-busy` rc=11 が 12 |
  | `rulings-full18-verdicts` | 16 回 | 全て `phase=post-provenance` |
  | `dev-wave-t2582-manifest-measurement-sources` | 13 回 | 全て `lock-busy`、位相は混在 |

  全件で `retryable_same_request=true`、`main_before == main_after` であった。

- **飢餓には 2 つの位相がある** (同じ wave・同じ引数で両方出る)。

  | 位相 | 実測 | 読み |
  |---|---|---|
  | `phase=initial` | `waited_s=180.003〜180.006` / `window_elapsed_s` も同値 / `limit_s=180.000` | lock を取れないまま窓を使い切る。load 27.63 の回でも出る |
  | `phase=post-provenance` | `waited_s` 0.017〜156.048 と小さいのに `window_elapsed_s` が 198.5〜620.208 へ伸びる | lock の外の監査が窓を食い切る。例: 窓 600.208 秒のうち約 448 秒が監査、実際に待てたのは 152.541 秒 |

  **原因が違うので、再試行間隔を広げるだけでは後者に効かない。** 一度に 1 本へ絞る順番待ちが本体である。

- **lock 自体は壊れていない。** 排他保持は実測 1 分 27 秒で回っている。
  当初「保持者が枠を跨いで 10 分持ち続けた」という見立てが出たが、根拠が `lsof` の
  1 発のスナップショットだけで保持時間を測っておらず、提案者自身が撤回した。
  **スナップショットで誰が握っていたかは、握りっぱなしかどうかの証拠にならない。**

- **`rc=29` は provenance 違反ではない。** 実測された本文は
  `provenance audit failed: TimeoutExpired after 480 seconds` (発生時 load average 75.33) と
  `main/wave heads or collision paths changed during the provenance audit` であった。
  監査の timeout と、監査中の head 移動である。誤読しやすいので明記する。
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
- **当座の解き方 (本 wave で実際に効いたもの)。** 全 wave が再試行を止め、
  **一度に 1 本だけ**投げる順番待ちへ切り替える。順序は**受入 `child-green` の受領証 file の
  mtime が早い順**とする。これは各 wave が自分で測れる客観値で、表の配布も更新も要らず、
  後から参加した wave も自動的に列に入る。
  **本 wave は当初 branch 名の辞書順で 10 分ずつの枠を配ったが、これは失敗した** — (1) 表が
  参加 wave を 3 件取りこぼし、載っていない側から見れば順序が存在しないのと同じで、
  (2) 枠を単独で使った wave が 10 分待っても `lock-busy` で戻った (自粛していない投入が
  残っていたため)。**順序表を配る方式は、配り手が全参加者を知っていることに依存する。**
  受入は共通 lock を取らないので、列の外で走らせてよい。受領証が古くなった wave は
  受入を終えてから次に空いた順番に入る。
- **列の位置は「その wave が最初に `child-green` を得た時刻」で固定し、受入のやり直しでは
  更新しない。** 現在の受領証 mtime で毎回取り直すと、stale になった wave は取り直しのたびに
  新しい mtime を持つので**最後尾へ回され、原理的に永久に着地できない**
  (実測で受入のやり直しは 25〜30 分かかり、その間に後続が通ってまた stale になる)。
  受入は共通 lock を取らないので、列の位置を保ったまま列の外で回せる。
  また、**land に実際に渡せない古い受領証で位置を主張してはならない** —
  ある wave は 03:54:07 の `child-green` を持っていたが、5 commit 前の main に束縛されていて
  使えないため申告せず、実際に渡す 06:02:24 を申告した。これが正しい。
- **この列は、順序の基準を固定しない限り「1 本通るたびに測り直す順序」になってしまう。**
  `tools/dev_wave_land.py` は locked main が tested した監査閉包の外へ動いていると
  `RC_STALE_MAIN` / `status=stale-main` を返す。**先頭が通って main が進んだ瞬間、
  後続は全員 `DW-O23` の取り込みと受入の取り直しが必要になり、受領証 mtime が振り直される。**
  順序が保たれるのは全員の取り直しが同時に始まり完了順も元と同じときだけで、
  実際には取り直しの所要が wave ごとに違うので列は毎回変わる。
- **帰結: main の吸収能力は「受入全走 1 回 + land 1 回」あたり 1 wave である。**
  6 本並んでいれば 6 回の land と 5 回の受入全走 (1 回あたり 23,000 件超、実測 214.9〜735.0 秒に
  queue 待ちが加わる) を要する。**これは飢餓とは別の、構造的な上限である。**
  並行 wave 数がこの吸収能力を超えると、詰まりは必ず起きる。
- 再発検知: main の先端 commit 時刻と現在時刻の差。30 分以上開いていて `dev_wave_land.py` が
  複数走っていれば本件である。`status=lock-busy` かつ `waited_s << limit_s` かつ
  `window_elapsed_s > limit_s` の組が `post-provenance` 位相の署名、
  `waited_s == window_elapsed_s == limit_s` が `initial` 位相の署名になる。
