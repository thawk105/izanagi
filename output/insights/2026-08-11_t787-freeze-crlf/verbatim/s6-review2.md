# 結論: NO-GO

実装自体は段 4 の設計に沿っていますが、テスト検出力と変異の帰属に未閉鎖の穴があります。pytest は実走していません。

## Must-fix 所見

### 1. 凍結発行 API と複数世代履歴を迂回する弱実装が生存する

CR/LF の直接 hash、単一世代の履歴検証、activation report は検査されていますが、`prepare_revision()` の CR/LF テストがありません。NUL には発行前・既存 freeze 後の 2 テストがあるのに、CR/LF は追加されていません。[test_s8c_preregistration_core.py:1679](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:1679)

次の弱実装は全テストを通せます。

- `evidence_contract_sha256()` と履歴検証では新検査を使う。
- `prepare_revision()` だけ従来の NUL-only hash 経路を使う。
- 既存 NUL 発行テストは通るが、CR/LF 契約を発行できる。

また、legacy CR/LF テストは g1 単独だけです。[test_s8c_preregistration_core.py:1170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:1170) 祖先では旧 hash、tip だけ新 choke point を使う実装なら、CR/LF-bound g1 → clean g2 の履歴を受理できます。これは段 4 が明示した祖先順検査とも未接続です。[stage4-adjudication.md:9](/work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage4-adjudication.md:9)

必要なのは CR/LF ×「初回発行／既存 freeze 後」の `prepare_revision` テストと、CR/LF-bound 祖先を clean 世代で覆った複数世代テストです。

成果物影響: CR/LF path の hash・`protected_sha256` が凍結台帳へ発行されるか、不正な祖先を含む proof chain が certified 選択に受理されるかが変わります。

### 2. 「その他の制御文字を受理」の検出力が不足する

正例は VT、U+0085、U+2028、U+2029 などを固定していますが、C0 のうち VT 以外は未検査です。[test_s8c_preregistration_core.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:761)

例えば「CR/LF/NUL に加えて TAB・BS・FF・U+0001 を拒否するが、VT は特別に許す」実装は全テストを通り、親 brief の「その他の制御文字は従来どおり通る」を破ります。[brief.md:31](/work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/brief.md:31) 発効層の TAB 正例は別層なので、この穴を埋めません。

成果物影響: 本来有効な schema 非検証契約が凍結台帳・proof chain から除外され、`protected_sha256` と certified 選択の受理集合が狭まります。

### 3. 文書順と任意形状に生存変異がある

複数 CR/LF の fixture は、両 node に同じ制御文字を入れています。[test_s8c_preregistration_core.py:863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:863) 「文書順ではなく常に CR を LF より優先する」実装は通ります。先行 LF／後続 CR と、その逆を固定すべきです。

また、最深 fixture は `/conditions/0/required_evidence/0/0/path` 程度です。[test_s8c_preregistration_core.py:978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:978) 深さ 6 までだけ走査する実装や、root が list なら走査しない実装も通ります。root-list と十分深い dict/list 交互入れ子がありません。

成果物影響: 未検出 CR/LF path の hash が台帳へ入るか、エラー pointer が別 node を参照して proof chain の修復対象を誤るかが変わります。

### 4. M4/M5/M6/M11/M12 の「KILLED」分類は規約違反

段 4 はこれらを negative mutation の KILLED としています。[stage4-adjudication.md:69](/work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage4-adjudication.md:69) しかし、いずれも入力は変異前後とも拒否され、変わるのは reason・pointer・detail・先取り診断だけです。`DW-M03/M08` に従い diagnostic sensitivity pin として別枠にすべきです。[mutation.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/docs/dev-wave/mutation.md:16)

加えて「reason 統一は M1 が包含する」は不成立です。M1 は CR/LF を受理へ戻す変異であり、CR/LF を NUL reason で拒否する診断変異とは別物です。[stage4-adjudication.md:80](/work/1/SFC/tanab/dev-wave-jobs/t787-freeze-crlf/stage4-adjudication.md:80)

成果物影響: mutation ledger が受理集合防壁の kill と診断感度を混同し、凍結 proof chain の検証証拠を実態より強く記録します。

## M1〜M12 の静的 kill 集合

現在の param 数からの導出です。

