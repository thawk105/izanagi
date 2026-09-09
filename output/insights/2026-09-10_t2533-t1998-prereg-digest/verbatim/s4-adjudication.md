# [T-2533] 段 4 裁定とプラン v2

## 結論

**実装する。** 段 3 の 2 レンズが挙げた 16 件のうち、must-fix 8 件はすべて real で、うち 5 件は
**同じ 1 つの欠陥の別の面**である — 段 2 plan の事前登録は、consumer の受理集合を実際には束縛せず、
呼び手が手組みした identity をそのまま受理する形になっていた。プラン v2 はここを閉じる。

## 親が現物で実測して確定させたこと (裁定前提実測)

1. **target の source digest は段 1 brief / 段 2 plan の値が誤りだった。** 正式 producer は
   `patches/silo-backoff-fixed.patch` を適用した状態で campaign を走らせ
   (`orchestrator/campaign/backoff_sweep.py:410-411`)、evidence はその状態から解決される
   (`orchestrator/campaign/loop.py:627-630`)。親が `patchharness.applied` の内側で測り直した結果:
   - baseline `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6` (**変わらず**、
     `src_token="stock"`。patch は `BACKOFF_FIXED=-1` では inert)
   - target `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` (**変わる**)
   測定後に作業木は patch 前へ戻り、`git status --porcelain` は空、gitlink も不変 (DW-O19)。
   生出力は `artifacts/probe-source-digest-patched.json`。
2. **既存負例 `test_launcher_script_digest_is_bound_to_preregistration`
   (`orchestrator/tests/test_t1998_stock_inline_pair.py:501-515`) は、拒否 field が
   `reservation.binding.script_sha256` であることを要求している。** plan の「先行 scalar 比較」を
   そのまま入れると、この node が赤になる。レンズ B の指摘は現物で確認した。
3. **`docs/README.md:13-38` は事前登録の正本を個別に列挙している。** 新文書は地図へ載せる必要がある。
4. **受入所要時間台帳の被覆 gate は
   `orchestrator/tests/test_acceptance_schedule_order.py:706-713` の `coverage >= 0.90`。**
   新 test file は作らないので harness の追加登録は不要。

## real / refuted

| # | 出所 | 判定 | 採否 | 理由 |
|---|---|---|---|---|
| A1 | レンズ A | **real (親が実測で確定)** | **採用** | target digest を `678b7203…` へ訂正する。誤値のままなら正式成果物は `source-identity-unbound` で全件拒否され、T-1998 の適格値が 1 本も得られない |
| A2 | レンズ A | **real** | **採用 (限界の明記のみ)** | login の `g++` と compute の `g++` の同一性は証明できない。ただし食い違えば `source-identity-unbound` で fail-closed に落ち、偽の緑は生まれない。文書の限界節と insight に明記する。**新しい gate は足さない** |
| A3 / B2 | 両レンズ | **real** | **採用 (設計変更)** | D1790 の 2 定数は**どちらも事前登録文書の sha** である。job body sha への読み替えは逐語と違う。下記「D1790 の 2 定数」で閉じる |
| A4 | レンズ A | **real** | **採用 (同じ機構で閉じる)** | 呼び手が渡す `repository_commit` を artifact と比べるだけでは恒真。測定時点の文書 blob sha で束縛する |
| A5 / B3 | 両レンズ | **real** | **採用** | loader が optional では、結果を見た後に artifact から写した identity が受理される。consumer 側で文書由来 identity と exact 一致を要求して閉じる |
| A6 | レンズ A | **real** | **採用 (文書の書き方として)** | 発火しない field は文書に「記述であって発火しない」と明記する。**発火させるための gate は足さない** |
| A7 | レンズ A | **real** | **採用** | 単独で殺せない loader テストは変異事前登録から外す |
| A8 / B1 | 両レンズ | **real** | **採用 (対処済み)** | plan の壊れた literal は `artifacts/AUTHORITATIVE-VALUES.md` を値の正本にして遮断する |
| B4 | レンズ B | **real (親が実測で確定)** | **採用** | 先行 scalar 比較を置かない。文書由来 identity の照合は既存の artifact 比較の**後**に置き、既存負例の拒否 code / field を 1 つも動かさない |
| B5 | レンズ B | **real (静的)** | **条件付き採用** | 台帳登録は先にやらない。段 6 の受入実走で被覆 gate が緑なら触らない (稼働中 T-2417 との衝突を避ける)。赤なら正本 producer の `--add-only` で登録する。**推定値・placeholder は入れない** |
| B6 | レンズ B | **real (親が確認)** | **採用** | `docs/README.md` へ 1 行足す。`docs/pegasus-runbook.md` と `docs/phase3.md` は更新不要 |
| B7 | レンズ B | **real** | **採用** | spool fragment と insight は段 7 の親作業。plan の変更面に無いのは正しい |
| B8 | レンズ B | **real** | **採用** | 2 定数に「値が不等」を要求しない。初版では両者が同値になるのが正しい |
| — | レンズ B「無駄」 | **一部 real** | **一部採用** | 既存正例と重複する `test_current_arm_source_digests_are_accepted` と target 側 drift 負例は作らない。baseline 側 drift 負例だけ足す |
| — | 段 2 plan の `docs/…-preregistration.md:55-145` 等の行番号 | **refuted (行の実在)** | — | 未作成 file の行番号は根拠にならない。実装子には「行未確定」と渡す |

