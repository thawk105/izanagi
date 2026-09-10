# 段 1 brief — [T-940] 既知違反台帳の件数 literal 固定を外す

## 確定済みユーザー裁定 (authority: user, 2026-08-12 第 6 束)

「T-940 = 件数 literal 固定のみ外す (内容完全一致は保つ、敵対検証を受入条件)」。
受理集合を広げてよいのは**承認済み entry の件数変化のみ**。内容の一致要求は一切緩めない (規律 2)。
起票本文: docs/archive/worklog-phase3-0812-488.md の [T-940] 項。

## 親の実測 (2026-08-12 23:05 JST, worktree dev-wave-t940-ledger-count, base 2310ea67)

`tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` へ 39 件目を実編集で追加し、
`orchestrator/tests/test_check_ai_provenance.py` を計算ノード (request 908040.nqsv) で全走した。
即時復元済み (`git checkout --`、blob = HEAD:tools/check_ai_provenance.py と一致、dirty 0)。

- 結果: **2 failed, 281 passed**。赤は次の 2 node だけ。
  - `test_known_violation_ledger_is_exactly_thirty_eight_literal_entries` (:1448 `len(...) == 38`)
  - `test_production_registry_notes_satisfy_descriptive_contract` (:1914 `len(registry) == 38`)
- 起票本文が名指すのは前者だけ。**後者は起票時に見えていなかった第 2 の件数 literal** であり、
  外さなければ「承認のたびに受入が止まる」は解消しない。
- 件数を持つ site は他に無い。`:1450 len({row[0] for row in expected}) == 38` は test 自身の
  literal 表に対する重複検査で、production が増えても赤にならない (実測で無反応)。
- pin 閉包 (DW-O09): `KNOWN_PROVENANCE_VIOLATIONS` を読む python は checker と当 test file のみ
  (`grep -rn --include=*.py`)。docs / FROZEN_MANIFEST / receipt に件数 38 を pin する記述は無し
  (`grep -rn "thirty_eight|38 件|38件"` の hit は無関係な別文脈のみ)。凍結 bytes は動かない。
- 起動時確認: t904-hashobject-sep / t930-hold-no-bypass の branch diff に
  `tools/check_ai_provenance.py` / 当 test file / `docs/ai-provenance.md` は**含まれない**。衝突なし。

## scope (実装面は Codex role=author が書く。親は直接編集しない)

`orchestrator/tests/test_check_ai_provenance.py` のみ。production (`tools/check_ai_provenance.py`) は
**1 bit も変えない**。docs 変更なし。

1. 関数名から件数語を外す (改名)。
2. `:1448` の件数 assert を落とす — `observed == expected` の tuple 比較が長さを含意するため
   検出力は減らない。
3. `:1450` の `== 38` を `== len(expected)` にする (重複 SHA 検査を literal 無しで維持)。
4. `:1914` の `== 38` を `== len(provenance.KNOWN_PROVENANCE_VIOLATIONS)` にする。
5. `observed == expected` (内容完全一致) と `_LEDGER_FINDING_KINDS` /
   `_NOTE_REQUIRED_FINDING_KINDS` の集合 assert は**逐語で保つ**。

## 不変条件

- 未知 entry が production 台帳へ 1 件混入したら、変更後も必ず赤になる。
- 既存 entry の内容 (commit / kind / ruling / note / value) が 1 文字でも変われば赤になる。
- 内容一致検査が恒真化しない (production を空にしても、literal 表を空にしても赤になる形)。
- 承認済み entry を裁定つきで足すとき、更新が要るのは `expected` 表**だけ**になる。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 第 2 site (`:1914`) を scope に含める。裁定文言「件数 literal 固定のみ外す」は機構を指し
  行を指さないと読む。含めなければ裁定の目的 (受入停止の解消) が達成されない。
- **(P2)** `:1914` を `len(KNOWN_PROVENANCE_VIOLATIONS)` に置換する案は、直後の
  `tuple(registry.values()) == KNOWN_PROVENANCE_VIOLATIONS` に含意され**恒真になりうる**。
  維持 / 削除 / 別の非恒真形 (例: 重複 SHA 折り畳みの独立検査) のどれが正しいかは段 3 の争点。
- **(P3)** 改名先は `test_known_violation_ledger_matches_literal_entries`。

## 成果物影響 (DW-G05)

- 2 を実装しない場合: 承認済み違反を台帳へ足すたび受入全走が 2 node 赤になり land が止まる
  (成果物の値は変わらないが、以後すべての wave の受入結果が「赤」に固定される)。
- 内容一致を緩めた場合: 未承認 entry が台帳へ入っても緑になり、provenance 監査の受理集合が
  無制限に広がる — certified 選択結果と proof chain の著作者記録が無検査で通る (規律 2 違反)。
- (P2) が恒真化した場合: registry の重複 SHA 折り畳みが無検査になり、台帳 39 件が 38 件に
  黙って縮んでも緑になる。

## 分割方針

受理集合を変える wave のため軽量版にしない (DW-C00)。段 2 プラン 1 本、段 3 敵対 2 レンズ
(A=正しさ境界・恒真性、B=整合と scope・変異帰属)、段 5 実装 1 本、段 6 レビュー 2 本 + fix。
受入・実測は Pegasus 計算ノードへ dispatch (login では pytest 不可)。
