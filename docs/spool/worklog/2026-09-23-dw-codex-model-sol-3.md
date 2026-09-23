---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: dw-codex-model-sol
seq: 3
title: dev-wave の Codex 子 model を gpt-6-astra から gpt-6-sol へ移行する (docs + check_docs + テスト、branch worktree-dw-codex-model-sol)
---

## 本文

- ユーザー指示 (2026-09-23): 「gpt-6-sol が使えるようになったのでそちらへ移行したい、reasoning は medium」。model 権威の改訂として {{D:dev-wave-codex-model-sol}} に記録した。
- **切り替わりの時点:** 起動器は投入時点の `--repo-root` の docs から model を導出する。本 wave の land 後に始まる wave (とその子 worktree) から gpt-6-sol になり、land 前に始まって走っている wave は自分の木の docs どおり gpt-6-astra のまま走り終える。過去記録の astra 表記は書き換えない (規律 7)。
- commit: e39e43c9c (docs: DW-O01 の model 行) → b8c9c6cbe (check_docs.py の literal とテスト期待値 5 行、Codex author)。
- 生死確認: `codex exec -m gpt-6-sol` (medium、read-only、サブスクのログイン) rc=0。実装子自体も改訂後 docs から gpt-6-sol / medium を導出して走り、受領証に同値が記録された。
- 段 5 の 1 回目は非 NFC 行の表示で起動器に不受理 (F223 の再発)、行範囲禁止を足した 2 回目で受理。
- 検査: login の check_docs 違反なし、焦点走 (Pegasus、8 file) 1437 passed / 11 skipped、変異 final KILLED 2 / SURVIVED 1 / MISMATCH 0 (全件登録どおり)。受入全走は land の受領証を正とする。
- 工数: Codex author 2 本 (いずれも gpt-6-sol / medium、各 12 call、1 本目は不受理)、read-only の疎通 1 回。計算ノード: 焦点走 1 job、変異 probe + final 10 job、受入 1 回。段 2・3・段 6 レビュー子は軽量版で省略。
- 一次資料: `output/insights/2026-09-23/dev-wave-codex-model-sol/README.md`。

## 次の一手差分

### 見送り追記

- [T-855] 2026-09-23 に再発火 (F223 再発、model 移行 wave の段 5 author 1 回目が test_check_docs.py 5756 / 5779 行を表示して不受理)。追加裁定はせず記録のみ。
