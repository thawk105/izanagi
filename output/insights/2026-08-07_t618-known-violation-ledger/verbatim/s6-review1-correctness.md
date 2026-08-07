## must-fix

該当なし。

## real (must-fix ではない)

該当なし。

## 変異 M1〜M5 の殺傷判定

1. **M1 — 殺せる**  
   期待された 4 node すべてで検出可能。literal 7 件 pin、実 commit 照合、空台帳時の 7 finding、単一 commit の rc=0 の各 assertion が entry 不在と不一致になる。  
   根拠: [test_check_ai_provenance.py:1323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1323), [同:1385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1385), [同:1925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1925), [同:1949](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1949)

2. **M2 — 殺せる**  
   rc=0 の実 commit node と rc=1 の合成 node は、いずれも ` note=…` を含む stdout を literal に期待している。helper から suffix を落とすと両方で不一致になる。

3. **M3 — 殺せる**  
   `test_known_violation_nonempty_note_is_public_on_rc1` は既知 1 件と新規 1 件を同一 range に置き、確実に rc=1 側の出力ループへ到達する。旧式 formatter への迂回は exact stdout の note 欠落として検出される。  
   根拠: [test_check_ai_provenance.py:1884](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1884), [check_ai_provenance.py:2097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2097)

4. **M4 — 殺せる**  
   guard 2 本を削除すると、synthetic commit の `missing-ai-agent` 1 件が台帳に consume され、stale にもならない。`None` は helper で `note=None` と文字列化され、改行 4 case もそのまま出力されるため、全 5 case が rc=0 まで到達し、期待する rc=2 と不一致になる。  
   根拠: [test_check_ai_provenance.py:1549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:1549)

5. **M5 — 殺せる**  
   型 guard は改行入り `str` を拒否しない。改行 guard だけを削除すると LF / CR / CRLF / U+2028 の 4 case が rc=0 へ到達するため、その 4 case が検出する。`non-str` case だけは型 guard で rc=2 のまま。

## refuted

1. **受理集合の過剰拡大を攻撃したが refuted。**  
   台帳 SHA は 40 桁を検証した後、`registry.get(audit.commit)` で完全一致 lookup される。finding 種別も完全一致で、`consumed_registry_entries` により同じ entry が consume するのは最初の 1 finding だけである。同 commit の別種別・同種別 2 件目はいずれも新規 finding に残る。  
   根拠: [check_ai_provenance.py:211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:211), [同:1022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1022)

2. **correction / waiver / merge / `--message-file` との合成を攻撃したが refuted。**  
   correction が期待 finding を先に suppress した場合と、waiver が期待 finding を消した場合は、台帳 entry が consume されず stale rc=2 になる。merge でも照合 key は実 commit の full SHA のまま。`--message-file` 分岐は台帳を参照せず、既知化を一切行わない。既存の合成 pin も残っている。  
   根拠: [check_ai_provenance.py:1176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:1176), [同:2046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:2046), [test_check_ai_provenance.py:2311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:2311), [同:2984](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/orchestrator/tests/test_check_ai_provenance.py:2984)

3. **`note` predicate の境界を攻撃したが refuted。**  
   `python3 -c` による直接評価では次のとおりだった。

   - `""` は前置条件で許可され、既存 6 件を拒否しない。
   - `"abc\n"`、先頭改行、`"\n"`、末尾 CR / CRLF は拒否。
   - NEL、U+2028、U+2029、VT、FF、U+001C〜U+001E も拒否。
   - 空白のみ `"   "` は許可される。これは「単一行」契約には一致し、stdout の物理行を増やさないため所見化しない。

   guard 後の note は両 rc 出力で同じ helper を通る。ANSI 等による表示撹乱は裁定済みの scope 外 nit であり、今回の固定 literal にも含まれない。  
   根拠: [check_ai_provenance.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:236), [同:250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t618-provenance-known-ledger/tools/check_ai_provenance.py:250)

4. **変更された 6 テストの恒真化・production oracle 化を攻撃したが refuted。**

   | test | 判定 |
   |---|---|
   | exactly-seven | SHA・種別・ruling・note を独立した literal で pin |
   | real-commit-findings | production は被検査対象で、期待 pair は hard-coded。期待値を production から導出していない |
   | empty-registry | 台帳を空にした後の 7 / 6 / 1 件を literal で pin。live full 監査件数ではない |
   | ledgered `3f2c…` | SHA・note・stdout・stderr を literal に exact pin |
   | rc=1 nonempty-note | synthetic known/new の実 finding と exact stdout の双方を要求 |
   | broken-note rc2 | malformed input を作るだけで、期待 rc・診断は production から導出していない |

   反転前の「`3f2c…` は未台帳・rc=1」という pin だけがユーザー裁定により意図的に消えた。raw finding の存在・種別・新 entry・公開出力には代替 pin があり、無代替の消失はない。

5. **`test_ledgered_3f2c43d7580b_is_known_and_rc0` の揮発性を攻撃したが refuted。**  
   `git rev-list 3f2c…^!` は対象 1 commit だけを返す。対象 object・message・変更 path は固定されており、working tree や live full 監査件数には依存しない。無関係な commit を HEAD に追加するだけでは stdout は変わらない。全台帳の破損で rc=2 になる依存はあるが、これは意図された global fail-closed である。

6. **規律 2 / 3 違反を攻撃したが refuted。**  
   受理集合の変更はユーザー裁定された 1 SHA × 1 finding だけで、範囲式・correction・waiver・他 SHA は変更されていない。性能や利便性のための緩和はなく、note の rc=0 / rc=1 公開はむしろ違反理由の可視性を増している。

## nit

該当なし。

## 総括

- 静的レビュー上、must-fix / real / nit はない。
- 受理集合は `3f2c43d7…` の `missing-ai-agent` 1 件だけ広がり、裁定と一致する。
- 最も危ない攻撃面は rc=1 側だけ helper を迂回する M3 だが、新設 exact stdout node が静的に殺せる。
- M1〜M5 はすべて、指名された期待 node で検出可能。
- pytest は実行しておらず、親報告の 238 passed を本レビューの実測としては扱っていない。