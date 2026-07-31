# [T-194] 段 6 敵対レビュー A — レンズ「正しさ境界」(逐語)

- 実行: claude / opus / 静的レビューのみ (pytest 未実走。共有ログインノード制約)
- 対象: 段 5 codex 実装子の diff (`tools/pegasus/dispatch_compute.py` +83、
  `orchestrator/tests/test_pegasus_dispatch_compute.py` +152)
- 読んだもの (子の自己申告): 親 brief、s4 裁定、`git diff` 全文、`dispatch_compute.py` 全体 (HEAD 比較込み)、
  テスト全 1057 行、`tools/run_tests.py` の dispatch 経路、`hooks/guard_bash.py`、`docs/failures.md` 索引、
  `docs/pegasus-runbook.md`

---

## A-1 (must-fix) 中継が SIGINT/SIGTERM を握り潰し、既存の signal 契約を無効化する窓を作る

**主張**: `_relay_scheduler_logs` の `except BaseException: continue` は `_SignalAbort` (= SIGINT/SIGTERM
ハンドラが投げる例外) も飲むため、中継中に来たシグナルが無応答になる。

**根拠**: `dispatch_compute.py:569-570`、`:885-892` (SIGINT/SIGTERM → `_SignalAbort`)、
`:1237-1242` (ハンドラ復元は `finally` = 中継より後)。既存契約は
`test_pegasus_dispatch_compute.py:923-949` が固定している
(`receipt["outcome"]["reason"] == "_SignalAbort: signal N"`、qdel 実施、rc = INFRA_RC)。

**失敗シナリオ**: 赤走 (child_rc≠0) で `.o` が数百 KiB〜2 MiB。`:1186` の中継が stdout へ書いている
最中に、背景 dev-wave job の driver が SIGTERM を送る。PEP 475 により write が EINTR で中断され
ハンドラが `_SignalAbort` を投げるが、`:569` が飲んで次の stream へ `continue` し、そのまま
`return child_rc`。stdout が詰まった FS / 遅い reader に向いていると write がブロックしたままで、
その間 SIGINT も SIGTERM も一切効かない。最終的に SIGKILL するしかなく、
`tools/run_tests.py:884-905` の `_record_task_run` に到達しない。

**成果物影響**: 中断された受入全走が試行台帳 (`output/task-runs`) に entry を残さず、その run の
`exit_status` / `duration_s` が欠落する (台帳の穴)。

**注記 (実装子への公平な指摘)**: `BaseException` を握るのは brief の不変条件「中継の例外を握って
rc を変えてはならない」を字面どおり満たすための唯一の手段になっている — `:1186` で例外を通すと
外側 `except BaseException` (`:1192`) が拾い、`receipt["outcome"]` を `infra` へ書き換え、
`_persist_receipt` (`:1225`) が O_EXCL 衝突で `receipt-fallback-<nonce>.json` を矛盾する outcome で
二重生成し、rc も INFRA_RC へ変わる。つまり不変条件の書き方自体が欠陥 (→ A-6b)。

---

## A-2 (must-fix) 「rc は中継で変わらない」は関数戻り値でしか検証されておらず、broken pipe で process 終了ステータスが化ける

**主張**: 新テストは `_emit` に `RuntimeError` を注入した場合しか見ておらず、`BrokenPipeError` 経路では
process の exit status が child_rc から 120 へ変わりうる。

**根拠**: `test_pegasus_dispatch_compute.py:305-317` (注入例外は `RuntimeError` のみ)、
`dispatch_compute.py:558-568` (`print(..., flush=True)` を最大 4 回)、`:569` の swallow。
前例は `docs/failures.md` F44 (`producer | grep -q` の SIGPIPE が計測ジョブを偽赤停止させた)。

**失敗シナリオ**: `python3 tools/run_tests.py | grep -q "passed"`。HEAD では dispatcher の stdout は
`_progress` 数行だけなので `grep -q` が先に閉じる前に producer が終わり、rc = child_rc。中継導入後は
赤走で 2 MiB を流すため `grep -q` が最初のマッチで pipe を閉じ、中継の `flush()` が `BrokenPipeError`
→ `:569` が飲む → `return child_rc`。しかし TextIOWrapper のバッファに未 flush の bytes が残り、
インタプリタ終了時の `sys.stdout` flush が失敗して CPython は終了ステータス 120 を返す。
`set -o pipefail` 下では緑走が偽赤になる。

**成果物影響**: 受入全走の rc が 0 → 120 に化け、その値が `_record_task_run(exit_status=rc)` 経由で
試行台帳へ偽の赤として記録される (F44 と同型の再発)。

