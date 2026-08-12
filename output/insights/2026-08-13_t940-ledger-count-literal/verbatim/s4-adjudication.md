# 段 4 裁定 — [T-940] 既知違反台帳の件数 literal 固定を外す

判定日時: 2026-08-13 00:40 JST。入力: s1-brief.md、s2-plan.md、s3-lensA.md、s3-lensB4.md。

## 所見の real / refuted 裁定

| # | 所見 | 出所 | 裁定 | 採否 | scope |
|---|---|---|---|---|---|
| F1 | tuple/str の subclass で内容 oracle を欺き、未承認 entry を隠せる | A-1, B-14 (独立 2 レンズ) | **real** | 不採用 (記録・起票) | **外** |
| F2 | 通常の entry 追加・削除・順序入替え・重複は変更後も確実に赤 | A-2 | refuted | — | — |
| F3 | 内容一致検査は恒真でも到達不能でもない (`expected` は 38 要素の直書き、導出なし) | A-3 | refuted | — | — |
| F4 | `observed == expected ⇒ 長さ一致` は現行の exact built-in 前提では破れない | A-4 | refuted | — | — |
| F5 | `:1914` 削除は subclass 局面の検出を失う / plan の「置換は恒真」は言い過ぎ | A-5 | **real** | **採用** | 内 |
| F6 | 親の 39 件目実測は `observed == expected` の発火を実測していない (件数 assert で先に停止) | A-7 | **real** | **採用** (段 6 変異で実測) | 内 |
| F7 | (P1) `:1914` を scope に含めるのは裁定の拡大解釈ではない | B-4 | refuted (親案を支持) | **採用** | 内 |
| F8 | brief と plan が `:1914` で不一致 (置換 vs 削除) | B-5 | **real** | **採用** (下記 D2 で確定) | 内 |
| F9 | 改名で active な mutation spec の期待 node が壊れうる | B-6 | **real** | **採用** (本 wave の spec は新名で書く) | 内 |
| F10 | 変異登録が 3 件だけで (a)(b)(e) が未登録 | B-7 | **real** | **採用** | 内 |
| F11 | (a) 件数 literal 再導入は SURVIVED、(b) 内容 assert 削除も SURVIVED、(e) guard 削除単独も SURVIVED | B-8, B-9, B-12 | **real** | **採用** (正直に control として登録) | 内 |
| F12 | (d) note 変更は対象 SHA 次第で node 数が変わる (`3f2c...` は stdout も pin) | B-11 | **real** | **採用** (対象を `187fed...` に固定) | 内 |
| F13 | 新 entry の「実在違反であること」を検査する positive coverage が無い (固定 35 件のまま) | B-1 | **real** | 不採用 (記録・起票) | **外** |
| F14 | 他 file (`test_dev_wave_land.py` / `test_hooks.py` / `test_check_docs.py` / docs) と stdout に件数 pin は無い | B-3 | refuted | — | — |
| F15 | 「更新面は expected 表だけ」は test 側限定でのみ成立 (production 台帳への追加は当然必要) | B-13 | **real** | **採用** (記録の文言を限定) | 内 |

## 確定裁定 (プラン v2)

対象は `orchestrator/tests/test_check_ai_provenance.py` のみ。
production (`tools/check_ai_provenance.py`) と docs は **1 bit も変えない**。

- **D1** 改名: `test_known_violation_ledger_is_exactly_thirty_eight_literal_entries`
  → `test_known_violation_ledger_matches_literal_entries` (:1328)。
- **D2** `:1448` の `assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38` を**削除**する。
  直後の `observed == expected` が長さを厳密に含意する (A-4 が反証を試みて破れなかった)。
- **D3** `:1450` の `assert len({row[0] for row in expected}) == 38` を
  `== len(expected)` にする。重複 SHA 検査を件数 literal 無しで維持する。
- **D4** `:1914` の `assert len(registry) == 38` は **削除せず**
  `assert len(registry) == len(provenance.KNOWN_PROVENANCE_VIOLATIONS)` へ**置換**する。
  - plan は削除を推奨したが不採用。理由: 現行の `== 38` は「`__len__` が 38 と偽り、
    checker には 39 件目を渡す」型 (F1 の局面) を**今日は捕まえている** — registry が 39 になるため。
    削除するとこの検出を失い、受理集合が裁定の許す範囲 (承認済み entry の件数変化) を超えて広がる。
    置換なら件数 literal を外したうえで検出を完全に保つ。
  - 正直な限定: exact built-in 型かつ重複 guard が生きている通常局面では、この assert は直後の
    `tuple(registry.values()) == KNOWN_PROVENANCE_VIOLATIONS` に含意され発火しない。
    価値があるのは `__len__` を偽る型が入った局面だけである (A-5 の実測に基づく)。
