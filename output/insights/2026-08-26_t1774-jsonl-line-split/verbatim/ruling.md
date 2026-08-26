# 段 4 裁定 (親)

段 2 plan と段 3 相談 A (レンズ = 正しさ境界) / B (レンズ = 整合・実効性) の所見を裁定する。

## 採用した real 所見

### R1. 親 brief の「bytes 5 箇所は F609 の経路ではない」は 2 箇所で誤り (A, B)

`tools/codex_worker_launch.py:1273` と `:4097` は分割後に `parse_jsonl` を呼び、
同関数が bytes を str へ decode してから `str.splitlines()` を通る
(`orchestrator/codex_roles/events.py:170-181,314-316`)。よって site 自体は bytes でも
**経路としては現在の F609 に到達する**。`:1406` `:2335` `:4119` は 1 行だけ decode して
`strict_json_loads` へ直接渡すため、下流に str 行分割は無い。

**裁定: real・採用。** 用語を分ける。
- **局所原因**: `events.py:316` の 1 箇所だけ。
- **経路上の影響あり**: `:1273`、`:4097`。
- **経路上の影響なし**: `:1406`、`:2335`、`:4119`。

brief の当該記述を上記へ訂正する。

### R2. 受理集合は CR / CRLF 側で縮む。brief の不変条件は書き直す (A, B)

`bytes.splitlines()` は CR / CRLF でも切って CR を捨てるが、`split(b"\n")` は CR を行に残す。
`_decode_jsonl` と `strict_json_loads` は CR を拒否するので
(`events.py:193-194,291-292`)、これまで黙って受理されていた CR / CRLF 終端 event は
拒否されるようになる。

**裁定: real・採用。ただし実装は裁定どおり 6 箇所すべて変える。** 不変条件を次へ書き直す。

> 正常な LF JSONL への挙動は不変。U+2028 / U+2029 を含む正当な入力は受理側へ広がる。
> CR / CRLF による過受理は縮む。

裁定の前提「正常入力への挙動は不変」は覆らない。根拠は 3 つで、いずれも実測である。

1. この系は CR を既に不正と宣言している (`events.py:193-194`、`:291-292`)。
   `splitlines()` による CR 除去は、その宣言に反する入力を黙って修復していた。
   縮むのは**宣言済みの不正入力に対する過受理**であって、正常入力ではない。
2. 親が既存の封印済み codex event artifact を全件走査した。
   `/work/1/SFC/tanab/dev-wave-jobs` 配下の `attempt-*.events.jsonl` **3,678 件を走査し、
   CR を含む file は 0 件**だった。相談 A が挙げた「旧版で封印された CRLF artifact が
   resume 監査で壊れる」は、その artifact が実在しないため発火しない。
3. 既存テストに CR / CRLF 仕様を固定するものは無い (相談 B が独立に確認)。

**却下: 相談 A の推奨 1 (`events.py:316` だけ直す)。** これは承認済みユーザー裁定
{{D:jsonl-line-split-ratified}} の 6 箇所を親が 1 箇所へ縮めることであり、`DW-S04` により
親は承認済み裁定を不採用にできない。前提を覆す未見の新事実は上記のとおり存在しない。

**却下: 相談 A の推奨 2 (分割後に末尾 CR を落として CRLF 耐性を保つ)。**
それは `events.py` が CR を不正と宣言している規律に反する黙示修復を新設し直すことである。
さらに `bytes.splitlines()` と機能的にほぼ等価になるため、変更の意味が消える。

### R3. 変異とテストの一対一帰属は成立しない (A, B)

`events.py:316` を戻すと、stdout 経路を通る 3 本が同時に赤になる。

**裁定: real・採用。** 変異事前登録は**一対一を主張せず、変異ごとに「指定 killer node の集合」**
を登録する。fanout は許容し、その旨を台帳に書く。各 bytes site には、
その site だけを戻したときに赤になる専用 node を 1 本ずつ持たせる。

### R4. 親の (P3) は 5 変異すべてを SURVIVED にする (A, B が独立に一致)

`bytes.splitlines()` は U+2028 / U+2029 では分割しないので、対象文字の受理だけを検査する
テストは bytes 5 箇所の変異に対して恒真である。

**裁定: real・採用。(P3) を撤回する。** bytes 5 箇所の killer は
**CRLF 終端の ASCII JSON event** とする。対象文字の受理検査は別関数に分け、
両方を新規 file に置く。

### R5. 新規 test file は F42 のメタ検査で確実に赤になる (B)

`orchestrator/tests/test_codex_role_runtime.py` は自走 harness を持たず
`orchestrator/tests/README.md:129-135` の allowlist に載って成立している。
plan の §4 は import bootstrap を自走性と誤認していた。

**裁定: real・採用。** 新規 file に
`if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))` を置く。
README の allowlist は編集しない (変更 file を増やさない)。
親の焦点走に `orchestrator/tests/test_plain_runner_coverage.py` と
`orchestrator/tests/test_dev_waves_isolation_contract.py` を必ず含める。

### R6. 直接呼出しテストの fixture 契約が不足している (B)

**裁定: real・採用。** 相談 B が実測した exact な契約を実装子へそのまま渡す。

