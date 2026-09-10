# [T-2050] B-4 実走前 issuer の検証記録

- authority: none
- default_effect: no-state-change
- 対象 commit: `80da45e6f873255946a51c34c0e0fc8e05608bb7`
- 対象 branch: `worktree-dev-wave-t2050-b4-issuer`

## 結論

B-4 に限定した pre-run issuer を新設し、予定 attempt 全列、一度だけ取得する32 byte seed、既存 ledger が作る registry / manifest、予定 result path、final receiptを同じ commitmentへ束縛した。発行時とload時の双方で、予定外attempt、seed source差替え、fixed artifactとのpath衝突、予定result同士の祖先関係、非canonical・型不正なreceiptをfail-closedに拒否する。

result pathの不存在検査はpoint-in-timeであり、formal launcher / raw producerと共通lockを持たない。したがってformal B-4全経路での結果前発行、外部権威母集合、別root再発行拒否、署名・外部pin、coordinated rewrite検出、並行result writer排他は保証しない。

## 実測

- issuer焦点走: `29 passed`、rc=0。
- 既存ledger + campaign source列挙meta: `32 passed`、rc=0。
- 第2焦点review: 元8所見と追加3所見を `closed`、must-fix 0、regressed 0と判定。reviewer自身はtest未実走。
- full-history AI provenance: 6870件、新規違反なし。既知違反54件は既存台帳どおり。

## 変異 matrix

初回はbaseline PASSED、M1〜M3 KILLED、M4 / M5 MISMATCHだった。M4はRNG前拒否を検出するsymlink-component nodeの登録漏れ、M5はtemp unlinkを消す変異がunlink fault testまで赤にしたことが原因であり、検出力の生存ではない。初回ledgerはerratumとして残した。

再登録後はbaseline PASSED、M1〜M5がすべてKILLED、expected / failed node集合完全一致、各anchor countは1、SURVIVED 0、MISMATCH 0だった。M4は3 node、M2は5 nodeへ初回事前登録を訂正し、M5はtemp cleanupを保ったまま競合final名をunlinkして上書き可能にする変異へ再照準した。

## 束縛した構造化証拠

- `verbatim/mutation-spec.json`: SHA-256 `99f2afe86088c8bb3f1a7a92d89e80eceef8de3fa47c398110e6de7426ea5e33`
- `verbatim/mutation-ledger-attempt1.json`: SHA-256 `1f40030b0dfa2b89b73d4adadc351e3a8d46429f67b4161668188e868142ce96`
- `verbatim/mutation-attempt1.json`: SHA-256 `9370011f37ea1c10f7a4fc84030c84982e13041209c0b7ab8df7e52f39647dc3`
- `verbatim/mutation-ledger-attempt2.json`: SHA-256 `c1d328ef4f5a503ba0b3c66a49b88dafa54ddb85887d51f1e8d2a0297931c9c3`
- `verbatim/mutation-attempt2.json`: SHA-256 `909d44afc4de195dc9106aa8416c4d09e031aa3bf98d7496d370e4cac44b6271`

これらは開発時の検出力証拠であり、B-4正式実走のproof chainやissuer receiptそのものではない。
