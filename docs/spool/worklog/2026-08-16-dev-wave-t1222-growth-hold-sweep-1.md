---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1222-growth-hold-sweep
seq: 1
title: 成長比例テストの母集合を REAL_REPO_SERIAL_NODES の外へ広げ、実 check_docs を起動する 3 node を恒久保留した — 子の推奨 74 件のうち 71 件を実測で却下し、親の裁定を 2 件撤回した (コード + テスト + docs、branch worktree-dev-wave-t1222-growth-hold-sweep、変異 matrix = 4/4 KILLED)
---

## 本文

[T-1222] の wave。段 2 の全件走査は候補 230 件・登録推奨 74 件を出したが、親は
**3 件だけを登録**し、71 件を却下した。却下は実測に立脚する。

### 判定式を先に固定した

D335 の「repository の成長に比例する構造」を、**秒数の閾値ではなく入力集合の性質**で判定する
({{D:growth-hold-input-set-criterion}})。この式が無いと「file が増えればコピー量も増える」
という発火しない一般化で、ほぼ全テストが比例になる。

### 30 日ぶんの部分木成長を同一手続きで数えた

`git ls-tree -r -l` を各時点の commit へ適用した。repo 全体は 845 file → 12,685 file、
docs は 56 file / 1,968 KiB → 510 file / 14,097 KiB へ増えた 30 日間に、copytree 系 fixture が
写す 4 部分木 (`.claude/agents` 13、`.codex/role-adapters` 13、`orchestrator/codex_roles` 8、
`tools/task_runs` 7) は **14 日前から現在まで file 数が変わっていない**。
`tools/task_runs` だけは 30 日前に 0 file (未作成) で、作成時の 1 回の段差を持つ。

### 親が自分の裁定を 2 件撤回した

段 6 の敵対レビュー 2 本が、親の裁定文の誤りを独立に突いた。どちらも real で撤回した。

1. **「copytree 対象 4 部分木は 1 file も増えていない」は誤り**だった。上記のとおり
   `tools/task_runs` は 0 → 7 である。分類も「非比例」から「比例だが設計上限のある
   固定用途集合」へ改めた。結論 (登録しない) は変えていないが、理由の書き方を変えた。
2. **「provenance の実 repo 2 node は固定歴史なので非比例」は誤り**だった。
   `_audit_history` は毎回 `_scope_policy_commit()` / `_implementation_policy_commit()` を呼び、
   これは現在の HEAD に対して `git log -S … -- docs/ai-provenance.md` を走らせる。
   親は `_commit_range` と `_build_ancestry` だけを見て断定していた。tip 依存の項は実在し
   (実測 0.046 秒 / 全体 3.78 秒)、比例と認めたうえで D451 で見送った。

### 71 件を却下した理由は 2 つある

第一に上記の入力集合。第二に、`test_dev_waves_integration.py` へ guard binding を入れると
**保留対象外の node が既定で赤になる**。同 file は fresh subprocess で自分自身を package import し、
その利用者 `test_socket_roundtrip_works_beyond_108_byte_repository_path` は推奨 40 件に入っていない。
段 2 は self-loader 無しと判定していた。2026-08-16 の `test_s8b_floor_campaign.py` と同型である。

また、代替経路の主張も成立しなかった。production が同じ関数を呼ぶのは正常系だけで、
保留対象が検査しているのは tamper・drift・duplicate key・bijection 違反の**拒否経路**である。
71 件を保留すると 112 pytest item の検出力が既定ゼロになり、除ける費用は合計約 2.8 秒だった。

### 母集合は閉じていない ({{F:primitive-sweep-misses-in-process-calls}})

段 2 の 230 件は少なくとも 11 top-level node を落としていた。落ちた理由は構造的で、
探索 primitive の文字列検索 (`(?:check_docs|check_ai_provenance)\.py` など) は
**production の重い関数を同一プロセス内で呼ぶ形**を拾えない。親とレンズ B が独立に
`test_s8c_preregistration_invariant.py:274` の `check_docs.main()` を検出した。

