## M12 の実効性

- 第1段は実物の `P._fraction_token((1, 3))` を直接呼んでいる。stub、複製実装、registry は介在しない。`test_p3_b4_raw_record_producer.py:1143-1145`
- production の `if denominator != 1` を削除すると、`1/3` は `exponent == 0`、`scaled == 0` となり整数 `0` を返すため、`pytest.raises(ArithmeticError)` が確実に落ちる。`p3_b4_raw_record_producer.py:353-368`
- 第2段の publication は全行 `(100001 + 10*i, 10)` であり、既約分母は常に 10。非有限十進は含まれず、registry の新検査で先に落ちない。`test_p3_b4_raw_record_producer.py:115-125`
- `_publish` は実物の `publish_b4_attempt_result` を呼び、現行 production は `_derive_b4_attempt_data` 内で `_fraction_token` を呼ぶ。`test_p3_b4_raw_record_producer.py:780-793`、`p3_b4_raw_record_producer.py:1739-1747`、`:1541-1549`
- `except ArithmeticError` の写像を削除すると、外側の一般例外処理による `IO_ERROR` などになり、期待する issue 全項目との一致が確実に落ちる。`test_p3_b4_raw_record_producer.py:1157-1165`
- ただし、旧 M12 の unpatched control publication は消え、patched mock の呼出し回数も検査していない。呼出し行を `raise ArithmeticError` に置換する単一変異では、mock が一度も使われないまま両段が緑になる。したがって「publish が本当に `_fraction_token` を呼ぶ」という保証は弱くなっている。

## 述語の正しさ

`reference is not None` の guard は型・正値検査の直後にあり、位置は正しい。非 `SCHEDULED` の `None` は述語を通らず保存され、`SCHEDULED` の不完全な `None` は従来どおり後段で拒否される。`p3_b4_analysis_ledgers.py:341-366`

正の exact rational を `Fraction` に正規化した後の分母については、registry と producer の有限十進判定は同じ集合、すなわち既約分母の素因数が 2 と 5 だけの集合を切る。`p3_b4_analysis_ledgers.py:344-351`、`p3_b4_raw_record_producer.py:350-359`

| 入力 | registry | producer 直接呼出し | 判定 |
|---|---|---|---|
| `(1, 3)` | 新 message で拒否 | `ArithmeticError` | 一致 |
| `(1, -2)` | 正値検査で拒否 | 正値検査で拒否 | 一致 |
| `(-1, -2)` | `1/2` に正規化して受理 | `1/2` として受理 | 一致 |
| `Fraction(1, 2)` | 受理して `(1, 2)` に正規化 | tuple でないため拒否 | 表現域は不一致。ただし実経路では registry が tuple 化する |
| `1` | 受理して `(1, 1)` に正規化 | tuple でないため拒否 | 同上 |
| `True` / `(True, 1)` | exact-type 検査で拒否 | exact-type 検査で拒否 | 一致 |
| `(1, 2**6200)` | 有限十進として受理 | 分母判定後、標準の整数文字列桁数上限では `str` が失敗 | 既知の操作上の残差、裁定どおり scope 外 |

`Fraction` と `int` の直接入力差は、`_normalize_attempts` が accepted reference を canonical tuple にするため、実際の publication には伝播しない。`p3_b4_analysis_ledgers.py:447-466`

恒真・恒偽になる意図外の型はない。正の `int` は分母 1 なので常に通り、`None` は意図的に bypass する。bool やその他の不正型は新述語より前に拒否される。

## テストの強度

- `(1, 10)` 正例は `_seal` の receipt hash 計算から実述語を通る。述語を恒偽化、または 2・5 の除去を削除すると例外になり確実に赤になる。`test_p3_b4_analysis_ledgers.py:158-163`
- `None` 正例は guard を削除すると `reference.denominator` 参照で失敗するため、過剰拒否を確実に検出する。`:166-180`
- `(1, 3)` と `(1, 30)` は述語を恒真化すると `scheduled_attempts_sha256` が正常終了し、`pytest.raises` が確実に赤になる。`:183-197`
- `(1, 30)` は実物の `_ratio_from_payload([1, 30]) == (1, 30)` を先に固定している。既存の not-reduced 検査を通過し、新検査だけが拒否することを示している。`:191`
- 追加された期待値に working-tree hash、時刻、絶対 path はない。ledger fixture の hash は固定 label から生成される。`:19-20`
- M12 の `certified_evidence` は一時 repository を構築する既存 fixture であり、現行 worktree の commit hash を期待値へ差し込んでいない。`test_p3_b4_raw_record_producer.py:813-845`
- ledger 検査は実 module の seal/hash/codec を名指しする。M12 第1段も実 helper を名指ししており、両層 stub で緑になる形ではない。ただし第2段の mock 呼出し未確認は所見一覧の must-fix に該当する。