**修正案**: `except BrokenPipeError:` を別枝にし、`break` して以降の中継を止め、
`os.dup2(os.open(os.devnull, os.O_WRONLY), stream.fileno())` で終了時 flush を無害化する。
加えてテストに broken-pipe fixture を足す。

---

## A-3 (must-fix) 中継本体が無 prefix・無エスケープで、子出力が dispatcher 自身の出力を詐称できる (規律 6)

**主張**: (P3) は枠線に `[Pegasus dispatch]` を付けたが、本文は素通しなので、子は end 枠も `_progress`
行も偽造できる。

**根拠**: `dispatch_compute.py:562` (`_emit(tail, stream=stream)` — 行 prefix なし)、`:200-202`
(`_progress` が同じ prefix を使う)、枠線は `:558-568` の固定文字列。

**失敗シナリオ**: 計算ノードの pytest 出力 (= CCBench / LLM 生成 variant / 外部由来 fixture が
印字しうる文字列) に `[Pegasus dispatch] child stdout end` と `[Pegasus dispatch] receipt を ... へ
保存しました (child rc=0)` が含まれると、親の job log 上で子データと dispatcher の信頼出力が
字面上区別できない。より本質的には、中継は汚染されうる子出力を親エージェントの裁定コンテキストへ
「データ」の枠なしで流し込む新しい搬入経路であり、brief にも裁定にも規律 6 への言及が一切ない。

**成果物影響**: 汚染された trace / variant 出力が「verifier は通った」「これは serializable だ」と
主張する行を親の文脈へ運び、親が受入結果を worklog・試行台帳の受入欄へ誤記録する
(規律 2/3 を緩める運び屋経路の新設)。機械 gate は動かない (`tools/run_tests.py:838-855` は int 戻り値
のみを使い、`hooks/guard_bash.py` も `tools/dev_wave_land.py` も dispatcher stdout を parse しない —
実測で確認済み)。

**修正案**: 中継本文を 1 行ごとに `| ` などで prefix する、または枠マーカに request nonce を埋める。

---

## A-4 (must-fix) 緑走の切り詰めが無告知で、`begin` 枠が嘘になる (brief 攻撃点 4 の的中)

**根拠**: `dispatch_compute.py:521-532` (`_utf8_tail` は notice ごと先頭を捨てる)、`:512` (notice は
tail の先頭に付く)、`:553-557` (成功時のみ切り詰め)、`:558-561` (枠は無条件に `child stdout begin`)。
テスト `:266-287` は「先頭が消えること」を要求しているだけで、消えた事実の告知は要求していない。

**失敗シナリオ**: 緑走で `.o` が 8 KiB のとき、親は `child stdout begin` に続く断片を見る。実際は
先頭 4 KiB が捨てられ、そこにあった `warnings summary` / `errors during collection` / skip 理由は
消えている。`_utf8_tail` は行境界でなく codepoint 境界で切るため 1 行目は断片で、`begin` という語が
その断片を「子 stdout の先頭」だと主張する。`.o` が 2 MiB 超なら `_bounded_log` の省略注記も
一緒に落ち、二重に省略された 4 KiB が無印で出る。

**成果物影響**: 親が緑走の中継を「子の全出力」と読み、切り落とされた collection error / skip を
見落として受入欄に「全 pass」と誤記録する。

**修正案**: 切り詰めた場合の枠を `child stdout tail (last N bytes of M)` にする、`_utf8_tail` を
直近改行境界まで戻す、`record["omitted_bytes"]` と `record["size"]` を枠行へ載せる
(record には既に両方ある: `:513-518`)。

---

## A-5 (must-fix) 中継サイトは 4 箇所あるが検査は 3 箇所で、事前登録 M6 / M7 が site 未指定のまま「kill 済み」と記録される

**根拠**: 中継呼び出しは 4 箇所 — `:1138` (marker infra)、`:1179` (receipt 永続化失敗)、`:1186` (通常帰還)、
`:1226` (外側 except)。テスト対応は `:1138` → test:347、`:1186` → test:238/252/266/289/305/320、
`:1226` → test:361 と test:375 (両方とも同じサイト)、`:1179` → 対応テストなし。この経路を通る既存
テスト `test_success_without_any_persisted_receipt_is_infra_rc` (test:815-819) は rc しか見ない。

**失敗シナリオ**: harness が M6 を `:1179-1183` の削除として当てると、赤になるテストが 1 つも無く
SURVIVED になる。M7 を `:1137↔:1138` または `:1225↔:1226` に当てても、順序を見るテストは test:320-345
だけで、それは `:1171` の永続化 (通常帰還サイト) しか拘束しないため SURVIVED になる。つまり変異行列の
値が harness の site 選択に依存する。

