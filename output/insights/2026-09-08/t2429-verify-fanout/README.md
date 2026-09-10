# [T-2429] 認証 campaign の正しさ検査を兄弟ノードへ分割する — 生死確認 4 本、裁定、実装、変異

## 結論

- **1 回建てた実行ファイルは、建てたノードとは別のノードで同一 bytes のまま動く** (生死確認 1)。
  A-6 attempt `a6-20260908b` が bnode031 で建てた 4 本 (stock / 採用版 × trace / perf) は共有 `/work` の
  durable cache に certification.json の記録どおりの sha256 で残っており、bnode012 で原本・`/work` 複製・
  `/scr` (ノード内蔵) 複製の 3 か所とも記録値に一致し、trace 版は rc=0 で trace を出し、perf 版は rc=0 で
  trace を出さなかった。
- **1 要求で複数ノードを取り、head から兄弟ノードへ ssh で仕事を届けられる** (生死確認 2)。`-b 2` の
  要求で `PBS_NODEFILE` に 2 ノードが並び、head から兄弟へ BatchMode の ssh が通った。
- **CLI の `-b` は script 内の `#PBS -b` directive に優先する** (生死確認 3)。job body の directive を
  変えずに submitter が渡す `-b $SCHEDULER_NODES` だけでノード数を増やせる。
- **1 ノード要求でもノード一覧ファイルは実在し、自ノード 1 行だけである** (生死確認 4)。`nodes` を 1 の
  ままにした A-2 でも、兄弟 0 台を要求する同じ契約がそのまま成立する。
- 裁定は「配る」を採り、再現可能ビルドは採らない。輸送は単一の multi-node request と ssh である。
  実装は入り、変異 matrix は **17 KILLED / 1 SURVIVED (事前登録した等価変異) / MISMATCH 0** で
  期待ノード完全一致だった。**実機の 5 ノード実走はまだ行っていない。**

## 「ノードを跨いで建て直すと bytes が変わる」の一次資料

D1763 と `output/insights/2026-09-08_t2411-a6-readheavy-submitted/README.md` は「ノードを跨いで
建て直すと bytes が変わることは 2026-09-02 に実測済み」と書く。一次資料を辿ると、実測の本体は
`output/insights/2026-08-31_t1905-b10-formal-run/README.md` (88-108 行) の **「job 固有の作業 path が
binary に混入する」実測** (`.rodata` の `__FILE__` 由来 8 件と RUNPATH、path 非依存化 2 巡で差分が
149 → 56 → 45,454 bytes と収束せず) であり、**別ノード 2 台で建て直して sha256 を突き合わせた生記録は
無い**。正確には「別 job で建て直すと bytes が変わる」が実測で、「別ノード」はその含意である。
含意自体は正しい (別ノードで建てるとは別 job で建てることだから) が、後続文書の言い切りは一次資料より
強い。本 wave はこの点を書き分け、実測で置き換えた。

## 生死確認 1 — 別ノードでの同一 bytes と実走 (job 982835.nqsv)

- 投入 06:53 JST、開始 07:01:12 (Pre-running が約 8 分)、Elapse 9 秒、host **bnode012** (建て元 bnode031)、
  boot_id `1cb51557-9e47-4cab-9deb-6c0b6fdea735`、glibc 2.35、競合 `ycsb_` プロセス 0。
- 対象: `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/cache/contracts/e576e9cd…/<store>/cc/silo/ycsb_silo.exe`

| binary | 記録値 (certification.json) | 原本 / `/work` 複製 / `/scr` 複製 | ldd 未解決 |
|---|---|---|---|
| stock trace | `098cdd82…d25bcbf` | 3 か所とも一致 | 0 |
| stock perf | `d3f94526…8e9e2c` | 3 か所とも一致 | 0 |
| 採用版 trace | `f9eeb78e…675a23b9` | 3 か所とも一致 | 0 |
| 採用版 perf | `98f65c2d…0229c64` | 3 か所とも一致 | 0 |

