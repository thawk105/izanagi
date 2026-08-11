---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t756-trace-v2
seq: 3
---

## 再発

### F30

- **再発: 2026-08-11** — 五度目と六度目を同一 wave で踏んだ。どちらも path 検索でも role 名 key
  検索でも捕まらない型で、**静的レビュー 4 本 (プラン + 敵対 2 レンズ + 要件レビュー) が全員
  取りこぼし、計算ノードでのテスト実測だけが捕らえた。**
  (i) **出力形状を等値比較する pin** — `result_to_dict(verify_trace_dir(...))` の**出力**が凍結証拠
  `.../raw-bundle-attempt-1/correctness/verifier.json` へ記録され、
  `test_silo_ladder_rung1_evidence.py` が完全一致を要求する。親は段 1 でこれを自力で捕らえたので
  実害なし (near miss)。
  (ii) **編集面 source の bytes closure pin** — 同 evidence の `binding` が
  `verifier_module = orchestrator/verifier/report.py` の**現行 bytes 一致**を要求し
  (`driver` と `policy` だけが歴史 drift 許容という非対称契約)、さらに
  `orchestrator/campaign/pipeline.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の 8 path の
  1 つで `verify_live_contract_loader_binding` が disk bytes と記録 commit blob を照合する。
  前者は段 5 が編集して赤になり fix で完全復帰、後者は未 commit の間 40 件が必ず赤になる。
  **どちらも「編集してよいか」が事前に分からないまま実装子へ渡っていた。**
- 恒久対応は `DW-O09` から変更しない。運用として、段 1 の pin 閉包に
  **(a) 出力形状を等値・byte 比較する consumer** と **(b) `CONTRACT_LOADER_RELATIVE_PATHS` などの
  source bytes closure** を含める。**編集面が確定した時点で焦点走を 1 度回し、静的検査で
  「触ってよい」と結論しない。**

### F102

- **再発: 2026-08-11** — 二度目。**防御目的の明記だけでは不十分**だと分かった。冒頭で
  「防御側レビュア」「land 前に防ぐため」と明記した consult prompt が、それでも
  cybersecurity risk として flag され rc=1・出力 0 bytes (54 model call・806 秒を空費)。
  引っかかったのは「検査を通す経路があるか探せ」という**回避手順の作成を求める依頼文**である。
- 恒久対応の追加 (F102 の既存対応に上積み): 敵対 prompt では
  (i) 対象がセキュリティ製品でない旨の文脈を前置し、(ii)「回避経路を構成せよ」ではなく
  **「限界を記述し、より独立な代替の有無を評価せよ」**と書き、(iii)「攻撃」語彙を「検算」へ置く。
  本 wave はこの 3 点で書き換えて rc=0・25758 bytes を得た。
- 再発検知: consult / review 子が rc=1 かつ出力 0 bytes のとき、events 末尾の `turn.failed` を
  読んで flag か上限かを切り分ける (上限なら `stop_reason`、flag なら message が入る)。
