# [T-2409] B-10 集約の受理経路へ、記録された正しさ判定を束縛する

- wave: `dev-wave-t2409-wal-verdict-bind`
- branch: `worktree-dev-wave-t2409-wal-verdict-bind`
- 起点 local main: `cc9bba523ac7804aadb7891d686bf4c925789a3f`
- 裁定: D1772 (2026-09-08 /rulings 全件 第 14 回、相談で推奨が逆転)
- 実装 commit: `6d7c5c7741d1688ffd630be231eb7c65519b15dd`

## 何を閉じたか

B-10 の legacy 3 系列 report は、block record 45 件の内容を exact に縛る一方で、同じ campaign の
WAL にある `anomalies` / `certified` / `verdict` を一切見ていなかった。45 record と campaign lock を
変えず、`verify_done` の件数 90 と `workload.tag` の内訳 15/75 を揃えたまま WAL を差し替えれば、
anomaly が出ていた走行でも同じ判定の report を発行できた。

`_verification_source_disclosure` の `verify_done` ループへ exact 値述語を 1 つ足して閉じた。

## 着手前の実測 — 既存 literal の再発行は不要 (0 個)

D1772 が「既存 2 系列の literal を再発行せずに追加 exact 条件として重ねられるかを実測せよ」と
命じていたので、着手前に測った。

| 測ったこと | 結果 |
|---|---|
| 「既存の内容 digest」の正体 | `LEGACY_{WRITE_HEAVY,BALANCED,READ_HEAVY}_RECORD_SHA256S`、各 45・計 135 literal |
| 値の出どころ | block record 本体の canonical JSON の sha256。**同じ値が現物 file 内に `record_sha256` として書かれている** (現物は `{schema_version, record_sha256, record}` の封筒形式) |
| 現物からの再計算 | 3 系列とも production 関数で読み直し、literal 集合と完全一致 (各 45/45) |
| block record に 3 field はあるか | **無い。3 系列とも 0/45。** `correctness_certified` はあるが別物 |
| 3 field の所在 | 別 file `runs/wal.jsonl` の `verify_done` payload のみ |

したがって「内容 digest の対象を広げる」を字義どおり行うと **135 個の凍結 file の書き換え**になり、
それは literal の再発行ではなく凍結証拠そのものの改竄で、規律 7 と D1597 に反する。
**D1772 が指示した「追加 exact 条件として重ねる」形なら 135 literal は 1 個も変わらない。**

### 述語が現物で成立するか (DW-O13)

3 系列とも `verify_done` はちょうど 90 件、`anomalies=0` / `certified=true` /
`verdict="serializable"` が各 90/90、field 欠落 0 件。tag は legacy 15 / performance 75。
WAL の stage 内訳は 3 系列とも `build_start` 15 / `build_done` 15 / `verify_done` 90 / `commit` 15。

**系列間の形の差が 1 件:** read-heavy だけ payload に `proof_surfaces` key が余分にある。
述語は名指しの 3 field しか見ないので、余分な key では壊れない (正例で固定した)。

**この実測の射程は、指定 3 campaign の現時点の bytes に限る。** 将来の WAL schema や他 campaign、
live campaign、trial campaign には及ばない。

## 実装

`orchestrator/campaign/b10_backoff_shape_sweep.py` の `_verification_source_disclosure` に 10 行。

- `type(anomalies) is int` かつ `anomalies == 0` かつ `certified is True` かつ
  `verdict == "serializable"`。外れたら `legacy-wal-verdict` の `PreflightError`。
- 整数型の検査は `False == 0` による迂回を塞ぐ。`is True` は `1` を弾く。
- **既存の broad `try/except Exception` の外**に置いた。内側だと新しい `PreflightError` まで
  握り潰されて `wal_read_error` + 空 counts に化ける。
- **unknown tag と unmapped variant の `continue` より前**に置いた。後ろだと、悪い record の
  tag を未知値にするだけで検査を回避できる。

legacy 限定は現行の call graph が担保する。`_verification_source_disclosure` の production caller は
`_collect_report_inputs` の 1 箇所だけで、そこへ到達する campaign は固定 3 ID だけである。

## 段 3 の敵対相談が親の枠組みを 2 点で倒した

親 brief は「D1772 の字義は実装不能なので最も近い代替を採る」という枠で書いていた。**これは誤りで、
段 4 で撤回した。**

1. **D1772 自身が「literal を再発行せずに追加 exact 条件として重ねられるかを実測せよ」と
   書いている。** よって値述語は裁定が名指しした第一候補そのものであって、代替ではない。
2. **「135 file の書き換え or 系列別 whole-WAL digest」の二択も偽だった。**
   `variant` + tag + 3 field に限定した projection digest という第三形がある。
   「read-heavy に `proof_surfaces` があるから系列別 literal が必須」という論証も従って成立しない。
   第三形は**存在を認めたうえで不採用**とした — 新しい digest producer・期待値・対応規則を要し、
   D1772 の「新しい gate 機構は作らない」から遠い。

