# 段 4 裁定 — [T-2115] 段 7 cross-protocol の実装残余

親が段 2 プランと段 3 の 2 レンズを受けて裁定する。以下がプラン v2 の正本である。

## 0. 親自身の誤りの訂正 (先に置く)

- **編集面は 4 file ではなく production 8 file である。** brief の「編集面 4 file」は誤り。
  正しくは `genome.py`、`between_run_floor.py`、`screening_driver.py`、`backoff_sweep.py`、
  `s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`layer3_report.py`、`layer3_schema.json`。
- **「凍結 bytes への影響なし」の根拠が狭すぎた。** `FROZEN_MANIFEST` の key と
  `_GENERATOR_SOURCES` しか見ておらず、**凍結成果物の内部にある source SHA pin** を探していなかった。
  実際 `genome.py` の SHA (`8e8abd7f…`) は `known_axes_freeze.json`、`measurement_freeze.json`、
  `holdout_freeze.json` の 3 成果物に記録され、現在の bytes と一致している。
  両レンズの方法論的批判は **real** であり、受け入れる。
- **並行 wave との編集面衝突は「重なりうる」という推測であって実測ではなかった。**
  レンズ B が実測し、`dev-wave-t1981-t088-floor-remeasure` は base からの tracked diff を持たない。
  現時点の実衝突は無い。段 9 の land 直前に再照合する。
- **「mocc の live 軸は 3 本」は用語として不正確。** 正しくは
  「現行 CMake から**直交操作できる**軸が 3 本」。`RWLOCK` は live なコード分岐だが bare define で
  cache から off にできない。anatomy の `2^4=16` はこの固定分岐を数えた値であり、差はここに由来する。
  加えて `KEY_SORT` の live site は `include/ycsb.hh` なので、8 通りという数は **YCSB 条件付き**である。

## 1. 実測で確定した事実 (裁定の土台)

- **凍結の live-bytes 検査はユーザー裁定で保留中である。** `freeze_verification_hold.HELD = True` で、
  保留 ID に `s8b-oracle.known-axes-live-bytes`、`s8b-holdout.known_axes_freeze-implementation-bytes`、
  `t080.live-known-axes-artifact-bytes` を含む (21 件)。
- **`known_axes_freeze.json` の live tree 検証は base commit 2bf9cf387 で既に赤である。**
  親が実走した結果は `FreezeError: generator sha256 不一致
  (recorded=1d4d45a3… actual=9cc9f877…)` で、source 一覧に到達する前に落ちる。
  さらに source 側も `backoff_sweep.py` / `s6_sort_sweep.py` / `s8a_trigger_sweep.py` の 3 本が
  既に drift している。**この成果物の source SHA は歴史記録であって live binding ではない** (F39 の分類)。
- **`_T080_SOURCE_GOLDEN` (test 側の pin) が固定するのは凍結 JSON の中の値**であって live file の hash ではない。
  live file を編集しても凍結 JSON は変わらないので、この golden は緑のまま。`genome.py` はこの golden に含まれない。
- **live bytes を `8e8abd7f…` と比べる pin は `.py` に 1 件も無い** (literal 全文検索で hit 0)。

**したがって: 本 wave は現に緑である gate を 1 つも赤にしない。** ただし `genome.py` の source 記録は
3 つの凍結成果物で stale になる。これは既に 3 本の caller で起きている前例のある状態であり、
規律 7 に従い「当時の bytes という歴史的事実」は変わらない。**この staleness は段 7 で明記して記録する。**

## 2. real / refuted の裁定

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| A-1 | legacy implicit silo が protocol 不明の stock mocc calibration を silo として公式 report に入れうる | **real** | scope 内で緩和。下記 3.4 |
| A-2 | 凍結 pin は manifest の path key 以外にもあり brief が見落とした | **方法論は real / 帰結は refuted** | 訂正を 0 節に記載。gate は元から赤・かつ保留中 |
| A-3 | `{"silo"}` 固定 allowlist は hook の有無に束縛されず負例が恒真 | **real** | 述語を source 事実へ束縛する。下記 3.3 |
| A-4 | mocc 正例は production 経路で生成できない synthetic input に依存する | **real だが不採用** | 本 wave は初手 mocc の足場であり、certified mocc campaign は trace 移植後。残余として明記 |
| B-1 | within-run certified calibration (`calibration/registered/`) の閉包が未着手 | **real / scope 外** | 残余として記録。裁定パッケージへ |
| B-2 | screening の照合述語が records/threads を見ておらず層 3 と揃わない | **real / scope 外** | 本 wave が作った欠陥でも悪化させる欠陥でもない。残余として記録 |
| B-3 | canonical genome の解析述語が二重化・未定義 | **real** | scope 内。下記 3.5 |
| B-4 | 焦点走が consumer 閉包を覆っていない | **real** | 焦点走集合を確定。下記 5 |
| B-5 | 編集面 8 file・凍結内部 source hash 参照 | **real** | 0 節で訂正済み |
| B-6 | 「live 3 軸」は不正確、8 は YCSB 条件付き | **real** | 0 節で訂正。`notes` に明記させる |
| B-7 | genome 欠落 floor fixture が新たに拒否される | **real** | 意図した受理集合変更として宣言。下記 3.6 |

## 3. プラン v2 (実装する内容)

### 3.1 scope に入れる編集面 (production 8 file)

`orchestrator/campaign/` の `genome.py`、`between_run_floor.py`、`screening_driver.py`、
`backoff_sweep.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py`、`layer3_report.py`、`layer3_schema.json`。
`screening_driver.py` と 3 caller を外すと、同一 workload の第 2 protocol floor が置かれた瞬間に
**既存の silo screening が `matches=2` で全部落ちる**。整合部品として必須である。

### 3.2 genome 空間

`MOCC_SPACE` を追加し `SPACES` を silo / mocc の 2 件にする。軸は
`BACK_OFF`、`TEMPERATURE_RESET_OPT`、`KEY_SORT` の 3 ブール、制約なし、8 genome。
`notes` に次を書く — (a) `RWLOCK` は live 分岐だが bare define で直交操作できないため軸にしない、
(b) `INSERT_*_DELAY_MS` は計測撹乱ノブとして除外 (規律 4)、
(c) この 8 通りは **YCSB workload での数**であり `KEY_SORT` の live site が `include/ycsb.hh` に限られること。
tictoc/cicada は登録しない (D1360 の初手 mocc、段階導入)。

### 3.3 between-run floor の protocol 対応と admission

- baseline を protocol から引く写像にする。silo は現行値を 1 bit も変えない。
- 新 protocol の出力 stem は `between_run_noise_<protocol>_t…`。**silo は現行 stem を維持**し、
  既存 4 file の bytes を変えない。出力は create-only とし既存 file を上書きしない。
- **admission は固定 allowlist にしない。** A-3 の指摘を採る。
  「その protocol の CCBench source が現行 pin で trace hook を持つか」を実際に読んで判定し、
  証拠が見つからなければ **拒否側に倒す** (fail-closed)。build・measure・write より前に拒否する。
  述語の名前と docstring は、それが**何を検査していないか**を明示する (D1362 の精神) —
  hook の意味論的正しさも、verifier が通ることも証明しない。
  これにより mocc の trace 移植が land した時点で述語は自動的に真へ変わり、
  「移植後も拒否し続ける恒真検査」にならない。

### 3.4 層 3 の floor 照合キー

- 照合キーを `(protocol, records, threads, workload)` にする。
- campaign 側の protocol は **WAL `build_start.payload.genome` の canonical から取る**。
  campaign.lock / whiteboard / variant 名には protocol が実在しない (実測済み)。
- protocol が欠落・不正・複数なら、report は生成するが両 floor を `no-matching-env-record` にする。
  誤った floor を採るより欠落を明示する方へ倒す。
- **within-run の legacy 扱い:** `noise_floor` block を持ち `genome` を持たない歴史的 record は
  silo campaign に限って一致させる。ただし **その一致が「genome を持たない legacy record である」
  という根拠を report に明記させる**。値の出所を「silo と確認した」と読める書き方をしてはならない。
  A-1 の残余 (calibrator が mocc binary で genome 無し record を書ける) は本 wave の変更で
  作られたものではないが、黙って追認しない。段 7 で残余として記録する。

### 3.5 canonical genome の解析

screening と層 3 の両方が floor JSON の `genome` を解析する。**解析規則を 1 箇所に置き、両者が同じものを使う。**
`|` の前を取るだけにせず、欠落・非文字列・`|` 不在・空 protocol を拒否する。
既存 private parser (`artifact_admission`) を二重権威にしない — 本 wave で足すのは floor JSON 用の
最小の共有 helper 1 本とし、置き場所は実装子が実在の依存方向から決める。

### 3.6 意図した受理集合の変更 (宣言)

- workload が一致しても `genome` を欠く between-run floor は **新たに拒否**する。
  これに当たる既存 test fixture (`test_screening_driver.py` の legacy fixture) は
  canonical genome を持つよう **fixture を直す**。期待値の反転・緩和・skip・削除ではない。
- `space_for("mocc")` が `KeyError` から受理へ変わる。
- 現行 pin での mocc floor 生成は build 前に拒否される。

### 3.7 scope 外 (実装しない・残余として記録する)

B-1 (certified calibration `registered/` の閉包)、B-2 (screening の records/threads 照合)、
within-run producer への protocol 記録、tictoc/cicada 登録、certified mocc campaign 経路。
いずれも **本 wave が作った欠陥ではなく、悪化もさせない**。

## 4. 変異事前登録 (DW-M01)

実装前に登録する。各変異は単一理由性を実装子がコードで確認し、確認できなければ登録を取り下げる。

| ID | 変異位置 | 変異内容 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `screening_driver.load_between_run_floor` | protocol 比較を除去 | KILLED | 同一入力を拒否する層が前後に無い。層 3 は別 consumer で本 test を通らない |
| M2 | `layer3_report._calibration_floors` | 照合条件から protocol を除去 | KILLED | screening は本経路に参加しない |
| M3 | `between_run_floor` の trace-hook 述語 | 常に真へ倒す | KILLED | 親が実測: `source_digest` の ALLOWLIST は既に mocc を含み、buildcache も protocol 汎用で、mocc build を止める層は他に無い |
| M4 | `genome.SPACES` | `mocc` entry を除去 | KILLED | `space_for` に他の受理層が無い |

期待 node は完全集合として実装後に確定し、`DW-M08` に従って記録する。

## 5. 焦点走の対象 (DW-O26、B-4 を採用)

直接: `test_campaign.py`、`test_between_run_floor.py`、`test_screening_driver.py`、`test_layer3_report.py`。
consumer: `test_screening_opt_in.py`、`test_backoff_sweep.py`、`test_s6_sort_sweep.py`、
`test_s8a_trigger_sweep.py`、`test_guided.py`、`test_p2_2_site_aware.py`、
`test_t1416_backoff_compiler_binding.py`。
内容走査型 (名前 grep から漏れる): `test_s8b_floor_campaign.py`、`test_official_perf_closure.py`、
`test_ccbench_spawn_sites.py`、`test_pegasus_floor_scoping.py`。
これらは受入全走の代替ではない。全走は段 7 の記録 commit 後に行う。

## 6. 分割

**Codex `role=author` 1 単位**とする。producer (`between_run_floor`) と consumer
(`screening_driver` / 3 caller / `layer3_report` / schema) が 1 本の契約でつながっており、
分割すると契約が単位を跨いで壊れる。genome 登録は技術的には分離できるが、
受入を揃える必要があるため同じ単位に置く。
