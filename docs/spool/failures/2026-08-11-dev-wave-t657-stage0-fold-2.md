---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t657-stage0-fold
seq: 2
---

## 再発

### F102

- **再発: 2026-08-11** — 焦点再レビュー 3 巡目の初回が
  `This content was flagged for possible cybersecurity risk` で rc=1・出力 0 bytes になった
  (31 model call・486 秒を空費)。冒頭に防御目的は書いていたが、点検項目に
  「この 1 行を足せば通る形の decoy を 1 つでも構成できたら blocker として挙げよ」という
  攻撃者視点の指示が残っていた。**防御的 framing は冒頭だけでなく点検項目の動詞にも要る** —
  「構成せよ」でなく「取りこぼしている条件があれば指摘せよ」と書き、
  検査対象が自チームのコードであることを明示して再投入したら成功した。

### F217

- **再発: 2026-08-11** — 焦点再レビュー 1 巡目が web 検索を 4 回使い、
  `codex_exit_code=0` / 出力 8479 bytes / `## 総括` ありにもかかわらず
  `evidence_status=invalid` / `accepted=false` で不採用になった (20 model call・475 秒)。
  **F217 の恒久対応「子 prompt に web 検索禁止を明記する」がどの dispatch 節にも配線されて
  おらず、書き手の記憶に依存していた。** `DW-O05` (read-only codex) へ明記を義務として足そうと
  したが、`docs/dev-wave/**` の L1.5 予算 (9566 bytes) に余地が無く、最小の 1 行 (約 90 bytes)
  でも `check_docs` が赤になった。**予算は上げず本文編集を見送り**、候補として worklog へ
  記録した。恒久対応は現時点で memory と本エントリだけが担っており、**機械強制されていない**。
