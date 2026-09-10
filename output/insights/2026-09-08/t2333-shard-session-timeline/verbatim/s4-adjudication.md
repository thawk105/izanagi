# 段 4 裁定 — [T-2333] 受入 shard report.json の session timeline 観測 field

親が段 3 の全所見を real / refuted に裁定し、plan v2 を確定した。**実装子はこの文書を plan.md より
優先する。** plan.md と食い違う箇所はこの文書が正しい。

---

## 裁定 1 — `_REPORT_FIELDS` への必須追加は行う (A#1 / B#1 は blocker としては refuted)

### 所見
両レンズが「`session_timeline` を `_REPORT_FIELDS` へ必須追加するのは D1647 の
『gate・判定・受理集合には触れず』違反である」と主張した。

### 裁定: **refuted (blocker としては不成立)。(P1-a) を維持する。**

理由は 3 つ。

1. **その読みでは裁定が実行不能になる。** `merge_reports` は `set(report) != _REPORT_FIELDS` で
   厳密一致を要求する (tools/acceptance_shards.py:618)。したがって「report.json に field を足す」
   実装は (a) `_REPORT_FIELDS` を伸ばす か (b) 厳密一致を緩める の 2 つしかない。
   (b) は明らかに gate の弱体化で規律 2 に反する。「key 集合の字面が変わってはならない」と読むと
   D1647 は自分が命じた行為の唯一の実装をすべて禁じることになる。裁定は実行できるように読む。
2. **走行の受理集合は変わらない。** shard report は 1 回の走行の中で書かれ、同じ走行の中で
   読まれる (`create_session` が走行ごとに session dir を作り、`_load_reports` はその session
   だけを読む)。producer と consumer は同じ commit で出荷される。この変更以前に書かれた report が
   新しい `merge_reports` に渡ることはない。**以前 certified になった走行が reject されることはない。**
3. **B#1 が挙げた「旧 14-key を厳密に読む既存 consumer」は現物で refuted。**
   `output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py:501` は 2026-08-24 の
   insight 用の入力準備 script である。親が実測した: `orchestrator/tests` と `tools` から
   参照する test / tool は 0 件 (`git grep -q` rc=1 を 2 本)。さらに同 script は
   `shard_count == 2` と当時の固定 `EXPECTED_COUNTS` を要求するので、そもそも新しい report を
   食わせられない。自分の insight の凍結入力だけを読む歴史記録である。

### ただし所見の核は採用する → 裁定 2 へ

---

## 裁定 2 — `validate_report_evidence` への timeline 形検査は **足さない** (A#1 / B#1 の核を採用)

### 裁定: **plan の「形の検査を足す」設計を却下する。**

plan は `session_timeline` の key 集合・型・有限性・非空性を `validate_report_evidence` から
検査し、違反を `report-invalid` にする設計だった。これは却下する。

理由:

- ユーザー指示は「gate・判定は足さず」「本題の実装だけ。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外」である。新 field 用の検査 helper を足すのは**検査の追加**であり、
  それが守る危険 (壊れた timeline) は実在の欠陥ではなく仮想リスクである。
- 検査を足さなければ、**観測値の内容が判定を変える経路が構造的に存在しなくなる。**
  A#1 / B#1 の懸念は設計から消える。「timeline に基づく判定・gate ではない」と弁明する必要も無い。
- `_REPORT_FIELDS` への追加だけで、key の存在は既存 gate が保証する。それ以上は要らない。

**実装子への指示:** `validate_report_evidence` (tools/acceptance_shards.py:518) は **1 行も変えない。**
timeline 専用の検査 helper を新設しない。`_REPORT_FIELDS` (同 61) にだけ `"session_timeline"` を足す。

**gate の禁止の署名:** `validate_report_evidence(report, records, selected, expected_junit_path)` は
`report["session_timeline"]` を読んではならない。読む実装は拒否する。

**通る正例:** `_reports()` が作る report に正規の `session_timeline` を載せた状態で
`_merge(_reports())` が `(0, "ok")` を返すこと。

---

## 裁定 3 — collection 終了時刻は `pytest_collection_finish` (trylast) で採る (A#2 / B#2 = real、採用)

