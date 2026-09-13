## 総括

P1 の無限定な「login dedicated-scope 経路は存在しない」は **refuted**。対象 model 本走用に限定すると、調査した認可済み経路には**無い**。
凍結入力不在も **refuted**。発見済み 2 本を再読し、各 269,108 bytes・完全 SHA-256 一致を確認した。
最大の穴は、テスト scope の観測を対象 model 本走の footprint・分類へ一般化することである。

## 所見

以下、repo 相対参照は HEAD `75bea8e5fe918e7ec9fd18c10cd0dadcf474c51a`。逐語資料・プランは指定された親 job 配下を指す。

1. **主張：AI が使える login scope は存在しない。**
   - **根拠：** `hooks/guard_bash.py:199` は tests/provenance を sanctioned path とする。`tools/run_tests.py:2496` の条件分岐から `:2545` で local scope を起動し、`:1895` が専用 unit・MemoryMax を構築する。provenance も `tools/check_ai_provenance.py:3066` → `:2731` に同型経路がある。逐語 `d210.md:15` も両経路を明示する。
   - **判定：refuted。** 親自身のテスト scope 実測とも矛盾する。
   - **成果物への影響：** 「経路不足」の対象を model の凍結入力・本走 argv に限定する必要がある。
   - **推奨：** 段 2 の `stage2-plan.md:27` の限定した結論を採る。

2. **主張：その既存 scope に model 本走を渡せる反例がある。**
   - **根拠：** `tools/run_tests.py:1897` の `script_path` は内部 seam だが、実呼出し `:2015` は指定せず自己再 exec。CLI は `:2397` → `:2682` の pytest 経路。provenance は `:2737` で自己固定、`:2976` の CLI に任意実行引数は無い。mutation は `tools/mutation_fanout.py:1824` の `run` に command 引数を持つが、`:1867` の receipt cap、`:1555` の実行条件束縛、`:407` の生存 cgroup `memory.peak` 検証を要する。
   - **判定：refuted。** 対象の未測定本走を開始できる認可済み login dedicated-scope 経路は、調査した現行面には**無い**。
   - **成果物への影響：** 内部 seam や mutation の command 引数を「利用可能な測定入口」と記載できない。
   - **推奨：** CLI と認可条件の不一致を不足理由として残す。静的検索を全実行面の不在証明にはしない。

3. **主張：raw 拒否 1 件が経路不在を証明する／compute generic が反例になる。**
   - **根拠：** hook は `hooks/guard_bash.py:2730` の site 条件下で、`:1188` の解析結果が `head == "systemd-run"` の場合に拒否する。ただし `:1192` は非実行の command-reader 例外。admission の射程は `:614` と `:1205` の exact 登録・Pegasus subtree。compute CLI は `tools/pegasus/dispatch_compute.py:4482`、generic の argv 実行は `:1623` にあるが、`:851`・`:1582` が compute 判定を行う。`:1058` の隔離は user/mount namespace。
   - **判定：両推論とも refuted。** 拒否はその呼出しの証拠であり、generic は login scope の反例ではない。
   - **成果物への影響：** 「無条件拒否」「namespace 隔離＝専用 memory cgroup」という記述は不成立。
   - **推奨：** 親の拒否ログは exact な実行面・argv の発火証拠として引用する。compute 側の専用 cgroup は実在を確認したとは書かない。

4. **主張：serial 3 回の最大値 161,529,856 bytes が対象 model の footprint の bound になる。**
   - **根拠：** `orchestrator/tests/test_t2216_backoff_walk_model.py:97` は合成入力、`:502` は pin 差替え、`:529` は `predict_all` の fake 化。`tools/run_tests.py:2014` の起動後に `:2027` で sampler を開始し、`:1958` で 5 ms sleep。親の `samples.ready.wait` は起動後であり、対象開始前の barrier ではない。逐語 `runbook-7.0.md:53`・`:90` は先行 sampler と実行ごとの射程を要求する。
   - **判定：refuted。**
   - **成果物への影響：** serial 値も xdist 32 worker 値も、それぞれのテスト scope の観測値にとどまる。
   - **推奨：** 本走と同じ処理・入力・argv・環境・cap、全子孫と全実行期間の観測が成立しない限り転用しない。sampling 最大値は数学的上界ではなく、規範上の分類にも所定 margin が別途必要。3 回という回数だけでは成立しない。

