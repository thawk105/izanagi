# [T-2457] A-6 認証の 5 ノード実走 — 73 分が 17 分 37 秒になった。ただし最初の実走は 5 秒で落ちた

**種別: 実行基盤の実機測定。** 本稿が測ったのは、認証の正しさ検査を兄弟ノードへ分割する機構が
実機で動くか、動くとして何分かである。**A-6 の科学的な結論の再現ではない。** [T-2430] は
「反復 attempt は行わない」で A-6 の判定 (`reject`、read-heavy で採用版が stock より 5.78% 遅い) を
閉じており、本稿はその判定を更新しない。本走で付随して得られた性能値は §6 に書くが、
**A-6 の主張の根拠に使ってはならない**。

- 日付: 2026-09-09
- wave: `worktree-dev-wave-t2457-a6-fanout-live` (local main `2143a49c0` から)
- 実走した source commit: `86bcea64e`
- 一次資料: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/`
  配下の attempt `a6-20260909a` (失敗) と `a6-20260909b` (成功)
- 統治する裁定: D1810 (認証の正しさ検査を単一 multi-node request 内の ssh で分割する)

## 0. 何が分かったか

1. **最初の 5 ノード実走は 5 秒で落ちた。原因は D1810 が置いていた暗黙の前提の誤りである。**
   NQSV の `-b 5` は job script を head だけでなく **5 rank すべてで走らせる**。job body は
   1 回だけ走る前提で書かれていたので、rank 1〜4 が同じ compute 結果 file を作ろうとして衝突した。
2. **その前提は [T-2429] の生死確認 2 の誤読に由来する。** 同確認は「job script は job 0 (head) で
   だけ走った」と書いたが、probe は 1 本の要約 file へ書いており rank 0 の内容しか残らない。
   **実測ではなく推論だった。**
3. **最小修正で直った。** rank>0 が即終了しても割当ノードは request に保持され head から ssh が
   通ることを probe で実測し、job body に「job 番号 0 以外は durable path を触らず rc=0 で抜ける」
   gate を足した。
4. **修正後の実走は完走した。所要は 1057 秒 (17 分 37 秒)。** 1 ノードの前回 attempt は 4382 秒
   (73 分 2 秒) だったので **4.15 倍速**である。段 3 の静的見積り「16〜18 分」の帯に入り、
   段 3 敵対相談の再見積り「中心 16〜17 分台、運用 17〜19 分」とも一致した。
5. **48 スレッド・100 万レコードの full-scale 正しさ検査が兄弟ノードで完走した。**
   12 件の検査すべてが `serializable` / `certified` / anomaly 0 で、各 performance 検査は
   1533 万〜1735 万コミットを処理している。[T-2429] が限界として挙げていた
   「full-scale を別ノードで完走させた実測ではない」は閉じた。

## 1. 失敗した実走 — attempt `a6-20260909a` (request `985957.nqsv`)

投入 01:00:25、Started 01:00:41、Ended 01:00:41、Elapse **5 秒**。割当自体は成立していた。

```
    Job Condition:
        Job NO: 0-4 ""
    Number of Jobs = 5
  Execution Hosts(JSVNO):
    bnode071(71) bnode072(72) bnode076(76) bnode080(80) bnode092(92)
```

`job.stderr` の逐語 (5 rank 分の出力が並ぶ):

```
%NQSV(INFO): ------- Output from job:0000 -------
compute result already exists

%NQSV(INFO): ------- Output from job:0001 -------
allocation qstat evidence is not fresh
ln: failed to create hard link '<attempt>/jobs/rr95/compute-result.json': File exists

%NQSV(INFO): ------- Output from job:0002 -------
allocation qstat evidence is not fresh
ln: failed to create hard link '<attempt>/jobs/rr95/compute-result.json': File exists

%NQSV(INFO): ------- Output from job:0003 -------
allocation qstat evidence is not fresh
ln: failed to create hard link '<attempt>/jobs/rr95/compute-result.json': File exists

%NQSV(INFO): ------- Output from job:0004 -------
```

**`compute-result.json` を実際に作ったのは rank 4 で、head ですらなかった。** 逐語:

```
{"schema_version":"paper-story-a2-compute-result/v2","workload":"rr95","driver_rc":1,
 "pbs_jobid":"4:985957.nqsv","current_pin":"511c953"}