### 所見
plan は `pytest_collection_modifyitems` の末尾で時刻を採る。しかし acceptance plugin の同 hook は
`trylast=True` の**非 wrapper** であり、その後に conftest 側の wrapper が yield 後処理
(`_validate_real_repo_shard_state`、`_strip_real_repo_loadgroup_suffix`、
`_reorder_acceptance_items_by_duration`) を実行する (orchestrator/tests/conftest.py:2065-2077)。

### 裁定: **real。採用する。**

放置時の成果物影響: `collection_finished_epoch_s` が実際より早くなり、LPT 並べ替えと suffix 除去の
所要が「collection 後の空白」として report に誤って記録される。T-2273 が分解したいのは正にその
区間なので、この誤りは観測の目的そのものを潰す。

**実装子への指示:** acceptance plugin に自前の `pytest_collection_finish` を `trylast=True` で追加し、
そこで `time.time()` を採る。conftest 側の `pytest_collection_finish` は `tryfirst=True` なので
(同 2100)、trylast の当方が最後に走り、prewarm も含めた collection 全体の終端を捉える。
`pytest_collection_modifyitems` (tools/acceptance_shards.py:826) の本体は **1 行も変えない**
— 並行 wave の 837〜850 行に触れないという制約も同時に満たす。

---

## 裁定 4 — 観測の欠測・異常は受入の rc を変えてはならない (A#3 / B#3 = real、採用)

### 所見
- report 組立は `except Exception` で `session.exitstatus = INFRA_RC` に落ちる
  (tools/acceptance_shards.py:1023 付近)。plan の `float(report.start)` は属性欠落・非数値で例外を投げうる。
