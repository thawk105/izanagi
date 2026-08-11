# 裁定パッケージ — trace v2 の commit 系譜と、手順 4 の protocol 前提

```text
authority: dev-wave (背景 job) が [T-816] 手順 1・2 の実装中に起票 (2026-08-11)
wave: dev-wave-t756-fn2-trace-v2 / branch worktree-dev-wave-t756-fn2-trace-v2
根拠: [T-816] Q1〜Q3 全問 (a) (output/insights/2026-08-11_t756-commit-witness/verbatim/ruling-package.md)
性質: (Q1) 人間承認の対象が変わる設計択一、(Q2) 手順 4 の開始条件
一次資料: 同 directory の README.md / s3-lens-a.md / s6-review-a.md / s6-review-b.md
並走ガード: 実装は完了済み。裁定を待つ間も既存の受理集合は 1 つも変わらない (gitlink 不変)
```

## 0. 状況

[T-816] の手順 1・2 は完了した。新 commit は
`511c9538e4e8efa54b45cda62e72389ed3b706ec` (submodule branch `izanagi-trace-t816-fn2`、
親 = 現行 pin `d706650`)。bundle で repo 外へ保全し、新規 clone から復元できることを実証した。
旧/新 pin の TRACE=0 等価性は 3 本の実走で pass、実 trace 244,971 txn で framing も実測した。

**次は手順 3 (ユーザーが push して新 pin を承認する) だが、その前に 2 問の裁定が要る。**

## Q1: 新 commit をどの系譜に載せるか (主問)

### 事実 (親が一次資料で裏取り)

- **`c9c1a9c` はユーザー承認済みの新 pin である。** `docs/archive/worklog-phase3-0729-49-58.md:577` に
  「[T-167]: **採用**。ccbench の新 pin `c9c1a9c` をユーザー承認 (D16)」とある。
  中身は write-intent shadow (`I` 行、`Integrity.write_intent_violations`) で、
  `output/insights/2026-07-29_t152-write-intent-shadow.md` が正本。**status は not_integrated、push 待ち。**
- [T-167] は worklog 430 の次の一手にも carry されている (未実装のまま)。
- **本 wave の worktree からは `c9c1a9c` に到達できない。** submodule は origin からの fresh clone で、
  `git cat-file -t c9c1a9c` が `fatal: Not a valid object name` を返す。
- したがって新 commit `511c953` は `d706650` を親に持ち、**`c9c1a9c` と兄弟**である。
  単一 pin で両方を得ることはできない。

### なぜこれが重要か

`c9c1a9c` の write-intent shadow は、**本 wave の FN-2 v2 が閉じられない偽陰性を閉じる独立 witness** で
ある。v2 の C 行が持つ件数は R/W 行と同じコンテナから取るので、write set から要素が消えれば
件数も W 行も同時に減り検出できない。そこを埋めるのが `c9c1a9c` である。
つまり 2 つは競合ではなく**補完**であり、最終的には両方が同じ pin に乗るのが望ましい。

### 択一

- **(a) 推奨: `511c953` を `c9c1a9c` の上へ乗せ直してから push する。**
  ユーザーの checkout には両方の commit があるので、`git rebase --onto` か cherry-pick で 1 本にできる。
  承認手番が 1 回で済み、v2 と write-intent shadow が同時に有効になる。
  **代償:** SHA が変わるので TRACE=0 等価性の実走をやり直す必要がある。ただし checker は
  (old, new) の 2 commit を引数に取るので**再走 1 回**で済み、設計もテストもやり直しにならない。
  再走は `python3 tools/check_trace0_preprocess_identity.py --repo <submodule> --old d706650… --new <新 SHA> --cxx g++-12 --expect-paths cc/silo/transaction.cc` の 1 コマンド。
- (b) 兄弟のまま両方を push し、pin は片方だけ進める。もう片方は次の pin 前進まで待つ。
  承認手番が 2 回に増え、待たされた方の偽陰性が残り続ける。
- (c) `511c953` だけを push して pin を進め、`c9c1a9c` ([T-167]) は破棄または再実装する。
  既に承認済みの成果を捨てるので推奨しない。

**(a) を推奨する理由:** 2 つの機構は補完関係にあり、片方だけでは FN-2 の同時欠落型が残る。
乗せ直しのコストは checker の再走 1 回に閉じており、承認手番を 1 回に減らせる。

## Q2: 手順 4 の「v1 拒否」を protocol 無差別に適用してよいか

### 事実

- 本 wave が v2 化したのは **silo だけ**。`cc/si/transaction.cc` (SI) は v1 helper を使い続ける。
- SI を v2 化できなかったのは編集面の制約による。`hooks/guard_write.py` の `EVOLVE_BLOCK_SOURCES` は
  CCBench の編集面を `include/backoff.hh` と `cc/silo/transaction.cc` に限定しており、
  SI の transaction.cc も `include/trace.hh` も書けない。迂回は D41 が却下済み。
- 現行 verifier の parser は C を固定 5 field で unpack し、未知 tag を `ParseError` にする。
  つまり **v2 trace は今は fail-closed で拒否される** (certified が偽で出ることはない)。
- 将来 protocol を広げる場合 (S1 移植の mocc など) も同じ壁に当たる。

### 択一

- **(a) 推奨: 編集面を広げる裁定を先に取り、SI (と将来の移植先) も v2 化してから v1 を拒否する。**
  防壁の変更なのでユーザー裁定が要る。広げ方は「trace-hook 用の別 allowlist を設け、
  Phase 3 の coder が触れる EVOLVE-BLOCK とは分ける」のが素直である
  (coder の編集面を広げないまま、trace-hook 作業だけを通す)。
- (b) verifier の入力へ protocol を束縛し、**silo の v1 だけ**を拒否する。SI は v1 のまま受理する。
  編集面を触らずに済むが、「protocol ごとに受理形式が違う」状態が恒久化する。
- (c) v1 拒否を延期し、v2 を受理しつつ v1 も受理し続ける。FN-2 が残るので
  [T-816] Q3 (a) の裁定 (v2 必須) に反する。

**(a) を推奨する理由:** (b) は受理集合を protocol ごとに分岐させ、後から「どの protocol の
どの形式が certified の土台か」を追いにくくする。(c) は既決の裁定に反する。
(a) は防壁の変更を伴うが、変更対象は「AI が CCBench のどのファイルを書けるか」であって
正しさゲートそのものではなく、coder の編集面を広げない形に設計できる。

## この裁定で変わらないこと

- 絶対規律 1〜6。本 wave が実装した v2 emitter と TRACE=0 同一性 checker。
- CCBench の現行 pin `d706650` と、それに束縛された既存の凍結成果物・certified 結果。
- `test_characterization_txn_tail_loss_is_false_green` の期待値 (手順 4 まで反転しない)。
