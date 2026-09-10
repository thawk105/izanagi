## 総括

必読資料はすべて読了した。pytest と書き込みは行っていない。  
`validate_condition_freeze_at` の完全実走は、環境に利用可能な一時ディレクトリがなく未実施である。以下はソース、record、`git ls-tree`、SHA-256、インメモリ解析による静的実測である。

### B-1

- **主張**: `§5` の値・本文・空行後の行は保護 hash に含まれず、意味のある変更が世代変更として検出されない。
- **証拠**: [`s8c_preregistration.py:759`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:759)、[`s8c_preregistration.py:881`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:881)、[`s8c_preregistration.py:191`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:191)、[`phase3-8c-preregistration.md:243`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:243)。読了範囲は lexer 718-756、`§5` 759-803、`§6` 838-878、contract 881-932。
- **深刻度**: must-fix
- **成果物影響**: `§5` の値や prose を変えても同じ freeze record が通り、後から発効条件だけが変化し得る。
- **推奨**: `§5` の値・本文を今回の変更対象から明示的に除外し、変更禁止検査を追加する。対象に含めるなら `§5` 全体または文書 bytes の hash を凍結対象へ追加する。

### B-2

- **主張**: 親 brief の実行コマンドは存在せず、さらに `prepare_revision` には六つの失敗経路がある。
- **証拠**: 親 brief [`s1-brief.md:48`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/artifacts/s1-brief.md:48)、CLI [`s8c_preregistration.py:1971`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1971)、実装 [`s8c_preregistration.py:1849`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1849)、[`test_s8c_preregistration_invariant.py:324`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8c_preregistration_invariant.py:324)。読了範囲は `prepare_revision` 1837-1917、CLI 1971-2012。
- **深刻度**: must-fix
- **成果物影響**: 親 brief のままでは g6 が生成されず、wave が開始時点で停止する。
- **推奨**: `prepare-revision` に統一する。経路は次の通り確認する。

  - `spurious-revision`: 保護 hash が不変。空白、強調、コード span、`§5` 値だけの変更、8b だけの変更で発火し得る。
  - `generation-gap`: freeze namespace が 1 から連続しない場合。現在の tracked record は g1-g5 で連続。
  - `record-ruling-reference`: 既存世代があるのに裁定参照が欠落または正規表現不一致の場合。
  - `revision-exists`: g6 の宛先が既に存在する場合。排他的作成なので stale file でも停止する。
  - `freeze-namespace-unknown`: freeze directory に想定外の tracked path がある場合。
  - `generation-limit`: 世代番号が 1024 を超える場合。現在は該当しない。

### B-3

- **主張**: `D496` は機械的には通るが、実体の本文は今回の failed-configuration-only 変更を承認していない。
- **証拠**: 正規表現 [`s8c_preregistration.py:61`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:61)、裁定検査 [`s8c_preregistration.py:1381`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1381)、現行 D496 [`decisions.md:20614`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/decisions.md:20614)、本文の決定3 [`decisions.md:20623`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/decisions.md:20623)、暫定 fragment [`rulings-worklog-fragment.md:20`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/artifacts/rulings-worklog-fragment.md:20)。実測では `D496` は通り、`D0`、`D0496`、小文字、末尾空白付きは通らない。検査は見出しの存在だけで本文を読まない。
- **深刻度**: blocker
- **成果物影響**: g6 が「裁定参照あり」として検証済みになっても、参照先の本文と変更内容が矛盾する。
- **推奨**: canonical decisions に新しい裁定本文を先に着地させ、その見出しを参照してから record を生成する。見出し存在だけでなく、裁定本文の digest または変更対象との構造化対応表を導入する。

### B-4

- **主張**: `§6` 条件4・7を文書だけ変更して evidence contract と evaluator を変更しない計画は、文書 hash と実際の判定意味を分離する。
- **証拠**: plan [`s2-plan.md:120`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/artifacts/s2-plan.md:120)、文書 [`phase3-8c-preregistration.md:189`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:189)、evidence contract の条件4 [`s8c_preregistration_evidence_contract.v1.json:131`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:131) と条件7 [`s8c_preregistration_evidence_contract.v1.json:245`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:245)、consumer [`s8c_preregistration_evidence.py:1710`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration_evidence.py:1710)。
- **深刻度**: blocker
- **成果物影響**: 新しい条件 hash を持つ g6 が、後段では旧来の no-restart と floor 判定で評価される。
- **推奨**: 今回は条件4・7の本文を変更しないか、evidence contract・evaluator・関連テストを同一 wave で更新する。後者なら意味変更なので decider version と新世代を再設計する。

### B-5

- **主張**: P1 の「8b に新規 §10 を追記」は手続き文面には合うが、現在の bytes pin と hold 状態では機械的な再凍結にならない。
- **証拠**: 8b §8 [`phase3-8b-descriptor-design.md:265`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8b-descriptor-design.md:265)、pin [`output/s8b-freeze/holdout_freeze.json:7`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/output/s8b-freeze/holdout_freeze.json:7)、hold [`freeze_verification_hold.py:14`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/freeze_verification_hold.py:14)、解除後の検査 [`s8b_holdout_freeze.py:875`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8b_holdout_freeze.py:875)、hold 中の処理 [`s8b_holdout_freeze.py:917`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8b_holdout_freeze.py:917)。実測 SHA は pin `1829af7...` に対し現行 bytes は `5fbdd7d...`。
- **深刻度**: blocker
- **成果物影響**: hold 中は成功ではなく保留、解除後は design source mismatch で失敗し、8b の再凍結 record も承認も成立しない。
- **推奨**: 8b の v2 再凍結、bytes pin 更新、ユーザー承認、hold 解除後の再検証を別途完了する。そこまでできないなら本 wave で8bを編集しない。

