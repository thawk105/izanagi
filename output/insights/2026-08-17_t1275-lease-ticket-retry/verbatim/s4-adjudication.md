# 段 4 裁定 — [T-1275] 受入 lease の待ち札を同一 process 内で再試行させる

親裁定。2026-08-17 09:35 JST。base main = e6306848 (wave branch を ff 済み)。
裁定 inbox 再走査済み — `2026-08-17-rulings-full5-36rulings.md` §5 は択 (a) を再確認するだけで新事実なし。

## 所見の裁定

| # | 判定 | 採否 | scope |
|---|---|---|---|
| A-1 release 後の再 claim は先着順位を維持しない | real | 採用 (must-fix) | 内 |
| A-2 rc=16 は実走赤を握りつぶしうる | real | 採用 (must-fix) | 内 (scope 拡大) |
| A-3 land の `claim` 流用は lease / 札を新規生成 | real | 採用 | **外 (S2 ごと持ち越し)** |
| A-4 retry 判定の根拠が成果物から消える | real | 採用 (must-fix) | 内 |
| A-5 前 attempt の main を red-check に渡す変異が殺せない | real | 採用 (must-fix) | 内 |
| A-6 held-self renew テストが stale 再取得でも通る | real | 採用 | 外 (S2 ごと) |
| A-7 P1 は唯一の実害例を直さない | real | 採用 (scope の言い直し) | 内 |
| B-1 P1 は t1180 の post-claim / pre-command 失敗を拾わない | real | 採用 (scope の言い直し + 新規タスク) | 内 |
| B-2 P4 は command hang に適用されない | real | 採用 (P4 を狭める) | 内 |
| B-3 S2 の `claim` は renew でない (A-3 と独立 2 例) | real | 採用 | 外 (S2 ごと) |
| B-4 S2 の成功診断が exact stderr テストを壊す | real | 採用 | 外 (S2 ごと) |
| B-5 U2 が安全な S2 の編集面を含まない | real | 採用 | 外 (S2 ごと) |
| B-6 fake clock が時刻を進めない | real | 採用 | 内 |

refuted はゼロ。全 13 所見を real と裁定する。

## 裁定 1 — P2 を撤回する。[T-1172] (S2) は本 wave から外す

A-3 と B-3 が**独立に**、「`wave_land_window.claim` を renew として流用すると lease と待ち札を
新規生成し、land が retryable 終端なら最大 2400 秒 / 300 秒残る」と実コードから成立させた。
安全な S2 には `wave_land_window.py` へ非取得型 renew primitive を新設する必要があり、
これは D253 の実装面そのものである。D253 の待ち札意味論に触れないという [T-1275] の裁定条件を
守るには、その新設に独立の敵対検証を掛けねばならず、本 wave に相乗りさせる規模ではない。

[T-1172] の裁定文は「[T-1275] と同じ作業で扱ってよい」であって義務ではない。
絶対規律 5 (段階導入) に従い別 wave へ送る。A-6 / B-4 / B-5 も S2 に付随するので同時に持ち越す。

**scope は S1 のみ。**

## 裁定 2 — A-1 を採用し、再試行は lease を保持したまま行う

段 2 プランの release-and-requeue を却下する。`_create_lease` 成功時 (`tools/wave_land_window.py:685-693,713-720`) と
`release` (`:784-836`) の双方が自分の札を削除するので、同一 process から即座に再 claim しても
**新しい `queued_at_ns` の札**になり、残っている後着の後ろへ回る。裁定 (a) の目的が発効しない。

採用する形:

- 再試行可能な attempt が終わったとき、`ownership` が `ACQUIRED` なら **release しない**。
- attempt 境界で自 holder の `claim` を 1 回打ち、`held-self` で lease mtime を更新して残 TTL を戻す。
  この renew は既存の受領証発行直前の再 claim (`tools/dev_wave_wait.py:3236-3247`) と同じ形で、
  **専用の confirmation lifecycle を使い `active_lifecycle.ownership` を `ACQUIRED` のまま保つ**
  (`HELD_SELF` へ落とすと release 権限を失い、cleanup が lease を残す)。
- renew が `held-self` 以外、または holder / main が一致しないなら再試行せず terminal。
- 最終 attempt が失敗したときの release は現行 cleanup がそのまま行う。

I5 (緑の lease を自分から手放さない) は不変。緑になった attempt は現行どおり `RETAINED`。

## 裁定 3 — A-2 を採用し、再試行の発火条件へ肯定的証拠を要求する

親が一次資料で確認した: `tools/pegasus/dispatch_compute.py:1877-1891` は
`_persist_receipt` が失敗すると **`child_rc` を得ているのに `INFRA_RC` (=16) を返す**。
つまり pytest が実走して rc=1 の赤を出しても待ち手には 16 に見える。
raw rc だけを発火条件にすると実走赤を再試行でき、**規律 2 の直接違反**になる。

