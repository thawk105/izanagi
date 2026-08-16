## 総括

- **must-fix が 3 件ある。現差分のままでは段 6 を通してはならない。**
- F1 の実際の起動形は `main()` を通り、lease 環境変数も存在する。正常 land 成功時の F1 は閉じる。
- ただし provenance 後の control-plane 変更による `rc=21` が解放不能のままで、同型の TTL 残留を起こせる。
- 新しい JSON 2 field により、従来 64 KiB 未満だった有効な land 結果が `message()` で拒否される境界退行がある。
- 既存テスト 23 node の期待値が変更されており、依頼の「既存 node の期待値変更は blocker」という条件に反する。`LandResult` の dataclass equality も実際に変わった。
- F2 は最初の `rc=29` で lease を解放するが、外側 loop は止まらず、2 回目以降は lease 無しで重い provenance を再実行する。裁定 R-E の残課題は実在する。
- 新規テストによる `os.environ`、cwd、module pin の漏出は成立しなかった。親の焦点走で落ちた既存 exploration test の原因にはできない。
- release の stderr 1 行だけでは F1 再発を事後検出できない。特に t1142 の runner はログを毎回上書きする。

## 所見 1 — provenance 後の `rc=21` が release-safe に分類されない

**重要度: must-fix**

`tools/dev_wave_land.py:2793-2799` は provenance 実行後に control directory の snapshot が変化すると `_Reject(RC_CONTROL_PLANE, ...)` を送出するが、新しい `release_safe` / `retryable_while_holding` を指定していない。

この時点では最初の locked preflight が active plan 不在を確認済みであり、この land 自身もまだ main を変更していない。一方、`quiescent_rejection = True` の設定は `tools/dev_wave_land.py:2842` まで行われない。そのため `tools/dev_wave_land.py:3145-3158` の outer catch は既定値 `(False, False)` を返し、`main()` は lease を保持する。

新しく変更された既存テスト `orchestrator/tests/test_dev_wave_land.py:2413` も、この誤った `(False, False)` を期待値として固定している。

成立する状況:

1. wave が lease を持つ。
2. 初期 preflight は active plan 不在で通る。
3. provenance 実行中に control directory が置き換わる。
4. 再取得後に `rc=21`。
5. retryable ではないのに自動解放もされず、外側 runner が終了する。
6. lease は TTL まで残る。

これは裁定 `ruling.md:92-95` の「`rc=21` を一律 retryable にせず、release-safe を個別判定する」という B-3 採用理由に反する。

最小修正は、この直接送出点でも active plan 不在を再確認して `release_safe=True` とするか、snapshot-change 判定を active-plan 再確認後へ移すこと。

**成果物への影響:** 後続 wave が acceptance lease を取得できず、certified 選択、レポート生成、台帳確定が TTL まで遅延または未完了になる。

## 所見 2 — JSON 2 field の追加が 64 KiB 境界で既存の成功経路を壊す

**重要度: must-fix**

`LandResult.as_json()` は `tools/dev_wave_land.py:170-171` で次の field を追加する。

- `release_safe`
- `retryable_while_holding`

一方、`wave_land_window.message()` の JSON 上限は `tools/wave_land_window.py:34,872-888` の 65,536 bytes のままである。

静的に parser-valid な `non-attributable-only` receipt を組み立てると、たとえば現実的な長さの nodeid を 1,205 個含むケースで次が成立する。

| 対象 | byte 数 | 判定 |
|---|---:|---|
| receipt | 65,220 | land の上限内 |
| 変更前の成功 JSON | 65,517 | `message()` 受理 |
| 変更後の成功 JSON | 65,572 | `message()` が rc=3 で拒否 |

入力、land 判定、既存 JSON field は同じで、追加した 2 bool だけが境界越えの原因になる。新規テストにはこの境界がない。

候補修正は、stdout JSON を compact separators で出力して十分な余裕を確保するか、land JSON に対する安全な最大長を証明したうえで `message()` の上限を拡張し、変更前後の境界を回帰テストにすること。

**成果物への影響:** main と canonical ledger は更新済みなのに `message()` が結果を拒否し、後続レポートや通知から main SHA、fold、receipt 参照が欠落する。

