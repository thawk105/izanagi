静的レビュー結論は **NO-GO** です。テスト・変異は一切実行しておらず、以下はコード上の評価です。

### 1. [must-fix] deadline 待機中に pin mask が外れても α として誤受理できる

**場所** [env_attestation.py:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:434)、[env_attestation.py:446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:446)、[test_env_attestation.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:156)

**なぜ危険か** `set_affinity` と exact mask 検査の後に最大 50 ms の待機がある。その間に別 task が対象 thread の affinity を広げても、pre/post の瞬間だけ target CPU 上なら両 processor 検査を通る。read 中の移動も排除できず、exact pin でない snapshot が `rotating-min/k5` として返る。fake の `sleep()` は時刻しか変えないため、この経路を扱っていない。

**成果物影響** protocol 外の profile に α method が付き、値が帯内なら certified receipt の受理集合を拡大する。

**提案** 現在の exact mask 検査を `_wait_until_ns()` の直後、pre processor の直前へ移す。`sleep` 中に affinity を広げる一方、processor は target を返す fake 負例を追加する。read 全区間の境界確認まで要求するなら post 側でも mask を再取得する。

### 2. [must-fix] `finally` の復元例外が本来の失敗を上書きする

**場所** [env_attestation.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:425)、[env_attestation.py:488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:488)、[test_env_attestation.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:447)、[test_env_attestation.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:485)

**なぜ危険か** pin/read/pre/post の例外が active な状態で、復元 set・復元後 get・exact 比較のいずれかが raise すると、Python は元例外を復元例外で置換する。例えば affinity 操作が権限不足なら singleton pin と元集合への復元の両方が失敗し、「pin 失敗」が「復元設定失敗」になる。現行テストは pin/read 失敗と復元失敗を別々にしか起こさない。

**成果物影響** [run_probe.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/tools/pegasus/run_probe.py:61) が `str(exc)` を失敗成果物へ保存するため、probe report の原因が誤記され、変異の単一理由性も崩れる。受理自体は fail-closed のまま。

**提案** `finally` 内では復元結果を収集するだけにし、primary failure と restore failure を外側で統合した `AttestationError` にする。`pin+restore`、`read+restore` の同時失敗テストで primary と restore の双方が残ることを固定する。

### 3. [must-fix] M02/M10 は別の固定 K gate に mask される

**場所** [s4-adjudication.md:106](/work/1/SFC/tanab/dev-wave-jobs/t419-alpha-wiring/s4-adjudication.md:106)、[env_attestation.py:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:330)、[env_attestation.py:354](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:354)、[test_env_attestation.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:406)

**なぜ危険か**

- M02 で K を 1 にすると、reader-outlier test は一読みに到達せず `count < 2` で先に拒否される。identity test は有効だが、「単読み退化を検出した」という帰属にはならない。
- M10 で target 数だけを affinity 数へ切り下げると、2 read 後に reducer の `len(reads) != 5` が拒否する。K 未満テストは期待メッセージ不一致で赤くなるが、入力は依然 fail-closed で profile に到達しない。F113 型の偽 kill である。

**成果物影響** 段 6 の変異 matrix が、単読み・K 切り下げを検出できていないのに kill と記録される。

**提案** M02 は K/method を維持したまま「最初の snapshot を残り4回へ再利用する cache mutant」へ再照準する。M10 は不足 CPU を繰り返して5読みに到達する具体 mutantにするか、selector と reducer の両層変異として事前登録する。

### 4. [must-fix] M08 の CPU-set 負例は検査削除後も `KeyError` で落ちる

**場所** [env_attestation.py:364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:364)、[env_attestation.py:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/campaign/env_attestation.py:373)、[test_env_attestation.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:392)、[test_env_attestation.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:505)

**なぜ危険か** fixture は CPU 4 を削る。CPU集合 equality を消すと、直後の `mhz_by_cpu[4]` が `KeyError` を投げる。テスト node は赤くなるが、drift 入力は受理されていない。identity 側は検査削除時に profile へ到達するため、同じ M08 内でも帰属が異なる。

**成果物影響** M08 の CPU-set kill を記録すると、受理集合が変化していない偽の防壁証拠が残る。

**提案** 欠落 CPU ではなく余分な CPU 99 を追加する fixture にする。集合検査を消せば余分な値が reducer に無視され、profile が実際に返る。M08-set と M08-identity は別変異へ分割する。

### 5. [must-fix] M03 の reader-outlier fixture が実際の pin target と結び付いていない

**場所** [test_env_attestation.py:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:136)、[test_env_attestation.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:325)

**なぜ危険か** snapshots は事前計算した `[0,2,4,6,8]` に従って高値 CPU を移す。実装を「全 read を CPU 0 へ pin」に壊しても、fake は高値を 0→2→4→6→8 と移し続け、min 結果と verdict は正常のままになる。赤くなるのは `requested_targets` の列比較だけで、「reader-outlier により kill」という登録は成立しない。

