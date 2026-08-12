---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t886-rollout-fastpath
seq: 4
title: dev-wave 段 8 — 台帳の件数 literal 固定が D316 の 2 例目だと確定し、submodule drift を手順へ戻す (docs のみ、branch worktree-dev-wave-t886-rollout-fastpath)
---

## 本文

- **段の順序を誤った。** 段 7 の記録後、段 8 を飛ばして段 9 の land を実行した。
  land 後に気づき、段 8 を改めて実行して docs のみの追い land とする。
  **段 9 で取り込んだ集合には段 8 の成果が入っていない**ため、監査済み集合は 2 回に分かれる。
- 候補 3 件を評価し、2 件を台帳へ送り 1 件を落とした。
  - **送った 1**: 生きた台帳の件数を literal 固定した検査が承認済みの追加で受入を止めた
    ({{F:known-violation-ledger-count-pinned-literally}})。**D316 と同型で、異なる
    producer / consumer での 2 例目**にあたるため `DW-G03` の族一般化条件が成立する。
    恒久対応は正しさゲートの受理集合を変えるので裁定へ返す (下記 新規)。
  - **送った 2**: main 取り込みが submodule pointer を進めても working tree が追随せず、
    受入が `prerun-clean rc=70` で止まった ({{F:submodule-pointer-drift-after-merge}})。
    `DW-O20` へ「受入投入前に `git submodule update --recursive` で記録へ揃える」を追加した。
  - **落とした 1**: parametrize 済みテストの期待 node を suffix 無しで登録した件。
    変異 harness が collection と照合して**起動前に止めた**ため損失ゼロで、
    義務は既に機械検査が代替している。D271 の鏡像により手順へは足さない。
- **docs-only 受入免除判定の証拠**: 本追い land の変更は `docs/spool/` の fragment 2 本と
  `docs/dev-wave/operations.md` の 2 行のみ (判定手順 = `git diff --name-only` が
  docs 配下だけを示す)。実装面ゼロ。`docs/dev-wave/operations.md` を対象にする nodeid は
  `orchestrator/tests/test_check_docs.py` に存在するため、**免除せず check_docs を実走**して
  rc=0 を確認した。

## 次の一手差分

### 新規

- {{T:apply-d316-to-provenance-registry-test}} **P2・新規**: D316 を provenance の既知違反台帳へ
  適用する。`test_known_violation_ledger_is_exactly_*_literal_entries` は entry 数を literal で
  固定しており、承認のたびに受入を止める。検出力の本体 (entry 内容の完全一致) を保ったまま
  件数固定だけを外す形が候補だが、**正しさゲートの受理集合を変えるため独立の敵対検証を
  受入条件とする。** 関数名にも件数が入っているため改名も伴う。
