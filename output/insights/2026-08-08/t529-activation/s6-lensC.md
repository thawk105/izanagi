静的レビューの結論は **NO-GO** です。指定された 12 modified / 4 untracked file を確認しました。pytest は実行しておらず、親の「555 passed / 0 failed」は再測定していません。

### 1. head pin が reviewed commit ではなく、可変 worktree の一回限りの snapshot に留まる

深刻度: **must-fix**

根拠:

- 裁定は Python の head 定数が reviewed commit に束縛されることを前提にしています。[s4-adjudication.md:80](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s4-adjudication.md:80>)
- 実装は live worktree の directory を読み、`source_commit` を受け取りません。[env_contract.py:458](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:458>)
- 既存 source binder は receipt commit と import 済み module を比較しますが、generic certified path からは呼ばれません。[certified_writer_preflight.py:85](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/certified_writer_preflight.py:85>)、[loop.py:131](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/loop.py:131>)、[pipeline.py:595](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/pipeline.py:595>)
- 具体的な suffix 反例は、valid `00000002.json` と対応する head 定数 `(2, H2)` を未 commit のまま置き、`loop.run_campaign()` / `pipeline.evaluate()` を直接呼ぶ構成です。commit 照合がないため Pegasus g2 が current として通ります。
- tail rollback は、将来 head 2 を一度 load した process で `00000002.json` を削除すれば成立します。snapshot は PID 中で再走査されません。[env_contract.py:501](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:501>)。テスト自身が、load 後に record を削除しても `lookup()` が成功することを正例にしています。[test_env_contract_activation.py:422](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py:422>)
- directory は一度列挙して scanner を閉じた後、再走査せず publish します。[env_contract_activation.py:356](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:356>)。列挙後の suffix・隠し file 追加、全 bytes 読込後の tail 削除は観測されません。
- head 検査は全 file の読込・parse・chain 検査後です。[env_contract_activation.py:279](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:279>)。head 1 に巨大な `00000002.json` を足すと、head mismatch より先に無制限読込が走ります。[env_contract_activation.py:343](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:343>)

**成果物影響:** 未 review の suffix で certified contract hash が g1 `e576…` から g2 `1346…` へ変わり、warm-process rollback では record 2 が存在しないまま g2 前提の receipt・WAL commit が生成され得ます。

修正案:

- 全 generic certified writer を、既存 preflight と同等の reviewed-commit 検査へ結線する。
- authority は可能ならその commit の Git tree から読む。live directory を使う場合も commit の exact file set/bytes と照合する。
- mutable snapshot を維持するなら directory fd による列挙、終端再走査、record 数・size 上限を追加する。PID cache は reviewed commit 由来の immutable snapshot にだけ許す。

### 2. receipt は production では自己発行・自己照合であり load-bearing でない

深刻度: **must-fix**

根拠:

- guard は caller から receipt を受け取らず、その場で current state を読み receipt を生成します。[execution_guard.py:90](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:90>)、[execution_guard.py:180](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:180>)
- 直後の PID、seal、cached-object、state-object、serial/hash 検査は、その同じ issuer が生成した値に対する自己照合です。[execution_guard.py:112](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:112>)
- 普通の fork child では callback 後に child 用 receipt を新規発行するため、親 receipt が guard に渡る production edge はありません。
- forged/stale/fork テストは `current_activation_receipt` 自体を差し替えて、存在しない入力 edge を作っています。[test_execution_guard.py:60](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_execution_guard.py:60>)、[test_execution_guard.py:98](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_execution_guard.py:98>)、[test_campaign.py:2246](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_campaign.py:2246>)
- `lookup()` を禁止するテストは site を `OTHER` に変えています。[test_execution_guard.py:39](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_execution_guard.py:39>)。実 Pegasus branch は `lookup_required_attestation_contract()` で `REGISTRY` を再度引くため、lookup 相当の fallback が残ります。[execution_guard.py:221](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:221>)、[env_contract.py:603](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:603>)
- process seal は別 process から推測可能ではありませんが、receipt field として同一 process 内に露出します。実効防御は cached-object identity であり、それも自己発行経路では恒真です。

**成果物影響:** receipt 検査を current state の直接解決へ置換しても production の certified 受理集合・JSON・WAL は変わらず、所見1の stale snapshot も receipt によって拒否されません。

修正案:

