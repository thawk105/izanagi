---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t933-submission-write
seq: 1
title: submission の durable write に完了保証を入れた — 敵対レビューが検査の穴 3 件を摘出し変異 3/3 一致 (コード + テスト、branch worktree-dev-wave-t933-submission-write)
---

## 本文

2026-08-12 第 3 束の R5 (a) で分離起票された [T-933] を執行した。`_durable_json` の単発
`os.write` は戻り値を捨てており、partial write が起きても切り詰めた JSON を fsync して
正常復帰していた。同 package の `atomic_publish` が確立した offset ループへ揃え、
進捗なしを `SubmissionPreparationError` で拒否する形にした。

**着手前の実測で凍結 pin の閉包が空だと確定した。** `contract.py` の
`REQUIRED_CODE_IDENTITY_PATHS` は `submission.py` 自身を含むが、`_identity_files` が実行時に
`sha256_file` と HEAD blob から導出する動的値であり literal pin ではない。既発行の durable
manifest は 0 件、`FROZEN_MANIFEST` の 23 key に qualification 系はない。よって編集で
series identity が変わっても、旧 bytes を要求する consumer は存在しない。段 6 レンズ A が
grep と find で独立に反証を試み、この結論を支持した。

**段 6 の敵対レビューが検査の穴 3 件を摘出し、いずれも real と裁定して fix で閉じた。**
(1) 最初の fake は「1 回目だけ 3 bytes、2 回目は必ず全量」だったため、最大 2 回だけ retry する
不完全実装も通過した。(2) `written <= 0` の guard に検査がなく、削除しても誰も気づかなかった
(レンズ A も backlog として独立に指摘し、2 本一致で real)。(3) `submission.os` は共有 `os`
module 本体であり、`patch.setattr` が process 全体の `os.write` を差し替えて同一 worker の
pytest capture を巻き込みうる。fix は fake を毎回 short write へ変え、zero-write 専用の検査を
足し、monkeypatch を submission module 側の名前だけを差し替える proxy へ狭めた。

**親の (P1) 段構成判定は甘かった。** 軽量版として段 2・3 を省く根拠に「受理集合は変わらない」を
置いたが、レンズ A の対比表が示すとおり partial write 後に例外が起きる経路では受理集合が現に
変わる (従来は切り詰め成功、変更後は rc=2)。レンズ A の「段 2・3 を省く例外はない」という主張
自体は `DW-C00` に軽量版条項が明文であるため refuted としたが、条項の適用判定を誤った点は親の
過失である。段 3 の主機能 (brief の実測値と一般化への攻撃) はレンズ A の prompt へ明示的に
負わせて実行済みで、成果物値の誤りは発見されなかったため巻き戻さず記録に留めた。

**scope 外として残した real 所見が 2 つある。** 失敗時に不完全 file が残り同じ `output_dir` の
直接再実行を `O_EXCL` が塞ぐ件は、production submit が実行ごとに新しい nonce directory を作るため
現行受理集合を変えない。同型の単発 `os.write` が `orchestrator/qualification/artifacts.py` の
`append_jsonl` と `orchestrator/campaign/wal.py` の lock preimage に残る件は、独立 2 例が揃うため
族として別タスクへ起票する。

工数は Codex 4 本 (author / fix / review 2 本、いずれも `gpt-5.6-sol`・effort=high)、
変異 4 run、焦点走 2 回。実装子と fix 子はどちらも login ノードで pytest を走らせられず
rc=16 (`qstat -Q` の socket 不可) で止まり、正しく「実装済み・未実走」と申告した。緑の判定は
すべて親が計算ノードで実走して確定した。

変異は事前登録どおり 3/3 一致した。M01 (完了保証ループを wave 前の単発 `os.write` へ戻す) は
新テスト 2 本を KILL、M02 (`written <= 0` guard の削除) は zero-write テストが KILL、
M03 (chunk 変数を挟む等価変換) は SURVIVED で過剰拒否がないことを示した。失敗 node は
いずれも期待完全集合と一致し、M03 も `injection_diff_sha256` が実在するため注入なしの
偽 SURVIVED ではない。

## 次の一手差分

### 完了

- [T-933] `_durable_json` に write 完了保証を入れ、partial write と zero write を検出する検査を
  新設した。変異 3/3 一致、受入全走で確認した。
  remaining: none
  base: 4d3817a95773dd9269cba3a04dd11848bd59eb237128fcd58521fa5e63d12b49

### 新規

- {{T:durable-write-guard-family}} **P3・新規**: `qualification/artifacts.py` の `append_jsonl` と
  `campaign/wal.py` の lock preimage に残る同型の単発 `os.write` を是正する。[T-933] と合わせて
  独立 2 例が揃ったため族として扱う。受理集合は変えず write の完了保証に限定する。
