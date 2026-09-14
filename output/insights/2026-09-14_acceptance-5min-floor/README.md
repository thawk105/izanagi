# 受入全走の律速 — 実測と、効いた打ち手・効かなかった打ち手 (2026-09-14)

wave `dev-wave-acceptance-5min-floor`。ユーザーの依頼は「受入全走を 5 分に収めろ」。

## 結論 (最初に読む)

**着地したのは 306.9〜321.3 秒の緑。300 秒を切る形 (279.8 秒) も実測できたが、
赤を伴ったので本 wave では着地させなかった。**

同じ窓の旧コード **91 走**の最遅 shard wall は中央値 **361.7 秒** (最小 314.9 / 最大 667.7 /
下位四分位 336.6)。本 wave の走行は次である。

| 走 | 入っている変更 | wall | 旧 91 走中の位置 | 赤 |
|---|---|---|---|---|
| A | t080 base 共有だけ | 361.9 秒 | 51 パーセンタイル | あり |
| B | 同上 (高負荷時) | 562.3 秒 | 88 パーセンタイル | あり |
| C | subreaper 撤去後 | 334.2 秒 | 20 パーセンタイル | **0 件** |
| D | + 配分の所要秒均等化 | **306.9 秒** | **0 パーセンタイル** | 22 件 |
| E | + F480 足場修正 + 重複削除 | 316.0 秒 | 2 パーセンタイル | **0 件** |
| F | + prewarm 並行化 | 307.9 秒 | **0 パーセンタイル** | **0 件** |
| G | + barrier 撤去 (collection 後) | 320.0 秒 | 3 パーセンタイル | **0 件** |
| **H** | **+ 起動を collection 前へ** | **279.8 秒** | **0 パーセンタイル** | 4 件 |
| **I** | **最終 (H を撤去)** | **321.3 秒** | **4 パーセンタイル** | **0 件** |

**緑の構成 5 走 (D 306.9 / E 316.0 / F 307.9 / G 320.0 / I 321.3) はすべて旧 91 走の下位 4%
に入る。** 5 走が独立に極端値へ入ったので偶然では説明しにくい。
中央値 361.7 秒に対し**約 45 秒 (12%) の短縮**である。

**H の 279.8 秒は旧 91 走の最小値 314.9 秒すら下回る。** 300 秒は到達可能である。

### 効いたもの・効かなかったもの

| 打ち手 | 結果 |
|---|---|
| **配分の所要秒均等化** | **効いた。** 本 wave の短縮のほぼ全部 |
| **prewarm の起動を collection 前へ** | **効いた (279.8 秒)。** ただし赤 4 件で撤去 |
| t080 base の worker 間共有 | **効かない。** 走 A が 51 パーセンタイル = 中央値付近 |
| prewarm の並行化 | **効かない。** 内訳が 215 対 1 |
| barrier 撤去 (collection 後へ背景化) | **効かない。** 窓が +36 秒に膨らむ |
| subreaper 化 | **害。** 44 走緑だったテストを赤に |

### 残り 16 秒の在処 (走 E の shard-0)

| 区間 | 秒 |
|---|---|
| collection | 約 62.6 |
| **collection 終了 → 最初のテスト開始** | **28.3** |
| テスト実行窓 | 225.1 (最長単体 214.0 が支配) |
| **合計** | **316.0** |

**28.3 秒は 48 worker 全員がぴったり同じだけ待っている** (28.28〜28.31 秒、ばらつき 0.03 秒)。
競合ではなく**全テストの前に 1 回だけ走る直列の barrier** である。
shard-1 は 0.09 秒、shard-2 は 0.12 秒でこの barrier が無い。

実体は `orchestrator/tests/conftest.py` の `pytest_collection_finish` (2224 行付近) で、
controller だけが `_prewarm_receipt_memo` と `_prewarm_oracle_environment_memo` を呼ぶ。
どちらも実 repo (lustre) を読む。shard-1 / shard-2 で 0 秒なのは consumer が不在のためである。

**この barrier の内訳を計測したところ、決定的な偏りが出た。**

```
IZANAGI_MEMO_PREWARM_V1 {"barrier_s":28.329, "hook":"xdist_node_collection_finished",
                         "oracle_environment_memo_s":0.132, "receipt_memo_s":28.328}
```

