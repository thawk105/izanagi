# 親が段 1 前に実測した値 (一次資料)

計測日 2026-08-26、機体 = izanagi の開発ホスト。すべて親が直接実行した結果である。

## production 依存 root
- path: `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree`
- `rev-parse HEAD` = `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`
- `rev-parse --show-toplevel` = 同 path (すなわち root 自身が VCS の top-level)
- regular file 196 件、symlink 0 件、非 regular / 非 directory 0 件

## fixture
- path: `orchestrator/tests/fixtures/sort_swo_masstree/`
- `SHA256SUMS` は 101 行 (宣言 path 101 件)、fixture の regular file は 102 件 (= 101 + SHA256SUMS 自身)
- `sha256sum SHA256SUMS` = `8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875`
  (= `sort_swo_oracle.DEPENDENCY_MANIFEST_SHA256`)
- `PIN` の中身は `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` + 改行 (41 bytes)

## 集合差
- 宣言集合の全リスト: `fixture-declared-101.txt`
- production 実在集合の全リスト: `production-actual-196.txt`
- fixture のみ (production に無い): `PIN` の 1 件だけ
- production のみ (宣言に無い): 95 件
  - `.git/` 配下 26 件
  - `.deps/` 配下 26 件
  - `autom4te.cache/` 配下 7 件
  - その他 36 件: `GNUmakefile`, `config.h.in`, `config.log`, `config.status`, `configure`,
    `stamp-h`, `libjson.a`, `libkohler_masstree_json.a`, `*.o` 24 件,
    実行可能 `mtclient`, `mtd`, `mttest`, `test_atomics`

## bytes 一致
- 宣言 101 path のうち `PIN` を除く 100 path について、production 側の同名 file と
  sha256 を突き合わせた結果: mismatch 0 件、missing 0 件。
- `config.h` も一致 (`e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a`)。
  すなわち configure 生成物であってもこの機体では fixture と同一 bytes である。

## 生死確認 (DW-G01) — repo 外の使い捨て driver
手順:
1. 空 directory を作る。
2. fixture 宣言集合から `PIN` を除いた 100 path を、production root から同じ相対 path へ複製する。
3. `PIN` に production root の HEAD commit id (末尾改行込み) を書く。
4. root 内の全 regular file を `LC_ALL=C sort` 順に並べ、`sha256sum` 形式
   (64 hex + 空白 2 個 + 相対 path) で `SHA256SUMS` を生成する。

結果:
- 生成された `SHA256SUMS` は fixture の `SHA256SUMS` と **byte-identical** (`cmp` が一致)。
- その sha256 は `8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875` で pin と一致。

この駆動は repo 外 (job tmp) で行い、repo へは何も書いていない。

## oracle 側の既存 E2E
`orchestrator/tests/test_sort_swo_oracle.py` の
`test_cpp_e2e_clean_generic_lambda_positive` と
`test_cpp_e2e_stable_cross_allocation_pointer_positive` が、fixture root を dependency root として
compile + execute まで走らせ `OracleStatus.PASS` を確認している。
canonical root は fixture と全 101 file が bytes 一致するため、oracle から見て両者は区別不能である。

## 追記 (2026-08-26 09:55 JST) — 親が段 3 投入前に追加で確かめた事実と、**確かめていない事実**

### 依存 root には 2 つの形がある
- **staged 形**: `s8b_floor_campaign.py` の staged 検証 (2584 行付近) は
  `<base>/<name>-src` (すなわち `<base>/masstree-src`) を要求する。
- **直接 root 形**: 同 file の 2812〜2925 行付近の関数は、渡された source root 自身が
  VCS の top-level であることを要求する。`orchestrator/tests/test_sort_swo_oracle.py:963`
  (`test_resolver_without_explicit_root_rejects_synthetic_ancestor_cache`) は
  `<cache>/masstree` という形を想定した合成 root を作っている。
- 親が実測した `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` は後者の形であり、
  `-src` suffix を持たない。`docs/pegasus-runbook.md:288` が
  `IZANAGI_PEGASUS_THIRDPARTY_CACHE=/work/1/SFC/tanab/izanagi-thirdparty-cache` を定義している。

### 親が**確かめていない**こと (模擬と実の差)
- 床値 campaign を実際に走らせたときに `_dependency.source_root` が
  `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` になるという保証は、親は確認していない。
  親はこの path を「HEAD が policy pin と一致し config.h と archive を持つ実在の root」として
  見つけただけである。campaign が走行時にどの base をどう解決するかは未実測である。
  この差を埋めるのはプランとレビューの仕事である。
