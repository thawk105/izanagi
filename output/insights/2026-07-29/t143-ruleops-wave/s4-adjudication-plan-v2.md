# T-143 RuleOps — 段4裁定 / plan v2

## 裁定要約

- 段3 finding は安全レンズ 11 件、実効性レンズ 10 件。重複を統合して **real 21 / refuted 0**
- A-1〜A-3、B-1〜B-3 の NO-GO は採用。plan v1 の「retirement proof」設計は破棄する
- P1 は採用: CLI は read-only で `delete/move/apply/archive` を持たない
- P2 は差し替え: v1 は evidence の内容が削除安全を証明すると主張せず、候補 package の構造・
  blob pin・未裁定 hit を検査して人間裁定へ送る
- P3 は採用: HEAD tree の動的 inventory + 明示候補 ledger。全 348 件の事前登録は行わない
- 親の byte 実測は worktree bytes を数えたため誤り。HEAD tree の正しい値は test
  97 / 2,726,974 bytes、insight 251 / 7,860,617 bytes。固定値を実装へ転写しない
- 成果物影響: 本 wave は correctness / certified 選択 / proof chain を変えず、回収候補を
  再現可能な package としてユーザー裁定へ運ぶ導線を新設する

## finding 裁定

| finding | real/refuted | scope | 採否 |
|---|---|---|---|
| A-1 / B-2 receipt 自己申告 | real | producer は外、過大主張是正は内 | evidence は advisory、実験証明を名乗らない |
| A-2 test 同時候補循環 | real | 内 | ledger 全候補を依存先から除外 |
| A-3 / B-1 package 自己参照 | real | 内 | exact control artifact だけ除外し、除外 hit も出力 |
| A-4 / B-6 semantic/history 過大表現 | real | 内 | `observed_hits` / `pickaxe_events` に改名し、人間 review signal に限定 |
| A-5 receipt epoch | real | 内 | target/evidence current blob pin を検査。古い receipt を安全証明にしない |
| A-6 / B-3 authority と retention の混同 | real | 内 | state authority と retention class を分離し、legacy は人間分類 |
| A-7 D96 境界 | real | 内 | 潜在的受理集合変更は新 D + 境界 test が必要と lifecycle に明記 |
| A-8 / B-4 実効 gate 不在 | real | 内 | acceptance run に軽量 schema check、`inspect --draft` と実 checkout dry-run |
| A-9 / B-10 親実測・族一般化 | real | 内 | HEAD 値へ erratum、共通化は inventory primitive のみ |
| A-10 実削除状態遷移 | real | docs は内、実削除は外 | proposed→human ruling→fresh pin→別 deletion commit を規定 |
| A-11 nested test 外延 | real | 外 | 現 HEAD は nested 0。将来の裁定候補 |
| B-5 schema / CLI 未確定 | real | 内 | exact key/type/enum/limit、canonical JSON、rc 表を固定 |
| B-7 replace/grafts | real | 内 | Git env scrub、replace/graft/shallow 拒否、timeout |
| B-8 AST node 過大表現 | real | 内 | AST を安全証明に使わず、symbol は inspect signal のみ |
| B-9 basename 過剰拒否 | real | 内 | full path / 解決済み link を signal、basename は一意時のみ補助 |
| C-1 staged deletion 強制 | real | 外 | v1 は削除 gate と呼ばない |
| C-2 mutation producer | real | 外 | 別 wave / 裁定 |
| C-3 既存 insight 移行 | real | 外 | inventory-only、個別候補として人間分類 |
| C-4 node 単位 retirement | real | 外 | v1 は file 単位 |

## plan v2

### 実装子の所有

単一 Codex author がコードとテストだけを編集する。

- `tools/ruleops.py`: stdlib-only read-only CLI
  - `inventory`: HEAD tree の test / insight inventory を canonical JSON で出す
  - `inspect PATH [--query TEXT] [--draft]`: metadata、observed literal/link/pickaxe signal、
    人間が埋める candidate draft を出す
  - `check [--ledger PATH]`: exact schema、blob drift、候補間循環、control artifact 除外、
    unresolved review を検査する
  - 成功出力は `structurally_valid`, `candidate_count`, `human_approved: false` に限定し、
    `safe` / `eligible` / `approved` を出さない
- `tools/run_tests.py`: acceptance run の軽量 preflight として production ledger の `check` を呼ぶ
- `tools/check_docs.py`: `docs/ruleops.md` を living doc として登録する
- `orchestrator/tests/test_ruleops.py`: synthetic repo と real checkout dry-run の境界検査
- `orchestrator/tests/test_run_tests_preflight.py`: RuleOps preflight の発火・失敗伝播・targeted 非発火
- `orchestrator/tests/test_check_docs.py`: living doc の独立 literal pin / 消失 positive control

### 親の所有

- `docs/ruleops.md`: v1 契約、CLI/rc、test/insight の証拠差、D96、人間裁定、削除の別 commit 境界
- `docs/ruleops-candidates.json`: authority のない空 ledger。通常 artifact の追加には追随不要
- `docs/README.md` / `output/README.md`: RuleOps への導線と proof-chain / 正式 report 対象外
- `orchestrator/tests/README.md`: 新規 pytest-only test の allowlist
- phase / decisions / worklog / handoff / review verbatim の記録

### v1 の固定境界

- 対象: HEAD の direct `orchestrator/tests/test_*.py` と tracked `output/insights/**` regular file
- 対象外: campaign、WAL、lock、freeze、正式 report、env、submodule、docs/failures、node 単位
- Git: non-shallow、replace refs / grafts 無し、read-only subcommand allowlist、timeout、env scrub
- ledger: duplicate key / unknown key / 非 UTF-8 / path traversal / symlink / gitlink / blob drift を拒否
- reference/history は観測 signal。完全性・削除安全・受理集合同値を主張しない
- empty ledger は構造 canary。`inspect --draft` の real checkout dry-run を受入へ加える

## 変異事前登録

| ID | 単一変異 | 期待する単一の赤 |
|---|---|---|
| M1 | test scope regex を空集合化 | literal inventory set test |
| M2 | insight scope を `output/**` へ拡大 | scope positive control |
| M3 | HEAD blob size を worktree `stat()` へ置換 | dirty-worktree invariant |
| M4 | unknown ledger key を許可 | strict schema test |
| M5 | control artifact 除外を削除 | committed non-empty package self-reference test |
| M6 | 他候補を replacement/source に許可 | ledger-wide cycle test |
| M7 | unresolved observed hit を無視 | unresolved review test |
| M8 | basename hit を常時 hard rejection | duplicate-basename positive control |
| M9 | `human_approved` を true、または `safe` field を追加 | output exact-key literal test |
| M10 | acceptance preflight の RuleOps 呼出しを除去 | runner preflight integration test |
| M11 | `delete` subcommandを追加 | CLI command closed-set test |
| M12 | replace/graft/shallow check のいずれかを除去 | hardened Git negative matrix |

各変異は author 実装後に実位置を照合する。同じ入力を先に拒否する gate がある変異、または複数理由で
赤になる変異は matrix へ採用せず、最初の実効 gate へ再照準する。

## scope 外の裁定パッケージ

- 実削除を staged diff と human approval receipt に機械束縛する C-1
- mutation 実験を生成・隔離・復元し producer-bound receipt を作る C-2
- 既存 251 insight の型移行 / archive / tombstone C-3
- test file 内 node 単位の価値判定 C-4
- nested test が初めて現れた時の外延拡張 A-11
