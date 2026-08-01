# [T-194] 段 6 敵対レビュー B — レンズ「テストの検出力と甘さ」(逐語)

- 実行: claude / opus / 静的レビューのみ (pytest 未実走。共有ログインノード制約)
- 対象: 段 5 codex 実装子の diff

## 1. 変異 M1〜M7 × 新設 9 テストの静的予測表

新設テストの略称 (すべて `orchestrator/tests/test_pegasus_dispatch_compute.py`):

| # | テスト | 行 |
|---|---|---|
| T1 | `test_nonzero_child_relays_stdout_to_parent_stdout` | 238 |
| T2 | `test_nonzero_child_relays_all_collected_stdout` | 252 |
| T3 | `test_success_relays_only_last_four_kib_of_stdout` | 266 |
| T4 | `test_child_stderr_relays_only_to_parent_stderr` | 289 |
| T5 | `test_relay_exception_does_not_change_child_rc` | 305 |
| T6 | `test_relay_exception_happens_after_receipt_is_persisted` | 320 |
| T7 | `test_missing_compute_marker_relays_collected_logs` | 347 |
| T8 | `test_accounting_grace_failure_relays_collected_logs` | 361 |
| T9 | `test_post_collection_exception_relays_collected_logs` | 375 |

実装の中継呼び出しは 4 か所ある: **A** `:1138` (compute-marker 欠落)、**B** `:1179` (receipt 永続化失敗)、
**C** `:1186` (child 正常経路)、**D** `:1226` (外側 `except BaseException` ハンドラ)。

| 変異 | 適用位置 (静的に一意に決まるか) | 赤になると予測するテスト | 予測の確度 |
|---|---|---|---|
| M1 rc≠0 中継を no-op | 一意でない — rc≠0 専用の呼び出しは存在せず `:1186` が両 rc を兼ねる | T1, T2, T4, T6 | 高 |
| M2 rc≠0 も 4 KiB 枠 | `:1189` `successful=child_rc == 0` → `True` | T2 のみ | 高 |
| M3 rc=0 の枠撤廃 | `:553-557` の `if successful:` 削除 | T3 のみ | 高 |
| M4 子 stderr → 親 stdout | `:545` `sys.stderr` → `sys.stdout` | T4, T7, T8, T9 | 高 |
| M5 例外捕捉を外す (kill) | `:569-570` 削除 | T5, T6 | 高 (rc 11/12 → 16) |
| M6 accounting grace 経路の中継削除 | `:1226` (A の `:1138` は対象外) | T8, T9 | 高 |
| M7 中継を永続化の前へ (kill) | `:1186` を `:1171` の前へ | T6 のみ | 高 |

**単独 killer を持つテスト**: T2 (M2), T3 (M3), T5 (M5), T6 (M7)。
**単独 killer を持たないテスト**: T1, T4, T7, T8, T9。
**どのテストにも殺されない中継コード**: `:1179` (B)。

---

## 2. 所見

### B-1 (must-fix) — 中継呼び出し `:1179` を殺すテストも変異も存在しない

**根拠**: `dispatch_compute.py:1173-1184` / 既存 `test_pegasus_dispatch_compute.py:815-819`
(`test_success_without_any_persisted_receipt_is_infra_rc` は `_persist_receipt` を None 返しに mock して
この経路を通るが、`capsys` を取らず出力を一切見ない)。

**失敗シナリオ**: `:1179-1183` の 5 行を丸ごと削除しても新設 9 テストは全緑。共有 FS の ENOSPC/EEXIST で
receipt を落としたときに、子の失敗出力が親へ 1 文字も出ない退行が無検出で入る。

**成果物影響**: receipt が無い＝台帳に記録が残らない最悪ケースで、親 stdout に残る唯一の一次資料まで
消え、worklog の原因欄が「不明」になる。

**深刻度**: must-fix (既存テスト `:815` に `capsys` と 2 行の assert を足すだけで塞がる)。

### B-2 (must-fix) — M6 の登録が infra 経路を 1 か所しか指しておらず、`:1138` が変異未登録

