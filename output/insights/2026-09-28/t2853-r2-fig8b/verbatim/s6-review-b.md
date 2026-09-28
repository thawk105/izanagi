## 所見

### F1 — must-fix：fig8b 形式の図が成果物にない

**根拠:** [README §5.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:203) は、同じ生成器が R2 の fig8b 描画を目盛文字の重なりで拒否したと記す。repo にある PNG は、各 group を別々に描いた fig8 形式の２枚だけである。段４裁定は描画拒否時に値と理由を残す方針を認めている。

**放置時の影響:** 「fig8b を同じ生成器で描いた」再現パッケージとして扱うと、実際には存在しない図を成果物に数える。

**推奨:** 測定・４群対照・fig8 形式の図は有効な到達点として残し、冒頭と結論で「fig8b 形式の図は未生成」と明示する。fig8b 図の完成を受入条件とするなら、この成果物は未達と判定する。検査を外した図への差し替えは勧めない。

### F2 — should-fix：図を再作成するための記録が repo 内で閉じていない

**根拠:** [README §5.2、§8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:216) は wrapper のハッシュと repo 外の所在を示すが、最終描画の実行 argv と PNG に対応する provenance 本体は repo にない。[wrapper](/work/1/SFC/tanab/tmp/t2853-r2-fig8b-20260928/wrapper/t2853_r2_fig8b_plot.py:120) は provenance の再現コマンドに生成器の直接実行形を渡しており、実際の wrapper 呼出しをそれだけでは復元できない。段４裁定も wrapper の実行 argv・入力ハッシュ・出力 provenance の記録を求めている。

**放置時の影響:** repo の PNG ２枚を第三者がどの入力と操作から作ったか、repo の記録だけでは追えなくなる。

**推奨:** 最終２回の wrapper argv と各 provenance を insight に残す。wrapper 本体は段４裁定どおり repo 外に置くなら、長期に参照できる保管先を示す。PNG ２枚は閲覧用として妥当で、削除する必要はない。

### F3 — should-fix：費用の合計に見積りが混在する

**根拠:** [README §6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:230) の測定 1.40 node 時間は６ job の Elapse 実測だが、受入全走 0.25 node 時間は「見込み」である。合計約 1.65 を実績のように読む余地がある。

**放置時の影響:** 第三者が２ node 時間の線を実測で満たしたと誤認する。

**推奨:** 「実測 1.40、受入全走は見積り 0.25、合計は見積り」と一文で分け、実績が取れた場合だけ更新する。

### F4 — nit：実行記録の周辺資料が本題を埋もれさせる

**根拠:** [README §0、§1、§7、§8.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig8b/output/insights/2026-09-28/t2853-r2-fig8b/README.md:9) は「合成しない」「主張しない」を繰り返し、未使用 checkout の precheck、負例テスト、逐語ログの空白復元表まで本文と repo に載せている。依頼の driver 名の誤記を訂正した §1.1 と、trace 保全口を使えなかった §1.3 は必要な説明である。

**放置時の影響:** 読者が測定条件、原値との対照、fig8b 描画失敗という主要結果を探しにくくなる。

**推奨:** 本文は条件・４群対照・図の成否・費用・主張の限界に縮める。`startup-gate.log`、未使用 checkout の precheck、相談・実装子の逐語ログや空白復元表は、残すとしても本文からの参照を最小限にする。wrapper の負例用分岐も今回の最終成果物には不要である。

## 総括

**NO-GO（fig8b 図を含む完成品として）。** 元の driver 名の誤記は適切に訂正され、２ group の測り直し、原値との４群対照、実測費用、主張の限界は概ね分かる。fig8b 形式の図は生成されていないため、段４裁定に沿った**描画拒否を伴う再測定記録**として位置付け、図の再作成記録と費用表記を補えば、その範囲では読める。