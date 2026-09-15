## 数値の逐語照合

**数値不一致の疑い：refuted / nit。成果物影響：新文面に過小計上・算術誤記は確認できない。**

以下、S＝[certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/tools/pegasus/certify_calibration.sh)、C＝[cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/orchestrator/calibrator/cli.py)。行番号は変更後の現物。

| 計測前の項 | 現物の行 | timeout 指定値の集計 |
|---|---|---:|
| qstat | S:265 | 30 |
| static probe | S:396 | 120 |
| gflags configure/build/install | S:488・494・500 | 3×60＝180 |
| glog configure/build/install | S:553・559・565 | 3×120＝360 |
| third-party copy | S:598–609 | 3×120＝360 |
| pristine 検証 | S:611 | 120 |
| CCBench configure/build | S:694・695 | 2×900＝1800 |
| binary hash / nm | S:698・700 | 60＋60＝120 |
| pre probe | S:742 | 120 |
| perf version / smoke | S:882–905 | 2候補×2×10＝40 |
| **合計** | | **3250** |

perf 候補は [policy.json:19](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/tools/pegasus/policy.json:19) で独立に2件と確認。第1候補の version 成功・smoke 失敗後、第2候補の両方へ進めるため、4回分を数える。

CLI の定数（C:63–66）と予約式（C:220–234）から、

```text
10 + 1200 + p×3×120 + 10×120 + 2×3×120 + 60
= 3190 + 360p
p=5 → 4990
3250 + 4990 + 600 = 8840 > 7200
```

p＝5 は既定の100万→200万→400万→800万→1600万。S:935–945 は点数・反復数を上書きしない。S:783 の凍結値も独立計算で **6610**。CLI 内部予約60秒と wrapper の後処理予約600秒は別項である。

## 禁じた主張の混入

**混入の疑い：refuted / nit。成果物影響：実測や outer timeout を根拠とする包括保証は新文面にない。**

コメント S:7–24 と formula S:784–806 の両方を照合した。

- 186秒・35〜39秒・302秒などによる十分性の主張はない。
- 8840 は明示的に「上限ではない」としている。
- outer timeout が最大経路を包含するとの主張はない。
- accepted 公開物について「残りうる」と限定し、「残らない」「常に残る」とは書いていない。

## 限界の記述の正確さ

**限界の欠落・逆転の疑い：refuted / nit。成果物影響：要求された保証限界はコメントと receipt 用文字列の双方に保持されている。**

未計上として列挙された処理は、すべて現物に存在する。

| 処理 | 存在の根拠 |
|---|---|
| `git status` | S:223・461・525・636 |
| `git worktree add` | S:639 |
| `/proc` 全走査 | S:711–738、走査開始716 |
| worktree 削除 | S:112・992 |
| receipt I/O、`fsync` | C:279–283・302–319、S:842–844 |
| 最大60回の `sleep 1` | S:210–213 |

これらに個別 timeout はない。CLI 内の処理には outer timeout が掛かるが、それによって8840が各処理を積算した実時間上限になるわけではない。

accepted 判定は計測呼出しの正常帰還（C:991–1003）と事後検査の後、C:1017で行われる。例外時の組立ては `status="rejected"`（C:1125–1129）。

一方、公開 C:1067 と正常終了 C:1100 の間には追加処理がある。そこで TERM を受ければ公開物が残りうる。wrapper の非ゼロ処理（S:986–988）と EXIT 清掃（S:108–117）は公開物を撤去しない。新文面の限定は正しい。

## 予約定数の由来

**luna の指摘：real / nit（反映済み）。成果物影響：未実行の720秒を、実行される2群の timeout と誤表示していない。**

現物で検証できた。

1. C:997 は `certify=True` を渡す。
2. [sweep.py:294](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2563-impl/orchestrator/calibrator/sweep.py:294) は certify 時に即 return。
3. small / medium の測定は、その後の301行・306行にある。
4. 予約式 C:232 は引き続き `2*sweep_reps*120` を加える。

したがって、この720秒は certify では実行されない scale 2群に対応する予約項である。S:20–21・801–802 の説明と一致する。

## 旧文面の誤りの説明

**旧内訳の誤り：real / nit（訂正済み）。成果物影響：旧1080秒を build 全体の逐次上限と誤読させる説明は撤回されている。**

旧式は各 command に付く timeout を、各ライブラリ全体に一度だけ付く値のように加算していた。

```text
旧内訳：900 + 60 + 120 = 1080
現物：  1800 + 180 + 360 = 2340
差：1260
```

さらに copy・pristine 検証・計測前probe・qstat・hash/nm・perf の **910秒**が旧内訳にはない。2340＋910＝3250となる。

新文面 S:11–15・788–794 はこの違いを正しく説明し、1080を予約配分の項として残している。

## 総括

**このレビュー範囲で must-fix は0件。新文面を反証する不一致は確認できませんでした。**

数値、未計上処理、未実行の予約項、公開後TERMの限定は現物と一致します。これは保証説明の訂正であり、最大経路を収容する時間式再凍結の完了ではありません。

静的照合と独立算術のみ実施。テスト・計測・編集・commit・push は行っていません。読めなかった path はありません。