## 段 6 で見つかった欠陥

- **行番号 pin が動いた (親の実走と段 6 レビューが独立に検出)。** production へ 10 行足したことで
  `run_formal` の build sink が 4051 行から 4061 行へ動き、deferred-gate 登録簿の行番号 pin が
  stale になって既存 3 node が赤になった。登録簿と期待集合の 2 箇所を同期して閉じた。
  もう 1 つの pin (`_build_binary` の 3294) は挿入点より上なので動いていない。
  **親の段 1 pin 閉包の穴** — whole-file sha256 pin は path で探したが、**行番号 pin を
  探していなかった。** consumer 拡張の焦点走 (`DW-O26`) が拾ったので着地前に閉じられた。
- **攻撃の再現 test が無かった (親が検出)。** 実装子は受理側の collector test しか足しておらず、
  T-2409 が名指しした攻撃を再現する拒否側が欠けていた。これが無いと wave の主張を挙動で示せない。
  fix で追加した。

## 主張の限界 (隠さずに書く)

- **束縛するのは WAL に記録された 3 値であって、その生成主体・verifier の実行・block record との
  attempt 対応ではない。** WAL に hash chain は無く (`wal.py` 自身が明記)、真正性は束縛しない。
  3 field を正常値で自己申告した偽 WAL は通る。閉じるには暗号学的束縛 = 新しい gate 機構が要り、
  D1772 が却下し、ユーザーも scope 外と指示している。
- **検査の母集合は「`read_records_checked` が例外なく返した終端済みで parse 可能な record のうち
  `stage == "verify_done"` のもの」に限る。** WAL 欠落・読取例外・未終端 tail は述語へ到達しない。
  ただしこれらの経路では `incomplete_slots > 0` か `wal_read_error` が立った**見て分かる別物の
  report** になるので、T-2409 が名指しした「同じ判定の report が出る」穴には当たらない
  (`_verification_completeness` は一度も raise せず開示するだけであることを親が確認)。
- **collector の test は WAL 述語との結線を通すが、3 validator は stub である。**
  validator は各 record の `submission_receipt` を実 path として開き bytes の sha256 を照合するため、
  repository 内の fixture では通せない。receipt path を書き換えると record 内容が変わって
  `record_sha256` が 45 個の凍結 literal と一致しなくなるので逃げ道が無い。
  **「統合を通した」とは書かない。** validator 側の本物の証拠は既存の専用 test 4 本が担う。
  lock は実物を通している。

## 実測 (親の権威ある実走)

| 走 | 結果 |
|---|---|
| `test_b10_backoff_shape_sweep.py` 単独 (fix 前) | 181 passed、rc=0 |
| consumer 拡張 6 file (fix 前) | 3 failed / 775 passed / 3 skipped、rc=1 (行番号 pin) |
| b10 + ccbench (fix 後) | 226 passed、rc=0 |
| consumer 拡張 6 file (fix 後) | 779 passed / 3 skipped、rc=0 |
| consumer 拡張 6 file (main 取り込み後) | 779 passed / 3 skipped、rc=0 |

consumer 集合は名前の推測でなく参照関係で引いた (`DW-O26`) —
`b10_backoff_shape_sweep` を参照する test は 6 file だけである。

## 変異 (probe → 再照準 → 本走)

`mutation-spec-probe.json` を全件 SURVIVED で登録して観測 node を集め、
その観測集合を期待 node に据えた `mutation-spec-final.json` で本走した (`DW-M07`)。

**本走: baseline PASSED、12/12 KILLED、MISMATCH 0・SURVIVED 0・TIMEOUT 0、期待 node 完全一致。**

| id | 種別 | 変異 | 期待 node 数 |
|---|---|---|---|
| M1 | negative | 述語ブロックを削除 | 11 |
| M2 | negative | `type(x) is int` を `isinstance` へ | 1 |
| M3 | negative | `== 0` を `>= 0` へ | 4 |
| M4 | negative | `is True` を `== True` へ | 1 |
| M5 | negative | `certified` 条件を削除 | 3 |
| M6 | negative | `verdict` の exact 比較を truthy へ | 1 |
| M7 | negative | 連言を `or` へ | 11 |
| M8 | negative | 述語を unknown tag の `continue` より後へ | 1 |
| M9 | negative | 述語を unmapped variant の `continue` より後へ | 2 |
| M10 | negative | 送出を握り潰して `continue` へ | 11 |
| M12 | negative | collector から disclosure 呼出しを迂回 | 2 |
| **M11** | **positive (過剰拒否の正例)** | stage filter を削除し全 stage に 3 field を要求 | 1 |