レンズ A の修正案のうち「pre-child failure 専用 rc を返す」は採らない。
rc 意味論 (0 / 1 / 13 / 16) は runbook §7.3 と land が依存する受理集合であり、変えない。

採用する形 — **再試行は次の全条件が成立したときだけ許す。1 つでも取れなければ terminal (fail-closed)**。

1. `child_rc not in (0, 1)` である。
2. 捕獲 log に、dispatch が **child process を 1 度も RUN 観測しないまま失敗した**ことを述べる
   **構造化 attestation がちょうど 1 件**ある。この attestation は本 wave で新設する
   (下記 scope 拡大)。`child_started` が真の attestation は再試行を許さない。
3. 捕獲 log から pytest の判定痕跡が 1 件も導けない (赤 nodeid 抽出 0 件かつ session summary 不在)。
   2 の肯定証拠に対する裏取りであり、これ単独を根拠にしない。
4. postrun clean / index flags / fingerprint 検査を通過している。
5. `ownership` が `ACQUIRED` で、cleanup failure が無い。
6. attempt 上限と共有 deadline に余裕がある。

### scope 拡大 (裁定 3 に伴う最小の追加)

`tools/pegasus/dispatch_compute.py` の INFRA_RC 返却経路へ、`receipt["outcome"]` と同じ事実を
1 行の構造化 attestation として stdout / stderr へ出す。既存の `IZANAGI_EFFECTIVE_SCHEDULER_V1`
marker と同型式にする。含める field は最小限とする。

- `kind` — `"infra"` 固定
- `reason` — closed vocabulary (`queue-wait-timeout` 等)
- `child_started` — `run_seen` に基づく真偽。**受領証永続化失敗の経路では必ず真**
- `child_rc` — 得られていれば整数、無ければ `null`

rc は 1 bit も変えない。既存 consumer は行を無視するだけで壊れない。

## 裁定 4 — A-4 を採用する (規律 3)

attempt 1 が rc=16、attempt 2 が緑だと、現行のままでは受領証にも終了 rc にも初回失敗が残らない。
「なぜ再試行したか」を構造化して返すのは規律 3 の要求である。

- 各 attempt 境界で、待ち手の stderr へ機械可読な 1 行 (attempt 番号、分類、raw / normalized rc、
  退避先 log path、log の SHA-256、claim した main、再試行するか否かとその理由) を出す。
- 成功終端でも消さない。
- **受領証 schema は変えない** (`dev-wave-acceptance-receipt/v3`、root field 集合とも不変)。
  attempt 情報は受領証の外に置く。land 側 exact 検査 (`tools/dev_wave_land.py:70-96`) を触らない。

## 裁定 5 — A-5 を採用する

attempt ごとの値 (`claim_context`, `prerun/postrun_fingerprint`, `log_sha256`,
`effective_scheduler`, `environment`, `resolved_runner_path`, `waiter_blob_sha`, `red_check`) は
attempt helper の中で生成し、outer loop へ露出させない。red-check 実行から受領証 bytes 生成までを
helper 内で閉じる。A-5 の変異 (red-check へ前 attempt の main を渡す) を殺すテストを登録する。

## 裁定 6 — A-7 / B-1 を採用し、本 wave の主張を狭める

B-1 の指摘は正しい。F365 が記録する t1180 の決定的失敗は
**lease 取得後・受入 command 投入前の rc=70 (merge-message 不足)** であり、
本 wave が対象にする「受入 command が判定を産まずに戻った」型ではない。

- 本 wave は「**受入 command が pytest の判定を 1 つも産まずに戻った走行**」だけを閉じる。
- 実測された t1180 の 52 分喪失は、この wave では閉じない。brief の成果物影響から
  「非判定失敗 1 件ごとに 40〜70 分」という一般化を削る。40〜70 分は queue 長 4〜6 の
  観測範囲であり、確定値ではない。
- 残余 (post-claim / pre-command failure からの回復) は**新規タスクとして worklog へ起票**する。
  同じ argv の即時再試行では直らず、親が修正済み message path を供給する協調点の設計が要るため、
  裁定パッケージ候補である。
- rc=16 型の発火率と節約時間は現時点で未計測である。裁定 4 の retry journal が入れば
  以後測れるようになる。worklog にはそう書く。

## 裁定 7 — B-2 を採用し、P4 を狭める

「必ず止まる」の主張は **受入 command が戻った後の retry loop** に限る。
`timeout=none` で走る受入 command 自身の hang は既存の限界であり、本 wave では変えない。
child kill と cleanup の設計は scope 外。worklog に限界として書く。

## 裁定 8 — B-6 を採用する