- **D5** `observed == expected`、`_LEDGER_FINDING_KINDS`、`_NOTE_REQUIRED_FINDING_KINDS` の
  assert は**逐語で保つ**。

## scope 外と裁定した real 所見 (ユーザーへ返す裁定パッケージ候補)

- **F1 (subclass による内容 oracle 回避)**: 本 wave では実装しない。
  - 理由 (1) 本 wave が作った穴ではなく、現行 production が `isinstance` を使っていることに由来する
    既存の穴である。(2) 成立には production を書き換える攻撃者が要り、その攻撃者は test も
    書き換えられる (脅威モデル外)。(3) D4 により本 wave で**現行の検出力は 1 つも失われない**ため、
    裁定の履行に F1 の修復は要らない。(4) 防御的堅牢化は既定で見送るというユーザーの方針。
  - **したがって T-940 の検出力主張から F1 を明示的に除外する** — 本 wave が保証するのは
    「exact built-in 型の台帳に対する内容完全一致」であり、多相型に対する保証ではない。
  - 起票候補: 「台帳の容器・spec・全 5 field の exact type を literal oracle 直前で固定する」
    (test-only、A-1 が逐語案を提示済み)。
- **F13 (新 entry の実在違反 positive coverage)**: 本 wave では実装しない。
  起票候補: 「production 台帳の各 SHA を個別に `_audit_history([sha])` へ通す独立 positive test」。

## 変異事前登録 (DW-M01)

対象 node 名は**改名後**の名前で書く (F9)。単一理由性は「赤理由が 1 つ」で判定し、
検出層が複数あることは理由の分散と見なさない。

| id | 層 | 変異 | category | 期待 | 期待 node | 単一理由性の根拠 |
|---|---|---|---|---|---|---|
| M1 | production | 未承認の 39 件目を schema-valid・一意 SHA で追加 (expected 表は触らない) | negative | KILLED | `test_known_violation_ledger_matches_literal_entries` | 固定 35 件・固定 30 件の外の SHA なので実在検査と empty-registry には触れない (B-2)。registry 検査は valid entry を自動受理する (B-10) |
| M2 | production | `187fed69...` の note を schema-valid な 1 文字に変更 | negative | KILLED | 同上 | `187fed69...` は固定 35 件に無く、note の pin は expected 表だけ (実測: test 内の出現は :1443 のみ) |
| M3 | production | `187fed69...` の entry を 1 件削除 | negative | KILLED | 同上 | 同上。削除後も registry と台帳は同数なので `:1914` は発火しない |
| M4 | 両層 | 承認済み entry 1 件を production と expected の**両方**へ追加 | positive | SURVIVED (全緑) | — | 本 wave の目的そのもの。DW-M01 が要求する「承認外の過剰拒否を検出する正例」。wave 前の形では同じ変異が 2 node で KILLED になることを親が段 1 で実測済み |
| M5 | test | wave 前の形へ戻す: `assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38` を再導入 | positive control | SURVIVED | — | production が 38 件のままなら真。source-contract 検査は存在しない (B-8)。**wave 前の実コードの形を matrix に含めるための登録** |
| M6 | test | `assert observed == expected` を削除 | positive control | SURVIVED | — | test 自身の弱体化を検出する別層は無い (B-9)。恒真性の主張ではなく「test 層の変異は自己検出されない」ことの正直な記録 |
| M7 | production | `_known_violation_registry` の重複 SHA guard を削除 | positive control | SURVIVED | — | 現 38 件が一意なので重複データを同時に注入しない限り観測できない (B-12)。guard 削除と重複注入を 1 変異にまとめない |
| M8 | production | 台帳を `__len__` が 38 を返す tuple 派生型にし、実体には 39 件目を持たせる | negative | KILLED | `test_known_violation_ledger_matches_literal_entries`, `test_production_registry_notes_satisfy_descriptive_contract` | 赤理由は 1 つ (台帳が実は 39 件)。検出層が 2 つあるだけ。**D4 の置換が発火することの実測**。A-1 の呼び手識別型 (test にだけ隠す形) は production への実装が 1 変異に収まらないため未登録 — この局面の根拠は A-1 の in-memory probe に留まる |

M1〜M3 は F6 (親の実測が `observed == expected` の発火を未実測) を埋める実測でもある。

## 分割方針 (段 5・6)

実装面は 1 file 4 箇所と小さいので Codex 実装子 1 本。段 6 は敵対レビュー 2 本 + fix、
変異 matrix (M1〜M8)、受入全走。受入 lease を `tools/dev_wave_wait.py acceptance` で claim してから投入する。
