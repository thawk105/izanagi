# 受入全走の律速 — 実測と、効かなかった打ち手の記録 (2026-09-14)

wave `dev-wave-acceptance-5min-floor`。ユーザーの依頼は「受入全走を 5 分に収めろ」。

**結論を先に。5 分には収まっていない。** 本 wave で入れた変更に、同時刻の対照に対する
wall 短縮は観測できなかった。以下はその実測と、残る打ち手がなぜ裁定を要するかの記録である。

## 1. 受入 wall の分布 (一次資料: repo 外の shard 成果物)

`/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/shard-<n>/junit.xml` の
`<testsuite name="pytest">` 属性を集計した。集計 script は `tools/` に置いた。

**2026-09-14 03:47〜07:28 の旧コード 44 走 (本 wave の変更を含まない):**

| 量 | 値 |
|---|---|
| 最遅 shard の wall 中央値 | **368.6 秒** |
| 同 最小 / 最大 | 319.4 秒 / 735.0 秒 |
| `test_s8b_oracle_driver` の最長単体 中央値 | 258.8 秒 |
| 同 最小 / 最大 | 208.5 秒 / 556.9 秒 |

**09-10〜09-14 の 112 走 (3 shard がそろうもの):**

| 量 | 値 |
|---|---|
| 最遅が shard-0 | **103 走 (92%)** |
| 最遅が shard-2 / shard-1 | 7 走 / 2 走 |
| 最遅 wall が 300 秒超 | **106 / 112 走 = 94.6%** |
| 最遅 wall 中央値 | 345.2 秒 |

**D1918 (2026-09-10) の「最遅 shard は shard-2」は失効している。** 同決定は 2026-09-09 の
9 走を根拠にしており、標本が小さい。現行は shard-0 である。

## 2. wall の内訳 (最遅 shard、本 wave の走行 `531cc7a5`)

| 区間 | 秒 |
|---|---|
| collection | 約 93 |
| collection 終了 → 最初のテスト開始 | 25.6 |
| テスト実行窓 | 243.4 |
| **合計 (junit の `time`)** | **361.9** |

**テスト以外が約 1/3 を占める。** shard-1 / shard-2 では「収集終了 → 開始」が 0.1〜0.7 秒で、
25.6 秒は shard-0 固有である。

## 3. 混雑の寄与

同時に走っていた他の受入走行の本数と、最遅 shard の wall の相関係数は **0.381 (n=46)**。

| 同時走行数 | 走数 | 最遅 wall 中央値 |
|---|---|---|
| 1 本 | 5 | 385.3 秒 |
| 2 本 | 10 | 331.7 秒 |
| 3 本 | 10 | 347.3 秒 |
| 4 本 | 5 | 359.2 秒 |
| 5 本 | 6 | 493.3 秒 |
| 6 本 | 9 | 438.5 秒 |

**混雑は効くが支配的ではない。同時走行が最少のときでも中央値 385.3 秒であり、
混雑をゼロにしても 300 秒には入らない。**

## 4. fixture 入力の肥大 (律速の正体)

`orchestrator/tests/test_s8b_oracle_driver.py` の `_t080_stub_free_e2e_repo` は、
`orchestrator/` 全体と Git から見える `output/` 全件を temp repo へ複製し、
`git add -A` して commit し、`git submodule add` し、子 python で
draft → validate → finalize → verify → public gate を走らせる。

| コピー元 | 2026-07-26 (docstring 記載時、commit `6d3f2d21a`) | 2026-09-14 |
|---|---|---|
| 件数 | 2,094 | **22,988** (11.0 倍) |
| bytes | 24,427,374 | **639,898,207** (26.2 倍) |

内訳は `output/insights` 18,199 件 / 396.2 MB、`output/env` 3,246 件 / 195.4 MB。
**この 2 dir は削れない** — 並行の repo 肥大掃除 wave が独立に調べ、tracked の削除確定 0 件、
pin 閉包が閉じている、と結論した (件数の独立集計は 22,994 件 / 639,961,594 bytes でほぼ一致)。

repo は `/work` = **lustre** にあり、書き先 `/tmp` はローカル xfs である。
コピー元の全件読み出しの実費 (負荷の高い login node、`tar` で `/dev/null` へ):

| 対象 | metadata のみ | 全 bytes |
|---|---|---|
| `output/insights` | 8.3 秒 | 16.7〜20.9 秒 |
| `output/env` | 0.78 秒 | 2.1 秒 |
| `orchestrator` | 0.58 秒 | 0.71 秒 |

