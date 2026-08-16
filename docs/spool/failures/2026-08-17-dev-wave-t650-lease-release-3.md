---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t650-lease-release
seq: 3
---

## 再発

### F283

- **再発: 2026-08-17** — 同じ gate (`NG: Codex hook 配線の exact 検証に失敗:
  tools/pegasus/admission_registry.json: working bytes が HEAD blob から drift`) で
  codex 子が 2 度 launcher_error になった。**引き金が既載と異なる。**
  既載は「段 5 の実装子が同ファイルを変更した直後」だが、本件は
  **`git merge --no-ff --no-commit main` の競合解消中**である。実装子は同ファイルを
  触っておらず、main 側が持ち込んだ版が index に staged された結果、
  working bytes が自 HEAD の blob と一致しなくなった。
  **既載の恒久対応 (レビュー投入前に統合 commit を作る) では防げない** — 統合 commit は
  作ってあり、その後の merge で drift したためである。
- 新しい情報は 3 点。(i) **merge 進行中は codex 子を起動できない。** 実装面の競合解消は
  Codex `role=author` が担う契約なので、競合が実装面に出た瞬間に「子が要るのに子を起動できない」
  状態になる。(ii) 回避は working tree だけを HEAD の bytes へ戻して起動し、子の完了後に
  index から復元する形で成立した。index 側の sha256 を事前に控え、復元後に一致を照合した
  (`git show :<path> | sha256sum` → `git show HEAD:<path> > <path>` → 子 → `git checkout -- <path>`)。
  (iii) 1 度目の失敗が完全な receipt を残すため、**同じ prompt での再投入は
  `NG: 既存の完全な receipt は上書きできない` で止まる**。`--artifact-root` を分ける必要がある。
- 実害: 子の起動失敗 2 回と、回避手順の設計で約 4 分。誤った land には至っていない。
