---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1629-ratification-broker
seq: 1
title: [T-1629] 取り残された D905 執行機構を独立監査して回収し、署名 receipt による批准 gate として着地させた (コード + テスト + docs、branch worktree-dev-wave-t1629-ratification-broker、変異 matrix = baseline PASSED・18/18 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- 依頼は「未 commit のまま 3 本の codex worktree に取り残された D905 実装を、
  独立監査したうえで回収し 1 本の wave として着地させる」。
  取り残しは `t1629-u1` / `t1629-u2` / `t1629-u4` の untracked 7 file で、
  いずれも detached HEAD `9463bcbc`、locked、担当セッション不在だった。
  **worktree を畳めば消える状態**だったので、着手直後に repo 外へ sha256 付きで退避した。

- **監査の結論は「機構の骨は使えるが、そのままでは着地できない」だった。** real と裁定した欠陥は
  段 2〜3 で 19 件、段 6 のレビューで更に 18 件。**refuted は 0 件**である。重いものは次の 5 つ。
  - **配線が丸ごと欠けていた。** broker は閉包 27 path を前提にしていたが main は 25 path で、
    差を埋める単位が存在しなかった。回収物だけでは 1 行も発火しない死んだコードである。
  - **回収物の土台が古い。** T-1742 の履歴検査 DAG 修正 (`9885a156` / `9c1d49ef`) は
    `9463bcbc` の祖先ではない。回収した検証子は旧・線形版を持ち戻していた。
  - **broker が AI に `hooks/` への正規の書込経路を与えていた。** 親が `hooks/guard_bash.py` の
    `decide()` を副作用なしに静的評価した結果、次が全部 ALLOW だった:
    自前 Ed25519 鍵の生成 / broker の起動 / 承認プロンプトへの `y` の流し込み /
    信頼根の `git add`。**broker は ssh 越しに書くため hooks の書込拒否も通り抜ける。**
    信頼根が不在なら AI 自身の鍵が信頼根になる。D906 が名指しした恒真化そのものだった。
  - **署名が実質飾りだった。** `source_commit` は存在確認しかしておらず、
    その commit の closure が署名 digest と一致するかを見ていなかった。
  - **検証の計算量が二次だった。** 履歴の各版で全行を再検証するため、
    台帳 10 行 × 792 呼び出しで約 4.3 分、100 行で数時間という見積りが出た。

- **段 3 の 2 レンズが、別のレンズから独立に同じ構造的限界へ到達した。**
  判定器とその呼び出し元は判定対象の閉包の内側にあり、呼び出し前に
  「今動いている判定器の bytes が以前に批准された bytes と同じか」を確かめる外側の実行器が無い。
  したがって repo を編集できる主体は鍵を持たなくても gate を消せる。
  **これは v1 から存在する構造で、本 wave が作る欠陥ではない。**
  D906 が署名対象へ「実行器と検査器の bytes」を含めよと書いているのがこの穴である。
  本 wave は閉じられないので、主張上限を {{D:ratification-claim-bound}} で定め、
  **D905 / D906 を「満たした」とは書かないことにした。**

- **段 6 の 3 所見が別々に書かれていたが帰結は 1 つだった。**
  broker が「検証子なら拒否する行」を書けると、台帳は 1 行の不正で全体が拒否されるため
  **最初の批准が gate を永久に閉じうる**。これは依頼の完了条件を直接壊す。
  3 件を 1 つの fix にまとめ、書き手が読み手と同じ規則で事前に確かめる形にした ({{F:broker-can-brick-the-gate-with-one-row}})。

- **人間の判断が入る唯一の場所の表示が偽装できた。** 初回批准は path と hash しか表示せず、
  operator は内容を 1 byte も見ずに `y` を押せた。加えて bidi override が端末へ素通りしていた。
  初回も全 bytes を表示し、LF 以外を単射な ASCII 表現へ escape する形へ直した。

- **実装子が親の監査の範囲外を突いて実欠陥を 1 件出した。** 回収した Ed25519 検証子は
  R が単位元の署名を受理する。親が独立検算したところ `cryptography` も受理し `PyNaCl` は拒否する、
  cofactor 付き検証と厳格検証の既知の分岐だった。**署名の生成には秘密鍵が要る**ので
  偽造経路ではないが、厳しくする変更は受理集合を広げないため厳格側を採った。
  **親の「所見 0 件」は「親が試した範囲での 0 件」だった。**
  実装子は勝手に直さずテストも緩めず、止まって確認を求めた。

- **実機でしか出ない本番欠陥を 3 件掘り当てた。** OpenSSL の一括署名が標準入力から読めない件
  ({{F:openssl-rawin-needs-seekable-file}})、`/dev/tty` を `r+` で開くと Python が拒否する件
  ({{F:devtty-rplus-not-seekable}})、broker と本体で閉包 tuple の順序が食い違っていた件。
  **いずれも回収コードに元からあり、あのコードは一度も緑になっていない。**
  1 巡目の fix 子は失敗 digest に紛れた `subprocess.run` の docstring を真因と誤判定した。
  親が実走して初めて本当の原因が出た。

- **codex 子は本 repo で pytest を実走できない (構造的制約)。** `tools/run_tests.py` の
  実行場所自動判定が `qstat -Q` を叩き、隔離環境は socket を拒否するため必ず `rc=16` になる。
  段 5 の 4 子すべてが当たり、単位 C の 1 巡目は 12 回試して 12 回とも失敗した。
  **以後、テストは親が毎回実走し、赤の本文と原因を実測して子の prompt へ貼る運用に切り替えた。**
  この切替が効いて、上記 3 件の本番欠陥が出た。

- **段 6 の fix が 1 件やりすぎて、逆に 1 件壊した。** レビューの指摘に従って共有 fixture の
  binding 参照先を合成 repo へ向けたところ、CLI subprocess を起動する consumer が壊れた
  (子プロセスは monkeypatch を継承せず、つねに実 repo を見る)。
  所見自体を再評価すると、**production は receipt の source commit と binding の commit が
  同じ履歴に属することを要求していない** (署名が縛るのは closure digest である)。
  つまり指摘は production より強い制約を共有 fixture へ持ち込むものだった。
  参照先の変更は戻し、意図は専用テスト 1 本で満たした。

- **変異は probe を先に回した価値がそのまま出た。** 事前登録では各変異の期待 node を 1 件と
  見積もっていたが、実測では M03 が 8 件、M05 が 24 件を巻き込んでいた。期待 node は完全集合
  でなければならないので、**probe 無しで本走していたら 4 件が MISMATCH で止まっていた。**
  probe は 18/18 で SURVIVED 0 件、本走は **baseline PASSED・18/18 KILLED・
  SURVIVED 0・MISMATCH 0**、期待 node 56 件が全件一致した
  (`repo_head` `87532e9f`、spec sha256 `9f54b633...`)。

- **変異 3 件は「登録不可」として外した。** 焦点再レビューが帰属を検算し、
  broker の信頼根不在検査は段 6 で新設した事前検査が同じ入力を先に弾くようになったため
  単独では殺せない (**防壁が二重になった結果**)、端末要求は二段構えで単一置換にならない、
  特殊 file 形式は別層も弾く、と判定した。DW-M01 に従い登録せず通常の回帰テストに留めた。
  代わりに source の tree mode 検査と decision 検査を新規登録した。

- **[T-1378] の見送りが D905 で失効していた。** 「批准台帳の外部 trust root と署名の新設」は
  2026-08-23 の裁定で「設けない」と見送られていたが、D905 (08-25) がこれを覆していた。
  本 wave がまさにその項目を実装している。phase doc の見送り台帳へ発火記録を追記した。

- **D956 の適用可否を親が裁定した** ({{D:d956-not-applicable-to-ratification}})。
  D905 より後の裁定で「受入 gate の実装は閉包を編集しない」と定めているが、
  主題が正式受入であって批准ではないこと、D526 が本件について逆向きに既裁定であること、
  そして**代償が実測でゼロ**であることから適用外とした。
  実測は tracked lock 32 件中 closure map 保持 0 件、repo 外 lock 1536 件中 36 件保持だが
  記録されているのは 8 path と 12 path のみで、**現行 25 path を記録するものは 0 件**だった。

- **受入は赤 1 件を除いて緑で、その 1 件で land が止まっている。**
  最終走は `1 failed, 17764 passed, 61 skipped`。
  赤は `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` で、
  **main 単独で再現する** (`b9d21206` で 15912/17700 = 89.898305%、閾値 90%)。
  peer session が**テスト node を 1 つも足さない wave** で同じ 1 件だけの赤を独立再現し、
  分母 17700 も一致した。**現時点で受入を通す全 wave が塞がっている。**
  本 wave の 126 node に所要をすべて与えても 16038/17826 = 89.97% で届かない。
- **「台帳を再生成すれば直るか」を実測して否定した。**
  `tools/update_acceptance_duration_ledger.py` は join ではなく**全面置換**で、
  再生成すると台帳は 15944 node から 17825 node になり、
  `test_t1574_changed_suite_ledger_node_delta_is_exact` の pin が
  所要値 12/12・node 集合 6/8・removed 1 件で壊れる。
  **所要値は機体負荷で動くので、exact 値 pin が在る限り生成器は永久に使えない**
  (観測差は 39% に達し、量子化の吸収範囲の外)。
  したがって hold 登録は一度きりの回避にならず、恒久的な更新が要る。
- **ユーザーが「迂回してでも land しろ、known-violation 登録で進めろ」と指示したが、
  それより良い道が見つかったので指示から外れた。** 明示して報告した。
  - **hold 登録は構造的に成立しなかった。** `flaky_test_holds.py` の `evidence_id` は
    `^F[0-9]+$` かつ `docs/failures.md` に実在することを要求するが、F 番号は land 時の
    fold でしか生まれず、fold には緑の受入が要る。canonical 台帳は fold だけが書けるという
    **運用規則との循環**である (コードが禁止しているのではない。codex の訂正を採用)。
    `reintroduction_task_id` は T 番号の placeholder 表記を許すのに `evidence_id` は
    許さない、という非対称がある。
  - **代わりに実測値の追記で実際に直した。** 診断走の JUnit から、pin される 8 接頭辞配下と
    removed 5 node を除いて 1851 件を追記し、**coverage 89.267882% -> 99.652174%**。
    既存値の変更は 0 件で、pin 4 本すべてを保存した。
    **除外は分母を減らさず numerator だけ減らすので coverage を下げる方向にしか働かない。**
    除外しなければ 100% であり、90% 到達は除外の有無と無関係である。
  - **4 本目の pin は親が見落としており、並行セッションの指摘で気づいた。**
    `test_acceptance_schedule_order.py` の G6 pin (無 suffix key の不在、`@real-repo == 0.19`、
    consumer の suffix fallback、reorder 後の順序)。規則によって結果的に保護されるだけなので、
    将来 `sort_swo_oracle` を除外から外す判断が出たときに無音で壊れる。
  - 8 接頭辞配下の 62 件は未被覆のまま残る。収集が 19736 件を超えると再び 90% を割るので、
    **新規 node 約 1911 件ぶんの余裕**がある。恒久解は {{T:acceptance-ledger-duration-pin}}。
- **codex と並行セッションの双方に独立判定させ、いずれも「迂回ではなく正当な是正」で一致した。**
  codex は親の主張 5 件を訂正した。うち「追記 1851 件に失敗中の G5 が含まれる」は
  **親が実測で否定した** (生成器が failure 行を既に除外しており `G5 in augmented: False`)。
- **段 8 の自己改善候補 2 件は byte 予算に収まらず、契約どおり編集を止めた。**
  「子は Web 検索禁止が prompt へ自動で入らない」と
  「隔離環境の子は pytest を実走できない」を `DW-O02` / `DW-O05` へ統合しようとしたが、
  最小形でも L1.5 が 9858 bytes となり予算 9566 を 292 bytes 超えた。
  **予算のために安全義務を削らない**ため revert し、候補として裁定へ回す。
- **並行 wave `dev-wave-b10-overthrottle-grid` が、批准突き合わせの撤去を草案している。**
  /rulings セッションの照会で判明した。草案
  (`dev-wave-jobs/b10-overthrottle-grid/draft-decisions-ratify-removal.md`) は
  「ユーザーの決定である」と書き、`enforcement_source_ratification.py` の削除と
  `ident.py` からの呼び出し除去を指示している。参照先に本 wave の file は 1 つも入っていない。
  - **撤去の中心的な理由は、本 wave が解いた問題そのものである。**
    草案は「批准は closure 版ごとにしか効かず、**書いた瞬間から古くなる**。
    運用を丁寧にしても解消しない」と書く。これは v1 (人間が 64hex を転記する形) には
    完全に正しく、**D905 がその解決を命じ、本 wave が実装した**。
    broker は official 起動の直前に remote HEAD から digest を計算して署名するので、
    転記は無く、古くなる構造が消える。**草案はこの機構を知らずに書かれている。**
  - **親が現行 main (`283fb29a`) の `docs/decisions.md` を自分で確かめた結果、
    批准突き合わせの廃止を定めた裁定は存在しない。** `廃止 / 撤去 / 削除 / やめ` で
    `批准` 周辺を検索して 0 件。逆に**同じ 2026-08-27 付のユーザー裁定 2 件が批准を拡張している** —
    D1070 (批准検査を artifact 受入と dispatch へ広げる)、
    D1071 (批准の撤回を正当操作とし、撤回記録で表す = 機構の存続が前提)。D1039 も同方向。
  - 親は b10 が誤っているとは主張しない (ユーザーが対話で直接指示した可能性があり
    decisions.md は遅れる)。**同日 landed の裁定と逆向きである事実を裁定材料として返した。**
  - 本 wave の land は何も削除しない (追加と gate の切替だけ)。撤去が正しければ
    b10 は削除対象が増えるだけであり、land が撤去を妨げない。
    逆に撤去が退けられた場合、**本 wave が着地していなければ D905 は未実装のまま残る。**
- **本 wave が確かめていないこと:** 実 repo の信頼根と台帳はまだ存在しない。
  したがって**現時点の批准受理集合は空**であり、certified な選択結果は 1 件も生成できない。
  これは land 前と同じ状態であり後退ではない。gate が開くのは、人間が一度きりの bootstrap を
  行い、broker で最初の receipt に署名した時点である。

## 次の一手差分

### 完了

- [T-1629] D905 の執行機構を署名 receipt として着地させた。閉包を 27 path へ広げ、
  批准 gate を v1 から v2 へ切り替えた。取り残し 3 worktree の内容は独立監査のうえ、
  Ed25519 検証子を採用、receipt 検証子と broker は書き直して採用した。
  remaining: none
  base: 86f22ac3704fb43aa026f2465d3280a79dce8cf109fa4930d84b6fe80f70a510

### 更新

- [T-1647] **P1・ユーザー gate 待ち (内容の承認のみ)**: A-2 の 4-cell certification 実走。
  台帳の履歴検査が merge で赤になる障壁は解消済み、D905 の執行機構も本 wave で着地した。
  残るのは**人間の一度きりの bootstrap と、最初の receipt への署名**だけである。
  手順は本 wave の insight に逐語で置いた。
  base: 7ec2b75e9aa7ebccad5f8acb8887cbf2d51f7600feb7fdd9d5d57ac4cccf8241

### 新規

- {{T:ratification-external-executor}} **P1・裁定へ返す**: 判定器が判定対象の内側にある
  構造的限界を閉じる設計。D906 の「署名対象に実行器と検査器の bytes を含める」を
  どう実装するか。repo の外に固定された実行器が要る。
- {{T:ratification-resume-bypass}} **P1・裁定済み (D1039 / D1070) → 実装待ち**: 既存 lock の
  resume と certified artifact consumer が署名 gate を素通りする。
  **本 wave は当初「裁定へ返す」と書いたが、方向は既に裁定済みだった** —
  D1039 が再開時の再検査を「穴として塞ぐ」と定め、D1070 (ユーザー裁定、2026-08-27) が
  批准検査を artifact 受入と dispatch へ広げると定めている。並行の /rulings セッションの
  指摘で気づいた。本 wave では素通りを固定する負例テストだけを入れており、実装は未着手。
  閉じるには campaign lock の authority へ signed receipt identity を記録する schema 変更が要る。
- {{T:ratification-key-lifecycle}} **P2・裁定へ返す**: 鍵の紛失・交代・信頼根 rotation を
  schema が表現できない。epoch / key-id を足す形の是非。
- {{T:ratification-window-lease}} **P2・裁定へ返す**: 批准から official 起動までの間に
  閉包 27 file が変わると receipt は機械的に拒否される (安全側だが承認が失効する)。
  この非介在条件を機構で強制する lease の是非。
- {{T:ratification-history-toctou}} **P2・新規**: 全史検査と履歴取得の間に履歴 view が
  変わると過去の不正を取り逃す。v1 も同一構造。外部の固定実行器を要する。
- {{T:qualification-signed-gate}} **P3・新規**: qualification lane へ署名 gate を付けるかは
  evidence-only lane の意味を変えるため別裁定とする。
- {{T:acceptance-ledger-duration-pin}} **P2・新規**: `test_t1574_changed_suite_ledger_node_delta_is_exact`
  の `added` 12 node は**実測所要値を exact に固定**している。所要は機体負荷で動くので、
  **この pin が在る限り生成器は永久に使えない** (本 wave の実測で 12/12 不一致、差は 39% に達した)。
  そのため本 wave は追記で回避し、8 接頭辞配下 62 件を未被覆のまま残した。
  恒久解は pin を値の性質を見る述語 (有限・非負・上限、あるいは相対誤差) へ置き換えること。
  そうすれば生成器が再び使え、未被覆も解ける。
- {{T:flaky-hold-evidence-id-circularity}} **P2・新規**: `flaky_test_holds.py` の `evidence_id` は
  `^F[0-9]+$` かつ `docs/failures.md` に実在することを要求するが、F 番号は land 時の fold でしか
  生まれず、fold には緑の受入が要る。**同一 wave 内で新種の赤を hold 登録できない。**
  `reintroduction_task_id` は T 番号の placeholder 表記を許すので、`evidence_id` も
  同じ表記を許すか、fold と hold の順序を変えるかの裁定が要る。
- {{T:dev-wave-web-search-prompt}} **P2・新規**: `DW-C01` の「子は Web 検索禁止」が
  子の prompt へ自動で入らない。本 wave は書き落として 2 回全損した (約 47 分・約 9M token)。
  `DW-O02` へ統合しようとしたが L1.5 の byte 予算に 292 bytes 収まらず revert した。
  予算を確保するか、`dev_wave_codex.py` が prompt へ機械的に前置する形にするかの裁定が要る。
- {{T:dev-wave-child-cannot-run-pytest}} **P2・新規**: 隔離環境の codex 子は
  実行場所判定が scheduler を叩くため pytest を実走できず必ず `rc=16` になる。
  本 wave の段 5 は 4 子すべてが当たり、1 子は 12 回空振りした。
  `DW-O05` へ統合しようとしたが同じく byte 予算に収まらなかった。
