# 段 1 brief — [T-2396] A-1 受領証の公開を os.link() へ改める

基準 commit: `0e02169b0` (local main)。worktree
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2396-a1-receipt-oslink`、
branch `worktree-dev-wave-t2396-a1-receipt-oslink`。

## 確定済みユーザー裁定 (覆さない)

- **D1732 (2026-09-07、/rulings 全件 第 13 回、推奨どおり):** A-1 driver の group submission receipt
  の公開を `os.link()` による hard link へ改める。素の rename への退避と `O_EXCL` の直接書込みは採らない。
  `complete` の completion receipt 公開と materialize 側も同族として同じ形へ棚卸しする。
  実装は Codex `role=author` が持ち、正例・負例を同じ commit へ入れる。
- 一次資料: `output/insights/2026-09-07_a1-pilot-attempt-0002/README.md` §5・§7、`docs/failures.md` F870。

## 親が実機で測り直した前提 (2026-09-08 00:35 JST、durable base 直下の scratch、fstype=lustre)

| 操作 | 結果 |
|---|---|
| `renameat2(RENAME_NOREPLACE)` → 空き先 | errno 22 EINVAL (欠陥は現在も再現する) |
| `os.link()` → 空き先 | 成功、`nlink=2`、**staging は残る** |
| `os.link()` → 既存先 | errno 17 EEXIST、**宛先 bytes は不変** |

probe: 本 job dir の `probe_link.py` (repo 外)。裁定の前提を覆す新事実は無い。

## scope (本題の実装だけ)

1. **(必須)** `_publish_submission_receipt` の公開を `os.link()` へ改める。公開成功後に staging を外す。
2. **(P1)** `complete` の completion receipt (`_run_complete_v3` / `run_complete` の 2 箇所) は現在
   `_exclusive_write` で完成名へ直接書いている。親の provisional 裁定は **同じ staging + `os.link` 形へ
   揃える**。成果物影響: 書込み途中で落ちると `receipts/completion.json` が create-only 名を千切れた
   bytes で占有し、その attempt の proof chain を二度と閉じられなくなる (submission 側に staging が
   ある理由と同型)。**攻撃対象。**
3. **(P2)** materialize 側 (`_publish_materialization_bundle` 系) は **directory** を公開するため
   `os.link` を使えない。provisional 裁定は **棚卸し結果を記録するだけで変更しない**。既存の
   probe + `PUBLISH_EINVAL_FALLBACK` を残す。**攻撃対象。**
4. **(P3)** `receipts/submission-failure.json` (`_write_v3_submission_failure`) も同じ directory の
   create-only 受領証だが、裁定が名指ししていない。provisional 裁定は **棚卸しのみ・変更しない**
   (失敗経路の受領証が千切れても成功した attempt の chain を塞がない)。**攻撃対象。**
5. 正例・負例を同じ commit へ入れる。既存の 7 本の submission 公開テストは機構の置換に伴い
   書き換えるが、**検査を弱めない** (受理集合を 1 件も広げない)。

## scope 外 (足さない)

- 仮想リスク向けの gate・検査・台帳・一般化。file system probe や機構選択 evidence を submission
  受領証へ新設しない (`os.link` は Lustre でも tmpfs でも通るので選択肢が要らない)。
- 受領証 JSON の schema・field・bytes の変更。producer の出力 bytes は 1 byte も変えない。
- `_exclusive_write` / `_exclusive_write_text` の一般利用者 (intent、barrier、qsub stdout 等) の変更。
- calibrator・A-2 など他 module の同型経路。

## 不変条件

- **create-only の排他性を落とさない。** 既存先への公開は必ず失敗し、既存 bytes を 1 byte も変えない。
- 公開は原子的で、部分公開の窓を作らない (完成した staging への hard link だけ)。
- 失敗時に staging を残さない。identity 検査 (dev/ino) つきの既存 cleanup 契約を維持する。
- 規律 2: correctness gate・verifier・受理集合を緩めない。テストの期待値を甘くして緑にしない。
- 公開される receipt の bytes は現行と同一。

## 成果物の形

Codex `role=author` の 1 commit: `paper_story_a1_paired.py` + `test_paper_story_a1_job_contract.py`
(+ 必要なら `test_paper_story_a1_paired.py`)。docs / 台帳 fragment は親が段 7 で別 commit。

## 分割方針

編集 path が 1 production file + 1〜2 test file で密結合のため **単一単位**。段 5 の実装子は 1 本。

## 受入・実測環境

login node (Pegasus)。計算ノード job は不要 — 変更は Python の file 操作だけで、
Lustre 上の挙動は上表の probe で測り済み。受入は全走 (`tools/dev_wave_wait.py acceptance`)。