- contract 選択時に `(contract, receipt)` を一体で返し、caller が保持した receipt を guard の必須引数にする。
- guard はその receipt だけから解決し、Pegasus の required-contract 検査も receipt state 内から導出する。
- stale/fork テストは issuer monkeypatch を使わず、実 public API で取得した旧 receipt を cache 更新・fork 後に渡して拒否させる。

### 3. head serial 検査は state hash に包含され、テストは診断文字列だけで kill している

深刻度: **should-fix**

根拠:

- state hash は `activation_state_sha256` 以外、すなわち `activation_serial` を含む全 record body の SHA-256 です。[env_contract_activation.py:124](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:124>)
- したがって SHA-256 collision を除けば、serial 不一致は必ず terminal state hash 不一致にもなります。[env_contract_activation.py:313](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:313>)
- tail rollback / suffix テストは `"head serial 不一致"` という理由文字列を要求します。[test_env_contract_activation.py:253](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py:253>)、[test_env_contract_activation.py:265](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py:265>)。serial check を削除しても入力は state-hash check で拒否され、変わるのは診断だけです。

**成果物影響:** certified 受理集合は変わらない一方、mutation ledger は M1 を実効 gate の kill と誤記録できます。

修正案:

- serial check は診断用の冗長検査と明記し、load-bearing mutation から外す。
- tail/suffix は head pin 全体の拒否を検査し、state-hash gate は同一 serial・別 state の独立反例で固定する。

### 4. 歴史較正のテストは実検証ではなく内部 cache bit を見ている

深刻度: **should-fix**

根拠:

- production は current 行だけを authority load 時に検証し、歴史 entry は resolver で検証する実装になっています。[env_contract.py:473](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:473>)、[env_contract.py:523](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:523>)、[env_contract.py:577](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:577>)
- しかし対応テストは private `_VERIFIED_CONTRACT_SHA256S` への hash 追加だけを見ています。[test_env_contract_activation.py:353](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py:353>)
- `_verify_entry_calibration()` を呼ばず hash だけ追加する mutant はこのテストを通ります。逆に、全歴史 entry を eager 検証しても cache set に追加しない実装なら「current-only」assert を通せます。
- g2 calibration の直接検証テストも、resolver との結線は観測しません。[test_env_contract.py:807](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract.py:807>)

**成果物影響:** wiring regression が入ると、壊れた g1 較正を歴史 floor/oracle report が受理するか、逆に未使用 g1 の欠落で current g2 の全 admission が拒否されます。

修正案:

- temp source-stage で g2 current / g1 historical を作り、g1 較正を欠落・改変させる。
- 実 loader/resolver を通して「current lookup は成功、g1 historical resolve だけ失敗」を確認する。`REGISTRY`、index、resolver は monkeypatch しない。

### 5. `terminal_rows` assert は決して発火しない

深刻度: **nit**

根拠:

- 空 chain は loop 前に拒否され、非空 loop の各 iteration で `terminal_rows` が必ず代入されます。[env_contract_activation.py:269](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:269>)
- その後の `assert terminal_rows is not None` は到達可能な入力では常に真です。[env_contract_activation.py:322](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:322>)

**成果物影響:** 削除しても受理集合・選択値・レポート・台帳は変わりません。

修正案: security check として数えず、型 narrowing が目的なら `cast` または非空列の末尾から直接構築する。

## 反例が成立しなかった点

- cold・不変 directory では、隠し file、別拡張子、大文字拡張子、9 桁以上の serial 名は exact regex で拒否されます。[env_contract_activation.py:29](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:29>)、[env_contract_activation.py:372](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract_activation.py:372>)
- repo 全体検索では、production の `_CONTRACT_SHA256_INDEX` 読出しは `resolve_by_contract_sha256()` 内だけでした。既知 g2 は ever-active 検査を通らず返りません。[env_contract.py:558](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:558>)
- activation record 間の no-op / skip / downgrade 拒否は混入していません。正例テストも三遷移を受理しています。[test_env_contract_activation.py:303](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract_activation.py:303>)
- 通常の forged / fork 継承 receipt を検査自体に通す反例はありません。問題は、それらが production guard の入力にならず、検査が受理集合を変えないことです。

## 総括

1. **判定: NO-GO**
2. **must-fix: 2 件** — reviewed commit と head が generic certified sink で未結線であり、receipt も自己発行・自己照合のため production 受理集合を変えていません。