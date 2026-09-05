# 親の実測 — V-8 の費用内訳 (段 2 plan の訂正を反映した版)

すべて B-10 正式走の既存成果物と、実行中の走行を read-only で読んだもの。**新規の測定投入は
していない。** 一次資料の所在:

- 公式出力 root: `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output`
- 各 campaign の WAL: `<root>/campaigns/<campaign_id>/runs/wal.jsonl`
- 投入証拠 root: `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions`

段 2 plan (`artifacts/t2261-v8-cost/s2-plan.md`) が親 brief の (P1)(P2)(P3) を訂正した。
本書はその訂正を反映済みである。訂正の内容は §6 に明記する。

## 1. campaign run の外側固定費 — job 開始から最初の `build_start` まで

| campaign | workload | job 開始 (JST) | 最初の WAL (JST) | 差 |
|---|---|---|---|---:|
| `068fd2cd` | write-heavy | 09-01 01:26:36 | 09-01 01:26:59 | **23 s** |
| `15e75b3f` | balanced | 09-01 05:02:11 | 09-01 05:02:39 | **28 s** |
| `ed8a676b` | read-heavy | 09-02 01:07:49 | 09-02 01:08:17 | **28 s** |
| `e3de15eb` | write-heavy | 09-01 21:16:42 | 09-01 21:17:20 | **38 s** |
| `143a3f74` | balanced | 09-03 20:30:05 | 09-03 20:30:38 | **33 s** |

**最後の 1 行は現行コードでの実測である。** live job `974207.nqsv` の submit receipt が
`source_commit = c7ed565892cd4aba52d7fa47a7d1da17b117c005` を記録しており、これは本 wave の
起点 local main と同一である。job 開始時刻は `qstat -f 974207.nqsv` の `Started Request Time`。

**この 23-38 秒は `run_campaign()` の固定費そのものではない。** job script の prologue・
python 起動・module import を含む混合区間であり、**per-run 固定費の上限にしかならない。**
33 run を 1 つの job・1 つの process で連続実行するなら、prologue と import は 1 回しか払わない。

**この上限は `do_bench=False` の走行で測ったものである。** B-10 の shape campaign は
`bench_done` を 1 件も出しておらず、perf preflight と `settle()` を通っていない。
bench を有効にする走行では、per-run 固定費に perf preflight (2 候補 x timeout 10 秒 =
最悪約 30 秒) と `settle()` (1 回 20 秒上限、高 CV 再測定を含めて最大 3 回) が加わる。

## 2. 1 行 (1 variant) の費用 R

### 2.1 検査器並列化の前後を同一 variant で比較する — 帰属が確定している

同じ variant `84319b1127a6`、同じ balanced workload、同じ 6 パス構成 (legacy 1 + performance 5)。
**各パスの commit 数も 1-4% しか違わない**ので、所要差は検査対象量の差ではない。

| パス | 並列化前 `15e75b3f` (08-31) | commits | 現行コード `143a3f74` (09-03) | commits |
|---|---:|---:|---:|---:|
| build | 50 s | — | 51 s | — |
| legacy | 28 s | 629,914 | 17 s | 639,048 |
| performance 1 | 321 s | 3,914,759 | 173 s | 4,083,126 |
| performance 2 | 314 s | 4,050,041 | 163 s | 4,110,736 |
| performance 3 | 314 s | 4,074,556 | 167 s | 4,150,200 |
| performance 4 | 330 s | 4,053,699 | 171 s | 4,123,584 |
| performance 5 | 316 s | 4,073,441 | 166 s | 4,096,412 |
| **行全体 (`build_start`→`commit`)** | **1673 s** | | **908 s** | |

performance 1 パスの平均は 319.0 s → 168.0 s で **1.90 倍速**。
1 commit あたり 79.2 マイクロ秒 → 40.9 マイクロ秒。

**908 s は外挿ではなく実測である** (`build_start` 2026-09-03T11:30:38Z →
`commit` 2026-09-03T11:45:46Z)。

**この 1.90 倍は「検査器単体の 2.2 倍」とは別の量である。** 本表は end-to-end の
混合区間 (trace 実行・flush・C 行再計数・parse・検査・tmpdir・WAL) を測っており、
T-2191 が測った検査器単体値を R 全体へ掛けたものではない。

### 2.2 build cache は 33 行の間では効かない

