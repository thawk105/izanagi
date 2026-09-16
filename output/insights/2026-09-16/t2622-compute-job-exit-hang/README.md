# [T-2622] 計算ノード job が pytest 完了後に終わらない事象 — 原因同定の再調査

authority: none / default_effect: no-state-change

wave = `dev-wave-t2622-compute-job-exit-hang`、基準 commit = `ac472026c`。
目的は**原因の同定だけ**で、防壁・回収処理・機構の追加は scope 外である。
subreaper は採らない (F973)。

---

## 0. 結論 (先に書く)

**確定したのは 1 つである。**

> `--task generic` の単純な `fork` 構造で、子が job の stdout / stderr を**即座に、または 30 秒後に
> 手放しても**、NQSV の会計上の job 終了は子の 75 秒の寿命に対応した。
> **子による job 出力 fd の保持は、この遅延の必要条件ではない。**

**確定しなかったことを同じ強さで書く。**

- NQSV が何を見て request を RUN に留めるか (session / process group / scheduler の追跡集合)
  は**特定していない**。本実験の全記録で `sid == pgid` であり、所属を変えた条件が無いので分離できない。
- **F853 当時の機序は未同定である。** 本実験は FIFO の open で止まった孫を再現していない。
- D1684 の是正 (`start_new_session=True` + `os.killpg`) の各要素の寄与も未分離である。
  **是正そのものは有効であり撤回しない。**
- 依頼が挙げたもう 1 つの容疑者 **directory fsync は、今回の残余の原因ではない**
  (全条件で `result-dir-fsync-complete` の後に `job-run-returned` がある) が、
  **稀な再発の原因としては未棄却**である。

---

## 1. 依頼の前提が成り立っていなかった

依頼は「前 wave が残した `IZANAGI_DISPATCH_JOB_TRACE` が、次の再発時にどの段で止まったかを
与える」を出発点にしていた。**その再発が起きていない。**

| # | 実測 | 値 |
|---|---|---|
| M1 | トレース導入 commit `52e8fe7cf` (2026-09-14 07:44:44 +0900) 以降に終了した計算ノード job | 169 本 |
| M1 | うち `IZANAGI_DISPATCH_JOB_TRACE` 行を持つもの | 159 本 |
| M1 | 持たない 10 本 | worktree `dev-wave-t2582-manifest-measurement-sources` の基底が導入前でコードが無い |
| M1 | **159 本すべての最終事象** | `job-run-returned` (他の最終事象は 0 件) |
| M2 | `Ended Request Time` − `job-run-returned` (秒) | n=159、最小 -1.0 / 中央値 -0.4 / **最大 0.0** |
| M3 | 保存されている全 `izdw-*.e*` (338 本) の `(Ended − Started) / walltime` の最大 | **0.227** (408 / 1800 秒、`888604.nqsv`) |
| M11a | `receipt.json` の `terminal_reason` | **332 件すべてが `scheduler-end-state`** |
| M11a | `overall-timeout` を含む受領証 | **0 件** |
| M15 | task 内訳 (全期間 338 本) | `tests` 202 / `provenance` 130 / `generic` 6 |

`_SignalAbort: signal 15` を含む受領証が 4 件あるが、これは dispatcher が SIGTERM で殺された
2026-09-15 の事故 (非 detached 起動) であって本症状ではない。

**痕跡から原因を同定する経路は行き止まりである。** F853 の実例 (request `979716`) と
F901 の実例 (`982386`) の submission dir はどちらも保存されていない。

---

## 2. 陽性例は F853 の 1 件だけである

当初 F901 も同型の陽性例に数えていたが**取り下げた**。F901 は
「変異が待ち手の deadline 検査を外した結果、待ち手自身が既定 6 時間待機した」事例であり、
pytest 完了後に job が終わらない本症状とは機序が違う。

残る唯一の一次記録 F853 の根本原因欄は次のとおり (逐語)。

