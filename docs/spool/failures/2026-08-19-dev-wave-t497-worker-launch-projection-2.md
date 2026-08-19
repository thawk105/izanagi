---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t497-worker-launch-projection
seq: 2
---

## 再発

### F225

- **再発: 2026-08-19(2回目)** — [T-497] `dev_wave_wait.py acceptance` の受入 lease 判定
  (`owned-path-overlap`) は、`HEAD...main` の三点 diff に `--owned-path` で渡した path が
  含まれるかどうかだけを見る独立した判定であり、DW-O17 の checker が見る「merge 結果が両親の
  どちらとも異なる (combined path)」判定とは別物である。F225 の恒久対応 (Codex 子が main 側の
  変更を先に wave branch のファイルへ取り込む) は前者を通過させない — wave が実装面 path を
  変更している限り、main 側の内容をどれだけ先取り統合しても `owned-path-overlap` は
  behind が非 0 である間ずっと発火し続ける (`git diff --name-only HEAD...main` に wave 自身の
  変更が常に現れるため)。今回この誤解により、受入投入前に不要な Codex 統合子を1本余分に
  投じた (main-t1361.patch の先取り統合、結果的には commit `461b600f` として無駄にはならず
  最終的な実装統合には使えたが、受入 fail-closed の回避策としては効かなかった)。
  **正しい恒久対応は「待ち手に自動 merge を任せず、`owned-path-overlap` で拒否されたら
  親が `git merge --no-ff --no-commit main` → `check_ai_provenance.py --message-file` →
  `git commit -F` で手動 merge commit を作ってから受入を再投入する」である。**
  pegasus-runbook.md §7.3 の既存記述 (「待ち手では merge せず親へ戻す」) 自体は正確だったが、
  F225 の恒久対応節と読み合わせた際に「Codex 子の先取り統合だけで足りる」と誤読しやすい
  構成だった。
