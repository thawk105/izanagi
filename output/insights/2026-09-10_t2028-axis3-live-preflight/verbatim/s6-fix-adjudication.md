# 段 6 fix 裁定 — [T-2028]

親が段 6 レビュー 2 本 (計 10 件の must-fix) を裁定した確定版。`plan-v2.md` を base とし、
次の点を上書きする。**この文書が fix の正本である。**

## 0. 親自身の裁定の訂正 — retry の対象を絞る

`plan-v2.md` §3.2 は「再試行の対象は送信失敗 (transport 例外) と retryable な非 200 (429 / 503)」と
裁定した。**429 / 503 を retry 対象に入れたのは誤りだった。**

レビュー A が最小再現で示したとおり、retry loop は最新 attempt で response / evidence / probe を
上書きするため、**evidence が `[429, 200]` の row の status が `ready` になる**。これは凍結契約に反する。

旧登録 §8.4 逐語:

> - **429・503・空ボディ・通信失敗・再試行上限到達は、その query を `未完走` にする。**
>   完走した query だけを取り出して軸の成熟度を名乗ってはならない (§7.3 の論理積)。

**したがって確定裁定は次のとおり。**

- **429 / 503 を retry しない。** 非 200 を観測した時点でその row は `unavailable` とし、
  loop を次の row へ進める。**これは変更前の挙動である。** 規律 2 により、
  取得完全性のゲートは緩めない。
- **retry するのは transport 例外 (`live_transport`) だけ。** 送信そのものが成立せず、
  HTTP status を 1 つも観測していない場合に限る。

この訂正により、`plan-v2.md` §3.2 が認めた「WAL 順序 validator の受理形拡大」の根拠も消える
(下記 F2)。

## 1. must-fix

### F1. transport 例外を retry 対象にする【A-1・B-1、最重要】

現実装の retry loop は返却済みの `response.status` だけを見るので、`LiveHTTPTransport` が
接続切断を `ContractError("live_transport", ...)` に変えて送出すると **1 回目で CLI まで抜けて
走行が終わる。** report 自体が出ない。**本 wave が塞ごうとした当の失敗そのものである。**

- transport 例外を retry する。**最大 3 回の再試行 (初回 + 再試行 3 = 合計 4 attempt)。**
  根拠は旧登録 §8.3 逐語:「**その各ページが最大 4 回 (初回 + 再試行 3) 送られる。**」
  現実装の合計 3 attempt は登録より 1 回厳しい。
- backoff は 3 値とも到達可能にする: arXiv / OpenAlex `3, 6, 12` 秒、DBLP `15, 30, 60` 秒。
- 再試行が尽きたら、その row を **`unavailable`** とし、通信失敗と分かる reason code を入れて
  **loop を継続する** (§8.4 の「通信失敗・再試行上限到達」)。
- **`live_transport` 以外の `ContractError` を握り潰さない。** 予算超過・締切超過・seal 不整合・
  分類失敗はそのまま送出する。**例外 code で厳密に分岐せよ。**

### F2. 429 / 503 の inline retry を撤去する【A-2】

- 非 200 を観測した row は、その場で `unavailable` にして次へ進む。retry しない。
- **これにより `_validate_preflight_wal_attempt_sequence` の受理形拡大は不要になる。**
  transport 例外の再試行が committed WAL evidence を作らないなら、**この述語を変更前の形へ戻せ。**
  作るなら、1 stream あたり最大 4 attempt (初回 + 再試行 3) で境界を切り、5 回目を
  `ContractError("bundle_preflight_sequence", ...)` で拒否せよ。**どちらになったかを報告に明記せよ。**
- 初回 OpenAlex 429 の exact-one stop は現状どおり維持する。

### F3. scope 外の混入を戻す【A-6】

`_derive_finalize_eligibility` で retryable tail を非終端にする条件が `kind == "preflight"` に
限定されている。そのため **final bundle の 429 / 503 tail が `terminal_tail` として finalize 可能に
なり、本走の resume / retry が失われる。**

- **本走 (`kind == "final"`) の挙動を変更前へ戻せ。** 本 wave は preflight 経路だけを触る。

### F4. 実送信時刻を本当に `send` の直前で取る【A-3】

現状は `limiter.issue()` で時刻を取った後、`LiveSearchSession._send_with_receipt()` の型検査と
transport identity 検査を経てから実際の `.send()` が呼ばれる。

- 時刻取得を実 `.send()` の直前へ寄せる。wrapper 内の処理時間が記録値と実送信の差にならないこと。

### F5. resume の pacing observation を捏造しない【A-4】

`_pacing_observations_from_intents` は秒精度の `intent_at` の差を `observed_interval_seconds` として
最終 report へ入れる。**これは実際の送信間隔ではない。**

