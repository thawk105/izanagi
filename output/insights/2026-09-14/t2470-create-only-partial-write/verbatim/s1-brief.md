# 段 1 brief — [T-2470] create-only writer の作りかけ file 撤去

## 研究前進
8c 正式走の試行台帳 (成果物 3 本のうち「再現可能な試行台帳」) は genesis 1 件と slot ごとの分類受領証を
create-only で一発だけ書く。書き込み途中で失敗すると作りかけ file が canonical path を占有し、以後
genesis も当該 slot の分類も恒久拒否になり、その freeze の試行台帳が発行不能になる。最小差分は
「自分が O_EXCL で作った file を失敗時に unlink して再試行可能に戻す」1 箇所。完了判定 = 失敗注入後の
再試行が成功し、既存の完成物は失敗経路でも消えないことを同一 commit のテストで示す。

## 確定済みユーザー裁定 (command 引数)
- 影響する caller を列挙する。
- 失敗時に消す正例と、既存の完成物は消さない負例を同じ commit へ足す。
- 実装面なので Codex `role=author` (D95) と変異事前登録が要る。規律 2 を緩めない。
- 本題の修正だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
- 着手直前の local main (7dc4ecc39) から fresh worktree を作る。→ 実施済み。

## scope と変更面 (実アンカー)
| # | file:anchor | 役割 | 変更 |
|---|---|---|---|
| A | `orchestrator/campaign/trial_registry.py:2433` `_write_create_only` | 共有 create-only writer | 作成成功後の失敗経路で自作 file を unlink |
| B | `orchestrator/tests/test_trial_registry.py` | 既存テスト file | 正例 (失敗→撤去→再試行成功) と負例 (既存完成物は非撤去) を追加 |

影響する caller (production、grep 実測):
1. `create_attempt_registry_genesis` (定義 `trial_registry.py:2471` / 呼び出し `:2530` /
   gate=`attempt-registry-genesis`) → `output/s8c-preregistration/attempt-registry.jsonl`。
   CLI 入口は `trial_registry.py:6559`。
2. `classify_attempt` (定義 `:3254` / 呼び出し `:3288` / gate=`attempt-classification-receipt`) →
   `output/s8c-trial-registry/classification-receipts/<sha256>.json`。別名
   `classify_attempt_failure` (`:3336`)。production caller は
   `orchestrator/campaign/p3_autonomous_workload_trial.py:4876`。
非対象: `s8b_attempt_registry.py` / `attempt_registry_core.py` は本 writer を使わない (独自 layout)。

## 成果物影響 (DW-G05)
放置時: 部分書き込みが 1 度起きた freeze では (1) genesis が壊れた bytes で path を占有し、その freeze の
certified 選択・試行台帳が発行不能、(2) 分類受領証側は当該 slot が恒久的に分類不能となり受理集合から欠落する。
修正後: 成功経路の bytes・fsync 順序・例外型は不変なので、既発行成果物の値・参照は変わらない。
受理集合の変化は「作りかけ残骸が消えた後の再試行が通る」1 点だけで、既存の完成物に対する拒否は不変。

## 不変条件 (規律 2 を緩めない)
- `FileExistsError` 経路 (= 既存 file が居る) では絶対に unlink しない。撤去するのは
  「この呼び出しが `O_EXCL` で作成に成功した file」だけ。
- 成功経路の bytes、`fsync(fd)` → `fsync(parent_fd)` の順序、送出例外型 `TrialRegistryError` は不変。
- unlink 自体の失敗で元の失敗原因を握り潰さない。
- 撤去は `dir_fd=parent_fd` 相対で行い、path 再解決による別 file の削除を作らない。

## 成果物の形
`trial_registry.py` の 1 関数の差分 + `test_trial_registry.py` への正例・負例テスト (同一 commit)。
新規 test file は作らない (所要台帳・自走 harness の追加は不要)。gate・台帳・一般化は足さない。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)
- **(P1)** 部分書き込みの実発生は実測 0 件。近縁の T-1854 (分類受領証 durability) は `docs/phase3.md:1057` で
  D205/D730 により「現行 claim への具体的影響が立証されない追加防御」として除外済み。親の provisional 裁定:
  本件は追加防御ではなく、既存 writer が自らの create-only 契約 (失敗は再試行可能) を満たしていない
  正しさ欠陥であり、同 repo 内 `tools/issue_env_contract_activation.py:46` に正しい先例実装がある。scope 内とする。
- **(P2)** **[2026-09-14 親が自己訂正。初版の「reader 0 件」は誤りだった]** s8c 受領証の reader は実在する:
  `orchestrator/campaign/trial_registry.py:2311` `_assert_attempt_classification_receipts` が
  `output/s8c-trial-registry/classification-receipts/<digest>.json` を読み、
  `sha256(bytes) != classification_receipt_sha256` なら
  `_fail("attempt-classification", "classification receipt digest differs")` で赤にする。
  したがって作りかけの bytes が正当な受領証として受理される経路は無く、本件は**可用性**の欠陥であって
  規律 2 の直接侵害ではない、と親は provisional に裁定する。
  さらに `classify_attempt` は受領証 file を書いてから registry 行を append するので、部分書き込み時は
  registry 行が存在せず、壊れた file は孤児として誰からも参照されない。要裏取り (段 3 luna)。
- **(P3)** 失敗注入は `os.write` / `os.fsync` の monkeypatch で行う。DW-O14 に従い実装を読んだが
  trial_registry に正規の注入 seam は無く、同 repo の先例テスト
  (`orchestrator/tests/test_env_contract_activation.py:2586`) が同じ手段を採っている。
- **(P4)** `fsync(parent_fd)` 失敗時も撤去する (先例の `directory_fsync` ケースに合わせる)。

## 並列分割方針
変更面は 1 production file の 1 関数 + 1 test file なので所有の分割は不要。段 2 plan 1 本、段 3 敵対相談 2 本
(異なるレンズ)、段 5 実装子 1 本、段 6 敵対レビュー 2 本 + 変異 matrix + 受入全走。
正しさ防壁 (create-only) に触り受理集合が動くため、DW-C00 に従い敵対検証子は省かない。

## 受入・実測環境
login node で焦点走 → 受入全走 (`tools/dev_wave_wait.py acceptance`)。新規 Pegasus 実行体は無いので
計算ノード投入は不要。
