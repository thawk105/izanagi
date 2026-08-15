# 受入全走のボトルネック分解と、速度改善候補 2 件の反証

- wave: `dev-wave-acceptance-bottleneck` (branch `worktree-dev-wave-acceptance-bottleneck`)
- base main: `43ac2d67`
- 依頼: 「受入全走のボトルネックを改善してください。リワードハック禁止」
- 結論: **実装差分ゼロ。** 候補 2 件をいずれも実測で反証し、`DW-S04` の「実装しない」裁定とした。

## 1. 受入全走の実時間分解 (初の定量化)

一次資料 = `/work/1/SFC/tanab/dev-wave-jobs/*/acceptance-{waiter,child}-*.log` と pid/done の mtime。
測定日 2026-08-13〜14、Pegasus login ノード + gen_S。

| 区間 | 実測 |
|---|---|
| pytest 本体 | 146.67 秒 (10913 passed / 65 skipped) |
| dispatch job elapse | 156 秒 (queue 待ち 9 秒) |
| 受入 1 回の実時間 | 318 秒 (無競合) 〜 2755 秒 (競合時) |
| lease 待ちが占める割合 | 93% (t1053-fixflakes 試行 2: 2634 秒中 2457 秒) |
| 受入成功後、親が lease を握ったまま行う作業 | 約 290 秒 |
| land 本体 | 53 秒 |
| 非帰属 checker (赤のときだけ) | 15 + 63n 秒 |

**ボトルネックは「テストが遅いこと」ではなく「受入が 1 回で終わらないこと」である。**

## 2. 受入試行 31 回の終端

| 終端 | 件数 |
|---|---|
| 成功 | 8 |
| `acceptance-red-check rc=70 source_rc=2` | 17 |
| `merge-message-provenance rc=70` | 2 |
| `signal-15` / `preflight-submodule-ready` / `cli-usage` / `acceptance-receipt` | 各 1 |

`acceptance-red-check` 17 件の内訳と現況:

| reason | 件数 | 現況 |
|---|---|---|
| `probe worktree is not clean, including ignored files` | 13 | [T-1053] `fb7e204f` で解消済み |
| collect の `TimeoutExpired ... 120.0 seconds` | 3 | `_DISPATCH_TIMEOUT_SECONDS = 5100.0` で解消済み |
| `logged pytest nodeid has no exact collected selector` | 1 | 未解消 |

**失敗 23 件のうち 16 件 (70%) の原因は既に main で閉じている。**

## 3. [T-1053] 修正後の checker を初めて実走で検証した

`tools/check_acceptance_reds.py` を base main に対し 6 回実走 (うち 2 回は別 probe-root で同時実行)。
**6/6 とも指紋 gate を通過し、`probe worktree is not clean` は 1 度も出なかった。**
rulings 第 12 回 #2 が置いた再訪条件 (T-1053 適用後の実受入で再発したら [T-1066] を再訪) は、
現時点で不成立である。

所要時間モデル (低負荷時): 赤 1 件 = **77.99 秒**、赤 2 件 = **141.02 秒**。
固定費 ≈ 15 秒、node あたり限界費用 ≈ **63 秒**。`T(n) = 15 + 63n`。

赤 n の実分布 (acceptance-child log 17 本): n=1 が 7、n=2 が 8、n=3 が 1、n=5 が 1。平均 1.76。

## 4. 反証 1 — [T-1090] 非帰属 checker の有界並列化は採らない

前 wave (t1027) が「別 wave の設計事項」として送った項目。段 2 プランは実装可能な設計を出したが、
段 3 の 2 レンズが**独立に**blocker を出し、親が実測で裏取りして不採用にした。

**(a) 正しさ — 判定が「land を通す」向きへ系統的に偏る。**
checker の rerun は「その赤が `tested_main` **でも**落ちるか」を単独走で判定し、
`rerun_rc == 1` なら**非帰属 = land を通す**。ところが worklog 544 / 548 が実測したとおり
signal / launcher 系のテスト族は**負荷が上がると落ちる** (544:「残る 5 件はすべて単独走で緑になる
signal 系のフレーク」)。probe を 4 並列にすればこの単独走のノイズ床が上がり、
`rerun_rc` は 0 から 1 へ倒れやすくなる。すなわち**帰属する赤を非帰属と誤判定して land を通す**。
敵対的な入力を仮定せずに成立する。**性能のために正しさ防壁のノイズ床を上げる構造**である。

