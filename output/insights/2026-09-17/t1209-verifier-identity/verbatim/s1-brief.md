# 段 1 brief — [T-1209] T126 qualification の code identity へ verifier の dsg/model/parse を含める

- wave: dev-wave-t1209-verifier-identity / branch worktree-dev-wave-t1209-verifier-identity / base = local main 1042a1bc9 (2026-09-17 00:3x JST)
- 研究前進 (土台): 論文主張「certified 選択の正しさ判定は記録された verifier 実装に束縛される」を T126 qualification 系列でも支える。
  現状 `REQUIRED_CODE_IDENTITY_PATHS` (orchestrator/qualification/contract.py:39-76) は verifier では `core.py` だけを pin し、
  serializability 判定の実体 (`dsg.py` の cycle 検出、`model.py` の依存型、`parse.py` の trace 解釈) の変更に series identity が反応しない。
  完了判定 = 新規取得の series-identity.json の `code_identity` key 集合に verifier 3 file が入り、いずれか 1 つの除去が test 赤になる。最小差分 = frozenset 3 行 + 包含 test 1 本。
- 確定済みユーザー裁定: 2026-08-17 /rulings 全件 第 5 回「含める」(entry 622: docs/archive/worklog-phase3-0817-622.md:483)。条件 = 過去の qualification 成果物は歴史記録として据え置き、以後の取得から新 identity を適用。
- 実測した前提: (a) repo 内に `code_identity` を持つ committed JSON は 0 件、live qualification は未実施 (docs/phase3.md:1313)。壊れる既存成果物なし。
  (b) contract.py の現 sha256 c50e2b05… / blob 6c1451b1… の pin は repo 内 0 件。path pin は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` (campaign_lock.py:107,204、HEAD blob と disk の live 比較。commit 後に整合、歴史 lock は不変) のみ。DW-O10 は非適用 (凍結 producer の出力に該当なし)。
  (c) 兄弟閉包 D442/D473 (campaign_lock) は verifier の core/dsg/model/parse/__init__/report/commit_receipt を既に束縛し、D442 は「別閉包 (T126) は追随しない」と明記 → 本 wave がその追随。
  (d) 編集面重複: branch tip 0 件、作業ツリー dirt は着地済み T-548 の Codex 子木 (t548-*, 生存 process 0) のみで contract.py には触れていない。
- 不変条件: I1 規律 2 を緩めない (verifier の判定・受理集合の意味論に触れない)。I2 変更は identity 集合の純増のみ — schema_version、hash domain、`series_identity()` の検証意味論、`REQUIRED_SCRIPT_IDENTITY_PATHS`、campaign_lock 閉包、凍結 manifest は変えない。
  I3 互換層・census gate・台帳・一般化を足さない (DW-G05、依頼の scope 外指定)。I4 実装面は Codex author のみが書く。I5 3 台帳は spool fragment。
- 変更面 (実アンカー):
  | file | anchor | 変更 |
  |---|---|---|
  | orchestrator/qualification/contract.py | :75 `"orchestrator/verifier/core.py",` | 直後に `orchestrator/verifier/dsg.py` / `model.py` / `parse.py` を追加 (frozenset なので順序は identity に無関係、可読性のため core の隣) |
  | orchestrator/tests/test_t126_pegasus_tools.py | :1505 `test_required_code_identity_closes_activation_receipt_imports_without_records` の隣 | 独立 test: verifier 4 file (core + 新 3) ⊆ REQUIRED_CODE_IDENTITY_PATHS を個別に assert (T316/T529 の先例と同型)。既存 parametrized `test_every_required_identity_path_is_tracked_in_this_repo` は 3 node 自動増 |
- 成果物: commit (author 実装 + 親の記録)、output/insights/2026-09-17/t1209-verifier-identity/ (README + verbatim)、spool fragment (worklog / decisions)、変異 matrix、受入全走。
- 割れうる前提 (親の provisional 裁定・攻撃対象):
  (P1) 追加は裁定が名指す 3 file だけ。`core.py` の import 閉包に同居する `verifier/__init__.py` (pipeline.py が `from ..verifier import` で辿る dispatch 面)、`report.py`、`commit_receipt.py` (artifacts.py が直接 import) は裁定外・scope 外として足さず、real なら裁定パッケージでユーザーへ返す (DW-S04)。
  (P2) 歴史成果物への互換層は作らない。repo 外に旧 key 集合の series があっても新 code の `series_identity()` は required set mismatch を返すが、それは裁定の条件 (歴史記録として据え置き) の受容範囲。
  (P3) 包含 test は repo 不変条件の test であって受理集合を変える gate ではない (D473 決定 4 と同じ位置づけ)。DW-O13 の新設 gate に当たらない。
  (P4) fixture (`_attempt`) は generic path を `fixture {relative}` で埋めるので新 path に追加対応は不要。
- 分割方針: 実装子 1 本 (contract.py + test 1 本、所有は両 file)。段 3 consult 2 本 (レンズ A = 受理集合・歴史成果物・裁定逐語との整合、レンズ B = 変異で殺せる test か・identity 経路の consumer 取り残し (t126_driver/identity/collector/submit script/fixture))。段 6 review 2 本。
- 受入・実測環境: 受入全走は `tools/dev_wave_wait.py acceptance --lease-optional` (計算ノード)。変異 matrix は `tools/mutation_worktree.py` 系 (段 4 で事前登録)。
