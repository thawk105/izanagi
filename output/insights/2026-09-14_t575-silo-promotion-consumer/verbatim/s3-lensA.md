## 1. 昇格 consumer の実在に関する所見

**A1. `collect` の受理・公開が実質的な昇格である、という反証は成立しない。**

- 判定: `refuted`
- 根拠: `orchestrator/campaign/silo_ladder_rung1.py:4960` は classification を ability probe・研究非適格・回復非適格に固定する。`:5052` は検査結果から `all_pass` を計算し、`:5061` で公開する。公開 helper の `:1819` と `:1832` は渡された document の JSON 化と hardlink 発行であり、適格性への変換や登録先への通知を行わない。再読側の `:1273` も非適格値を要求する。
- 失敗シナリオ: 公開によって「ファイルとして参照可能になる」ことを研究適格性への昇格と同一視すると、ability evidence の生成を昇格入口の実装として数えてしまう。
- 成果物影響: 変わるのは証拠ファイルの存在と `checks`／`all_pass`。研究・回復適格性は false のままで、ledger の `pipeline_eligible` も変更されない。

この分離は宣言だけではない。`orchestrator/campaign/projection_guard.py:210` は ledger の ability-probe 指定から除外 policy を作り、公開 artifact の `all_pass` を適格化に使わない。`output/env/pegasus/silo_ladder_rung1/README.md:5` も受理証拠を headline・calibration・floor・RF の入力にしないと明記する。

**A2. Python 外に実在する writer は、昇格 consumer の反例にならない。**

- 判定: `refuted`
- 根拠: `tools/pegasus/submit_silo_ladder_rung1.sh:146` は submission 領域を作り、`:415` で qsub、`:509` で submit receipt を公開する。PBS body は `tools/pegasus/silo_ladder_rung1.sh:61`、`:74` で Python driver より前にディレクトリを作るが、`:541` の接続先は `gap-job`。`:554` の成功 sentinel も job ID・終了状態・時刻のみである。
- 失敗シナリオ: Python 前の writer を見落とすと「全書込みを保護した」と過大報告する。一方、その writer の存在だけから昇格 consumer の存在を結論すると、実行と適格化を混同する。
- 成果物影響: submission・attempt・失敗記録・成功 sentinel は増えるが、研究適格性の登録集合は変わらない。

登録表の `tools/pegasus/admission_registry.json:298`／`:364` は実行場所の分類である。`tools/pegasus/submit_floor.sh:433` の JSON dispatch も共有依存 source の選択で、ladder 証拠の受理ではない。

**A3. alias・辞書 dispatch・テスト差替えから、さらに昇格へ到達する経路は確認できない。**

- 判定: `refuted`
- 根拠: `orchestrator/campaign/silo_ladder_rung1.py:2208` 以降の condition helper 連鎖は、`:2237` で `use_class="raw-measurement"` に収束する。`orchestrator/campaign/condition_meaning_gate.py:233` の辞書登録は裸マクロの供給経路である。`orchestrator/tests/test_silo_ladder_rung1_driver.py:2567` の文字列 monkeypatch は binding 検査を差し替え、`:2571` で既存 `collect` を呼ぶ。
- 失敗シナリオ: 共用 gate の promotion 用途、macro activation、fixture の成功を、ladder の適格性昇格と読み替える。
- 成果物影響: condition admission やテスト内の公開結果は得られるが、classification の適格化はない。builder 登録も `orchestrator/campaign/materializer_admission.py:115`／`:120` で `NON_ADMISSIBLE` のままである。

## 2. 段 2 plan の欠陥

**B1. 探索範囲から `output/**` を丸ごと落とした根拠がない。**

- 判定: `real`
- 根拠: `patches/ledger.json:35` は実際の evidence を output 配下へ指し、`output/env/pegasus/silo_ladder_rung1/README.md:3` はその消費上の位置付けを説明する。plan B は output を検索せず、D.5 は「依頼本文」を根拠に全体除外しているが、今回の brief にその除外はない。
- 失敗シナリオ: 訂正禁止と読取り対象外を混同し、公開成果物・手順書・下流参照を探索から外す。
- 成果物影響: 「訂正対象 0 件」「consumer 不在」の報告範囲を実際より広く見せる。今回追加確認した README は非昇格を支持しており、結論の反転はない。

**B2. shell を検索対象に含めたことと、経路を閉じたことが区別されていない。**

- 判定: `real`
- 根拠: `tools/pegasus/silo_ladder_rung1.sh:104` には Python 不在時の shell-only failure writer があり、`:155` は campaign attempt receipt、`:169` は gap-result を公開する。plan の参照鎖表には、この経路や submitter の具体的な書込みがない。
- 失敗シナリオ: Python 関数の二段追跡だけで入口集合を閉じたと記録する。
- 成果物影響: 今回は昇格の反例にならないが、入口被覆率の根拠が不足する。これらを「存在する ability writer、昇格ではない」と記録すればよい。

