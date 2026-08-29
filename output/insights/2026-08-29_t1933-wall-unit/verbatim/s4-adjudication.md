# 段4 裁定 — [T-1933] 受入 wall を決めている単体処理の同定

親が段2 プラン (`out/s2-plan.md`)、段3 正しさレンズ (`out/s3-correctness.md` 18 所見)、
段3 実効性レンズ (`out/s3-effectiveness.md` 10 所見) を裁定した。

## 結論

**実装しない。** 段5・段6 を飛ばし `4→7→8→9` とする。実装面の差分ゼロなので D95 の変異 matrix を
免除する。受入全走と land 前検査は免除しない。

同定は**負結果として確定する**。現行 tip・hold 有効の状態で、受入 wall を決めている単体処理は
**存在しない**。ユーザー指示の「同定結果が具体的な処理を 1 つ指し示した場合にだけ短縮を実装する」
という条件は成立していないので、短縮は実装しない。

## 採用した所見 (real)

### R1. `wall − max_occ` は「テストを走らせていない時間」の**上界**であって下限ではない
正しさ所見2、実効性所見1。`tools/acceptance_shards.py:862-872` は phase の `report.duration` を
node ごとに加算するだけである。全 worker の phase 区間の和集合を A、真の全体無稼働時間を N とすると
`|A| >= max_occ` なので `wall − max_occ >= N` である。
`orchestrator/tests/conftest.py:2083-2085` の real-repo lock 取得は `yield` の外側にあり、
lock 待ちは phase duration に入らず、この差分へ混入する。
**親の `measurements.md` の「下限」という記述を撤回する。**

### R2. LPT は実 scheduler の makespan の下界ではない
正しさ所見3、実効性所見4。`xdist/scheduler/loadscope.py:367-402` の実配布は動的補充であり、
LPT との大小関係は定まらない。**親の「LPT でも縮まないなら実 scheduler でも縮まない」を撤回する。**

代わりに、**scheduling model を必要としない定理**だけで論じる。
任意の schedule について `makespan >= 最長 unit の所要` である。
したがって最長 unit を無料にしても、makespan は次に長い unit の所要を下回れない。

### R3. shard-1 / shard-2 の床の範囲を誤記した
正しさ所見5。IQR を範囲として書いていた。正しい値 (K=3、直近 60 走、`analyze14.txt`):
shard-1 は min 52.7 / p25 54.6 / median 55.1 / p75 56.2 / **max 78.7**、
shard-2 は min 53.1 / p25 54.4 / median 54.9 / p75 55.6 / **max 67.0**。
安定しているのは中央域であり、全走ではない。

### R4. collection 回数と universe 件数を誤記した
正しさ所見6。K=3 の 1 走の collection は worker 144 回 + login collection 1 回 = **145 回**である。
universe は **18,895 件** (`observed_universe` の実長)。
親が書いた 18,954 は `login-collection.log` の行数であって item 数ではない。

### R5. 最 busy worker の item 数分布を切り詰めて引用した
正しさ所見8。全 484 走の分布は中央値 **72** で二峰性である
(2/3/5 item が 203 走、72/74/76 item が 222 走)。
「2〜5 node」が成り立つのは **K=3 の直近 117 走 (2 が 26、3 が 41、5 が 50、合計 117/117)** に
限られる。母集合を明示せずに一般化していた。

### R6. 床の伸びを 2 点だけで「非線形」と結論していた
正しさ所見18。**撤回し、多点の実測へ差し替える。**
critical でない shard 675 本 (universe 15,063〜18,895 件) で
`wall − max_occ` を universe 件数へ回帰すると
**傾き 0.00245 秒/件 (= 1,000 件あたり 2.45 秒)、切片 10.5、r 0.490** である。
bucket 中央値は 15,000 件で 46.1 秒、16,000 で 48.5、17,000 で 52.0、
18,000 で 52.3〜53.0、19,000 で 54.7 と単調に増える。
非線形の主張は取り下げ、**この範囲では概ね線形に 1,000 件あたり 2.45 秒**とする。