pytest は依頼どおり実走していない。

## 裁定からの逸脱

HEAD `3be06d9ff` は clean で、`git show HEAD --stat` の変更は次の3ファイルだけだった。

- `orchestrator/campaign/p3_b4_analysis_ledgers.py`
- `orchestrator/tests/test_p3_b4_analysis_ledgers.py`
- `orchestrator/tests/test_p3_b4_raw_record_producer.py`

個別確認結果:

- `p3_b4_analysis_contract.py` と `as_b4_exact_fraction` は変更なし。現物は `:233`。
- `p3_b4_analysis_adapter.py` は変更なし。
- `_attempt_is_eligible` は変更なし。`p3_b4_analysis_ledgers.py:922`
- `generate_analysis_manifest` 本体は変更なし。`:1050`
- `_ratio_payload`、`_ratio_from_payload`、`_manifest_row_payload` は変更なし。`:279`、`:288`、`:939`
- `_exact_ratio` は変更なし。`:263`
- 事前登録 §5.1.1 の文書は変更なし。`docs/phase3-b4-reflux-ablation-preregistration.md:257`
- production の `p3_b4_raw_record_producer.py` は変更なし。変更されたのは test file のみ。
- `orchestrator/tests/acceptance_duration_ledger.json` は変更なし。
- ledger production 差分は `_validate_attempt` の8行だけで、巨大な有限十進向けの桁数上限は追加されていない。`p3_b4_analysis_ledgers.py:344-351`

裁定の「変更しない」一覧からの逸脱はない。

## 所見一覧

- **must-fix / real — M12 第2段は monkeypatch の実効発火を固定していない。**
  `mock.patch.object` を変数として保持せず、呼出し assertion がない。`_fraction_token(...)` の呼出しを `raise ArithmeticError` に置換する変異は、実 helperを呼ばずにM12を通過する。[test_p3_b4_raw_record_producer.py:1148](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/tests/test_p3_b4_raw_record_producer.py:1148)、[p3_b4_raw_record_producer.py:1542](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2102-b4-reference-tps-domain/orchestrator/campaign/p3_b4_raw_record_producer.py:1542)
  **成果物影響:** この退行を放置すると有限十進 publication まで named rejection になり、raw attempt artifact が作られず、certified 選択と report の参照が欠落しうる。

- **nit / refuted — registry の有限十進述語が producer と異なる数値集合を切る。**
  正規化後の正の有理数について分母判定は一致する。`Fraction` と `int` の直接入力差は registry の canonical tuple 化で閉じる。`p3_b4_analysis_ledgers.py:263-275,344-351,455-466`
  **成果物影響:** なし。実 publication に異なる表現は到達しない。

- **nit / refuted — `(1, 30)` が既存の not-reduced 検査で落ちている。**
  実 codec の成功を先に assertion しており、新述語だけの発火を固定している。`test_p3_b4_analysis_ledgers.py:191-197`
  **成果物影響:** なし。負例は意図した registry admission の縮小を検査している。

- **nit / refuted — 裁定外の production、文書、台帳が変更された。**
  HEAD の変更対象は指定された3ファイルだけで、production producer や acceptance duration ledger は含まれない。
  **成果物影響:** なし。certified 選択規則、report 契約、既存台帳 bytes に変更はない。

## 総括

M12 の名指し2変異、registry 述語、追加 ledger 検査は静的には意図どおり機能する。
registry の有限十進判定は、canonical な正の有理数について producer と一致する。
裁定の「変更しない」対象と巨大値 scope からの逸脱はない。
ただし M12 は旧 control を失い、mock の実効呼出しも固定していないため、call-site 変異が生存する。
結論は must-fix 1件。pytest は実走していない。