## 所見 3 — 既存テスト 23 node の期待値が変更され、dataclass equality も非互換

**重要度: must-fix**

依頼は「既存 node の期待値が 1 つでも変更されていたら blocker」と明記している。差分では既存 23 node に新 field の期待値が追加されている。

| 既存 node | 現在行 | 変更 |
|---|---:|---|
| `test_colliding_untracked_target_is_rejected` | 1292 | `(True, False)` 追加 |
| `test_noncolliding_untracked_path_is_allowed` | 1306 | `(True, False)` |
| `test_foreign_handoff_is_rejected` | 1374 | `(True, False)` |
| `test_common_lock_timeout_is_retryable` | 2056 | `(False, True)` |
| `test_provenance_gate_nonzero_is_release_safe` | 2159 | `(True, False)` |
| `test_post_provenance_reacquire_rejects_control_directory_replacement` | 2413 | `(False, False)` |
| `test_waited_initial_lock_rejects_stale_main` | 2627 | `(True, False)` |
| `test_provenance_removed_during_execution_is_retryable` | 2704 | `(False, True)` |
| `test_receipt_each_bound_case` | 2776-2792 | bool 期待値と列挙構造を変更 |
| `test_executed_bytes_mismatch_is_release_safe` | 2813-2819 | bool 期待値追加 |
| `test_provenance_subprocess_exception_is_retryable` | 2947-2953 | bool 期待値追加 |
| `test_zero_fragment_success` | 3588-3600 | `LandResult` equality 2 箇所変更 |
| `test_zero_fragment_missing_layout` | 3619 | bool 期待値追加 |
| `test_candidate_fold_plan` | 3640 | bool 期待値追加 |
| `test_finalize_failure` | 3842 | bool 期待値追加 |
| `test_n35_supervised_path` | 4198 | bool 期待値追加 |
| `test_fold_failure_rolls_back` | 4223 | bool 期待値追加 |
| `test_rollback_failure` | 4578 | bool 期待値追加 |
| `test_active_recovery` | 4834 | bool 期待値追加 |
| `test_shape_b_finalizes` | 4868,4894 | bool 期待値 2 箇所追加 |
| `test_shape_b_origin_other` | 5030 | bool 期待値追加 |
| `test_not_landed` | 5134 | bool 期待値追加 |
| `test_partial_mutation` | 5156 | bool 期待値追加 |

既存 rc、status、reason の反転、緩和、skip、削除は見つからなかった。しかし `LandResult` に通常の比較対象 field を追加したため、`test_zero_fragment_success` の既存 dataclass equality は変更しない限り失敗する。これはテストだけでなく外部 Python caller の equality semantics も変える。

互換性を必要とするなら新 field を `field(default=False, compare=False)` とし、既存 node は元に戻し、新しい分類の検証は新規 node へ分離すべきである。

**成果物への影響:** 既存受入テスト集合が赤になり、wave の land と certified 完了を阻止する。外部 caller が `LandResult` equality を分岐に使う場合は受理集合も変わる。

## F1 追跡 — 実際の perf-optional 起動形では正常 land 後に解放される

**判定: この攻撃は正常成功経路では成立しなかった**

実 script は `/work/1/SFC/tanab/dev-wave-jobs/2026-08-16_perf-optional/unattended_land.sh`。

- `:15` で必要な環境を export。
- `:46` で waiter に lease directory を渡す。
- `:69-76` で `$MAINWT/tools/dev_wave_land.py` を直接 CLI 起動。
- `:79-82` で land の rc=0 を受け、そのまま exit。

したがって land 呼び出しは `tools/dev_wave_land.py:3183-3264` の `main()` を通る。`IZANAGI_WAVE_LEASE_DIR` も script の環境に存在する。

成功した `LandResult` は `tools/dev_wave_land.py:2695-2703` で `release_safe=True`。`main()` は JSON を stdout に flush した後、`tools/dev_wave_land.py:3237-3247` で lease directory を読み、tested main SHA を添えて `release()` を呼ぶ。

実事故の receipt-2 と handoff の lease payload は holder と tested main SHA が一致しているため、この差分が当時の launch shape に入っていれば guarded release は成功する。