現行コードの `143a3f74` で、2 行目 `602b4ce9c788` の build は 50 秒かかっている
(11:45:49 → 11:46:39)。cache key は `src_token` (preprocess 後の内容 hash) を含むので
(`buildcache.py:624`)、別 wire は別 key になる。さらに正式 S8b materialization は
一意 worktree の絶対 `source_root` を admission preimage に含めるため、
**正式経路では cache hit は起きないと buildcache 自身が明記している**
(`buildcache.py:2312-2318`)。

したがって 33 行の build は (a) でも (b) でも 33 回必要である。cache は run を跨いで効くが、
それは同じ変種を 2 度 build しないという意味であって、33 行を安くしない。

### 2.3 行間費用

`143a3f74` で `commit` (11:45:46) から次の `build_start` (11:45:49) まで **3 秒**。
`15e75b3f` と `e3de15eb` では 2-2.3 秒。これは 1 campaign run の中で行を繋ぐ費用であり、
(a) では払わず (b) では払う。**(a) に有利に働く項である。**

## 3. (b) は 33 行を物理実行しない — 32 行である

`variant_id` は genome と `src_token` だけで決まり、query ordinal・replicate ordinal・
trigger nonce を含まない (`pipeline.py:121-127`)。8c topology では source base と
`m == m_s` の validation 行が同じ wire を持つので、2 行目が `loop.py:522-528` で skip される。

**したがって (b) の物理実行は 32 行である。** §5.3 の意味上の記述は現行実装と一致する。
ただし同節が引く行番号 `loop.py:242-246` は古く、現行位置は `522-528` である。

さらに §3.4 の対応表は `duplicate skip` を「record を発行しない → 当該行以降を tombstoned」に
写しており、**(b) では origin が aborted になる。** これは費用ではなく正しさ側の理由であり、
本 wave の測定はこの判断を動かさない。**(b) は 33 行の成果物を作れないので、
厳密には「同じ成果物あたりの費用」の比較対象になっていない。**

## 4. 倍率の再計算

`J` = job/process の共通費 (33 run を 1 job・1 process で回すなら 1 回)、
`F` = run ごとの固定費、`S` = 条件付きの settle / perf preflight、
`R` = 1 行の費用、`D` = skip された行が skip までに払う費用、`g` = 行間費用。

    (a)  = J + 33 x (F + S + R)
    (b)  = J + F + S + D + 32 x R + 31 x g
    (b*) = J + F + S + 32 x g + 33 x R      (duplicate も実行できると仮定した反実仮想)

    倍率 = (a) / (b) または (a) / (b*)

### 4.1 測った regime での値

現行コード・balanced・`do_bench=False`・6 verify パスの実測 (`F+S <= 33`、`R = 908`、`g = 3`):

    (a)/(b*) = 33 x (33 + 908) / (33 + 33x908 + 32x3) = 31053 / 30093 = 1.032
    (a)/(b)  = 33 x (33 + 908) / (33 + 32x908 + 31x3)  = 31053 / 29182 = 1.064

**約 1.03-1.06 倍。**

### 4.2 P6 の行はもっと安いかもしれない — そのぶん倍率は上がる

B-10 の 1 行は legacy 1 回 + performance 5 回の 6 パスを回している。P6 の trigger 系の
correctness mode は `legacy+S2` であり (`p3_s4_loop_trigger_gating.py:583-600`)、
1 行が legacy 1 パス + S2 1 パスなら R はずっと小さい。現行コードの実測値で組むと

    R = build 50 + legacy 17 + S2 168 = 235 s
    (a)/(b*) = 33 x (33 + 235) / (33 + 33x235) = 8844 / 7788 = 1.136
    (a)/(b)  = 33 x (33 + 235) / (33 + 32x235) = 8844 / 7553 = 1.171

**約 1.14-1.17 倍。**

### 4.3 上限

倍率は `R` について単調減少するので、`R` を最小・`F+S` を最大に取ると上限が出る。

- `R` の下限: 物理実行する行は必ず 2 本の build と少なくとも legacy 1 パス + S2 1 パスを含む。
  現行コードの最小観測は build 50 + legacy 8 + S2 63 = **121 s** (variant `602b4ce9c788`)。
