実装可能です。推奨案は「旧 mode2 を削除し、同じ 3 arm のまま明示名 `modeX` へ置換」「gflags/glog は probe 専用 env seam で `/work` から供給」「受理条件・workload・5 rep は維持」です。`verify-deps` の一般経路は意図的に rc=1 のまま残ります。

以下の行番号は現行 checkout  
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe` 基準です。本段では build、pytest、qsub、性能計測を実行していません。

## A. modeX の実装

### A-1. mode2 の置換にする

第 4 arm は足さず、旧 `mode2` を `modeX` で置換する。

- brief 自体が「不成立 mode2 の置き換え」と定義している。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/brief.md:7-8`
- 現 driver は 3 arm × 5 rep × 2 workload = 30 performance run である。`tools/pegasus/probes/t139_positive_control_probe.sh:52-75`
- 第 4 arm にすると performance は 40 run、liveness は 384 worker-cell、nm build は 8 本になり、P3 の 288/288 と整合しない。現行 288 は 2 workload × 3 arm × 48 worker から生じる。`tools/pegasus/probes/t139_positive_control_probe.sh:35-45,49-60`
- 旧 mode2 の位置づけまで新たに受理条件へ入れる必要が生じ、事前登録する問いそのものが変わる。

名前も流用せず、macro・arm・symbol を一貫して `modeX` へ変える。これにより前回 mode2 の raw と今回の候補を誤認しない。

### A-2. patch の変更箇所

対象は [t139_positive_control.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control.patch:8) の 2 ハンク。

1. `tools/pegasus/probes/t139_positive_control.patch:8-38`

   - `IZANAGI_T139_PC_MODE2` を `IZANAGI_T139_PC_MODEX` に改名。
   - 排他 `#error` も MODE1/MODEX に変更。
   - `<array>`、`<mutex>` に加え `<cstdint>` を include。
   - padding なしの `std::array<std::mutex, 2>` を、要素ごとに整列する wrapper 配列へ置換。
   - `izanagi_t139_pc_mode2_identity` を `izanagi_t139_pc_modex_identity` に変更。
   - modeX branch 内に bounded suffix mixer を置く。

2. `tools/pegasus/probes/t139_positive_control.patch:70-84`

   - key 全体を回る FNV 風 loop を削除。
   - `stripe_for(storage_, key_)` を 1 回呼ぶ。
   - `gates[stripe].mutex` の lock 中に、現行と同じ CAS 式を 1 回だけ置く。

具体形は次とする。

```cpp
struct alignas(64) StripeGate {
  std::mutex mutex;
};

static_assert(alignof(StripeGate) >= 64);
static_assert(sizeof(StripeGate) % 64 == 0);

std::array<StripeGate, 2> gates;

inline std::size_t stripe_for(Storage storage,
                              const std::string& key) noexcept {
  constexpr std::size_t kTailBytes = 8;
  const std::size_t count =
      key.size() < kTailBytes ? key.size() : kTailBytes;
  const std::size_t begin = key.size() - count;

  std::uint64_t value = 0;
  for (std::size_t i = begin; i < key.size(); ++i) {
    value = (value << 8) | static_cast<unsigned char>(key[i]);
  }

  value ^= static_cast<std::uint64_t>(storage)
           * 0x9e3779b97f4a7c15ULL;
  value ^= static_cast<std::uint64_t>(key.size())
           * 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 30;
  value *= 0xbf58476d1ce4e5b9ULL;
  value ^= value >> 27;
  value *= 0x94d049bb133111ebULL;
  value ^= value >> 31;
  return static_cast<std::size_t>(value & 1U);
}
```

この loop は最大 8 iteration なので key 長に対して O(1)。短い key は全 byte、空 key は 0 byte、8 byte 超は末尾 8 byteだけを読む。`std::string` は NUL を含む binary key でも扱える。key の実体型は `std::string` である。`external/ccbench/include/op_element.hh:16-21`

YCSB は 8 byte 全体が big-endian key なので、YCSB では全 identity byte が mixer に入る。`external/ccbench/include/ycsb.hh:44-48`、`external/ccbench/include/workload.hh:17-27`

