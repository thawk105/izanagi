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
- {{T:ratification-resume-bypass}} **P1・裁定へ返す**: 既存 lock の resume と
  certified artifact consumer が署名 gate を素通りする。閉じるには campaign lock の
  authority へ signed receipt identity を記録する schema 変更が要り、D956 の領域に当たる。
  本 wave では素通りを固定する負例テストだけを入れた。
- {{T:ratification-key-lifecycle}} **P2・裁定へ返す**: 鍵の紛失・交代・信頼根 rotation を
  schema が表現できない。epoch / key-id を足す形の是非。
- {{T:ratification-window-lease}} **P2・裁定へ返す**: 批准から official 起動までの間に
  閉包 27 file が変わると receipt は機械的に拒否される (安全側だが承認が失効する)。
  この非介在条件を機構で強制する lease の是非。
- {{T:ratification-history-toctou}} **P2・新規**: 全史検査と履歴取得の間に履歴 view が
  変わると過去の不正を取り逃す。v1 も同一構造。外部の固定実行器を要する。
- {{T:qualification-signed-gate}} **P3・新規**: qualification lane へ署名 gate を付けるかは
  evidence-only lane の意味を変えるため別裁定とする。