ただし所見 1 の `rc=21` 経路が残るため、「land 到達後の残留を一般に根治した」とまでは言えない。

**成果物への影響:** 正常 land 成功時は後続 6 wave が TTL まで待つ事象を避けられるが、certified の値や受理集合自体は変えない。

## F2 追跡 — 最初の `rc=29` では解放するが、loop は停止しない

**重要度: should-fix**

実 loop は次の二段構成である。

- `/work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/land2-loop.sh:18-31`
- `/work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/run-land2.sh:4,7-17`

`run-land2.sh` は `IZANAGI_WAVE_LEASE_DIR` を export し、wave worktree 内の `tools/dev_wave_land.py` を起動する。

この差分がその worktree に存在すると仮定すれば、provenance checker の決定的 nonzero は `tools/dev_wave_land.py:1998-2003` で `release_safe=True` となり、1 回目の `rc=29` で lease は解放される。

しかし `land2-loop.sh:26-31` は rc=21/29 を 5 秒後に再実行し、lease を claim し直さない。したがって 2 回目以降は lease 無しで provenance を走らせる。

具体的な害は次のとおり。

- 次の holder と同時に 38〜61 秒級の全履歴 provenance を走らせる。
- 次の holder の receipt や main snapshot を古くしやすい。
- CPU、I/O、dispatch slot を消費し、別 wave の acceptance を遅らせる。
- release 自体は holder mismatch により他 wave の lease を消さない。

R-E は明示的に scope 外であり、今回得た資料だけでは must-fix への格上げ根拠まではない。ただし「F2 を閉じた」ではなく、「F2 の lease 占有だけを最初の失敗で止める」が正確である。

最小追加案は、rc=21/29 後に lease を解放した場合は loop を終了するか、再試行前に fresh claim と fresh receipt を必須にすること。

**成果物への影響:** certified の判定規則は変わらないが、後続 wave の完了時刻、receipt の鮮度、レポートと台帳に入る採用 wave が競合順序によって変わり得る。

## 全 `_Reject` 送出点の分類

合計 104 箇所を静的に列挙した。「既定」は直接には `(False, False)` だが、上位 wrapper で再分類されるものを併記する。

| 関数 | 行 | 宣言 |
|---|---|---|
| `_bytes_sha256` | 277 | 既定 |
| `_verify_*` 初期入力 | 296,305 | 既定 |
| `_require_git` | 394 | 既定 |
| `_open_dir` | 425,428 | 既定 |
| `_openat_dir` | 442,445 | 既定 |
| `_read_regular_at` | 465,469,479,483 | 既定 |
| `_acceptance_rejected` | 501 | 既定 |
| `_canonical_absolute` | 729,732,736,738 | 既定 |
| `_parse_gitdir_file` | 745,753 | 既定 |
| `_validate_admin_binding` | 773,776,791,793,799,804 | 既定 |
| `_verify_repository` | 823,834,841,844,847,855 | 既定 |
| SHA decode | 877,885,887 | 既定 |
| symbolic HEAD | 912,920 | 既定 |
| heads 検証 | 939,942,947,949 | 既定 |
| history modifiers | 963,964,970 | 既定 |
| effective config | 988,993 | 既定 |
| handoff snapshot | 1019,1033,1037 | 既定 |
| worktree snapshot | 1088,1095,1122,1130 | 既定 |
| status records | 1162 | 既定 |
| main clean | 1175,1184,1202 | 既定 |
| main tracked/index dirt | 1218 | 既定 |
| wave clean | 1223 | 既定 |
| NUL records | 1230 | 既定 |
| target paths | 1275 | 既定 |
| ignored ancestor | 1302,1315 | 既定 |
| target collision | 1337,1349 | 既定 |
| ancestry | 1406 | 既定 |
| audit verification | 1432,1434,1442,1444 | 既定 |
| gitlink map | 1455,1462,1466,1469 | 既定 |
| normal entries | 1481,1488,1492,1494 | 既定 |
| gitlink path | 1504 | 既定 |
| main dirt check | 1583 | 既定 |
| land-lock binding | 1647,1659 | 既定 |
| `_locked_preflight` wrapper | 1750 | `release_safe=(active_plan is None)`、retry を伝播 |
| stale main | 1759 | `release_safe=True` |
| `_open_lock` | 1799,1802 | 既定 |
| provenance checker binding | 1865,1870,1876 | 既定 |
| audit provenance 内部 | 1923,1934 | 既定、内部で捕捉 |
| audit timeout/例外 | 1950,1955,1964 | `retryable_while_holding=True` |
| receipt provenance 内部 | 1980,1986,1994 | 既定、内部で捕捉 |
| deterministic provenance failure | 1999 | `release_safe=True` |
| provenance timeout/例外 | 2008,2013,2019 | `retryable_while_holding=True` |
| post-provenance control snapshot | 2795 | **既定のまま。問題箇所** |
| provenance 再試行条件 | 2811,2818,2834 | `retryable_while_holding=True` |
| late quiescent checks | 3089 | 既定だが outer classifier が `quiescent_rejection` を反映 |