**不採用にした所見はない。** レンズ A の裁定パッケージ候補 3 件のうち 2 件 (D1790 と producer schema の
衝突、一意な measurement commit) は下記の設計で scope 内に閉じた。残る 1 件 (正式経路の CLI / submitter
への loader 不可避化) は **scope 外**として裁定パッケージへ返す。

## D1790 の 2 定数 — 採用する形

D1790 の逐語は「**成果物が記録しているべき事前登録 sha (測定時点の版)**」と「**解析規則の正本として
渡される文書に要求する sha (現行の版)**」の 2 つを別定数にせよ、である。T-1998 の producer は
事前登録 sha を成果物へ書かない (schema 拡張は scope 外)。しかし**成果物は `repository_commit` を
記録している**ので、測定時点の事前登録文書はそこから一意に復元できる。

- `T1998_PREREGISTRATION_PATH` — 事前登録文書の canonical path。
- `MEASUREMENT_TIME_PREREGISTRATION_SHA256` — **成果物側**。成果物が記録する
  `repository_commit` における事前登録文書 blob の sha256 がこの値であることを要求する。
- `CURRENT_PREREGISTRATION_SHA256` — **解析規則側**。いま渡された作業木の文書 bytes の sha256 が
  この値であることを要求する。

どちらも scalar 一値の exact 比較にする。集合・tuple・allowlist・fallback・「いずれかに一致」を作らない。
**両者は初版では同値になる。同値であることを禁じるテストは書かない (B8)。**
文書を改訂したときに `CURRENT_…` だけが動き、旧 cohort の成果物は
`MEASUREMENT_TIME_…` で引き続き解析できる — これが D1790 が守ろうとしている性質である。
**将来 cohort 用の互換層は作らない (D1790 の逐語)。**

これで A4 も閉じる。呼び手は任意の `repository_commit` を渡せない — その commit の文書 blob が
`MEASUREMENT_TIME_PREREGISTRATION_SHA256` に一致しなければ拒否されるからである。

## プラン v2

### 1. 事前登録の正本文書 (新規、docs のみ)

`docs/t1998-balanced-stock-inline-preregistration.md`。日本語。段 2 plan の節構成をおおむね採るが、
**次を必ず満たす。**

- 固定する実値は `artifacts/AUTHORITATIVE-VALUES.md` の表から取る。**target は `678b7203…`。**
- 機械可読 block は 1 つだけ置き、**consumer が実際に比較する field だけ**を入れる:
  `ccbench_gitlink_commit` / `environment_contract_sha256` / `launcher_script_sha256` /
  baseline・target の `canonical_genome` と `source_bytes_sha256`。
- それ以外 (workload、target_fixed_us、点数、sample 数、推定量、除外規則、arm 順序) は
  **散文の節に書き、「これは記述であって、consumer は module 定数で判定する」と明記する** (A6)。
  機械可読 block へ入れて恒真な保証にしない。
- `repository_commit` の literal を書かない (F36)。束縛規則だけを書く。
- **限界の節**に次を書く: (a) login node で計算した source digest が compute node の値と一致する
  保証はない、食い違えば `source-identity-unbound` で fail-closed に落ちる (A2)。
  (b) 成果物から復元できるのは job body までで、投入器の同一性は復元できない。
  (c) A-5 (但し書き 3) は D1525 により未充足のままで、本書はそれを外さない。
- 値の導出手順 (patch 適用下で `resolve_evidence` を呼ぶ) を再現できる形で書く。

### 2. consumer (`orchestrator/campaign/t1998_stock_inline_pair.py`)

- module 定数として上記 3 つ (`T1998_PREREGISTRATION_PATH`、
  `MEASUREMENT_TIME_PREREGISTRATION_SHA256`、`CURRENT_PREREGISTRATION_SHA256`) を追加する。