| 変異 | 実際に赤になる集合 |
|---|---|
| M1 | CR/LF 拒否系 100 node。発行 API と複数世代履歴は赤にならない |
| M2 | CR 系 50 node |
| M3 | LF 系 50 node |
| M4 | 「先行 CR/LF・後続 NUL」の 2 nodeだけ。同一 path の 2 nodeは NULを先に見るため通る。診断 pin |
| M5 | 複数同種 CR/LF の 2 node。混在 CR/LF の優先誤りは未検出。診断 pin |
| M6 | dict/list 両方の `reversed` を外すなら、NUL 文書順 1 + CR/LF 文書順 2 = 3 node。どちらを外すか未特定で、list 側だけなら生存しうる。診断 pin |
| M7 | 38×2 matrix 76、interior 4、inner 2、文書順 2、root 2、malformed 6、legacy validation/report 4 = 96 node。段4記載は過少 |
| M8 | non-path controls 3 + non-string-path dict/list・non-exact-key 3 = 6 node |
| M9 | all-C0 なら赤は VT 1 nodeだけ。U+0085/U+2028/U+2029 は C0 ではなく、段4期待は過剰 |
| M10 | 具体的置換が未定義なので完全集合を確定不能。pointer allowlist 型なら inner 2 + 文書順 2 + root 2 + malformed 6 = 12 node |
| M11 | helper 全体を canonical 化前へ動かすなら NUL surrogate 1 + CR/LF surrogate 2 = 3 node。診断 pin |
| M12 | 両 detail を `repr(node)` にする累積変異なら NUL 51 + CR/LF 98 = 149 node。診断 pin |

このまま期待 node を段 4 の短い表現から作ると、M6・M7・M9・M10・M11・M12 は MISMATCH になる可能性が高いです。

## F1〜F7 照合

- F1: 実在し、指定された list/deep fixture を満たす。[test_s8c_preregistration_core.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:826)
- F2: NUL と同種 CR/LF の文書順は実在。ただし CR/LF 混在順は未固定で部分的。
- F3: 指定された VT・U+0085・U+2028・U+2029・文字どおりの `\r`/`\n` と exact hash は実在。
- F4: pre-wave hash literal、validation、activation report の両方が実在。[test_s8c_preregistration_core.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:37)
- F5: root CR/LF 2 node が実在。[test_s8c_preregistration_core.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:931)
- F6: non-string `path` dict の exact hash 正例が実在。[test_s8c_preregistration_core.py:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:794)
- F7: escaped raw bytes と surrogate により canonicalization reason を固定している。[test_s8c_preregistration_core.py:1024](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:1024)

## 回帰面・自己整合

リポジトリ全体の参照検索では関連テストは次の 5 ファイルだけで、`orchestrator/tests/` 外の該当テストはありません。

- `test_s8c_preregistration_core.py`: 旧 CR/LF 受理 4 param は意図どおり反転。NUL helper の全 callsite は新名へ更新済み。
- `test_s8c_preregistration_invariant.py`: 現行契約と candidate commit を動的に使い、現行契約に CR/LF がないため意味上は不変。
- `test_s8c_preregistration_predicates.py`: LF fixture は発効層の `load_contract_bytes()` に先取りされ、従来どおり `evidence-contract-invalid`。
- `test_p3_autonomous_workload_trial.py`、`test_trial_registry.py`: `ActivationReport` API の構築だけで、変更した hash 経路には到達しない。

NUL 側は 38位置、interior、malformed、文書順、legacy validation/report、発行前・既存 freeze 後が残っており、静的な helper 一般化破損は見つかりません。

新しい hash helper は production と同じ canonicalization を書き直していますが、各結果を固定 literal にも照合しているため恒真ではありません。[test_s8c_preregistration_core.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:160) 揮発値の焼き込みもありません。`test_evidence_contract_hash_is_semantic_canonical_json` の左右が production 同士なのは単独では弱いものの、別の literal test が補完しているため nit です。成果物影響はありません。

## T-739 資産

`output/insights/2026-08-11_t739-freeze-nul/` の全 17 tracked fileについて、working-tree blob hash と HEAD blob hash が一致しました。変更・mode差・untracked追加はいずれもなく、1 byte も変わっていません。

## 総括

- 結論は **NO-GO**。
- 実装本体は段4設計どおりだが、発行 API の CR/LF テストが欠落。
- CR/LF-bound 祖先を clean tip で覆う履歴変異が生存する。
- TAB等を過剰拒否する実装が正例不足で生存する。
- 混在 CR/LF の文書順と root-list／深い形状が未固定。
- M4/M5/M6/M11/M12 は kill ではなく diagnostic sensitivity。
- M6/M9/M10等の期待 node は現状の記述では MISMATCH。
- F1〜F7は概ね実在するが、F2は混在順について部分的。
- NUL 回帰と exact hash に静的破損は見つからない。
- T-739 資産 17 file は HEAD と byte-identical。