- **resume 経由で再導出した observation の `observed_interval_seconds` は `null` にせよ。**
  測っていない値を書かない。件数と順序の整合は従来どおり保つ。

### F6. resume が cooldown と limiter state を fail-closed に継承する【A-5・B-3】

- **cooldown を永続化する。** cooldown に入るとき、その host の「最終発行時刻」を
  `now + cooldown - minimum_interval` へ進めて limiter 状態へ書けば、resume は既存の床計算だけで
  残り cooldown を尊重する。**新しい state field や新しい機構を足さない。**
- **limiter state file が欠落・空のときに「待ち不要」と解釈してはならない。**
  現状は `O_CREAT` で開いて空を新規状態として受理する。committed attempt が既にある bundle で
  state が欠けている場合は、**WAL の最後の `intent_at` を最終発行時刻とみなして復元**せよ
  (保守側)。resume を壊さず、かつ床を飛ばさない。
- DBLP の cooldown は、transport 再試行の尽きた失敗と 429 / 503 の**どちらでも**発火させる
  (host が嫌がっている信号はどちらも同じ)。

## 2. scope 外として確定 (裁定パッケージへ)

- **process が request の途中 (intent 後、commit 前) で死んだ場合、`resume_bundle` は
  `unconfirmed_attempt_intent` で止まる** (`plan-v2.md` §5.1)。F1 で通信失敗は in-process 処理に
  なるので、この窓は「process 死」だけに縮む。**今回は塞がない。**
  - **materialize のテストが「resume は blocked のまま」を望ましい終状態として固定しているのは
    誤解を招く。** テストの意図を「raw 証拠が失われないこと」に書き直し、resume が blocked を
    返すことは**現時点の既知の限界**として明示せよ。
- **同一 bundle への 2 process 同時起動** (B-4)。`flock` は limiter 状態だけを守り、WAL の
  `journal_byte_count` は process ごとに独立なので truncate しうる。**本 wave が作った欠陥ではなく
  bundle writer の既存性質である。** 運用排他 (`plan-v2.md` §4) で守り、実行記録へ限界として書く。
- body ceiling / attempt 全体の wall-clock ceiling (`plan-v2.md` §5.2)。

## 3. テストの追加・訂正

- **F1 の正例・負例を実体で固定する。**
  - 正例: `run_preflight` で 1 row が transport 例外を 3 回返し 4 回目で 200 を返すと、その row は
    `ready` になり、**loop は次の row へ進む**。
  - 負例: 4 attempt すべて transport 例外なら、その row は `unavailable` になり、
    **`run_preflight` は例外を送出せず report を返す**。
  - **`live_transport` 以外の `ContractError` は握り潰されない** (例: 予算超過はそのまま送出)。
  - backoff の 3 番目の値 (arXiv 12 秒 / DBLP 60 秒) が実際に使われることを送信時刻列で固定する。
- **F2 の負例:** evidence が `[429, 200]` になる経路が**存在しない**こと。429 を観測した row は
  `unavailable` のままで、`ready` にならない。
- **F3 の負例:** `kind == "final"` の retryable tail が finalize されないこと (変更前の挙動)。
- **F4:** production 経路 (`LiveSearchSession`) を通る正例で、記録された発行時刻が実送信の直前で
  あることを固定する。**`NonProductionTransport` の直接送信だけを見るテストでは足りない**
  (レビュー A の指摘)。
- **F5:** resume 由来 observation の `observed_interval_seconds` が `null` であること。
- **F6:** cooldown 中に落ちた状況を模し、別 limiter instance が残り cooldown を待つこと。
  limiter state を消した resume が、WAL 最終 intent から床を復元すること。
- **cooldown テストの補強** (B の nit): 各 retry の送信時刻列と「再試行が連続して同一 stream で
  あること」も検査する。
- **既存期待値 (`wire_attempt_count == 1929`、`blocked == 193`、`rows == 2122`、
  `len(transport.calls) == 1929`) を変えない。** F1 / F2 に伴う retry 境界テストの訂正だけが例外で、
  これは親の裁定訂正に伴う変更であって実装を通すための緩和ではない。
- 受入所要台帳を再度、正本 producer で更新する。

## 4. 不変条件 (変更なし)

`plan-v2.md` §6 をそのまま継承する。catalog bytes 不変、凍結 4 文書不変、CLI と schema 4 本不変、
`_probe_response` の非 200 → `unavailable` を緩めない、最小間隔を短くする経路を作らない。
編集面は `orchestrator/related_work_search.py`、`orchestrator/tests/test_related_work_search.py`、
`orchestrator/tests/acceptance_duration_ledger.json` の 3 file に限る。