**根拠**: `s4-adjudication.md` の M6 行 / `dispatch_compute.py:1137-1144` と `:1225-1230`。T7 は `:1138` を
通るが、M1〜M7 のうち T7 を殺すのは M4 だけで、これは T7 の目的ではない。

**失敗シナリオ**: `:1138-1142` を削除する変異を matrix に入れると T7 が赤になる — つまり検出力はあるのに
登録がないため、matrix は「T7 は M4 の副次赤」としか報告できず、T7 の存在理由が証明されない。逆に
登録どおり M6 だけを回すと、`:1138` 削除は matrix 上「試していない変異」として残る。

**成果物影響**: 変異 matrix の被覆主張が実際の call site 数 (4) より狭く、試行台帳の「中継を全 infra
経路で検査した」という記述が実測より強い。

**深刻度**: must-fix (登録を M6a=`:1138` / M6b=`:1226` に分割)。

### B-3 (must-fix) — M7 は kill ではなく pin。登録された期待「receipt が永続化されない」は実装上到達不能

**根拠**: `dispatch_compute.py:547-570` (try は for ループ本体全体を包み、例外は握って `continue`) /
`s4-adjudication.md` M7 行。

**失敗シナリオ**: M7 を注入して T6 が赤になっても、赤の理由は `:340 assert all(persisted_when_called)`
(順序プローブ) であって、receipt 消失ではない。登録の期待と実際の赤理由が食い違うため、「fail-closed
後退を kill で捕まえた」という主張は成立しない。実際に receipt を失うのは **M5 ∧ M7 の連言**のみで、
これは登録されていない。

**成果物影響**: 試行台帳の変異 matrix に、実証されていない kill が 1 件 (M7) 計上される。台帳の受理集合
主張が実測より強くなる。

**深刻度**: must-fix (M7 を pin へ格下げし、真の kill として M5∧M7 の連言変異を登録し直す)。

### B-4 (must-fix) — 宣言の巻き上げ `:881-882` が load-bearing なのに無検出

**根拠**: `dispatch_compute.py:881-882` と `:1226-1230`、`:1231-1235`。既存 `test:838` (queue timeout) と
`test:952` (qstat 例外) は rc と receipt.json しか見ない。

**失敗シナリオ**: 巻き上げを戻すと、collection 到達前に投げる経路 (queue-wait timeout, qsub 失敗,
overall timeout) で `:1226` が `UnboundLocalError` を投げ、外側 `except` を抜けて `dispatch()` の catch
(`:1293`) に落ちる。結果、運用者が見る唯一の原因行が `Pegasus dispatch infrastructure failure: <本当の原因>`
から `Pegasus dispatch setup failure: UnboundLocalError: ...` に**すり替わる**。rc は INFRA_RC のまま、
receipt.json も `:1225` で書けているので `test:838` も `test:952` も緑。

**成果物影響**: 原因が消えるのではなく偽の原因に置換されるため、worklog の失敗記述が誤った型
(setup 失敗) で台帳に入る。B-1 より悪い。

**深刻度**: must-fix (M8 として登録 + `test:838` に原因文字列の assert を 1 行)。

### B-5 (nit) — T6 は 3 変異で赤くなる過剰決定テスト

**根拠**: `:338 assert rc == 12` (M5 で赤)、`:339 assert persisted_when_called` (M1 で赤)、
`:340 assert all(persisted_when_called)` (M7 で赤)。

**失敗シナリオ**: `DW-M08` の「第一失敗 node」を test 関数名の粒度で記録している場合、M1・M5・M7 が
同一 node を返し区別できない。assert 行番号まで記録している場合のみ区別可能。

**深刻度**: nit (harness の node 粒度を assert 行に固定すれば足りる)。

### B-6 (nit) — T8 と T9 は同一の 1 行 (`:1226`) しか固定していない

**根拠**: `dispatch_compute.py:1145` と `:1162` がともに外側ハンドラ `:1226` へ落ちる。

**成果物影響**: 台帳の被覆記述が実測より 1 経路分厚く見える。値は動かない。→ nit。

### B-7 (nit) — infra 3 テストが stream 対応も同時に主張しており、M4 と M6 を区別できない

**根拠**: `:356-357`, `:370-371`, `:384-385`。

