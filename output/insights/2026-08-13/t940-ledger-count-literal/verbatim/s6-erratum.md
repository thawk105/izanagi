# 段 6 erratum — 段 4 裁定 D2 の訂正と変異事前登録の再確定

作成: 2026-08-13 01:35 JST。入力: s6-reviewA.md、s6-reviewB.md。
段 4 (s4-adjudication.md) を上書きする差分だけを書く。触れていない項は段 4 のまま有効。

## 訂正 1 — D2 を「削除」から「動的置換」へ (レビュー A の real 所見)

### 何が誤っていたか

段 4 の D2 は `assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38` を**削除**すると裁定し、
根拠を「直後の `observed == expected` が長さを厳密に含意する」に置いた。段 2 プランと段 3 レンズ A の
所見 A-4 もこの含意を支持していた。**しかしこの含意は `observed` が台帳の反復から作られることに
依存しており、反復が呼び手によって件数を変える容器では成立しない。**

段 6 レビュー A が具体形を実測した (書込みなし in-memory probe):

- 台帳を `tuple` 派生型にし、**`len()` は正直に 39 を返す**。
- `__iter__` は literal test から呼ばれたときだけ未承認の 1 件を隠し、checker には 39 件すべて返す。
- 変更後は `observed == expected`・SHA 一意性・`len(registry) == len(台帳)`・
  `tuple(registry.values()) == 台帳`・実在 35 件検査が**すべて緑**。
- 削除した `assert len(...) == 38` だけが `39 == 38` で赤になっていた。

これは既存の穴ではなく**本 wave の削除が開けた穴**であり、受理集合を
「承認済み entry の件数変化」を超えて広げる。ユーザー裁定に反するため修正は必須。

### 訂正後の D2 (= D2')

`:1448` を**削除せず置換**する。

- 変更前: `    assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38`
- 変更後: `    assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == len(expected)`

D3 (`len({row[0] for row in expected}) == len(expected)`) と同型の変換であり、件数 literal は残らない。
`expected` は承認時にどのみち更新するので、承認済み entry 追加の更新面は `expected` 表 1 箇所のまま。
**検出力は wave 前と入力ごとに完全に同一**になる (旧 `== 38` と新 `== len(expected)` は
`expected` が 38 要素である限り同値)。

### レビュー A が提案した exact-type 固定は採らない

レビュー A は `type(KNOWN_PROVENANCE_VIOLATIONS) is tuple` と全 field の exact type 固定を提案した。
D2' はレビュー A が実測した攻撃を型検査なしで捕まえるため、型固定は本 wave に不要である。
段 4 の F1 裁定 (scope 外・起票候補) を維持する — 型固定でしか捕まらないのは
「件数が同じまま `str` 派生型で SHA を別物にすり替える」形で、これは wave 前の `== 38` でも
捕まっていなかった**純粋に既存の**穴である。**T-940 の検出力主張からはこの形を引き続き除外する。**

## 訂正 2 — 変異事前登録の再確定 (レビュー B の real 所見)

### 単一理由性の解釈 (レビュー B の所見 1 への裁定: refuted)

レビュー B は「LIT と REG の 2 node が赤になる M8 は DW-M01 違反」と判定した。**不採用。**
本 repo には先行判断がある — `output/insights/2026-08-07_t618-known-violation-ledger/s4-adjudication.md`
の M1 は、赤理由が「entry 不在」の 1 つで node が 4 本になった事例を
「node が 4 本になるのは検出層が 4 つあるためで、理由の分散ではない」として全 node を登録している。
DW-M01 の要求は「無効化時の赤理由が一つに絞れること」であり、検出層の数ではない。
したがって多層で赤くなる変異は、赤理由が 1 つなら期待 node を完全集合として登録する。

### exact payload / anchor の固定 (レビュー B の所見 2・DW-M04 への裁定: 採用)