一方、この `transaction.cc` は ycsb 専用ではなく、同じ source が tpcc/bomb/sbomb にも使われる。`external/ccbench/cc/silo/CMakeLists.txt:1-3`。TPCC には 16 byte key もある。`external/ccbench/include/tpcc/tpcc_tx_neworder.hh:112-115`。したがって `key.size()==8` の assert や末尾への無条件 8-byte load は入れない。

長い key では同じ suffix を持つ異なる record が衝突しうるが、2 stripe なので衝突自体は必然であり、正しさには影響しない。必要なのは「同じ `(storage,key)` が常に同じ stripe へ行く」安定性であって、単射ではない。

### A-3. record address を使わない理由

stripe は `(storage_, key_)` の値だけから決める。`rcdptr_`、`&key_`、`key_.data()` は使わない。

- logical identity は `storage_` と `key_` で保持されている。`external/ccbench/include/op_element.hh:19-21`
- pointer の下位 bit は alignment により常に同じになりやすく、2 stripe が実質 1 stripeになる。
- allocator、ASLR、再配置、別 run により同じ logical record の address が変わり、再現可能な mapping にならない。
- address を使わなくても、最終的な排他は record 自身の CAS が担うため、stripe collision は並列性だけを下げる。

### A-4. cache-line 分離

`alignas(64)` を wrapper struct に付ける。配列全体だけを `alignas(64)` にしても、内部の 2 mutex 間隔は広がらないため不可。

64 は CCBench 自身の `CACHE_LINE_SIZE` と一致する。`external/ccbench/include/cache_line_size.hh:1-5`

標準 header は `<array>`, `<cstdint>`, `<mutex>`。`alignas` は言語 keyword なので専用 header は不要。`std::hardware_destructive_interference_size` と `<new>` は使わない。CCBench は GCC 系で `-Wall -Wextra -Werror` を有効にするため、compiler/`-mtune` 依存値に対する `-Winterference-size` の余地を持ち込まない。`external/ccbench/cmake/CompileOptions.cmake:1-3,30-32`

これは静的判断であり、GCC 実コンパイルは本段では未実施。

### A-5. CAS と deadlock/serializability

modeX branch は次の形を維持する。

```cpp
bool acquired;
{
  std::lock_guard<std::mutex> guard(
      izanagi_t139_positive_control::gates[
          izanagi_t139_positive_control::stripe_for(
              (*itr).storage_, (*itr).key_)].mutex);
  acquired = compareExchange((*itr).rcdptr_->tidword_.obj_,
                             expected.obj_, desired.obj_);
}
if (acquired) {
```

根拠は以下。

- stock の lvalue、expected、desired は `transaction.cc:170-173` の式そのもの。
- `compareExchange` は非 blocking の atomic builtin 1 回で、失敗時は `before` を更新して返る。`external/ccbench/include/atomic_wrapper.hh:63-69`
- mutex scope は CAS 直後に終わる。CAS failure 後の stock loop、lock 検査、abort/retry は mutex 外で実行される。`external/ccbench/cc/silo/transaction.cc:155-184`
- 動的に CAS retry が起きる場合も「stock loop 1 iteration 当たり 1 CAS」のまま。modeX 独自の probe CASや二重 CASは置かない。
- transaction が前の record lock を保持したまま stripe mutex を待つ場合はあるが、逆側の mutex 保持者は record lock を待たず非 blocking CAS後に必ず mutex を離す。したがって `record lock → mutex → record lock` の待ち cycleは作らない。
- CAS成功後の lock coverage、validation、write、unlock はそのまま残る。`external/ccbench/cc/silo/transaction.cc:174-192,437-483`。mutex は schedule を狭めるだけで、Silo の serializability mechanism を置き換えない。

### A-6. nm witness

`tools/pegasus/probes/t139_positive_control_probe.sh:32-45` を次のように変更する。

- build arm は引き続き 6 本:
  `stock mode1 modeX stock-live mode1-live modeX-live`
- define は `-DIZANAGI_T139_PC_MODEX=1`
- TSV header は `mode1_symbols modeX_symbols trace_symbols`
- `mx=$(grep -c 'izanagi_t139_pc_modex_identity' ...)`
- 条件は:

  - stock*: `m1==0 && mx==0`
  - mode1*: `m1>=1 && mx==0`
  - modeX*: `m1==0 && mx>=1`
  - 全 binary で `izanagi_trace==0`

