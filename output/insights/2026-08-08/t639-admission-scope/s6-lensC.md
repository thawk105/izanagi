GO 不可です。以下は静的監査結果であり、テストは実行していません。

[所見 1] blocker / `hooks/guard_bash.py:258,586,958,1175,1203`・`orchestrator/tests/test_hooks.py:2011` / 非 Pegasus `local-ok` に対する lookup の「第三防壁」は独立していない。lookup は不正 entry を `None` に落とすだけなので、同じ path が `_SANCTIONED_PATHS` に入った整合的な破損状態では、admission loop を素通りして `_is_sanctioned()` が早期許可する。例えば registry と sanctioned の双方へ `pytest` の `local-ok` を注入すると、本来拒否される `pytest -q` が許可へ移る。現在のテストは registry だけを patch するためこの経路を検出しない / `_script_targets()` → admission `None` → `_is_sanctioned()` → generic pytest 判定前の return、という順序を静的追跡 / 非 Pegasus `local-ok` は `None` でなく deny sentinel にし、registry と sanctioned の双方を汚染した end-to-end 拒否テストを追加する。既存期待を sentinel へ変更するのは強化であり、緩和ではない。併せて `local_ok_paths` の union を Pegasus 配下だけに限定する。

[所見 2] blocker / `hooks/guard_bash.py:197-201,1636-1638`・`orchestrator/tests/test_hooks.py:2231,2573` / raw-mention 防壁が fallback 集合から独立した手書きで、現在も parser が正規化して認識する `tools//claude_session_ledger.py` や `tools/./claude_session_ledger.py` を内部例外時に見落とし、`main()` が rc=0 へ倒れる。さらに fallback path を増やして集合一致テストを直しても regex の追随漏れは赤にならない / `_invocation_path()` はこれらを ledger path に正規化する一方、regex は canonical slash と module の二綴りしか受理しない。新規テストも ledger をハードコードしている / raw detector を `_NON_PEGASUS_ADMISSION_FALLBACK_PATHS` から生成し、各 fallback path の slash・module・正規化綴りを列挙する generic subprocess テストで exact rc=2 を固定する。

[所見 3] blocker（既知の赤 1、発見数外） / `orchestrator/tests/test_hooks.py:1807-1810,2573-2593` / 1 回目の `_run_guard_subprocess()` が `orchestrator/campaign` を作り、同じ `tmp_path` での 2 回目が無条件 `mkdir()` に衝突して `FileExistsError` になる。module 綴りの rc=2 assertion へ到達しない / helper と loop の呼出し関係から確定 / slash・module ごとに `tmp_path` 配下の独立 root を作り、その各 root で fixture 作成・source 変異・subprocess 実行を行う。二つの exact rc=2 assertion は維持し、対象や期待値を減らさない。

[所見 4] blocker（既知の赤 2、発見数外） / `orchestrator/tests/test_check_docs.py:80-92,1080-1085` / `first_row` は projection 表と unknown 表の両方の先頭文字列なので count は 2。projection 追加前の準備 assertion 自体が落ちる / synthetic runbook の二表を逐語確認 / prefix ではなく class・evidence を含む projection の完全な一行を anchor にし、その完全行が 1 件であることを assert して置換する。count 緩和や assertion 削除は不可。

[所見 5] must-fix / `s4-ruling.md:129-142`・`s5-impl.md:55-68` / M1〜M10 の「指定 node だけ」という帰属と kill 意味論が成立していない / anchor と全テスト consumer を静的照合 / expected-node 集合を再登録し、構造 pin と受理集合 kill を分離する。

| 変異 | 静的判定 |
|---|---|
| M1 | block は一意だが、実 registry も loader failure へ倒れるため literal golden・既存 local-ok 系も赤経路を持つ。指定 node のみではない。 |
| M2 | 新規 node に加え既存 negative corpus の `[outside-path]` も同じ loader 条件を検出する。 |
| M3 | 新規 site matrix に加え既存 login/suspect bit pin と sanctioned 衝突テストも検出する。 |
| M4 | anchor は実在するが、直接 lookup テストは上流と sanctioned を片方だけ除いた非整合 fixture。受理集合 kill になっていない（所見 1）。 |
| M5 | fallback 集合テストは有効で恒真ではないが、registry-failure matrix の全 failure parameter でも ledger が許可へ移る。 |
| M6 | `return _PEGASUS_UNREGISTERED` は二箇所あるため、条件を含む二行 block を exact anchor にする必要がある。「matrix の ledger case」は具体的 nodeid でもない。 |
| M7 | subtraction を消しても admission 判定が sanctioned 早期許可より先に拒否するため、実受理集合は不変。新規テストは内部 set assertion だけで赤になる diagnostic pin。 |
| M8 | 条件 block は一意で、指定 node に実効的に到達する。 |
| M9 | 条件 block は一意で、正例が過剰拒否を検出する。 |
| M10 | clause は一意で mask はないが、基準 node が既知の赤 1 のため現状では kill を数えられない。 |

疑われた fallback 集合テストと実在テスト自体は、前者が独立集合比較、後者が非空 assertion と `stat` を持つため恒真ではない。ただし raw regex drift はどちらも検出しない。

成果物影響: 現状のままでは変異台帳の M4/M7 の `kill` と M1/M2/M3/M5/M6 の `expected_nodes` が虚偽になり、レポートが参照する機械防壁の検出力を certified と扱えない。

[所見 6] must-fix / `docs/pegasus-runbook.md:424-443,497-500`・`hooks/README.md:81-88`・`tools/README.md:31-34` / docs が実装より広い。runbook は一度「未登録はすべて拒否」と書いた直後に非 Pegasus 未登録は素通りと訂正しており、後段でも「hook は未登録の実行体を拒否」と再度一般化している。また「配置場所を問わず」は canonical repo-relative 制約より広く読める。hooks README の「一次強制は各 entry point 自身」も、site gate を持たない ledger には成立しない / loader の canonical 条件、`decide()` の site gate、ledger source を照合 / 「repo 内の exact 登録 path」「登録済み deny class と Pegasus 配下の未登録だけを拒否」と統一し、ledger は Claude Bash hook が唯一の現行機械面であること、三層が全 entry に揃うわけではないことを明記する。

成果物影響: runbook／hooks README を参照するレポートは、実受理集合より広い未登録閉包と存在しない entry-point 防壁を記録し、台帳の防壁参照が実装と不一致になる。

## 総括

- 最危険なのは、非 Pegasus `local-ok` の lookup 防壁が sanctioned と組み合わさると fail-open になる点。
- raw-mention は現在も正規化綴りを漏らし、将来の fallback 追加との drift も検出されない。
- 既知の赤 2 本と無効な M4/M7 帰属により、現状の変異・受入結果は認証根拠にできない。