**成果物影響** 変異 matrix が rotation の構造検査を observer-effect 除去の意味検査として過大報告する。

**提案** fake に独立した actual-processor 状態を持たせ、snapshot の高値 CPU を実際の fake affinity/processor から生成する。target 列検査と outlier 除去の期待は別テストへ分離する。

### 6. [must-fix] 変異登録の単一 anchor と期待 test が未確定

**場所** [s4-adjudication.md:110](/work/1/SFC/tanab/dev-wave-jobs/t419-alpha-wiring/s4-adjudication.md:110)、[s4-adjudication.md:112](/work/1/SFC/tanab/dev-wave-jobs/t419-alpha-wiring/s4-adjudication.md:112)、[s4-adjudication.md:115](/work/1/SFC/tanab/dev-wave-jobs/t419-alpha-wiring/s4-adjudication.md:115)、[test_env_attestation.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-alpha-wiring/orchestrator/tests/test_env_attestation.py:309)

**なぜ危険か**

- M06 は pre と post の2箇所、M08 は CPU集合と identity の2箇所であり、「その1箇所」の変異になっていない。
- M11 の γ 判定は実際には no-touch の `execution_guard.py` comparator にあり、env_attestation の新規領域には expected band がないため一意な anchor がない。
- M12 が期待する quiet fixture は5ベクトルが完全一致している。完全一致を要求する過剰拒否変異でも、この test は通過する。

**成果物影響** harness の注入実在・期待 node 完全一致を確定できず、段 6 の mutation report を監査済み成果物にできない。

**提案** M06-pre/post、M08-set/identity を分割する。M11 は comparator を変異対象にするか、producer が1 extreme sampleを落とす具体的変異へ裁定し直す。M12 は全値が帯内の小さな read 間 jitter を quiet fixture に入れるか、変動を持つ reducer 正例へ期待 node を明示的に再登録する。

## M01–M12 静的帰属表

| ID | 静的判定 | 単一理由性・再照準 |
|---|---|---|
| M01 | 成立見込み | method identity のみ。ただし identity test に加え fixture の method assert も赤候補として登録が必要。 |
| M02 | 部分成立 | identity は有効。取得退化は `count < 2` に mask。cache mutant へ再照準。 |
| M03 | 部分成立 | distinct target 列は検出するが、reader-outlier の意味検査は検出しない。 |
| M04 | 成立見込み | `max` は reader-outlier、非対称性、reducer minimum の各正例を同じ集約理由で壊す。期待 node 全件の列挙が必要。 |
| M05 | 成立見込み | noop set 時、fake の pre/post は target を返すため mask branch だけが拒否する。 |
| M06 | 要分割 | pre 削除・post 削除は各 parameter 負例で独立に検出可能だが、1変異としては2 anchor。 |
| M07 | 成立見込み | profile を返す具体的 fallback mutantなら、restore は成功し runtime/direct parser spy と拒否期待が単一経路になる。 |
| M08 | 不成立/部分成立 | CPU-set は `KeyError` の偽 kill。identity は clean。2変異へ分割し、CPU-set は余分な CPU fixture へ。 |
| M09 | 成立見込み | `finally` 全削除なら restore 負例と TSC順序が同じ復元欠落理由で検出する。復元を assert する他 node も期待集合へ必要。 |
| M10 | 不成立 | reducer の固定5 read gate が後段で拒否する。profile 到達 mutantまたは両層変異へ再照準。 |
| M11 | 判定不能 | env新規領域に一意な γ anchor がない。comparator変異なら persistent 以外の単一外れ値 test も赤候補。 |
| M12 | 部分成立 | quiet integration は完全一致なので検出不能。変動する reducer 正例なら検出可能だが、期待 test の再登録が必要。 |

静的に成立している点は、default runtime に cache・fallback・`continue`・直接 parser の別経路がなく、K=5 の distinct target と reducer の exact K が結線されていること、read-start 間隔と最小 horizon が pairwise deadline で保証され、lateness 拒否がないこと、TSC が成功時の復元後にしか呼ばれないことです。

`/proc/thread-self/stat` は field 3 を index 0 として processor field 39 を `39-3=36` で取っており正しいです。`rfind(")")` も comm 内の空白・`)` を扱えます。現行テストが comm 内 `)` を含まない点だけは非 blocking の coverage nit です。

## 総括

最重要所見は、**待機中に affinity mask が変わっても α method 付き profileを返せる誤受理経路**です。加えて、復元例外による primary failure の消失と、M02/M08/M10を中心とするF113型の偽 killが残っています。

**判定: NO-GO。** affinity 再検査位置、同時失敗の例外保存、変異の再照準・分割・期待 node 修正を行い、その後に親環境でテストと変異を実測する必要があります。