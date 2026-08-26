# 段 4 裁定 — [T-1798] 床値 SWO oracle の依存 manifest を production で成立させる

裁定者 = 親。入力 = 段 2 plan (`s2-plan.md`)、段 3 レンズ A (`s3-lens-a.md`)、レンズ B (`s3-lens-b.md`)、
親の実測 (`MEASUREMENTS.md`)。裁定 inbox は段 4 直前に再走査した — `docs/handoff/` は README のみ、
local main は wave 開始時と同じ `9463bcbc` で、wave 開始後の更新はない。

## 0. 親自身の誤りの訂正 (先に片付ける)

- 親は段 1 で `/work/1/SFC/tanab/izanagi-thirdparty-cache/masstree` を「production の依存 root」と
  呼んだ。**誤りである。** 床値 campaign が oracle と build へ渡すのは `<effective_base>/masstree-src`
  である (`s8b_floor_campaign.py:2810`)。
- 親は MEASUREMENTS へ「build 境界が見る root は oracle が見る root と同じ path ではない」と書いた。
  **誤りである。** `source_root.parent` が base なので、buildcache が組み立てる `base/masstree-src` は
  同じ directory を指す。レンズ A はこの訂正を読み、旧記述に基づく所見を出していない。
  レンズ B の所見 1 前半はこの旧記述に依拠しているので、その部分は **refuted** とする。
- 親は brief で「canonical root は fixture と bytes 同一だから oracle から見て区別不能」と書いた。
  レンズ A 所見 8 のとおり不正確である。以後「受理判定に必要な file bytes について同値」と限定する。

## 1. 所見の裁定

### レンズ A

| # | 判定 | 採否 | scope |
|---|---|---|---|
| 1 archive 生成 tool の未束縛 | **real** | 保証水準の限定を採用、実装は不採用 | **scope 外 → 新規起票** |
| 2 合成受理集合の拡大 | **real** | **採用** (表現と記録の規定) | scope 内 |
| 3 build 中の A→B→A 再生成 | real | 不採用 | scope 外 (T-1799 / T-1805) |
| 4 mimalloc の持続改変 | real | 不採用 | scope 外 (T-1800) |
| 5 resume が新 gate を通らない | real | 不採用 | scope 外 (T-1804) |
| 6 portable 成果物が等価検査を永続化しない | real | 保証水準の限定を採用 | scope 外 (T-1805) |
| 7 config.h の機体依存 | **real** | **採用** | scope 内 |
| 8 「区別不能」は不正確 | real (nit) | **採用** (表現の限定) | scope 内 |

### レンズ B

| # | 判定 | 採否 | scope |
|---|---|---|---|
| 1 成功系列の非空性が未証明 | 前半 **refuted**、後半 **real** | **親が実測で閉じた** (下記) | scope 内 |
| 2 `s8b_oracle_n_pilot` が canonical も capability も受け取らない | **real** | 不採用 | **scope 外 → 新規起票** |
| 3 ambient 環境変数から fixture を受理する入口 | **real** | 保証水準の限定を採用 | **scope 外 → 新規起票** |
| 4 resume | real | 不採用 | scope 外 (T-1804) |
| 5 同一 uid の A→B→A | real | 不採用 | scope 外 (T-1805 / T-1799 / T-1802) |
| 6 提案テストが production 全系列が空でも緑 | **real** | **採用 (must-fix)** | scope 内 |
| 7 新設 test file の自走契約が無い | real (nit) | **採用** | scope 内 |

### レンズ B 所見 1 に対する親の実測 (段 3 完了後に親が実行、repo 外)

