## 総括

**plan の衝突指摘は real です。既存 materializer／正規 seam を確認しましたが、凍結契約を変えずに通せる反証は見つかりませんでした。** D1936 項3の実装承認を取り消す理由ではありません。ただし、brief の「driver／関連テストだけで二原因を閉じ、投入まで進める」という前提は成立未確認です。

| 判定 | 所見・根拠 |
|---|---|
| **real** | A-1 は関門にも実 build にも未 patch source を渡します。関門は [paper_story_a1_paired.py:6748](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:6748)、campaign 呼出しは同 `:7022`。build は [buildcache.py:2493](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/buildcache.py:2493) の source を同 `:2663` で configure に渡します。 |
| **real** | patched root を渡すと、balanced 経路の各 trace/perf build 前に拒否されます。[loop.py:755](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/loop.py:755) が canonical pin を指定し、[pipeline.py:1942](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1942) が同じ `ccbench_dir` を検査、同 `:1129` が tracked 差分を拒否します。 |
| **refuted** | 「buildcache 内部で既存 patch が自動適用される」という救済経路はありません。通常の `build_v2` は [buildcache.py:3051](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/buildcache.py:3051) で直接実装へ進みます。S8b の descriptor 経路も、渡された snapshot を期待 materialization と照合するもので、A-1 の clean 検査を満たす source 変換ではありません。 |
| **real** | 既存 `patchharness.applied()` は **適用前**の pinned-clean を確認してから patch を適用します。[patchharness.py:247](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/patchharness.py:247)。これは **適用後・build 直前**の tracked-clean と異なる契約です。 |
| **未確認** | attempt-0004 の実配線・build・verify 成功。親報告の196 passed／checks 緑は、その証明ではありません。既存 A-1 関門テストも capture と evaluator を差し替えています。[test_paper_story_a1_paired.py:4093](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/tests/test_paper_story_a1_paired.py:4093)。 |

canonical pin の `include/backoff.hh` と `cmake/Options.cmake` は `git show` で直接確認しました。固定量 decoder と CMake 供給定義はなく、既存 [silo-backoff-fixed.patch:12](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/patches/silo-backoff-fixed.patch:12)・同 `:69` が追加します。単に marker の検査を変えれば済む問題ではありません。

**既存裁定との関係**

[D1936 項3](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/docs/decisions.md:58117) は patch 適用後 source への配線を承認していますが、build 境界の tracked-clean を変更するとは記していません。一方、[凍結 prereg:216](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/output/insights/2026-09-01_paper-story-a1-balanced5-pilot-preregistration/README.md:216) はその境界を明記しています。さらに [D1300:41778](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/docs/decisions.md:41778) は、preflight 後の dirty source を受理する抜けを既に問題視しています。したがって、検査を適用前へ移すだけでは同値な修正になりません。

**推奨**

依存 prefix・arm 別 flags・全 arm 検査・T-2514 detail 保存の配線設計は進められます。ただし投入前に必要な最小裁定は、次の一点です。

> A-1 の build source 契約を「実 tree が canonical tracked-clean」から「canonical tracked-clean を起点に、指定した既存 patch を既存 materializer で適用した source を受理する」へ変更するか。その場合、凍結 prereg／policy との整合をどう扱うか。

これは既存承認の再確認ではなく、今回現物で確認した追加の契約衝突です。採用する場合も、任意 dirty source の拒否、関門と実 build の束縛、trace/perf 分離、verifier、stock 比較を維持する必要があります。別 root への検査差替え、dirty 拒否削除、patch commit による pin 変更は推奨しません。

編集・commit・submit・pytest・性能実走は行っていません。