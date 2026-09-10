# 段 4 裁定とプラン v2 — [T-2028]

親が段 2 プランと段 3 相談 2 本を裁定し、実装子へ渡す確定版。

## 0. 前提の訂正 (brief からの変更)

- **(P1) は refuted 側で確定。** live preflight は契約の `本走` に含まれない (契約は三段を別名で
  呼び、U11 は exact に `run-ready --live` を止める)。さらに親が独立に確認したとおり、
  **U11 自体が D1623 (2026-09-04、ユーザー裁定) で決着している** — 「免除を与えず現契約どおり
  `未完走` のまま」。したがって live preflight を止める契約条項は無い。
- **(P2) は「床の値」としては維持、「移植の仕方」としては誤り。** 3.0 / 1.0 / 45.0 秒を短くする
  根拠は無い。しかし軸 1 の 45 秒は **retry (3→6→12 秒) と 45 分 cooldown と組で**成立していた値で、
  床だけ移植すると保護不足になる。軸 3 の preflight は末尾に **DBLP 1415 本連続**を持つ。
- **親の「数百行が恒久的に未完走」は精度が誤っていた。** 被害は最大で残り全行に及びうる一方、
  「恒久的」は言い過ぎ。実行記録ではこの精度で書く。

## 1. 親が独立に裏取りした致命的欠陥 (段 3 の所見を超える)

`run_preflight` の行 loop で、送信は try の外にある。

```
request = materialize_request(row)
response = _send_with_raw_commit(...)          # ← try の外
try:
    evidence, probe = _validate_and_classify_response(...)
except ContractError:
    writer.materialize_pending_attempt()
    raise
```

`LiveHTTPTransport.send` は `OSError` / `http.client.HTTPException` を
`ContractError("live_transport", ...)` に変えて送出する。したがって **DBLP が接続を切った瞬間に
19.5 時間の走行ごと落ち、しかも pending intent が materialize されないので bundle が
`unconfirmed_attempt_intent` で再開不能になる。** 軸 1 は同一索引で「15 秒間隔でも 7 リクエスト
程度で `RemoteDisconnected`」を実測している。**この欠陥を塞がずに live 走行を始めてはならない。**

## 2. 裁定一覧

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-R1 | `pacing_observations` の validator が N3 を受理関門へ変える | real | **不採用の方向で採用** (記録はするが値で拒否しない) | 内 |
| A-R2 | limiter の時刻と実 wire send 時刻がずれ、短すぎる送信を通す | real | 採用 | 内 |
| A-R3 | §8.2 の 1 request 3 回上限が未実装、resume が 429 を `ready` へ洗濯しうる | real | 採用 | 内 |
| A-F1〜F4 | — | refuted | — | — |
| B-P2 | 45 秒床だけの移植は保護不足 (DBLP 1415 連続) | real | 採用 | 内 |
| B-1 | pending intent の窓が広く時間上限も無い | real | **一部採用** (送信失敗経路だけ塞ぐ) | 一部外 |
| B-2 | deadline / 20 万上限の検査が `begin_attempt` の後 | real | 採用 | 内 |
| B-3 | `intent_at` が秒精度なので WAL からの exact 再導出は不可能 | real | 採用 (A-R1 と同じ結論を強化) | 内 |
| B-4 | OpenAlex 枠は単独なら安全だが並行 axis 1 と共存しない | real | 採用 (運用排他) | 内 |
| B-5 | test は fake clock も対で要る、直接呼び出しが複数、所要台帳が未更新 | real | 採用 | 内 |
| 親-1 | 送信失敗が走行ごと殺し bundle を再開不能にする | real | 採用 | 内 |

## 3. 確定した実装 scope (プラン v2)

段 2 プランを土台に、次の 7 点を確定する。**これ以外を足さない。**

### 3.1 pacing (段 2 プランの 1〜4 をそのまま採用、ただし時刻の取り方を訂正)

- host 別最小間隔は source literal で `export.arxiv.org: 3.0` / `api.openalex.org: 1.0` /
  `dblp.org: 45.0`。CLI option・catalog 値・環境変数による上書き経路を作らない。
