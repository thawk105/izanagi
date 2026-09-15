# [T-1643] 段 1 brief — `__has_include` 族を実 pair で実測する

## 研究前進

`source_digest` の identity は「checker が preprocess した bytes」で variant の受理と cache key を
決める。checker と実 build で `__has_include` の真偽が食い違えば、identity が実 build を代表せず、
別挙動の variant が stock の certified 結果を継承しうる (規律 2 直撃の経路)。現行 checker は
blanket reject で fails-closed にしているが、**その reject が実際にどの式・どの pair で発火するかは
g++-12 の 1 式しか実測がない**。本 wave は対照表を作り、Phase 3 で coder が EVOLVE-BLOCK を触る
ときの identity 正当性の根拠を 1 段固める。完了判定 = 実測した対照表が insight に残ること。

## scope (純増のみ)

既存被覆: `output/insights/2026-07-28/t148-review-verbatim/review-focus-claude-closed-partial-table.md:15`
が g++-12 で `#define IZ_H __has_inc##lude` + `#if IZ_H("tsc.hh")` を実測済み
(逐語「実測: `-nostdinc` で 0、既定 path で 1」)。`docs/decisions.md:790-813` (D30 系案 A) が
`-nostdinc` 維持と computed include の known-limitation を記録。

純増は次の 3 つだけ。
- (a) **admission toolchain** (実 build が実際に使う compiler) での実測。
- (b) 未実測の式 — angle 形式 `__has_include(<...>)`、`__has_include_next`、
  system header と project header の区別、`#define` 経由の間接形。
- (c) **g++-13 の可否そのもの** (下記の新事実)。

## 親が brief 前に実測した、引数の前提を覆す事実

- **`g++-13` は login node pegasus02 に存在しない。** `/usr/bin` にあるのは `g++-9` / `g++-11` /
  `g++-12` のみ、既定 `g++` は 11.4.0。`module avail` の compiler 群は cuda / intel / nvhpc のみ。
  台帳も一致する — `docs/failures.md:8023-8024`「この環境に `g++-13` は login / compute とも
  存在しない」、`docs/decisions.md:13614-13616` (D293)。
- したがって依頼の「g++-13 と admission toolchain の実 pair」は、**g++-13 側が字句どおりには
  実測できない**。不在そのものを対照表の 1 行として実測記録する (先例 = `docs/decisions.md:51603`
  付近の D1644 系「本番の cxx が存在しない機体でも…到達可能性は g++-12 で実測済み…限界は記録に明記する」)。
- `orchestrator/campaign/buildcache.py:1838` `compilers_for_current_site()` は site が
  Pegasus compute のときだけ `("gcc", "g++")` を返し、それ以外では不在の
  `DEFAULT_CC, DEFAULT_CXX = ("gcc-13", "g++-13")` (`:621`) を返す。
  → **admission toolchain の実体は Pegasus compute の system `g++`** である。
- 実 pair の配線: `orchestrator/campaign/pipeline.py:1790` が `_compilers_for_current_site()` の
  `resolved_cxx` を checker 側 `evidence_cxx` へ、`:1945` が同じ関数の戻り値を build 側 `cc`/`cxx` へ渡す。
  checker と実 build は同じ compiler を共有する配線である。

## 確定済みユーザー裁定・先例 (緩めない)

- D293 (`docs/decisions.md:13635`): 「固定要求のまま `g++-13` を Pegasus へ用意する」は**却下済み**。
  用意経路は root 権限かコンテナに限られ、計測条件を変え、変更が計測機の外に出る。
- 依頼の明示指示: checker の一般化へ広げない。仮想リスク向けの gate・検査・台帳・一般化の追加は
  scope 外。結果を見る前に「欠陥がある」と決めない。規律 2 を緩めない。

## 不変条件

- checker (`orchestrator/campaign/source_digest.py`) の受理集合・実装を**変えない**。
- 実装面 (probe script) は Codex `role=author` が書く (D95)。親は実装面を直接編集しない。
- probe は repo へ残さない (親が実行後 repo 外へ退避、`DW-C01`)。
- 規律 2: 正しさゲートを緩める方向の変更をしない。

## 成果物の形

`output/insights/2026-09-14/t1643-has-include-real-pair/README.md` に
(1) **対照表** — 行 = `__has_include` 族の式、列 = (compiler × argv 環境) の pair、値 = 真偽・rc、
(2) 実測できなかった pair とその理由 (g++-13 不在など)、(3) 子の逐語。
probe script と raw JSON は job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1643-has-include-pair/` に保全する。

## (P1) 割れうる前提 — 親の provisional 裁定・攻撃対象

- **(P1-a)** admission toolchain = Pegasus compute の system `g++`。`compilers_for_current_site()`
  の読解であり、compute では未実測。
- **(P1-b)** login の `g++` 11.4.0 は compute の `g++` と同一である。未実測。
- **(P1-c)** `g++-13` は compute にも無い。login は親が実測、compute は台帳の記録による。
- **(P1-d)** checker は `__has_include` を blanket reject する (`source_digest.py:1866-1876`、
  `:1855-1861`) ので、真偽差は受理集合に到達しない。読解であり、probe で確かめる。
- **(P1-e)** checker 側 argv は `[cxx, "-E", "-P", "-nostdinc", "-Werror=undef", "-std=c++20",
  "-O3", "-DNDEBUG"]` (`source_digest.py:1663`、`BUILD_FLAGS` は `:371`)。実 build 側の実 include
  path は未取得であり、CCBench の実 compile command から取る必要がある。

## 並列分割方針

- 段 2: plan 1 本 (codex `read-only`)。
- 段 3: 敵対相談 2 本 (`sol` / `luna`) — 実測設計が恒真な結論に倒れないかを別レンズで攻撃させる。
- 段 5: 実装子 1 本 (probe、`workspace-write`)。
- 段 6: 敵対レビュー 1 本 + fix。変異 matrix の扱いは段 4 で裁定 (実装面が probe だけのため)。

## 受入・実測環境

probe は preprocess の真偽判定で決定的・軽量なので **login node** で走らせる
(runbook §7.0.0 の自動判定、性能計測ではない)。compute の compiler 版の実測が必要かは段 4 で裁定する。
受入全走は `tools/run_tests.py` の自動判定に従う。