- 実走 (legacy 構成 `-ycsb_tuple_num=200 -thread_num=4 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=true
  -ycsb_max_ope=5 -extime=1 -clocks_per_us=2100`、`IZANAGI_TRACE_DIR` 設定、`/scr` 複製を実行):

| run | rc | wall | trace file | trace C 行 | stdout の `commit_counts_` |
|---|---|---|---|---|---|
| stock trace | 0 | 1.02 s | 4 | 512,567 | 512,567 (batch 0) |
| 採用版 trace | 0 | 1.01 s | 4 | 503,567 | (同様) |
| stock perf | 0 | 1.02 s | 0 | 0 | 1,523,288 |
| 採用版 perf | 0 | 1.01 s | 0 | 0 | (同様) |

- 動的依存: NEEDED は libstdc++ / libm / libgcc_s / libc のみ。RUNPATH は消滅した
  `/scr/tanab/paper-story-a2-certification/0_982234.nqsv/dependencies/lib` を指すが解決対象が無く無害。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/summary.txt`。

## 生死確認 2 — 2 ノード要求と ssh (job 982842.nqsv)

- `#PBS -b 2`、Elapse 5 秒。head **bnode011**、`PBS_NODEFILE` = `bnode011`, `bnode016`。job script は
  job 0 (head) でだけ走った。
- `ssh -o BatchMode=yes bnode016 'hostname; cat /proc/sys/kernel/random/boot_id'` → `bnode016`、
  `2fc2eb68-e86c-46b1-9f67-b3c3719e2f97`。続けて読もうとした `/work/.../bin/stock-trace.exe` は
  生死確認 1 がまだ走っておらず未作成だったため `ssh_rc=1`。到達と実行は成立している。