**barrier のほぼ全部 (215 対 1) が `_prewarm_receipt_memo` 1 本である。**

親はまず「2 つの prewarm が逐次だから並行化すれば半分になる」と考えて並行化したが、
**この比では効果が無かった。** 並行化後の走は 307.9 秒で、直前の 316.0 秒との 8 秒差は
走行ごとのばらつきと区別できない。**並行化は無効である。**
ただし同時に足した計測行が上の内訳を出したので、次の一手が確定した。

`_RECEIPT_MEMO.prewarm` は `_PRODUCTION_RESOLVE(root=ROOT)` を呼ぶ。
production の resolver が実 repo (lustre) を走査する費用であり、**production は触れない。**

### 28.3 秒をどこへ置くかで結果が正反対になった (本 wave の最終的な発見)

この 28.3 秒をテスト実行と重ねる実験を 2 通り行い、**置き場所が答えであることが分かった。**

| 走 | 構成 | wall | 開始待ち | 実行窓 | 最長単体 |
|---|---|---|---|---|---|
| F | barrier あり (現状) | 307.9 秒 | 25.5 秒 | 220.6 秒 | 212.6 秒 |
| G | barrier 撤去、**collection 後**に背景化 | 320.0 秒 | **0.1 秒** | **256.7 秒** | **247.6 秒** |
| H | 起動を **collection 前**へ移動 | **279.8 秒** | **0.1 秒** | **217.0 秒** | 208.0 秒 |

- **G:** barrier で節約した 25.4 秒が、実行窓の **+36.1 秒**になって返ってきた。
  prewarm は実 repo (lustre) を走査する I/O で、t080 群も同じ lustre I/O を使う。
  背景化すると両者が競合する。**28.3 秒は「無駄な待ち」ではなく実際の I/O である。**
- **H:** collection (約 63 秒) は import 主体で lustre I/O をあまり使わない。
  そこへ隠すと**実行窓は伸びず** (217.0 秒)、**300 秒を切った。**

**H は本 wave では着地させなかった。** shard-1 / shard-2 に 4 件の赤が出たためである
(入れ子 pytest で prewarm が走り、`result.stderr == ""` を期待するテストへ
`IZANAGI_FREEZE_HOLD` が漏れる等)。consumer の有無は collection 前に確定できないので、
実装は「全 controller で起動する」を選ばざるを得なかった。
本物の受入 shard session だけへ閉じる修正 (`_izanagi_acceptance_shard_spec` で判定) を入れたところ、
今度は probe の入れ子 xdist 走行で worker が crash した。
**本 wave の中では安全に収束しないと判断し、撤去した。**

**次の wave が単独の変更として入れれば安全に着地できる。** 設計も数値も揃っている —
起動位置は `pytest_configure_node`、判定は `_izanagi_acceptance_shard_spec`、
worker 側は cache を最大 120 秒待ち `.pending` / `.failed` marker で失敗を共有する。
残る課題は**入れ子 pytest / probe 経路との共存だけ**である。

---

**以下は撤去に至るまでの記録である。**

**残る手は、この 28.3 秒をテスト実行と重ねることである。**
調べたところ**プロセス跨ぎの共有機構は既に在った** — controller の prewarm は
`tempfile.gettempdir()` 配下の JSON へ書き、worker の `_ReceiptMemo.get` はそれを読む。
cache が無ければ fail-closed で失敗し、いまは barrier がその存在を保証している。
したがって変えるのは 2 点だけである。

1. controller は背景で書き、collection hook を待たせない。
2. worker の `get()` は cache を上限つきで待つ (現行の即時失敗を待ちへ)。

**「cache が無いので既定値」「worker が自分で resolver を呼ぶ」へ倒してはならない。**
production resolver を呼べる唯一の経路が prewarm である性質を壊すためである。

---

以下はそこへ至るまでの実測と、残る打ち手がなぜ裁定を要するかの記録である。

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

## 8b. 配分の均等化は効く。ただし別の族に阻まれる (本 wave の最重要の測定)

