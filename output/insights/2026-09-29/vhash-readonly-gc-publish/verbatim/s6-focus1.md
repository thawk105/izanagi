## 1. 所見ごとの対応表

| 所見 | 判定 | 根拠 file:line |
|---|---|---|
| A1 探索範囲 | **partial** | [ro_gc_publish.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:43) は 2 worker の4構成と 3 worker・1 key・1 read の1構成。3 worker・2 key・2 read は未探索。 |
| A2 bad-raise の到達性 | **partial** | 共通初期状態からの witness になったが、違反には ro 途中の追加 flag が要る。[ro_gc_publish.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:9)、[test_vhash_forwarding_model_rogc.py:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_forwarding_model_rogc.py:87)。 |
| A3 safe 腕の切断なし | **closed** | safe 両腕の切断を検査。[test_vhash_forwarding_model_rogc.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_forwarding_model_rogc.py:64)。 |
| A4 固定履歴 J1 | **closed** | 探索から J1 を除き、直列化可能性は対象外と明記。[ro_gc_publish.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:24)。 |
| A5 raw schema 不一致 | **closed** | driver が `measurement_env` を出し、作図器が最上位値と照合。[vhash_ro_gc_publish.py:339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:339)、[plot_vhash_ro_gc_publish.py:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:147)。 |
| A6 rc=3 の `accepted` | **partial** | 誤読を招く名称は変更。rc=3 の受理自体は親の裁定どおり維持され、認証済みとは別ラベル。[vhash_ro_gc_publish.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:119)、[同:303](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:303)。 |
| A7 旧文言 | **closed** | 72／54 件に更新。[test_condition_meaning_gate.py:3865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_condition_meaning_gate.py:3865)。 |
| B1 旧文言 | **closed** | A7 と同じ修正。[test_condition_meaning_gate.py:3865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_condition_meaning_gate.py:3865)。 |
| B2 固定履歴 J1 | **closed** | A4 と同じ修正。[ro_gc_publish.py:315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:315)。 |
| B3 陰性対照の前進 | **refuted-by-parent** | 裁定理由は妥当。`progress` は active 中の MinRts 変化であり、GC 安全違反でも公開回数でもない。早期 flag 単独の違反 0 を検査。[ro_gc_publish.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:3)、[test_vhash_forwarding_model_rogc.py:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_forwarding_model_rogc.py:125)。 |
| B4 (b) の集計 | **closed** | 条件間の境界年齢差、ro 保持者割合、stock 公開 0／未定義を数表へ出力。[plot_vhash_ro_gc_publish.py:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:78)、[同:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/plotting/plot_vhash_ro_gc_publish.py:266)。 |
| B5 smoke の時間見積り | **refuted-by-parent** | driver の追加要件としない裁定は妥当。build・run 時間は raw に残り、親が概算を記録。ただし本計測の所要は未確定。[vhash_ro_gc_publish.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/campaign/vhash_ro_gc_publish.py:205)、[handoff.md:37](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/handoff.md:37)。 |
| B6 非同居の証拠 | **partial** | 親が照合方法を記録した段階。対象 job の node・時間区間の照合結果は提示資料にない。[handoff.md:40](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/handoff.md:40)。 |
| B7 字面だけの patch test | **partial** | guard と順序の検査は増え、smoke3 で ro 比率・flag 発火を確認。非 ro の実際の write は今回の smoke 数値だけでは直接確認できない。[test_vhash_ro_gc_publish.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_ro_gc_publish.py:140)、[smoke3.json:20527](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/raw/smoke3.json:20527)。 |
| B8 bad-raise の初期 prefix | **partial** | A2 と同じ。条件付き反例であることは明記された。[ro_gc_publish.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:9)。 |

## 2. 親の派生値の照合

[model-big.json:2559](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/model-big.json:2559) を再集計した。**登録された5構成×6腕は全30件 complete**。w3 の safe-flag は154,824状態・切断624・違反0、safe-mainte は502,328・2,496・0、neg-early-flag は562,350・3,180・0。stock は5,980状態・公開0・切断0、bad-clear は違反1,044、bad-raise は違反654で、親の記載と一致する。「全構成」は登録された5構成を指す場合に限り正しい。

bad-raise の49 step witness には ro 途中の `early_store_flag` が2回入る。[ro_gc_publish.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:195) の遷移と、Cicada が `ThreadRtsArray` を begin で書き、flag を `mainte()` で立てる実装（[transaction.cc:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/external/ccbench/cc/cicada/transaction.cc:34)、[同:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/external/ccbench/cc/cicada/transaction.cc:859)）は、親の「早期 flag＋slot 引上げ」の解釈を支える。variant の flag 呼出しは commit 時なので、**slot 引上げ単独の到達反例ではない**。

件数 pin の55→58は追加 define 3件に一致し、deferred 14 は維持。[test_ccbench_spawn_sites.py:3633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_ccbench_spawn_sites.py:3633)。smoke3 raw も rc=0 の報告値と一致し、vlife は公開99回・境界年齢平均12,424.7 µs、4 run の argv に `izanagi_long_kind` はない。[smoke3.json:59111](/work/SFC/tanab/tmp/vhash-ro-gc-publish-2026-09-29/raw/smoke3.json:59111)。

## 3. 新しい所見

- **should-fix — [ro_gc_publish.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/tools/vhash_forwarding_model/ro_gc_publish.py:43):** 「全構成 complete」を元の 3 worker・2 key・2 read 上限全体へ広げると、未探索域を安全確認済みと誤記する。成果物には5構成を列挙し、上限全体を主張するなら残りの構成を探索する。
- **nit — [test_vhash_ro_gc_publish.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ro-gc-publish/orchestrator/tests/test_vhash_ro_gc_publish.py:35):** vlife macro の test は AST 上の文字列と個数を見るため、将来の呼出し先変更では実際の build 引数との対応が崩れうる。成果物の argv が再び不整合になり得るので、build receipt の macro と run argv を突き合わせる検査を加える。今回の smoke3 では不整合は確認されなかった。

修正による受理条件の反転、作図器と driver の schema 不一致、既存期待値の無関係な緩和は差分上確認しなかった。

## 4. GO / NO-GO

**焦点 fix の統合は GO。一次資料の確定は NO-GO。** A1・A2 の結論を上記の範囲に限定し、並行中の焦点走3と、予定された verify・本計測・非同居照合の結果を確認する必要がある。これらを緑と報告する根拠は現時点でない。

## 総括

主要な確定不具合だった safe 腕の空の切断検査、固定履歴 J1、raw schema、旧件数 pin、smoke の build 順序と vlife flag は解消した。bad-raise は**追加の早期 flag を伴う条件付き正例**として扱えば、モデルと Cicada の実装に整合する。