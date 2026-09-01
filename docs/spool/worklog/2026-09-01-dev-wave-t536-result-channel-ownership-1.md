---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: dev-wave-t536-result-channel-ownership
seq: 1
title: [T-536] 計算ノードの結果チャネルを親の包み側の所有にする (コード、branch worktree-dev-wave-t536-result-channel-ownership)
---

## 本文

- **依頼と裁定。** D859 (2026-08-25 /rulings 全件、択 (a) 採用) に従い、被検査コードが結果を
  書けない経路へ再設計した。ユーザーは「本題の所有境界の設計だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外」と指定した。
- **編集面の重複検査。** 依頼が名指しした稼働 wave `dev-wave-t2061-acceptance` は、branch・
  worktree・稼働 session のいずれにも実在しなかった。実在する 7 worktree と全 branch を対象に
  検査し直し、`tools/pegasus/dispatch_compute.py` の差分は 0 件だった。
- **生死確認 (段 2 の plan が未実測と明記した点を親が測った)。** login node pegasus02 と
  計算ノード bnode007 の両方で、非特権の user / mount 名前空間が使えることを確認した。
  計算ノード側は `--task generic` で probe を投入した (request 965573.nqsv、child rc=0)。
  read-only の bind mount 下では被検査側の書き込み・作成・削除・mode 変更がすべて拒否される。
  **同じ名前空間の中からは read-only を外せる**が、**入れ子の名前空間からは外せない**。
  被検査側が自分の名前空間に別の file system を重ねても、親の視界には届かない。
- **段 3 の 1 本が内容フィルタで拒否された。** 親が書いた敵対相談の prompt が
  「誤った緑を作る経路を手順として書け」という攻撃寄りの表現だったため、49 回の model 呼び出しと
  1358 秒を費やして出力ゼロで終わった。受理条件を 1 つずつ列挙させる検査の語彙へ書き直して
  再投入し、通った。攻撃の語彙で敵対レンズを書くと成果物がゼロになる。
- **段 6 のレビュー 2 本が、焦点走が緑のまま残っていた欠陥を 2 件出した。** どちらも親が実測で確定した。
  (1) 結果 directory だけを read-only にしても、被検査側が**書ける祖先を rename** して同じ
  絶対 path を作り直せる。実測では偽の結果を置くことに成功し、名前空間の外から元の path を
  読むとその偽の内容が返った。所有境界が成立していなかった。
  (2) 隔離した被検査コードが uid 0 で動き capability を全付与された状態になっていた。
  修正案もそれぞれ実測してから fix 子へ渡した。祖先の mount point 化で全階層の rename が塞がり、
  祖先の中身への書き込みは成功したままだった。内側で実 uid へ写し戻すと identity が隔離前と一致した。
  設計判断は {{D:compute-result-ancestor-pinning}} と {{D:compute-child-identity-preserved}}。
- **保証の言い方を限定した。** 守る相手は被検査コードとその子孫だけで、名前空間の外にいる
  同一 uid の別 process は守らない。「常に書けない」ではなく「親と login 側が読む実体を
  変更できない」と書く。名前空間が使えない環境では走行が infra へ倒れる。fallback は入れない。
  {{D:compute-result-channel-boundary-scope}}。
- **D859 の第 2 条項は実装しなかった。** 親は当初「scheduler の終了状態は入力が実在しない」と
  裁定したが、これは言い過ぎだった。scheduler の man に wait(2) の終了状態を 16 進で出す欄があり、
  終了コード 7 の試験投入 (request 965604.nqsv) に対して実際に読めた。ただし読める窓は
  21:49:32 から 21:49:36 の約 5 秒で、21:49:39 には request が消えて読めなくなった。
  取り逃しをどちらへ倒しても規律に反するため、この変更には入れない。
  {{D:scheduler-exit-code-window-too-short}}。
- **変異の確認。** 事前登録した 3 変異がすべて狙った層で殺されることを確認した。
  入れ子の名前空間を外す変異では、負例が「被検査側が実際に書けるようになった」ことを
  直接観測して落ちた。負例が空回りしていないことの実証である。
  1 件目は最初、狙った層でない場所で殺されていたので再照準した。
  これは変異 harness の本走ではなく、親が一時変異と即時復元で確かめたものである。
  queue が混雑しており (gen_S 総数 199、待ち 48、hold 98)、混雑下で dispatch を強行しない
  方針に従った。復元は commit との bytes 一致で確認した。
- **親の操作ミスを 1 件記録する。** 受入全走を投入した直後、親が spool の base digest を取るために
  同じ作業ツリーで `git checkout main -- docs/` を実行した。受入待ち手はその裏で main を
  取り込む merge を進めており、両者が競合して**main の台帳更新を巻き戻す混成 merge** ができた。
  land していれば他 wave の記録を消していた。merge を捨てて実装 commit へ戻し、
  記録 commit を受入より前に置く順序へ組み直した。作業ツリーを触る操作は、
  受入待ち手が走っている間は行わない。
- **非帰属の赤。** 変異 harness 系の 5 件は login node の site policy が
  `--runner-mode local` を拒否するため赤になる。親の変更を外した base でも同一に赤であることを
  実測で確認した。触っていない file の経路である。

## 次の一手差分

### 完了

- [T-536] 被検査コードが書けない結果経路へ再設計した。親が起動前に赤い guard を置き、
  被検査コードは結果 directory を read-only にした mount 名前空間と入れ子の user 名前空間の
  内側でだけ動き、祖先 directory はすべて mount point にして rename を塞ぐ。親は
  子孫を回収した後に置換で publish する。login 側は変更していない。
  負例は実 launcher を通し、被検査側が記録した errno で拒否を観測する。
  remaining: none
  base: 10609115523b149f1c03ab28c8f170e590d0590d54282b32709cdc5fbfc5001e