前回 raw がこの 6-row witness 形を実証している。`output/env/pegasus/t139-positive-control-probe/0_877859.nqsv/nm-witness.tsv:1-7`

旧 `mode2` symbol を互換名として残す案は却下する。残すと新旧実装の nm 識別が曖昧になる。

## B. 依存 source の調達

### B-1. PBS の env seam

[t139_positive_control_probe.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe/tools/pegasus/probes/t139_positive_control_probe.pbs:12) の `:12-24` を変更する。

新しい env は probe 固有の単一 root:

```text
IZANAGI_T139_DEPENDENCY_SOURCE_ROOT
```

構造は次で固定する。

```text
<root>/gflags
<root>/glog
```

PBS の処理は以下。

1. env が非空、絶対実在 directory、非 symlink であることを確認し、`realpath -e` で正規化。
2. inline Python は policy の path を出力せず、`gflags/glog + dependency_pins` を出力。
3. 各 `<root>/<name>` について:

   - 実 directory、非 symlink
   - `git rev-parse --show-toplevel` がその directory 自身
   - `HEAD == silo_ladder_rung1.dependency_pins[name]`
   - `git status --porcelain --untracked-files=all` が空

4. `GFLAGS_SOURCE=<root>/gflags`、`GLOG_SOURCE=<root>/glog` を設定。
5. 現在の build/install `pbs:41-51` はそのまま使う。
6. `IZANAGI_GFLAGS_SRC_HEAD` / `IZANAGI_GLOG_SRC_HEAD` は env root から得た値ではなく、policy pin を exportする。driver がそれらを CMakeへ渡している。`tools/pegasus/probes/t139_positive_control_probe.sh:29-31`

policy は同じ値を top-level expected head と nested dependency pin に重複保持している。`tools/pegasus/policy.json:14-17,36-38`。PBS の inline Python でも両者の一致を assertし、既存 driver 契約と合わせる。正式 driver はこの一致を既に検査している。`orchestrator/campaign/silo_ladder_rung1.py:829-845`

加えて、PBS が検査した `policy_sha256 / dependency / resolved_path / expected_pin / observed_head / clean=1` を stage 内の `dependency-witness.tsv` に書き、driver が `mkdir "$OUT"` の直後に raw へコピーする。変更位置は `pbs:20-24` と `probe.sh:7`。これは probe provenance であり、qualification artifact や Izanagi gate ではない。

### B-2. clone の場所

使用 root は、現に pin 一致・clean で存在する次を採用候補とする。

```text
/work/1/SFC/tanab/izanagi-thirdparty-deps/
├── gflags
└── glog
```

親は投入直前に再検査し、無ければログインノード上で通常 clone → detached pin checkoutする。計算ノードから network取得しない。Pegasus では `/work` が永続領域、`/scr` は job-local一時領域である。`docs/pegasus-runbook.md:258-268`

これは既存 `/work/1/SFC/tanab/izanagi-thirdparty-cache` と別の sibling root にする。既存 cache は masstree/mimalloc/googletest 3 本用である。`docs/pegasus-runbook.md:282-292`、`tools/pegasus/README.md:181-205`

`IZANAGI_THIRDPARTY_SOURCE_ROOT` には cache root 自体ではなく、`fetch_third_party.py hydrate` の出力 `.source_root` を渡す。cache には ignored build物が残りうるため、consumerへ直接渡さない契約である。`tools/pegasus/README.md:197-204`

### B-3. policy.json 編集を却下する根拠

単なる「方針」ではなく、現行 bytes が複数箇所で pin されている。

- committed rung1 JSON は現在の policy SHA-256  
  `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac` を保持する。`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json:41-43`
- current-binding validator は policy の現行 bytes を再 hashし、JSON binding と不一致なら拒否する。`orchestrator/campaign/silo_ladder_rung1.py:3511-3531`
- submit/collect も `policy_sha256` を source binding として比較する。`orchestrator/campaign/silo_ladder_rung1.py:2405-2435,4553-4577`
- T-126 の required code identity set に policy が含まれる。`orchestrator/qualification/contract.py:38-66`
- identity verifier は required pathすべての commit blob hashを照合し、さらに live policy と `{commit}:tools/pegasus/policy.json` の内容を比較する。`orchestrator/qualification/identity.py:130-160`
- テストも旧 source pathを literal として固定している。`orchestrator/tests/test_pegasus_tools.py:349-354,383-388`
- 運用文書も T-139 evidence が bytesを pinするため共有 policyを編集しないと明記する。`tools/pegasus/README.md:15-20`