- `mpirun` は Intel oneAPI (intelpython) の hydra で、OpenMPI 流の引数を受けない。使わない。
- 計算ノードからの `qsub` は、probe が `/bin/hostname` (binary) を script として渡した誤りで
  `UnicodeDecodeError` になり、可否は未確定。本裁定では使わない。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/multinode-summary.txt`。

## 生死確認 3 — CLI `-b` の優先 (job 982936.nqsv)

- script に `#PBS -b 1` を書いたまま `qsub -b 2` で投入 → `PBS_NODEFILE` は 2 行 (`bnode011`, `bnode015`)、
  Elapse 4 秒。CLI が directive に優先する。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/boverride-summary.txt`。

## 生死確認 4 — 1 ノード要求の `PBS_NODEFILE` (job 982979.nqsv)

- `-b 1` の要求でも `PBS_NODEFILE` (`/var/opt/nec/nqsv/jsv/jobfile/<job>/nodelist`) は実在し、自 host
  1 行だけ (`bnode016`)。nodes=1 の A-2 policy でも job body の nodefile 契約 (兄弟 0 台) が成立する。
- 逐語: `/work/1/SFC/tanab/izanagi-job-evidence/t2429/attempt-001/nodefile1-summary.txt`。

## 裁定 (段 4)

- **配る / 再現可能ビルド:** 配る。主 job が建てて durable cache に置いた trace-enabled binary を兄弟
  ノードが `/work` から読み、ノード内蔵 `/scr` へ同一 bytes で複製して実行する。建て直しは禁止。
- **輸送:** 単一 multi-node request。A-6 policy の `scheduler.nodes` を 1 → 5 にし、job body が
  `PBS_NODEFILE` から兄弟ノード (ちょうど 4 台) を取り `run-workload --verify-fanout-hosts` で渡す。
  head は rep 0 を既存経路で、兄弟 4 ノードで rep 1..4 を ssh 経由で並列に走らせる。legacy (1 回) と
  bench は head だけ。cell の順序 (stock → 採用版) は変えない。
- **束縛 (規律 2):** task.json (build_attempt_id、trace_bin_sha256、tag、rep、flags、clocks_per_us、
  numactl、genome、source / build admission receipt、期待 HEAD、task_sha256) と result.json の echo。
  worker は複製 binary の sha256 一致を要求し、ノード内蔵 lock と pgrep で単独性を確かめ、local と
  同じ repetition executor を走らせる。欠落・不一致・ssh 失敗は `verify-remote-unavailable`
  (indeterminate) であり pass にはならない。verifier の capability は発行 PID に束縛されるため、
  `commit_receipt` に狭い橋 (worker 側 serialize、head 側 admit → PID 束縛・単回使用の evidence) を足す。
- **変えないもの:** reps / records / threads / extime、`verify_done` payload の key、`_raw_cell_from_wal`
  以降の認証判定、A-2 policy (nodes=1 のまま)。`scheduler` は `_protocol_preimage` に入らないので
  `protocol_sha256` は不変、policy bytes の sha256 だけ変わる。変更後の fresh attempt だけが対象で、
  既存成果物は書き換えない。
- **見込み:** 検査の critical path が 10 回 × 約 425 秒から 2 cell × (legacy + 1 rep 分) へ縮み、
  73 分が 16〜18 分程度になる (段 3 レンズ B の見積、未実測)。

## 実装 — 何を作ったか

fan-out は A-6 policy の `scheduler.nodes` を 5 にすることで有効になる。job body が `PBS_NODEFILE` から
兄弟ノードを取り、ちょうど `nodes - 1` 台であることを要求して `run-workload --verify-fanout-hosts` へ
渡す。A-2 は `nodes` を 1 のままにしたので、兄弟 0 台を要求する同じ契約を通って従来どおり 1 ノードで走る。

主 process は performance-tag の repetition のうち rep 0 を自分で走らせ、rep 1 以降を兄弟ノードへ
配る。legacy 検査と性能計測は主ノードだけで走り、cell の順序 (stock から採用版へ) は変えていない。

配る単位は `task.json` で、次を束縛する。

- campaign lock の識別子と enforcement source closure の digest
- `build_attempt_id`、tag、repetition 番号
- trace-enabled 実行ファイルの絶対 path と `trace_bin_sha256`
- workload の flags、`clocks_per_us`、NUMA の起動接頭辞、trace の timeout
- genome、source evidence の受領証、build admission の受領証
- head が local で束縛した compiled source snapshot (兄弟は source tree を読まない)
- task 自身の canonical sha256

worker は次の順に検査してから、local と**同じ repetition executor** を呼ぶ。

1. pipeline と verifier を import する前に、自 checkout の enforcement source closure を実測して
   task の digest と照合する。
2. `/scr` から task root までの各 component を symlink 非追跡で検査する。作れなければ result を
   書かずに非 0 で終わる。
3. 共有 `/work` の実行ファイルを task root へ複製し、複製後の sha256 が `trace_bin_sha256` と
   一致することを要求する。一致しなければ実行しない。ビルドへの fallback は持たない。
4. ノード内蔵の lock を取り、競合ベンチの probe を実走直前に行う。

結果は `result.json` に create-only で書く。head は取り込みの最初に HMAC を照合し、続けて task の
echo (task sha256、build attempt、tag、rep、trace sha) を照合する。1 つでも欠けるか食い違えば
`verify-remote-unavailable` として reject する。取り込みは repetition の順に行い、最初の失敗で
現行と同じ abort を出して後続を WAL に載せない。WAL に出る `verify_done` の key 集合は変えていない
ので、認証側 (`_raw_cell_from_wal` 以降) は 1 行も変えていない。

### 遠隔結果の権威 — なぜ HMAC なのか

verifier の capability は発行した process に束縛されており、別ノードから持ち込めない。最初の実装は
公開情報の canonical hash を再計算する受領証を作ったが、段 6 の敵対レビューが「task を読める同じ uid の
process が `serializable` の result を偽造できる」ことを具体的な入力とともに示した。

そこで、head が repetition ごとに 32 byte の secret を生成し、**task 文書にも argv にも環境変数にも
載せず ssh の標準入力だけ**で worker へ渡す形にした。worker は result の canonical bytes に対する
HMAC を書き、head は取り込みの最初にそれを照合する。secret は head の process 内にしか無く、
repetition ごとに使い捨てる。trace を走らせる子 process には渡さない。

## 段 3 と段 6 が見つけたもの

段 3 (プランへの敵対相談 2 本) の主な所見。

- verifier の capability が発行 process に束縛されているので、遠隔結果をそのまま COMMIT へ渡せない。
- 兄弟ノードには head の一時 worktree にある patched source tree が見えない。放置すると全 cell が
  indeterminate になる実機の blocker だった。
- プランが「ssh は未実測」を根拠に重い案を第一候補にしていた。probe は既に ssh 到達を示していた。
- `scheduler` は protocol の preimage に入らないので、policy に手を入れても `protocol_sha256` は
  変わらない。親 brief の逆の記述は誤りだった。

段 6 (実装への敵対レビュー 2 本 + 焦点再レビュー) の主な所見。

- 受領証が公開 hash の再計算だけで偽造できる。
- verify payload が受領証に束縛されていない。
- 同じ受領証を 2 回受理できる。
- worker の HEAD 照合が実行される bytes を束縛しない。
- ノード内蔵 lock が `/scr` 不可時に共有 filesystem へ落ちる。
- `/scr` 配下の path component を symlink 非追跡で検査していない。

いずれも fix 3 と fix 4 で閉じた。閉じなかったものは次の節に書く。

## 変異 matrix

事前登録は段 4 で 10 件 (M1〜M10)、段 6 の裁定で 6 件 (M11〜M16) と M17 を追加した。本走は
`tools/mutation_harness.py --runner-mode dispatch --detached` で 2 群に分けた。runner argv は
`python3 tools/run_tests.py --force-dispatch <対象 test file> -q -rf`。

| 群 | 対象 test file | baseline | KILLED | SURVIVED | MISMATCH |
|---|---|---|---:|---:|---:|
| A | `test_verify_fanout.py` | PASSED | 15 | 1 | 0 |
| B | `test_paper_story_a2_job_contract.py`, `test_paper_story_a2_certification.py` | PASSED | 2 | 0 | 0 |

**期待ノードは全件で完全一致した。** 生存 1 件は事前登録した等価変異で、harness が SURVIVED を
報告する能力そのものの正例である。

| ID | 変異 | 落ちたノード数 |
|---|---|---:|
| M1 | 複製後の実行ファイルの再照合を外す | 1 |
| M2 | 結果欠落を成功として補う | 1 |
| M3 | 完了順に WAL へ出す | 1 |
| M4 | 受領証側の task 識別子の照合を外す | 1 |
| M5 | 競合テナントの検知を外す | 1 |
| M7 | COMMIT 受領証が素の辞書を受ける | 1 |
| M8 | ノード内蔵ではなく共有 home の lock を使う | 1 |
| M9 | ノード数不一致を致命でなくする | 7 |
| M10 | 兄弟ノード一覧を campaign へ渡さない | 1 |
| M11 | 結果の HMAC 照合を外す | 1 |
| M12b | task 生成関数へ秘密鍵の key を混ぜる | 9 |
| M13a | 走査内の二重受理を許す | 1 |
| M13b | process 内の受領証二重受理を許す | 1 |
| M14 | worker の closure 照合を外す | 1 |
| M15 | `/scr` 不在時に root を作って続行する | 1 |
| M16 | 重複ホストと自ホストを受理する | 2 |
| M17 | path component の symlink 検査を外す | 1 |
| EQ | 受理済み集合への追加を等価な書き方へ置換 | 0 (SURVIVED 期待) |

### 単独理由性が成立しなかった 2 件 (明記する)

- **M9 は 7 ノードを落とす。** 3 つは狙った `test_m9_...` の 3 パラメータだが、残り 4 つは
  `_assert_static_job_contract` を呼ぶテストである。同 helper が job body の字面
  (`nodefile-policy-count` など) を pin しており、その行を消す変異は共有する 4 テストを同時に
  落とす。冗長 gate として明記し、単独変異の証拠からは外す。
- **M12b は 9 ノードを落とす。** 1 つは狙った `test_m12_...`、残り 8 つは同じ task fixture を使う
  worker テストで、worker 側の exact key 検査が余分な key を持つ task を拒否するためである。
  単独理由にはできないが、**「秘密鍵を task 文書に載せない」性質が head 側の key 集合検査と
  worker 側の exact key 検査の 2 層で守られていること自体の証拠**である。

### 事前登録の訂正 (erratum、初回結果は消さない)

- **M12 の初回登録は照準を外していた。** 「秘密鍵を task 文書へ書く」変異を**書き込み地点**
  (`_write_create_only_json(task_path, task)`) へ当てたところ、login probe で赤ノードが 0 件で
  生存した。テストが検査するのは本番の task 生成関数 `_make_verify_fanout_task` が返す key 集合で
  あり、書き込み地点はどのテストからも観測されていなかった。DW-M02 に従い実効 gate である
  生成関数へ M12b として再照準した。**書き込み地点そのものは head 側のテストでは覆われていない。**
  本番では worker の exact key 検査が余分な key を持つ task を fail-closed で拒否する。
- **M9 の再照準 (M9b) は hang 変異になった。** 静的 pin される字面を残したまま
  `expected_siblings` を観測値へ書き換えると、ノード数の検査が素通りして job body が後段で
  block し、login probe が 1800 秒で timeout した。DW-M06 に従い dispatch 本走へは入れず、
  M9 は原形のまま 7 ノードの完全集合で登録した。

## 検査

- 焦点走 (統合 + 修正 4 本の後、16 test file、計算ノード): **1504 passed / 0 failed / 10 skipped**。
- pin 閉包の再検査 (修正 1・2 の後、6 test file): **613 passed / 0 failed / 6 skipped**。
- 変異 matrix: 上表のとおり **17 KILLED / 1 SURVIVED (等価) / MISMATCH 0**。
- 全史 provenance 監査: 新規違反なし。
- 受入全走: 記録 commit を含む最終 tip に対して実施 (結果は worklog)。

## 主張の上限と限界

1. **実機の 5 ノード実走はまだ行っていない。** 73 分から 16 分から 18 分へという見込みは、検査 1 回
   あたり約 425 秒という 1 attempt の実測からの静的な計算である。ssh の到達・`PBS_JOBID` の運搬・
   `/scr` の単独性・repetition 順の WAL は、次の attempt で確かめる。
2. **生死確認の実走は legacy 構成** (4 スレッド・200 tuple・1 秒) であり、48 スレッド・100 万レコードの
   full-scale trace と検査を別ノードで完走させた実測ではない。
3. **生死確認 1 は A-6 の特定 attempt の 4 本、bnode031 から bnode012 への 1 回だけである。** 別の
   toolchain や A-2 の実行ファイルへ無検査で一般化しない。実装は attempt ごとに sha256 を照合する。
4. **worker と contract loader は自分自身を使って自分の checkout を検査する。** head の照合後・worker の
   import 前の窓に同じ uid の別 process が共有 checkout を書き換えれば、この照合は迂回できる。
   複製済み実行ファイルの hash 後 TOCTOU と同族の限界で、単独テナントの前提の外にある。閉じるには
   head 供給の二段 bootstrap という新機構が要るので、本 wave では実装せず限界として書く。
5. **「1 ノード内では並べられない」は CPU を根拠にした判断である。** 検査器は解析段で 16 worker、
   依存グラフ段で ProcessPool を使う。memory 上で 2 本並べられるかは測っていない。
6. **計算ノードから qsub できるかは未確定のまま**である (本設計では使わない)。

## 裁定パッケージ候補

- worker と contract loader の自己検証を head 供給の二段 bootstrap に置き換えるか、
  dirty checkout を脅威 model から明示的に外すか。
- ノード内で検査器を複数並べられるかの memory 実測。
- 2 cell の build を先行させ、12 repetition を同時に投入する campaign lifecycle の再編。
- A-2 (rr5 / rr50) を `nodes` 5 にするか。
- 直前の 62 path campaign lock を歴史閲覧の対象に残すか。