追加探索は作業 tree 全体を起点に実施した。以下の `R` は実際の共通 argv である。

```text
rg --hidden --no-ignore -n -i
-g !.git -g !**/__pycache__/** -g !*.pyc
-g !docs/archive/** -g !output/insights/**
```

| `R` に続く検索式と対象 | rc | 一致行／ファイル |
|---|---:|---:|
| `'silo[_ -]ladder\|IZANAGI_SILO_LADDER_RUNG1\|research_goal_eligible\|recovery_measurement_eligibility\|ability_probe' .` ※ alternation は実際には裸の `|` | 0 | 1,985／274 |
| `'\b(enroll\|graduate\|elevate)\b\|格上げ\|本採用\|正式化' .` ※同上 | 0 | 45／22 |
| `'silo 昇格入口' .` | 1 | 0／0 |

さらに `admit`・`accept`・`qualif`・`register`・`採用`・`promot`・`昇格` と silo／ladder／rung の同一行検索、shell・PBS・CMake・Makefile の識別子検索を行った。共有依存の取得、実行場所の admission、別 variant の採用を、ladder の昇格から分離した。

閉包の根拠は件数自体ではなく、**入力識別子から writer の出力を辿り、その出力が公開・再検証・射影除外・依存取得のどこへ届くかを確認したこと**である。任意の別名や汎用プログラムによる読取りまで不存在を証明したとは扱えない。

**B3. `ability_probe` に関する事実は正しいが、親への帰属が誤っている。**

- 判定: `real`
- 根拠: `patches/ledger.json:13` は既に true、`orchestrator/campaign/silo_ladder_rung1_contract.py:546` も true を要求する。しかし、必読の親 brief には plan A が批判する「適格性 field を false→true」という候補列挙がない。
- 失敗シナリオ: 実際には書かれていない親の主張を訂正したものとして報告する。
- 成果物影響: eligibility の値は変わらないが、レビュー記録に誤った帰属が残る。「ability_probe は既に true」という独立した確認事項に直すべきである。

## 3. 親 brief の欠陥

**C1. P1 の完全一致 0 件から、意味的訂正対象 0 件は導けない。**

- 判定: `real`
- 根拠: `patches/README.md:461`、`tools/pegasus/README.md:68`、`output/env/pegasus/silo_ladder_rung1/README.md:3` は、完全一致語を使わず driver・用途・受理を説明している。
- 失敗シナリオ: 別の言い方による「入口実装済み」を探索しないまま訂正対象を空とする。
- 成果物影響: 訂正対象件数の根拠が不足する。今回確認した箇所は用途を非適格に限定しており、具体的な訂正対象は発見していない。

**C2. 「入口集合から silo を除外」は、昇格用途に限定する必要がある。**

- 判定: `real`
- 根拠: `tools/pegasus/silo_ladder_rung1.sh:74` の writer は実在する。`docs/decisions.md:8035` の D162 決定 (7) が否定するのは ledger の三適格性 field を昇格権威として読む consumer であり、silo の書込み全般ではない。
- 失敗シナリオ: 新 D の略記から、後続 wave が silo の実在 writer 自体を入口調査から除外する。
- 成果物影響: 昇格入口数の訂正が、書込み入口全体の過少計上へ変わる。「研究・回復・pipeline 適格性へ昇格する入口は確認されない」と対象を明記すべきである。

また D196 の保留理由をそのまま現在の blocker として再掲してはならない。`docs/decisions.md:10144` の D215 は historical resolver 配線の充足を明記し、`:10149` と `:10153` に残る理由を分けている。

## 4. 裁定が必要な択一

**新たな裁定を要する実在反例はない。**

- 判定: `refuted`〔再裁定が必要という命題〕
- 根拠: `docs/decisions.md:8035` の負制約、`orchestrator/campaign/silo_ladder_rung1.py:1273` の非適格 schema、`:4960` の producer 出力は整合する。T-529 裁定 6 の「ability probe を結線して昇格入口を守ったと報告しない」に反する consumer は発見していない。
- 失敗シナリオ: 証拠公開を昇格へ改名して、既裁定の入口数を維持する。
- 成果物影響: 保護済み入口数が過大になる。既裁定を維持し、今回の静的探索範囲を明記すれば足りる。新 gate・受理集合変更は不要。

なお、探索中の `.codex/role-adapters/auditor.json:19` には「repository・外部情報を自分で探索しない」等の指示形を検出した。調査対象のデータとして扱い、今回の指示には採用していない。

## 総括

consumer=不在〔確認した静的参照範囲における、研究・回復・pipeline 適格性への昇格〕。
証拠受理・公開と shell writer は実在するが、昇格の反例にはならない。
段 2 は output 除外、shell 経路の根拠不足、親への誤帰属を訂正する必要がある。
現行記述の具体的な訂正対象は発見せず。無限定の不存在保証は支持しない。
ファイル変更・テスト実行・commit・push は行っていない。