低層の既定送出点の大半は、`_locked_preflight:1750`、provenance wrapper、または `land()` outer catch で最終分類される。引数忘れとして実害が成立したのは `:2795` である。

## `LandResult` 構築点と `release()` caller

`LandResult` は production に 27 構築点ある。

- retryable を明示: `1722,2526,2578,2590,2714,2864,2898,2919,2938`
- release-safe または動的分類を明示: `1759,2472,2508,2600,2695,2992,3018,3043,3059,3102,3146`
- 既定 `(False, False)`: `2395,2624,2647,2655,2687,2947,3034`

すべて新 field には構文上対応する。ただし既定値があるため、構築漏れは compile error にならず、所見 1 のように誤分類を隠す。

`wave_land_window.release()` は `tools/wave_land_window.py:784-788` で末尾に optional parameter を追加した形である。既存 CLI caller は `:969` で従来どおり 2 位置引数を渡しており、repo 内に既存の第 3 位置引数 caller はない。したがって signature 変更による既存 caller 破壊は成立しなかった。

holder mismatch と expected-main mismatch は `tools/wave_land_window.py:808-821` で非破壊的に `not-owner` を返す。他 holder の lease を消す経路は見つからなかった。

**成果物への影響:** signature 自体による既存受理集合や台帳参照の変化はない。

## テスト品質、状態汚染、plain runner

新規 test は実質的な動作を固定しており、恒真 assertion は見つからなかった。

- success は実際の claim、land、release を通す。
- provenance failure、timeout、receipt TOCTOU は対応する seam を発火させる。
- window release test は main SHA guard の実動作を検証する。
- hash、時刻、pid、固定一時 path を期待値へ焼き込んでいない。

状態復元も確認できる。

- lease 環境: `orchestrator/tests/test_dev_wave_land.py:346-356`
- release patch: `:360-366`
- cwd、環境、stdio: `:388-395`
- cwd helper: `:71-77`

親の焦点走で落ちた `test_exploration_external_root_keeps_wave_clean` は `:5736` にある既存 node で、新規 test より名前順で先に実行される。さらに親資料では exact-node 単独実行でも失敗している。新規 test が先に環境や cwd を汚染したという因果は成立しない。

plain runner についても、新しい `test_dev_wave_land.py` の node は引数なしで、同 file の自走 harness `:6180-6194` に適合する。`test_wave_land_window.py` の新規 node は `tmp_path` / `capsys` を使うが、この file は pytest-only allowlist に載っており、`test_plain_runner_coverage.py:60-86` の契約に抵触しない。

不足しているのは所見 2 の 64 KiB 境界 test である。

**成果物への影響:** 新規 test の状態汚染や plain-runner 不適合によって受入集合が変わる攻撃は成立しなかった。一方、境界退行は受入全走でも捕捉されない。

## stderr 1 行では release の機械化を事後測定できない

**重要度: should-fix**

`tools/dev_wave_land.py:3260` の stderr は、その invocation を保存していれば release の成否を確認できる。しかし次は分からない。

- claim されたのに release 行が出なかったのか。
- process が途中終了したのか。
- stderr が保存されなかったのか。
- TTL reclaim だったのか。
- holder mismatch だったのか。
- release 後に同じ wave が再 claim したのか。