- 軸 1 の `HostLimiter` と同型を移植する。状態は live bundle 内に永続化し、`resume` で引き継ぐ。
- **待ち (sleep) は `begin_attempt` より前に置く** (段 2 プランどおり)。
- **【A-R2 の訂正】limiter が記録する「最終発行時刻」は、`transport.send` を呼ぶ直前に取った
  実時刻とする。** `acquire` 時点の時刻を最終発行時刻にしてはならない。待ち時間の計算は
  「直前の実送信時刻 + 最小間隔」から行う。これで WAL 書き込み遅延の差が実送信間隔を
  下限未満へ縮める経路が閉じる。

### 3.2 §8.2 の retry を登録どおり実装する【A-R3・親-1】

- **1 request あたり最大 3 回の再試行。バックオフ 3→6→12 秒。DBLP は 15 秒起点** (§8.2 逐語)。
- 再試行の対象は「送信失敗 (transport 例外)」と「retryable な非 200 (429 / 503)」。
- **3 回を超えたらその row を `unavailable` として loop を継続する** (§8.4 どおり。
  ここを緩めない)。
- 再試行も wire attempt として `WireBudget` に数える (§8.3 の `preflight_retries`)。
- `_validate_preflight_wal_attempt_sequence` を、**初回 plan の途中でも同一 stream の
  再試行を最大 3 回まで受理する**形へ変える。現在の validator は再試行を「初回 plan の完走後」に
  しか許さないので、inline retry を入れるとこの述語の受理形が動く。
  **これは受理形の拡大に当たる。正当化は次のとおり:**
  - 旧登録 §8.2 は再試行を「1 request あたり最大 3 回」と定め、§8.3 の予算表は
    `preflight_retries` を独立列として持つ。**登録は preflight 中の再試行を明示的に想定している。**
  - 現 validator の「完走後だけ」という形は登録に無く、実装側の artifact である。
    したがってこの変更は登録を超えて広げるのではなく、実装を登録へ揃える。
  - 同時に上限 3 を新たに強制するので、**現状より締まる方向の変更も同じ commit に入る**
    (現状は回数を数えておらず無制限)。
- **負例を必ずテストで固定する:** 同一 stream の 4 回目の attempt を持つ WAL は
  `ContractError("bundle_preflight_sequence", ...)` で拒否されること。
- **retry を義務にしない。** §8.2 は上限であって義務ではない。transport 例外と 429 / 503 以外は
  再試行しない。

### 3.3 送信失敗で pending intent を残さない【親-1・B-1 の一部】

- `_send_with_raw_commit` の transport 例外経路でも `writer.materialize_pending_attempt()` を
  呼んでから送出する。既存の分類失敗経路と同型であり、新機構ではない。
- **scope 外:** 「raw response が耐久化済みの pending intent を回復可能にするか」。
  one-shot receipt・重複送信・予算会計の契約に触るので裁定パッケージへ回す。

### 3.4 DBLP の連続失敗 cooldown【B-P2】

- **DBLP に限り**、1 row の再試行 3 回が尽きた時点で **2700 秒 (45 分) の cooldown** を置いてから
  次の row へ進む。値は軸 1 が同一索引で実測した回復条件そのもの。
- これは gate でも検査でもなく **scheduling** である。旧登録 §8.3 は「最小 request 間隔と
  cooldown を実行段の preflight で測り、記録する」と既に登録している。
- 一般化しない。arXiv・OpenAlex には cooldown を入れない。

### 3.5 予算・締切の検査を intent より前へ【B-2】

- `WireBudget` に**状態を変えない検査**を足し、`begin_attempt` の前に呼ぶ。
  `consume` は現在位置のままにする。
- これで deadline 超過・20 万到達が「送っていない pending intent」を作らなくなる。

### 3.6 N3 の記録 — 記録だけにする【A-R1・B-3】

- preflight report に `pacing_observations` を足す。field は段 2 プランの 7 つでよい。
- **禁止する gate の署名:**
  `validate_preflight_report(report, catalog, seal)` が、
  `pacing_observations[i]["observed_interval_seconds"]` の**値**を理由に
  `ContractError` を送出してはならない。WAL 由来値との exact 一致要求も禁止
  (`intent_at` は秒精度なので構造的に不可能 — B-3)。