5. **主張：cap が違う 3 回を同条件の反復として扱える／提示値が実効 `memory.max` である。**
   - **根拠：** 逐語 `runbook-7.0.md:94` は cap 変更時の再測定を要求する。`tools/run_tests.py:1754` が表示するのは付与予算。`:1818` は kernel 値を読み、`:1832` はページ切下げ値も受理する。提示値 3,940,686,240 は 4,096 の倍数ではなく、同ページ幅なら切下げ値は 3,940,683,776。
   - **判定：同条件扱いは refuted。実効値との同一視は根拠不足という real な穴。**
   - **成果物への影響：** 最大値は「異なる cap を含む観測集合の最大」であり、固定条件 3 反復の結果とは書けない。
   - **推奨：** 各回の予算・実効値・rc・cap 到達・fallback を分けて記録する。低い cap が reclaim や完走性に影響しないとは仮定しない。実効値の逐語回収が無ければ未取得とする。

6. **主張：凍結入力不在により本走 argv が再現不能。**
   - **根拠：** 親 `brief.md:37` 以降の走査主張に対し、`output/insights/2026-09-07/t2313-13pt-audit/README.md:35` と外部出力 `t2216_model_tail.json:225` が参照鎖を与える。指定された外部 `measured.json` 2 本を本段でも読取り、`tools/t2216_backoff_walk_model.py:38` の完全 pin 一致を再確認した。
   - **判定：refuted。段 2 と親の訂正は real。**
   - **成果物への影響：** 「凍結 bytes 不在」を独立障害として残せない。
   - **推奨：** 旧走査は指定範囲の一致 0 件として保存する。別 repo・拡張子・`.git` 除外は網の外を残す。20 MB 上限は任意の JSON 不在証明には不足するが、今回の既知 269,108-byte ファイルを漏らした原因ではない。入力発見は実行環境までの再現成功を意味しない。

7. **主張：段 2 は docs-only と言いながら実装変更を計画している／参照が架空である。**
   - **根拠：** `stage2-plan.md:95` の所有成果物は insight と spool fragments、`:106` は成立条件の仕様化、`:114` は内部関数転用を明示的に除外する。主要 file:line は現物と一致した。細かな位置差は provenance の `--force-dispatch` が `:2976` ではなく `:2978`、runner の引数処理が `:2395` ではなく `:2397`。
   - **判定：実装混入・架空参照という攻撃は refuted。**
   - **成果物への影響：** 小さな参照位置補正以外に、実装変更の帰属を主張する根拠は無い。
   - **推奨：** 既存コードの条件差は既存実装への所見として扱い、本 wave が導入した変異・回帰とは呼ばない。`docs/spool/worklog/README.md:64` に従い、残る本走分類は「更新」にする。

8. **主張：不足経路の仕様を書けば、経路の実装・受入まで完了する。**
   - **根拠：** 逐語 `d180.md:28` は即時新設を却下、`d210.md:15` は既存 entry point 内に限定。`hooks/README.md:332` は通常 wave の hook 編集制約を記す。`tools/check_docs.py:4610` は既存投影表等の照合であり、仕様の実行可能性を検証しない。
   - **判定：refuted。所有範囲と実効層の隔たりは real。**
   - **成果物への影響：** 今回完了できるのは不足の特定・仕様・証拠記録である。
   - **推奨／裁定パッケージ候補：**

     | 層 | 本 wave の scope 外 |
     |---|---|
     | hook | 拒否条件・受理集合・配線の変更 |
     | admission registry | 族再設計、class 昇格、許可根拠の変更 |
     | runbook 投影表 | 実装済み・分類済みとしての状態変更 |
     | `check_docs.py` | checker 自体の変更、新仕様の機械検証の追加 |
     | 受入 | 新経路の実動確認、本走の正式分類完了 |

     D180 の即時新設却下と対象限定経路の関係、D210 の entry point 境界、上記各層の未変更範囲を裁定資料へ載せる。既存 docs 検査の成功を、新経路の受入成功に読み替えない。

## 棄却した攻撃

- 別綴り、子 agent、subprocess、内部 seam 転用、systemctl／D-Bus、直接 cgroup 作成、hook 未解析面は認可経路の反例に数えなかった。
- 共有 cgroup 差分・per-process RSS・過去測定 script は正式分類の代替にしなかった。
- `--help` 通過や dispatcher の `legacy-admitted` を本走認可・実測済みの証拠にしなかった。
- pin 変更、unknown の軽量側への変更、新 gate・台帳・一般化、即時実装は提案しない。

## 読めなかった資料

なし。必読資料は全文読取済み。静的検査と入力 hash 照合のみ実施し、編集・pytest・model 本走・親のメモリ実測の再実行は行っていない。