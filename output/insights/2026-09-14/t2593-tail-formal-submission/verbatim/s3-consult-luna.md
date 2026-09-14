## 行番号と CLI：訂正は正しく、提示 argv は受理される

- **所見：** plan の既存ファイルへの行番号参照に不一致は見つからず、提示された `run`・`report` の argv は argparse の定義と一致する。
- **根拠（静的読解）：** `submit_b10_backoff_grid.sh:13–34,184–188`、`b10_backoff_grid.sh:624–665` は訂正どおり。テストの回数 assertion は `test_backoff_extended_sweep.py:1705,1842`。driver の `:779–792` では global option が subcommand より前、`report` は campaign 3 本を要求する。`--ccbench-dir` は省略可能だが、省略時は `backoff_extended_sweep.py:160–163` の共有 checkout へ戻るため、job では提示どおり指定すべきである。
- **成果物影響：** 提示 argv 自体による受理集合の誤りはない。ただし argparse の受理は、その後の実行成功を意味しない。
- **深刻度：** nit（修正不要の照合結果）。

## 実行環境：固定 PATH に明白な欠落はないが、checkout の成立条件が確認計画から抜けている

- **所見：** 新 driver の起動に必要な Git 履歴と作業ツリーの条件を確認せず、argv の一致だけで配線完了としてはならない。
- **根拠（静的読解）：** driver の直接 import は標準ライブラリと repo 内 module（`:8–41`）で、`-I` に対する repo パス追加も `:26–28` にある。job は `:206–225` で Python 3.10、`git`、`qstat` 等を固定 PATH 上で検査する。`load_preregistration():232–242` はローカルの `git rev-parse`、`merge-base --is-ancestor`、`git show <commit>:<document>` を使い、作業ツリーの bytes と比較する。fetch はしない。したがって指定 commit の object、HEAD までの必要な履歴、同一 bytes の文書が計算ノードから見える必要がある。
  
  また、submit の repo は script 所在地から決まる（`submit_b10_backoff_grid.sh:53–55`）一方、job は `PBS_O_WORKDIR` を使う（`b10_backoff_grid.sh:239`）。qsub 呼出し `:190–192` は作業ディレクトリを指定していない。投入手順には対象 repo root からの実行が必要である。**実環境での欠落は実測しておらず、起動不能とは断定しない。**
- **成果物影響：** 条件不成立なら argparse 通過後に停止し、formal campaign と判定材料が生成されない。
- **深刻度：** must-fix（既存 loader を通す確認と投入手順の補完。新 gate の追加は不要）。

## qsub 伝播：新値の検査は妥当だが、既存 OUTPUT_PARENT の穴は残る

- **所見：** 新2値の文字集合検査は指定された危険文字を排除するが、それを `-v` 全体の安全性へ一般化することはできない。
- **根拠（静的読解）：** `plan.md:34–40` の commit 正規表現と explore の正規化前後の正規表現は、コンマ・等号・空白・改行をすべて拒否する。既存 `submit_b10_backoff_grid.sh:47–51` は正規化前だけを検査するため、安全な親 symlink を経由してコンマ入り実パスへ解決され得る。その値は `:181–191` で `QSUB_ENV` に入る。shell の引用は1引数への保持であり、qsub 内部のコンマ分割を防がない。等号・空白・改行についても shell 引用だけを転送保証にはできないが、新値では検査で到達を防げる。
- **成果物影響：** 新2値による分割は防げる一方、既存 output path 由来の環境値破損は残る。
- **深刻度：** scope 外（既存 OUTPUT_PARENT の修正）。plan の強度差の説明自体は正しい。

## job テスト：断片間の接続を壊しても緑になり得る

- **所見：** plan の job テストは各断片の性質を検査するが、入力検査から driver 起動・完了処理までの到達性を保証しない。
- **根拠（静的読解）：** `plan.md:118–125` は、command 部分を timeout stub、入力検査を別断片、finalizer を fixture で個別実行する。例えば入力検査を scratch 作成後へ移動したり、抽出対象の外側に新系列を拒否する条件を残したりしても、各断片だけなら期待結果を返せる。submit の qsub stub と job の timeout stub の間にも、実際の伝播値を受け渡す検査が指定されていない。
  
  抽出自体は可能。ただし command は `b10_backoff_grid.sh:579–609` の改行継続を保持し、finalizer は Python 本文だけでなく `:618–620` の argv・引用付き heredoc 開始から `:683` の終端まで含める必要がある。既存 `_shell_function()`（`test_backoff_extended_sweep.py:88–91`）は関数用で、このトップレベル heredoc には流用できない。
