# 段 4 裁定 — [T-650] プラン v2

2026-08-16 22:50 JST。基準 main `e44aa4f9` (取り込み済み)。
裁定 inbox 再走査: `docs/rulings*` および `/work/1/SFC/tanab/rulings-inbox` はいずれも不在 (0 件)。

## 全体判定

**レンズ A の blocker 判定を受け入れる。プラン v1 の中核である
「`terminal = rc not in {11,21}`」は却下する。** rc は release 安全性を表現できない。
v2 は **2 つの直交する述語**を land の**到達点**から決める。

## 所見の裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-B1 | 例外・中断を terminal 化して release すると merge/fold/rollback の途中状態で解放する | real | **採用** | 内 |
| A-B2 | rc と release-safe は同じ 1 bit に畳めない (rc=30 は retryable、rc=28 は release-safe でない) | real | **採用** | 内 |
| A-B3 | rc=29 は checker の決定的非 0 も timeout も中断も畳んでおり単一意味でない | real | **採用** | 内 |
| A-B4 | 同一 slug の別 invocation が取り直した lease を旧 lander が削除できる (実行で確認) | real | **部分採用** | 内 (限定) |
| A-B5 | receipt 二重 parse は同じ parser でも読取間の差し替えを拘束しない | real | **採用** | 内 |
| A-B6 | release 後 print だと main が進み lease も消えたのに結果 JSON が空になりうる | real | **採用** | 内 |
| A-B7 | 既存 retry loop は lease を再取得せず land を再実行する (呼出し protocol 非互換) | real | **部分採用** | 一部外 |
| A-8 | F3 の 308 秒・4827 秒は lease 生存時間を証明しない | real | **採用** | 記録 |
| A-9 | 空転回数は保存ログ実測で 43 回 (31+12)、自己申告の 42 とずれる | real | **採用** | 記録 |
| B-2 | `terminal` を読む既知 caller は 0/6 | real | **部分採用** | 一部外 |
| B-3 | rc=21 の無期限保持が F2 を別の色で再現する | real | **採用** | 内 |
| B-4 | P1 の期待値比較が成立していない | real | **採用 (P1 却下で解消)** | 内 |
| B-5 | 64 KiB 境界で landed 後の通知が失われうる | real | **採用 (JSON を増やさない設計で縮小)** | 内 |
| B-7 | 監査証跡が無く効果を測れない | real | **不採用 (scope 外)** | 外 → R-D |
| B-1 | land 未到達の穴は残る | real | **不採用 (本 wave の scope 外)** | 外 |
| B-8 | scope 表記は「land 到達後の lease 残留を根治」とすべき | real | **採用** | 記録 |
| B-9/10/11 | 親の測定の過大一般化 3 件 | real | **採用 (訂正済み)** | 記録 |
| B-6 | FIFO の新規 starvation | **refuted** | — | — |
| B-12 | M0 欠落 | **refuted** (登録済み) | — | — |
| B-12 | テスト gap 6 件 | real | **採用** | 内 |
| A | リワードハック | **成立せず** (両レンズとも) | — | — |

## provisional 裁定の再裁定

- **(P1) 却下。** 「未知は terminal 側 (手放す側) に倒す」は**安全側ではない**。
  レンズ A の比較を採用する — terminal を retryable と誤る最悪値は「TTL または誤 loop が続く間の停止」
  (時間損失) だが、retryable・未知・中断状態を terminal と誤る最悪値は
  「元 lander が再開可能な間に排他を解き、別 wave の受入を重ねる」(正しさに隣接)。
  **正しさに隣接する側を避ける。** 置換規則は下記 v2-1。
- **(P2) 支持。** stale-main (rc=10) は同一 request では回復不能。レンズ A が独立に確認
  (`tools/dev_wave_land.py:1559-1572,1716-1726`)。
- **(P3) 条件付き支持。** 新 field は互換だが、**rc だけから計算してはならない**。
  さらに B-6 より **`lease_release` を JSON へ入れない** (stdout の結果 JSON は core のみ)。
- **(P4) 修正。** TTL・heartbeat・FIFO・通知の意味論には触れない (維持)。
  ただし **I2 のために `release()` へ compare-and-delete を 1 つ足すことだけ例外的に採用する。**
  完全な fencing token ([T-649] 見送り済み) は作らない。残余は下記に明記する。

## v2 設計

### v2-1. 2 つの直交する述語を land の到達点から決める

**rc からの導出をやめる。** `LandResult` に 2 つの bool を持たせ、**各 return site が自分で宣言する**。

- `retryable_same_request`: 同じ request をそのまま再実行して成功しうるか。
- `release_safe`: main・fold transaction・mutation が quiescent で、lease を手放しても
  別 wave が中間状態の上で受入を始めることがないか。

**release する条件は `release_safe and not retryable_same_request` のみ。**
既定は両方 `False` (= 保持) とし、**明示的に宣言した return site だけ**が値を上げる。
未宣言・例外・中断は自動的に「保持」に落ちる。これが P1 の反転である。

**release-safe を宣言してよい到達点 (実装子はコードで各点を確認してから宣言する)**