- したがって「production 依存 root」と親が呼んでいるものは、**oracle の受理形になり得ない実 root の
  一例**として扱うのが正確である。bytes 一致の測定結果はこの実例に対するものである。

### build 境界が見る root は oracle が見る root と同じ path ではない
`orchestrator/campaign/buildcache.py` の `_assert_post_oracle_dependency_material`
(938 行付近) は、binding の `fetchcontent_base_dir` から
`source_root = os.path.join(base, "masstree-src")` を組み立ててそこを検証する。
一方 `s8b_floor_campaign.py:2156` は `"fetchcontent_base_dir": str(dependency.source_root.parent)`
を書く。よって build 側が見るのは `<dependency.source_root の親>/masstree-src` である。
`dependency.source_root` の basename が `masstree-src` でない限り、この 2 つは別 path になる。
親が実測した root の basename は `masstree` であり `masstree-src` ではない。
**この食い違いが実行時に何を起こすか (build 側検査が不在 path で必ず落ちるのか、
それとも staged mode でしか binding が作られないのか) は親は未実測である。**
プランとレビューはここを名指しで検査すること。

### テスト側は fixture を dependency root にして oracle を走らせている
`orchestrator/tests/sort_swo_oracle_receipt_memo.py` は
`dependency_root=MASSTREE_FIXTURE` を固定して `resolve_oracle_environment` を 1 度だけ呼び、
その環境をテスト消費者へ配る。すなわち fixture root は
「oracle が実際に受理する canonical root」の実在例である。
この module は `orchestrator/tests/` 配下にあり、production の床値経路ではない。

## 訂正と追加実測 (2026-08-26 10:15 JST) — 親が段 3 投入**後**に確かめた

段 3 の 2 レンズは、この訂正より前の版を読んでいる。所見がここで訂正した誤りに依拠する場合、
親は段 4 でそれを refuted とする。

### 訂正 1: build 境界と oracle が見る root の path は食い違わない
先の「### build 境界が見る root は oracle が見る root と同じ path ではない」節は**誤りである**。
`s8b_floor_campaign.py:2810` は `unresolved_source = resolved_cache / "masstree-src"` として
source root を base から組み立てる。したがって `dependency.source_root` は必ず
`<effective_base>/masstree-src` であり、`source_root.parent` は `effective_base` に等しい。
`buildcache.py` が `os.path.join(base, "masstree-src")` で組み立てる path は
同じ directory を指す。basename の食い違いは起きない。

### 訂正 2: 親が最初に測った root は床値 campaign の依存 root ではない
`/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` は `-src` suffix を持たず、
`docs/pegasus-runbook.md:288` の `IZANAGI_PEGASUS_THIRDPARTY_CACHE` が指す永続 cache である。
床値 campaign が oracle と build へ渡すのは `<effective_base>/masstree-src` の方である。
`effective_base` は、明示 base 引数が無ければ `_canonical_floor_fetchcontent_base(None, ...)` が
作る job-local base、あれば staged base である (`s8b_floor_campaign.py:3064-3078`)。

### 追加実測: campaign が使う形の root でも規則は成り立つ
親は `<base>/masstree-src` の形の実在 root を 1 つ見つけて測り直した。

- root: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-pilot-submit/repro/fc-base/masstree-src`
- HEAD = `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38` (policy pin と一致)
- 自身が VCS の top-level、tracked 99、regular file 125 (= tracked 99 + VCS metadata 26)、symlink 0
- **規則導出集合 (tracked 99 ∪ {config.h, PIN}) = 101 path。fixture 宣言 101 path と完全一致
  (両方向の差 0 件)。** すなわち規則の成立は最初に測った root だけの性質ではなく、
  masstree pin `b3c5d054` の性質である。独立な 2 root で確認した。
- ただしこの root は **`config.h` も `libkohler_masstree_json.a` も持たない**。
  fetch までは済んでいるが prebuild (configure / make) を経ていない状態である。
  床値 campaign は `buildcache.prepare_masstree_fetchcontent` を呼んでから
  `_verify_floor_oracle_dependency_source` を呼ぶので、実行時にはこの 2 つが生成される。

### 残る未確認点 (段 3 レンズ A の論点そのもの)
`config.h` の bytes が **base をまたいで同じか**は、親は 1 つの root
(`izanagi-thirdparty-cache/masstree`) でしか確認していない。上の root には `config.h` が無いため
比較できなかった。`config.h` は configure が生成するので、base・機体・autoconf 版が変われば
変わりうる。変わった場合に本設計が fail-closed するか黙って壊れるかは、
プランとレビューが答えるべき論点である。

## 追加実測 2 (2026-08-26 10:20 JST) — config.h は再現する

上の「残る未確認点」を親が実測で閉じた。

- CCBench の `cmake/ThirdParty.cmake:66-78` の recipe は
  `./bootstrap.sh && ./configure --disable-assertions` である。
- 親は fetch のみ済みの root
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-pilot-submit/repro/fc-base/masstree-src`) を
  repo 外へ複製し、同じ recipe を走らせた。bootstrap rc=0、configure rc=0。