- `load_preregistration(repo_root, prereg_commit) -> T1998PreregisteredIdentity` を追加する。
  文書 blob と作業木 bytes の一致、`CURRENT_PREREGISTRATION_SHA256` との一致、
  機械可読 block の厳密 parse (重複 key 拒否・余剰/欠落 field 拒否) を行い、
  `repository_commit` には `prereg_commit` を入れる。
- `consume_balanced_stock_inline_pair` の**既存の比較を 1 つも動かさない**。
  **既存の artifact 比較がすべて通った後**、ratio 計算の直前に次を足す:
  1. 成果物が記録する `repository_commit` における文書 blob の sha256 が
     `MEASUREMENT_TIME_PREREGISTRATION_SHA256` と一致すること。
  2. その blob から導いた identity が、渡された `preregistered` と**exact 一致**すること。
  拒否は既存と同じ構造 (`code` / `field` / `expected` / `actual` / `arm`) を持たせる。
  **既存の拒否 code・field を 1 つも変えない (B4)。**
- **先行 scalar 比較を置かない。** 既存負例 `:501-515` の拒否 provenance を守る。

### 3. テスト (`orchestrator/tests/test_t1998_stock_inline_pair.py`)

既存 file に足す。新 test file は作らない。既存テストの期待値を変えない。

- fixture の `_SCRIPT_SHA` を新 job body digest へ、arm の source digest を
  `2d691b45…` / **`678b7203…`** へ置換する。
- 旧 job body digest `0ef4d41e…` を artifact 側に持つ負例
  (`launcher-script-identity-mismatch` / `reservation.binding.script_sha256`)。
- baseline 側 source digest drift の負例 1 本 (target 側は既存負例と重複するので作らない)。
- 文書由来 identity の照合を殺す変異を捕まえる負例: 成果物の `repository_commit` における
  文書 blob が `MEASUREMENT_TIME_…` と違う場合、および文書由来 identity と渡された identity が
  食い違う場合。
- loader の境界: 作業木 bytes と blob の不一致、`CURRENT_…` との不一致。
  **単独で殺せない (後段の hash 比較が先に赤にする) ものは書かない (A7)。**

### 4. docs 地図

`docs/README.md` の事前登録の並びへ 1 行足す。

### 5. 台帳

段 6 の受入実走の結果で決める (B5)。緑なら触らない。

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認する。

| ID | 変異位置 | 期待 |
|---|---|---|
| m1 | `MEASUREMENT_TIME_PREREGISTRATION_SHA256` の比較を `if False:` で無効化 | KILLED |
| m2 | `CURRENT_PREREGISTRATION_SHA256` の比較を `if False:` で無効化 | KILLED |
| m3 | 文書由来 identity と渡された identity の exact 比較を `if False:` で無効化 | KILLED |
| m4 | 事前登録文書の target `source_bytes_sha256` を旧誤値 `6454d9f34b…` へ差し替え | KILLED |
| m5 | 事前登録文書の `launcher_script_sha256` を旧 digest `0ef4d41e…` へ差し替え | KILLED |
| m6 | loader の blob と作業木 bytes の一致検査を `if False:` で無効化 | KILLED |
| m7 | 2 定数を 1 つの定数へ統合 (同一視) | KILLED |
| m8 | 機械可読 block の重複 key 拒否を無効化 | KILLED |
| m9 (probe) | `MEASUREMENT_TIME_…` と `CURRENT_…` の値が等しいことを禁じる検査は**置かない**ので、両者を同値にする変異 | **SURVIVED を期待** (B8。初版では同値が正しい) |

## scope 外として裁定パッケージへ返すもの

1. **正式経路への loader 不可避化。** production CLI / submitter は今回 scope 外。
   consumer 側で文書由来 identity を強制したので、consumer を通る限り抜け道は無いが、
   「consumer を呼ばずに主張する」経路は塞いでいない。どの entry point を正式経路とするかは裁定が要る。
2. **producer schema へ事前登録 sha を書くか。** 今回は `repository_commit` 経由で復元する形で
   閉じたが、成果物が事前登録 sha を直接記録する方が強い。schema 拡張は D1244 の最小 3 部品の外。
3. **login と compute の compiler identity の証明。** 現状は fail-closed に頼っている。

## 不変条件 (再掲)

- 既存の拒否を 1 つも外さない・緩めない (絶対規律 2)。追加はすべて受理集合を**狭める**方向。
- 既存負例の拒否 code / field を変えない。
- 歴史成果物の digest を書き換えない (規律 7)。
- 既存 A-5 投入器・job body・契約テスト・登録簿の bytes を変えない。
- 正式測定の投入を行わない。qsub を 1 回も打たない。
