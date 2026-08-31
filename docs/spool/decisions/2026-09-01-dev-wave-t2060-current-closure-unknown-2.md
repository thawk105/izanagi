---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t2060-current-closure-unknown
seq: 2
---

## {{D:historical-conformance-unknown-display}}. 歴史閲覧は現行適合を unknown と明示表示する

**決定:** 歴史 view は `current_verifier_conformance` を exact `"unknown"` として持ち、Layer 3 の
歴史 report は同じ値を top-level の optional field として出す。certified report は同 field を
持ってはならず、schema が `certifying_input == true` のときこれを拒否する。
記録 epoch の nested object、reason enum、certified 側の `current-closure-unavailable` は変えない。

**理由:**
- D1245 は歴史閲覧の拒否理由にしないことと、現行適合を unknown と表示することの 2 つを要求する。
  前者は中央 gate で既に成立していたが、後者はどこにも実体が無く、読者は記録時の判定
  (`state=E1 / reason=recorded-closure`) を現行適合の主張と読めた。
- nested epoch object に置くと既存の exact dict 期待値を書き換えることになる。top-level なら
  既存期待値を 1 つも変えずに同じ意味を出せる。
- `additionalProperties: false` の下で新 field を足すと certified 契約まで受理形が広がるため、
  certified 側の禁止条件は新設の gate ではなく**その拡大を打ち消す補償**である。
- optional に留めることで、既に保存された v2 / v3 report が 1 件も読めなくならない (絶対規律 7)。

**却下した選択肢:**
- nested `campaign_verifier_epoch` object へ足す — 既存 test の exact dict 期待値の変更を強いる。
- top-level `required` へ入れる — 保存済み report を無効化し、規律 7 に反する。
- 表示を足さず「拒否しない」だけで完了とする — 現行適合を過大主張しうるという D1245 の
  却下理由に当たる。

## {{D:purpose-declaration-is-per-consumer}}. どの消費者がどの purpose を宣言するかは D1245 と別の裁定にする

**決定:** D1245 は歴史閲覧と現行認証の**分け方**を定めた裁定であり、既存の各消費者が
どちらの purpose を宣言するかまでは決めていない。過去の測定を読む消費者
(`replay.load_landscape`、`s1_report` の epoch gate、`s8b_oracle_report` の epoch 証拠) の
再分類は、certified 成果物の受理集合を変えるため、D1245 の実装として親が一存で行わない。
再分類はユーザー裁定を経た別 wave で行う。

**理由:**
- 現行閉包の可用性検査は「作業ツリーが commit 済みか」を見るもので、意味互換性そのものではない。
  しかし外すと、certified と名の付く gate が汚れた作業ツリーでも通るようになる。これは
  「現行の正しさ主張に必要な意味互換性は維持する」の線引きを動かす判断である。
- `s1_report` は可用性 gate と保存済み COMMIT 証拠検査が別関数のため、記録された証明の鎖を
  失わずに可用性だけを外せる。ただし素朴な purpose 付け替えでは
  `E0 / v1-authority-absent` の拒否まで同時に落ちるため、局所に明示的な維持が要る。
- `replay.load_landscape` は exact 型拒否と replay 証拠 capability に束縛されており、
  purpose だけ替えても動かない。動かすために wrapper を緩めると保存済み COMMIT 検査と
  証拠 capability を同時に失い、絶対規律 2 に触れる。

**却下した選択肢:**
- 本 wave で `s1_report` を移す — 小さく安全に見えるが、certified gate の受理集合を
  ユーザー裁定なしに広げる。
- 記録 commit と保存済み受領証は検査するが現行閉包を要求しない第三の purpose を新設する —
  現在の消費者集合を越える一般化であり、要求外の互換層に当たる。
- 現状維持とし何も記録しない — 同じ検討を後続の着手者が繰り返す。
## {{D:expired-external-evidence-skips-only-on-absence}}. 失効した外部証拠は不在のときだけ skip し、重複と破損は fail-closed のまま残す

**決定:** repo 外の保持期限で失われうる証拠に依存する検査は、必要な証拠の**実在を pin 付きで判定**し、
**不在のときだけ**失効した識別子を理由に出して skip する。重複と内容不一致は従来どおり赤にする。
失効に依存しない検査は合成入力へ移して実走を維持する。**負例は skip する側のラッパーではなく、
skip しない下位 resolver を直接呼ぶ。** skip 経路自体の正例も別 node で持つ。

**理由:**
- 入力が恒久的に失われた検査は、緑にできない赤であって coverage ではない。放置すると
  受入全走が全 wave で止まり続け、何も守らないまま前進だけを止める。
- 一方で「使えないなら全部 skip」は、失効と無関係な検査まで落として受理集合を広げる。
  実測では最大 23 node が巻き添えになる形だった。
- **負例が skip する側を呼ぶと、「重複も破損も skip に倒す」変異で node が失敗ではなく skip になり、
  fail-closed が壊れたことを検知できない。** 変異で実測して確かめた。
- 記録された過去の検証事実は無効にしない。再検証できないことと、事実でないことは別である
  (絶対規律 7)。

**却下した選択肢:**
- 必要部分を repo 内の凍結 fixture へ移す — **元 bytes が既に失われており実行不能**。
  復元できるのは原本が別媒体に在る場合だけである。
- 除外登録する — 契約が要求する既存の失敗記録が無く、記録を作っても受入が緑にならなければ
  land できず循環する。
- root の有無だけを見る既存ガードの粒度を上げる — 失効に依存しない検査まで巻き添えにする。
- 期待値から証拠を逆算して fixture を作る — 独立 2 経路の一致という当の性質を自作自演にする。
