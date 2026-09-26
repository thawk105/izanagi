## 所見

- **A-01 — must-fix。V28 の「作れない」という結論は強すぎる。** `Version` は GC で鎖から外され、`reuse_version_from_gc_` に入り、後の書き込みで再初期化される。[garbage_collection.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/garbage_collection.cc:82)、[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:268)。YCSB は INSERT/DELETE を生成しないため、親が挙げた abort INSERT の `Tuple` 削除は今回の cell では起きない。[ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/include/ycsb.hh:55)。**影響:** V28 行を実走対象外で確定すると、依頼された検出表を埋められない。**推奨:** status 除外だけの変異を隔離した実走用 patch として作り、異常終了・停止も結果として記録する。

- **A-02 — should。V28 の安全性リスクは実在するが、種類を分ける必要がある。** UPDATE は inflight 版を CAS で公開してから `body_` を代入する。[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:209)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:287)。YCSB の READ は値の正しさを比較しないが、RMW は `val_` をコピーするため、未完成 body は実行挙動や異常終了に影響しうる。[ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/include/ycsb.hh:121)。また GC の watermark は reader の `Version*` を直接保護せず、回収後の別版への再利用を否定できない。[garbage_collection.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/garbage_collection.cc:53)。**影響:** crash・停止・不可解な R を通常の verifier verdict と混同できない。**推奨:** process 異常終了を独立状態とし、V28 の機構検出とは数えない。

- **A-03 — should。V28 の dirty read は trace に必ず orphan として残るわけではない。** R の版番号は読んだ時点に固定されず、commit 時に保持ポインタから再読される。[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:541)。書き手が先に commit すれば正常な commit stamp に置き換わり、orphan は消えうる。abort 版または未 commit 版の番号が producer 不在なら orphan、偶然別の producer と一致すれば見逃し、ポインタ再利用時は別版の番号になりうる。[dsg.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/verifier/dsg.py:752)。同じ key を後で update すれば R 自体が消える。[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:239)。**影響:** V28 の I や N を単独で dirty read の成否に帰属できない。**推奨:** `changed/committed`、orphan、巡回、process 状態を別々に記録する。

- **A-04 — should。V29 の機構変更は成立するが、K の N は変異検出と数えられない。** committed 後の拒否だけを外せば、古い snapshot の writer が CAS 成功後に commit できる。inflight 分岐と CAS 再試行は残る。[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:170)、[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:653)。commit stamp は `++Lsn` なので、この変更だけで同一 key・同一 stamp の W 二本は導けない。[同](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:479)。L0 の無改変 K t4 自体が N・2,443 巡回である。[liveness.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-si-v2/liveness.md)。**影響:** K の V29/V28 の N を検出数へ加えると過大計上する。**推奨:** K は「N、変異への帰属不能」とし、対照との差分も因果証明に使わない。

- **A-05 — should。発火診断は「候補を見た」と「挙動が変わった」を区別すべき。** V29 の `reached` は元の拒否条件が真、`changed` はその条件を経て CAS 成功、`committed` はその取引が成功、で整合する。V28 の `reached` は単に非 committed 版に遭遇した回数では広すぎる。snapshot 条件を満たして実際にその版を選び、元コードなら別版または not found になったときだけ `changed` とする。[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:147)。**影響:** 診断を誤ると「盲点」と「未発生」の分類が崩れる。**推奨:** 両変異とも取引単位の `committed` を成功後に一度だけ加算する。

- **A-06 — nit。v2 framing は有効だが、独立した完全性証人ではない。** C の件数と R/W は同じ `read_set_`・`write_set_` を使い、E は W ループ後に出る。[instr-si-trace-v2.patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/patches/instr-si-trace-v2.patch:4)。parser は件数不一致と E 欠落を検査する。[parse.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/verifier/parse.py:289)。node 検証で abort した取引は emitter に到達しない。[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:482)。**影響:** L0 の framing 0 は検査が効いていない意味ではなく、出た frame の構造が整っていた意味に限る。**推奨:** 欠けた読取りや誤った版番号まで保証した値として扱わない。

## V28 の可否の結論

**条件付きで作れる。** 最小変更は `read_internal()` の status 除外だけを変異マクロ下で外し、snapshot の `txid_ < cstamp_` 条件を残すこと。[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:153)。期待は、発火した読取りが commit すれば orphan・巡回・I のいずれもありえ、異常終了や停止もありえる、というもの。`Version` の直接 free を今回の YCSB 経路から断定する根拠はない。一方、GC による**別版への再利用**と未完成 body の読取りは現実のリスクであり、得られた verdict の帰属には制限がある。

## 推奨 cell

| 対象 | flag | 分離できる理由 |
|---|---|---|
| V29 | `ycsb_max_ope=1, ycsb_rratio=0, ycsb_rmw=true`、高競合・4 thread | 一取引一 key の RMW。update が同じ key の R を消し、別 key の write skew は構造的に起きない。`changed/committed>0` で機構発火を確かめ、巡回 0・I なら観測上の盲点と記録できる。 |
| V28 | `ycsb_max_ope=1, ycsb_rratio=100, ycsb_rmw=false`、高競合・4 thread | 読み専用取引の R が残り、write skew は起きない。別の writer が作る inflight／abort 版の選択と orphan を狙える。ただし発火、stamp 再読、再利用により orphan は保証されない。 |

根拠は YCSB の操作生成と RMW 実行経路、および同一 key の R 消去である。[ycsb.hh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/include/ycsb.hh:55)、[transaction.cc](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:239)。

## 総括

V29 は予定の変更で実走可能。V28 も隔離した変異として実走可能だが、結果は安全な版参照を前提に解釈できない。si は巡回があれば N、なければ証拠面不足で I となり、S は期待しない。[model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/orchestrator/verifier/model.py:554)。K の N は V36 の write skew と分離できないため変異検出に算入せず、上記の一操作 cell と発火診断で効果を調べる。静的検査のみで、build・実走はしていない。