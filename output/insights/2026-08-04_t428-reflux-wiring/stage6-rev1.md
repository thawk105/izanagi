静的レビューの結論は **NO-GO**。pytest は指定どおり実行していない。

署名 1 の key 閉包＋`parse_wire`、署名 2 の `strip()` 後 32 正準 membership、署名 3 の WAL 構造・source/receipt・commitment 検証は実在する。また nonce は `os.urandom(32)` で生成され commitment に含まれるため、commitment 単体への 32 点辞書攻撃は成立しない。裁定が非主張とした「WAL 上の mask＋sha 連動改変」は所見に数えていない。

## 所見

所見 1: producer-time の predicate↔binding byte-exact 結合が gate ではなく、別々の引数を正しく渡す caller 慣習に留まる [捏造/幻覚][恒真ゲート]  
/ 根拠: [`_quarantine_and_audit` は coder から predicate を作るが別引数 binding と比較しない](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:353>)、[`run_campaign` は binding の型と source-null しか検査しない](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/loop.py:119>)、[`pipeline.evaluate` はその mask/sha を任意の現 SourceEvidence へ付け替える](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/pipeline.py:643>)。テスト自身も predicate の実在を示さない mock source に mask=20 を結合して certified としている（[test_campaign.py:2070](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_campaign.py:2070>)）。  
/ 攻撃シナリオ: 正準 predicate A を materialize・検疫した後、自己整合する binding B を `run_campaign` へ渡す。pipeline は source A の receipt を binding B に束縛し、replay/admission は mask B↔sha B と source A↔receipt A を別々に検証して通す。これは裁定が非登録とした事後の連動改変ではなく、producer API の取り違えである。  
/ 成果物影響: binary/source は A なのに WAL・provenance・report は候補 B を指し、certified 選択理由と実体が分離する。  
/ 提案: materializer が IR・正準 predicate bytes・SourceEvidence を一体化した sealed receipt を発行し、loop/pipeline はそれ以外の binding を受けないようにする。最低限、coder A＋binding B の交差 32×31 負例を sink と pipeline の双方へ置く。  
/ severity: blocker 候補

所見 2: proposal campaign は lock/WAL を機械 sweep 形へ書き換えると binding 要求を downgrade できる [恒真ゲート][ドリフト]  
/ 根拠: proposal 判定は marker または `axis+reflux` 等だけ（[wal.py:646](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:646>)）、機械判定は forge 可能な `generator/space` 文字列だけ（[wal.py:659](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:659>)）。artifact admission は campaign ID を directory basename から採り、lock preimage から再計算しない（[artifact_admission.py:463](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/artifact_admission.py:463>)）。現テストは `reflux` を残した marker 欠落と、独立した正常 machine の二例だけである（[test_artifact_admission.py:278](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_artifact_admission.py:278>)）。  
/ 攻撃シナリオ: 有効な proposal artifact から marker・`reflux`・`trigger_binding` record・build_start commitment を削除し、`generator="reason-subset-v1"` と固定 `space` を追加する。receipt は coder-authored のままでも分類器は見ず、machine exemption として admission を通す。  
/ 成果物影響: proposal 由来の certified 点が binding/provenance 検証なしの機械 sweep として formal report・台帳へ混入する。  
/ 提案: lock から campaign ID を再導出し、機械 sweep は sealed generator receipt、non-coder admission class、完全な lock key closureを一体で要求する。proposal→machine 変換を直接行う負例を追加する。  
/ severity: blocker 候補

所見 3: commitment-only 開示境界は recipient sink で閉じておらず、auditor が raw wire/mask を WAL・report・critic・trial report へ反射できる [恒真ゲート][ドリフト]  
/ 根拠: auditor の `violations/nits` は任意の `list[dict]` を許す（[auditor_gate.py:125](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/auditor_gate.py:125>)）うえ、辞書全体を文字列化して evidence にする（[auditor_gate.py:78](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/auditor_gate.py:78>)。それが abort payload に保存され（[p3_s4_loop.py:245](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop.py:245>)）、Layer3 は専用 record 以外の payload を丸ごと複写する（[layer3_report.py:100](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/layer3_report.py:100>)）。critic も evidence をそのまま描画する（[digest.py:642](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/critic/digest.py:642>)）。  
/ 攻撃シナリオ: working diff を見た auditor が、正しい digest と reject verdict に `violations=[{"wire":"10100","mask":5}]` を添える。型検査を通り、専用 `trigger_binding` record の外へ raw 値が永続化・投影される。  
/ 成果物影響: critic が具体候補と勝敗を取得して次提案を変え、Layer3/trial report にも raw 候補が残る。  
/ 提案: raw auditor 出力は非投影領域へ隔離し、WAL/report/critic には閉じた violation code のみ渡す。provenance・report・harness outcome にも recursive reserved-field 検査ではなく、任意文字列を持たない exact projection schema を設ける。nested raw 値を含む auditor reject の負例を追加する。  
/ severity: blocker 候補