### R7. hold の opt-in 状態は走の同値キーに入る
正しさ所見10、実効性所見7。`orchestrator/tests/conftest.py:1668-1680` の環境変数で
growth hold は解除できる。同値キーは tested tip・K・worker 数・collection digest だけでは足りない。
**同定結論は「hold 有効」という条件付きである**と明記する。

### R8. T-080 の約 100 秒は「10 本が共有する 1 回の処理」ではない
実効性所見3。`orchestrator/tests/test_s8b_oracle_driver.py:909-927` は process-local cache を
引いた後も毎回 `shutil.copytree(base_root, root, symlinks=True)` で実体コピーを作る。
同:895-903 は「各テストへは独立した実体コピーを渡す」「コピーは共有しない実体でなければならない」と
明記する。**正しくは「共通のコード経路を 10 本が独立に実行している」である。**
親の記述を訂正する。

### R9. 重い node は 2 系統でなく 3 機構
正しさ所見9、段2 プラン。
(i) `test_s8c_preregistration_invariant.py:362-385` の module fixture
(fresh index、`read-tree HEAD`、pathspec なしの `git add -A` (同:205)、`write-tree`、`commit-tree`)、
(ii) `test_s8c_preregistration_predicates.py::test_repository_candidate_uses_real_s8c_budget_module` の
C06 evaluator による到達可能性探索 (`s8c_preregistration_evidence.py:1341-1468`、
`git add` は 4 path 限定)、
(iii) `test_s8b_oracle_driver.py:1022-1254` の repo 実体コピー + submodule add + verify。
(i) と (ii) は別機構である。

### R10. mixed-tip corpus を current-tip 主張へ使っていた
正しさ所見11。**tip を実際に引いて訂正した** (`analyze15.txt`)。
hold 有効の 4 走は同一 tip ではなく **同一 tip の 2 組**である。

| 組 | 走 | tested_main | shard あたり item |
|---|---|---|---:|
| A | `9c62f3e9` (02:36)、`6fbbc43d` (02:24) | `93fcb4663` | 6,299 |
| B | `96dd3976` (02:05)、`ef85f4f2` (01:52) | `c9f868ba` | 6,277 |

4 走とも growth-hold の解除環境変数は未設定 (hold 有効)。
D357 の 3 走要件は満たしていない。**組ごとに 2 走であることを明記する。**

### R11. 「総仕事量律速ではない」は一般化しすぎ
正しさ所見7。host slowdown が全 node を同率に膨らませる交絡がある。
**「この corpus では最 busy worker の occupancy の方が平均 occupancy より wall をよく説明する」に
弱める。** 下記の主結論はこの相関に依存しない。

### R12. 実行しない方がよいこと
実効性所見10。現 regime で `s8c-preregistration-candidate` の `git add -A` を短縮しても
その group は 0.0 秒なので wall は動かない。T-080 の一部だけを同一 worker へ寄せる grouping は
D1260 が既に不採用と確定している。**どちらも実装しない。**

## 不採用にした所見 (scope 外 / 過剰)

### N1. report v2 の phase timeline instrumentation — 本 wave では実装しない
正しさ所見12、実効性所見6・9。
段2 プランは `node_execution` (全 TestReport の setup/call/teardown の開始終了) と
`session_milestones` を恒久 report へ足すことを提案した。親の裁定は**不採用**である。
- `brief.md` の scope は「既存 artifact の事後読取だけ。計測系へ観測を差し込まない」。
- 実効性所見6 が指摘するとおり、mapping だけでも本 wave の負結果は変わらない。
- 実効性所見9・正しさ所見12 のとおり、恒久 telemetry framework が wave の主成果に化ける。
- `CLAUDE.md` 絶対規律5 と `DW-G05`、およびユーザーの過剰実装禁止に反する。
**裁定パッケージとしてユーザーへ返す** (最小形は `node_to_worker` 1 field、
`tools/acceptance_shards.py:999-1022` と closed field 集合 `同:61-66`)。

