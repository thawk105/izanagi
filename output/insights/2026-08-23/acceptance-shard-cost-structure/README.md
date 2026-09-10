# 受入全走の cost 構造を 1 走から実測し、2 分割の同時投入を生死確認した (2026-08-23)

- wave: `dev-wave-acceptance-shard-dispatch` (branch `worktree-dev-wave-acceptance-shard-dispatch`)
- base main: `4cbaf041`
- 依頼: 「受入全走の高速化。Pegasus で開発中、テストを計算ノードに投げることがある。
  それをいい感じに分割して計算ノードに投げることで受入全走の高速化を試みる」
- 実測環境: Pegasus gen_S 計算ノード (割当 48 CPU)、`-n 48 --dist loadgroup`
- 逐語: 同 directory の `measure1-summary.txt`、および repo 外 job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-shard-dispatch/`
  (`measure1.log` / `measure1-junit.xml` / `groupmap.json` / `fixed.log` /
  `probe2_0.log` / `probe2_1.log` / `probe_both.result` / `analyze3.py` / `make_split.py`)

## 1. D531 / D532 の模型は現規模で成立しなくなっている

D531 (2026-08-18) は `wall = real-repo 直列鎖 + 固定費 約 26 秒` を正本模型とした。
5 日後の本計測では、この模型が予測を外す。

| 量 | 2026-08-18 (D531/D532) | 2026-08-23 (本計測) |
|---|---|---|
| testcase 件数 | 12951 | 14467 (受入形では 14405) |
| pytest wall | 99.35〜122.03 s | **229.41 s** |
| 直列総和 | 2862.9〜4198.2 s | **5364.9 s** (受入形 5349.7 s) |
| `real-repo` 鎖 | 77.53〜94.86 s (69 件) | **103.0 s** (70 件) |
| `s8c-preregistration-candidate` 鎖 | 71.65〜77.54 s (4 件) | **103.0 s** (5 件) |
| `dev-waves-runtime` 鎖 | 15.4〜15.9 s (22 件) | 14.9 s (22 件) |
| 最長単体 (ungrouped) | 54.89 s | **85.46 s** |
| work 下界 = 直列総和 / 48 | 69.4 s | **111.5 s** |
| 実効並列度 | 59% | **48.7%** |
| 固定費 | 26.24 s (差分推定) | **12.86 s (直接実測)** |

2026-08-18 は鎖 90.65 s > work 下界 69.4 s だった。本計測では work 下界 111.5 s > 鎖 103.0 s である。
**ただし「律速が鎖から総 work へ移った」と一般化してはならない。** これは 1 走の観測であり、
junit の duration は共走の競合を含む (D531) ため `直列総和 / 48` は K を跨ぐ下界ではなく
「K=1 の duration を固定した仮想 capacity 指標」にすぎない。103.0 s と 85.46 s も
将来走の硬い床ではなく K=1 の観測値である。段 3 のレンズ A / B が独立にこれを指摘し、親は撤回した。
確かなのは 1 点だけ — **gen_S は 1 job あたり CPU 48 が上限** (D532 が receipt で実測) なので、
単一 job ではこれ以上コアを増やす手段がない。

### 固定費は差分推定でなく直接測った

48 worker を起動し全 file を collection し、テストを 1 件も走らせない走行
(`-k` で全件除外) を計算ノードで実行した。ログは `48/48 workers created`、
`no tests ran in 12.86s`。job Elapse 18 s、外側 wall 37 s。

**固定費 = 12.86 s。** D531 の 26 s は wall と鎖長の差分から推定した値だが、
現規模では直接実測の方が小さい。差分推定を固定費と呼ぶと、鎖以外の遊びを固定費へ混ぜてしまう。

## 2. wall の 46% はどの項でも説明できない

```
wall 229.41 s
  固定費        12.86 s  ( 5.6%)
  work 下界    111.5  s  (48.6%)   <- 直列総和 5349.7 / 48
  排他鎖床     103.0  s            <- work 下界の下に隠れる
  残余         約 105 s  (45.8%)   <- 未解明