したがって `/home/...` を `/work/...` へ書き換えるだけでも、rung1 current binding・T-126 identity・既存 testsを同時に動かす。これは本 probe の依存復旧ではなく、凍結 evidence の再 bindingになるため却下する。

閉包上の残余は 2 点ある。

- probe-local env root は policy SHAの一部ではない。上記 `dependency-witness.tsv` と段 4 の exact qsub argv/hash凍結で補うが、正式 qualification identityとは呼ばない。
- `git status --porcelain --untracked-files=all` は ignored fileを列挙しない。現 probeは従来契約を維持するが、完全な source-tree byte closureではない。artifactを発行しない理由の一つとして残す。

### B-4. fetch_third_party.py 拡張は本 waveでは行わない

現 CLI は policyを次の二群に分けている。

- URLを持つ `third_party_sources` 3 本: fetch/hydrate/verify対象
- pathとpinだけを持つ gflags/glog: `verify-deps` 対象

`tools/pegasus/fetch_third_party.py:67-90,513-575,652-700`

gflags/glogを fetch対象へ入れるには、URLの新しい正本、cache layout、publish/verify契約、tests、README、既存 consumer一般化が必要になる。policyにはこの2本のURLがなく、policy編集は禁止なので、URLをscriptへ直書きするのも新しい二重正本になる。

従って一般化は scope 外として段 4 の裁定パッケージへ返す。なお `verify-deps` は凍結 policy pathを読むため、本変更後も rc=1 のままである。`tools/pegasus/README.md:191-194`。本 waveが直すのは probe PBS経路だけで、rung1/T-126一般経路を直したとは報告しない。

## C. 事前登録

### C-1. 受理条件

P3 の条件は J=1 の生死確認として十分であり、変更しない。D126 が明示的に固定した条件そのものである。`docs/decisions.md:6191-6208`

現 `awk` は各 workloadについて:

```text
count(mode1) == count(mode2) == count(stock) == 5
max(mode1) < min(mode2)
max(mode2) < min(stock)
```

を判定する。`tools/pegasus/probes/t139_positive_control_probe.sh:77`

`mode2` を `modeX` に改名すれば、これは「どの mode1標本もどの modeX標本より小さく、どの modeX標本もどの stock標本より小さい」という全標本 strict orderingと正確に同値である。等値は不受理。

ただし現 awk は rep番号の一意性や余分な未知 rowを検査しない。実装時には同じ行で次も確認する。

- workload は W1/W2だけ
- arm は mode1/modeX/stockだけ
- rep は1〜5で、各 `(workload,arm,rep)` がexact-one
- data rowはexactly 30

これは malformed rawの拒否であり、正常標本の性能受理条件は変えない。

### C-2. workload、rep、liveness、単独性

次は変更しない。

- W1: `rmw=true, skew=0.9, tuple=10000, max_ope=10, t48, 3秒`
- W2: `rratio=50, skew=0.5, tuple=100000, max_ope=10, t48, 3秒`

定義は `tools/pegasus/probes/t139_positive_control_probe.sh:47-48`。前回結果は未較正の局所観測であり、headline/calibration/floorには使えない。`output/insights/2026-08-02_t139-positive-control-probe/README.md:79-81`

repは5のまま。J≈11/d≈1.0は将来の正例本走設計であり、各 studyの実走前に固定するもの。`docs/archive/worklog-phase3-0803-142-143.md:3-11,34-38`

livenessも以下を維持する。

- performance: `CCBENCH_TRACE=0`, `ADD_ANALYSIS`なし
- liveness: `CCBENCH_TRACE=0`, `ADD_ANALYSIS=1` の別 build・別 run
- 2 workload × 3 arm × 48 worker = 288/288

分離は `tools/pegasus/probes/t139_positive_control_probe.sh:21-25,35-39,49-60,63-75` に実装済み。