`tools/acceptance_shards.py` の `allocate` は重みに **`weight=len(nodeids)`** を使っていた。
件数で均等化しても秒数は均等化されない。実際、件数は 7,800 / 7,800 / 7,799 とそろっているのに、
親が junit から測った直列和は **13,075 / 2,865 / 7,522 秒**で 4.6 倍の開きがあった。

重みを `orchestrator/tests/acceptance_duration_ledger.json` の所要秒へ変えて実走した結果。

| shard | 変更前 wall | 変更後 wall | 変更前 件数 | 変更後 件数 |
|---|---|---|---|---|
| 0 | 334.2 秒 | **306.9 秒** | 7,800 | 9,898 |
| 1 | 214.9 秒 | 306.1 秒 | 7,800 | 6,752 |
| 2 | 225.2 秒 | 296.2 秒 | 7,799 | 6,754 |

**最遅が 334.2 → 306.9 秒。3 shard が約 300 秒でそろう。**
`test_s8b_oracle_driver` の最長単体も 242.0 → 208.1 秒へ下がった
(shard-0 の同居負荷が減ったため)。**300 秒まであと 6.9 秒である。**

**しかし shard-1 で 22 件が赤になった。すべて `orchestrator/tests/test_codex_worker_launch.py`。**

- 抜き取った 6 件はいずれも**旧構成の 54 走すべてで緑**、変更後の 1 走で赤。
- **shard は動いていない** (旧も新も shard-1)。移動ではなく、shard-1 の密度がほぼ倍になったこと
  (wall 214.9 → 306.1 秒) が原因。
- 失敗本文は timeout である。`LauncherReturncodeMismatch: actual rc timeout != expected rc 0`、
  `launcher_budgets: wall='10'`、`loadavg=(63.67, 37.03, 21.43)`。

これは **F480**「絶対 wall-clock を assert するテストが受入全走の並列負荷で非再現の赤になる」族である。
F766 の恒久対応は「上界が検査対象の性質ではなく `subprocess.run` の anti-hang guard だったため、
当該 1 呼び出しの予算を広げて閉じた。**この抜け道は上界が性質そのものである node には無い**」とし、
**契約側の境界変更は受理集合に関わるとして [T-2095] でユーザー裁定へ返している。**

**一度は撤去した。** しかしユーザーが「早くしてほしい。codex に相談して決めてください」と
差し戻したため、裁定へ返さず相談のうえ決めた。

**決定: 足場の上界だけを広げ、配分の均等化を維持する。**

read-only の相談が 22 件を 1 件ずつ現物で判定した結果、
**22 件すべてで上界は検査対象の性質ではなく足場であり、`max_wall` 自体が性質である node は 0 件**
であった。判定基準は「上界を無限大にしたとき test が無意味になるか」である。
これは F766 の先例 (anti-hang guard の予算を広げる) と同型で、**製品の受理規則を変えない**ので
新しい裁定を要しない。

変更したのは `test_codex_worker_launch.py` の内側だけである。外側 watchdog 10 → 60 秒 (21 node)、
`max_wall` 3 / 8 / 10 / 11 → 30 秒 (17 node、互換 4 node の 100 は据え置き)、
manifest lock の待機 2 → 30 秒 (5 箇所)、manifest 生存中追記の観測競争を解放 marker 待ちへ置換。

**保持した性質側の値:** `evidence_grace=0.3`、termination grace、attempts / calls 上限と累積停止、
checker rc=2、sealed-artifact 再計算、receipt bytes 不変、v2 の (100, 0) / (100.001, 2) 境界、
PID 消滅 assert、manifest の生存条件、lock 競合と完全な因果 trace。
**負例 2 つ** (子終了後にしか manifest を追記しない実装 / 排他を外す実装) が変更後も発火することを
静的に確認した。AST 比較で test 関数 166 件・assert 725 件のうち、意図した 5 箇所以外は不変。

**5 分への順序が確定した。F480 族の足場を直してから配分を均す。** 逆にすると均した瞬間に赤になる。

## 8c. 「いらないテスト」は探したが、ほぼ無かった (独立 2 調査が同じ 1 件に収束)

ユーザーの指示は次であった。

> まず高速化を頑張るのはいいけど、**いらないテスト消すのも優先度高い**と思いますよ。
> 技術的負債はなるべく早く消した方がいいよね

