---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: worktree-dev-wave-t1479-known-violation-merge-authorship
seq: 1
title: known-violation台帳(53件)のうち反復増加していた21件のmerge偽陽性を根本修正した (コード+テスト、branch worktree-dev-wave-t1479-known-violation-merge-authorship、変異matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)
---

## 本文

- ユーザー依頼「known-violationの根本解決。今何件かあると思う」を起点に、
  `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` (当初53件) を分類し、
  「受入投入前に local main を取り込む merge で両 parent が同じ実装面 test file を非衝突編集
  しただけの偽陽性」型が21件、同一の構造的原因であることを実測で特定した。
- 根本原因: `_commit_paths()` のmerge分岐が「全parentとのpairwise diffの積集合」で
  実装面著作を判定しており、両parentが同じfileを非衝突編集しただけでmerge結果がどちらの
  parent単体とも異なるため、実際の新規著作の有無と無関係に偽陽性になっていた。
- 段2プランは `git diff-tree --cc --exit-code` を判定に使う案だったが、段3で codex (lensA) が
  実在しないSHAを使った反例を出しつつも「`--exit-code`は自明性を反映しない」という指摘自体は
  正しく、親が使い捨てrepoで実測したところ**真の衝突解消mergeでも`--exit-code`は常にrc=0を
  返す**という重大な欠陥が判明した ({{D:combined-diff-triviality-not-exit-code}})。正しい判定
  (`git diff-tree --cc --no-renames --no-commit-id -p` のraw bytes出力が空かどうか) へ設計を
  訂正し、実プロジェクト全履歴(1295 merge中241候補)で46件がUnicodeDecodeErrorになる別の
  実装バグも段6レビューで発見・修正した (raw bytesのまま判定しUTF-8 decodeしない)。
- `_message_file_paths()` (commit前のpreflight) は本waveでは意図的に未修正のまま残した
  ({{D:defer-preflight-fix}})。使い捨てcommit object生成が`tools/audit_dangling_commits.py`
  へ副作用しうるとレビュー2本が指摘し、親が実装を読んで確認したため。
- 受入投入前のlocal main取り込みで、他の並行wave (T-1371、T-1476、T-755、T-1458等) が
  同じ`KNOWN_PROVENANCE_VIOLATIONS`タプル末尾へ独立に追加していたエントリと実競合が複数回
  発生した。解決の過程で、本wave対象外だったT-1371のmerge2件・T-1476のmerge1件も
  本waveの根本修正で実装面findingが消えていた(known-violation-stale検出、個別に
  `_commit_paths()`で再確認)ため、あわせて台帳から削除した。
- 段6のmerge競合解決中に親(Claude)がCodexへ委任すべき通常commitを直接編集してしまう手順
  ミスが1回あり ({{F:parent-direct-edit-after-merge-resolved}})、`git reset --soft`で取り消し
  Codexへ正しく委任し直して是正した。
- 本waveが実際に削除したエントリは計22件 (対象の19件 + 副次的に解消したT-1371 2件・
  T-1476 1件、いずれも`_commit_paths()`で個別に`[]`を再確認済み)。着地後のmain上の台帳は
  44件 (本waveの削除・追加に加え、並行して着地した他wave — T-755・T-1371・T-1476等 — の
  独立追加を含む、`len(check_ai_provenance.KNOWN_PROVENANCE_VIOLATIONS)`で実測)。
  全履歴監査(正規Pegasus dispatch経由)でrc=0・新規違反なしを複数回確認し、受入全走は
  混雑環境で8回試行 (無関係な他waveのprovenance違反・submodule同期・複数回のmerge競合を経て)
  child-greenで着地した。main advance: `4208a3f4b4d3c8ba6a25e30434a6c0c173eff80f`。

## 次の一手差分

### 新規

- {{T:message-file-paths-preflight-fix}} **P2・新規**: `_message_file_paths()`
  (commit前preflight) が本waveと同型のpairwise-intersection偽陽性を持ったまま残っている。
  修正には使い捨てcommit object生成が要り`tools/audit_dangling_commits.py`への副作用を
  安全に避ける設計 (隔離object store等) が必要。post-hoc監査 (`_commit_paths()`、
  本waveで修正済み) だけでland/記録のrc判定は正しくなるため緊急度は低いが、
  commit前の意図しない警告が残り続ける。