単独性は各6 liveness runと30 performance runの直前、計36回の `load1<=48` と競合 ycsb process 0を維持する。`tools/pegasus/probes/t139_positive_control_probe.sh:10-15,53-54,69-70`

### C-3. interleaveだけ固定 schedule化を推奨

現 `shuf` は実行時乱数であり、同じ jobを再投入すると順序を引き直せる。`tools/pegasus/probes/t139_positive_control_probe.sh:65-75`

各 rep内の3-arm interleaveは維持するが、段4で次の balanced 5 permutationを固定し、runtime `shuf` を削除することを推奨する。

```text
r1: stock  mode1 modeX
r2: mode1  modeX stock
r3: modeX  stock mode1
r4: stock  modeX mode1
r5: modeX  mode1 stock
```

W1/W2とも同じ表を使い、`order.tsv` への記録は継続する。各 armのposition回数は `(2,1,2)` またはその順列になり、runtimeで有利な順序を引き直す余地を消せる。

段4が「前回実装を一切変えず `shuf` 維持」と裁定する場合は、少なくとも最初に exact verdictまで到達した jobを唯一の結果とし、順序を理由に再投入しないことを明記する必要がある。

### C-4. outcome後に動かせる余地と凍結方法

現状残る裁量は次のとおり。

- patch/driver/PBSが未commitのままなら、macro、workload、rep、AWKを投入直前まで編集できる。
- runtime `shuf` は再投入ごとに順序を変えられる。
- job IDごとに別 raw directoryができるため、複数jobから都合のよい1件を選べる。`tools/pegasus/probes/t139_positive_control_probe.pbs:52-55`
- acceptance falseでは awkが rc=1を返すため、科学的な不成立を「job failure」と誤分類して再投入できる余地がある。`tools/pegasus/probes/t139_positive_control_probe.sh:77-78`
- qsub env root、dependency clone、repo checkout、policy/PBS bytesは現 rawに記録されない。
- `solo_load1_threshold=48`、timeout、liveness run数もdriverのmutable literal。
- rawはstage7でcommitされるまで手編集可能。

段4では最低限、以下を固定する。

1. patch/driver/PBSのSHA-256、CCBench pin、policy SHA-256。
2. modeX関数と2 stripe、arm集合、workload argv、rep=5、schedule。
3. acceptance式、nm 6/6、liveness 288/288、solo 36/36。
4. dependency root realpath、両HEAD、third-party hydrate root。
5. 「最初にexact verdictまで到達したjobが唯一のJ=1」。
6. retry上限と理由。推奨は最大2 submission、retry可能なのは `verdict.tsv` 未完成のinfra failureだけ。true/falseどちらでもexact verdict生成後は再投入禁止。
7. 全 submission IDを報告し、不成立jobを省かない。

## D. 走らせ方

### D-1. qsub前の調達

ログインノードで以下を行う。

1. repo rootで `git status` を確認し、保護対象や他session差分がないことを確認。
2. `tools/pegasus/policy.json` の SHAが既存 bindingと同じであることを確認。
3. CCBench pinと patch dry-runを再確認。
4. `/work/1/SFC/tanab/izanagi-thirdparty-deps/{gflags,glog}` の実path、非symlink、HEAD、cleanを確認。
5. third-party cacheを `fetch_third_party.py verify` し、`hydrate` の出力 `.source_root` を保存。
6. `bash -n`、patch static inspection、nm symbol名の整合を確認。
7. generic sourceであるため、親の計算ノード検査では少なくとも modeX付き ycsb buildに加え、tpcc/bomb/sbombのcompile smokeを行う。対象一覧は `external/ccbench/cc/silo/CMakeLists.txt:1-3`。
8. `qstat -Q`、`pegasusinfo`、`rbudgetcheck`、`check_quota` を投入直前に確認する。runbookの投入前項目は `docs/pegasus-runbook.md:645-650`。

### D-2. qsub

必ず repo rootをcwdにする。PBSは `PBS_O_WORKDIR` を repo rootとして解決する。`tools/pegasus/probes/t139_positive_control_probe.pbs:7-10`

