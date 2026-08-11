# 段 1 brief — dev-wave [T-717]/[T-485]/[T-792]

## scope (worklog 440 の裁定、実施 3 件)

- **[T-717]** `tools/pegasus/dispatch_compute.py:28` の `DEFAULT_WALLTIME` を `"00:40:00"` →
  `"01:00:00"`。呼び出し側経路は作らない (D244 と同じ方針)。
- **[T-485]** evidence bytes の解決は **content-addressed resolver** (取得後に digest を再計算して
  照合) とする、を設計正本へ記録する。受領証 (authority-backed receipt) 方式は不採用。
- **[T-792]** `orchestrator/tests/test_real_repo_serialization.py` の 2 node を
  `from tests import ...` → `from orchestrator.tests import ...` へ ((b))。

## scope 外 (除外 1 件)

- **[T-800]** = 除外。裁定文が「fold transaction wave へ同梱」と routing し、その wave
  (`worktree-dev-wave-t798-t799-finalize`) が稼働中で `_rollback_fold` の当該ブロックを
  書換え済み (`git diff main...` で実測)。別 branch で同一行を触れば land で衝突する。
  ユーザー指定の除外 3 wave には含まれないが「射程が重なる項は除外」に該当する。

## 段 1 前提実測 (裁定の前提を実で確認)

1. **[T-717]**: `grep -n walltime tools/run_tests.py` = **hit 0**。呼び出し側から上げる経路は
   実在しない → 定数変更が唯一の手段。裁定文の前提は成立。
2. **[T-792]**: 当該ファイル単独の焦点走 (`run_tests.py <file> -q --force-dispatch`、
   request `904675.nqsv`、Elapse 28S) = **2 failed / 2 selected、いずれも
   `ModuleNotFoundError: No module named 'tests'`** (`:826` と `:909`)。逐語は
   `s1-premise-t792-before.log`。`orchestrator/` を載せているのは
   `test_reflux_ir.py:120` の `sys.path.insert(0, str(_ORCH))` 副作用のみ。
3. **[T-792] 修正形の実在**: `from orchestrator.tests import ...` は既存 5 ファイルで使用中
   (`test_ruleops.py:24` 他)。名前空間 package (両 dir に `__init__.py` 無し) で成立しており、
   同ファイルは既に `sys.path` へ repo root (`ORCHESTRATOR.parent`) を載せている (`:31`)。

## DW-O09 pin 閉包 (実測)

`DEFAULT_WALLTIME` / `00:40:00` の全出現 = production 4 箇所 + test 2 箇所。test は
`test_pegasus_dispatch_compute.py:255` (qsub 伝播の期待値) と `:2467` (下限 pin) の**両方が
定数導出**であり literal pin は無い (D244 が literal から定数導出へ移済み)。docs の hit は
D244 本文・failures・archive worklog の**歴史記録**のみで live pin ではない。

## 不変条件

- 正しさゲート・verifier・受理集合を一切緩めない。T-792 は偽赤の除去であって受理集合の拡大ではない。
- T-717 は確保上限の引き上げであり、消費短縮ではない (D244 が D105 と整合させた論法をそのまま継ぐ)。
  D258 の却下案「`DEFAULT_WALLTIME` の単独引き上げ」は**受入 wall の短縮手段としての却下**であり、
  切断回避目的の本裁定と矛盾しない。この整合を decisions 本文に書く。
- `docs/phase3-8c-wiring-design.md` は「設計であって実装ではない」。T-485 でコードは書かない。

## 成果物影響 (DW-G05、1 行ずつ)

- T-717 未実施 = 履歴成長で receipt 解決が伸びた際に受入全走が walltime 切れで全損し、
  その wave の受入結果が台帳に載らない (worklog の受入欄が未実施のまま残る)。
- T-485 未実施 = 8c formal consumer の evidence 取得方式が未確定のまま実装 wave が起票され、
  proof chain の「物理実行を主張できる」根拠が resolver 不在で成立しない。
- T-792 未実施 = 焦点走・二分探索のたびに偽赤 2 件が出続け、失敗診断が誤った原因へ誘導される。

## 親 provisional (攻撃対象)

- **(P1)** T-485 の記録先 = `docs/decisions.md` の新 D (spool fragment) を正本とし、
  `docs/phase3-8c-wiring-design.md` §3 系へ resolver 契約の小節を 1 つ足す。
- **(P2)** T-717 は定数 1 行の変更で足り、新規テストは不要 (既存 `:255` `:2467` が定数導出で
  自動追随する)。ただし「60 分」という値そのものを pin するテストは足さない
  (再訪条件 R-c で戻す裁定なので、値の pin は将来の戻しを阻害する)。

## 軽量版判定 (DW-C00)

設計択一は 3 件ともユーザー裁定で確定済み (割れない)、正しさ防壁に触れない、受理集合を変えない。
→ **軽量版**。段 2・3 と段 6 の review 子を省く。実装面 2 件があるため段 5 の Codex 実装子は必須。
実測 (前提・変異・受入) は省かない。

## 並列分割

- 実装子 1 (Codex author): T-717 定数 + T-792 import の 2 ファイル。互いに独立、衝突なし。
- 親 (docs-only): T-485 の decisions fragment + 8c 設計文書の小節、worklog fragment。