```

残余 105 s は、固定費でも、総 work を 48 で割った値でも、排他鎖でも説明できない。
候補は worker 間の競合 (junit の duration は共走の競合を含む — D531)、
tail の遊び、fixture の I/O 競合だが、**本 wave では特定していない**。

## 3. 2 分割の同時投入 — 252 s が 135 s になった

`groupmap.json` (collection 実測) から file と `xdist_group` の二部グラフを作り、
連結成分 (238 file -> 223 成分、最大成分 16 file / 1086.9 s) を最小単位として
junit 所要で LPT 詰めした 2 分割 (各 2682.4 s) を、**2 本同時に** gen_S へ投入した。

| 走行 | 外側 wall | pytest wall | 結果 |
|---|---|---|---|
| K=1 (全 file、単一 job) | **252 s** | 229.41 s | 10 failed (全部 `test_sort_swo_oracle`) |
| K=2 同時 (合計) | **135 s** | — | — |
| └ shard 0 | 135 s | — | 12 failed + 1 error |
| └ shard 1 | 119 s | **94.04 s** | 6424 passed / 10 skipped、rc=0 |

**外側 wall は 252 s から 135 s になった。ただしこれは採否証拠ではない。**
shard 0 で `test_s8b_approved.py` が collection error になり 10 node
(K=1 走での所要 0.0 s) が実行されていないため、**完全集合の走行ではない**。
所要への影響は無視できるが「1.87 倍」は暫定値であり、
D531 が要求する同一 tip・同一 seam・交互・複数回の対測定で確定させる。
さらに本 probe は production 設計と 3 点が異なる (duration-LPT / file 直指定 / barrier 無し)。
`DW-G01` の生死確認としては成立するが、性能の採否根拠にはならない。

そして重要なのは残余の挙動である。

| | 下界 | 実測 | 残余 |
|---|---|---|---|
| K=1 | 12.86 + max(111.5, 103.0) = 124.4 s | 229.41 s | **105 s** |
| K=2 | 12.86 + max(55.7, 103.0) = 115.9 s | 135 s | **約 19 s** |

**この 1 走では、残余 105 s は分割で消えた。** 分割の利得は下界の差 (124.4 - 115.9 = 8.5 s) ではなく
残余の縮小 (105 -> 19 s) が主だったことになる。ただし残余の正体は特定できていないので、
「work 量に比例するから消えた」と断定してはならない。
段 3 のレンズ B は「二つの 103 s 鎖が同じ worker へ載った条件だけでほぼ説明できる」
(`229.41 - 12.86 - 2 x 103.0 = 10.55`) という対抗仮説を出した。親は
`--loadscope-reorder` が件数降順で並べる (`real-repo` 70 件 / `dev-waves-runtime` 22 件 /
`s8c` 5 件) ため初期配布でこの 2 群が同居しにくいことを根拠に PLAUSIBLE 止まりと裁定した。
**確定していない。** 対測定では group から worker への実割付けを記録する。

**ただし床は動かない。** K を 3 以上にしても `max(直列総和/(48K), 103.0)` の 103.0 s は割れない。
排他鎖は D63 の隔離のための直列化であり、分散では消せない。

## 4. 同時実行で本物の事故を 1 件観測した

`test_s8b_floor_campaign.py::test_pilot_resume_rejects_launch_certificate_contamination[certificate-file]`
が `assert repo_before == _real_output_snapshot()` で落ちた。差分は

```
At index 12989 diff: ('dir', 'pegasus-dispatch/515d4818b68a9b2080d17875d379c5d9')
                  != ('file', 'pegasus-dispatch/31c7c08c.../result.json', '6a367482...')