**成果物影響**: 段 7 の変異行列 (成果物の一部) が「M6/M7 kill 済み」という偽の緑を記録し、fail-closed
後退の検出力の証明が空証明になる。`DW-M04` 置換一意性違反。前例 F28・F60・F33 と同型。

---

## A-6 (must-fix、brief 自身への攻撃) scope 1 の被害記述「台帳の受入欄から node 名が欠落する」は、本 wave では解消しない

**根拠**: `tools/run_tests.py:858-905` — Pegasus dispatch 経路の `_dispatch_and_record` は
`_record_task_run(..., sidecar=None)` を渡す (`:903`)。`_record_task_run` は `sidecar is None` のとき
`counts` と `collected_node_digest` を `None` のまま `record_test_run` へ渡す (`:727-751`)。sidecar は
`_dispatch_environment` (`:816-823`) が計算ノードへ渡す環境から明示的に落としている。中継は stdout へ
text を出すだけで、この経路に一切触れていない。

**失敗シナリオ**: 本 wave land 後、worklog に「T-194 で Pegasus 経由でも `DW-M08` の失敗 node 記録が
可能になった」と書かれる。実際には `output/task-runs` の entry の `collected_node_digest` は依然 `None` で、
node 名は人間/エージェントが stdout から手写しした場合にしか worklog へ入らない。

**成果物影響**: 試行台帳の `collected_node_digest` 欄が空のまま「修復済み」と記録され、後続 wave が
台帳を根拠に失敗 node を引けると誤前提する (F31 と同型)。

**修正案 (コード修正は不要)**: brief / worklog の記述を「台帳欄の修復ではなく、人間・親エージェントが
読める一次資料の確保」に訂正する。台帳欄の修復は別タスクとして起票する。

### A-6b (must-fix、不変条件自身への攻撃)

brief の不変条件「dispatcher が返す rc は中継の有無・成否で変わらない。中継は best-effort で、
その例外を握って rc を変えてはならない」は、「中継の失敗」と「中継中に起きた無関係な事象
(ユーザー中断)」を区別していない。この文言が実装子を `except BaseException` へ追い込み、A-1 の
signal 契約破壊を生んだ。不変条件は「中継の I/O 失敗 (= `Exception`) で rc を変えない。
`BaseException` (シグナル・SystemExit) は従来どおり伝播させる」と書き直すべきである。
**成果物影響**: 現行の文言のまま land すると、`_SignalAbort` を握り潰す実装が「不変条件を満たす正解」
として凍結される。

---

## A-7 (backlog、(P1) への攻撃) 赤の「収集済み全量」は 1 stream 2 MiB / 計 4 MiB の無制限で、緑を絞った理由がそのまま当てはまる

**根拠**: `dispatch_compute.py:33` (`DEFAULT_LOG_LIMIT_BYTES = 2 * 1024 * 1024`)、`:553-557`
(successful=False なら切り詰め皆無)、`:1186-1190`。brief `scope (in)` 2 の理由付け。

**失敗シナリオ**: 受入全走が赤で traceback と assertion diff により `.o` が数百 KiB。中継は stdout へ
全量、stderr へも全量を流す。背景 dev-wave job の log をそのまま読む親の裁定容量が、診断が最も必要な
瞬間に食い潰される。`DW-M08` が要る情報 (失敗 node 名) は pytest の short summary = 末尾にあり、
全量は必要条件ではない。

**成果物影響**: 親が赤の中継を読み切れず wave が完走できない場合、worklog の「次の一手」と台帳の
受入欄が未記入で残る。

**backlog とする理由**: 実際の `.o` サイズを本 wave では実測していないため、被害の発火確率を断定できない。
親の再裁定を求める。対案 = 赤も上限付き (例: 64 KiB) の末尾 + 明示的な省略注記。全量は receipt に
既に残っており一次資料は失われない。

---

## A-8 (nit) infra 3 経路で「dispatcher 自身の原因行」と「子ログの山」の順序が不揃い

**根拠**: `:1174-1183` は「receipt を永続化できませんでした」→ 中継 の順。`:1137-1143` は 中継 →
`_print_terminal_handoff` の順。`:1225-1235` は 中継 → 「Pegasus dispatch infrastructure failure」の順。