**1 回の全件読み出しが約 20〜24 秒。** これを 1 走で 11 回払っていた。
t080 の 11 node は引数の組が 5 種類しかないが、process 内 memo は worker ごとなので
全部別 worker に載ると 1 度も当たらない (shard-0 の実行窓 313.609 秒に対し当該 node の所要が
287.973〜310.177 秒であり、最小 2 件の和 357.761 秒が窓を超えることから確定)。

## 5. 単独走との差 = 奪い合い

同じ node を計算ノードで単独に走らせた (job `996264.nqsv`)。

| 走り方 | `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5` |
|---|---|
| 受入全走の中 (48 worker) | 303.8 秒 |
| 計算ノードで単独 | **108.69 秒** |

差 195 秒 (64%) は本質的費用ではない。

## 6. 入れた変更と、効かなかったこと

**入れたもの (commit `11226808a`):** t080 の base を pytest session の worker 間で 1 回だけ組む。
複製する bytes と全件性は 1 byte も変えていない (同 file 1302 行・1328 行が全件性そのものを
検査しており、絞ると正しく赤になる)。あわせて fixture が作る repo 7 箇所で自動 gc を無効化した
(背景 gc が後始末の削除と競合して `gc.pid` の消失で落ちていた)。

**機構は動いている。** `test_t080_shared_base_builds_real_builder_once_across_processes` が
実 builder の呼び出し回数を数えて緑になる。lustre からの全件読み出しは 11 回 → 1 回。

**しかし wall 短縮は観測できない。**

| | 最遅 wall | t080 最長 | 判定 |
|---|---|---|---|
| 旧コード 44 走 (同時刻) | 中央値 368.6 秒 (319.4〜735.0) | 中央値 258.8 秒 (208.5〜556.9) | — |
| 新コード run A | 361.9 秒 | 239.9 秒 | 赤 (subreaper 由来の回帰を含む) |
| 新コード run B | 562.3 秒 | 385.0 秒 | 赤 (同上) |
| **新コード run C (撤去後、最終)** | **334.2 秒** | 242.0 秒 | **`child-green`・赤 0 件・error 0 件** |

**3 走とも旧コードの分布の内側である。** 理由は算術で説明がつく。build は 1 回 20〜24 秒、
node 全体は約 260 秒。11 回を 1 回にしても 1 node あたり 20 秒 (約 8%) で、ばらつきに埋もれる。

run C の内訳は 収集終了→開始 26.0 秒 / 実行窓 245.8 秒 / 残り 62.4 秒 (collection)。
shard-1 は 214.9 秒、shard-2 は 225.2 秒で、**shard-0 だけが 300 秒を超える。**
shard-1 / shard-2 の「収集終了→開始」は 0.1 秒で、shard-0 の 26.0 秒は shard-0 固有である。

**親は当初「438.5 秒 → 361.9 秒」と報告したが、これは撤回した。** 基準に選んだ 438.5 秒は
旧コードの中央値 368.6 秒より遅い 1 走であった。単一走どうしの比較で効果を主張してはならない。

## 7. 撤去したもの

計算ノード job が pytest 完了後に終わらない事象に対し、supervisor を subreaper にして
残存子孫を回収する変更を入れた。実走で**孫 6 本の取り残しを実際に回収できた**。

しかし `orchestrator/tests/test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed`
が赤になった。同 test は旧コード 44 走すべてで緑である。機序は次のとおり。

- subreaper を置くと孤児は init でなく supervisor へ付け替わる。init は常時 `wait` しているので
  実質即座にゾンビを消すが、supervisor は直接の子が終わるまで `wait` しない。
- 残存数の計数は `/proc/<pid>/stat` の PGID 一致で加算し、**state が `Z` でも除外しない。**
- 継続回収 (`waitpid(-1, 0)`) を入れた版では焦点走 1247 件が緑になったが、
  受入全走の負荷下では再び赤になった。**窓は subreaper を置く限り消えない。**

絶対規律 2 に従い撤去した (commit `52e8fe7cf`)。診断の `IZANAGI_DISPATCH_JOB_TRACE` だけ残した。
result 公開前後の各段を job の stderr へ時刻つきで出すので、**次に job が終わらなくなったとき
どの段で止まったかは特定できる。**

## 8. 価値の側の判定 (段 3 の相談、lane=sol)