- `_worker_payload` (同 913) は try の外で呼ばれるので、そこで例外が出ると hook 自体が落ちる。
- xdist の crash `TestReport` は `worker_id` を持たず `start` / `stop` の既定値は 0。
  無条件に集計すると存在しない `"serial"` worker と epoch 0 が report に混入する (B#3、実測)。
- worker 異常終了 (`worker_errordown`) では custom workeroutput が届かない。

### 裁定: **real。採用する。**

放置時の成果物影響: test も scheduler も既存 evidence も同一なのに、観測の採取失敗だけで
shard report が生成されず受入が rc 16 になる。

**実装子への指示 (不変条件):**

- **観測の採取・組立は、いかなる入力でも例外を外へ出してはならない。** `float(x)` を信頼できない
  属性に直接使わない。`getattr(report, "start", None)` で取り、`type(v) in {int, float}` と
  `math.isfinite(float(v))` を確かめてから使う。既存の `duration` の扱い (同 871-873) に倣う。
- **`start` / `stop` は有限かつ `> 0` のときだけ bounds を更新する。** これで xdist の crash report の
  既定値 0 が混入しない。これは観測値の妥当性 filter であって判定ではない。
- **欠測は欠測として記録する。** worker の workeroutput が届かなければ、その worker の
  lock interval は map に現れない。それをエラーにしない。payload 件数と worker 数を突き合わせる
  gate を**新設しない** (scope 外)。
- `_worker_payload` の追加 key は、状態が無くても既定値 (時刻は `None`、interval は `[]`) を返し、
  例外を投げない。

---

## 裁定 5 — `item.config` を直接読まない (B#4 = real、採用)

### 所見
plan の疑似コードは `item.config` を評価する。しかし既存の protocol 契約テスト
`orchestrator/tests/test_real_repo_serialization.py:2088` は `path` / `name` / `originalname` だけを
持つ `SimpleNamespace` を渡す (親が現物で確認)。`item.config` は `AttributeError` になる。

### 裁定: **real。採用する。**

放置時の成果物影響: 既存テストが赤になり、受入全走が certified 結果を出せない。

**実装子への指示:** `getattr(item, "config", None)` を使い、`None` なら計測せず既存の
`_real_repo_locks(access)` へ直行する。同テストが patch する `suite_conftest._real_repo_locks` は
module 属性なので、新 helper は**呼び出し時に module global を引く**形にすること
(import 時に関数を捕まえて保持しない)。

---

## 裁定 6 — 受入台帳 `acceptance_duration_ledger.json` を更新する (A#4 / B#5 = real、採用)

### 親の実測 (権威 probe)
`IZANAGI_ACCEPTANCE_LEDGER_COVERAGE_PROBE` を使って権威と同じ経路で測った。
base c5754d1f4 での測定: rows = 21569、covered = 19419、被覆率 = 90.031990%、余裕 k = 7。
`consumer_keys` 集合は `--collect-only -q` の素朴な行抽出と**完全一致**した (集合等価を確認)。
よって A#4 の「親の測り方が権威と違うかもしれない」は **refuted**、値は権威で確定した。

**その後 main を取り込んで tip = 240ee6360 で測り直した (こちらが現行値):**
rows = 21596、ledger = 19541、covered = 19439、被覆率 = **90.012039%**、**余裕 k = 2**。

main が collection を 27 件増やしたため余裕が縮んだ。**余裕はほぼ無い。**
台帳更新は必須であり、追加した node を 1 件残らず登録しないと受入が赤になる。
main はこの wave の間も動くので、受入直前に測り直す。

### 裁定: **real。採用する。**

放置時の成果物影響: `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` が赤になり、
受入全走が certified にならない。

**実装子への指示:** 追加した test node id を**すべて** (parametrize 展開後の実 node id をすべて)
`orchestrator/tests/acceptance_duration_ledger.json` の `duration_seconds_by_nodeid` へ足し、
`nodeid_count` を同数だけ増やす。所要時間は実測できないので、既存台帳にもある `0.0` を
未実測 placeholder として置く。**90% の閾値を下げてはならない。**
node id は実際の collection から取ること (推測で書かない)。

---

## 裁定 7 — brief の言い回しの訂正 (A / B の nit を採用)

親 brief は「受理集合が変わるため段 2・3 を省かない」と書いたが、正確には
**「report の key 集合は変わるが、受理される走行の集合は変わらない」**である。裁定 1 の理由 2 が正本。

---

## plan v2 — 確定した実装

### 足す field の形 (plan.md の形を採用、ただし null を許す)

```json
{
  "session_timeline": {
    "collection_finished_epoch_s": 1788800000.125,
    "workers": {
      "gw0": {
        "first_test_started_epoch_s": 1788800000.250,
        "last_test_finished_epoch_s": 1788800123.750,
        "real_repo_lock_intervals": [
          {"acquired_epoch_s": 1788800010.5, "released_epoch_s": 1788800021.875}
        ]
      }
    }
  }
}
```

- `collection_finished_epoch_s`: JSON number **または null**。null は未観測を意味する。
- `workers`: dict。**空でもよい** (観測が 1 件も無い場合)。
- worker entry の key は 3 つ固定。`real_repo_lock_intervals` は list (空可)。
- serial 実行の worker key は既存表現に合わせて `"serial"`。
- 時刻はすべて Unix epoch 秒の float。丸めない。
- top-level に足すのは `session_timeline` の 1 key だけ。`SCHEMA` は v1 のまま変えない。

### 編集する file (4 file)

1. `tools/acceptance_shards.py`
   - `_REPORT_FIELDS` (61) に `"session_timeline"` を追加。
   - plugin の module 状態に worker bounds 用 dict を追加し `pytest_configure` (806) で初期化。
   - **新規** `pytest_collection_finish` を `trylast=True` で追加し collection 終了時刻を採る。
   - `pytest_collection_modifyitems` (826) の本体は変更しない。
   - `pytest_runtest_logreport` (862) で `start` / `stop` から worker 別 bounds を更新
     (有限かつ > 0 のときだけ)。
   - `_worker_payload` (913) に collection 時刻と lock interval を追加 (既定値で例外を出さない)。
   - `_controller_state` (928) を拡張。serial は config-local、xdist は全 worker payload から
     collection 時刻の max、lock interval は worker ID ごとの map。
   - `pytest_sessionfinish` (956) の report payload に `session_timeline` を組み立てて載せる。
   - **`validate_report_evidence` (518) と `merge_reports` (603) は 1 行も変えない。**
   - conftest から呼ばれる記録関数 `record_real_repo_lock_interval(config, acquired, released)` を追加。
2. `orchestrator/tests/conftest.py`
   - `pytest_runtest_protocol` (2081) に lock 取得後 / 解放後の時刻採取を足す。
   - `getattr(item, "config", None)` を使う。`None` または shard spec 不在なら計測せず直行。
   - lock 取得が失敗したとき、および解放が失敗したときは interval を記録しない。
   - 内側の例外はそのまま再送出する (置換しない)。
3. `orchestrator/tests/test_run_tests_shards.py` — テスト追加と `_reports()` の更新。
4. `orchestrator/tests/acceptance_duration_ledger.json` — 追加 node の登録と `nodeid_count` 更新。

### テスト (裁定 2 により plan から検査系テストを削る)

必須:

- `_reports()` に正規の `session_timeline` を入れ、既存 merge テストが全部通ること。
- **通る正例**: `session_timeline` を載せた report で `_merge(_reports())` が `(0, "ok")`。
- `session_timeline` を消した report が `report-invalid` になること (`_REPORT_FIELDS` の効果)。
- **`validate_report_evidence` が `session_timeline` を読まないこと** — 中身を壊した (型不正・
  NaN・key 欠落・空 dict) timeline を載せても `_merge` が `(0, "ok")` を返す。これが裁定 2 の
  「判定を足していない」の positive control である。
- `pytest_runtest_logreport` が worker ごとに min start / max stop を採ること (到着順を入れ替えて確認)。
- `start` / `stop` が 0・非有限・欠落の report で bounds が更新されないこと (crash report の混入防止)。
- `worker_id` 不在の非 xdist 実行で `"serial"` に記録されること。
- `_worker_payload` が状態不在でも例外を出さず既定値を返すこと。
- `_controller_state` の serial 分岐が config-local 状態を使うこと。
- `_controller_state` の xdist 分岐が collection 時刻の max を取り、worker ごとに lock interval を保つこと。
  payload が欠けた worker が map に現れないこと (エラーにならないこと)。
- `record_real_repo_lock_interval` が shard spec 不在・state 不在で no-op になること。
- `pytest_runtest_protocol` が `config` を持たない `SimpleNamespace` item で従来どおり動くこと
  (既存 `test_real_repo_serialization.py` の契約を壊さない positive control)。
- lock 取得失敗時に interval を記録しないこと。
- lock 解放失敗時に interval を記録しないこと。
- `access is None` のとき clock を読まず記録もしないこと。
- 内側 protocol の例外が置換されず、そのとき interval が記録されないこと。
- collection 終了時刻が `pytest_collection_finish` で採られること (`modifyitems` 完了より後であること
  を、hook 順序を観測する合成 plugin で確かめる)。

### 変異事前登録 (DW-M01)

実装前に登録する。段 6 で probe し、赤理由が 1 つに絞れることを確認する。

| # | 変異 | 位置 | 期待 |
|---|---|---|---|
| M1 | collection 時刻の採取を `pytest_collection_finish` から `pytest_collection_modifyitems` 末尾へ戻す | acceptance_shards.py | hook 順序テストが赤 |
| M2 | bounds 更新の `> 0` 条件を外す | `pytest_runtest_logreport` | crash report 混入テストが赤 |
| M3 | `getattr(item, "config", None)` を `item.config` へ戻す | conftest | SimpleNamespace 契約テストが赤 |
| M4 | lock 取得失敗時にも interval を append する | conftest | 取得失敗テストが赤 |
| M5 | lock 解放失敗時にも interval を append する | conftest | 解放失敗テストが赤 |
| M6 | `access is None` でも clock を読み記録する | conftest | access None テストが赤 |
| M7 | `_REPORT_FIELDS` から `session_timeline` を外す | acceptance_shards.py:61 | key 欠落テストが赤 |
| M8 | `_worker_payload` から lock interval を落とす | acceptance_shards.py:913 | xdist 集約テストが赤 |
| M9 | controller 集約の collection 時刻を max から min へ変える | `_controller_state` | xdist 集約テストが赤 |
| M10 | serial 分岐で config-local 状態を使わず `_WORKER_PAYLOADS` を要求する | `_controller_state` | serial 分岐テストが赤 |
| M11 | `validate_report_evidence` に `report["session_timeline"]` の非空検査を足す | acceptance_shards.py:518 | 裁定 2 の positive control が赤 |

M11 は「判定を足していない」ことの帰属を確かめる変異である。これが赤にならないなら、
裁定 2 の positive control は恒真である。

### scope 外 (実装しない)

- timeline に基づく判定・gate・閾値・前後関係の検査。
- worker payload 件数と configured worker 数を突き合わせる新 gate。
- `SCHEMA` の v2 化。
- host 間 clock skew の補正。
- receipt / `tools/dev_wave_wait.py` / `MergeResult` への timeline の伝播。
