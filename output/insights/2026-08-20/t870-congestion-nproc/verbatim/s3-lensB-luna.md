結論として、`grant_budget()` の今回の判定が `DISPATCH` になることは支持されます。しかし「(e) は受入全走に適用不能」「したがって記録だけで十分」は過剰です。現時点の full-suite × `nproc=4` の実ピークは未取得です。

### 1. reward-hack 回避

判定: 「今すぐ通常 local 実行できない」は支持、「安全な改善案が無い」は未立証です。

- `peak=4 GiB` → 見積り `5 GiB`、上限 `4 GiB` なので恒常的に `DISPATCH` になる構造は正しいです。現在の空き `370 MB` も、最小 local 予算 `1 GiB` を下回ります。`handoff.md:39-63`、`stage2-plan-output.md:128-137`
- ただし full-suite の `nproc=4` peak は未実測で、dispatch 先の peak も台帳に反映されません。したがって「nproc低下で full-suite が収まらない」とまでは証明できません。`stage2-plan-output.md:147-168`
- Steelman 可能な最小案は、operator 明示の一回限り local retry です。peak を一時的に無視しても、ライブ空き容量・予約・lock/atomic write・`MIN_LOCAL_BUDGET_BYTES`・`MemoryMax`・CAP_OOM fallback は維持し、失敗時は台帳を消さない設計なら、検証内容を減らさず実行できます。現在の 370 MB 状態では必ず拒否すべきです。
- ただし台帳には `operation/peak_bytes/recorded_at` しかなく、CAP_OOM sentinel と実ピークの provenance がありません。自動判定は危険で、明示 opt-in または別途 provenance 設計が必要です。`handoff.md:28-35`

よって、今 wave で実装を見送る判断は可能ですが、「改善余地なし」ではなく「安全な一回限り recovery を未実装の課題として残す」が正確です。

### 2. 記録先

判定: 主記録は `output/insights`、失敗型は `docs/failures.md` 候補、次の一手は worklog。`decisions.md` への直接追記はまだ不要です。

- wave 固有の証拠・算術・live call は既定成果物である `output/insights/2026-08-20_t870-congestion-nproc/README.md` に記録するのが第一です。`handoff.md:112-117`
- 「CAP_OOM peak sentinel による tests-full local admission の自己固定」は再利用可能な失敗型なので `docs/failures.md` に昇格候補です。ただし同ファイルは今回の射影外で、既存 entry との重複は未確認です。
- `docs/decisions.md` は観測事実ではなく、「自動回復を採用しない」「明示 opt-in recovery の条件」などの裁定を行った場合だけ新規 decision にするべきです。D612へ混載しないでください。
- worklog には `(h)` などの新項目として、「CAP_OOM sentinel の安全な recovery/provenance と full-suite peak を再検証する」を残すべきです。

### 3. 重複・整合性

判定: 既存 `(e)` とテーマ上の接点はあるが、実質的には別問題です。

重要な射影不整合があります。現物の `docs/worklog.md:3044-3059` は T-870 の次の一手ではなく、`[T-583]`〜`[T-650]` の継承 ID 一覧です。`handoff.md:164-167` の「行番号・折込先は変わり得る」という注意どおり、指定行は古いようです。

現物の T-870 ブロックは `docs/worklog.md:1971-1986` です。

- `(e)` は `IZANAGI_TEST_NPROC=4` の full-suite 適用可能性。
- 新発見は `CAP_OOM` peak ledger が admission を自己固定する失敗構造と、その回復手段。
- `(a)`〜`(c)` の lease timing、`(d)` mutation harness、`(f)` fencing とは重複しません。`docs/worklog.md:1975-1986`
- brief にある `(g)` は `handoff.md:80-85` にありますが、現物の T-870 block には展開されていません。

したがって `(e)` を上書きせず、別の `(h)` または `(e)` の阻害因子として追記するのが整合的です。

### 4. D612 整合性

判定: 自動選択・`is_acceptance` 分岐を拒否する部分は整合していますが、D612を「明示 opt-in recovery も禁止」と読むのは射程超過です。

D612が拒否したのは、既定 timeout の変更と `_is_acceptance_run(args)` による自動分岐です。`docs/decisions.md:24540-24549`。一方、D612自身は明示 opt-in override を採用しています。`docs/decisions.md:24575-24577`

したがって、generic な operator 明示・一回限りの local retry は、`is_acceptance` も queue timeout も変更しない限り、D612の再訪ではありません。逆に「peak が cap なら自動的に無視する」実装は、新たな裁定なしに入れるべきではありません。

### 5. scope 境界

判定: 発見自体は `(e)` の scope 内です。`(d)(f)(g)` への実質的な踏み込みはありません。

対象は `tests-full` の `run_tests.py` → `login_headroom.grant_budget()` と peak ledger であり、brief が定めた対象経路そのものです。`handoff.md:69-85`

ただし、ledger schema の変更や `grant_budget()` の既定挙動変更は mutation harness その他へ波及し得るため、今回行うなら明示 opt-in・既定値不変に限定すべきです。mutation timeout、lease fencing、`dev_wave_land --lease-dir` を同時に扱うのは scope 外です。

## 総括

親の「現在の混雑状態では local 不可」は正しいです。一方、「(e) の改善不能」と「記録だけで完結」は未立証です。現 wave でコード変更を見送る場合も、full-suite peak 未取得と、CAP_OOM sentinel を一回だけ安全に再試行できる recovery gap を明示的な次の一手として残すべきです。pytest は実行していません。