M1・M4・M8・M9 の exact SHA・entry 内容・置換 anchor を spec 生成時に固定する。
- 混入・追加する SHA は 40 桁小文字 hex、既存 38 件と非重複、固定 35 件 (:1458 起点)・
  固定 30 件 (:2529 起点)・stdout pin (:2629 起点) のいずれにも含まれないものを使う。
- kind は `missing-codex-author` (note の記述性検査は `malformed-ai-agent` 専用のため先取りしない)、
  `expected_finding_value` は空文字 (非 malformed では空必須)。
- M4 の `expected` 側 anchor は末尾 SHA 単独にしない (3 箇所一致で harness が停止する)。
  行全体と直後の tuple 閉じを含む文脈で一意化する。

### M4 の主張の限定 (レビュー B の所見 3 への裁定: 採用)

M4 が示すのは「schema-valid かつ両層同期した entry 追加を過剰拒否しない」ことだけである。
**「実在する承認済み違反であること」は M4 では証明されない** (未選択 SHA の実在性・実違反を
検査する経路が無い)。この限定を記録へ明記する。実在性の coverage 追加は段 4 の F13 のまま scope 外。

### 再確定した変異 matrix

`LIT` = `orchestrator/tests/test_check_ai_provenance.py::test_known_violation_ledger_matches_literal_entries`
`REG` = `orchestrator/tests/test_check_ai_provenance.py::test_production_registry_notes_satisfy_descriptive_contract`

| id | 層 | 変異 | category | 期待 | 期待 node | 根拠 |
|---|---|---|---|---|---|---|
| M1 | production | 未承認の 39 件目 (固定 payload) を追加 | negative | KILLED | LIT | 反復が 39 件を見るので長さ・内容の両 assert が赤。選択集合外なので stale は発火しない |
| M2 | production | `187fed69...` の note を schema-valid な 1 文字に変更 | negative | KILLED | LIT | 当該 SHA の note pin は expected 表のみ。`missing-codex-author` は記述性検査の対象外 |
| M3 | production | `187fed69...` の entry を削除 | negative | KILLED | LIT | 削除後も registry と台帳は同数なので REG は発火しない |
| M4 | 両層 | 承認済み entry 1 件を production と expected へ同期追加 | positive | SURVIVED | — | 裁定の目的。**主張は schema/件数の受理に限定** |
| M5 | test | wave 前の形へ: `assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38` を再導入 | positive control | SURVIVED | — | production が 38 件なら真。source-contract 検査は存在しない |
| M6 | test | `assert observed == expected` を削除 | positive control | SURVIVED | — | test 層の弱体化を検出する別層は無い (正直な記録) |
| M7 | production | 重複 SHA guard を削除 | positive control | SURVIVED | — | 現 38 件が一意なので重複データを同時注入しない限り観測不能 |
| M8 | production | 台帳を `__len__` が 38 を返す tuple 派生型にし実体に 39 件目を持たせる | negative | KILLED | LIT, REG | 赤理由は 1 つ (台帳が実は 39 件)。**D4 が単独で発火することの実測** |
| M9 | production | 台帳を `len()` が 39 を返す tuple 派生型にし反復では 38 件しか返さない | negative | KILLED | LIT, REG | 赤理由は 1 つ (容器の申告と反復が食い違う)。**D2' が単独で発火することの実測** — レビュー A の攻撃の単純化版。呼び手識別版 (test にだけ隠す形) は同じ `len` assert が捕まえる (A の probe が実測) |

M9 について: レビュー A の攻撃は `__iter__` が呼び手を見る形だった。呼び手識別を production へ
注入するのは変異として過剰に複雑なので、同じ assert が捕まえる単純化版で実測する。
呼び手識別版そのものの根拠はレビュー A の in-memory probe に留まる (本走では未実測) と明記する。

## fix の scope

`orchestrator/tests/test_check_ai_provenance.py` の 1 行だけ (D2')。
production と docs は引き続き 1 bit も変えない。