fake clock の `sleep` が monotonic を進める形にし、共有 deadline の実効性を検査できるようにする。
実時間 sleep と履歴比例のコストは入れない (テスト時間退行禁止規律)。

## plan v2 (確定 scope)

編集面 (所有素集合の 2 単位):

- **U1**: `tools/dev_wave_wait.py`, `orchestrator/tests/test_dev_wave_wait.py`
- **U2**: `tools/pegasus/dispatch_compute.py`, `orchestrator/tests/test_pegasus_dispatch_compute.py`

U2 が先行単位である (U1 の発火条件 2 が U2 の attestation を消費する)。U2 完了後に U1 を投入する。

段 2 プランのうち、次はそのまま採用する。

- single-attempt helper と outer loop への分離 (§1)
- attempt 上限 2 と共有 deadline の二重境界 (§2, §3)
- 失敗 log の sibling への no-overwrite 退避、caller path の解放 (§4)
- attempt ごとの preflight 再実行 (§5)
- 受領証 schema と root field の不変 (§7)
- signal / KeyboardInterrupt の扱い (§8)

次は裁定で置き換える。

- §6 の lease 遷移表 → 裁定 2 (release せず保持 + 境界で self-renew)
- §1 の発火条件 → 裁定 3 (肯定的証拠の全条件)
- retry journal の新設 → 裁定 4
- §S2 全体 → 削除 (裁定 1)

## 変異事前登録 (DW-M01 / B-057)

実装前に登録する。anchor の逐語と期待 node は fix 後の最終 commit で `DW-M07` に従い再検証する。
本走は `--runner-mode dispatch`、runner argv へ `--force-dispatch` を入れる。

| ID | 変異 (位置と内容) | 単一理由 | 期待 |
|---|---|---|---|
| M1 | `dev_wave_wait`: 発火条件から「attestation の `child_started` が偽」要求を外し raw rc だけにする | 実走赤の再試行が通る | KILLED |
| M2 | `dev_wave_wait`: 発火条件から「pytest 判定痕跡ゼロ」の裏取りを外す | 裏取り層の消失 | KILLED |
| M3 | `dev_wave_wait`: 再試行前に lease を release する (段 2 プランの旧設計へ戻す) | 先着順位維持の消失 | KILLED |
| M4 | `dev_wave_wait`: attempt 境界の self-renew を削る | 残 TTL が戻らない | KILLED |
| M5 | `dev_wave_wait`: self-renew で `active_lifecycle.ownership` を `HELD_SELF` にする | release 権限喪失 | KILLED |
| M6 | `dev_wave_wait`: attempt 上限 2 を撤廃する | 有界性の消失 | KILLED |
| M7 | `dev_wave_wait`: 共有 deadline を attempt ごとに作り直す | 有界性の消失 | KILLED |
| M8 | `dev_wave_wait`: 失敗 log 退避を上書き可にする | 一次資料の破壊 | KILLED |
| M9 | `dev_wave_wait`: 受領証へ attempt 1 の `claim_context.main_sha` を渡す | 前 attempt 値の混入 | KILLED |
| M10 | `dev_wave_wait`: red-check へ attempt 1 の `tested_main` を渡す | A-5 の型 | KILLED |
| M11 | `dev_wave_wait`: cleanup failure 後も再試行する | fail-closed の破れ | KILLED |
| M12 | `dev_wave_wait`: retry journal の出力を削る | 規律 3 の破れ | KILLED |
| M13 | `dev_wave_wait`: attempt 2 の preflight を省略する | 検査層の消失 | KILLED |
| M14 | `dispatch_compute`: attestation の `child_started` を常に偽にする | 他層 (M1 と対) の防壁破れ | KILLED |
| M15 | `dispatch_compute`: 受領証永続化失敗の経路で attestation を出さない | 肯定証拠の欠落 → terminal へ倒れるべき | KILLED |
| P1 (正例) | 無変異。dispatch が RUN 前に落ちた走行 → 再試行 → 2 回目緑 → 受領証発行 | 過剰拒否の検出 | PASSED |

M1 と M14 は同型欠陥の 2 層であり、`DW-M04` に従い両層同時変異の kill 期待も登録する
(M1+M14 同時 → KILLED)。

## 成果物影響 (DW-G05、裁定 6 で言い直し済み)

- **実装しない場合**: 受入 command が pytest の判定を 1 つも産まずに戻った走行は、
  親が解析して再投入するまで待ち手 process が存在しない。その間に待ち札が
  300 秒で失効すると、certified 選択・材料レポート・試行台帳の確定時刻が、
  観測範囲で 40〜70 分遅れる。値そのものは変わらない。
- **本 wave が閉じない残余**: lease 取得後・受入 command 投入前に落ちる型 (実測 t1180)。
  新規タスクとして起票する。