**失敗シナリオ**: T8 が赤になったとき、単体では「infra 中継が消えた」のか「stream が入れ替わった」のか
判別できない。区別は T1/T2 との集合比較でのみ可能で、テスト単体の赤理由は一意でない。

**成果物影響**: `DW-M01` の単一理由性が集合レベルでしか成立せず、テスト単体を証拠として引けない。→ nit。

### B-8 (nit) — 枠テスト T3 は「枠の縮小」を検出できない

**根拠**: `:282-286`。fixture は 29 + 6000 = 6029 bytes なので、枠を 6029 超へ拡大した場合のみ `:281` の
`not in` が赤になる。期待値を `DC.DEFAULT_SUCCESS_RELAY_LIMIT_BYTES` から導出するため、定数と期待値が
同時に動き、枠を 4096 → 512 に縮めても緑のまま。

**失敗シナリオ**: 緑走の中継枠が 4 KiB から 64 bytes に縮む退行が入っても全テスト緑。brief scope 2 の
「既定 4 KiB」というリテラルを固定するテストが 1 本もない。

**成果物影響**: 成果物の値・受理集合は変わらない (診断量のみ)。よって nit と自己申告する。

### B-9 (backlog) — 失敗経路の中継量に上限テストがなく、T2 が「無制限」を積極的に固定している

**根拠**: `dispatch_compute.py:33` (4 KiB) と `:1256` (`log_limit_bytes=2 MiB`)、`:1186-1190`、`test:263`。

**失敗シナリオ**: dogfood 経路で子 pytest が大量に落ちると、最大 2 MiB が親エージェントの stdout に
流れる。これは brief scope 2 が緑走について挙げた「親の裁定容量を食う」失敗を、赤走で丸ごと再現する。
後から上限を入れる修正は T2 を赤にする。

**成果物影響**: 値は変わらないが wave の完走可能性が下がる (scope 2 と同じ失敗モード)。

**深刻度**: backlog ((P1) の設計判断そのものへの異議。少なくとも赤側の上限を定数化して pin を 1 本
置くべき)。

### B-10 (backlog) — 境界マーカが偽装可能で、しかもこのテストファイル自身が偽装文字列を含む

**根拠**: `dispatch_compute.py:558-568` (本文は無加工)、`test:249`, `:277`。dogfood 経路で
`test_pegasus_dispatch_compute.py` が失敗すると pytest の traceback にソース行が印字され、中継本文に
偽の end マーカが現れる。

**失敗シナリオ**: T3 (`:278`) と同じ `split(end, 1)[0]` 型のパースを親や後続ツールが行うと、本文が途中で
切れる。マーカ衝突を固定するテストは 1 本もない。

**成果物影響**: 診断の境界が誤って解釈され、worklog の原因記述が中途半端な抜粋に基づく。受理集合は
不変。→ backlog。

### B-11 (nit) — 中継失敗が完全に無音で、「子が無出力」と「中継が壊れた」を親が区別できない

**根拠**: `dispatch_compute.py:569-570`、`test:305-317` (T5 は `_emit` が呼ばれたことすら assert しない)。

**失敗シナリオ**: 親 stdout が閉じたパイプ (BrokenPipeError) のとき、中継は静かに全滅する。親エージェントは
「子は何も出力しなかった」と結論し、brief scope 3 が防ごうとした「原因記述が推測になる」状態へ裏口から
戻る。加えて `BaseException` は `KeyboardInterrupt` / `SystemExit` も飲むため、最大 2 MiB の書き出し中の
Ctrl-C が握り潰される。

**成果物影響**: 中継が壊れた事実が台帳に残らず、worklog の原因欄が誤った前提 (子が無出力) で書かれうる。

**深刻度**: nit (T5 に `assert emit_mock.called` を足せば少なくとも到達性は固定できる。現状 T5 の前件
到達性は T6 に依存しており、T6 が変われば T5 は無言で恒真化する)。

### B-12 (backlog) — 不変条件「再 decode・再読込をしない」に対応するテストも変異もない

**根拠**: 全 fixture が `log_limit_bytes` (既定 2 MiB) 未満で、`_bounded_log` の切り詰めが発火しない。
よって `record["path"]` からファイルを読み直す実装に置き換えても、9 テスト全部が同じ結果になる。

