---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t770-conditional-unrun
seq: 1
title: template patch 未適用の 4 skip を「条件付き未実走」へ別分類した — 裁定 R1 (b) + R2 (a) を実装、変異 4/4 KILLED (コード + docs、branch worktree-dev-wave-t770-conditional-unrun)
---

## 本文

- 依頼は「[T-770] を裁定どおり実装」。裁定 (エントリ 403) は R1 = (b) patch 窓は開けず
  README / census の分類を「条件付き未実走」へ正す + (c) 隔離 checkout の境界テストは別途起票、
  R2 = (a) 分類語を改める。**(c) は裁定文が「別途起票」と定めているため本 wave では実装せず
  起票した。**
- **裁定の前提を段 1 で実測し、覆っていないことを確認した。** wave 前 HEAD `0c0fbf25` で
  計算ノード request `901500.nqsv`、対象 4 node は 4 skipped / 2.75 秒 / rc=0、理由文は 4 本とも
  「template patch 未適用 …」。`test_source_digest_fixed_variant_distinct` に `_require_g13()` が
  無いことも静的に確認した (窓を開けないので guard は足していない)。
- **軽量版で回した。** 設計択一が割れず、正しさ防壁に触れず、受理集合も変わらないため段 2・3 と
  段 6 の review 子を省いた。実装面は Codex `role=author` 1 本 + fix 子 1 本。
- **親が段 6 で挙げた所見 1 件を fix 1 巡で閉じた。** 段 5 の実装で 4 node の skip 理由文から
  機構名「template patch 未適用」が落ちていた。これは親 brief が「node 固有の条件だけを残す」と
  書いた結果であり実装子の逸脱ではない。worklog・failures・裁定パッケージの census はすべて
  この語でこの 4 件を数えているため、受入出力からこの語が消えると census 側の grep が 1 件も
  当たらなくなる。4 本とも復元した。
- **焦点走で出た赤 2 件は差分に帰属しない (DW-O18)。** `test_real_repo_serialization.py` の
  `test_ratified_memo_has_a_real_resolution_payer` と
  `test_protocol_builder_repo_tree_guard_is_wired_to_real_root` が
  `ModuleNotFoundError: No module named 'tests'` で赤になった。両 node の `from tests import ...` は
  `orchestrator/` が `sys.path` に載っていないと解決せず、載せているのは `test_reflux_ir.py:122` の
  module import 副作用だけである。焦点走がそのファイルを収集していないための偽赤で、本 wave の
  差分は当該 import 経路に到達できない。この隠れ結合自体は実在する所見なので scope 外として起票した。
- **本 wave が導入した機械 pin は 1 本。** `test_skip_classification.py` が AST 結線・真の依存物不在
  skip を巻き込まない正例・理由文の中身・README census の 4 本を持つ。裁定は検査新設を要求して
  いないが、(i) 本タスク自体が分類ドリフトの実害であり、(ii) 検査が無いと変異 matrix が空になる、
  の 2 点を根拠に親が採用した。対象 vector の既存被覆を性質で先に検索し、skip 理由文または
  README 分類を assert する検査が 0 件であることを確認している。
- **凍結済みの census は編集していない。** `output/insights/2026-08-11_known-red-exceptions/README.md`
  と `docs/archive/worklog-phase3-0811-395.md` はどちらも記録であり、前者は census 表の当該行を
  既に「repo 内で満たせる前提」と正しく分類したうえで正本を `orchestrator/tests/README.md` と
  明示している。訂正は living 正本と本エントリで行った。
- **wave 中に local main を 1 回取り込んだ** (`f4db7036`、10 commit)。incoming が触った
  `orchestrator/tests/` の path は本 wave の編集面と重ならず、automatic merge で競合ゼロだった。
- 逐語と変異台帳は `output/insights/2026-08-11_t770-conditional-unrun/`。

## 次の一手差分

### 完了

- [T-770] 分類是正を実装し、変異 4/4 KILLED で裏取りした。裁定の (c) と compiler 解消後の
  再検討は {{T:conditional-unrun-boundary-run}} へ送った。
  remaining: none
  base: 2266a959f36335b6c707052311e0300ae7509be115465ba0c5ba56f6d34b7fbc

### 新規

- {{T:conditional-unrun-boundary-run}} **P2・新規**: 「条件付き未実走」の 4 node を実際に
  走らせる経路を決める。ルート A = 隔離 checkout ([T-770] R1 (c) の裁定。`tools/mutation_worktree.py`
  と同型の使い捨て worktree をテストが作り patch を当てる。実 submodule を触らないが受入全走が
  submodule clone のコストを毎回払う)。ルート B = [T-747] の pinned compiler blocker が解けた後の
  受入 suite 直接窓開け ([T-770] R1 (a) の再検討。回収が 2 node から 4 node へ増えるため裁定が
  変わりうる。`test_source_digest_fixed_variant_distinct` への `_require_g13()` 追加を伴う)。
  塞がないままの成果物影響は source digest の alias 防止・未定義 macro の fail-closed・
  hook 編集面の実 template 結線が受入全走で恒久未検査であること。
  正本 = `orchestrator/tests/README.md` の「条件付き未実走」節と
  `output/insights/2026-08-11_known-red-exceptions/package.md` の R1。
- {{T:reflux-sys-path-hidden-coupling}} **P3・新規**:
  `orchestrator/tests/test_real_repo_serialization.py` の 2 node が `from tests import ...` を使い、
  `orchestrator/` を `sys.path` へ載せているのが `test_reflux_ir.py:122` の module import 副作用
  だけになっている。当該ファイルを収集しない選択走では `ModuleNotFoundError` で赤になる
  (2026-08-11 に request `901504.nqsv` で実測)。全走では緑なので受入は素通りするが、焦点走・
  二分探索・単一ファイル再現のたびに偽赤を生む。選択肢 = (a) conftest で `orchestrator/` を
  明示的に載せる / (b) 2 node 側を `orchestrator.tests` 経由の import へ直す / (c) 現状維持で
  README の「二重 runner」節に既知事項として書く。
