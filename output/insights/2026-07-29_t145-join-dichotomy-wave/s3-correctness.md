NO-GOです。指定6ファイルはすべて全文読了しました。以下は静的監査だけで、pytest・mutation は実走しておらず、緑は主張しません。編集もしていません。

## real

### R1 — BLOCKER: wrapper は production にない wakeup を供給する

production の停止経路は次です。

```text
shutdown Event set
  → 実 select の有限 poll が戻る
  → loop predicate 再評価
  → thread 終了
```

production の `shutdown()` は Event を set するだけで、selector を直接起こしません（[daemon.py:1613](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1613)、[daemon.py:1615](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1615)、[daemon.py:1643](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1643)）。

一方、plan は次回 `select` を test gate 内に止め、shutdown 後に test が release します（[s2-plan.md:30](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:30)、[s2-plan.md:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:38)）。これは predicate は検査しても、実 poll が shutdown を有限時間で再観測させる契約を検査しません。

反例は `select(..., 0.25)` の timeout を `10**9` にする変異です。

- wrapper が release 後に空 readiness を合成すれば、production なら停止しない実装を test が救済して偽緑にする。
- 実 `select` へ委譲すれば、plan の無期限 `join()` が hang する。
- plan は `None` だけを拒否し、有限値の増減を判定しないため、この反例を分類できません（[s2-plan.md:28](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:28)）。

現行 `join(120)` はこの巨大 timeout を赤にするため、「製品 daemon の受理集合を変えない」という brief とも矛盾します（[s1-brief.md:10](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s1-brief.md:10)）。

Must-fix: 許容 poll 上限を明示して引数を構造的に pin するか、production に実 wakeup 経路を入れる裁定が必要です。`select_fn` 注入 seam だけでは mock の局所化には効いても、実 wakeup 契約は追加されません。

成果物影響: 巨大な有限 poll を持つ commit を mutation/受入が通したと誤記するか、受入・試行記録が無期限に生成されません。

### R2 — BLOCKER: 確定退行も「scheduler starvation」と同じ hang に落ちる

plan の「`loop_parked` または `serve_finished`」待ちと無期限 `join()` は、どちらも上限がありません（[s2-plan.md:32](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:32)、[s2-plan.md:40](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:40)）。

具体的反例として、[daemon.py:1638](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1638) の `conn.shutdown()` 直後に `threading.Event().wait()` を入れると、

1. client は write-half close を観測して roundtrip を完了する。
2. run も terminal になる。
3. serve thread は次回 `select` に到達せず、終了もしない。
4. main は shutdown を呼ぶ前の `loop_parked or serve_finished` 待ちで永久停止する。

現行テストなら `shutdown()` 後の `join(120)` と `is_alive()` で赤になります（[test_dev_waves_integration.py:1223](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1223)）。したがって、plan の「hang は thread が再 scheduling されない場合だけ」という分類は反証されます（[s2-plan.md:56](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:56)）。

また `daemon=True` でも pytest の main thread 自身が無期限 join していれば全走は終わりません。これは T-137 が守った「daemon thread の退行を赤にし、全走 hang にしない」境界を実質的に失います（[test_dev_waves_integration.py:1203](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1203)）。

受入に使う `run_tests.py` は pytest を timeout なしの `subprocess.call` で待ちます（[run_tests.py:714](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/run_tests.py:714)）。mutation だけ外部 ceiling を付けても受入は閉じません。

Must-fix: この pre-select stall を事前登録反例に加え、少なくとも受入 node を kill 可能な subprocess 境界と外部 ceiling に置く必要があります。「確定停止退行は assertion red」という brief を維持するなら、production 観測 seam または wakeup 機構まで scope 拡大が必要です。

成果物影響: 退行時に FAILED node、task-run、受入レポートのいずれも確定せず、repository 全走を巻き添えにします。

### R3 — must-fix: event/field が実際の観測点と一致しない

- `roundtrip_selected` は listening socket が ready だった観測です。実際の accept・receive・dispatch・send はその後です（[daemon.py:1623](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1623)）。roundtrip 完了ではありません。
- `loop_parked` は shutdown 前に評価された predicate の後で `select` に入った観測です。shutdown 後の predicate 再評価ではありません。
- 「post-release select 1回」は、呼出し自体は pre-release に始まるため二義的です（[s2-plan.md:30](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:30)、[s2-plan.md:42](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:42)）。
- `serve_finished` は正常 return と例外終了を区別しません。

Must-fix: bool 群ではなく、少なくとも `listener_ready_returned → exchange_completed → parked_select_entered → shutdown_event_set → parked_select_released → serve_returned/serve_raised` の順序付き状態を持たせ、sentinel は専用例外型と専用失敗署名に分けるべきです。直接観測していない predicate 再評価を成果物で実証済みと書いてはいけません。

成果物影響: mutation の赤を shutdown predicate の検出力へ誤帰属し、実際には readiness、test release、または別の正常 return を測った台帳になります。

### R4 — must-fix: process-wide patch と失敗時 cleanup が閉じていない

`mock.patch.object(daemon_mod.select, "select", ...)` は Supervisor 単体でなく process-wide です。xdist meta-test が保証するのは node 間の group 一致だけで、同一 node 内の thread や残留 thread からの隔離ではありません（[test_dev_waves_isolation_contract.py:102](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_isolation_contract.py:102)）。

さらに、exchange・status・assert のどれかが失敗した時に、必ず `release_loop`、best-effort shutdown、thread 終了確認を行う外側 `finally` が plan にありません。park 中に主例外が出れば、patch を復元しつつ daemon thread と lease/socket を残すか、patch context 自体を閉じられません。[s2-plan.md:134](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:134) の「thread 終了まで patch を保持」は願望で、失敗経路の機構がありません。