> `subprocess.run` の timeout は直接の子 (`bash`) しか kill しない。FIFO の open で block した
> 孫 (heredoc の `python3`) が job の stdout / stderr を掴んだまま残るため、pytest が終わっても
> job が終われない。

**これは観察からの推論であって、分離実験の裏づけを持たない。** 同 F には停止時の PID / fd /
wchan、dispatcher の消滅時刻、fd だけを変えた比較の記載が無い。是正
(D1684 の `start_new_session=True` + timeout 後の `os.killpg`) は所属分離と子孫終了を同時に
変えており、どの要素が効いたかを分けていない。

F973 の実走では subreaper が**孫 6 本**を実際に回収している。子孫が残ること自体は実在する。

---

## 3. 機構の地形 (コード読解)

| # | 事実 | 出所 |
|---|---|---|
| M7 | job script の最終行は `exec "$selected" "$DISPATCHER" --job-run "$REQUEST"` | submission dir の `dispatch.sh` |
| M12 | job 内 dispatcher は隔離 child を `/usr/bin/unshare --user --map-root-user --mount -- <python> -I -c <bootstrap>` として `Popen` する。**`start_new_session` も `stdout` / `stderr` も指定しない** | `dispatch_compute.py` の `Popen` 呼び出し |
| M12 | bootstrap は `os.fork()` 後 `os.waitpid(child_pid, 0)` で**正の pid を指定して直接の子だけ**を待つ。孫以下を列挙して待つ処理は無い | 同 |
| M12 | `unshare` は user / mount namespace だけを作り **PID namespace は作らない** | 同 |
| M6 | **投入側** dispatcher の待機ループは `qstat` 由来の状態が `END` になるまで回る。`result.json` の出現では止まらない | 同 |
| M13 | **per-job cgroup による資源境界は無い** (2026-09-09 実測、`986762.nqsv`)。process が入るのは job 間で共有する NQSV service の cgroup | `docs/pegasus-runbook.md` |
| M13 | 終了した request は約 5〜6 秒で `qstat` から消える | 同 |

**job 内 dispatcher (job の最上位 process) と投入側 dispatcher (login node) は別 process である。**
insight の以前の版はこれを 1 つの鎖に混ぜていた。訂正した。

---

## 4. 容疑者 2 つの扱い

依頼は「`_write_result_replace` 後の上限なし `os.fsync`」と「孤児化した孫 process」を挙げていた。

### 4.1 fsync — 段 1 で refuted としたのは誤りだったので撤回した

親は段 1 で「fsync が返らなければ `result.json` が公開されないので症状と両立しない」として
refuted にした。**これは誤りである。** `_write_result_replace` の順序は
`flush` → file fsync → close → `os.replace` → `result-published` → **`_fsync_dir(path.parent)`**
であり、**result.json は directory fsync より前に公開される**。`_fsync_dir` は
`os.open` → `os.fsync` → `os.close` で上限が無い。

実測の裾 (n=159): file fsync 中央値 19.777 ms / 最大 315.468 ms、
**dir fsync 中央値 1.716 ms / 最大 1633.431 ms**、`result-write-return` → `job-run-returned`
最大 0.042 ms。159 本の観測上限であって、稀な停止の上限ではない。

**今回の実験の残余の原因ではない** — 4 条件すべてで `result-dir-fsync-complete` の後に
`job-run-returned` がある。**稀な再発の原因としては未棄却である。**

### 4.2 孤児化した孫 — fd 保持は必要条件でないと分かった

次節の実験で分けた。

---

## 5. トレースは停止区間を絞るが、原因を一意にはしない

親は段 1 で「`job-run-returned` は正常終了時も hang 時も最後の事象になるので分けられない」と書き、
段 4 で「2 仮説を分ける」と反転させた。**どちらも強すぎた。**

