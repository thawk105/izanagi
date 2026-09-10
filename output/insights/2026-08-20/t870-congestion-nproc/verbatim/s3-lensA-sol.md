前提として、pytest・実測の再実行はしていない。以下は射影資料と対象コードの静的検査・机上計算である。handoff の live 呼出し結果は、コードと算術の整合性のみ確認した。

### 1. `CAP_OOM` 時の peak 記録

判定: 支持（ただし、当該ファイルが本当にその経路由来かは不明）

`tools/run_tests.py:1743-1763` では、signal 終了後の `memory.events` が条件を満たした場合、`_safe_remember_peak(..., max(cap, samples.peak_current or 0))` が実際に呼ばれる。したがって親のコード読解は正しい。

ただし、同じファイルの通常終了経路でも `samples.peak_current` を記録する (`tools/run_tests.py:1772-1777`)。peak record 自体には outcome/provenance がなく、`operation`・`peak_bytes`・`recorded_at` だけである (`login_headroom.py:947-974`)。したがって、値が4GiBであることだけから「この record は CAP_OOM 由来」と断定することはできない。

なお、`max_delta`/`oom_delta` という変数名でも、`_read_scope_events()` は raw counter を返しており、実行開始時との差分計算はしていない (`tools/run_tests.py:1447-1456`)。

### 2. peak record の staleness/expiry/decay

判定: 支持

- `_peak_name()` はファイル名を作るだけ (`login_headroom.py:941-944`)。
- `_remember_peak_locked()` は `recorded_at` を保存するが、単純に atomic overwrite する (`login_headroom.py:947-954`)。
- `_recall_peak_locked()` は timestamp の型・範囲を検査するだけで、経過時間比較、expiry、decay、削除を行わない (`login_headroom.py:957-976`)。
- `estimate_for()` と `grant_budget()` は、読んだ peak にそのまま1.25倍の見積もりを適用する (`login_headroom.py:1023-1040`, `1090-1125`)。

`STALE_RECORD_MAX_AGE_S` は予約 record の回収不能時の年齢上限であり (`login_headroom.py:693-735`)、`_collect_live_reservations()` も `.json` だけを走査する (`login_headroom.py:751-777`)。`.peak` record には適用されない。

### 3. 「永久固定で local は二度と成功しない」の反例

判定: 反証（絶対的な一般化に対して）

同じ `tests-full` key、同じ有効な ledger、通常の `grant_budget()` デフォルト値に限れば、親の数理は成立する。

`peak=4GiB` なら、`_estimate_peak_value()` により見積もりは5GiB (`login_headroom.py:1012-1018`)。一方、実運用呼出しは `max_bytes` を渡さず (`tools/run_tests.py:1310-1314`)、既定上限は4GiB (`login_headroom.py:1043-1049`)。したがって `usable <= 4GiB < 5GiB` となり、`login_headroom.py:1117-1125` で dispatch になる。

ただし、以下の反例がある。

- 現行でも partial run は `tests-partial-<digest>` という別 key を使う (`tools/run_tests.py:514-528`)。別 key や `operation=None` なら peak 見積もりを使わない (`login_headroom.py:1097-1110`)。
- `max_bytes` は正整数であれば呼出し側から変更できる (`login_headroom.py:921-928`, `1043-1049`)。5GiB超の上限と十分な空きがあれば local は成立し得る。
- `/run/user/<uid>` 配下の ledger がセッション終了等で消失・再作成された場合、peak recall は `None` になり (`login_headroom.py:481-490`, `957-976`)、空きが十分なら local 判定へ戻る。tmpfs であること自体はコードからは確認できず、自然消失は外部状態である。
- 有効な bounded scope 内では login admission を通らずに実行できる (`tools/run_tests.py:2046-2053`, `2152-2158`)。これは `grant_budget()` が LOCAL になる反例ではないが、「run_tests の local 実行が二度と起きない」という広い主張への反例である。
- `_invalid_reservation_is_reclaimable()` は予約 `.json` の回収だけを行い、peak は消さない (`login_headroom.py:717-777`)。予約回収で `available` は増えるが、既定4GiB上限と5GiB見積もりの不等式は変わらない。

したがって、正確には「自己強化的に再記録され続ける」のではなく、「一度4GiB recordになると、既定の同一 key では local 試行そのものが止まり、内部から自然に低下しない」である。

### 4. `370070616 bytes` を典型的混雑度とみなせるか

判定: 不明（代表値として一般化できない）

値自体は、`grant_budget()` の計算式

`effective_ceiling - admission_bytes - reservations - RESERVE_BYTES`

(`login_headroom.py:1090-1096`) と handoff の数値に整合する。つまり、これは raw free memory ではなく、予約控除後の一時的な admission available である (`handoff.md:50-56`)。

しかし、live 呼出しは1点だけである (`handoff.md:47-57`)。時系列、反復測定、混雑前後の比較、full-suite の別 nproc 測定は、読める資料内には無い。既存記録も targeted 単独走で、memory peak bytes を含まない (`stage2-plan-output.md:139-148`)。

したがって、370MBが異常に低いのか、通常値なのか、高負荷時の一時値なのかは判定できない。「今日の典型的混雑度」という一般化を支持する記録は無い。

### 5. P1「現 evidence は受入全走への (e) 実装を支持しない」

判定: 支持（ただし根拠の表現を限定すべき）

P1 の暫定方向自体は支持できる。受入全走が同じ admission 経路を通ることは確認できる (`tools/run_tests.py:2046-2053`) 一方、nproc=4 の full-suite peak が4GiB以内で CAP_OOM なし、という直接証拠はまだ無い (`stage2-plan-output.md:177-184`, `201-217`)。

ただし、結論は次のように限定すべきである。

> 現時点の evidence では、受入全走へ (e) を実装する十分な根拠がない。

「tests-full は永久に local 実行不能」「370070616 bytes は典型値」「peak record が CAP_OOM 由来と確定」という強い補助主張までは、今回の資料からは支持できない。

## 総括

P1 の不実装方向は正しさの観点から支持する。ただし、理由は「永久固定」や「典型的混雑度」ではなく、full-suite の nproc 変更後の実 peak と route の直接 evidence が不足しているためである。