1. `landed` — fold finalize と postcondition の完了後。
2. `already-landed` — 受入 receipt の完全検証後の no-op (レンズ A が `:2761-2767,2939-2964` で確認)。
3. 成功した active recovery — journal finalize 後 (`:2514-2534`)。
4. `stale-main` (rc=10) — lock 内の照合だけで、main も fold も触っていない。
5. **provenance 拒否のうち、checker が決定的に非 0 を返した場合に限る** — 下記 v2-2。
6. lock 取得前・mutation 前の拒否 (dirt / identity / audit / receipt 不成立)。
   **実装子は各 rc の発生点が本当に mutation 前かをコードで確認し、確認できない点は宣言しない。**

**release-safe を宣言してはならない到達点**

- 予期しない例外、`KeyboardInterrupt`、signal 由来のすべて (A-B1)。**新 rc 定数 (`RC_INTERNAL`/
  `RC_INTERRUPTED`) は作らない。** 現行の例外伝播をそのまま残す。
- `RC_FOLD_ROLLBACK_FAILED` (28) — rollback 不完了、journal または中間状態あり (A-B2)。
- `RC_LANDED_POSTCONDITION_FAILED` (25) — main が既に動いた可能性を含む。
- fold 系で active transaction が残りうるすべての点。

**retryable_same_request を宣言してよい到達点**

- `RC_LOCK_BUSY` (11) — 共通 lock の一時競合。
- `RC_FOLD_RECOVERY_FAILED` (27)、`RC_FOLD_FINALIZE_FAILED` (30) — 同一 request の recovery が
  実装済み (`:2467-2534,2778-2882`)。**ただし release_safe は False** なので release はしない。
- provenance の **timeout / 例外 / binding 読取失敗** による rc=29 (v2-2)。

**`RC_CONTROL_PLANE` (21) は retryable_same_request を宣言しない。** B-3 の blocker を採る。
rc=21 には決定的な拒否 (wave tip が foreign control-plane path と衝突、`:1293-1309`) も含まれ、
かつ制御面 churn は並行 wave が多いほど頻発するので、無期限保持は F2 を再現する。
release_safe は「mutation 前の拒否か」をコードで確認して個別に決める。

### v2-2. provenance rc=29 の下位区別

`_audit_provenance_history` (`:1845-1908`) は checker の決定的非 0 も 480 秒 timeout も
`KeyboardInterrupt` も binding 読取失敗も**すべて rc=29 へ畳んでいる**。
`_ProvenanceReceipt.returncode` は checker の実 returncode を保持しているので、
**「checker が起動して非 0 を返した」場合だけを決定的として区別できる。**

- checker が完走して非 0 → `release_safe=True`, `retryable_same_request=False` (t1142 の型を閉じる)
- timeout / 例外 / binding 失敗 / 中断 → `release_safe=False`, `retryable_same_request=True`
  (D254 自身が timeout を再試行へ回すとしている)

**この区別が実装できない (returncode が到達点で参照できない) と判明したら、
rc=29 全体を `release_safe=False` に倒して停止し、親へ返すこと。** 誤って解放するより保持する。

### v2-3. release 権限を receipt bytes へ束縛する (A-B5)

- release 権限の事前 snapshot は `_read_acceptance_receipt()` / `_receipt_object()` を**再利用**する
  (parser 差は出ない。レンズ A が確認済み)。
- snapshot 時に **receipt の bytes digest を保存**する。
- land が `acceptance_receipt_sha256` を返した場合は **digest 一致を要求**する。不一致なら release しない。
- land がそこまで到達しなかった場合 (rc=29 等) は、**release 直前に receipt を読み直して
  digest 不変を確認**する。不変でなければ release しない。

### v2-4. lease の compare-and-delete (A-B4)

`tools/wave_land_window.py` の `release()` へ **optional な引数を 1 つ**足す
(例: `expected_main_sha: str | None = None`)。指定されたときだけ、holder 一致に加えて
**lease payload の `main_sha` 一致**を unlink の条件にする。未指定時の挙動は現行と完全に同一とする。

land は `tested_main` を渡す。同一 slug の別 invocation が新しい main で claim し直した lease は
`main_sha` が異なるので削除されない。

**残余 (明記する)**: 別 invocation が**同じ main_sha で**claim し直した場合は区別できない。
完全な世代束縛には claim 側の generation 発行が要り、それは [T-649] で見送り済みである。
本 wave は I2 を「**別 slug に対しては絶対、同一 slug に対しては main_sha 一致でのみ**」へ
明示的に弱め、残余を worklog と decisions に書く。

### v2-5. 出力順序 (A-B6)

1. `land()` を完走させる。
2. **core 結果 JSON を stdout へ print して flush する。** JSON へ足すのは
   `release_safe` と `retryable_same_request` の 2 bool だけ。**`lease_release` は入れない。**
3. その後に release を試みる。
4. release の結果 (`state` と `reason`) は **stderr へ 1 行**書く。

これで `land-result.json` は release より先に durable になり、B-5 の 64 KiB 増分も 2 bool に留まる。