- 最終事象が `result-dir-fsync-start` なら、停止は **`_fsync_dir` 内**に絞れる。
  ただし同関数には `os.open` もあるので、`os.fsync` の syscall 中だとは断定できない。
- 最終事象が `job-run-returned` でも、**それは Python process の終了証拠ではない**。
  `_job_trace` は `print(..., flush=True)` であり、時刻はその書込み完了より前に採られる。
  interpreter 終了処理・stdio の close・scheduler 後処理のどれで止まっても同じ最終行になる。

**トレースは区間を絞る道具であり、識別器ではない。** 次の再発では、トレースに加えて
NQSV 会計・job 内 dispatcher の生存・子孫の状態を同時に採る必要がある (§9)。

---

## 6. 計算ノード実験

痕跡から同定できないので機序を直接測った。**判定表は結果を見る前に固定した** (段 4 裁定 §3)。
probe (`tools/probe_t2622_job_exit.py`、Codex `role=author` 作成、
sha256 `744a2966b369abd11f6669792236ecc372a8e8ee63829807487332ee3b4ae3ac`、15,308 bytes、
**repo へは残さない**) を `--task generic` で 4 条件、直列・detached で投入した。

全条件で親 probe は fork の 5 秒後に正常終了し、子を `wait` しない。
子は 75 秒生きて `os._exit(0)` する。統制条件 D だけ子を作らない。
**4 条件すべて bnode013 で走った。**

### 6.1 結果 (2026-09-16 11:12〜11:17)

| 条件 | 子孫 | 子が job の stdout/stderr を手放す時刻 | request | Elapse | **`Ended Request Time` − `job-run-returned`** |
|---|---|---|---|---|---|
| **D `no-child`** (統制) | 作らない | — | `558.nqsv` | 9S | **-0.076 秒** |
| **A `close-now`** | 75 秒生存 | 即時 | `559.nqsv` | 79S | **69.731 秒** |
| **B `close-30`** | 75 秒生存 | 30 秒 | `560.nqsv` | 79S | **69.586 秒** |
| **C `hold-75`** | 75 秒生存 | 手放さない | `568.nqsv` | 80S | **69.870 秒** |

**A・B・C の最大差は 0.285 秒**である。fd を手放す時刻を 即時・30 秒・手放さない と動かしても、
job の終了時刻は動かない。統制 D との差は約 70 秒である。

子の実寿命を monotonic 値から独立に計算すると A 75.001 秒 / B 75.001 秒 / C 75.001 秒。
条件 A の解放は `t0 + 0.00105` 秒、親の終了は `t0 + 5.00101` 秒で、
**解放は親の終了より 5.0 秒早い**。

### 6.2 事前登録の判定表の erratum

段 4 の判定表は「A≈+75」と書いたが、**時刻原点が曖昧だった**。子の寿命は `t0` 基準、
`J` は親が `t0+5` で終わった後に出る。よって `E − J` の期待値は **約 70 秒**であって 75 秒ではない。
fd 仮説が正しければ B は約 25 秒になるはずだった。

実測は A 69.731 / B 69.586 / C 69.870 で、**3 条件とも「子の寿命 `t0+75` に対応」**する。
B が 25 秒付近に来なかったことが fd 仮説を倒した。**判定の向きは変わらないが、
表の数値は `t0` 基準へ統一して読むべきである。** これを erratum として記録する。

### 6.3 evidence が示す事実 (全 27 記録を照合)

| fd | 参照先・属性 (解放前) |
|---|---|
| 0 | 全条件・全記録で `/dev/null` (`st_dev/st_ino = 5/5`) |
| 1 | `/var/opt/nec/nqsv/jsv/jobfile/0.<request>.10/stdout` (`66310/25166029`) |
| 2 | 同 `stderr` (`66310/25166030`) |
| 3 | 各条件の `evidence/probe-<条件>.jsonl` (device `743766374`、inode は条件ごとに別) |
| 4 | 全記録で readlink が ENOENT / fstat が EBADF — 列挙用の一時 fd |