- **成果物影響：** テストが緑でも、新系列が job 内で拒否される、別値で起動する、完了処理へ到達しない配線を見逃す。
- **深刻度：** must-fix。親の検証では、観測した `-v` を job 側へ渡し、初期検査の位置と driver argv、失敗時の終了伝播まで接続する。測定・scheduler 境界の stub 化は維持してよい。

## submit 負例：qsub 未呼出しだけでは「副作用より前」を証明しない

- **所見：** plan が約束する早期拒否に対して、負例テストの観測点が不足している。
- **根拠（静的読解）：** `plan.md:37` は queue 照会・receipt 作成・qsub より前の拒否を要求するが、`:113` は rc=2 と qsub 未呼出しだけを要求する。検査を `submit_b10_backoff_grid.sh:177–178` の manifest 作成後へ移しても、この期待値は満たせる。また既存の位置検査 `:65–68` は文字列付き `SystemExit` なので rc=1となる。新 explore 検査へそのまま複製すると plan の rc=2 契約とは一致しない。
- **成果物影響：** 拒否された入力でも submit receipt が残り、投入集団の参照に不要な記録が加わる。
- **深刻度：** must-fix。queue stub の未呼出しと receipt 不在を追加観測し、新検査だけ終了コードを整える。

## 集団入口：registry 同期を理由に文書だけへ縮退するのは不十分

- **所見：** registry の集合一致という読解は正しいが、それは要求された集団入口を省く理由にはならない。
- **根拠（静的読解）：** `test_hooks.py:4407–4415` は実行 bit に関係なく `.sh` を inventory に含める。したがって独立 script 新設には既存 registry の同期が必要である。しかし `brief.md:55–56` が禁じるのは仮想リスク向けの新しい gate・台帳・一般化であり、依頼された実入口に伴う既存 inventory の同期まで scope 外とは読めない。
  
  `plan.md:86–97` の文書は既存 report CLI の操作説明であり、`brief.md:45,60–64,76` が予定する投入側の実行入口を実装していない。最小形は、commit・explore・3 campaign・出力先を受け、既存 driver の `report` へ `exec` して終了コードを保持する薄い独立 script と、既存 registry の対応 entry である。新しい集団台帳や判定器は不要。ただし registry 同期だけで login 実行可と分類してはならない（`test_hooks.py:4393–4395`）。
- **成果物影響：** 文書だけでは集団入口の実装と終了コード伝播が検証対象にならず、手作業の呼出しが残る。
- **深刻度：** must-fix。

## 集団入口テスト：既存 main の検査だけでは新入口の欠落を検出しない

- **所見：** 文書の「argv 骨格」をテスト内で再構成すると、入口を削除・破損しても既存 driver のテストだけが緑になり得る。
- **根拠（静的読解）：** `plan.md:116–117` は既存 `main()` と制御した loader を使うため、`b10_backoff_static_tail_formal.py:789–803` の3引数制約・report 呼出し・invalid 時 rc=1は検査できる。一方、新しい shell 入口や文書の実内容を必ず通す方式は明記されていない。これは新配線の存在を検査する代わりにはならない。
- **成果物影響：** 集団入口が report を呼ばない、引数を落とす、invalid を成功扱いする変更を見逃し得る。
- **深刻度：** must-fix。新入口を実際に起動し、転送 argv と終了コードを観測する。

## 総括

重い所見は、①集団入口を文書だけへ縮退していること、②job の断片テストが接続・到達性を証明しないこと、③固定実行環境から実 loader と Git 履歴を通す確認が欠けていること。

親は、本走を投入せず、実入口の argv・終了コード、早期拒否時の queue 未照会・receipt 不在、job 相当環境での Python import と事前登録 bytes 解決を実測すべきである。計算ノード固有条件を再現できない部分は未確認として残す。

本段は静的読解のみ。ファイル変更・テスト・投入は実施していない。必読対象は読めた。追加検索した `hooks/pegasus*` と `hooks/*json` は該当なしだったが、registry の根拠は実在する loader と `tools/pegasus/admission_registry.json` で確認した。