## 総括

**固定 patch の実 source を既存 materializer・admission・verifier へ通す方針は成立します。ただし plan2 の FetchContent 供給と consumer 更新は不足しています。** 親 provisional の縮小方針を採用し、以下の局所修正で author へ渡すのが妥当です。追加承認要求には戻しません。

1. **real／必須：FetchContent は prefix だけでは閉じない。**
   canonical [ThirdParty.cmake:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/external/ccbench/cmake/ThirdParty.cmake:54) は configure 時に populate し、mimalloc・googletest も同ファイルで MakeAvailable します。plan2 §4 の供給では足りず、親 brief の「必要なら接続」も必須へ確定すべきです。
   **成果物影響：関門または build が停止し、attempt-0004 の正例が成立しません。**
   最小修正は、hydrate の `.source_root` → A2 と同じ scratch コピー → pristine 検査 → `prepare_masstree_fetchcontent`。既存実装は [A2 job:342](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/tools/pegasus/paper_story_a2_certification.sh:342)、[A2 関門:699](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a2_certification.py:699)。cache_root 直結は採りません。

2. **real／必須：供給と exact argv consumer を同時に更新する。**
   [pipeline:1484](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1484) は **base・source 3 本・dependency receipt の5値同時指定**を要求します。[loop:715](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/loop.py:715) には balanced branch に届く既存転送があります。一方、[A1 consumer:4918](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:4918) は旧 argv 長を固定しています。
   **成果物影響：供給だけ直すと、正常に build した arm が `trace0-source-route-incomplete` になります。**
   最小修正は既存5値の利用と、`_v2_commands` が生成する追加4 define の位置・個数・対応 path の厳密照合です。任意の追加引数を許可する変更は不可です。

3. **real／必須：clean 検査の移設だけでは実 build を受理できない。**
   [pipeline:1942](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1942) は各 trace/perf build 直前に実引数 `ccbench_dir` の tracked-clean を要求します。
   **成果物影響：固定 patch 正例も dirty として拒否されます。逆に検査を単に外すと追加差分を受理します。**
   最小修正は、A1 の固定追補に限り、同じ実 root の full HEAD・独立期待 materialization を照合する契約を転送することです。元 submodule と契約未指定経路の clean 検査は維持します。関門・source identity・両 build・初回 collection を同じ context 内に置きます。

4. **refuted：新しい materializer／WAL 検査 receipt が一律に必要という見立て。**
   [期待 materialization:614](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/s8b_expected_materialization.py:614) は implementation なしの固定 patch 適用を既に扱えます。[admission:615](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/build_admission.py:615) には generator 経路があり、tracked_clean を偽装する必要もありません。[pipeline:1854](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1854) は既に admission 全体を BUILD_START に保存します。
   この receipt と既存 source_binding を再利用し、追補・patch・期待 digest と実 source の対応、consumer の `-S` と admission root の一致を確認してください。新 WAL receipt、inode 防衛、readonly 化、全実装 closure 拡大を必須にする根拠は不足しています。

author の一回限りの probe は、**実供給を使う production 関門 → 同一 patched source の両 arm trace/perf build → 既存 verify**までを対象にしてください。T2514 の全 arm detail・元の拒否、旧 prereg/policy bytes、統計値、既存負例は維持します。probe 成功を pilot 完走とは扱いません。

静的確認のみ実施しました。編集・commit・submit・pytest・probe 実走は行っていません。