- 条件 A / B は解放後、fd 1 / 2 が `/dev/null` になり以後変わらない。条件 C は `child-exit` まで
  元の 1 / 2 を保持する。**子に残る fd に元の出力の複製は無い** (device/inode も別)。
  これは子自身の fd についての確認であり、job 内の全 process を列挙した証拠ではない。
- 子の `ppid` は親の終了後 `1` へ変わる (孤児化) が、**`sid` は job のまま**である。
  **ただし全記録で `sid == pgid`** であり、session と process group を分離できない。

### 6.4 言えること・言えないこと

**言える:** 同じ所属を継承したまま生き残った子孫が存命する間、job の会計終了が遅れる。
**子による job 出力 fd の保持はその必要条件ではない。**

**言えない:**

| 代替説明 | 判定 |
|---|---|
| 子が別 fd で元の stdout/stderr を保持していた | **今回の子については棄却できる** (fd 表と probe の操作) |
| session ではなく process group を待っていた | **棄却できない** (全記録で `sid == pgid`、分離処置が無い) |
| NQSV が記録した子孫集合を待っていた | **棄却できない** (追跡集合を観測していない) |
| evidence file の fd 3 を 75 秒保持したことが遅らせた | **棄却できない** (A/B/C は保持、D は非保持。寿命差と連動する) |
| `signal.alarm` が子を殺した | **コードと記録に反する** (子 alarm は 120 秒、子は 75 秒で自ら記録して終了) |
| 会計 daemon の走査周期で揃った | **全面棄却できない** (走査時刻が無い。ただし E が 3 条件とも `child-exit` と同じ秒に入るので、寿命と無関係な粗い走査だけの説明は弱い) |
| 秒単位会計の丸めが 70 秒差を作った | **棄却できる** |
| 固定順・時間帯の交絡 | **棄却できない** (各 1 走、直列。ただし全走 bnode013 なのでノード差は支持されない) |
| D と A/B/C の違いは「子孫の存在」だけ | **成立しない** — fork の有無、子 alarm、fd 3 の保持期間、45/60/75 秒の観測書込みも同時に変わる |

**「700 倍離れているので反復は要らない」という親の主張は取り下げる。** D の残余 -0.076 秒を
分母にした倍率は端数に左右される。言えるのは「約 70 秒の差は秒精度の丸めでは説明できない」まで
であり、再現性・発生頻度・一般的な終端条件は本実験では決まらない。

### 6.5 F853 への反映は supersede であって「誤り」の断定ではない

本実験は F853 の fd 原因説を**弱める**が、当時の機序を反証したことにはならない。
本実験は FIFO の open で止まった孫を再現していないし、session 分離単独も kill 単独も測っていない。
よって台帳へは `docs/failures.md` の運用規則どおり **`supersede 追記`** で反映する
(「同型の事象が新たに起きたら再発、既存エントリの**記述だけが後続の事実で古くなった**なら supersede」)。

---

## 7. 因果の鎖 — どこまで裏づけたか

| 段 | 判定 |
|---|---|
| 1. job script が job 内 dispatcher を `exec` する | **支持** (batch script の process を置換するところまで) |
| 2. job 内 dispatcher は `start_new_session` 無しで `Popen` する → 起動時の所属と fd を継承 | **起動時の継承は支持。** 「全子孫が常に同じ所属」は過剰 — 下流の子が自分で所属や fd を変えることをコードは禁じていない |
| 3. bootstrap は正の pid を指定した `waitpid` で直接の子だけを待つ | **支持** |
| 4. 直接の子より長生きした子孫は孤児化するが所属は残る | **今回の個体では支持。** PID namespace 不使用だけから一般化はできない |
| 5. NQSV は所属に生きた process がある限り RUN に留める | **未支持。** 遅延は支持されるが、判定方式は未分離 |
| 6. 投入側 dispatcher が待ち、期限超過で `overall-timeout` → orphan hold | **条件付きで支持。** 一度見えた request が照会から消えた場合も END 扱いになる。期限は投入時に初期化され RUN 初観測で更新される。hold は `job_may_remain is True` のときだけ立つ |