- **M11 が受理集合を縮小する wave に必須の「承認外の過剰拒否の正例」** (`DW-M01`)。
  3 field を持たない非 `verify_done` frame を含む正例だけが赤になり、帰属が 1 つに絞れている。
- **M6 が `[verdict-missing]` を殺さないことは事前に裁定済み** (A9)。`None` は元の述語でも
  truthy 化した述語でも拒否されるため、その case は mutant の証拠にならない。期待から外してある。
- 変異 runner の対象は b10 test file 単独とした。行数が変わる変異 (M1 等) が
  `test_ccbench_spawn_sites.py` の行番号 pin を巻き込んで機構と無関係な赤を出すのを避けるため。
  同 file の緑は最終 commit で別途確認している。

## 手順上の事故 (親起因、既知の型)

`tools/check_ai_provenance.py` の全史監査を `timeout 300` で打ち切り、dispatch 親が SIGTERM されて
PBS job が孤児化し、orphan hold が立って以後の dispatch が全部 rc=16 になった。
**これは F333 に何度も記録され、auto-memory にも「削除対象は 2 つある」まで書かれている既知の型で、
新しい事実は無い。** 記録があったのに読まずに踏んだこと自体が事象である。
復旧は既載の契約どおり — 手動 qdel をせず (F47 型ラッチを立てないため)、`qstat` の一覧で
request `985457.nqsv` が稼働中 (STT=PRR) と確認できたので終端まで待ち、
source の clean と HEAD 一致を確かめてから `orphan-hold.json` と
`orphan-holds/985457.nqsv.json` の 2 file を削除した。作業ツリーへの被害はゼロ。

## [T-2408] 着地後の取り込みと追随 (2026-09-09)

本 wave の受入待機中に [T-2408] / D1771 が同じ 2 file を大きく変えて着地した (+1215 / -223)。
先方は約束どおり本 wave の変更面 (`_verification_source_disclosure` の `verify_done` ループと、
`_collect_report_inputs` 内の同関数の呼出し 2 行) に触れていない。

### 競合 1 件 — 行番号 pin が「両親のどちらでもない値」になった

`test_ccbench_spawn_sites.py` の deferred-gate 登録簿が pin する build sink の行番号で 2 箇所競合した。
本 wave 側 4061、取り込み側 4460。**2 つの wave が同じ file の別の場所へ行を足したので、
merge 後の真の値はどちらでもない。** merge 後の現物で測ると `run_formal` 内の `run_campaign(`
呼出しは **4470** 行だった。両親と異なる実装面なので Codex `role=author` が解決し、
親も独立に測って一致を確認した。

### API 追随 2 点

report 経路が live `Preregistration` を作らなくなった結果、次の 2 つが変わった。

1. 3 つの `_legacy_*_binding()` から引数が消えた (`TypeError` で 2 node が赤)。
2. `_assert_report_lock_binding` へ `expected_lock_sha256` が必須引数として増えた。
   **本 wave の collector 正例は合成 lock を書いていたので、lock 全体の digest 照合で必ず落ちる。**

追随は Codex `role=author` 2 巡で閉じた。**production は 1 行も変えていない。**

- 1 巡目: 引数を外し、[T-2408] が収載した現物 lock snapshot を `_historical_layout` 経由で配置。
- 2 巡目: 1 巡目が自分で入れた `assert spec == prereg.spec` が原因で残った赤を閉じた。
  collector は現物 lock から導出した歴史 spec を validator へ渡すので、合成 spec との等値比較は
  必ず落ちる。合成 `prereg.spec` への依存を外し、受信した spec の `spec_sha256` が歴史 literal で
  あることを固定し、cell も受信 spec の `block_orders` から組み立てる形へ変えた。

**2 本の test が検査している中身は変えていない。** 拒否側は依然として、件数 90・tag の内訳
legacy 15 / performance 75・variant の列・block record 45 件・lock bytes をすべて保ったまま
1 record の `anomalies` だけを 0 から 1 にし、`legacy-wal-verdict` で止まることを固定している。

### 取り込み後の実測

| 走 | 結果 |
|---|---|
| `test_b10_backoff_shape_sweep.py` 単独 | 203 passed、rc=0 |
| consumer 拡張 6 file | 800 passed / 3 skipped、rc=0 |
| **変異本走 (最終 tip `75a760478`)** | **baseline PASSED、12/12 KILLED、MISMATCH 0・SURVIVED 0、期待 node 完全一致** |

変異は 12 anchor すべてが merge 後も一意に一致することを確かめてから走らせた (`DW-M07`)。
台帳は `mutation-ledger-postmerge.json`。

`test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy` は、取り込み直後に単独では
赤だったが (main の clean checkout でも同じ赤を再現した = 本 wave 非帰属)、file 全体の走行では
緑である。順序依存であり、本 wave は触っていない。