```

`allocation-qstat.stderr` の逐語は `Illegal batch_request_identifier value: 4:985957.nqsv`。
各 rank の `PBS_JOBID` は `<job 番号>:<request id>` の形で、job body の `${PBS_JOBID#0:}` は
rank 0 の形しか剥がせない。

この attempt は失敗として durable base に残した (絶対規律 7)。消していない。

## 2. 生死確認 — rank>0 の即終了は割当を壊さない (request `985960.nqsv`)

repo の外に置いた使い捨て probe を `-b 3` で投入した。rank 1・2 は即 `exit 0`、rank 0 だけ
45 秒待ってから兄弟へ ssh した。rank 0 の記録の逐語:

```
rank=0
pbs_jobid=0:985960.nqsv
host=bnode007
nodefile=/var/opt/nec/nqsv/jsv/jobfile/0.985960.10/nodelist
--- nodefile content ---
bnode007
bnode013
bnode018
--- after 45s sleep ---
--- qstat -f (self) ---
  Execution Hosts(JSVNO):
    bnode007(7) bnode013(13) bnode018(18)
--- qstat listing row ---
985960.nqsv     t2457rk  tanab    gen_S       0 RUN -   25.13M     0.00       45 N Y Y    3 
--- ssh to bnode013 ---
bnode013
bf898ddc-1e7e-44ce-8d0b-663c0432017a
/scr
31609
ssh_rc=0
```

**45 秒後も割当は 3 ノードのまま、request は RUN、head から兄弟への ssh は rc=0。**

probe 自身の欠陥を 1 つ明記する。`ssh` が nodefile の標準入力を消費するため、2 台目
(bnode018) は試されていない。1 台で結論は足りるが、「両方の兄弟で確かめた」とは書けない。

## 3. 修正 — job 番号 gate

`tools/pegasus/paper_story_a2_certification.sh` の必須環境検査の直後に置く。

- `PBS_JOBID` が `<canonical な 10 進 job 番号>:<非空 request id>` でなければ `exit 2`。
- job 番号が `0` でなければ、理由を stderr へ 1 行書いて `exit 0`。durable path は 1 つも触らない。
- job 番号が `0` なら従来どおり続行する。既存の `${PBS_JOBID#0:}` と `#PBS -b 1` directive は変えない。

段 6 の敵対レビュー 2 本が検査の穴を 3 件示し、いずれも閉じた — 非 0 rank の負例が durable tree を
3 path しか見ていなかった (job root 配下の全列挙へ)、実機で衝突した `4:` が実走テストに無かった
(parametrize へ追加)、配置検査が形式検査の `if` しか追っていなかった (抜ける分岐全体の位置を固定)。
加えて `[0-9]+` が `00:` を受理して文字列比較で非 0 扱いになる fail-open な分類を、canonical な
`0|[1-9][0-9]*` へ狭めて `exit 2` にした (実機で観測された形は `0:` と `4:` だけで、これは理論上の入力)。

**非 0 rank が出す 1 行の診断は残した。** レビュー A はこれを「durable な `job.stderr` を更新する」
must-fix としたが、親が実測で反証した。NQSV 会計検査の正規表現は `^Request ID:` と `^Group Name:`
の行に錨を打っており (`paper_story_a2_certification.py:91-94`)、この 1 行はどちらにも掛からない。
4 行入った `job.stderr` に対して `finish-group` は rc=0 で受領証を作った。**この 1 行は gate が
実機で発火した唯一の証拠である。**

## 4. 成功した実走 — attempt `a6-20260909b` (request `986046.nqsv`)

| 項目 | 値 |
|---|---|
| Created / Started / Ended | 01:23:25 / 01:24:11 / 01:41:44 JST |
| **Elapse** | **1057 秒 (17 分 37 秒)** |
| queue 待ち | 46 秒 |
| 割当 (5 ノード) | bnode050(50) bnode043(43) bnode081(81) bnode084(84) bnode093(93) |
| head | bnode050、`job_id` `0:986046.nqsv`、boot_id `44f2da91-becf-4ce6-875c-5beee4a8d218` |
| driver_rc | 0 |
| source commit | `86bcea64e` |
| CCBench pin | `511c953` |
| campaign | `paper-story-a2-rr95-paper-story-a6-certification-rr95-a4efd902` |
| campaign lock sha256 | `5812a6d729c51bce49170c0a0d858f83c05aecc8672821db0143a82b25fc26fa` |
| WAL sha256 | `c25e0873f0c5c7309abe904e2ba0bc7d9a8958a2f9b713034f79031f4e786cbf` |
| policy sha256 | `682e0f4ed980b74d509426d8f074f51f5b8062a1ca7cf82cd8dbbaae93c4446a` |
| protocol sha256 | `21427e71793ea744777d11bd90429ce2db1a8d3333ea9e2e0f227ecf377c25dc` (前回実走と同一) |

`policy sha256` は 1 ノードだった前回実走の値 (`8969a7e4…87a8`) と異なる。`scheduler.nodes` を
5 にした変更が policy bytes に入るためで、`scheduler` は protocol の preimage に入らないので
`protocol_sha256` は不変である。**「両方の SHA が前回と同一」と書いた親 brief の記述は誤りで、
段 3 の敵対相談が実測値を添えて訂正した。**

`job.stderr` に並んだ非 head rank の逐語 (gate が 4 rank すべてで発火した証拠):

```
%NQSV(INFO): ------- Output from job:0001 -------
nonzero PBS job number exits without running compute body

%NQSV(INFO): ------- Output from job:0002 -------
nonzero PBS job number exits without running compute body

%NQSV(INFO): ------- Output from job:0003 -------
nonzero PBS job number exits without running compute body

%NQSV(INFO): ------- Output from job:0004 -------
nonzero PBS job number exits without running compute body
```

### 所要の内訳 (campaign WAL の時刻差)

| 工程 | cell 1 (`960e57e1aeba`) | cell 2 (`7134e3303607`) |
|---|---:|---:|
| build | 17.2 秒 | 15.8 秒 |
| legacy 正しさ検査 | 16.5 秒 | 14.3 秒 |
| **head の rep 0 (full-scale)** | **420.6 秒** | **440.0 秒** |
| **兄弟 4 本 (rep 1〜4) の追加分** | **+29.2 秒** | **+21.5 秒** |
| 性能計測 | 16.9 秒 | 16.9 秒 |
| cell 合計 | 500.4 秒 | 508.6 秒 |

campaign 本体 (cell 1 の build 開始〜cell 2 の commit) は 1011.4 秒。job の Elapse 1057 秒との
差 45.6 秒が staging・条件 gate・後始末である。

**兄弟 4 本の rep 1〜4 は、それぞれ 0.02 秒以内に揃って WAL へ着地した。** rep 0 が終わってから
21〜29 秒後である。5 回の検査を直列に回せば 1 cell あたり約 2100 秒かかるところが約 450 秒で
済んでおり、**並列に走ったこと自体が時刻から読める**。

## 5. 実機経路 4 点の証拠と、その読み方の上限

依頼が名指しした 4 点それぞれについて、**成果物のどの field から何が読めるか**を分けて書く。
段 3 の敵対相談が「4 点は成果物 field だけではすべて立証できない」と正しく指摘したので、
推論の連鎖と直接の観測を区別する。

| 観測点 | 直接読めるもの | 推論で言えること | 読めないもの |
|---|---|---|---|
| ssh の到達 | 8 本 (2 cell × 4 rep) の `verify-fanout/<variant>/performance-{1..4}/result.json` が実在し、`result_mac` が head の照合を通った | ssh が通り、兄弟で worker が完走した。通らなければ `verify-remote-unavailable` で reject になる | 成功した worker の実 hostname (成功 result に host field が無い) |
| `PBS_JOBID` の運搬 | head 側の `compute-result.json` の `"pbs_jobid":"0:986046.nqsv"` | 兄弟へ届いた。ssh の remote command は `env PBS_JOBID=<値>` を明示的に載せ (`pipeline.py:826-833`)、worker は無ければ ValueError で止まる (`verify_fanout_worker.py:305-321`)。8 本とも result を返した | 兄弟が受け取った値そのもの |
| `/scr` の単独性 | (成功 field なし) | 通った。worker は `/scr` 直下に job 固有 root を symlink 非追跡で作り、ノード内蔵 lock を取り、実走直前に競合 probe を行う。どれかが失敗すれば result を書かずに終わる | ノード名、mount、scratch path、lock と probe の成功記録 |
| rep 順の WAL | 各 cell の `verify_done` が legacy → rep 0 → 兄弟 4 本の順に並ぶ。rep 番号は遠隔 `result.json` の `"rep"` にある | 取り込みは repetition 順で、最初の失敗で abort する | WAL の各 `verify_done` 行が rep 何番かは payload に無い。**並びは positional evidence である** |

12 件の検査結果 (2 cell × (legacy 1 + performance 5)) はすべて
`verdict=serializable` / `certified=true` / `anomalies=0`。performance の検査は
1533 万〜1735 万コミットを処理した。

## 6. 付随して得られた性能値 — A-6 の判定には使わない

本 attempt は認証 campaign をそのまま走らせたので、性能値も出た。**実行基盤の測定に付随した
副産物であり、[T-2430] が閉じた A-6 の判定を更新しない。** `collect` は行っていないので、
この値は repo の成果物として公開していない。

| cell | genome | 5 標本 (tps) | median |
|---|---|---|---:|
| `rr95-stock` | `BACK_OFF=0, BACKOFF_FIXED=-1` | 10241695, 10291656, 10269344, 10292981, 10236253 | 10,269,344 |
| `rr95-fixed2` | `BACK_OFF=1, BACKOFF_FIXED=2` | 10003117, 9768572, 9721956, 9796985, 9685483 | 9,768,572 |

効果は **−4.876%**。前回 attempt `a6-20260908b` の −5.784% と符号は同じで、大きさも近い。
性能計測は fan-out の対象外で head (bnode050) だけで走り、正しさ検査がすべて終わってから
始まるので、head の CPU が兄弟の検査と重なることはない。

**この値を A-6 の 2 本目の attempt として扱うかはユーザー裁定に返す** (§8)。本稿では扱わない。

## 7. 変異 matrix

probe 走 (全件 SURVIVED 登録で観測 node を集める) を先に行い、その観測集合で本登録して本走した。
本走は **5 件すべて KILLED、期待ノード完全一致、MISMATCH 0、baseline PASSED (69 passed)**。
spec sha256 は `55ca9095ed1c42d542fd24ee0ba4e1d522c6002e12659675e5201adbafd15e63`、
repo HEAD は `0b8c5bfa3`。

| ID | 変異 | 落ちたノード数 | 単独理由性 |
|---|---|---:|---|
| M1 | job 番号の捕捉を捨てて `pbs_job_number=0` にする | 2 | 成立 (非 0 の実走テスト 2 件のみ) |
| M2 | 捕捉値を `10#… % 4` へ写す | 1 | **成立**。実測形 `4:` の実走テスト 1 件だけが落ちる |
| M3 | 非 0 分岐に durable な file 作成を混ぜる | 5 | 不成立 (逐語 pin と同時に落ちる。冗長 gate として明記) |
| M4 | 非 0 分岐だけを durable 検査の後ろへ動かす | 3 | 不成立 (逐語 pin 3 件。**実走テストは 1 件も落ちない**) |
| M5 | 形式検査を `[0-9]+` へ戻す | 5 | 不成立 (逐語 pin と同時に落ちる) |

**M4 が示すことを明記する。** 非 0 分岐だけを後ろへ動かす変異は、実走テストからは 1 件も
見えない。配置を固定する静的 assertion だけがこれを落とす。段 6 レビュー B の指摘どおり、
実走テストと配置 pin は責務が違い、どちらも要る。

**M3・M4・M5 は逐語 pin と実走が同じ変異で同時に落ちる過剰決定である。** 単独理由性は成立せず、
冗長 gate として記録する。単独理由の証拠になるのは M1 と M2 だけである。

### 事前登録の訂正 (erratum、初回結果は消さない)

**変異の事前登録は実装より後になった。** 段 4 の裁定時点では「実装面の差分ゼロ」と判定しており
(`collect` を行わなければ repo を書かないため)、実装の必要は実機の失敗で初めて判明した。
そのため登録は段 6 の fix commit 後になっている。DW-M01 の「実装前に登録する」を満たしていない。
また期待ノードを静的に確定できなかったため、DW-M07 に従って全件 SURVIVED の probe 走
(spec sha256 `b16a0106f3e713315f2b663ae65e827e4aca19ae9d0120d7cb4f264b2752c6c5`) を先に行い、
観測ノードで再登録した。probe 走の結果 (5 件すべて MISMATCH) は消していない。

## 8. 主張の上限 (明記する)

1. **1 attempt・1 workload (rr95)・2 cell の 1 回きりである。** A-2 (`nodes` = 1) や他 workload へ
   一般化しない。
2. **rank 終了後の ssh session が job の cgroup / cpuset に属するかは測っていない。** 段 6 の
   レビュー A が挙げた論点で、`pgrep` による競合 probe は「他の CCBench が走っていないか」を
   見るだけで、scheduler の資源所有を証明しない。**17 分 37 秒という所要も、兄弟側の検査が
   割当の資源保証の下で走ったことを前提にしていない。**
   - **追記 (2026-09-09、[T-2486])。** 本 attempt とは**別の request `986762.nqsv`** (3 ノード) で
     この点だけを測った。結果は
     `output/insights/2026-09-09_t2486-ssh-cgroup-equivalence/README.md`。
     ssh session は rank 側とは別の cgroup object (systemd の login session scope) に入り、
     それは rank の終了とは無関係だった。ただし **per-job の cgroup 境界は rank 側にも無く**、
     cpuset と task affinity はどちらの側も全 48 CPU である。
     **本 attempt (`986046.nqsv`) の観測ではないので、上の記述はそのまま残す。**
     17 分 37 秒は実測 elapsed として不変であり、A-6 の正しさ結論も変わらない
     (D1810 決定 3 は遠隔結果の権威を HMAC に置いており、資源保証に置いていない)。
3. **`/scr` の後始末が失敗しても成功 result からは分からない。** worker は result を publish した
   後に task root を消し、失敗を stderr へ出すだけで、成功経路では永続化しない。
4. **遠隔実行に walltime より短い総 timeout が無い。** ssh の `subprocess.run` に timeout が無く、
   head は全 future の完了を待つ。証拠上の hard bound は 12 時間の walltime だけである。
5. **`collect` (materialize) は行っていない。** 2 本目の A-6 certification を公開していない。
   `tracked_destination` は前回 attempt の leaf を指したままである。
6. **5 ノード割当は 2 回とも 1 分未満で取れた** (16 秒と 46 秒)。混雑時の待ち時間は測っていない。
7. **失敗した attempt `a6-20260909a` の durable root は残っている。** attempt ID を 1 つ消費した。
8. **本稿は A-6 の科学的結論を再現していない。** 測ったのは実行基盤である。

## 9. 裁定パッケージ候補

- rank 終了後の ssh session と rank process の cgroup / cpuset・CPU affinity の実機同値性を、
  遠隔検査の受理条件に含めるか (段 6 レビュー A)。
- 遠隔実行へ walltime より短い総 timeout を入れるか (段 3 相談)。
- 本 attempt の性能値 (−4.876%) を A-6 の 2 本目の attempt として扱うか。扱うなら
  [T-2430] が書いた手順 (attempt 数・停止基準の事前登録、`tracked_destination` の新 leaf) に従う。
- A-2 (rr5 / rr50) の `scheduler.nodes` を 5 にするか。
- `/scr` 後始末の失敗を成功経路でも観測可能にするか。

## 10. 再現条件

| 項目 | 値 |
|---|---|
| 投入 | `tools/pegasus/submit_paper_story_a2_certification.sh --policy orchestrator/campaign/paper_story_a6_certification.v2.json --attempt-id a6-20260909b --ccbench-root <submit-tree>/external/ccbench --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps --third-party-source-root <submit-tree>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src` |
| 投入元 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2457-a6-fanout-live/submit-tree` (detached、`86bcea64e`) |
| 生値 | `<durable base>/a6-20260909b/jobs/rr95/raw/rr95-{stock,fixed2}.json` |
| WAL | 同 `campaigns/paper-story-a2-rr95-paper-story-a6-certification-rr95-a4efd902/runs/wal.jsonl` |
| fan-out 証拠 | 同 `campaigns/.../verify-fanout/<variant>/performance-{1..4}/{task,result}.json` |
| 外からの採取 | wave job dir の `qstat-samples-b.log` (30 秒間隔の `qstat -f`) |
| 生死確認 probe | wave job dir の `probe-rank/` (repo へは入れていない) |
| 段 3 相談・段 6 レビュー | wave job dir の `consult-a.md`、`s6-review-a.md`、`s6-review-b.md`、裁定 `s4-ruling.md` |
| 変異台帳 | wave job dir の `mutation-ledger.json` (本走)、`mutation-probe-ledger.json` (probe 走) |