- 生成された `config.h` の sha256 =
  `e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a`。
  **fixture の `config.h` と bytes 一致した。**

すなわちこの機体では、fetch した masstree pin `b3c5d054` に対して recipe が決定的に同じ
`config.h` を生む。base の場所には依存しない。独立な 2 つの base で確認したことになる。

**なお、機体・autoconf 版をまたいだ再現性はこれでも保証されない。** ただし一致しなくなった場合、
生成 manifest の hash が pin と一致せず fail-closed する。これは設計上望ましい振る舞いであり、
「黙って壊れる」のではない。プランとレビューはこの結論が正しいかを検査すること。

## 追加実測 3 (2026-08-26 10:35 JST) — 実在 root から oracle PASS まで通した

段 3 レンズ B の所見 1 は「実在する root から build まで閉じた成功系列がない」と指摘した。
親はその前半 (oracle PASS まで) を実測で閉じた。**すべて repo 外で行い、repo へは何も書いていない。**

### 手順
1. fetch のみ済みの実在 root
   `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-pilot-submit/repro/fc-base/masstree-src`
   を job tmp へ複製した。この root は複製時点で `config.h` も archive も持たない。
2. CCBench の recipe をそのまま完走させた。
   `./bootstrap.sh` rc=0 / `./configure --disable-assertions` rc=0 /
   `make -j CXXFLAGS="-g -W -Wall -O3 -fPIC"` rc=0 / `ar cr` rc=0 / `ranlib` rc=0。
   完走後の姿: regular file **196**、symlink 0、tracked 99。
   これは親が最初に測った `izanagi-thirdparty-cache/masstree` (196 file) と同じ姿である。
   すなわちあの root は prebuild 済みの依存 root と同型であった。
3. **規則だけで** canonical root を作った。宣言集合 = tracked 一覧 (99) ∪ {`config.h`, `PIN`}。
   `PIN` は HEAD + 改行。`SHA256SUMS` は Python `sorted()` と同じ codepoint 昇順、
   64 hex + 空白 2 個 + 相対 path + 改行。fixture は一切参照していない。

### 結果
- 宣言 101 path。生成 manifest の sha256 =
  `8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875`。
  **pin と一致し、fixture の manifest と byte-identical。**
- `sort_swo_oracle._verify_dependency_root(canonical)` が OK を返した。
  declared 101、`config_sha256` = `e9a4ecd3...`。
- `resolve_oracle_environment(ccbench, dependency_root=canonical)` が成功。
  compiler = `/usr/bin/x86_64-linux-gnu-g++-11`。
- `check_materialized_sort_swo(...)` を clean comparator で呼び、
  **`OracleStatus.PASS` / finding `None`** を得た (compile + execute まで実走)。
- prebuild 済み root の archive sha256 = `1423c4e85fed71204ff564751ff52bdef3de27e175de2786f017dfa2723024e4`。

### この実測が示すこと / 示さないこと
- **示すこと**: fetch した masstree pin `b3c5d054` から recipe を完走させ、
  規則だけで canonical root を作れば、oracle は実際に PASS する。
  成功経路は空でない。規則は fixture を参照せずに pin へ到達する。
- **示さないこと**: `buildcache.build_v2` の post-oracle capability を通した ycsb build までは
  走らせていない。二根検査 (canonical への exact 検証と実 source への等価検証) の実装も
  まだ存在しないので、その振る舞いは未実測である。ここは段 6 の受入で閉じる。
