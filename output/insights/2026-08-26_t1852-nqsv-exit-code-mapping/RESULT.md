# [T-1852] 実測結果 — NQSV `qstat -J -f` の `Exit Code` は失敗事由を名指ししない

`authority: none` / `default_effect: no-state-change`

実測日: 2026-08-26 (JST)。機体: Pegasus (筑波大 CCS)、queue `gen_S`、project `SFC`。
本書は事実の記録であり、可変状態の正本ではない。

---

## 0. この文書の位置づけ

[T-1852] は「`qstat -J -f` の `Exit Code` が `node_failure` /
`scheduler_external_interruption` のどちらを名指しするか」を確立する作業である。
D1006 が「値と事由の対応表が確立するまで復帰 authority を登録しない」と裁定し、
その対応表を作るのがこの作業だった。

**本 wave は事実確立だけを行い、登録も retry 方針の変更もしていない。**
`S8B_RETRYABLE_FAILURE_REASONS`、`_FLOOR_RECOVERY_AUTHORITIES`、
`FAILURE_REASON_RULES`、`OBSERVED_EXIT_CODE_COUNTS` は 1 byte も変えていない。
登録の可否は [T-1851] / [T-1853] のユーザー裁定に属する。

還元判断: 該当なし (CCBench への還元ではなく、計算環境の事実である)。

---

## 1. 結論

**結論は observed corpus の中だけで述べる。** 誘発できなかった事由の値は否定していない。

1. **観測した 7 点はすべて「job の終わり方」で説明でき、事由を示す成分は 1 つも要らなかった。**
   通常終了 5 点 (`exit` 0 / 7 / 11 / 17 / 255) と signal 死 2 点 (signal 9 と signal 10) が、
   `wait(2)` status の 16 進表記という 1 つの読み方で全部説明できる (§4)。
   **これは実測と整合した仮説であって、全値域についての証明ではない。**
2. **`9` は少なくとも 2 つの異なる事由で出る。** 実行時間超過 (D740 が `wall_timeout` として
   retry 可能事由から明示除外) と、実行中の `qdel` が**同じ `9`** を返した。
   **したがって `9` を見ても、その走行が retry してよいものかは決まらない。**
   ただし後者は**自分が撃った user 発行の削除**であり、D740 の
   `scheduler_external_interruption` そのものではない (§6-2)。
3. **閉集合の 2 事由はどちらも未観測である。** `node_failure` は共有計算環境で誘発できない。
   `scheduler_external_interruption` に当たる operator / scheduler 発行の中断も誘発していない。
   **表の該当欄は空のままにしてあり、推測で埋めていない。**

したがって [T-1852] の問い「どの `Exit Code` がどちらの事由を名指しするか」に対して、
本 wave が実測で言えるのは次の 2 つである。

- **閉集合の 2 事由に対応する値は、1 つも観測できていない。**
- **観測できた範囲では、`Exit Code` は事由でなく終わり方だけを載せており、
  `9` は retry 可否をまたいで衝突する。**

**この surface を分類の根拠にするには、まず 2 事由の実観測が要る。**
値の意味を推測して規則表を書くことは D1006 が却下した形であり、本 wave も行わない。

---

## 2. 実測の環境と手順

- login node `pegasus02`、queue `gen_S` (`Rerun default = No`、`Exclusive submit = OFF`)。
- 投入は背景 job セッションの Bash tool から行った
  (`docs/pegasus-runbook.md` §8 の F49 (ii) 例外)。投入直後に `qstat` で request の可視性を、
  終了後に `.o` / `.e` の実在を確認している。
- 観測は 0.3 秒間隔で `qstat -J -f <request>` と `qstat -f <request>` を撃ち続け、
  全 snapshot を保存する形で行った。**終端の記録は数秒で消えるため (§6)、
  事後に取りに行く形では観測できない。**