**これは「速くするためにテストを削れ」ではない。** D532 と D747 の枠は動いていない。
技術的負債の話として読み、**所要秒を一切見ずに**「消しても検出力が 1 ミリも落ちないと
証明できるテスト」を探した。

2 つの独立した調査が走った。本 wave の相談 (lane=luna) と、並行する repo 肥大掃除 wave の
段 2 plan + 段 3 敵対相談である。**両者は同じ 1 件に収束した。**

| 型 | 掃除 wave | 本 wave (luna) |
|---|---|---|
| 死んだ pin | 0 件 | 0 件 |
| 恒真 | 0 件 | 0 件 |
| 完全重複 | **1 件** | **1 件 (同じ node)** |
| 撤回済み機構 | 0 件 | 0 件 |

走査規模は `orchestrator/tests` の **378 Python file / 15,662 個の `test_` 関数** (AST 走査)。
定数 assertion は 161 か所見つかったが**すべて `assert False`** で、`assert True`、
非空 tuple/list/set 自体の assertion、空の test 本体は 1 つも無かった。

**唯一の削除候補:**

```
削除: orchestrator/tests/test_related_work_search.py:1978
      test_postprocessing_tier_api_remains_outside_executor_scope
残す: orchestrator/tests/test_related_work_search.py:1581
      test_tier_enforcement_remains_outside_registration_executor_scope
```

両者とも引数・decorator・個別 fixture が無く、本文は
`assert not hasattr(search, "validate_tier_analysis")` の 1 文だけ。assertion 集合が等しいので
削除側 ⊆ 残存側が等号で成立する。**test 本文 2 行 + 台帳 1 行 = 124 bytes。**

**結論: 受入が遅いのは死んだテストが溜まっているからではない。** 生きたテストが扱う repo が
育ったからである (§4 の 26 倍)。この 2 調査は「削るものが無い」ことを、件数と走査範囲つきで
確定させた点に価値がある。

**外した候補 (重要):**

- 環境不足による skip を死んだ pin と数えない。
- `test_codex_role_runtime.py::test_runtime_commit_prerequisites_are_available` は
  常時 skip ではなく、D60 が opt-in 発火を規定し、**単純削除を明示的に却下している**。
- AST 一致群は 22〜23 群あるが、**AST 一致は削除数ではなく調査入口である。**
  開いた約 11 群のうち非重複が 10 群で、残り群の意味論的検分は誰もやっていない。
  入力が違う (空白 / 相対 path / NUL)、別モジュールの同名 helper、別の実行入口、といった理由で
  外れる。

## 8d. 意味と価値で判定し直した — 受入の 34.5% は研究成果物を守っていない

ユーザーの指摘で基準を 2 度直した。

> 削るものがない？たとえば **100 円投資して 1 円だけリターンがある投資をやりますか？**
> あなたの言っているのは **1 円でもリターンがあればそこへ無限の資源を投下する**と言っている

> **生きたテスト？意味的に、価値的に判断できないのか？**

**親の従来の基準は 2 重に誤っていた。** (1)「消しても検出力が落ちないか」は安全性の基準であって
投資判断ではない。**検出力がゼロでないことと、毎走その費用を払う価値があることは別である。**
(2)「死んでいない = 生きている = 残す」は機械的な性質の判定であって、価値の判断ではない。

価値の物差しはこのプロジェクトの成果物 3 つとした。
**A = certified 選択結果 / B = proof chain 付き材料レポート / C = 再現可能な試行台帳。**
これに対し **D = 開発・運用の便宜** (AI 作業者の道具、手順の検査) と
**E = 別研究** (認証層比較、文献調査) は、ゼロではないが桁が違う。

### 費用の形

受入 1 走の直列和は **25,745.5 秒 / 351 file / 23,404 node**。
**351 file のうち 292 file (83%) は合計 1,782.3 秒 = 全体の 6.9% しか使っていない。**
安い file をいくら消しても意味がない (D747 の指摘はここでは正しい)。
**上位 35 file が全体の 81.4% を占める。** 判断の対象はここである。

### 判定 (read-only の相談が 35 file を 1 つずつ現物で判定)

