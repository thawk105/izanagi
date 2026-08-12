# [T-940] 既知違反台帳の件数 literal 固定を外す

- 日付: 2026-08-13 (JST)
- branch: `worktree-dev-wave-t940-ledger-count`
- 編集面: `orchestrator/tests/test_check_ai_provenance.py` のみ (production・docs は無変更)
- 裁定: 2026-08-12 第 6 束「T-940 = 件数 literal 固定のみ外す (内容完全一致は保つ、
  敵対検証を受入条件)」(authority: user)

## 結論

件数の絶対値 literal 3 箇所を、期待表または台帳から導いた長さへ置き換えた。内容完全一致
(`observed == expected`)、finding 種別集合、`tuple(registry.values()) == 台帳` は逐語で保っている。
設計判断は decisions の `{{D:ledger-count-dynamic}}` (fold で採番)。

| 位置 | 変更前 | 変更後 |
|---|---|---|
| 関数名 | `test_known_violation_ledger_is_exactly_thirty_eight_literal_entries` | `test_known_violation_ledger_matches_literal_entries` |
| literal test | `assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == 38` | `assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == len(expected)` |
| literal test | `assert len({row[0] for row in expected}) == 38` | `assert len({row[0] for row in expected}) == len(expected)` |
| registry test | `assert len(registry) == 38` | `assert len(registry) == len(provenance.KNOWN_PROVENANCE_VIOLATIONS)` |

第 2 の件数 literal (registry test) は起票が名指していない。段 1 で台帳へ 39 件目を実編集で足して
計算ノードで全走し (request 908040.nqsv、2 failed / 281 passed)、実測で見つけて scope に入れた。

## 段 4 の裁定を段 6 で覆した経緯

段 2 プランと段 3 レンズ A は「`observed == expected` の tuple 比較が長さを厳密に含意する」ことを
根拠に literal test の件数 assert の**削除**を推奨し、親も段 4 でそれを採った。段 6 の敵対レビュー A が
これを反証した。

- 台帳を `tuple` 派生型にし、`len()` は正直に 39 を返しつつ `__iter__` が literal test に対してだけ
  未承認の 1 件を隠すと、削除後は内容完全一致・SHA 一意性・registry の件数と値 tuple・
  実在 35 件検査が**すべて緑**になる (レビュー A の in-memory probe による実測)。
- 含意は `observed` が台帳の**反復**から作られることに依存しており、反復が呼び手によって件数を
  変える容器では成立しない。
- これは既存の穴ではなく**本 wave の削除が開けた穴**で、受理集合を裁定の許す範囲を超えて広げる。

fix は件数 literal を戻さずに `== len(expected)` という動的な形で行い、検出力を wave 前と
入力ごとに同一へ戻した。

## T-940 の検出力主張から明示的に除外する形

本 wave が保証するのは **exact built-in 型の台帳に対する内容完全一致**である。件数が同じまま
`str` 派生型で SHA をすり替える形 (`__eq__` だけ旧 SHA に真を返す) は捕まらない。これは
`isinstance` を使う production の性質に由来し、**wave 前の `== 38` でも捕まっていない既存の穴**である。
段 3 と段 6 の敵対レンズが独立に指摘した。修復案 (容器・spec・全 5 field の exact type 固定、
test-only) はレビュー A が逐語で提示済みで、worklog の新規タスクとして起票した。

新 entry が「実在する commit で実際にその違反を持つ」ことの positive coverage が無い点
(実在検査は固定 35 件のまま) も同様に起票した。

## 変異 matrix (9/9 事前登録どおり、MISMATCH 0)

spec は実ファイルから生成し、9 変異すべての置換位置の一意性を機械検査した。runner は
`orchestrator/tests/test_check_ai_provenance.py` の dispatch 走。anchor commit は `59e806e5`。
生の spec と結果は同ディレクトリの `mutation-spec.json` / `mutation-out.json`。

| id | 変異 | 期待 | 結果 | 赤 node |
|---|---|---|---|---|
| M1 | 未承認の 39 件目を production だけへ追加 | KILLED | KILLED | literal test |
| M2 | `187fed69...` の note を 1 文字変更 | KILLED | KILLED | literal test |
| M3 | `187fed69...` の entry を削除 | KILLED | KILLED | literal test |
| M4 | 承認済み entry を production と expected へ同期追加 | SURVIVED | SURVIVED | — |
| M5 | wave 前の形へ (`== 38` を再導入) | SURVIVED | SURVIVED | — |
| M6 | `assert observed == expected` を削除 | SURVIVED | SURVIVED | — |
| M7 | 重複 SHA guard を削除 | SURVIVED | SURVIVED | — |
| M8 | 容器が `len()`=38 と偽り実体 39 件 | KILLED | KILLED | literal test, registry test |
| M9 | 容器が `len()`=39 と申告し反復は 38 件 | KILLED | KILLED | literal test, registry test |

- M1 / M2 がユーザー指定の 2 論点への実測の答えである。「件数を外したら未知 entry が緑で通る」も
  「内容一致検査が恒真」も起きない。
- M9 がレビュー A の攻撃の単純化版で、fix が戻した動的件数 assert の有効性の裏取りである。
  呼び手識別版そのもの (test にだけ隠す形) は production への注入が過剰に複雑なため本走では
  未実測で、根拠はレビュー A の in-memory probe に留まる。
- M4 の主張は「schema-valid かつ両層同期した entry 追加を過剰拒否しない」ことに限る。
  **「実在する承認済み違反であること」は M4 では証明されない** (未選択 SHA の実在性・実違反を
  検査する経路が無い)。
- M5 / M6 / M7 の SURVIVED は検出力が無いことの正直な記録であり、KILLED と偽っていない。

## 受入

`1 failed / 10239 passed / 65 skipped` (125 秒)。赤は
`orchestrator/tests/test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
の 1 件だけで、**main 由来の既知赤**である。親自身の実測による切り分け:

| commit | `validate_condition_freeze_at` |
|---|---|
| `7c9ac465` (octopus 直前の main) | GREEN |
| `d1de13ad` (親 4 つの octopus merge) | RED `PreregistrationError [octopus-merge]` |

本 wave の差分はテスト 1 file の 4 行で s8c の履歴検査に到達しない。既知赤として land してよいという
ユーザー裁定 (authority: user、2026-08-13 01:05 JST) は**本セッションで直接受け取ったものではなく**、
別 wave が残した一次控え
(`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-known-red-octopus-merge.md`) を根拠にした。

## 逐語

`verbatim/` に段 1 brief、段 2 プラン、段 3 敵対 2 レンズ、段 4 裁定、段 5 実装報告、
段 6 敵対レビュー 2 本・erratum・fix 報告を置く。
