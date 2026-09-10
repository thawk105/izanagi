# T-173 段 6 review 裁定

## accepted

1. explicit-only policy と description の自然言語起動約束は矛盾する。policy=false を維持し、
   description を `$cleanup-branches` 明示起動専用へ直す。
2. 破壊直前の再検査は列挙5項目でなく、dispatcher §2 と Codex overlay の全 eligibility
   (ahead/cherry、clean、HEAD包含、recent、lock、canonical path、main/primary、ownership/foreign、
   `/proc` 滞在) を毎回再評価し、unknown / changed / new residency で停止する。
3. global prune の preview と実行は原子的に束縛できない。Codex overlay をさらに縮退し、
   `git worktree prune --dry-run --verbose` は報告用previewだけにし、real pruneは実行せず人間へ残す。
4. Skill / command の単純substringは安全極性・位置を守らない。Markdown comment / fenceを除いた一意な
   H2 section内のexact safety clauseとして検査し、反転・移動・decoyを拒否する。
5. adapter / command の全required clauseをstable ID付きparameterized positive controlで個別に抜き、
   first-element-only退行を殺す。
6. synthetic positive fixtureはchecker定数から生成せず、test側の独立した実Skill形本文とmetadataを使う。
7. Skill budgetはfinal bytesへ小幅headroomだけ加えた値へ縮め、byte / line超過の恒久負例を追加する。
8. negative-case registryはchecker側のexact expected IDsとtest側registryを相互照合する。
9. mutation期待nodeの曖昧さはreal。初回事前登録をerratumとして保持し、fix後・本走前にstable exact
   nodeを再登録する。
10. commit前にexact 4 filesをstageし、cached 4-file diff / cached diff-check / commit tree実在を確認する。

これらは同じSkill文言・checker・fixture・controlsが相互依存するため、4 file所有の単一Codex fix unitへ戻す。
fix前統合snapshotは `s6-pre-fix-integrated.patch`。

## refuted / scope外

- exact description field、exact metadata bytes、raw `[TODO` forbidden、helperの既存consumer後方互換は成立。
- common contractの一部再掲は現在fail-closed方向で、今回のmust-fixにしない。Claude command本文の改訂も
  cleanup-branches自己改善gateを迂回するためscope外。
- in-repo testの悪意ある全削除を完全防止する一般機構はscope外。production/test別fileの相互pinと
  adversarial reviewで今回の4-file surfaceを固定する。

## 成果物影響

未修正では、安全文言を危険側へ反転・decoy移動してもchecker greenになり、active/foreign worktreeや
共有Git metadataを失わせ得る。またexplicit-only矛盾により自然言語依頼がoverlayを通るという虚偽の
利用可能性を記録してしまう。
