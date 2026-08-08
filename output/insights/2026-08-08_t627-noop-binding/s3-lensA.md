静的読解のみで判定した。ファイル変更、pytest、import、build は実行していない。

## 所見

### 1. must-fix — 「途中 no-op」負例が実際には末尾 no-op

- 根拠: probe の列は `(1,1)→(2,1)→(2,1)` で、no-op は terminal pair である。[s1-probe.py:86](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-probe.py:86) 段 2 も同じ fixture を「terminal pair しか見ない実装」の検出用としている。[s2-plan.md:301](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:301) また `g1→g2→g3` 正例は受理表にあるが、独立 node 一覧には無い。[s2-plan.md:211](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:211)
- 成果物影響: serial 2 の no-op 後に正当な serial 3 が続く chain を terminal-only 実装が受理し、certified 選択・レポート・台帳に重複した activation 参照を残し得る。
- 修正案: 負例を `(1,1)→(1,1)→(2,1)` として serial 2 で拒否させる。併せて `(1,1)→(2,1)→(3,1)` の正例を追加し、terminal と ever-active 集合を exact assert する。

### 2. must-fix — 全 changed env の successor 検査を保証していない

- 根拠: 複数 env 同時前進は正例だけで、predicate spy は 1 env 前進時の「1 回」しか要求しない。[s2-plan.md:299](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:299) [s2-plan.md:306](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:306) `False` 負例も 1 env だけの前進である。[s2-plan.md:305](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:305)
- 成果物影響: 2 env が同時に +1 し、後方 env の bound contract だけが不正でも、先頭 env だけ検査する実装が state を受理して不正 hash を成果物へ流せる。
- 修正案: `(1,1)→(2,2)` で ordered な 2 callback を exact assertし、2 件目だけ `False` にした独立負例も追加する。

### 3. must-fix — production adapter の負方向が未検査

- 根拠: adapter は exact hash/generation 解決と `is_valid_successor` の結果返却を要求する。[s2-plan.md:145](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:145) しかし production adapter test は正当な real g1/g2 と呼出引数しか検査せず、`False` の負例は任意 synthetic callable を loader に直接渡している。[s2-plan.md:305](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:305) [s2-plan.md:310](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:310)
- 成果物影響: adapter が row hash を無視する、または `is_valid_successor=False` を呼ぶだけで捨てる実装でも、別の contract に対する proof を使って activation 行を受理できる。
- 修正案: 正しい row で `ec.is_valid_successor=False` を返して loader が拒否する統合負例と、generation は正しいが hash が違う row を `_resolve_activation_entry` が解決しない負例を追加する。

### 4. must-fix — 必須 capability 契約がテストで固定されていない

- 根拠: plan は既定値なしの keyword-only callable と、serial 1 でも非 callable を拒否すると定める。[s2-plan.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:8) [s2-plan.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:112) しかし新規 node 一覧に omission／非 callable のテストが無い。[s2-plan.md:292](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:292)
- 成果物影響: permissive default を足す変異が生存すると、将来 caller が capability を省略して T-627 不適合 transition を trusted state として受理できる。
- 修正案: `validate_activation_records` と `load_activation_state` の引数省略が `TypeError`、serial 1 に `None` を明示した場合が `ActivationRecordError` になる独立 node を置く。既存の外部 probe を互換性維持の理由に default 化してはならない。

### 5. should-fix — DW-G04 の説明は事実上 T-624 と同じ論法

- 根拠: production artifact は `00000001.json` だけで、新述語は発火しない。一方、既存 `is_valid_successor` は pegasus g1/g2 の import-time `validate_generations` から実際に呼ばれる。[env_contract.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:300) [env_contract.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:334) [env_contract.py:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/env_contract.py:367) したがって brief の「同じ結線済み・未発火」は成立しない。[s1-brief.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-brief.md:43)
- 成果物影響: 現在値への直接影響はないが、この説明を先例化すると、未発火 gate を成果物保証として採録する再発を招く。
- 修正案: 「DW-G04 は満たしていないが、後発のユーザー裁定が T-657 より前の実装を明示したため、本件だけ狭く override された」と記録する。consumer 存在を発火証拠とは呼ばない。

### 6. should-fix／scope 外の裁定候補 — source binding は全 certified producer には閉じていない

- 根拠: silo は activation leaf を動的 source hash に含める。[silo_ladder_rung1.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/silo_ladder_rung1.py:254) qualification も両変更 module を code identity に含める。[contract.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/qualification/contract.py:38) ただし汎用 certified 経路がその source binding を呼ばない既知穴は現行台帳にも明記されている。[worklog.md:2803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/docs/worklog.md:2803)
- 成果物影響: T-657 後、汎用 producer では dirty／未レビューの loader bytes で certified 選択・レポート・WAL を生成しても activation 参照だけでは検出できない。
- 修正案: T-627 へ実装を混ぜず、T-657 前提の別裁定パッケージとして、汎用 certified writer の code identity／reviewed-commit 束縛を扱う。

### 7. nit — probe H は C と同一入力

- 根拠: hash は常に generation から生成されるため、H の「hash 据置」は構成されていない。[s1-probe.py:32](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-probe.py:32) C と H はともに `[(1,1),(2,1)]` である。[s1-probe.py:82](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-probe.py:82) [s1-probe.py:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s1-probe.py:87)
- 成果物影響: certified 成果物への直接影響はなく、段 1 証拠のケース名だけが実入力を誤記している。
- 修正案: H を削除するか、wrong-hash record を直接組み立て、既存 registry pair gate の拒否確認として位置付ける。

## 境界・再著述の確認

repo 内の state 生成経路は loader だけで、別 production caller は見つからなかった。`ActivationState(...)` の直接構築は issuer テストだけである。[test_env_contract_activation.py:990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/tests/test_env_contract_activation.py:990) `execution_guard` は遷移を再検査せず、cached issuer receipt、exact `ActivationState`、terminal row と `GENERATIONS` の一致を信頼する。[execution_guard.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t627-noop-binding/orchestrator/campaign/execution_guard.py:44) この構造では production loader と issuer への必須 adapter 配線が閉じれば、guard 自体の変更は不要である。

既存テストの再著述は次の判定になる。

- delta 非強制テストの置換: 裁定済みの受理集合縮小なので正当。ただし must-fix 1・2 の補強が必要。
- downgrade historical fixture: 正当。forward g1→g2 後に g1 の ever-active membership と resolver を検査するため、元の「歴史世代を解決できる」性質は維持される。[s2-plan.md:248](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:248)
- issuer success fixture: g1/g1 から g1/g2 へ変え、旧入力を拒否 node に残すので正当。[s2-plan.md:269](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:269)
- valid-suffix test: forward suffix 化と内側の head mismatch 検査は、偶然緑を除く強化である。[s2-plan.md:282](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t627-noop-binding/s2-plan.md:282)

初期 record bytes、head serial/hash、`lookup()` の g1 選択を変える計画上の経路はない。activation leaf は `FROZEN_MANIFEST` 非収録で、silo/T126/T419 の列挙は path membership または動的 hash で閉じている。凍結成果物を更新しない判断も正しい。

## 総括

判定は **条件付き GO**。必須 callable＋production adapter という実装構成自体は T-627 と D228 の受理集合に整合し、据置 env も拒否しない。

ただし、上記 4 件の test-oracle 穴を直さないままなら **NO-GO**。**must-fix は 4 件**。