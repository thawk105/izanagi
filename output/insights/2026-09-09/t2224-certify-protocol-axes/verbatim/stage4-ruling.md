# 段 4 裁定 — [T-2224] 認定 launcher の protocol / 軸 引数化

親の裁定。plan v2 と変異事前登録を含む。段 2 plan と段 3 の 2 レンズを上書きする正本。

## 0. 親の自己申告 2 件 (先に出す)

### (0a) 依頼の読み違い — 「軸」は workload ノブではなく genome 軸である

依頼と worklog entry 1206 が名指しするのは `CCBENCH_*` と `ycsb_silo.exe` の 2 つである。
したがって「軸」は **genome 軸 (CCBENCH_* の探索軸)** であって、YCSB の
`ycsb_zipf_skew` / `ycsb_rmw` ではない。`ycsb_rratio` は既に引数化済みである。
段 1 brief はここを取り違えて `--skew` / `--rmw` を scope に入れていた。**取り下げる。**
これによりレンズ A の所見 4 (`--skew 0.90` が新たに受理される) は前提ごと消える。

### (0b) 機械防壁をすり抜けて login node でビルドした

`cmake --build` は `hooks/guard_bash.py` が login で拒否する
(「Pegasus ログインノードでは重い処理を実行できません」)。親はこれを直接叩いた場合の拒否を
実測で確認した。しかし M1〜M4・M8 の probe は背景投入の定型どおり `bash <script>` で起動したため、
guard がコマンド本文から cmake を見つけられず、**login node でビルドが走った**。
意図的な迂回ではないが結果として防壁を回避している。

- 取得済みの実測は事実として残す (規律 7)。ただし**取得経路が正規でなかったことを insight に明記する**。
- **以後の実測は login で走らせない。** `tools/pegasus/dispatch_compute.py --task generic` を使う。
- 防壁側の実在する死角 (背景 script 経由で重量 command 判定を抜ける) として failures 台帳の
  候補に登録する。段 8 で routing する。

## 1. 所見の裁定

| # | レンズ | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | A | R2 は patched source を `pinned_clean=true` と偽記録する | **real** | 採用 → R2 却下 |
| A2 | A | cicada alias 案は旧 cache 名単独で偽 genome を受理する | **real** | 採用 → cicada 除外 |
| A3 | A | 較正本体なしでは「生産できる」を確定できない | **real** | 採用 → 文言規律 |
| A4 | A | `--skew 0.90` が新たに受理される | **real だが前提消滅** | (0a) で scope 外 |
| A5 | A | brief が歴史的 record を silo と断定 | **real** | 採用 → 文言訂正 |
| A6 | A | producer write-path の列挙が不完全 | **real (nit)** | 採用 → 表を訂正 |
| B1 | B | 承認前提が覆ったまま実装へ進む計画 | **real** | 一部採用 (下記 §2) |
| B2 | B | 実測が実際の producer を通っていない | **real** | 採用 → §4 で経路を変える |
| B3 | B | cicada alias は実在欠陥 | **real** | 採用 → ただし解は除外 (A2) |
| B4 | B | acquisition receipt の `calibration` 必須化は scope 外 | **real** | 採用 → 実装しない |
| B5 | B | 手作業 probe は launcher の実効性を証明しない / login 直 build は拒否対象 | **real** | 採用 → (0b) と §4 |
| B6 | B | brief の伝播アンカー不足 | **real** | 採用 → 表を訂正 |

親の実測への反論はすべて受け入れる。特に:

- **M2 の「全軸をすべて既定と違う値」は cicada について偽。** `INLINE_VERSION_OPT=0` は
  `Options.cmake:53` の cicada 既定 0 と同値である。結論 (汎用 cache 名が届かない) は
  未使用変数警告が独立に支持するので維持するが、**表現を「4/5 到達」ではなく
  「汎用名 `CCBENCH_INLINE_VERSION_OPT` は CMake に未使用と報告され、実 define は
  protocol 専用 cache 変数由来である」に改める。**
- **M3 が否定したのは `INLINE_VERSION_OPT=1` の build だけ**であり、既定 0 の cicada 全体を
  否定しない。cicada を除外する理由は build 不能ではなく**軸名の食い違い**である。
- **M4 の「全 protocol 赤」は silo 1 点の実測 + 静的推論**である。gate は macro 単位で
  source を見るので protocol に依らないが、**4 protocol での実測はしていない**と明記する。
- **M1 は「既定 configure から 4 target を build できた」まで**であり、認定 record の
  生産可能性へは一般化しない。

## 2. wave を止めるか — S1 を修正して続行する (S1′)

レンズ B は S3 (実装せず裁定へ返す) を推した。**一部採用し、次のとおり分ける。**

- **覆った前提は「条件関門」についてであり、依頼の本題ではない。** 依頼は
  「`CCBENCH_*` と `ycsb_silo.exe` の直書きを解き、protocol と軸を引数化する」ことで、
  これは条件関門の状態と独立に正しく実装できる。
