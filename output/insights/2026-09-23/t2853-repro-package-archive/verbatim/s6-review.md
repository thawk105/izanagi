## 総括

**NO-GO。** 写しの件数・総 bytes は manifest と一致し、照合も原本と写しを別々に読んでいる。ただし、R1 の source 再構成手順、未完走履歴の扱い、trace 不在の断定に修正が必要。
静的読解・小さい記録の照合によるレビューであり、テスト・再判定・78 GB の再ハッシュは実施していない。

## must-fix

- **M1 — B-8 の R1 手順では当時の source context を復元できない。**
  [README:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-23/t2853-repro-package-archive/README.md:207) は pin に patch を当てるだけだが、記録の `patch_sha256=31316713…` は **template patch** の hash。実際の [runner:634](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py:634) は適用後、`bindings.gate_predicate` を `quarantine(..., write=True)` で書き込む。template の `izanagi_gate_pass = true;` のままでは当時の source にならない。
  **修正:** 両系列の patch 所在を記録 commit 内の path で明記し、B-8 は gate predicate の適用と `source_before/source_after` に対する照合を追加する。D2160 は `patches/silo-backoff-fixed.patch`、B-8 は `patches/silo-backoff-trigger-gating-variant.patch` の hash が記録値と一致することを確認した。

- **M2 — 全94走を同じ「旧判定との比較」手順にできない。**
  [README:199–209 の入口](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-23/t2853-repro-package-archive/README.md:199) は全走を対象として `verifier.json` と比較するが、D2160 の `run/calib/fixed-{5,10}-{write-heavy,balanced}/extime-10/verifier.json` は4本とも **0 B**。前段 [README:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-22/t2853-repro-package-estimate/README.md:90) も明記している。また、手順が引用する32.4 GiBは改修版の値で、当時の旧版・既定workerによる10秒走の資源実績ではない。
  **修正:** 判定取得済み90走と未完走4走を分け、後者は `result.json` の timeout/kill・未完走記録を保持した追加評価とする。当時版／改修版別に資源見積りを示す。B-8 の `reverify` も汎用R1入口ではなく、[runner:829](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py:829) が完走済み・校正recordを拒否するため、その制限を明記する。

- **M3 — 調査範囲を超えて trace の不在を断定している。**
  [README:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-23/t2853-repro-package-archive/README.md:16) の「2系列だけ」、§0項4、§2.4の「存在しない」、[§5.4:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-23/t2853-repro-package-archive/README.md:224) は、§4.4・§4.5自身の未調査限定と整合しない。前段 [README:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-22/t2853-repro-package-estimate/README.md:101) は、標準経路の削除処理から別コピーの不在までは証明できないと明記している。
  **修正:** 「今回R1入力を確認できたのは2系列」「他系列は原履歴を確認できず、現時点でR1手順を提供できない」に揃える。B-5にも同じ限定を適用する。

## should

- **S1 — 別ツールでの再読は cache 排除の証拠ではない。**
  [README:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-23/t2853-repro-package-archive/README.md:73) の説明は強すぎる。`sha256sum -c` も同じ filesystem cache を読み得る。「別実装でmanifestとの一致を再確認した」とする。追加の全量読取りは不要。

- **S2 — 除外理由にA-1公開leafの照合を明記する。**
  [README:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-23/t2853-repro-package-archive/README.md:81) では、未追跡一覧にあるA-1の4 fileの扱いが説明されていない。今回、4本とも現在の追跡下 `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002/` とbyte同一と確認した。**保全漏れではない**が、その対応を記す。また、job-staging全体には追跡済みの旧raw/traceもあるため、「除外した未追跡分」と全体を区別する。

- **S3 — copy scriptのrc=0だけでは照合成功を意味しない。**
  [archive_copy.py:129](/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260923/tools/archive_copy.py:129) は不一致を記録するが異常終了せず、全体のextra/missingも表示だけである。同じfileを二度読む恒真比較ではなく、今回の記録は `mismatch=[]`・extra/missing空なので、この点だけで写しを否定しない。再利用を案内するなら、**終了コードではなく各照合結果を確認する必要がある**と明記する。

## nit

- **N1 — checkoutコマンドの引数不足。**
  §4共通前提の `git worktree add --detach <commit>` は、`git worktree add --detach <新しいdir> <commit>` に直す。前者では指定値がpathとして扱われ、意図する過去commitのcheckoutを指定できない。