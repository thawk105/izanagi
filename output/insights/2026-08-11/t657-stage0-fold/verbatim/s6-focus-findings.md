判定は **NO-GO**。新 fence scanner に blocker 1 件、削除型テストと R4 文面に must-fix 2 件を確認しました。親の 66 passed は実測事実として採用し、追加検証は read-only の in-memory probe です。

### FOCUS6-01

- **主張:** backtick fence の info string に backtick を含む無効 opener を正規 fence と誤認し、可視な非 canonical 本文を除去して緑にする新しい抜け道がある。
- **file:line 根拠:** `_FENCE_OPEN_RE` は marker 後を無条件の `.*` で受理します。[contract.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:76)。その行から closer までを無条件で捨てます。[contract.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:349)。比較元も同じ regex ですが、別の ambiguity 検査は backtick info 内の backtick を明示的に「無効」と判定しています。[check_docs.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/tools/check_docs.py:708)、[check_docs.py:3311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/tools/check_docs.py:3311)
- **具体的な失敗シナリオ:** §7.5 canonical 表の前へ `````text`invalid``、空行、`scope = 非空 string` の緩和表、````` を置く。CommonMark では最初の行は opener でないため緩和表が本文に現れ、後の ````` が opener となって canonical 表を隠す。一方 `_read_design` は緩和表を捨てて canonical 表だけを読み、in-memory probe で `status=incomplete / pending=5 / unresolved=2` と正常受理した。通常の `````text`` と、backtick を含む tilde info は正しく受理される。問題は backtick marker の info に backtick がある場合。
- **深刻度:** **blocker**
- **成果物影響:** 人間が読む設計正本と validator が読む権威 bytes を再び分離でき、§7.5 schema や段 6 契約の decoy 差し替え防壁が成立しない。

### FOCUS6-02

- **主張:** §7.5 表用に新設した削除型 2 node は、raw-text M1 mutant でも受理されず、依然として診断差だけの偽 KILL である。段 6 行用の 2 node は真の KILL になっている。
- **file:line 根拠:** helper は表直後へ blank-line terminator より先に fence closer を置きます。[test_contract.py:856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:856)。表 extractor は次の空行までを全行 row として読むため、raw mutant では closer が malformed row になります。[contract.py:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:457)。該当 node は [test_contract.py:885](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:885) と [test_contract.py:897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:897)。段 6 helper は row 単位なので raw regex が拾います。[test_contract.py:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:870)
- **具体的な失敗シナリオ:** `_read_design` を raw text へ戻すと、tilde 表 node は `revocation table has a malformed row` で拒否されるが、テストは `missing or duplicated` を期待するため診断差で赤くなる。対して段 6 tilde node は raw mutant で正常受理され、現実装では `stage 6 row is missing or duplicated` となることを確認した。
- **深刻度:** **must-fix**
- **成果物影響:** M1 全体の KILL は段 6 node で成立するが、I2 が要求した「§7.5 と §10 の両方」のうち §7.5 側の受理集合差の証拠が未成立。

### FOCUS6-03

- **主張:** §12.3 は R4 を未裁定と登録しながら、選択前の事実として「対応する record が要る」と断定しており、実質的に (a) を既成事実化している。
- **file:line 根拠:** 見出しは「親が決めない」ですが、本文は「対応する record が要る」と断定した直後に、record を持たない (b) を候補として列挙しています。[bundle-design.md:858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:858)、[bundle-design.md:864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:864)。manifest 上は正しく `unresolved` です。[contract.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:217)
- **具体的な失敗シナリオ:** ユーザーが (b) を選ぶと、裁定結果が既存の「record が要る」という正本文と即座に矛盾する。後続実装者は unresolved gate を見ても、正本の断定を根拠に cancellation record の存在だけを先取りできる。
- **深刻度:** **must-fix**
- **成果物影響:** gate は段 0 完了を止めるため直ちに fail-open しないが、R4 のユーザー決定権と三択の中立性が文書上失われる。

### FOCUS6-04

- **主張:** 段 6 の 2 文分割は boundary marker の逐語に依存し、意味が同じ合法な書き換えも拒否する。
- **file:line 根拠:** 分割位置は exact な太字 marker で決まり、control と execution boundary の双方が定数と exact 比較されます。[contract.py:501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:501)、[contract.py:958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:958)
- **具体的な失敗シナリオ:** 「本行が固定するのは」を同義の「本行の固定対象は」へ直すだけでも boundary missing として拒否される。一方、3 文目の前置・後置、boundary 内への `。` 追加、末尾 `。` 削除はいずれも probe で拒否された。
- **深刻度:** **nit**
- **成果物影響:** 受理集合の縮小だけで正しさは緩まないが、意味不変の編集にもコード・test の同時更新が必要になる。

照合上、以下は問題ありませんでした。

- 4-space インデントした fence 風ブロックへ表全体を移す攻撃は `missing or duplicated` で拒否された。
- R4 は裁定 profile に混入しておらず、`_applicable_unresolved_count` は引き続き S/B の 2 件だけを数える。[contract.py:809](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:809)
- 現行値は `required_gates=13`、hash は指定値と三者一致、blocking 5、`status=incomplete / pending=5 / applicable_unresolved=2`。
- `_extract_stage6_contract` の caller は production 1 件と test 1 件だけで、双方とも 4 要素へ更新済み。
- `_UPPER_REVOCATION_SCHEMA` 7 組、段 6 predicates 5 文、control 文、実行境界文は現行 docs と逐語一致。
- hash 自己参照、R4 の profile 誤算入、consumer 取り残し、無許可の期待値緩和は確認しなかった。

## 総括

- 判定: **NO-GO**
- blocker の所見 ID: **FOCUS6-01**
- SOL6-A-01: **open** — tilde・長い backtick・closer 長は閉じたが、無効な backtick info string を fence と誤認する新しい decoy 経路が残る
- SOL6-A-02: **closed** — 段 6 削除型 node が raw M1 mutant を実際に受理へ倒す。ただし §7.5 側 2 node は FOCUS6-02
- SOL6-A-03: **closed** — control・execution boundary の exact 比較により、3 文目と句点の追加・削除を拒否する
- LB-B-03: **closed** — R4 を user-owned unresolved gate として登録し、段 0 の blocking 5 件へ算入した。ただし推奨と決定の文面境界は FOCUS6-03
- M1 を KILL する node の名前: **`test_design_stage6_row_only_in_tilde_fence_is_rejected`**