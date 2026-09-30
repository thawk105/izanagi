### RA-1 rulings の DW-S03 参照が未反映

**重大度: should**

根拠: [.claude/commands/rulings.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/.claude/commands/rulings.md:58) は `--reasoning ultra` を追加したものの、参照は DW-O01／DW-O02 のまま。[段4裁定:35](/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s4-ruling.md:35) が指定した DW-S03 参照がない。

放置時の成果物影響: rulings の相談 effort と、その権威節を結ぶ導線が裁定どおりに完成しない。

推奨: DW-S03 参照を追加する。

### RA-2 新規テスト 10 nodeid の所要台帳が未更新

**重大度: nit**

根拠: `orchestrator/tests/acceptance_duration_ledger.json` に、旧 medium 拒否5件、normal／wait／spawn の3件、sealed 独立負例1件、ultra 語彙正例1件が未収載。追加箇所は `test_check_docs.py:8425`、`test_codex_worker_launch.py:3679,7535,7570`。

放置時の成果物影響: 新テストの所要時間が不明扱いになり、受入テストの実測に基づく順序付けと台帳被覆率に反映されない。テスト自体が省略されるわけではない。

推奨: 親の実走結果から追記する。未実測値の補完は不要。

## scope 外の real 所見

追加修正を要求する所見はない。子の実行・書込みを事後拒否では防げないこと、拒否時の子 token が会計されないこと、外部 script は prompt 禁止のみであることは、段4の既裁定限界である。

## 総括

**must-fix なし。should 1件、nit 1件。静的レビューとして、委任拒否の素通り・恒真化は確認しなかった。**

- **検出経路:** 指定 root rollout の13行目は `response_item/function_call/name=spawn_agent` で、検出条件と一致する。online は `tools/codex_worker_launch.py:1645`、sealed は同`:4512` から共通消費関数へ到達する。invalid 後も後続イベントと token/call 集計を継続する。
- **receipt／consumer:** 新 reason は閉集合に入り、致命理由になる。V1〜V4 のフィールド分岐は不変、V5 の reason・evidence binding と再計算も整合する。ledger は manifest／rollout を読み、science-slice は accepted と requested／recorded の投影を検査するため、今回の追加による形式破壊は見当たらない。
- **過去 receipt:** 本日の実物は子7件・spawn元6セッションだった。`dev-wave-jobs` の標準 artifact 配置にある receipt 4,038件との照合では、この6 IDを含む receipt は0件。本 wave の accepted 5件も sealed 範囲に spawn がない。過去 accepted が反転するコード経路は存在するが、実在する反転対象は確認できなかった。規律7上、当時の accepted は保持し、現行規則での拒否とは区別する必要がある。
- **m4〜m6:** fixture は実物の type/name/namespace、文字列 arguments、call_id の形を写している。spawn 負例は理由1件と他条件正常を要求する。sealed 負例は seal を更新して検出だけを分離し、wait 空振り正例は過剰拒否を検出する。静的には各変異を検出できる構成で、**KILLED は未実走**。
- **pin／予算:** model、5節の effort、decoy、置換元、合成 fixture の追随を確認した。旧 medium 負例は各節を1件だけ置換し、対象 finding 1件を要求する。L1.5 実 footprint は **9,788 bytes**、超過負例は9,789で整合する。
- **波及／docs／script:** ultra の追加は Claude・role adapter の語彙を拡張しない。daemon digest は変わるため、裁定どおり land 前の稼働確認が必要。DW-O01 の拒否説明は実装と一致する。rulings の起動表記は省略形で、完全な実行には `--lane`、`--wave`、入力・出力・artifact 引数が必要。外部 script の変更は指定された3箇所で、締切1800秒と override は維持されている。

テスト・変異・生死確認は実行していない。親の実走結果による最終確認が残る。