- job script と観測 script は repo 外の job dir
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1852-qstat-exit-code/`) に置いた。
  再現に要る逐語は §10 に貼ってある。
- 削除したのは本 wave が投入した request だけである。他 session の job には触れていない。

---

## 3. 対応表 — 誘発した事由と観測値

| # | 誘発した事由 | request | `Exit Code` | `State Transition Reason` | manifest |
|---|---|---|---|---|---|
| E1 | 正常終了 (`exit 0`) | 949561 | `0` | `EXIT` | `evidence/e1_exit0-manifest.md` |
| E2 | job が `exit 7` | 949557 | `700` | `EXIT` | `evidence/e02-exit7-terminal-qstat.txt` (下記註) |
| E9 | job が `exit 11` | 949565 | `B00` | `EXIT` | `evidence/e9_exit11-manifest.md` |
| E14 | job が `exit 17` | 949571 | `1100` | `EXIT` | `evidence/e14_exit17-manifest.md` |
| E10 | job が `exit 255` | 949559 | `FF00` | `EXIT` | `evidence/e10_exit255-manifest.md` |
| E3 | job script が自分に SIGKILL | 949560 | `8900` | `EXIT` | `evidence/e3_sigkill_self-manifest.md` |
| E8 | job script が自分に SIGTERM | 949562 | `0` (終了せず完走) | `EXIT` | `evidence/e8_sigterm_self-manifest.md` |
| E16 | 実行中に外から `qsig -s SIGTERM` | 949587 | `0` (終了せず完走) | `EXIT` | `evidence/e16_qsig_term-manifest.md` |
| E6 | 実行時間超過 (scheduler が SIGKILL) | 949564 | `9` | `EXIT` | `evidence/e6_walltime-manifest.md` |
| E15 | 実行時間超過 (警告値 60 秒を設定した構成) | 949573 | `9` | `EXIT` | `evidence/e15_sigterm_warn-manifest.md` |
| E4 | 実行中に `qdel` | 949566 | `9` | **`DELETE`** | `evidence/e4_qdel_run-manifest.md` |
| E13 | 実行中に `qdel -g 10` (grace 付き) | 949570 | `9` | **`DELETE`** | `evidence/e13_qdel_grace-manifest.md` |
| E11 | 実行開始前に `qdel` | 949569 | **付かない** | `SUBMIT` → `STAGEIN_SUCCESS` まで | `evidence/e11_qdel_early-manifest.md` |
| E17 | 実行中に外から `qsig -s SIGUSR1` | 949588 | `A` | `EXIT` | `evidence/e17_qsig_usr1-manifest.md` |
| — | **node 故障** | — | **未観測** | **未観測** | — |
| — | **operator / scheduler が発行する削除** | — | **未観測** | **未観測** | — |
| — | **保守停止・preemption** | — | **未観測** | **未観測** | — |

**E4 と E6 が同じ `9` を返している**のがこの表の要点である。**両者は事由として別物なのに、
この field 上では同一である。** ただし正確に書くと、E4 は user 発行の `qdel` であって
D740 の `scheduler_external_interruption` そのものではない。したがってこの 2 走が示すのは

- `9` は「実行時間超過」と「実行中の削除」を区別しない、

までであって、「retry 可能事由と不可能事由が衝突する」ことの直接の証明ではない。
**閉集合側の値が未観測である以上、衝突の有無は確定していない。**
言えるのは「`9` を見ても事由は 1 つに定まらない」ことである。

E11 は request が実行に入る前に消えたため、`Exit Code` が `(none)` のまま消滅した。
manifest には `qdel` の発行時刻 (`07:05:00Z`)、最後に存在していた snapshot
(`+1s`、`Exit Code = (none)`)、最初に `does not exist` を返した snapshot (`+2s`) が入っている。
待ち行列で殺された request からは、この surface は何も返さない。

註: E2 は本 wave 最初の生死確認で、観測 harness を組む前に手で投入したため
`qsub` 出力を file に残していない。manifest は無く、終端 snapshot の逐語だけがある。
E2 が支えている事実 (`exit 7` → `700`) は E9 / E14 / E10 が同型で再現しており、
E2 単独に依存する主張は無い。

---

## 4. `Exit Code` の読み方

観測した 7 点は、次の 1 つの読み方で全件説明できた。**「`Exit Code` は `wait(2)` status を
16 進で、接頭辞なし・0 詰めなしで書いたもの」という仮説**である。
**これは 7 点と整合した読み方であって、全値域についての証明ではない。**
未観測の事由がこの規則から外れた値を出す可能性は、本 wave では否定していない。

- job の最上位プロセスが終了コード `n` で終わったとき → `hex(n << 8)`。
  本 wave が n = 0 / 7 / 11 / 17 / 255 の **5 点で確認**した
  (`0` / `700` / `B00` / `1100` / `FF00`)。
- 最上位プロセスが signal `s` で死んだとき → `hex(s)`。
  本 wave が確認したのは signal 9 (`9`、E6 / E15 / E4 / E13) と
  signal 10 (`A`、E17) の **2 点**である。

**16 進であることは E10 と E17 が決めている。** `exit 255` が `FF00` を、
`qsig -s SIGUSR1` (signal 10) が `A` を返した。`FF` も `A` も 10 進表記には現れない字であり、
「10 進で桁を並べている」という読み方はこの 2 点で否定される。

E3 はこの読み方の裏取りになっている。job script が自分に SIGKILL を撃つと `8900` が出た。
`8900` は 16 進で `0x89 << 8`、つまり終了コード 137 = 128 + 9 である。scheduler の stderr は

```text
-bash: line 1: 691903 Killed                  /var/opt/nec/nqsv/jsv/jobfile/0.949560.10/user_script
```

と書いており、**NQSV は job script を `bash` の wrapper 経由で走らせている**ことが分かる。
script が signal で死ぬと wrapper が 137 で終わり、scheduler はその wrapper の status を見る。
一方 scheduler 自身が job を殺す E6 / E4 では wrapper ごと死ぬので、
signal がそのまま (`9`) 出る。

**観測した範囲では、この読み方を超える情報は 1 つも出てこなかった。**
7 点はすべて「job の最上位プロセスがどう終わったか」だけで説明でき、
「なぜ終わらされたか」を示す成分は要らなかった。
**未観測の事由についてこの性質が続くかは、実際に観測するまで分からない。**

---

## 5. 過去の台帳値に §4 の仮説を当てる

`orchestrator/campaign/s8b_scheduler_accounting.py` の `OBSERVED_EXIT_CODE_COUNTS` は
`(none)` 263 / `1100` 4 / `F` 3 / `9` 2 / `A` 1 を「意味未確立の値域」として持っている。
§4 の仮説を当てると次になる。**「再現した」と書いた行だけが本 wave の実測であり、
残りは仮説と整合するという指摘にとどまる。** 実装側の「意味未確立」という扱いは
本 wave では変更していない。

| 値 | 件数 | §4 の仮説による読み | 本 wave での扱い |
|---|---|---|---|
| `(none)` | 263 | 終了 status がまだ提示されていない | **本 wave の全 case が実行中に `(none)` を返した。** ただし「まだ終わっていない」と断定はしない (提示されない他の理由を排除していない) |
| `1100` | 4 | 終了コード 17 | **E14 で再現した** (`exit 17` → `1100`) |
| `F` | 3 | signal 15 (SIGTERM) で死んだ | **未再現。** 仮説と整合するだけである (§8) |
| `9` | 2 | signal 9 (SIGKILL) で死んだ | **E6 / E15 / E4 / E13 で再現した** |
| `A` | 1 | signal 10 (SIGUSR1) で死んだ | **E17 で再現した** (`qsig -s SIGUSR1`) |

`F` と `A` は 2026-08-04 の [T-362] probe (`--accept-sigterm` の mitigation leg と
SIGUSR1 の split-warning leg) の観測であり、その構成が送る signal 番号と一致する。
`A` については本 wave が `qsig -s SIGUSR1` で独立に再現した。`F` は再現できていない
(既定では SIGTERM が job に効かないため。§8)。

`1100` について 1 点だけ正確に書いておく。**`1100` が終了コード 17 の表記であることは
E14 で確定したが、2026-08-15 の台帳で `1100` を出した producer が何だったかは
本 wave では特定していない。** その観測は `Execution Job ID = (none)`・CPU 時間 0 の
2 node request で、本 wave が誘発したどの case とも状況が一致しない。

---

## 6. 事由を名指ししうる唯一の field と、その限界

`qstat -f` (request 単位) には `State Transition Reason` がある。本 wave で観測した語彙は
`SUBMIT` / `STAGEIN_SUCCESS` / `RUN` / `PRERUN_SUCCESS` / `EXIT` / `POSTRUN_SUCCESS` /
`DELETE` の 7 語である (各 case の manifest に、poll 全走で観測した遷移列を入れてある)。
E4 / E13 の `DELETE` と E6 の `EXIT` は**実際に区別できていた**。

**それでも、現在の証拠でこの field を分類の根拠に登録することはできない。** 理由は 3 つある。

1. **閉集合の 2 事由がどの語を出すかが未観測である。** `DELETE` かもしれず、
   まだ見ていない別の語かもしれない。語彙が閉じていない述語は、
   恒真か恒偽のどちらかに倒れる (D1006 が却下した形そのもの)。
2. **`DELETE` は発行者を区別しない。** 本 wave が観測した `DELETE` は
   すべて**自分が撃った `qdel`** による。operator や scheduler が発行する削除が
   同じ語を出すのかは未観測であり、出すとしても
   「user が消した」と「外部要因で消された」を `DELETE` の 1 語では分けられない。
   D740 が要求しているのは外因性の確認であって、削除された事実ではない。
3. **観測窓が約 5〜6 秒しかない** (下記)。

### 終端記録が見えている窓

| case | `Exit Code` が付いた時刻 | request が `qstat` から消えた時刻 | 窓 |
|---|---|---|---|
| E2 (`exit 7`) | +25s | +31s | 約 6 秒 |
| E4 (実行中の `qdel`) | +25s | +30s | 約 5 秒 |
| E6 (実行時間超過) | +73s | +79s | 約 6 秒 |
| E14 (`exit 17`) | +27s | +33s | 約 6 秒 |
| E15 (実行時間超過) | +191s | +197s | 約 6 秒 |
| E16 (`qsig` 後も完走) | +412s | +418s | 約 6 秒 |

(いずれも投入からの経過秒。0.3 秒間隔の連続観測で測った。各 case の manifest に、
「終端値の初観測」「最後に存在した」「最初の does-not-exist」の 3 snapshot を逐語で入れてある。)

request が消えた後は `qstat -J -f` も `qstat -f` も
`does not exist` を返すだけになる (`qstat -T <消えた request>` も `No such request` である)。

**利用者の権限では、消えた後に取りに行く経路が無い。** 正確に書くと次のとおりである。

- `qstat` の usage に履歴用の mode は無い。
- 会計 command は**実在する** (`/opt/nec/nqsv/bin/racctreq`、`racctjob`)。
  ただし本 account から実行すると `sudo: パスワードが必要です` で止まり、
  request 単位の会計記録は読めない。**「命令が無い」のではなく「権限が無い」**である。
- 会計エピローグ (`<script>.e<ID>`) には終了 status が入らない。

したがって**終端記録を取るには、job の終了時刻に張り付いて観測しているしかない。**
権限のある側から `racctreq` を読めるなら話が変わりうるが、それは本 wave では確かめていない。

---

## 7. 実測中に踏んだ fail-open の罠 2 件

どちらも「検査を書いたつもりで何も検査していない」形になるため、記録しておく。
逐語と終了コードは `evidence/qstat-qsub-behaviour-verbatim.md` に取ってある。

1. **`qstat` は存在しない request に対しても終了コード 0 を返す。**
   本文は `Batch Request: 949557.nqsv does not exist on nqsv.` だが、
   終了コードは `0` である。**終了コードで存在を判定すると、常に「在る」になる。**
   本 wave の観測 script は最初この判定を持っており、
   「消えたら止まる」条件が一度も発火しなかった。本文で判定する形に直した。
2. **投入直後、job record が作られる前の窓では `qstat -J -f` が `does not exist` を返す。**
   E14 の poll 1 (`t=+0s`) では `-J -f` が `Batch Job: 949571.nqsv does not exist.` を返す一方、
   同じ snapshot の `-f` は request を `Current State = Queued` で返している
   (`evidence/e14_exit17-manifest.md`)。この窓は短く、E14 では次の poll (`+1s`) から
   `-J -f` も job record を返した。
   **したがって「まだ始まっていない」と「もう消えた」を `-J -f` だけでは区別できない。**
   request 単位の `qstat -f` を併せて見るしかない。

---

## 8. 未観測 — 埋めていないもの

- **node 故障。** 共有計算環境で意図的に起こせない。`Exit Code` も
  `State Transition Reason` も未観測である。
- **operator / scheduler が発行する削除。** 本 wave の `qdel` はすべて user 発行である。
  発行者が違えば同じ値になるのかは未観測。
- **保守停止・preemption による中断。**
- **`F` (signal 15 = SIGTERM) の再現。** signal 側は signal 9 と signal 10 の 2 点を
  実測できた (後者は `qsig -s SIGUSR1` で `A`。§4) が、**SIGTERM だけは job に効かない。**
  外から `qsig -s SIGTERM` を撃った E16 は `qsig` 自体が成功 (rc=0) したにもかかわらず
  job が終了せず、`sleep` を完走して正常終了した。job script 内から自分へ SIGTERM を
  撃った E8 も同じく完走している。既定では SIGTERM が握り潰されており、
  request 記録の `Accept Sigterm = No` がそれに対応する。
  E15 として `--accept-sigterm` と `--warning-signal=elapstim:SIGTERM` を付け、
  `elapstim_req="00:03:00,00:01:00"` (上限 180 秒 / 警告 60 秒) で投入した (request 949573)。
  **警告値は request 属性として記録された** — request 記録の
  `(Per-Req) Elapse Time Limit = Max: 180S Warn: 60S` がそれを示す
  (警告 signal が実際に配送されたかは確認できていない)。
  しかし**同じ記録の `Accept Sigterm` は最後まで `No` のまま**で、警告時点での終了は起きず、
  job は 180 秒の上限超過による SIGKILL で終わった (`Exit Code = 9`、
  `%NQSV(INFO): Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)`)。
  `--accept-sigterm` を渡したのに属性が `No` のままになる理由は**本 wave では特定していない**
  (qsub は syntax error を返さず受理している)。この経路で signal 15 を作れなかったため、
  `F` の再現には至っていない。[T-362] が未実測として残した mitigation leg は、
  この観測の後も未解決である。

---

## 9. 本 wave が変えていないもの

- `orchestrator/campaign/s8b_scheduler_accounting.py` (`FAILURE_REASON_RULES` は空のまま)。
- `orchestrator/campaign/s8b_holdout_admission.py` (`_FLOOR_RECOVERY_AUTHORITIES` は空のまま)。
- `orchestrator/campaign/s8b_attempt_profile.py` (`S8B_RETRYABLE_FAILURE_REASONS`)。
- retry の方針、受理集合、床値 campaign の配線。

**D1006 の判断は本実測で裏付けられた。** 対応表が無いから登録できなかったのではなく、
**`Exit Code` にはそもそも事由が入っていない**ことが分かったので、
この surface を根拠に authority を登録する道は無い。

---

## 10. 逐語 — 再現に要るもの

観測に使った job script は repo 外に置いた。内容は次のとおり
(PBS directive 以外は `sleep` と `exit` だけである)。

`exit` 系 (E1 / E2 / E9 / E10 / E14。`exit` の値だけが違う):

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -N izt1852e9
#PBS -l elapstim_req=00:05:00
echo "E9: script exits 11"
hostname
date -u +%Y-%m-%dT%H:%M:%SZ
sleep 15
exit 11
```