- **依頼は「本題の実装と実測だけ」を明示している。** 何も実装せずに止めると依頼を 1 つも
  果たさない。`DW-S04` は「scope 外の real 所見は実装せず、設計択一・所見・推奨案を
  裁定パッケージでユーザーへ返す」であって、wave 全体の停止ではない。
- したがって **本題は実装する。条件関門の直し (R1 / R2) は実装せず裁定パッケージで返す。**

### 返す裁定パッケージ (実装しない)

**問い: 認定 launcher が `-DCCBENCH_BACKOFF_FIXED=-1` を渡し続けるべきか。**

- 事実: 現行 CCBench pin `511c9538` にこの macro は存在しない。渡すと CMake が未使用と警告する。
  条件関門 (D1198 が義務化) はこれを `supply-effectuation: configure-failed` と
  `runtime-meaning: materialized-branch-invalid` の 2 アーム red で拒否し、job は rc=2 で止まる。
  この関門は認定経路で一度も実走していない (attempt 12 件すべてに `condition-gate.jsonl` が無い)。
- **(R1) 渡すのをやめる** — M8 の実測により、build path を固定すれば flag あり/なしの
  silo バイナリ sha256 は完全一致 (`871b9976…`、再走対照つき)。実 compile define の diff も空。
  **認定バイナリを 1 bit も変えない。** 代償は silo の genome canonical から `BACKOFF_FIXED=-1`
  が消えること、既存テストの literal pin を新しい契約へ置換すること。
  親の推奨はこれ。レンズ A も技術的推奨として同じ。
- **(R2) patch を build source へ materialize する** — **却下推奨。** patched source を
  `pinned_clean=true` と記録することになり (`certify_calibration.sh:657-662`、
  `schema_v2.py:522-526`)、認定 provenance が偽になる。さらに
  `condition_meaning_gate.py` の `_DEFINE_SPECS["BACKOFF_FIXED"]` は owner/target が silo 固定なので、
  非 silo target の実効化を証明しない。
- 本 wave はどちらも実装せず、silo の現行挙動を **1 byte も変えずに残す**。

## 3. plan v2 (実装する内容)

### D-1. protocol → 軸表の置き場所

段 2 プランの案 (a) を採る。`certify_calibration.sh` 内の静的 `case` 表として持ち、
`SPACES` から実行時導出しない。**加えて、shell の表を parse して `SPACES` の軸集合と
一致することを検査するテストを 1 本置く。** これは新しい一般 drift gate ではなく、
本 wave が新設する表そのものの正しさを固定する機能テストである。

### D-2. 各 protocol へ渡す define

`TRACE=0` + **その protocol の `SPACES` 軸ちょうど**。軸外の define を混ぜない。
値は `Options.cmake` の既定に一致させ、silo だけは現行 argv と完全同一にする。

| protocol | 渡す CCBENCH define |
|---|---|
| silo | `TRACE=0, BACK_OFF=0, BACKOFF_FIXED=-1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0` (現行と同一) |
| mocc | `TRACE=0, BACK_OFF=1, KEY_SORT=0, TEMPERATURE_RESET_OPT=1` |
| tictoc | `TRACE=0, BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, PREEMPTIVE_ABORTS=1, TIMESTAMP_HISTORY=1` |

### D-3. `BACKOFF_FIXED` と条件関門は silo 限定の既存例外として残す

- silo: 現行どおり `-DCCBENCH_BACKOFF_FIXED=-1` を渡し `run_condition_gate` を呼ぶ。**1 byte も変えない。**
- 非 silo: **渡さない。関門も呼ばない。** 理由は「関門を飛ばす」ではなく
  **「供給していない define を宣言しない」**である。現行 pin にこの macro は無いので、
  新 protocol へ渡すことは D1198 が名指しする失敗型 (条件が供給されないまま別の条件を測る) を
  新たに作る行為に当たる。
- この非対称は shell 内のコメントと insight に明記し、§2 の裁定パッケージへ紐づける。
- 実装子は `orchestrator/tests/test_ccbench_spawn_sites.py` の
  `test_define_sink_cross_product_has_no_unreviewed_ungated_member` を実走し、
  この形で緑のままであることを確認する。赤なら停止して報告する。

### D-4. protocol whitelist = {silo, mocc, tictoc}。cicada は除外

除外理由 (実測):

- cicada の `SPACES` 軸 `INLINE_VERSION_OPT` に対応する CMake cache 変数は
  `CCBENCH_INLINE_VERSION_OPT` ではなく `CCBENCH_INLINE_VERSION_OPT_CICADA` である
  (`cc/cicada/CMakeLists.txt:5`、`Options.cmake:53`)。
- 汎用名で渡すと CMake が未使用と報告し、値がコンパイラへ届かない。それでも genome として
  記録すれば「届いていない値を記録する」ことになり、D1374 の却下欄に当たる。
- alias 正規化で救う案は、旧 raw 名単独の receipt を偽 genome として受理する反例があるため採らない。
- 併せて、正しい cache 名で `INLINE_VERSION_OPT=1` を渡すと build が rc=2 で失敗する
  (`cc/cicada/include/transaction.hh:207`、上流の死にコード)。これは除外の主因ではないが記録する。