**(b) 検出力の純減。** 現行は node ごとの setup 直前に submodule 初期化状態を観測して
前 node の値と比較する。batch 全件を先に setup すると、worker 実行中の変化を検出できない。

**(c) 効果が小さい。** P=4 の節約は赤走行あたり平均 約 48 秒、受入試行 31 回全体に均すと **約 26 秒**。
lease 待ち 2457 秒に対して 1% である。n=1 (7/17) では利得ゼロ。

**(d) 全体では負になりうる。** checker の runner は常に `--force-dispatch` を付けて
`run_tests.py` の queue 判定を迂回する。4 本同時 qsub は**他 wave の qsub 待ちを増やしうる**。
受入は全 wave が 1 本の lease で直列化される資源なので、他 wave を遅らせれば全体では負になる。

レンズ A はさらに、linked worktree が隔離境界でないこと (再走するテスト自身が `git worktree list` で
兄弟 probe を観測・改変しうること) を指摘した。これも real である。

## 5. 反証 2 — merge-message provenance の claim 前 fail-fast は成立しない

実測で `stage=merge-message-provenance` は 2 件あり、いずれも **lease 待ちを約 2500 秒消費してから**
拒否されていた。lease と無関係なローカル判定に見えたので前倒しを設計したが、成立しない。

**`check_ai_provenance.py --message-file` の合否は message の内容だけでなく repository 状態にも依存する。**
claim 前は index が clean で `MERGE_HEAD` が無いため implementation path 集合が空になり、
Codex author 義務が発火しない。claim 後は merge 済みなので発火する。

**親の実測がこれを確定させた。**

- t1050-s8b-admission の受入試行 1 (21:07:29) は `merge-message-provenance rc=70` で失敗し、
  試行 5 (23:30:01) は成功した。
- 両者は**同一の `--merge-message-file`** を使う (`run-acceptance.sh:11`、`run-acceptance5.sh:11`)。
- その file の mtime は **08-13 20:45:45 で以後不変**
  (sha256 `be4ac7768993e0cbcff14216005149835e8a348e373e28b3efccb0453f720538`)。

同じ bytes が拒否され、のちに受理された。よって**合否は message の関数ではない**。
claim 前 (clean index) の検査はこの入力を通すので、2506 秒は救えない。

隔離 worktree で prospective merge を再現する案も採らない。待機は約 40 分あり、その間に main は動く
(並行 wave 7 本)。trial 時点と claim 時点で combined implementation path が変われば
**通るはずの投入を claim 前に拒否する**。t1050 の試行 1 と 5 の差はまさにその変化であり、
偽拒否は理論上の懸念ではなく実測された現象の裏返しである。

## 6. 一般化した設計規則 (独立 2 例から)

反証 1 と反証 2 は別々の機構だが同型である。**どちらも「速くするために、判定の入力文脈を変えていた」。**

- 反証 1: 判定 (単独 rerun) の**実行環境**を 4 並列へ変えていた。
- 反証 2: 判定 (provenance) の**repository 状態**を merge 前へ変えていた。

`DW-G03` の「独立 2 例」を満たすので族として一般化してよい。詳細は decisions の該当 D。

## 7. 親が自分の誤りを訂正した点

1. brief 初版の「n=5 なら有界並列 4 で約 100 秒」は算術誤り。自分の式で `15 + 63*ceil(5/4) = 141` 秒。
   節約 189 秒という表の値は正しく、誤っていたのは並列後の絶対値である (段 3 レンズ B が指摘)。
2. brief v2 の「受理集合を 1 bit も変えない」は誤り。前倒しは「開始時点で不正な message を
   待機中に直して間に合わせる」経路を塞ぐ。さらに段 2 (v2) 子が 2 件の未記載の縮小を列挙した
   (待機中に `behind == 0` になる場合、preflight の一時的実行失敗)。
3. brief 初版の provisional 裁定 P1 (共有状態は submodule の読みだけ) と P3 (通常経路 2 走で
   receipt の byte 一致を示せる) は、段 2・段 3 の双方から反証された。

## 8. 工数

codex 子 4 本、すべて `outcome=accepted`。
plan v1 (max)、consult sol (max)、consult luna (max)、plan v2 (max)。
実装子・fix 子・review 子は「実装しない」裁定のため起動していない。
