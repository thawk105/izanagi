静的判定は **NO-GO**。段 0 の `incomplete` 防壁そのものは破れませんでしたが、実装前に止めるべき blocker が 5 件あります。read-only のためテスト実走・編集はしていません。

### SOL-A-01

- 主張: 「exact schema」の drift 束縛が key 名しか守らず、型・literal・参照制約の弱体化を緑のまま通す。
- file:line 根拠: regex は制約 cell を `[^|]*` として捨てます ([s2-plan.md:139](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:139>))。プラン自身も「束縛するのは key 集合」と限定しています ([s2-plan.md:341](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:341>))。予定負例も key 置換だけです ([s2-plan.md:371](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:371>))。
- 具体的な失敗シナリオ: §7.5 の `schema_version` 制約を逐語 v1 から「任意の非空 string」へ変更、または `revoked_at` を int から string へ変更 → key 集合は同じ 7 件 → `frozenset == _REVOCATION_KEYS` が成立 → 弱化した設計を `validate_repository` が誤受理。
- 深刻度: **blocker**
- 成果物影響: S-B の「exact schema を機械束縛済み」という proof が成立しない。

### SOL-A-02

- 主張: 0 件マッチは落ちるが、可視でない Markdown decoy を権威として読むため、見出し・表を実質削除しても緑になる。
- file:line 根拠: `_read_design` は raw text を読み、HTML comment だけを拒否し code fence を除外しません ([contract.py:272](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:272>))。新 extractor も raw `find` / regex を使う計画です ([s2-plan.md:197](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:197>), [s2-plan.md:237](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:237>))。これは既知の F170/F215 型です ([failures.md:4407](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/failures.md:4407>), [failures.md:5307](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/failures.md:5307>))。
- 具体的な失敗シナリオ: canonical な §7.5 見出し・表、または §10 段 6 行を閉じた ````markdown` fence 内へ移し、可視部分から削除・緩和する → raw marker と row は exact 1 件のまま → extractor と定数比較は緑。空集合にはならないため、非空 `frozenset` 防壁も発火しない。
- 深刻度: **blocker**
- 成果物影響: S-B と S-C の両 drift gate が「可視の設計正本」ではなく隠れた例示を検査できる。

### SOL-A-03

- 主張: P2 の 7 key 内容はユーザー裁定から一意に導けず、親が未裁定の受理集合を選んで `resolved` と記録している。
- file:line 根拠: 一次裁定が固定したのは path・7 key・0/1・UTC int までです ([rulings:718](</work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:718>))。brief も key 内容は裁定されていないと認めています ([s1-brief.md:71](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s1-brief.md:71>))。plan 自身が別の 7-key 案を構成しています ([s2-plan.md:396](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:396>))。さらに正本が参照する下位 exact 設計には、同じ bundle-digest path の別の exact 7-field schema が既にあります ([bundle-design.md:43](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:43>), [freeze-permanent-design-s2.md:432](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:432>))。
- 具体的な失敗シナリオ: `approval_sha256` / `scope` を持つ下位同型 R と、P2 の `authority_bundle_generation` / `revoked_active_pointer_raw_sha256` を持つ R → どちらも外側の裁定「exact 7 key」を満たすが相互に拒否される → 親の選択だけで受理集合が変わる一方、manifest では `CFAB-R1-REVOCATION-RECORD=resolved` になる ([s2-plan.md:276](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:276>))。
- 深刻度: **blocker**
- 成果物影響: R1 の解決記録と §7.5 schema authority が過剰主張になる。

### SOL-A-04

- 主張: P2 は terminal fail-closed を全履歴について閉じておらず、世代不一致・削除・同 digest 再承認の意味が不足している。
- file:line 根拠: `authority_bundle_generation` は単に int ≥ 1 で、X/A との一致がありません ([s2-plan.md:55](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:55>))。履歴拒否は「同じ path の別 bytes」だけです ([s2-plan.md:62](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:62>))。下位 exact 設計は変更・削除・rename・再追加をすべて明示拒否しています ([freeze-permanent-design-s2.md:452](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/freeze-permanent-design-s2.md:452>))。

  | 入力 | plan から導ける結果 |
  |---|---|
  | (a) 同一束の矛盾 R 2 件 | 同一 HEAD では同じ exact path に置けない。履歴上の別 bytes は、X 成立後なら terminal。ここは強い。 |
  | (b) 実在しない X | X が一度も成立していない repo なら下位 fallback ([bundle-design.md:54](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:54>))。成立済みなら参照不一致として terminal。 |
  | (c) 実在しない世代 | `generation=999`、ただし bundle/X hash は実在値、という R が制約を通る → 有効な束を誤って terminal reject。 |
  | (d) 同 digest の新 A | A だけなら旧 X の失効が続き terminal。さらに X2 を置いた場合、R が bundle 全体の吸収 tombstone か旧 X だけの失効かが未規定で、実装により受理が分かれる。 |

- 具体的な追加失敗シナリオ: valid X → R を追加 → R を削除 → 現 HEAD は valid X・R 不在、かつ「同 path の別 bytes」も無い → resolver が X を再受理できる。これは失効後の受理集合再拡大。
- 深刻度: **blocker**
- 成果物影響: `no-lower-fallback-fail-closed` と revocation の不可逆性が証明できない。7 key の多寡より、世代一致・scope・履歴不変 predicate の欠落が本体。

### SOL-A-05

- 主張: 段 6 の「構造 predicate」は ancestry と generation を十分に固定せず、不正な X が全 5 条件を満たす。
- file:line 根拠: parent は非 genesis parent を「既存 X」としか要求しません ([s2-plan.md:87](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:87>))。一方、既存設計の解決義務は live tip 一意性・parent 連鎖・世代を要求します ([bundle-design.md:342](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:342>))。祖先 rollback と世代非単調も既に禁止済みです ([bundle-design.md:217](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:217>))。
- 具体的な失敗シナリオ: valid chain `X0→X1` と承認済み A2 を用意し、X2 の parent を current X1 でなく既存 X0、`authority_bundle_generation` を A2 と異なる 999 にする。exact 5 key・raw filename・既存 parent・bundle digest・approval hash・承認済み A の全条件を満たす → fork/世代不一致 X を誤受理。
- 深刻度: **blocker**
- 成果物影響: 段 6 の構造的完了 proof が fork・rollback・世代偽装を許す。これらは S/B policy ではなく既決の構造条件なので、policy gate へ送れない。

### SOL-A-06

- 主張: 「段 6 完了 predicate」と称する一方、陽性・陰性 fixture の実体も実 entrypoint 呼出しも無く、設計自身の完了判定規則に違反する。
- file:line 根拠: 正本は path・内容・期待値を持つ陽性/陰性 fixture が無ければ exact predicate を書かないと定めます ([bundle-design.md:624](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:624>), [bundle-design.md:630](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:630>))。plan は generic な「陽性 1・陰性 5」という文だけを pin し ([s2-plan.md:185](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:185>))、X resolver 実走は保証しないと明記しています ([s2-plan.md:363](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:363>))。
- 具体的な失敗シナリオ: X entrypoint・fixture が存在せず、実装が reject-all または SOL-A-05 の fork を受理する状態 → docs extractor は期待 tuple/control 文と一致して緑 → 「構造 predicate 固定済み」を誤受理。既存 assignment gate が pending なので段 0 完了までは進まない。
- 深刻度: **must-fix**
- 成果物影響: S-C は完了 predicate ではなく未実行の語彙宣言に留まり、後続 wave が空証明を消費し得る。

### SOL-A-07

- 主張: DW-O09 の結論は正しいが、「path を持つのは 2 箇所だけ」という親の列挙は不完全。
- file:line 根拠: brief の全称主張 ([s1-brief.md:51](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s1-brief.md:51>)) に対し、tracked な insight にも exact path があります ([README.md:4](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/output/insights/2026-08-11_t657-stage0-rulings/README.md:4>))。
- 具体的な失敗シナリオ: tracked occurrence 全列挙を「2 件」として wave を受理 → historical mention の分類が抜けた inventory を完全閉包と誤認。ただし現存する追加 hit は pin ではない。
- 深刻度: **nit**
- 成果物影響: 現 wave の bytes 再発行は不要という結論には影響なし。brief の実測表現だけが不正確。

## 破れなかった防壁

- 段 0 status: `_applicable_unresolved_count` は seal が unresolved のため guarantee を除外し、S-SEAL と B の 2 件を数えます ([contract.py:610](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:610>))。plan 適用後も `pending=5 / applicable_unresolved=2 / blocking_gates=4` で、`require_stage0_complete` の四重 OR を通る経路はありません ([contract.py:901](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:901>))。
- hash 自己循環: `26aa…` は U1 前に plan で固定済みで ([s2-plan.md:290](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:290>))、U1 の helper 利用は「再適用して照合」であって期待値への代入ではありません ([s2-plan.md:322](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t657-stage0-fold/s2-plan.md:322>))。意図した 12 entries から独立再計算して同値を確認しました。実行時も entries・manifest literal・module pin を比較します ([contract.py:494](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:494>))。
- fixture 不変・他者 gate: fixture/row の独立 pin 経路は required-gates 部分と分離されており ([contract.py:775](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:775>))、`FREEZE-AX-TOPOLOGY` と `FREEZE-CONFORMANCE-LITERAL` は exact tuple と blocking status の双方で維持されます。
- policy 密輸: P4 は S1/S2、G-a/b/c、副作用の運用停止対機械検査を選んでいません。§8 の三先送りは維持されています ([bundle-design.md:468](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:468>))。
- pin 閉包: 現設計 doc の SHA-256 は tracked file に pin されておらず、`FROZEN_MANIFEST` にも含まれません ([test_frozen_artifacts.py:38](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_frozen_artifacts.py:38>))。DW-O10 不成立の結論は維持できます。
- failures 型タグ: 説明と実装の食い違い＝SOL-A-01/A-06、恒真保証＝SOL-A-01/A-02、親実測の一般化＝SOL-A-03/A-07。consumer 取り残し、hash 自己参照、期待値の後付けは攻撃したが現 plan では破れませんでした。

## 総括

- blocker の所見 ID: **SOL-A-01, SOL-A-02, SOL-A-03, SOL-A-04, SOL-A-05**
- 攻撃したが破れなかった主張: **段 0 incomplete の算出式、fixture/row pin、他者手番 2 gate、required-gates hash 三者照合、§8 の policy 先送り、設計 doc bytes pin 不在**
- 追加で読むべきだったが読めなかったファイル: **なし**