さらに `/work/1/SFC/tanab/dev-wave-jobs/wave-t1142-oracle-n-pilot/run-land2.sh:17` は stdout と stderr を同じ `land2.log` にまとめ、各試行で上書きする。1 回目の `released` 証跡は2回目で失われる。

最小追加案は、lease directory 内に best-effort の bounded event log を置くこと。少なくとも claim、auto/manual release、TTL/stale reclaim を記録し、timestamp、wave、holder digest、main SHA、state、reason、source を含める。release event だけでは「release が起きなかった」を検出できないため claim event も必要である。これは gating には使わない。

**成果物への影響:** 現状では F1 再発件数や lease 滞留時間を台帳・レポートへ正確に帰属できず、改善率や再発ゼロという値を証明できない。

## stdout/stderr 結合 runner の互換性

歴史的 job には `land-result.json 2>&1` のように両 stream を結合する script がある。新しい stderr 行が出ると、ファイル全体は単一 JSON ではなくなる。

ただし確認できた該当例は現在必須の acceptance 引数を欠く旧 launch shape で、現行 CLI に対する有効 caller とは言えなかった。F1/F2 の実 script は結合先をログとして扱っており、単一 JSON として parse していない。

したがって現時点で current-valid consumer の破壊までは成立しなかった。運用文書には「機械可読 JSON は stdout のみを保存し、stderr を混ぜない」を明記すべきである。

**成果物への影響:** 現在確認できた有効な certified/report/ledger consumer の値や参照が変わる証拠はない。

## worklog に書いてよい主張、書いてはいけない主張

| 区分 | 主張 |
|---|---|
| 書いてよい | F1 は実在した単発事故で、perf-optional は land rc=0 後に release せず TTL まで保持した |
| 書いてよい | 実際の perf-optional launch shape は `main()` を通り、lease dir 環境変数も存在した |
| 書いてよい | 現差分は、分類済み結果について stdout flush 後に tested-main guard 付き release を試みる |
| 書いてよい | 決定的 provenance rc=29 の最初の試行では lease を解放する |
| 書いてよい | F3 の訂正済み基準値は 20 pair、median 276.5 秒、max 2037 秒。ただし lease lifetime ではない |
| 書いてよい | F4 の変更前事実と、「CLI epilogue に release attempt を追加した」という狭い記述 |
| 書いてよい | F5 は既知の上限が発火した歴史的事実であり、今回の効果測定ではない |
| 書いてよい | O は合計 43 試行、内訳 31+12、各 land 約38〜61秒。今回止めるのは最初の失敗後の lease 占有 |
| 書いてはいけない | 「land 到達後の lease 残留を根治した」 |
| 書いてはいけない | 「F2 の再試行 loop、計算浪費、競合を解消した」 |
| 書いてはいけない | 308秒、4827秒を lease lifetime として扱うこと |
| 書いてはいけない | 「lease 時間の80%以上が idle」 |
| 書いてはいけない | 6 wave、11〜50秒を定常的改善量として一般化すること |
| 書いてはいけない | event log 無しに再発率、平均待ち時間、改善率を主張すること |
| 書いてはいけない | L の argv/preflight zero-test hole を閉じたという主張 |
| 書いてはいけない | F57、ff-only、rc=16、全履歴 provenance 負荷を解決したという主張 |
| 書いてはいけない | 43 回の land 再試行そのものを削減したという主張 |
| 書いてはいけない | certified の受理集合や値を改善・拡張したという主張 |

## 最終分類

### must-fix

- provenance 後 control snapshot 変更の `rc=21` を release-safe に分類できていない。
- 追加 JSON field による 64 KiB 境界退行。
- 既存 23 test node の期待値変更と、`LandResult` equality の非互換。

### should-fix

- rc=21/29 後の外側 loop を停止するか、再試行前に fresh claim / receipt を必須化する。
- claim/release/reclaim の bounded event log を追加し、F1 再発を測定可能にする。
- stdout と stderr を結合しない caller 契約を運用文書へ明記する。

### nit

- 現在確認できた有効 caller では `release()` の末尾引数追加による位置引数破壊はない。
- 新規 test の恒真化、揮発値固定、環境・cwd・module pin 汚染、plain-runner 違反は成立しなかった。
- 既存 rc、status、reason の反転、緩和、skip、削除は見つからなかった。