- **通る正例:** 同一 host の 2 件目の `observed_interval_seconds` が `44.87` (下限 45.0 未満) で
  あっても、`validate_preflight_report` は `ContractError` を送出せず正常に完了すること。
  この正例をテストで固定する。
- **許す構造検査:** 件数が `wire_attempt_count` と一致すること、`stream_id` の並びが
  `preflight_evidence` と一致すること。これらは既存の report 構造検査と同類である。
- 理由: N3 は旧登録 §13.2 で non-blocking かつ `scheduling のみ` と固定されている。
  受理集合へ入れると、同じ response 列でも間隔値だけで成果物が拒否される。

### 3.7 test【B-5】

- fake clock と fake sleeper を**対で**差し替える。既存 fixture の固定 clock だけでは足りない。
- `_run_stream` の既存直接呼び出しをすべて更新する (`test_related_work_search.py` の
  1140-1142 / 1169-1174 / 1598-1603 / 2134-2136 付近)。
- **既存の期待値を 1 つも変えない。** `wire_attempt_count == 1929`、`blocked == 193`、
  `rows == 2122` はそのまま通ること。
- 実時間 sleep を 1 秒も走らせない。
- **受入所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` を正本 producer で
  更新する。** 0.0 の placeholder を書かない。
- 殺すべき変異 (positive control):
  1. 最小間隔を 0 にすると、pacing test が落ちる。
  2. limiter の最終発行時刻を `acquire` 時点へ戻すと、A-R2 の test が落ちる。
  3. retry 上限を 3 から 4 へ上げると、sequence validator の test が落ちる。
  4. 送信失敗経路の `materialize_pending_attempt()` を消すと、resume の test が落ちる。
  5. 予算検査を `begin_attempt` の後へ戻すと、pending intent の test が落ちる。
  6. §3.6 の禁止 gate を足すと、上記の「通る正例」が落ちる。

## 4. 運用の確定【B-4】

- **走行中は、同一 login node から同じ 3 host へ送る別 producer を出さない。** 軸 1 の走行と
  重ねない。実行前に `pgrep` で確認し、実行記録へ書く。
- OpenAlex は 23 request × 10 credit = 230 credit。単独なら 1 日枠 1000 の 23%。
- bundle は repo 外の恒久 path `/work/1/SFC/tanab/axis3-bundles/2026-09-09-t2028-preflight/bundle`。

## 5. scope 外 (裁定パッケージとしてユーザーへ返す)

1. **raw response 耐久化済み pending intent の回復強度** — one-shot receipt 契約に触る。
2. **transport の body ceiling と attempt 全体の wall-clock ceiling** — 失敗分類と受理集合が変わる。
   軸 1 は 16 MiB ceiling を持つが軸 3 は無い。socket timeout 30 秒が停滞は縛る。
3. **resolver と control 評価器の実装** — 本走の前提。これらを実装すると catalog と seal が
   変わり、今回の preflight bundle は本走に使えなくなる。
4. **DBLP 題名 lookup 5 本** — 凍結登録に完全 bytes が無い。resolver では閉じず、
   §8.5 の意味的 amendment (新日付・新 ID) が要る。
5. **今回の live preflight を実際に発火させるか** — 1929 本の外部 request と約 1 日を、
   後で supersede されると分かっている成果物に使うかの費用判断。**ユーザー裁定**。

## 6. 実装子への不変条件

- 凍結物 4 文書 (`2026-08-27-axis3-search-preregistration.md` /
  `2026-08-27-axis3-index-measurements.md` / `2026-09-01-axis3-search-amendment.md` /
  `2026-09-01-axis3-registration-preflight.md`) を 1 byte も変えない。
- 語・10 枝・cutoff (2026-12-31)・包含・除外・判定語彙・query ID 集合・catalog の
  `request_factory` state を変えない。**catalog bytes は同一のままであること。**
- `_probe_response` の非 200 → `unavailable` を緩めない (規律 2)。
- 最小間隔を短くする経路 (CLI option・環境変数・catalog 値) を作らない。
- 編集面は `orchestrator/related_work_search.py`、
  `orchestrator/tests/test_related_work_search.py`、
  `orchestrator/tests/acceptance_duration_ledger.json` の 3 file に限る。
  `tools/run_axis3_search.py` と schema 4 本は bytes を変えない。