実行時間超過 (E6):

```bash
#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -N izt1852e6
#PBS -l elapstim_req=00:01:00
echo "E6: exceeds per-req elapse time limit"
hostname
date -u +%Y-%m-%dT%H:%M:%SZ
sleep 300
exit 0
```

削除系 (E4 / E11 / E13) は `elapstim_req=00:10:00` で `sleep 400` する job を投入し、
外から `qdel <request>` を撃った。E4 は `Current State = Running` を確認してから 5 秒後、
E11 は投入 2 秒後 (実行開始前)、E13 は投入 40 秒後に `qdel -g 10` を撃った。

投入形は既存の sanctioned な submit script と同じ
`qsub -o <file> -e <file> <script>` である (`tools/pegasus/submit_floor.sh` と同型)。
`-o` / `-e` は repo 外へ向けた。

観測は次の形で、request が消えるまで 0.3 秒ごとに 2 つの qstat を撃ち、
全出力を 1 file へ追記した。

```bash
JF=$(qstat -J -f "$REQID" 2>&1)
RF=$(qstat -f "$REQID" 2>&1)
# 存在判定は終了コードでなく本文の "does not exist" で行う (§7-1)
```

`evidence/` には、各 case について**終端の `Exit Code` が最初に見えた snapshot 1 件**を
`qstat -J -f` と `qstat -f` の両方とも逐語で置いてある。

### scheduler 自身の宣言 (E6、実行時間超過)

`.e` の先頭行:

```text
%NQSV(INFO): Batch job received signal SIGKILL. (Exceeded per-req elapse time limit)
```

会計 block:

```text
Request ID:             949564.nqsv
Started Request Time:   Wed Aug 26 16:01:30 2026
Ended Request Time:     Wed Aug 26 16:02:30 2026
Resources Information:
  Elapse:               64S
  Remaining Elapse:     0S
```

### 同じ位置 (E4、実行中の `qdel`)

```text
Request ID:             949566.nqsv
Started Request Time:   Wed Aug 26 16:01:31 2026
Ended Request Time:     Wed Aug 26 16:01:41 2026
Resources Information:
  Elapse:               14S
  Remaining Elapse:     586S
```

E4 には `%NQSV(INFO)` の行が無く、`Remaining Elapse` も 0 ではない。
**ただしこの 2 つを判定に使ってはいけない。** `.e` は job の投入者が書ける場所に置かれる
file であり、job 自身が書けない surface という要件を満たさない。
D1006 が `qstat` 側を証拠源に選んだ理由がここにある。