**失敗シナリオ**: 中継が `omitted_bytes > 0` の tail ではなくファイル全体を読み直す実装に変わっても
無検出。加えてこの経路には既存欠陥がある — `dispatch_compute.py:512` の省略注記はリテラルの
バックスラッシュ + n であり改行ではないため、切り詰め時の中継 1 行目が注記と本文の接着した 1 行として
出る (既存テスト `:833` は改行を検査していない)。本 wave 以前は receipt JSON 内だけの問題だったが、
中継によって親の画面へ露出した。

**成果物影響**: 中継 tail の先頭行が壊れた形で親へ渡り、切り詰め有無の判断を誤らせうる。値・受理集合は
不変。→ backlog (`:512` の修正は本 wave の scope 外。切り詰め経路の中継テストを 1 本足すのは scope 内)。

### B-13 (nit) — T1 は M1〜M7 の中で固有の kill を持たない

**根拠**: 対応表 (M1 で T1/T2/T4 が同時に赤)。T1 固有の内容は `:248-249` のマーカ文字列 2 本だけで、
これは `DW-M03` により kill に数えられない診断文字列である。

**成果物影響**: 台帳の kill/pin 分類が 1 件ずれる。→ nit (T1 を pin と明示ラベルすればよい)。

---

## 3. 攻撃して空振りだった点 (実装/テストが持ちこたえた箇所)

- **stream 分離 fixture の同一内容問題**: 成立しない。T4 (`:292-293`) は別 sentinel を使い、双方向の
  `not in` (`:300`, `:302`) まで置いている。取り違えは両方向で検出される
- **枠テストの上限のみ検査**: 半分だけ成立 (B-8)。`:282` は厳密等値で、UTF-8 境界での切り捨て位置
  (1365 文字 × 3 = 4095 bytes、残り 1 byte で break) まで一意に固定している
- **`_emit` seam の人工性**: 注入は `RuntimeError` というテスト専用例外だが、実装側の捕捉が
  `except BaseException` なので例外クラスは検出力に影響しない。現実の失敗 (BrokenPipeError,
  UnicodeEncodeError, ValueError on closed file) はすべて同じ枝を通る。人工物だが無害と判断する
- **`capsys` が中継を捕捉できるか**: 捕捉できる。`:543-546` は `sys.stdout` / `sys.stderr` を呼び出し時に
  解決しており、`_emit` (`:204-207`) がそれを `file=` に渡すだけなので `capsys` の差し替えが効く
- **既存 905 行の破壊**: 静的には見当たらない。既定 fixture では `.o` が空 → stdout 中継は `:551` の
  空チェックで skip、`.e` は会計ブロックがあるため全既存テストで stderr 中継が発火するが、既存の
  stderr assert は `:638` の `in` 検査 1 本だけで、`not in` 型の stderr assert は存在しない。diff も
  既存テストを 1 行も書き換えていない (不変条件 4 は守られている)
- **latch の repo 汚染**: 成立しない。`root` は `output_root` (= `tmp_path/dispatch`) に解決される

---

## 4. まとめ (親への推奨)

- **must-fix 4 件**: B-1 (`:1179` 完全無防備)、B-2 (M6 が `:1138` を含まない)、B-3 (M7 は kill でなく pin、
  期待が到達不能)、B-4 (`:881-882` の巻き上げが無検出で、壊すと原因が偽装される)
- 変異事前登録の穴は **M1 の適用位置が一意でないこと** (rc≠0 専用の呼び出しが存在せず、`DW-M04` の
  置換一意性を満たす anchor が取れない) と、**call site 4 か所のうち 2 か所 (`:1138`, `:1179`) と
  巻き上げ 1 件が未登録**であること。M1 は「`:1186-1190` の呼び出しを削除する」形に読み替えたうえで、
  M6a/M6b/M8 (巻き上げ) /M9 (`:1179` 削除) を追加登録することを推奨する
- 検出力そのものは弱くない — T2/T3/T5/T6 は各 1 変異だけを殺す良い単独 killer である。問題は
  **被覆漏れ (call site 2 か所) と登録側の記述精度**に集中している