「高コストなテストは研究に必要か」というユーザーの問いへの答え。

- 100 秒以上の 37 node のうち、**「走ごとに答えが変わらないので毎走でなくてよい」と
  証明できたものは 0 件・0 秒。**
- 32 件は certified 選択・proof chain・材料レポート・試行台帳のいずれかを直接守る。
- 残り 5 件は別研究 (認証層比較、計 643.7 秒) が 4 件と開発運用が 1 件。
- **同じ案は F485 で実行済みで事故になっている** (T-080 の 11 node をコスト理由で opt-in 化し、
  11 日後に赤 2 件が発覚、凍結検証の追随漏れを隠していた)。
- D532 は削除・skip・selection 縮小を規律 2 違反として検討対象外にし、D700 は T-080 の
  別 gate 定期実行も却下している。

逐語は `verbatim/s3-consult-sol-value-lens.md`。費用の側は `verbatim/s3-consult-luna-cost-lens.md`。

## 9. 残る打ち手 (すべて裁定が要る)

300 秒に入るには中央値から約 62 秒削る必要がある。

1. **collection 約 93 秒 + 開始待ち 25.6 秒。** D1830 は「残余の動く分は主に collection に出る」、
   D1728 は自 shard 絞り込みを D711 の禁止ごと維持している。
2. **fixture の `output/` 複製範囲。** 絞ると 1302 行・1328 行が正しく赤になる (受理集合が変わる)。
3. **K を 3 から増やす。** D1620 が canonical を K=3 と明記、D1103 が「K=3 で既に単体テストの
   床に達している」とする (測定面の定義に触れる)。
4. **残存数の計数が zombie を除外するか。** 受理集合が変わる。
5. **land の共通 lock 待ち窓。** 本 wave の観測期間中、main が 1 時間 26 分進まなかった
   (05:43:32 の `640e5d431` から 07:09:45 まで、land が 8 本同時)。窓 180 秒を lock 外の
   provenance 監査 (数分級) が食い潰す。D254 / `DW-O25` の設計に触れる。

## 10. この dir の中身

- `verbatim/s1-measurements.md` — 親が段 1 で実測した一次資料 (子へ射影したもの)。訂正 2 件を含む。
- `verbatim/s3-consult-sol-value-lens.md` — 価値レンズの逐語 (gpt-6-astra / reasoning high)。
- `verbatim/s3-consult-luna-cost-lens.md` — 費用レンズの逐語 (同上)。
- `verbatim/s4-ruling.md` — 親の段 4 裁定。
集計 script は repo へ入れない (所在を問わず Python / Shell は実装面であり、
親が書いたものを置けない)。代わりに再現手順を書く。

## 11. 上の表の再現手順

一次資料はすべて `/work/1/SFC/tanab/.izanagi-acceptance-shards/<digest>/` にある。
**repo 外の走行成果物なので、古い走行が消えると再現しない。**

- **§1 の分布:** 各 session root の `shard-{0,1,2}/junit.xml` 先頭から
  `<testsuite name="pytest" ...>` を読み、`time` / `errors` / `failures` / `tests` /
  `timestamp` / `hostname` を取る。3 shard がそろう root だけを数え、
  `time` の最大を「最遅 shard の wall」とする。旧コードと新コードの区別は
  session root の digest で行う (本 wave の 2 走は `531cc7a5...` と `36df2372...`)。
- **§1 の t080 最長:** 同 junit で `classname` が `...test_s8b_oracle_driver` の
  `<testcase>` の `time` の最大。
- **§2 の内訳:** `shard-<n>/report.json` の `session_timeline`。
  `collection_finished_epoch_s` と、各 worker の `first_test_started_epoch_s` /
  `last_test_finished_epoch_s` から、収集終了→開始と実行窓を出す。
  `real_repo_lock_intervals` は取得**後**に記録されるので保持時間であって待ち時間ではない。
- **§3 の同時走行数:** 各走の区間を [最初の shard の `timestamp`,
  max(`timestamp` + `time`)] とし、他走の区間と重なる本数を数える。
- **§4 の読み出し実費:** worktree で `tar -cf /dev/null <path>` と
  `find <path> -type f -printf ''` を時刻差で測る。**負荷の高い login node の値である。**
- **§7 の帰属:** 対象 test 名で旧コード走と新コード走の `<testcase>` を引き、
  直後に `<failure` / `<error` が続くかで赤緑を分ける。自己終端 `/>` は緑。