```bash
repo_root=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-alt-x-probe
thirdparty_source_root=<hydrate 出力 JSON の .source_root>
dependency_source_root=/work/1/SFC/tanab/izanagi-thirdparty-deps

cd "$repo_root"

export_spec="IZANAGI_THIRDPARTY_SOURCE_ROOT=$thirdparty_source_root,IZANAGI_T139_DEPENDENCY_SOURCE_ROOT=$dependency_source_root"

qsub -v "$export_spec" \
  tools/pegasus/probes/t139_positive_control_probe.pbs
```

位置引数や独自の引渡し方法は使わない。既存 sanctioned interface は `qsub -v "$export_spec" "$JOB_SCRIPT"` である。`docs/failures.md:2280-2292`、`docs/pegasus-runbook.md:646-649`

`IZANAGI_REPO_ROOT`、gflags/glog個別path、cache rootは `-v` で渡さない。

- repo rootは `PBS_O_WORKDIR` からPBS自身が決める。
- gflags/glogは単一dependency rootから導出する。
- 3本cacheはjob consumerに直接渡さず、hydrate source rootだけを渡す。

### D-3. QUE 123下の扱い

混雑はqueue変更、重複投入、workload縮小の理由にしない。briefの観測は `QUE 123 / RUN 40`。`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/brief.md:32-33`

qsub直後に以下だけ確認する。

- request IDを段4凍結記録へ追記。
- `qstat` でrequestが可視。
- 同一waveのactive requestが1本だけ。
- 待ち時間が長くても別queueへ変えず、同じjobを重ねない。

終了後は `.o/.e`、PBS status、raw directory、`dependency-witness.tsv`、nm/liveness/solo/order/throughput/verdictをすべて回収し、exact verdictの有無でscientific completionとinfra failureを分ける。

実装子は上記3 probe fileだけを編集し、docs編集・commitを行わない。`docs/dev-wave/workers.md:26-30`。insight、spool fragment、commit、実測の帰属は親の段7以降に残す。

## 総括

### (a) 変更ファイル

- `tools/pegasus/probes/t139_positive_control.patch`
  - mode2→modeX、bounded suffix mixer、`alignas(64)` wrapper、modeX identity symbol、stock CASの単一wrapper。
- `tools/pegasus/probes/t139_positive_control_probe.sh`
  - arm/macro/nm/verdictをmodeXへ改名、exact 30-row検査、固定schedule、dependency witnessのraw取込。
- `tools/pegasus/probes/t139_positive_control_probe.pbs`
  - `IZANAGI_T139_DEPENDENCY_SOURCE_ROOT`、policy pin/clean検査、witness生成。
- runtimeのみ:
  - `output/env/pegasus/t139-positive-control-probe/<job>/`
- 親のみ:
  - `output/insights/2026-08-05_t139-alt-x-probe/` とspool fragment。実装子は触らない。

### (b) 却下した案

- 第4 arm: run数・liveness件数・受理条件が変わる。
- record addressによるstripe: 不安定でalignment偏りがある。
- key全体のhash / `std::hash<std::string>`: O(len)を再導入する。
- `std::hardware_destructive_interference_size`: compiler依存warning面を増やす。
- `policy.json` path編集: rung1/T-126のbytes/identity pinを破る。
- cache rootを直接consumerへ渡す: hydrate契約違反。
- `fetch_third_party.py` のgflags/glog一般化: URL/正本/testsを要し、本probeのscope外。

### (c) 実装不能・矛盾

- probe実装自体に実装不能点はない。
- ただし凍結policyを維持する限り、一般CLIの `verify-deps` はrc=1のまま。これをrc=0にすることまで成果に含めるならP2と矛盾する。
- 2 stripeへの写像を可変長keyの単射と解釈するなら数学的に不可能。必要条件は安定写像であり、collision-freeではない。
- 本段は静的検査のみで、build/test/qsubの緑は主張しない。

### (d) 段4で裁定すべき択一

1. interleaveを固定balanced scheduleへ変えるか、runtime `shuf` を維持するか。推奨は固定schedule。
2. exact false verdictを返したPBS rc=1を科学的完了として扱うか、専用rcへ変更するか。いずれでもfalse後のretryは禁止。
3. infra retryをゼロにするか最大2 submissionにするか。推奨は「exact verdict未生成時だけ最大1回retry」。
4. dependency witnessをrawへ追加するか、段4の外部記録だけにするか。推奨はrawへ追加。