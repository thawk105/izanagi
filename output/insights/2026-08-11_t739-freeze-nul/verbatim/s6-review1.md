静的検査のみ実施し、pytest は実行していない。親提示の `231 passed / rc=0` は前提事実として扱った。

## 所見

- **real / must-fix — 幅広 JSON で走査 stack が大幅にメモリ増幅する** — `orchestrator/campaign/s8c_preregistration.py:350-360,367,1745` — `_canonical_bytes` が成功する平坦な巨大 list でも、`list(enumerate(node))` と全 sibling の pending tuple・完全 pointer 文字列が同時に生き、入力 O(n) に対して追加メモリが O(n log n) になり得るため、NUL-free/schema-invalid 入力の実効受理集合が MemoryError・長時間停止で縮み、凍結台帳を発行できず、履歴検証・activation report・certified 選択も値を返さなくなる。
- **refuted / nit — JSON 位置の走査漏れ** — `orchestrator/campaign/s8c_preregistration.py:350-360` — canonicalization に成功した JSON の dict/list は全子孫へ到達し、`path` 値が非 str ならその値自体は許可しつつ、値が dict/list なら内部の exact `path` も走査するため、受理集合・hash・凍結参照に抜けはない。
- **refuted / nit — 文書順ではない違反が報告される疑い** — `orchestrator/campaign/s8c_preregistration.py:352-360` — dict/list の子を逆順に push して LIFO の `pop()` で先頭から深さ優先処理するため、最初の子の全子孫が次の sibling より先に検査され、文書順で最初の違反 pointer・reason が選ばれる。
- **real / nit — detail は厳密な JSON Pointer ではない** — `orchestrator/campaign/s8c_preregistration.py:357` — attacker-controlled key の `~` と `/` を `~0`・`~1` に escape しないため、`{"a/b":{"path":"…NUL…"}}` と `{"a":{"b":{"path":"…NUL…"}}}` の参照表示が衝突し得るが、変わるのは例外 detail の位置参照だけで、拒否、reason、hash、台帳、report の受理集合は変わらない。
- **refuted / nit — pointer 経由の生 NUL 漏洩** — `orchestrator/campaign/s8c_preregistration.py:354,357` — key 名に NUL・CR・LF・空文字等が含まれても、完成した pointer 全体を `repr()` してから例外 detail に渡すため、生 NUL は message に入らず、成果物の値・受理集合・参照に漏洩はない。
- **refuted / nit — NUL hash の凍結記録・certified proof chain への迂回** — `orchestrator/campaign/s8c_preregistration.py:1432-1440,1733-1757` — 発行は hash 計算後にのみ `_record_document` へ進み、履歴検証は freeze が存在する全祖先で契約 hash を再計算するため迂回はない；`s8c_preregistration_evidence.py:687-696` の raw blob hash は拒否 report の診断 evidence にだけ残り、loader と freeze validation が失敗するので effective capability や certified 選択には入らない。
- **refuted / nit — 裁定外の過剰拒否** — `orchestrator/campaign/s8c_preregistration.py:353-370` — 拒否条件は exact `path` edge・str 値・NUL の三条件だけであり、path の CR/LF、非-path field の NUL、NUL-free schema 違反、`{"predicates":[]}` は従来どおり hash まで到達するため、成果物の受理集合は裁定 §2.2 どおりである。
- **refuted / nit — 深い JSON に helper 固有の非停止が加わる疑い** — `orchestrator/campaign/s8c_preregistration.py:300-307,366-370` — 深さ限界に達する入力は再帰的な `_canonical_bytes` が helper より先に倒れ、helper 自身は有限 JSON に対する反復走査なので新たな無限ループはない；ただし幅広入力の新規メモリ問題は第一所見のとおり残る。
- **refuted / nit — 既存 hash・pin・reason 順序の回帰** — `orchestrator/campaign/s8c_preregistration.py:363-371`、`orchestrator/campaign/s8c_preregistration_evidence.py:180-191,269-272` — domain/canonical bytes は変更されず検査は canonicalization 後なので現行契約 hash と g1 の `evidence_contract_sha256` / `protected_sha256` は不変、`semantic_contract_sha256` は従来どおり schema loader を先に通すため reason 順序も不変である；core blob hash と activation-report digest だけは実装 byte 変更に伴い意図どおり変わる。

## 総括

1. must-fix: 幅広 JSON に対する全 sibling 一括 materialize と pending 積載を、文書順と NUL-only の受理集合を保ったまま深さ比例メモリの走査へ直す必要がある。
2. nit: JSON Pointer の `~`・`/` escape 欠落。その他の疑いは静的に refuted。
3. **NO-GO** — fail-closed の発行・履歴検証・report 経路に、canonicalization を通過する入力で新規の資源枯渇面が残る。
