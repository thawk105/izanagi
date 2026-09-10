## 総括

**plan2 は修正が必要です。親の scope 縮小を支持しますが、FetchContent は必須の修正として残してください。** 続行承認は前提とし、追加承認待ちには戻しません。以下は静的検査の結論で、実機閉鎖は未確認です。

1. **real／scope 内：prefix 転送だけでは configure に到達できない。**
   canonical [ThirdParty.cmake:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/external/ccbench/cmake/ThirdParty.cmake:54) は configure 中に masstree を populate し、`:112`／`:136` では mimalloc／googletest も展開します。A1 job は [`:1331`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/tools/pegasus/paper_story_a1_paired.sh:1331) で gflags／glog の prefix だけを渡します。放置すると、依存探索を直しても計算ノードで取得が止まります。
   **最小修正：** hydrate の `.source_root` → job ごとの scratch の `*-src` コピー → pristine 検査 → `prepare_masstree_fetchcontent` を既存 A2 同様に接続する。[A2 job:353](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/tools/pegasus/paper_story_a2_certification.sh:353)、[A2 driver:699](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a2_certification.py:699) が実例です。親 [brief:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/resume-brief.md:14) の「必要なら」は今回必須へ具体化してください。`cache_root` 直渡しは禁止のままです。

2. **real／scope 内：「実 build の argv grammar を維持」はそのままでは成立しない。**
   [buildcache:1970](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/buildcache.py:1970) は prefix の後に FetchContent base／source 引数を挿入します。一方、A1 [consumer:4917](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:4917) は固定長を要求し、`:4935` の配列と完全一致させます。供給だけ直すと、完走しても `trace0-source-route-incomplete` になります。
   **最小修正：** 追補適用時の exact grammar に base と source 3 本を追加し、重複・欠落・余分な引数を引き続き拒否する。転送は [pipeline:1494](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1494) が要求する **base＋source 3 本＋既存 dependency receipt の5値一式**を使う。loop の転送は既に [`:715`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/loop.py:715) にあります。

3. **real／scope 内：configure は rc=0 でも警告で拒否される。**
   [condition_meaning_gate:1617](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/condition_meaning_gate.py:1617) は stderr が非空なら拒否します。gflags／glog は独自 Find module の `find_library`／`find_path` を使うため、未使用の `gflags_DIR`／`glog_DIR` 等を足す案は採れません。[Findgflags:5](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/external/ccbench/cmake/Findgflags.cmake:5)、[Findglog:5](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/external/ccbench/cmake/Findglog.cmake:5)。
   **最小修正：** 既存 prefix と実際に消費される FetchContent 引数だけを渡す。probe は成功時も configure stderr を保存する。警告の実際の発生有無は未確認で、共通 gate の stderr 拒否を緩める理由にはなりません。

4. **real／scope 内：patched 関門だけを作っても実 build は通らない。**
   A1 は [`:6748`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:6748) で元 submodule を capture し、[`:7021`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:7021) の `run_campaign` に `ccbench_dir` を渡していません。balanced branch は [loop:765](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/loop.py:765) で canonical 検査を必須化し、[pipeline:1942](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/pipeline.py:1942) が各 build 前に実行します。
   **最小修正：** 固定 patch の独立した期待値との照合、同一 root の gate→SourceEvidence→trace/perf build への転送、consumer の `-S` と既存 admission の root の照合を残す。任意 dirty 受理や、元 root だけを検査する変更は不可です。

5. **real／scope 内：submit・preflight・complete の取り残しがある。**
   [qsub 契約:2536](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:2536) に third-party source の転送はありません。環境変数を job 側で読むだけでは供給経路が閉じません。
   **最小修正：** hydrate 出力の受渡しを既存 submit 契約へ明示し、追補 binding を [intent 作成:3161](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:3161) より前に確定する。元 submodule の [job preflight:351](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/tools/pegasus/paper_story_a1_paired.sh:351) は維持する。complete は [`:4142`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:4142) で submission／intent、`:4169` で各 shard を再検証するため、Python と正常／失敗 terminal の source 集合を揃える。materialize の [`:8571`](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:8571) および非認証 observation の raw 再収集も同じ契約を使わせます。

6. **refuted／今回の必須追加として不採用：inode 防衛・readonly 化・新 WAL receipt・全実装 closure の一律追加。**
   [plan2:36](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2397-a1-attempt4/artifacts/t2397-a1-attempt4/plan2.md:36)、`:42`、`:70`、`:77` の拡張について、既存 materializer／SourceEvidence／admission／build 境界照合では不足する根拠は示されていません。[DW-G05:79](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/docs/dev-wave/core.md:79) に従い削減できます。**固定 patch 以外の差分と別 root の拒否要件自体は残します。**

author の一回限りの probe は、production callable を通して **3 workload の全 arm 関門→同じ固定 source の trace/perf build→既存 verify** を確認し、実 argv が更新した consumer grammar に適合するところまで観測してください。probe 成功を submit／complete や pilot 完走の証拠とは扱いません。

旧 prereg／policy bytes、統計値、T2514 の全 arm detail と元の拒否、既存負例は維持。編集・commit・submit・pytest・probe 実走は行っていません。