Right contains one more item: ('file', 'task-runs/reports/20260720-20260722_task-efficiency.md', ...)
```

**もう一方の shard の dispatch が repo の `output/pegasus-dispatch/<nonce>/` を書いたのを、
この shard の「実 output tree を snapshot して不変を要求するテスト」が観測した。**

テスト同士の競合ではない。**dispatch 基盤そのものが repo の `output/` を書いている**のが原因で、
K=1 では dispatch が 1 本なので当たらないが、K 本を同時に走らせると必ず当たる。
`dispatch_compute.dispatch()` は `output_root` を引数に取るので、
shard の dispatch artifact を repo 外へ出せば閉じる見込みである。
D686 が指摘した「worktree の外の副作用」とも同じ面である。

## 5. file を直指定して分けてはならない (偽赤の族)

同じ 2 分割走で、`test_s8b_approved.py:31` が
`ModuleNotFoundError: No module named 'tests'`、
`test_profiler_directive.py:341` が `No module named 'codex_roles'` で落ちた。
**単一走では両方緑である。**

pytest へ file を直指定すると `sys.path` の確立が `orchestrator/tests` 指定時と変わる。
`DW-O18` が言う「file 選択走の import path 未確立による偽赤」そのものであり、
**分割の実装は file path を渡す形を採ってはならない。**
正しい形は「全 shard が同一の全 collection を行い、担当外を deselect する」である。
固定費が 12.86 s しかないので、全 collection を K 回払っても費用はほぼ増えない。
この形なら collection 集合が全 shard で同一になるため、
「併合後の実行集合 = 単一走の collection 集合」の証明も易しくなる。

## 6. 恒久除外は効いている — 測定側が受入形を外していた

本計測の 10 件の赤はすべて `test_sort_swo_oracle` である。これは
`orchestrator/test_selection_contract.py` の `SANCTIONED_EXCLUSIONS` に恒久除外として登録済みで、
**除外契約は破れていない**。親の測定走が `--junit-xml` を足したために
`_is_acceptance_run` が False になり、`tools/run_tests.py` の
`exclusions = _PERMANENT_FULL_SUITE_EXCLUSIONS if is_acceptance else ()` で
除外が適用されなかっただけである。

**測定のために受入形を外すと、受入形だけに効く gate も同時に外れる。**
受入の cost を測る走行は、この差を明記しないと除外表の破れと誤診される。
受入形へ補正した値は 14405 件 / 直列総和 5349.7 s (除外分 62 件 / 15.2 s)。

## 7. 反証したもの

- **D244 の「受入全走の分割 — 走行単位が増えると queue 待ちがその回数だけ掛かり総所要は延びる」**
  は逐次投入を前提にしている。**同時**投入では待ちも並列化される (D300 決定 4 と同じ理由)。
  本計測では K=1 の queue 待ちが 8 s、K=2 同時でも合計 135 s に収まった。
  ただし混雑時 (別セッション実測: queue 待ち 13.5 分) に K 本ぶんの空きが同時に要る点は
  新しい費用であり、本 wave では未評価である。
- **親自身の当初仮説「file 単位に割れば collection も K 分の 1」** は誤り。
  login node の実測で全 238 file が 8.15 s、奇数 119 file が 4.48 s、偶数 119 file が 5.93 s
  (合計 10.41 s > 8.15 s)。import の固定費が支配的で分割は sublinear にしか効かない。
- **親自身の当初値「collection 27.54 s」** は cold cache の値だった。warm は 8.15 s。

## 8. 単発 probe を全走への寄与と読み替えない

並行セッションから「`tools/codex_reasoning_ab.py` の `_find_rollout` が unpinned cold で
329.75 s、直列総和の約 6% を占める」という情報が来たが、**全走 junit には現れない**。
`codex_reasoning_ab` の全 367 件の合計は 74.0 s、最長単体は 22.77 s、
全体の最長単体は 85.46 s である。
**単発 probe の値を全走への寄与として読み替えてはならない。** 優先度は全走 junit に
実際に現れる所要で測る。この訂正は並行セッションが [T-1523] として起票した。

---

## 9. 対測定 (段 6) — テスト実行は縮むが、2 本目の shard が毎回ほぼ一定の queue 待ちを引く

同一 branch・受入形・`--force-dispatch` で K=1 / K=2 / K=3 を交互に測った。
tip は `d78977ff` (r1/r2) と `b56fd70f` (r3、テスト 5 件増)。

### 外側 wall

| tag | K | 外側 | job | queue | pytest | 実行件数 |
|---|---|---|---|---|---|---|
| r1k1 | 1 | 218 s | 197 s | 9 s | 187.35 s | 14383 passed |
| r1k2 | 2 | 476 s | — | — | — | 14383 passed |
| r1k3 | 3 | 291 s | — | — | — | 14383 passed |
| r2k1 | 1 | 326 s | 165 s | 147 s | 157.43 s | 14383 passed |
| r3k1 | 1 | 391 s | 359 s | 19 s | 347.45 s | 14388 passed |
| r3k2 | 2 | 495 s | — | — | — | 14388 passed |

### shard 別の 4 層

| session | K | shard | pytest | job | queue | selected / finished |
|---|---|---|---|---|---|---|
| 1f0d5970 | 2 | 0 | 134.13 s | 141 s | **324 s** | 7240 / 7240 |
| 1f0d5970 | 2 | 1 | 138.57 s | 150 s | 8 s | 7239 / 7239 |
| 02854056 | 2 | 0 | 117.25 s | 125 s | **330 s** | 7240 / 7240 |
| 02854056 | 2 | 1 | 127.40 s | 138 s | 21 s | 7239 / 7239 |
| b96bc23f | 2 | 0 | 136.78 s | 151 s | 8 s | 7242 / 7242 |
| b96bc23f | 2 | 1 | 144.99 s | 153 s | **324 s** | 7242 / 7242 |
| 14b31b24 | 3 | 0 | 130.07 s | 142 s | 7 s | 4826 / 4826 |
| 14b31b24 | 3 | 1 | 143.92 s | 155 s | 7 s | 4827 / 4827 |
| 14b31b24 | 3 | 2 | 112.89 s | 121 s | **157 s** | 4826 / 4826 |

### 読み

1. **テスト実行そのものは縮み、しかも安定する。**
   K=1 の pytest wall は **157.43 / 187.35 / 347.45 s** と 2.2 倍ばらつく。
   K=2 の最遅 shard は **138.57 / 127.40 / 144.99 s** で、値も小さく幅も狭い。
   K=3 の最遅は 143.92 s で K=2 を下回らない — 排他鎖 103.0 s + 固定費 12.86 s の床である。
2. **K=2 の一方の shard が毎回ほぼ一定の queue 待ちを引く。** 3 session とも
   **324 / 330 / 324 s** で、値のばらつきが 6 s しかない。混雑の揺らぎというより
   **スケジューラの周期に近い**挙動である。3 標本なので断定はしないが、
   もしそうなら K>=2 は約 325 s の準決定的な追加費用を払うことになり、
   現在の queue 設定では分割が総所要で勝つことはない。
3. **正しさは全 session で完全。** `selected == finished`、shard の和が collection と厳密一致
   (7240+7239 = 14479、7242+7242 = 14484、4826+4827+4826 = 14479)、
   `IZANAGI_EFFECTIVE_SCHEDULER_V1` はちょうど 1 本、rc=0。
4. **同一 tip・同一集合でも pytest wall が 157.43〜347.45 s とばらつく。**
   この noise floor は分割で得られる差 (最遅 shard で 20〜40 s 程度) より大きい。
   **受入の所要を 1 走で比較してはならない。**

### 実装が実害を出した 1 件 (修正済み)

shard の artifact 置き場を `repo.parent` にしたところ、repo が worktree のとき
`.claude/worktrees/` になった。`tools/dev_wave_land.py:123` の
`_CONTROL_CONTAINERS` はそこの子を**すべて git worktree と見なして** `.git` を要求するため、
`.git` を持たない artifact directory を置くと**同じ checkout の全 wave の land が rc=21 で止まる**。
並行 wave の land が実際に拒否されて判明した。
`git rev-parse --git-common-dir` から main repository の parent を導く形へ変え、
land の `_CONTROL_CONTAINERS` を **import して参照する** guard を足した (定数は複製していない)。
修正後の走行で `/work/1/SFC/tanab/.izanagi-acceptance-shards/` に置かれることを実測で確認した。
**「repo の外」という条件だけでは足りず、「別機構が所有を仮定している場所」も避ける必要がある。**