**失敗シナリオ**: stderr の先頭 N KiB だけを読んで infra 失敗を分類する読み手は、3 経路のうち 2 経路で
dispatcher の理由行ではなく子の stderr を見る。scope 3 が改善しようとしたまさにその経路で、原因文字列が
下へ押し出される。

**成果物影響**: worklog の原因記述が経路によって当たり外れになる (診断面のみ)。→ nit と自己申告する。

---

## A-9 (nit) `_bounded_log` の省略注記が改行でなく literal のバックスラッシュ + n で連結されており、中継で可視化される

**根拠**: `dispatch_compute.py:512` は非 raw 文字列中で 2 文字のエスケープを二重化しており、改行では
ない (`cat -A` で確認)。既存テスト `:822-836` は `in` 判定なので検出しない。

**失敗シナリオ**: 2 MiB 超の `.o` を持つ赤走で、中継の 1 行目が省略注記と最初の失敗 node 行が接着した
1 行として出る。

**成果物影響**: 診断表示のみ。既存欠陥 (HEAD にも存在) で本 diff は無罪だが、中継がこれを端末上に
露出させた。→ nit。

---

## A-10 (nit) F47 latch 2 経路に中継が無いのは今は無害だが、前提が明文化されていない

**根拠**: `INFRA_RC` を返す経路の全列挙 = `:831`、`:991`、`:1012`、`:1144`、`:1184`、`:1236`、および
`dispatch()` の `:1327`。このうち `:991` / `:1012` に中継は無い。実際には `_find_log` は終端状態ループ後の
収集ループ (`:1079-1092`) でしか呼ばれないため、両サイトでは record が必ず `None` であり、scope 3 は
空虚に充足されている。

**失敗シナリオ**: 将来「終端待ち中にも `.o` を先読みして進捗を出す」変更が入ると、`:991` / `:1012` だけ
収集済みログを黙って捨てる。これを赤にするテストは存在しない。

**成果物影響**: 現時点ではゼロ。→ nit。

---

## A-11 (nit) 中継途中で例外が起きると `begin` 枠だけが残り、切断の告知が無い

**根拠**: `:558-570` — `begin` を出した後に `_emit(tail)` が失敗すると `except` が `continue` するため
`end` 枠が出ない。

**成果物影響**: 診断表示のみ。→ nit。

---

## 攻撃したが問題を見つけられなかった点 (反証済み)

- **変数巻き上げ (brief 攻撃点 3)**: `stdout_record` / `stderr_record` の宣言を `:881-882` へ移した変更は、
  `_dispatch_impl` が 1 呼び出し 1 request である以上、古い request の record が漏れる経路を作らない。
  HEAD では収集ループ到達前に例外が出ると外側 except からこれらの名前が `NameError` になる潜在欠陥が
  あり、巻き上げはそれを塞いでいる。既存の early return 経路はいずれも巻き上げ位置より前または
  record が `None` の状態で、意味は変わらない
- **`_utf8_tail` の計算量と境界**: 末尾から 1 文字ずつ戻るが `remaining` が尽きた時点で `break` するので
  反復は高々 4096 回。2 MiB の tail でも O(limit)。`errors="replace"` 由来の U+FFFD もエンコード可能で、
  `while start:` により text が limit より短い場合は全文を返す。test:266-287 の期待値
  (`4096 // 3 = 1365` 文字) と一致する
- **(P2) 親 stdout が rc 判定に使われていないか**: 使われていない。`tools/run_tests.py:838-855` は
  `int(dispatch_fn(...))` の戻り値のみ、`_record_task_run` も rc のみ。`hooks/guard_bash.py` は
  `tools/run_tests.py` / `dispatch_compute.py` を sanctioned path に載せているだけで出力を parse しない。
  `tools/dev_wave_land.py` / `tools/dev_waves.py` / `tools/check_wave_startup.py` に pytest 出力の
  parse は無い (grep 実測)。したがって (P2) 自体は機械的な受理集合を動かさない — ただし A-3 の
  親エージェント経路は残る
- **qdel / abort 契約**: 中継 4 サイトはすべて `active = False` (`:1130`, `:1172`) または qdel 試行後
  (`:1198-1224`) に位置しており、A-1 のシグナル握り潰しでも「生きた request を残したまま抜ける」経路には
  ならない。ここは実装子の配置が正しい
- **変異 M1〜M5**: `:1186` サイトに当たる限り、新テスト (test:238/252/266/289/305) がそれぞれ単独で
  赤になる。特に M5 は注入 `RuntimeError` が外側 except → 再送出 → `dispatch()` へ抜けて rc が 11 → 16 へ
  変わるため、test:305 と test:320 の両方が赤になり kill される