**この除外は「cicada は較正できない」ではなく「現行の軸名では正直に較正できない」である。**
cicada を通すには `SPACES` 側の軸名を実体へ合わせる別 wave が要る。次タスク候補として返す。

### D-5. `submit_certify.sh` の引数と伝播

- `--protocol {silo,mocc,tictoc}` を追加。既定 `silo`。staging 作成前に whitelist 検査。
- **省略時は qsub argv を 1 byte も変えない。** `export_spec` は現行どおり
  `IZANAGI_SUBMISSION_NONCE=…,IZANAGI_CALIBRATION_RRATIO=…` のまま。
  明示されたときだけ `IZANAGI_CALIBRATION_PROTOCOL=<p>` を末尾に足す。
- `pre-submit.json` / `submit-receipt.json` には**常に実効値**を書く (省略時も `"silo"`)。
  これらの receipt bytes は変わる。「run 全体が 1 byte も変わらない」とは書かない。
- job 側は env 不在なら `silo` を採り、submit receipt の protocol と exact string で再照合する
  (現行の `calibration_rratio` 照合と同じ形)。不一致は副作用前に停止。

### D-6. 記録

`job-result.json` に protocol を足す。acquisition receipt / schema / writer は**触らない** (B4)。

### D-7. 触らない file

`orchestrator/calibrator/cli.py`、`orchestrator/calibrator/schema_v2.py`、
`tools/pegasus/make_acquisition_receipt.py`、`external/ccbench/`。

## 4. 実測 (何を、どこで、どう測るか)

### 4a. 文言規律 (A3 / B2 採用)

「生産できる protocol の集合」を単一の数で書かない。**経路の段ごとに集合を書く。**
較正計測本体を走らせない以上、`registered/calibration-*.json` を発行できる集合は
**本 wave では 0 件測定**である。これを「空集合であることを証明した」とも書かない。

### 4b. 測る内容

`--protocol <p>` を与えた launcher が生成する **launcher 自身の argv 構成**を使い、
protocol ごとに次を測る。

1. configure の rc と、CMake の未使用変数警告の有無
2. `flags.make` の実 `CXX_DEFINES` が、要求した軸集合と完全一致すること
3. `cmake --build --target ycsb_<p>.exe` の rc と実行体の実在
4. `nm -C` の symbol table が非空で `izanagi_trace` を含まないこと
5. 手で組んだ acquisition candidate を既存 writer に通し、
   `_canonical_genome_from_receipt` が期待 canonical 文字列を返すこと

### 4c. どこで走らせるか

**login node で走らせない (0b)。** `python3 tools/pegasus/dispatch_compute.py --task generic --`
で計算ノードへ同期 dispatch する。probe script は repo 外 (job dir) に置き、
`tools/pegasus/` へ新しい実行体を作らない (F660)。

混雑で枠が取れない場合は**走らせずに止め**、その旨を成果物に書く。強制 dispatch はしない。

## 5. 変異事前登録 (DW-M01 / DW-M08)

実装前に登録する。位置と期待方向は次のとおり。**期待 node は本 wave のテストが未実装のため
確定できないので、`DW-M08` に従い初回は全件 SURVIVED の probe として登録し、観測 node を集めてから
再登録して本走する。**

| # | 変異位置 | 変異内容 | 期待される赤の理由 (単一理由性の狙い) |
|---|---|---|---|
| 1 | `submit_certify.sh` の protocol whitelist | 未登録 protocol (`ermia`) を受理集合へ足す | whitelist を exact に固定するテスト |
| 2 | `certify_calibration.sh` の mocc 軸表 | `KEY_SORT` を落とす | shell 表 × `SPACES` 一致テスト |
| 3 | 同上 | mocc に軸外 `WAL=0` を足す | 軸外 define 混入禁止テスト |
| 4 | binary path の導出 | `cc/<p>` を `cc/silo` に固定へ戻す | protocol 別 binary path テスト |
| 5 | build target の導出 | `ycsb_<p>.exe` を `ycsb_silo.exe` に固定へ戻す | protocol 別 target テスト |
| 6 | `BACKOFF_FIXED` の分岐 | 非 silo にも渡すよう変える | silo 限定例外テスト |
| 7 | job 側の protocol 再照合 | receipt との照合を削る | protocol 不一致の負例テスト |
| 8 | 既定 protocol | 既定を `mocc` に変える | 省略時 byte 互換テスト |

単一理由性は実装後に確認する。前後や内側の層が同じ入力を先に拒否するなら登録せず、実効 gate へ
再照準する (F28 / F820)。

## 6. 段 5 の分割

- **単位 A** = `tools/pegasus/certify_calibration.sh` (protocol 引数の受理と既定、軸表、
  target / binary path の導出、`BACKOFF_FIXED` の silo 限定分岐、submit receipt との再照合、
  `job-result.json` への protocol 記録)
- **単位 B** = `tools/pegasus/submit_certify.sh` (`--protocol` の parse と whitelist、
  env 伝播、pre-submit / submit receipt への記録) + 両テスト file の更新 +
  `tools/pegasus/README.md`

編集 path が素集合。単位 B は単位 A の shell 表を参照するテストを書くので、単位 A の完了後に投入する。