**前の版の「全段が実測またはコード読解で裏づけ済み」は成立しない。第 5 段が未同定である。**

---

## 8. 仮説ごとの現状 — 「今回の残余」と「再発一般」を分ける

| 仮説 | 今回の約 70 秒の残余について | 将来の再発一般について |
|---|---|---|
| directory fsync | **原因ではない** (全条件で complete 後に `job-run-returned`) | 未棄却 |
| pytest / runner 自身の終了処理 (F846 型) | generic probe は当該経路を通らない | 未検証・未棄却 |
| job 内 dispatcher の interpreter 終了処理 | process の実消滅時刻を採っていない | 未棄却 |
| stdio の write / flush / close | **「job 出力 fd の保持が必要」説は条件 A で棄却** | stdio 停止一般は未棄却 |
| fsync 前後の filesystem I/O | 原因ではない | 未棄却 |
| supervisor 待機・内部 pipe read | `_job_run` は戻っているので原因ではない | 未棄却 |
| NQSV の stage-out / epilogue | 段階別時刻が無い | 未棄却 |
| namespace 後始末 | 子孫存命と分離していない | 未棄却 |
| session / group に基づく終端条件 | **積極的な候補になった** | 方式は未特定 |
| `qstat` 可視性・投入側 poll の誤判定 | **会計上の `Ended − J` も約 70 秒なので、投入側 poll だけでは今回の差を説明できない** | 未棄却 |

F846 は **login node の runner 自身が 23 時間 futex 待ちで生存し続けた**事例であり、
NQSV の job 終端待ちでは説明できない。同 F は根本原因を未特定と明記している。
**両者を同じ型に括らない。**

---

## 9. 次に再発したとき最初に見るもの

1. request ID、実行版 (commit)、task、**投入側 / job 内 dispatcher / runner の PID** を対応づける。
2. 最終 trace と `result.json` の**内容**を見る。**`result.json` は走行開始時にも guard として
   作られるので、存在だけで完了扱いにしない。**
3. job 内 dispatcher の生存、`sid` / `pgid`、子孫の `state` / `wchan` / fd を採る。
   **孤児は元の親の `pgrep -P` では拾えない。**
4. 同時刻の `qstat` 本文と rc、receipt、終了後の会計を保全する。
5. `Ended Request Time` と `job-run-returned` の差を計算する。
   **約 0 秒なら job 内は正常終了しており、遅れは子孫か scheduler 側にある。**

修正候補を選ぶときの証拠の対応は次のとおり (**本 wave は実装しない**)。

- 子孫が残っている → FIFO 待ちを作るテスト / 呼び出し元の契約。
- 最終 trace が `result-dir-fsync-start` 等で止まっている → その局所経路。
- job 内は正常終了・子孫も居ない → scheduler / 投入側の観測経路。

---

## 10. 主張の範囲

- **M1 / M2 / M3 / M11a は同じ保存成果物の集計であり、独立した反証実験ではない。**
- **M5 のとおり post-trace の母集合に受入全走級の job が 1 本も無い** (実 elapse の最大 227 秒)。
  長い受入全走に対する「再発 0 件」は **exposure が 0 件**であり陰性証拠にならない。
- 「再発 0 件」は**保存済みかつ終了済みの標本**に限る。
- F973 の孫 6 本と M2 の残余 0 秒は、版も条件も違うので反証の対にならない。
- 実験は `env_mode=clean` の `generic` job で、`fork` した単純な子 1 本の構造で測った。
  **受入全走の pytest / xdist の子孫構造や F853 当時の構造へ外挿しない。**

---

## 11. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2622-compute-job-exit-hang/` に保全した。
子の逐語は本 dir の `verbatim/` にも複製した。