### v2-6. 不変条件の更新

I1〜I5 を維持し、レンズ A の I6〜I9 を追加する。**I10 (auto-release 後の同一 receipt 再 land 禁止)
は不採用** — land に状態を持たせる必要があり、本 wave の規模を超える。裁定パッケージ R-E とする。

- **I6**: `release_safe` と `retryable_same_request` を分離し、active fold state・rollback 不完了・
  mutation outcome 不明では release しない。既定は両方 False。
- **I7**: release は lease directory identity・holder・`main_sha` を束縛した compare-and-delete で行う。
- **I8**: release 判断と land の完全検証は同一 receipt bytes (digest 一致) を使う。
- **I9**: main を進めた結果 JSON は release より先に durable にする。

## 変異事前登録 (DW-M01)

各変異は「同じ入力を拒否する層が前後に無い」ことを実装子がコードで確認してから確定する。
確認できない変異は登録せず実効 gate へ再照準する。

| ID | 変異 | 期待 |
|---|---|---|
| M0 | automatic release 呼び出しを丸ごと削除する。**wave 前の実コードそのもの** | KILLED |
| M1 | `release_safe` の既定を True にする (未宣言の到達点でも解放) | KILLED |
| M2 | `retryable_same_request` を release 条件から外す (`release_safe` だけで解放) | KILLED |
| M3 | 予期しない例外・中断の到達点で `release_safe=True` を宣言する | KILLED |
| M4 | rc=28 (rollback 不完了) で `release_safe=True` を宣言する | KILLED |
| M5 | rc=30 の `retryable_same_request` を False へ反転する | KILLED |
| M6 | rc=21 に `retryable_same_request=True` を宣言する (v1 の設計へ戻す) | KILLED |
| M7 | provenance の下位区別を外し rc=29 を一律 release_safe にする | KILLED |
| M8 | provenance の下位区別を外し rc=29 を一律 保持にする (F2 が閉じない向き) | KILLED |
| M9 | `release()` へ wave slug でなく holder digest を渡す | KILLED |
| M10 | `release()` の `lease.holder != self_holder` guard を外す | KILLED |
| M11 | `release()` の `main_sha` compare-and-delete を外す (同一 slug ABA が通る) | KILLED |
| M12 | receipt digest 束縛を外す (二重 parse の差し替えが通る) | KILLED |
| M13 | print と release の順序を入れ替える | KILLED |
| M14 | release 失敗時に land の rc を上書きする | KILLED |
| M15 | `release_safe` / `retryable_same_request` を JSON から削除する | KILLED |
| P1 (正例) | **通る正例**: 受入緑 → land 成功 → lease が解放され、rc=0、main が tip へ進み、`land-result.json` が完全 | PASS |

`P1` は受理集合を縮小する方向の gate ではないが、**過剰拒否 (正当な land で release を拒む)** を
検出する正例として登録する。

## 本 wave で閉じないもの (裁定パッケージへ)

`rulings-package-draft.md` の R-A (待ち札順位) / R-B (F57) / R-C (ff-only 連鎖) / R-D (監査証跡) に加えて:

- **R-E**: auto-release 後に同一 receipt で land を再実行する既存 loop (A-B7)。
  release 後の再 land は lease 外で走る。**land の権威は lease に依存しない (D239) ので
  正しさは壊れない**が、他 wave の受入を stale にしうる。恒久解は
  「terminal 結果を受けた caller は停止し、再試行には新 claim・受入・receipt が要る」という
  呼出し protocol の明文化と、[T-694] の正本 wrapper。
- **R-F**: `terminal` / `release_safe` を読む既知 caller は 0/6 (B-2)。本 wave は
  「他 wave を止めない」ところまでしか閉じない。**空転する wave 自身を止めるのは wrapper の仕事。**

## 記録の訂正 (worklog へ書く)

- lease 内実作業の中央値は **再現できなかった**。親の 26 対・308 秒に対し、レンズ A の再集計は
  時系列対 30 対・中央値 397.5 秒・最大 4827 秒、fold の第一 parent が当該 merge である厳密対
  20 対・中央値 276.5 秒・最大 2037 秒。**厳密対を採用し、親の初回値は erratum として残す。**
- 最大 4827 秒は親子関係のない commit 間の時刻差であり、**TTL 超過 holder の実在証明にならない**。
  TTL 超過 race の存在は D239 とコードから言えるが、この数字は根拠にしない。
- 空転回数は保存ログ実測で **43 回** (`land-loop.log` 31 + `land2-loop.log` 12)。
  land 1 回の所要は 38〜61 秒。自己申告の「42 回・25〜45 秒」は独立に支持されない。
- 21:41 の 6 wave / 11〜50 分は**一時点の観測**。22:20 には 1 本へ減った。定常状態として書かない。
- 「直列資源の 8 割超が空転」は**書かない**。取り残された場合の条件付き比率であり、
  取り残しの発生率は測っていない。
- scope 表記は「受入全走のボトルネック根治」ではなく **「land 到達後の lease 残留を根治」**。
