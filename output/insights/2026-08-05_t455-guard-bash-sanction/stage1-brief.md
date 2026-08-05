# 段 1 brief — [T-455] guard_bash sanctioned path へ fetch_third_party.py を追加

wave: dev-wave-t455-guard-bash-sanction-fetch / branch: worktree-dev-wave-t455-guard-bash-sanction-fetch
repo (worktree): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t455-guard-bash-sanction-fetch

## scope

確定済みユーザー裁定 (2026-08-04 /rulings、択 (a)) をそのまま実装する。

1. `hooks/guard_bash.py` の `_SANCTIONED_PATHS` (`:174`) へ `tools/pegasus/fetch_third_party.py`
   を 1 件だけ追加する。理由 comment を既存 entry と同じ粒度で添える。
2. `orchestrator/tests/test_hooks.py` へ、追加の受理集合変化を pin するテストを足す。
   - 正例: `python3 tools/pegasus/fetch_third_party.py fetch` 等の exact 綴りが
     `PEGASUS_LOGIN` で通る (`./tools/pegasus/...` 直起動と、fetch/hydrate/verify の代表 subcommand)。
   - 過剰拡大の positive control: 非 sanctioned な兄弟 (`tools/pegasus/exec_calibrate.py`,
     `tools/pegasus/collect_receipt.py`) は `PEGASUS_LOGIN` で拒否のまま。
   - exact 性: repo 内に当該ファイルが実在することを meta-test で固定する
     (既存 `test_bash_login_sanctioned_entries_are_exact` と同じ形)。

scope 外 (実装しない):
- 一律 `tools/pegasus/` 判定を allowlist/denylist へ変える択 (b)。裁定で不採用。
- 下記 (P2) の借用経路の族修正。裁定パッケージで返す。

## 確定済みユーザー裁定

- 択 (a) 採用。根拠 = 実測分類 local-ok + 「network を要する段は login でしか成立しない」構造 +
  `submit_silo_ladder_rung1.sh` との同型性。
- 防壁変更につき `hooks/README.md` の契約と `orchestrator/tests/test_hooks.py` に従う。

## 段 1 前提実測 (2026-08-05、pegasus02 = login node、本 worktree)

裁定の 3 前提をすべて実物で確認した。模擬なし (hook を実 subprocess で起動し実 stdin を与えた)。

1. **拒否は実在する。** `python3 tools/pegasus/fetch_third_party.py --help` を `hooks/guard_bash.py`
   へ与えて rc=2 / 「非 sanctioned Pegasus 実行体」を再現。
2. **local-ok 分類は land 済み。** `docs/pegasus-runbook.md` §7.0 の実測表に fetch (cold/warm)、
   hydrate、verify/verify-deps の 4 経路が載り、certified peak の最大は 222 MiB
   (規範値 512 MiB 未満)。sanctioned 化は全 subcommand を同時に開くが、4 経路すべてが local-ok
   なので裁定根拠の射程内。
3. **同型先例は実在する。** `submit_silo_ladder_rung1.sh` は `guard_bash.py:182` で既に sanctioned。

## 不変条件

- `hooks/README.md` は「sanctioned exact path の一覧と判定は `guard_bash.py` が正本、
  ここへは写さない」と定める。**README へ一覧を書き足さない。**
- 受理集合の変化は「`tools/pegasus/fetch_third_party.py` の exact 綴り 1 本を login/SUSPECT で
  通す」だけ。他の pegasus 実行体・他 head の判定を動かさない。
- 既存テストの期待値を変更しない。緩和・skip・削除を禁じる。
- 実装面 (コード・テスト) は Codex `role=author` が書く。親は直接編集しない。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 追加は `_SANCTIONED_PATHS` の 1 行のみで足り、`_script_target` /
  `_is_sanctioned` / `_heavy_segment_violation` の分岐は変更不要である。
  根拠 = `_script_target` は既に `tools/pegasus/` 前置の候補を返し、`_is_sanctioned` は
  frozenset 照合だけで判定する。
- **(P2)** `-m <他 module>` 借用の穴は本 wave の scope 外である。
  **実測:** `python3 -mpytest tools/pegasus/submit_certify.sh` は現状 rc=0 で**通る**。
  借用抑止 `_provenance_script_borrow` は `check_ai_provenance.py` の basename にしか効かず、
  sanctioned な pegasus path 一般には効いていない。したがって本 wave は既存の族欠陥へ
  5 件目を足すだけで、新しい欠陥類型を作らない。族修正は防壁の設計変更であり
  (`python3 -m py_compile tools/pegasus/...` の過剰拒否リスクを伴う)、裁定へ返す。
- **(P3)** 軽量版で足りる。`hooks/README.md` は本層 (Pegasus 重量処理層) を明示的に
  「正しさ防壁ではない」と分類しており、成果物の受理集合も動かない。ただし allowlist 拡大
  なので段 6 の敵対レビュー 2 本は残す。

## 成果物影響 (DW-G05)

実装しない場合: land 済みの `docs/pegasus-runbook.md` §7.0 / `tools/pegasus/README.md` §6 の
third-party 取得手順が、通常の起動綴りでは機械拒否されて実行できない。third-party source は
`silo_ladder_rung1` campaign の前段であり、取得が止まると同 campaign の試行が起票できず、
certified 選択の材料 (rung1 系の測定行) が台帳に増えない。値の書き換えではなく
「取得段が起動不能なので試行が発生しない」形で成果物へ効く。

## 成果物の形

- `hooks/guard_bash.py` の 1 行追加 (+ 理由 comment)
- `orchestrator/tests/test_hooks.py` の新規テスト
- 受入全走 + 変異 matrix + spool fragment (worklog / decisions) + insights 逐語

## 分割方針

実装単位は 1 つ (`hooks/guard_bash.py` + `orchestrator/tests/test_hooks.py`) で所有が閉じる。
並列分割しない。段 6 レビューは read-only 2 レンズ並列。

## 環境

受入・変異は本 worktree、cwd = repo root、pegasus02 (login node)。
計算ノード dispatch は不要 (`tools/run_tests.py` の受入形は login で走る sanctioned 経路)。
