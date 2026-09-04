---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-05
wave: dev-wave-t2298-certified-evidence-lock
seq: 2
---

## {{D:certified-evidence-rw-lock}}. certified_evidence の排他は fixture 自前の flock を seed 排他・読み手共有・書き手排他に分け、real-repo 資源 lock を流用しない

**決定:** `orchestrator/tests/test_p3_b4_raw_record_producer.py` の `certified_evidence` は、共有 seed の生成だけ
`LOCK_EX` (取得後の再確認付き、完了印 `evidence.json` は temp + fsync + `os.replace` で公開) を取り、
生成後は明示的に解放して、読み手は `LOCK_SH`、書き手は `LOCK_EX` を test 本体の間だけ保持する。
書き手は共有 seed を一時的に変える consumer だけで、別 fixture `certified_evidence_writer` を引数に取る
(現物では M17 と M18 の 2 本)。lock file は fixture 自前の `fixture.lock` のままとし、`real_repo_fixture_lock`
(`parent` / `ccbench` の git common-dir に束縛された資源 lock) は流用しない。

**決定 2:** lock の意味論は実 fixture scope で正例・負例を検査する。読み手保持中は競合の `LOCK_SH|LOCK_NB` が成功し
`LOCK_EX|LOCK_NB` が失敗すること、書き手保持中は `LOCK_SH|LOCK_NB` が失敗すること、seed 済みの読み手が `LOCK_EX` を
要求しないこと、共通 scope が mode を転送し yield が lock の内側にあること (AST)、書き手宣言の集合が対象 file 内の
直接 path mutation の閉包と一致すること (AST、helper 内の書込みは対象外と明記)。

**理由:**
- D1594 (排他は lock で行い、読み書きを区別する) の本 fixture への適用。旧実装は `yield` が `flock(LOCK_EX)` の
  内側にあり、読み取り専用の consumer 15 本まで直列化していた。
- `real_repo_fixture_lock` は git 資源の identity (common-dir digest) を key にする別資源の lock で、流用すると
  b4 evidence の書き手が real-repo の読み手・書き手を止め、逆も起きる。資源を取り違えた排他は過剰直列化であり、
  別資源を同一排他領域と誤表現する。resource を足す一般化は conftest の inventory・root 解決・key 生成・取得順・
  fixture context の 5 面に及び、本件の局所改修ではない。
- 書き手を marker でなく別 fixture にしたのは、宣言が関数引数として静的に見え、閉包検査が fixture 名を起点にできる
  ためである。`pytest.ini` の marker 登録も要らない。
- 完了印を transactional にしたのは、部分書込みの `evidence.json` を後続 worker が「seed 済み」と誤認して壊れた
  JSON を読む経路を塞ぐため (段 3 レンズ A)。実 fixture scope で mode を識別する検査を足したのは、共通 scope が mode を
  定数化する退行が helper 単体の正負例では緑のまま通るため (段 6 レンズ C・D が独立に指摘)。

**却下した選択肢:**
- `real_repo_fixture_lock` の流用 — 上記のとおり資源の取り違え。
- marker による書き手宣言 — 動作は同じだが閉包検査が文字列照合になり、strict marker の登録も要る。
- `LOCK_EX` から `LOCK_SH` への直接変換 — Linux flock の mode 変換は原子的な downgrade ではなく、解放と再取得の
  非原子区間を隠す。明示的に `LOCK_UN` → 再取得とし、区間中は metadata を読まない。

**射程と非保証:** worker が SIGKILL された場合、kernel は lock を解放するが書き手の `finally` による復元は走らない。
これは旧実装からの既知限界で、本決定は解消しない。閉包検査は対象 test file 内の直接 path mutation に限り、helper 内の
書込みや `joinpath` / `resolve` 経由の派生 path は追わない (現 15 読み手に該当は無い)。