Must-fix: primary error を保存する外側 `try/finally`、gate release、shutdown、専用 sentinel による回収、終了不能時の subprocess containment を plan v2 に逐語化してください。これを局所的に閉じられなければ、`SupervisorDependencies.select_fn` seam を production scope の裁定候補に戻すべきです。

成果物影響: 後続 node の socket/lease/select を汚染し、無関係な FAILED node や全走 hang を T-145 差分へ誤帰属します。

### R5 — must-fix: T145-M1〜M5 の事前登録は現状成立しない

| ID | 静的判定 |
|---|---|
| M1 | `conn.shutdown()` anchor は一意。ただし唯一の変更前 SURVIVE→変更後 KILL である一方、検出対象は「shutdown で止まる」ではなく「一要求後も次 iteration へ進む」です。T-145 の純増証拠には未裁定。 |
| M2 | 自然な anchor `_shutdown.set()` は [daemon.py:1622](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1622) と [daemon.py:1644](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/daemon.py:1644) の2箇所。plan の「anchor 一意」は、old/new bytes が未提示の現状では成立しません。旧新とも赤で、Event 欠落と sentinel の二理由にもなります。 |
| M3 | anchor は一意。旧新とも赤で、純増検出力ではなく failure latency/診断の変更です。専用 sentinel 署名なら preservation pin にはできます。 |
| M4 | anchor は一意。ただし wrapper が `None` を実 roundtrip 前に例外化するため、production の shutdown 挙動ではなく mock の引数 oracle による構造赤です。巨大な有限 timeout を見逃します。 |
| M5 | anchor は一意。production mutation ではなく test fixture 自身の `daemon=True→False` 変異です。T-137 cleanup invariant の構造 pin であり、製品停止検出力ではありません。 |

加えて、plan は「rc、FAILED node、skip 数を記録する」としか書かず、各変異の期待 FAILED node、exact error、SKIPPED node/reason、外部 timeout の期待を事前登録していません（[s2-plan.md:84](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/output/insights/2026-07-29_t145-join-dichotomy-wave/s2-plan.md:84)）。

対象 node は capability 不足なら mutation 到達前に skip します（[test_dev_waves_integration.py:1191](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1191)）。その場合、全 M1〜M5 は `SURVIVED` でなく `NOT RUN` とし、検出力証拠に数えてはいけません。`-rf` だけでは skip reason の署名も採れません。

T-136 preservation も、PM1/PM3/PM4 の実 anchor は residual・timeout・log-limit の別行です（[worker.py:552](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/worker.py:552)、[worker.py:555](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/worker.py:555)、[worker.py:557](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/tools/dev_waves/worker.py:557)）。`worker.py:552` と `daemon.py:1011` の二リンクだけでは4本の置換 spec になっていません。

Must-fix: final bytes に対する exact old/new、置換数1、旧新それぞれの normalized FAILED node・error・skip・timeout期待を登録し、M1〜M5を「純増」「preservation」「diagnostic pin」に分け直してください。

成果物影響: 無注入、別箇所変異、capability skip、別理由の赤を KILL と誤記し、検出力を持たない commit を certified 参照にできます。

## refuted

- 親の「T-136 は当該箇所を30→120へ広げただけ」という局所観測は正しいです。現行も [test_dev_waves_integration.py:1224](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1224) の形です。ただし、そこから「test-only release で shutdown 契約全体を決定化できる」への一般化は R1/R2 で反証されます。
- M3 の sentinel が thread を終了させること自体は、`serve_failures == []` を最後まで保持する限り直ちに偽緑ではありません。thread 非生存は通っても sentinel 捕捉で node は赤になります。ただし専用署名が必要です。
- test-only baseline で schema、request limits、state/reason、side-effect の production bytes が直接変わるという懸念は静的には refuted です。T-136 の preservation controls は必要ですが、非実走なので維持済みとは数えられません。
- long-path assertion、独立 capability probe、`daemon=True`、serve 例外回収、xdist marker を残す方針自体は T-137/T-138 を弱めません。弱化点はそれらの削除ではなく、R2/R4 の無期限待ちと cleanup 境界です。

## 裁定待ち

1. M1 の multi-request 契約を T-145 に含めるか。`serve_forever` という名称と現行 loop は支持材料ですが、brief は shutdown 停止検査を scope としています。採るなら brief に「一要求後も shutdown まで live loop を維持」を受理条件として追加し、受理集合縮小を明示する必要があります。採らないなら M1 を純増証拠から外します。

2. shutdown の許容契約を「exact 0.25」「明示上限以下」「任意の有限 poll」「wakeup-driven」のどれにするか。これは test-only の実装詳細ではなく製品受理集合の裁定です。

3. process-wide monkeypatch、per-instance `select_fn` seam、実 wakeup channel、subprocess-contained test のどれを採るか。`select_fn` seam や wakeup は未実装であり、production 0 byte と数えてはいけません。

4. P2 の node 分割却下は未確定です。単一 node では capability skip が shutdown mutation 全件も消します。seam を持つ決定的 contract nodeと real long-path nodeを分ける案は、cleanup 設計と併せて再裁定すべきです。

## 総括

- **NO-GO**
- **段5前 blocker:** test release が production wakeup を代替する問題、pre-select stall の無期限 hang、失敗時 cleanup、mutation の anchor/署名/単一理由不成立。
- **plan v2 必須修正:** shutdown の数値・wakeup契約を裁定し、順序付き observation state と専用 sentinel を定義し、外部 containment を受入にも付け、M1〜M5を exact anchor・FAILED/skip/timeout署名付きで再登録する。
- production seam または wakeup が必要との裁定になった場合は、test-only 実装済みとは扱わず、scope 拡大後に段5へ進むべきです。