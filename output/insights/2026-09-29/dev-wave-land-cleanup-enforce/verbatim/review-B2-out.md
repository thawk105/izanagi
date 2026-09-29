## 総括

**must-fix 0 件、GO。** tool 差分は 94 行（上限 250）、Stop hook は 91 行（上限 120）、追加テストは各ファイル 118 行・100 行以下（上限 300）。上限超過はありません。静的レビューのみで、テストは実行していません。

## 所見

- **should** — [docs/dev-wave/operations.md:221](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/docs/dev-wave/operations.md:221): DW-O28 は子 branch を `-D` で消すと書く一方、実装は期待 OID 付き `update-ref -d` です。文言とその pin を直す。**影響:** 復旧手順が、実際の競合防止策と食い違います。
- **should** — [orchestrator/tests/test_hooks.py:5315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/orchestrator/tests/test_hooks.py:5315): 8 件の Stop test がそれぞれ Git repo を作り、特に `stop_hook_active` の判定は repo 不要です。該当例を軽い入力で検査する。**影響:** 受理集合は変わらず、全体 5 分枠の余裕が増えます。既報の cleanup 208 件は 7.5 秒なので、現時点で超過の根拠はありません。
- **nit** — [tools/dev_wave_cleanup.py:1925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/tools/dev_wave_cleanup.py:1925): 退避経路でも `ancestry` を計算しますが、その経路では値を使いません。通常経路内へ移せます。**影響:** 成果物への影響はなく、不要な Git 判定を削れます。
- **nit** — [hooks/README.md:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-cleanup-enforce/hooks/README.md:330): hook の置き場と防壁ではない理由が冒頭の 8–10 行目と重複し、「何も拒否しない」は Stop を `block` する動作とも紛らわしい。冒頭へ集約し、ここでは「書込みを防護しない」と明記する。**影響:** 運用説明の誤読を減らせます。

実測残骸への対応は、**manifest 登録済みで wave が land 済みの子 rc=20**、**main 前進による rc=30**、**wave 木内で終了する cleanup 未呼出し**に届きます。wave 本体の reflog 起因 rc=20、manifest 外の補助木、symlink path の rc=2、停止・合図待ち、main に戻ってからの終了、admin 再検査など main 前進以外の rc=30 は止まりません。これらは今回の裁定範囲外として**後送**です。DW-S05-A の「同木・同 branch」と補助木登録は、今後の増加を抑える指示として妥当です。