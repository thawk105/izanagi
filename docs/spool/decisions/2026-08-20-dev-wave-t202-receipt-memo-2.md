---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t202-receipt-memo
seq: 2
---

## {{D:receipt-memo-nonce-json}}. receipt memo の cache は controller nonce 付き path + closed-schema JSON とする

**決定:** `orchestrator/tests/real_repo_receipt_memo.py` の xdist session cache は、
(1) cache path に UID hash・HEAD に加えて controller 限定で生成する session nonce
(既存 `_RECEIPT_MEMO_SESSION_ID_ATTR`、新設 `pytest_configure_node` フックで
`workerinput` 経由 worker へ伝播) を混ぜ、(2) 直列化形式を pickle から closed-schema
JSON (許容キー完全一致、`object_pairs_hook` で重複key拒否、`parse_constant` で
NaN/Infinity拒否、schema検証を終えてからのみ `ReceiptResolution` を構築) へ置き換える。
読込・書込の両方に bytes 上限 (8 MiB) を設ける。

nonce は cache **path** にのみ埋め込み、JSON **内容**とのbinding検証はしない。閉じるのは
「呼出し側が `--testrunuid` を固定して未来の cache path を事前予測する」攻撃と
「pickle 経由の任意コード実行」の2つに限定する。同一ホストの別ローカルユーザーが
in-flight の nonce を観測してから同じ path へ偽 payload を置く race は対象外とする
(現行設計が元々前提にしている shared `/tmp` の信頼境界の延長であり、本決定が新たに
持ち込む縮小ではない)。リモート分散 xdist (worker が別ホストで `/tmp` を共有しない構成)
も同様に対象外とする (UID+HEADのみだった旧設計も同じ前提を置いていた)。

**理由:**
- D518 の barrier 位置 (`pytest_xdist_node_collection_finished`/`pytest_collection_finish`)
  と UID charset 非拒否は変更しない制約のもとで、`--testrunuid` を呼出し側が固定できる
  ([T-202] 原文) ことへの対処は、UID そのものではなく **controller だけが知りうる
  非再利用な値**を鍵に混ぜることでしか解けない。xdist 3.8.0 の `pytest_configure_node`
  (`xdist/newhooks.py`) と `workerinput` 伝播 (`xdist/workermanage.py`, `xdist/remote.py`)
  は、worker 起動 (`pytest_sessionstart`) が controller の `pytest_configure` より後に
  発火するという既存の D518 記述と整合する経路として実在を確認した。
- pickle の deserialize は型検査の位置に関わらず任意コード実行を持つ。JSON へ切り替えれば
  「デシリアライズ自体は安全、構造検証してから信頼する」という設計にできる。
  `object_pairs_hook`/`parse_constant` を欠くと重複key・NaN/Infinity という別の穴が残る
  ([T-202] 原文の想定を段3敵対相談が具体化した)。

**却下した選択肢:**
- session 終了時に cache file を削除する — 異常終了時に残留し、worker の読取完了との
  race を持つ (段3敵対相談レンズB)。nonce 方式は別 invocation を別 namespace に分離する
  だけで、この race を新たに悪化させない。
- nonce を JSON 内容にも bind する認証機構を追加する — 段4 で意図的に scope 外とした
  (前述の「対象外」)。閉じたい脅威 (path 事前予測、任意コード実行) に対して不要な複雑化。
- `parse_constant` 除去を独立した変異として登録する — `_is_json_tree()` の finite 検査が
  全ネスト値に対し常に冗長に効くため、単一理由の変異にならないと段6敵対レビューが判定した
  (コードは defense-in-depth として維持)。