- `F+S` の上限: 測った外側上限 38 s に、bench 有効時の perf preflight 最悪 30 s と
  `settle()` 最大 3 回 x 20 s を足して **128 s**。

    (a)/(b) <= 33 x (128 + 121) / (128 + 32x121) = 8217 / 3999 = 2.05

**したがって倍率の上限は約 2 倍である。** この上限は「bench を有効にして固定費を最大まで
払いながら、行の費用は bench 無しの最小値のまま」という整合しない組合せで作った、
到達不能な上界である。実際の regime では 1.03-1.17 倍である。

## 5. 「33 倍」には 2 通りの読み方があり、片方だけが正しい

§5.3 は 2 つの別々のことを書いている。

1. 「**1 回の `drive()` の戻り値から 33 行を合成してはならない**」— 物理実行 1 回から
   33 record を作る形。これに対しては (a) は確かに **33 倍**である。
2. §11 の (b)「**1 run 内で 33 行を回す**」— 33 行を 1 つの campaign run で物理実行する形。
   これに対して (a) は **1.03-1.17 倍**にしかならない。

**「実行費用が 33 倍」は 1 の読み方でだけ正しい。** そして 1 は既存 WAL の再利用であり、
§5.3 自身が「per-query の物理実行保証が破れる」として退けている形である。**絶対規律 2 が
禁じている形を分母に置いた倍率**であり、実際に選べる択一 (§11 の (b)) との比較ではない。

§11 の V-8 の表は (a) の欄に「実行費用が 33 倍」と書き、(b) の欄に「1 run 内で 33 行を回す」と
書いている。**同じ行の中で分母が入れ替わっている。**

## 6. 段 2 plan が親 brief を訂正した 3 件

- **(P1) は誤りだった。** 「(b) でも 33 行の物理実行がある」と書いたが、現行実装では
  duplicate skip で 32 行になる。分母を過大にし、倍率を小さい側へ誤らせる向きの誤りである。
  本書は §3 と §4 で直した。
- **(P2) は尽きていなかった。** process 起動と import は `run_campaign()` の外であり、
  同一 process なら 33 回払わない。逆に environment attestation・reservation 検査・
  claim root capability・identity binding・campaign lock・WAL repair/replay が抜けていた。
  また「終端 seal」は存在しない (`loop.py:652-654` は log して return するだけ)。
  存在しない seal を F に入れると倍率を大きい側へ誤らせる。
- **(P3) の全体命題は誤りだった。** 検査器単体の 2.2 倍を R 全体へ掛けてはならない。
  本書はそれをせず、同一 variant・同一 commit 数の end-to-end 実測 (1673 s → 908 s) で
  1.90 倍を出している。数学的方向 (R が小さくなるほど倍率は 33 側へ動く) は正しい。
- **(P4) は real だった。** P6 の 33 行 producer は存在せず、事前登録の extime / reps も
  未確定なので、R は protocol 別の帯でしか書けない。

## 7. この測定が保証しないこと

- **正式な P6 protocol の R を測っていない。** 33 行 producer が存在せず
  (`phase3-8c-wiring-design.md:379-380`)、事前登録の extime / reps が未記入である
  (`phase3-8c-preregistration.md:194-206`)。上の R は B-10 の実測と、
  `legacy+S2` の既定パラメータから組んだ帯である。
- **`run_campaign()` の per-run 固定費そのものを分離できていない。** 既存 WAL は最初の
  `build_start` より前を記録しない。分離には新しい計測配線が要るが、本 wave は実装面の
  差分 0 で進めるので行わない。上限で議論している。
- **`settle()` と perf preflight の実費を測っていない。** B-10 の走行は `do_bench=False` で
  両方を通らない。上限 (20 秒 x 最大 3 回、30 秒) は静的な値である。
  login node で `settle()` を計時してはならない — load average の regime が計算ノードと違う。
- **33 個の campaign run を 1 つの job で連続実行できることは、コードの読取りで判定した。**
  実走で確かめていない。判定根拠は `reservation.py:26-55,223-275` (job/boot/deadline の
  再検査だけ) と `campaign_claim.py:383-434` (campaign identity ごとの one-shot claim)。
  ただし現行 `run_campaign()` は `required_s=1` しか要求しないので、33 run 分の walltime を
  確保する責任は外側の controller に残る。
- **live 走行 `974207.nqsv` の `source_commit` は submit receipt の記録である。** 実行体が
  その commit から作られたことを receipt の外で独立に裏取りしてはいない。