### B-6

- **主張**: 8c §3 の pointer 表は8bの古い要約を許すが、8c自身の要約欄と条件4・7は新しい8bの意味に合わせて更新が必要である。
- **証拠**: pointer の優先規則 [`phase3-8c-preregistration.md:72`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:72)、現行条件 [`phase3-8c-preregistration.md:189`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:189)、plan [`s2-plan.md:26`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/artifacts/s2-plan.md:26)。
- **深刻度**: must-fix
- **成果物影響**: pointer だけを直すと8c本文が旧意味のまま残り、過剰に行を編集すると不要な generation 差分が増える。
- **推奨**: 8c が所有する右側の要約と条件4・7だけを変更し、8b の旧本文そのものは変更しない。必要なら「8b §6 は §10 により上書き」と明記する。

### B-7

- **主張**: 親 brief の「テスト編集不要」は反証され、§5欄名変更と8b編集の双方に既存検査の影響がある。
- **証拠**: 8c test の固定欄名 [`test_s8c_preregistration_core.py:53`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8c_preregistration_core.py:53)、実文書との直接比較 [`test_s8c_preregistration_core.py:439`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8c_preregistration_core.py:439)、固定 corpus hash [`test_s8c_preregistration_core.py:585`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8c_preregistration_core.py:585)、8b whole-file golden [`test_s8b_oracle_driver.py:190`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/tests/test_s8b_oracle_driver.py:190)、repin spec [`t080_freeze_migration.py:90`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/t080_freeze_migration.py:90)。`check_docs` は living doc と address lint を行うが [`check_docs.py:48`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/tools/check_docs.py:48)、8b/8c全文の SHA pin は持たない。SHA 処理 [`check_docs.py:3995`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/tools/check_docs.py:3995) は別の skill guard 用である。
- **深刻度**: must-fix
- **成果物影響**: 欄名変更で現行 test が赤になり、8b の golden と migration receipt は旧 bytes を要求し続ける。
- **推奨**: 受理した契約変更に対応する固定値・golden・recordを更新する。テストを動的に緩めるだけの変更はしない。

### B-8

- **主張**: g6 の `revision_reason` と単一の `ruling_reference` だけでは、三件の裁定と各条件 hash の変化を後から機械復元できない。
- **証拠**: record 生成 [`s8c_preregistration.py:1808`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1808)、contract 構造 [`s8c_preregistration.py:191`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:191)、再凍結規則 [`phase3-8c-preregistration.md:247`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:247)、plan [`s2-plan.md:187`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/artifacts/s2-plan.md:187)。
- **深刻度**: must-fix
- **成果物影響**: 一つの検証済み record に、裁定対応のない変更を混在させても判別できない。
- **推奨**: 一世代を維持するなら、裁定 ID、変更対象、旧 hash、新 hash の構造化 map と裁定本文 digest を追加する。追加できないなら、復元可能性を成果物の保証範囲から外す。

### B-9

- **主張**: 同一 commit への同居だけでは、g6 と8b bytes、または g6 と未保護の8c変更の相互 binding にならない。
- **証拠**: plan の同一 commit 方針 [`s2-plan.md:202`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/artifacts/s2-plan.md:202)、`prepare_revision` が worktree bytes を読む箇所 [`s8c_preregistration.py:1882`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1882)、record照合 [`s8c_preregistration.py:1272`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1272)。record は8b全文 hashを保持しない。
- **深刻度**: must-fix
- **成果物影響**: 生成後に8bや`§5` proseだけを直しても、g6の検証が必ずしも失敗しない。
- **推奨**: 全文書と evidence contract を最終化してから一度だけ生成し、commit 後に8c検証と8b pin 検証を別々に行う。相互 binding が必要なら文書間 digest を追加する。

### B-10

- **主張**: plan の decider version 非変更は、純粋な文書・record変更に限れば正しいが、条件判定の意味を変えるなら誤りである。
- **証拠**: 現行値 [`s8c_preregistration.py:50`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-1347-refreeze/orchestrator/campaign/s8c_preregistration.py:50)、record 出力 [`s8c_preregistration.py:1818`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1818)、発効時の完全一致 [`s8c_preregistration.py:1733`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/orchestrator/campaign/s8c_preregistration.py:1733)、規則 [`phase3-8c-preregistration.md:247`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1336-t1337-t1347-refreeze/docs/phase3-8c-preregistration.md:247)、plan [`s2-plan.md:179`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1336-t1337-t1347-refreeze/artifacts/s2-plan.md:179)。
- **深刻度**: nit
- **成果物影響**: 不要な bump は decider mismatch を起こし、必要な bump の省略は旧 evaluator 意味で新文書を発効させる。
- **推奨**: 今回を docs-only と確定できる限り v2 のままにする。evidence contract や evaluator を変更する段階では v3 と新世代を同時に導入する。

## 総合判定

**NO-GO**

8b は hold 解除後に bytes pin 不一致で失敗し、現状は再凍結として発効しない。  
D496本文、条件4・7の実装契約、recordの裁定対応、既存goldenの扱いを先に再設計すべきである。