fetch のみ済みの実在 root
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1431-floor-pilot-submit/repro/fc-base/masstree-src`
を job tmp へ複製し、CCBench の recipe を完走させた
(`bootstrap.sh` / `configure --disable-assertions` / `make` / `ar` / `ranlib`、すべて rc=0)。
完走後の姿は regular file 196、symlink 0、tracked 99。
そこから **fixture を一切参照せず規則だけで** canonical root を作った
(宣言集合 = tracked 99 ∪ {`config.h`, `PIN`}、`PIN` = HEAD + 改行)。結果:

- 宣言 101 path、生成 manifest sha256 = `8d0151cf...` = pin と一致、fixture と byte-identical
- `_verify_dependency_root(canonical)` OK、`config_sha256` = `e9a4ecd3...`
- `resolve_oracle_environment(ccbench, dependency_root=canonical)` 成功
- `check_materialized_sort_swo(...)` が **`OracleStatus.PASS` / finding `None`** (compile + execute 実走)

**したがって oracle PASS までの成功経路は空でないことが実測で確定した。** 未実測なのは
`buildcache.build_v2` の post-oracle capability を通した ycsb build までであり、二根検査は
まだ実装が存在しないので当然未実測である。ここは段 6 の受入で閉じる。

## 2. レンズ A 所見 1 (blocker) の裁定 — 詳細

主張は「archive の生成 tool (`make` / `ar` / `ranlib` / autotools / `CXX`) が継承環境から解決されるため、
細工した tool が fixture と同じ `config.h` を残しつつ悪性 `*.o` を archive へ入れられる。
floor は生成**後**の archive hash を初めて観測してそれを権威にするので、全照合が通る」である。

**real と裁定する。** 事実関係は親が確認した。recipe は plain tool 名を継承環境で実行する
(親は実際にその recipe を走らせた)。`_verify_masstree_archive` は生成後の観測であり期待値照合ではない。

**しかし実装は本 wave の scope 外とする。** 理由:

1. **本 wave が作った欠陥ではない。** 変更前から archive は自己観測であり、T-1798 の起票文にも無い。
2. **tool identity の束縛は「実行権威の変更」であり、D425 が別審査とした書込み権威の変更と同型である。**
   recipe は `external/ccbench` 側にあり、CCBench の改変は D16/D18/D20 の手続きに属する。
3. `DW-G02` に従い、床値の 1 cycle を実際に通す前の hardening は、correctness 判定・selected/tie・
   数値・proof 参照・試行欠落を実際に変える欠陥だけを blocker とする。archive tool 汚染は
   「悪性 tool を PATH へ置ける主体」を前提にし、その主体は同じ権限で canonical root や
   binary そのものを差し替えられる。本 wave の gate はその主体を防ぐ設計ではない。

**代わりに採るのは、レンズ A 所見 1 の提案後半である。** すなわち **「因果束縛を閉じた」と主張しない。**
worklog / decisions / insights には保証水準を次の言葉で限定して書く。

> 本 wave が束縛するのは、oracle が判定した宣言 101 path の bytes と、build 境界が観測する
> 実 source root の同 101 path の bytes・HEAD・`config.h` の等価性である。
> **archive (`libkohler_masstree_json.a`) の生成権威は束縛しない。** archive は生成後に観測した
> hash を権威として運ぶだけであり、その archive を作った tool の identity は検査していない。
> 宣言外の生成物 (`configure`、`config.h.in`、`GNUmakefile`、`*.o`) も検査していない。

新規起票する ([T-1810] とする。番号は段 7 の spool で確定する):
**masstree prebuild が使う tool (`CC`/`CXX`/`make`/`ar`/`ranlib`/autotools) の identity を
検証済み absolute path へ束縛するか、archive に独立した期待権威を設けるかを決める。**

## 3. レンズ A 所見 2 の裁定 — 「受理集合を広げない」の正確な言い方

親 brief の「oracle の受理集合を 1 bit も広げない」は、**primitive の意味では真、合成の意味では偽**である。
以後は分けて書く。

- **不変 (本 wave で 1 行も変えない)**: `sort_swo_oracle._verify_dependency_root` /
  `_parse_dependency_manifest` / `_dependency_file_inventory` / `_read_verified_dependency_file` /
  `_prepare_verified_dependency` / `_assert_verified_dependency_unchanged` /
  `_dependency_manifest_closure` / `resolve_oracle_environment` / `DEPENDENCY_MANIFEST_SHA256` と
  その全 consumer / fixture の bytes / fixture verifier。
- **意図的に拡大する**: `実 source root → floor の PASS` という合成述語の受理集合。
  従来は空集合だった (196 file の root は必ず `dependency-file-set-mismatch`)。
  本 wave は「実 source root の tracked 99 file と `config.h` を規則で射影した canonical root」を
  oracle へ渡すことで、この合成受理集合を空から非空へ変える。**これが T-1798 の目的である。**

ユーザー引数の「oracle の受理集合を広げずに解くこと (絶対規律 2)」は、primitive の意味で満たす。
合成の拡大は依頼そのものなので、規律 2 に反しない。ただし**この二段の言い分けを成果物へ明記する**。

## 4. plan v2 — 段 2 plan からの差分

段 2 plan の骨格をそのまま採る。すなわち:

- 新規 production module `orchestrator/campaign/sort_swo_dependency_material.py`
- 宣言集合 = VCS の tracked 一覧 ∪ {`config.h`, `PIN`} の規則導出。fixture を参照しない
- pin 比較は既存 `_prepare_verified_dependency` を再利用し、第二実装を作らない
- **二根検査**: canonical root へ既存 exact verifier、実 source へ canonical との tracked 集合・
  bytes・HEAD・`config.h` の等価検査、archive へ従来どおり独立 hash 検査
- 親の (P3)「buildcache を canonical root へ単純置換」は plan の反論どおり **撤回する**

差分として次を追加する。

### 差分 1 (レンズ B 所見 6 — must-fix): production 系列テストを必須にする

plan のテスト計画は generator 単体・floor 配線・buildcache を別々に緑にできる。
**同一実行で production 全系列を通す試験を 1 本必須にする。**

- 実 root (`<base>/masstree-src` の形) から canonical 生成 → oracle PASS →
  post-oracle capability 付き `build_v2` の cache miss → 同じ入力で cache hit、までを 1 本で通す。
- opt-in の環境変数で実 root を受け取ってよいが、**未設定でも系列の骨格が走る形にする** —
  実 masstree を必要としない部分 (canonical 生成 → 二根検査 → capability 検証 → cache identity) は
  合成 root で必ず走らせ、実 masstree を要する部分だけを opt-in にする。
- この系列テストは次の 3 つの変異でそれぞれ赤にならなければならない:
  (a) oracle へ `oracle_root` でなく `source_root` を渡す誤配線、
  (b) post-oracle capability から canonical root を落とす、
  (c) cache hit 経路の二根検査を省く。
- **親は段 6 で、実 root を使う系列を自分で 1 回実走する。** 子の非実走を緑と記録しない。

### 差分 2 (レンズ B 所見 7 — nit): 新設 test file に自走 harness を付ける

`orchestrator/tests/test_sort_swo_dependency_material.py` には `pytest.main` を呼ぶ `__main__`
harness を付ける。焦点走では露出しない偽緑を塞ぐ。

### 差分 3 (レンズ A 所見 7 — must-fix): config.h の機体依存を fail-closed で扱う

- 生成 manifest の hash が pin と一致しないときの失敗は、**「この機体の toolchain では canonical が
  pin へ到達しない」と読める detail_code** にする。plan の
  `floor-dependency-canonical-manifest-mismatch` を採用し、診断に生成 manifest の sha256 と
  期待 pin の両方を載せる (bytes 本体は載せない)。
- 「現在機で正例を実測した」ことは worklog へ書くが、**他機体へ一般化しない**。
  他機体で床値を走らせる場合は prebuild 後の実 root から生成器までを正例実測する、と運用要求を書く。

### 差分 4 (レンズ A 所見 1/2/6/8): 保証水準の限定を成果物へ書く

第 2 節・第 3 節の限定文を worklog / decisions / insights へそのまま書く。
「因果束縛を閉じた」「受理集合を 1 bit も広げない」「oracle から区別不能」は使わない。

### 変更しない範囲 (実装子への禁止事項として個別に列挙する)

1. `orchestrator/campaign/sort_swo_oracle.py` を **1 行も編集しない**。
2. `orchestrator/tests/fixtures/sort_swo_masstree/` 配下の **bytes を 1 byte も変えない**。
3. `orchestrator/tests/sort_swo_masstree_fixture.py` を編集しない。
4. `orchestrator/campaign/s8b_sort_swo_receipt.py` の pin 検査 (127 行付近) を編集しない。
5. `orchestrator/critic/digest.py` の pin 検査 (649 / 989 行付近) を編集しない。
6. `external/ccbench/` 配下を編集しない (recipe の tool 束縛は scope 外)。
7. `docs/` を編集しない (docs は親が書く)。
8. commit しない。`git add` もしない。
9. 既存テストの assert を弱めない。落ちるテストがあれば報告し、勝手に緩めない。

## 5. gate の禁止 — 署名と通る正例 (DW-S04)

新設する gate の禁止を署名で書く。

**禁止**: 床値の `sort_best` cell は、次をすべて満たす canonical dependency material を伴うか、
さもなくば oracle と build を 1 度も呼ばずに `_FloorOraclePreflightError` で拒否される。

- canonical root が `sort_swo_oracle._verify_dependency_root` を通る
- その manifest sha256 が `DEPENDENCY_MANIFEST_SHA256` と一致する
- canonical の宣言集合から `PIN` を除く全 path の bytes が、実 source root の同名 path と一致する
- 実 source root の tracked 一覧・HEAD・`config.h` が canonical 生成時のものと一致する

**通る正例 (親が実測済み)**:

- 実 source root = `<base>/masstree-src`、HEAD = `b3c5d054b66b08374d7a6ff5a0faeaf28b041a38`
- recipe 完走後: regular 196、symlink 0、tracked 99、
  `config.h` = `e9a4ecd3dfb9aef9c159e99cb2b7000651a2036ec909095f750b2c891404694a`、
  archive = `1423c4e85fed71204ff564751ff52bdef3de27e175de2786f017dfa2723024e4`
- 規則で作った canonical root: 宣言 101、manifest =
  `8d0151cfaa0b86d1a2753e69f514633ec2fe6ee1077caed819fd3a426b501875`
- この入力で `check_materialized_sort_swo` は `OracleStatus.PASS` / finding `None` を返す

## 6. 変異事前登録 (DW-M01)

実装前に登録する。各変異は実効 gate へ照準し、前後に同じ入力を拒否する層が無いことと、
無効化時の赤理由が一つに絞れることを、実装後の probe 巡で確認してから本走する。
確認できない変異は登録から落とし、実効 gate へ再照準する。

| ID | 位置 | 変異 | 期待する単一の赤理由 |
|---|---|---|---|
| M01 | canonical generator の宣言集合構成 | `PIN` を宣言集合から落とす (file は生成する) | 実在集合と宣言集合の不一致で `_verify_dependency_root` が `dependency-file-set-mismatch` |
| M02 | manifest 行の組み立て | path 区切りを空白 1 個にする | `_parse_dependency_manifest` が `dependency-manifest-invalid` |
| M03 | manifest の並び順 | `sorted()` を逆順にする | `_parse_dependency_manifest` の `paths != sorted(paths)` |
| M04 | 二根検査の実 source 側 | 実 source と canonical の bytes 等価検査を無効化する | 実 source 改変を検出する系列テストだけが赤 |
| M05 | post-oracle capability | capability から canonical root を落とす | 旧 5-key capability の拒否テストが赤 |
| M06 | cache hit 経路 | cache hit 時の二根検査を省く | cache hit drift 拒否テストが赤 |
| M07 | floor 配線 | oracle へ `oracle_root` でなく `source_root` を渡す | production 系列テストが赤 |
| M08 | generator の tracked 取得 | 一覧取得の失敗を握り潰して空集合で続行する | 空一覧拒否テストが赤 (fail-open の検出) |

`M01` は pin 比較より前に集合照合が発火するので、赤理由は 1 つに絞れる見込みである。
`M03` は ASCII path のみなら locale 差では順序が変わらないため、逆順という明示的な変異にした。
受理集合を縮小する変更 (post-oracle capability に canonical root を必須化する) を含むので、
**承認外の過剰拒否を検出する正例**として、第 5 節の正例入力が PASS し続けることを
`M04`〜`M08` の全変異巡で確認する。

## 7. 新規起票する項目 (段 7 で spool へ書く)

1. **masstree prebuild の tool identity を束縛するか** (レンズ A 所見 1)。
   `make` / `ar` / `ranlib` / autotools / `CXX` が継承環境から解決され、archive は生成後の
   自己観測 hash が権威になる。閉じるには recipe の tool を検証済み absolute path へ束縛するか、
   archive に独立した期待権威を設ける。CCBench の改変を伴うので D16/D18/D20 に従う。
2. **`s8b_oracle_n_pilot` を canonical 保証の対象にするか** (レンズ B 所見 2)。
   pilot は `source_root` を oracle へ渡し、build capability も付けない。非 authoritative な
   成果物なので、直すか対象外と明示するかを決める。
3. **ambient `IZANAGI_SORT_SWO_MASSTREE_ROOT` から任意の pin 適合 root を受理する production 入口を
   どう扱うか** (レンズ B 所見 3)。floor は明示引数を渡すので floor には影響しないが、
   `p3_s4_loop_sort.quarantine` と floor 以外の `s1_direct_comparison.prepare_cell` は
   ambient を受理する。

## 8. 段 5・6 の進み方

- 段 5: Codex `role=author` の実装子 1 本 (D95)。所有は新規 module + floor 配線 + buildcache 二根検査 +
  テスト。親は実装面を直接編集しない。
- 段 6: 敵対レビュー 2 本 (レンズは「二根検査の等価性が本当に成立するか」と「新設テストが偽緑でないか」)、
  fix、変異 matrix、受入全走。親は production 系列を 1 回自分で実走する。