所見 4: raw binding と build_start の二回 fsync が、新しい回復不能クラッシュ窓を作る [セッション死・救出]  
/ 根拠: WAL append は一 record ごとに fsync する（[wal.py:367](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:367>)）。`log_trigger_binding` の完了後に別 append で build_start を書き（[wal.py:548](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:548>)、[pipeline.py:679](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/pipeline.py:679>)）、validator は raw/start の attempt 集合完全一致を要求する（[wal.py:730](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/wal.py:730>)）。  
/ 攻撃シナリオ: raw binding の fsync 完了直後、build_start 前に SIGKILL・停電する。newline 完結 record なので truncated-tail repair は除去せず、以後すべての replay/admission が「一対一でない」で停止する。裁定 W1 の既存 crash-after-start とは異なる、本 diff 導入の crash-before-start である。  
/ 成果物影響: 同 campaign の過去の certified 点まで admission/critic/report から読めなくなり、セッション継続に手修復が必要になる。  
/ 提案: binding＋start を単一 transactional frame として耐久化するか、末尾 orphan binding を証拠付き recovery-abort/tombstone へ収束させる。二つの fsync 間へ fault injection する境界テストを置く。  
/ severity: blocker 候補

所見 5: planner axis は loader・direct construction・sink の全てで未検査で、M-C3 のテスト名が実際の保証範囲を過大表示する [捏造/幻覚][ドリフト]  
/ 根拠: `PlannerProposal` は受動 dataclass のまま（[p3_s4_loop.py:102](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop.py:102>)）、combined loader は値をそのまま構築する（[p3_s4_loop_trigger_gating.py:592](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:592>)）。`test_axis_mismatch_rejected_by_loader_and_direct` は coder axis だけを変更している（[test_p3_s4_loop_trigger_gating.py:1347](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1347>)）。  
/ 攻撃シナリオ: planner axis を sort/backoff にし、coder axis と wire は trigger のまま combined loader または direct API へ渡す。materialize/build は進み、whiteboard だけ誤軸 proposal を記録する。  
/ 成果物影響: binary は正準でも proposal・whiteboard・provenance の軸帰属が分裂し、軸別の停止判断と後続提案が汚染される。  
/ 提案: loader と最終 sink の双方で `planner.axis == coder.axis == MARKER_ID`、型、direction/magnitude enum を再検査する。静的変異対応は M-A1〜A6・M-B1〜B9・M-C1/C4 は識別可能だが、M-C2 は広い正例のみで exact 注入位置・単一理由が未固定、M-C3 は planner 側が現に受理される。DW-M01 証拠をその粒度で再照準する。  
/ severity: 要検討

所見 6: `--no-build` の pass と fresh fixture は、生成直後の artifact admission に自ら拒否される [セッション死・救出][ドリフト]  
/ 根拠: no-build pass は WAL を書かず `dry-pass` を返す（[p3_s4_loop_trigger_gating.py:496](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:496>)）が、`drive_iteration` は checkpoint 保存後に無条件で critic digest を生成する（[p3_s4_loop_trigger_gating.py:677](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop_trigger_gating.py:677>)。digest は admitted campaign を要求し（[p3_s4_loop.py:272](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/campaign/p3_s4_loop.py:272>)）、admission は WAL と proposal provenance を必須にする。fixture テストは `run_one_iteration` と `make_critic_digest` の双方を mock してこの衝突を隠す（[test_p3_s4_loop_trigger_gating.py:560](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t428-reflux-wiring/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:560>)）。  
/ 攻撃シナリオ: fresh layout で auditor pass の `--no-build --run-iteration`、または proposal 指定なし fixture CLI を実行する。前者は WAL 不在、build fixture は provenance 不在で digest admission が例外になる。  
/ 成果物影響: checkpoint/provenance だけ進んで CLI は失敗し、配線確認・dry-run の digest と正常終了が得られない。  
/ 提案: dry-pass/fixture を admitted-campaign consumer へ渡さない専用 preview 経路に分けるか、非 build attempt の閉じた WAL/provenance schemaを定義する。実 `make_critic_digest` を mock しない fresh-layout CLI テストを追加する。  
/ severity: 要検討

## 総括

最重要 3 件は以下。

1. predicate A と binding B を producer が結合でき、署名 3 の後段検証を通る。
2. proposal artifact を機械 sweep に偽装して binding 要求を外せる。
3. auditor の自由形式 evidence から raw wire/mask が critic・report へ反射する。

全体判定は **NO-GO**。加えて、新設された binding→build_start 間のクラッシュ窓が campaign 全体を回復不能にし、M-C3 と dry-pass/fixture の実装・テストにも独立した欠落がある。