### R7. 表記の是正 (B)

「JSONL の行分割は 6 箇所で閉じる」は repo 全体では偽。
live reader は `:1268` `:1401` の LF `rpartition` でも行を切っている。

**裁定: real・採用。** 以後は
**「指定 2 file の置換対象 `splitlines()` 6 式」**と表記する。
brief の当該記述を訂正する。

### R8. `tools/codex_worker_launch.py:327` の除外は正しい (B が独立確認)

現 checkout の `git rev-parse --show-toplevel` の stdout は末尾が LF であり、
`split("\n")` にすると 2 要素になって `len(top_level_lines) != 1` が真になる。
正確な言い方は「正常な live git 出力では常時失敗する」。

**裁定: real・確定。`:327` は変更しない。**

## refuted / scope 外

### N1. unknown stdout event の黙殺 (A)

`_consume_stdout_event` が `thread.started` と `turn.completed` 以外を無視するのは現行仕様であり、
本 wave の変更が作るものではない。今回の変更は「正当な JSON event が parse できるようになる」
だけで、正しさゲートを緩めない。**本件については refuted。**
unknown event を fail-closed にすべきかは別問題として scope 外・裁定候補に留める。

### N2. `tools/check_codex_hooks.py:423` に同型欠陥が残る (B) — **裁定パッケージへ返す**

`_parse_events` が Codex JSON event の str stdout を `stdout.splitlines()` で切っており、
`events.py:316` と**完全に同型**である。JSON string 内の U+2028 / U+2029 で同じく割れる。
親が現物で確認した (`tools/check_codex_hooks.py:420-431`)。

**裁定: real。ただし scope 外。** 承認済み裁定 {{D:jsonl-line-split-ratified}} は
「6 箇所」を明示列挙しており、7 箇所目を親の判断で足すと確定 scope を広げることになる
(`DW-S04`: scope 外の real 所見は実装せず裁定パッケージで返す)。
段 7 で failures へ記録し、ユーザーへ裁定パッケージとして返す。

### N3. test file の恒久配置 (A)

新規 file は別 wave との編集面重複を避けるための配置だが、
U+2028 / U+2029 と改行方針という主題が独立しているため恒久配置として妥当である。
**refuted (一時回避ではない)。**

## 確定した plan v2

**変更する 6 式 (これ以外のコードを変えない):**

| # | file:line | 変更前 | 変更後 |
|---|---|---|---|
| 1 | `orchestrator/codex_roles/events.py:316` | `text.splitlines()` | `text.split("\n")` |
| 2 | `tools/codex_worker_launch.py:1273` | `complete.splitlines()` | `complete.split(b"\n")` |
| 3 | `tools/codex_worker_launch.py:1406` | `complete.splitlines()` | `complete.split(b"\n")` |
| 4 | `tools/codex_worker_launch.py:2335` | `raw.splitlines()` | `raw.split(b"\n")` |
| 5 | `tools/codex_worker_launch.py:4097` | `closed.splitlines()` | `closed.split(b"\n")` |
| 6 | `tools/codex_worker_launch.py:4119` | `raw.splitlines()` | `raw.split(b"\n")` |

**新規 file:** `orchestrator/tests/test_codex_jsonl_line_split.py`

**テスト構成 (7 本):**

- `test_parse_jsonl_accepts_unicode_line_separators` — U+2028 / U+2029 を parameterize。
  変異 1 の killer。
- `test_parse_jsonl_still_rejects_malformed_and_oversized_lines` — 正例。
  受理集合を縮める wave の過剰拒否検出 (`DW-M01`)。既存の byte 上限・object 要求・
  重複 key 拒否が生きていることを固定する。
- `test_drain_stdout_rejects_crlf_terminated_event` — 変異 2 の killer。
- `test_tail_rollout_rejects_crlf_terminated_event` — 変異 3 の killer。
- `test_recorded_summary_skips_crlf_terminated_event` — 変異 4 の killer。
- `test_recompute_metering_stdout_rejects_crlf_terminated_event` — 変異 5 の killer。
- `test_recompute_metering_rollout_rejects_crlf_terminated_event` — 変異 6 の killer。

加えて、対象文字を含む LF event が stdout 経路で受理されること
(`test_drain_stdout_accepts_unicode_line_separators`) を 1 本置く。これは
end-to-end で F609 が直ったことの証拠であり、変異 1 でも赤になる (fanout を許容する)。

**変異事前登録 (6 本 + 正例、`DW-M01`):** 各式を `splitlines()` へ戻す 6 本。
指定 killer node は上記の対応どおり。変異 1 は 3 本以上が同時に赤になる fanout を許容する。
正例は `test_parse_jsonl_still_rejects_malformed_and_oversized_lines`。

**焦点走の対象:**

1. `orchestrator/tests/test_codex_jsonl_line_split.py`
2. `orchestrator/tests/test_codex_role_runtime.py`
3. `orchestrator/tests/test_codex_worker_launch.py`
4. `orchestrator/tests/test_plain_runner_coverage.py`
5. `orchestrator/tests/test_dev_waves_isolation_contract.py`
6. `orchestrator/tests/test_codex_hooks.py`