| file | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief |
| `s1-measurements.md` | 段 1 実測 M1〜M17 の逐語 |
| `s2-plan.md` | 段 2 プラン起草 (read-only codex) |
| `s3-lens-a.md` / `s3-lens-b.md` | 段 3 敵対相談 (機序帰属 / 実験設計と安全) |
| `s4-ruling.md` | 段 4 裁定 (real/refuted、plan v2、安全水準、変異免除の理由) |
| `s6-lens-a.md` / `s6-lens-b.md` | 段 6 敵対レビュー (データ照合 / 因果の鎖と記録) |
| `probe_t2622_job_exit.py` | probe 本体 (364 行、Codex `role=author` 作成、**repo へは残さない**) |
| `probe-*.jsonl` | 4 条件の生データ (本 insight の `evidence/` と同一) |

実験 4 条件の submission dir は wave worktree の `output/pegasus-dispatch/` にあり、
request は `558` / `559` / `560` / `568` の各 `.nqsv` である。

**`verbatim/` は可逆最小正規化を施してある** (`DW-S07`)。Markdown の強制改行に使われていた
**行末空白だけ**を `sed -i 's/[ \t]*$//'` で除去した (可視文字は不変)。原文は job dir 側にあり、
下表の SHA-256 と byte 数で同定できる。

| `verbatim/` の file | 原文の SHA-256 | 原文の bytes |
|---|---|---|
| `s1-brief.md` | `013208446c3016a453faed25451195ee71303114ac6d1331dbb1bd636111b4e6` | 6112 |
| `s1-measurements.md` | `dae03aa6d2f9c7dc1f4563c5a1aba4e54368a3d5fc3e21b8508d3a9fc67c4e36` | 14154 |
| `s2-plan.md` | `2f4a41b75e8c0320131732aa75a10de515cffe5412618f2a9560ac4a27dcd10d` | 13813 |
| `s3-lens-a.md` | `1db65e7f32dbb273cca65acd5486774a928534ffb4c8d0fff1801358b00e41f3` | 17017 |
| `s3-lens-b.md` | `bb335d08048d5e153e0207261dc56e861f7d47330b75e2661eea64e7efa87e80` | 15118 |
| `s4-ruling.md` | `073b54735d250fa1bd01f0e830b68ff8af6bf55293ea47c3080d9e558ec5fb0b` | 10948 |
| `s6-lens-a.md` | `926b00b635edea8dafee39359def09329cd02ec8d164d87515fa8aebe04d978a` | 12382 |
| `s6-lens-b.md` | `6a2f76357c4f66de881f08fddfc9fa4563624f689e7e1146b3b3e25b98de96c9` | 15774 |

---

## 12. 段 6 の敵対レビューで親が直したこと

**棄却した所見は無い。レンズ 2 本の所見はすべて real として採った。**

1. 「session が終端条件」の断定 → 撤回。`sid == pgid` で分離できない。
2. 「F853 の機序は誤り」の断定 → 撤回。supersede に留める。
3. 「通常 file には EOF の概念が無い」→ 撤回。`st_mode` を記録しておらず file 型を確定できない。
   fd 仮説の反証は条件 A に置く。
4. 「事前登録の第 2 行に一致」→ 時刻原点の erratum を明記 (§6.2)。
5. 「700 倍離れているので反復は要らない」→ 撤回。
6. 「bnode013 ほか」→ 4 条件すべて bnode013。
7. 因果の鎖の第 6 段 → 投入側と job 内の dispatcher を分け、request 消失経路・期限更新・
   hold 条件を補った。
8. 「トレースが 2 仮説を分ける」→ 区間を絞るが識別器ではない、へ限定 (§5)。
9. 仮説表 → 「今回の残余」と「再発一般」の 2 列に分けた (§8)。
10. 次の担当者向けの診断順序を追加 (§9)。