### ユーザー提示 (D335)

正しさゲートを担う 3 件を保留した。失う固定検査、残る経路とそれぞれが走らない条件、
`test_check_docs.py` の素の `python3` 実行が file 全体で拒否されるようになったことは
`output/insights/2026-08-16_t1222-growth-hold-sweep/` と各 row の `collateral_note` に置いた。

**受入 wall の短縮は主張しない。** 取り除いたのは観測条件下で約 16 秒ぶんの subprocess
elapsed 総和であり、critical path と net wall 差は未測定である。

### 変異の期待 node は probe で再導出した

初回登録は 4 件中 3 件が MISMATCH だった。変異が検出されなかったのではなく、
1 つの registry 変異が contract 側 2 node と inventory 側 2 node を同時に赤にするためで、
親の期待集合が不完全だった。probe の実測から完全集合を再導出して本走し 4/4 KILLED。

### 段 8 の裁定

候補は 2 件。(1) 段 6 レビュー A の待ち手が producer 生存中に rc=0・出力空で返った件は
F268 の再発として台帳へ追記した (6 本中 1 本)。(2) `tools/mutation_worktree.py` の本走が
`--detached` を要求する件は、tool 自身が plan-only 時に fail-closed の明示メッセージを出すため
**docs は編集しない** (機械代替済み。入口・reference の byte 予算を消費しない)。

### scope 外の real 所見 1 件

`tools/hold_inventory.py` の bypass 台帳は、現在の実装が二層で拒否する 4 経路を
`known-unresolved-bypass` と報告している。`test_hold_inventory.py` が古い表現を固定しているため、
誤報が検査で守られている。**本 wave が作った穴ではない。**

## 次の一手差分

### 完了

- [T-932] `REAL_REPO_SERIAL_NODES` の外に残っていた 5 候補 (`test_s8b_ratified_verify.py` /
  `test_check_docs.py::test_real_repo_clean` / `test_s8c_preregistration_invariant.py` /
  silo ladder 2 件) と copytree 系 fixture 2 file を、実測つきで全件裁定した。
  母集合の未閉包という残件は [T-1222] が引き継ぐ。
  remaining: none
  base: f30c2d3b140991f96d1a82757d4ff3394c21307ef6aefe3983fe1d637c2f8260

### 更新

- [T-1222] **P1・部分完了 (母集合は閉じていない)**: 名指し 5 候補と copytree 系 2 file を
  裁定し、実 `check_docs.py` を起動する 3 node を恒久保留へ登録した (56 → 59)。
  71 件は入力集合が設計上限のある固定用途集合であること、および guard binding が
  保留対象外 node を赤にすることを理由に却下した。**残件**: 段 2 の全件走査は
  少なくとも 11 top-level node を落としており、`module.func(ROOT)` 形の in-process 呼び出しを
  拾う探索が要る。既知漏れ (`test_codex_agents.py` 7 / `test_dev_waves_integration.py` 1 /
  `test_s8c_preregistration_invariant.py:257` 1 / `test_check_ai_provenance.py` 2) は
  比例と判定済みだが D451 の個別裁定が未了である。
  base: 00163cd86328aa9373ad7142a025cc40090cd28edd501bb548daecb86f3683f3

### 新規

- {{T:hold-inventory-bypass-surface-stale}} **P2・新規**: `tools/hold_inventory.py` の
  `bypass_surface` が、plain runner・`--noconftest`・`--confcutdir`・direct call を
  `known-unresolved-bypass` と報告する。現在の実装は import 時の `enforce_held_functions` と
  call 時の `_wrap_held_function` の二層でこれらを拒否しており、記述と実効挙動が逆である。
  `test_hold_inventory.py` が古い表現を固定しているため、誤報が検査で守られている。
  ユーザー向け hold inventory が実効受理集合を実際より弱く報告する。