| 判定 | file 数 | 秒 |
|---|---|---|
| 毎走必須 | 15 | 5,779.5 |
| **別系列へ** | **12** | **8,187.4** |
| 要分割 | 8 | 6,987.9 (うち移す分 695.7) |

**移せる合計 8,883.1 秒 = 受入全体の 34.5%。**

**別系列へ (12 file):**

| 秒 | file | 何を守っているか |
|---|---|---|
| 2260.3 | `test_run_tests_preflight` | 受入 runner 自身の前検査 |
| 881.5 | `test_check_ai_provenance` | commit の AI 作業者 trailer の監査 |
| 854.1 | `test_codex_worker_launch` | Codex 子の起動・受領証 |
| 844.1 | `test_p3_b4_producer_auth_experiment` | **別研究**の認証層比較 |
| 842.8 | `test_t126_pegasus_tools` | 計算ノード投入の道具 |
| 562.9 | `test_related_work_search` | **別研究**の文献調査 |
| 446.2 | `test_t1259_qsub_env_delivery_probe` | 投入診断 (`diagnostic-only`) |
| 397.1 | `test_spool_fold` | docs 台帳の fold 機構 |
| 388.5 | `test_codex_reasoning_ab` | Codex の reasoning 比較実験 |
| 253.5 | `test_check_docs` | docs の整合検査 |
| 237.6 | `test_run_tests_shards` | 受入の分割機構自身 |
| 218.8 | `test_login_headroom` | login node の資源余裕 |

**毎走側に残るのは 15 file + 分割後の研究側で 3,293 node / 12,071.7 秒。**
anomaly・verifier・証拠再導出、および F485 を捕まえる実行到達 probe は残す。

wall の見込みは **約 268〜298 秒**。ただし**未測定であり 300 秒以内を保証しない**
(最長単体 208.1 秒が床になり、線形には減らない)。

### 実装は現行裁定の下ではできない

- **D532** は「テストの削除・skip・selection の縮小で速くする — 規律 2 に反する。
  検討対象にしない」と明記する。**本案はテストを保存していても、各受入で実行する selection を
  縮小して速くする案であり、却下された形に当たる。**
  「別系列で必ず走る」という条件による例外は本文にない。
- **D711** は「各 shard が同一の全 collection を行ってから担当外を deselect する」
  「`Σ selected_i == U`、各 count = 1」「全 shard で `finished_i == selected_i`」を要求する。
  U を維持して実行だけ省けば等式が破れ、U を縮小すれば等式は成立するが
  **その緑は除外した検査の実行を証明しない。**
  D1728 も「gate 2 (全 shard の `observed_universe` 一致) は現行のまま置き、
  代替述語も新設しない」とする。

**したがって D532 の適用範囲と D711 の受入母集合を、ユーザーが明示的に改訂しない限り実装できない。**

### 別系列の機構は存在しない (作る必要がある)

現物で確認した状態: file / nodeid / `-k` / `-m` の選択走は可能だが、
`run_tests.py:693` は targeting や `-k/-m` を**受入形から外す**。
`test_selection_contract.py` の `SANCTIONED_EXCLUSIONS` は空。
日次系列の実行保証 marker、期限管理する runner、repo 内の CI / cron / timer は
**いずれも見つからない。**

**F485 の教訓は「任意実行という名称」ではなく、11 日間の未実行が何も止めず誰にも露見しなかったこと
である。「日次に走らせる」という散文だけでは再発防止にならない。** 最小限必要なのは次の 5 つ。

1. 外部 scheduler が日次で対象系列を起動し、既存 `tools/run_tests.py` を通す。
2. 対象 commit・系列定義・期待 node 集合・実際の selected / finished・成否・完了時刻を記録する。
   **起動成功や job ID を完走と扱わない。**
3. 「最後の成功から 24 時間」を検査する経路を scheduler 本体とは別に置く。
   未起動・queue 停止・途中死も期限超過として検知する。
4. 赤または期限切れなら、該当道具の新しい版や別研究の結果を**検証済みとして利用できないようにする。**
5. 関連道具を変更したときは、その変更の焦点走にも対象系列を含める
   (参照関係だけの抽出に依存しない。F521 が repo 全体 checker を漏らしている)。

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