### N2. `0.9 <= ΔW/ΔU <= 1.1` の x-for-x gate — 採用しない
実効性所見8。この比率条件は段2 プランの独自定義であり、D357 の逐語は
「同一条件 3 走以上・中央値・10% 未満は変化なし」しか要求していない。
full wall を 10% 以上短縮する処理を「単一支配でない」という理由で捨てる gate は過剰である。
**裁定パッケージへ送る。**

### N3. 同定のための新規 full 受入 3 走 — 本 wave では行わない
実効性所見5。`brief.md` は「同定のために新しい full 受入測定を積み増さない」と定めている。
land のための受入全走は行うが、**それを同定の証拠に使わない**。

### N4. 段2 の整合検査 3 件 (正しさ所見15・16・17) — 実装しないので moot
producer 由来値の自己照合、補集合定義による恒真、候補固有でない slack。
N1 を不採用にしたので実装対象にならない。裁定パッケージの注記として残す。

## 反証された疑義 (refuted)

- 正しさ所見1: `testsuite@time` を pytest session wall と読むのは正しい
  (`_pytest/junitxml.py:644-653`)。親の量の定義は妥当。
- 正しさ所見13: 段2 プランに skip / deselect / case 縮小 / assertion 変更 / timeout 緩和は
  紛れていない。
- 正しさ所見14: 段2 の因果確認部分は D1260 / D357 と整合する (hold pin の欠落を除く)。

## 確定した同定結果 (scheduling model に依存しない)

`makespan >= 最長 unit の所要` は定理である。hold 有効の 4 走で、
critical shard (すべて shard-0) の unit 所要分布は次のとおり (`analyze14.txt`)。

| 走 | tested_main | wall | max_occ | 97 秒以上の unit | 77 秒以上の unit | 上位 5 unit |
|---|---|---:|---:|---:|---:|---|
| `9c62f3e9` | `93fcb4663` | 204.8 | 127.6 | 11 | 11 | 126.6 107.3 104.7 100.7 99.5 |
| `6fbbc43d` | `93fcb4663` | 200.2 | 122.6 | 10 | 12 | 111.8 109.1 105.5 104.9 103.8 |
| `96dd3976` | `c9f868ba` | 224.3 | 145.3 | 10 | 20 | 120.5 118.3 113.5 113.0 112.7 |
| `ef85f4f2` | `c9f868ba` | 216.5 | 141.1 | 10 | 22 | 116.0 112.2 108.9 107.4 107.2 |

1. **単一処理は wall を決めていない。** 最長 unit を無料にしても makespan は次の unit を下回れず、
   その差は 2.7〜19.3 秒である。97 秒以上の unit が 10〜11 本あるので、
   makespan を 97 秒未満へ下げるには**10〜11 本を同時に短くする**必要がある。
   77 秒まで含めると 11〜22 本になる。これは定理からの帰結で、scheduler の挙動に依存しない。
2. **したがって D1260 の +0.37% は構造の帰結である。** 6 本を 1 worker へ寄せて memo を
   共有させても、97 秒以上の unit が他に 4〜5 本残る。
3. **wall のうちテスト実行でない部分は、shard-0 で最大 77.2 秒、他 shard で最大 55 秒台**である
   (R1 のとおり上界)。この残差は universe 件数に対し **1,000 件あたり 2.45 秒**で伸びる
   (非 critical shard 675 本、universe 15,063〜18,895 件、r 0.490)。
   内訳は現 artifact では分解できない (R1)。
4. **同定は 1 つの観測欠落で止まっている**: report に nodeid → worker の対応が無い。
   `tools/acceptance_shards.py:800` の `_REPORT_WORKERS` は既に計算されているが出力されない。
5. **結論は hold 有効という条件付きである** (R7)。hold を解除すると
   `s8c-preregistration-candidate` (5 node、実測 118〜267 秒の直列鎖) が単独で makespan を決める。

## 成果物

`output/insights/2026-08-29_t1933-wall-unit/` に上記を記録する。docs-only。
worklog / decisions / failures は `docs/spool/` の fragment で出す。
