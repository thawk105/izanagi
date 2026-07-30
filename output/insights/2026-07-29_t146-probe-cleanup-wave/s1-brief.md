# T-146 段 1 brief

- scope: `orchestrator/tests/test_dev_waves_integration.py` の AF_UNIX capability probe と、その局所テストだけを扱う。
- 確定入力: ユーザーは `$dev-wave T-146` を指定した。起票元は 2026-07-27 (26) のレビュー B-3 nit。
- 現 HEAD の前提実測: 既存 probe 正負テストと long-path roundtrip は 2/2 pass。
- 現 HEAD の前提実測: `os.unlink()` の `PermissionError` は元の判定を上書きし、`.s` を残して送出された。
- 現 HEAD の前提実測: 実 bind 後に wrapper が `OSError` を投げると、probe は `False` かつ `.s` 残留になった。
- 模擬差分: 上記 2 件は fault injection であり、通常の実 socket 正常経路での再現ではない。
- 既存被覆: socket 作成 / bind / listen の拒否と permissive mock の True、正常 cleanup の空 directory は固定済み。
- 純増する検出力: cleanup unlink 異常と bind 完了後例外を独立に再現し、判定と pathname 所有権を固定する。
- 不変条件: probe は本番 helper を呼ばず、同じ basename と syscall 列を保ち、T-138 の恒真 gate を戻さない。
- 不変条件: helper が作っていない既存 `.s` を削除せず、socket / dirfd を全経路で閉じる。
- 不変条件: production `tools/dev_waves/`、certified 選択、レポート、試行台帳、freeze / proof chain の bytes は変えない。
- 成果物: 局所 helper の例外安全な cleanup と、fault-injection positive control、変異台帳、受入記録。
- 成果物影響: 放置すると fault-injection 断面で long-path node が failed または SKIP となり、
  受入集合が過剰縮小または過剰拡大する。通常の product artifact 値・参照は変わらない。
- `(P1)` 親の provisional 裁定・攻撃対象: fix は probe の局所所有権を実在 pathname から判定し、
  bind 後例外を回収するが、事前存在した pathname は削除しない。
- `(P2)` 親の provisional 裁定・攻撃対象: cleanup 自体の失敗と capability 不足を同じ `False` に潰さず、
  fault-injection test が期待する判定を明示する。具体的 failure policy は段 3 の攻撃後に確定する。
- 分割: read-only plan 1、敵対相談 2 レンズ、workspace-write author 1、実装後 review 2 レンズ。
- 受入環境: 本 worktree のログインノードで局所 test、関連 test file、`tools/run_tests.py` 全走を行う。
  性能値は採取せず、wall time は比較に使わない。
