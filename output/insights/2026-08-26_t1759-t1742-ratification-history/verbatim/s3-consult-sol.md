## 所見

1. `must-fix` — 複数の独立した台帳導入が許され、未批准行を merge で受理集合へ入れられる。

段 2 規則は「台帳を持つ親が 0 個なら 1 行以下」を各 commit に独立適用します。したがって同じ台帳なし祖先から、人間側が `d1`、攻撃側が `dE` をそれぞれ別 commit で導入し、merge 結果を `[d1,dE]` にすると全 node が合格します。現行規則は二つ目の独立 blob が一つ目の厳密な前置拡張ではないため拒否します。導入 commit は reachable DAG 全体で高々 1 件という条件が必要です。

成果物への影響: `dE` を変更後 closure digest にすれば `verify_ratified_contract_loader_binding()` が `dE` を返し、未批准の certified v2 lock が選択可能になります。

2. `must-fix` — `_load_rows()` は blob bytes から行 tuple への単射ではありません。

`raw.endswith(b"\n")` の後に `raw.splitlines()` を使うため、LF、CRLF、途中の CR を同じ行境界として畳み込みます。例えば親を `R(d1)+LF`、子を `R(d1)+CRLF+R(dE)+LF` とすると、両行は canonical JSON として通り、子の tuple は `(d1,dE)` です。新規則は厳密な 1 行追記として受理しますが、現行 byte 前置検査は最初の行末が LF から CRLF に変わった時点で拒否します。

`raw.split(b"\n")` に変更して残存 CR を canonical 比較で拒否するか、各 blob が tuple から LF 終端で再構成した bytes と完全一致することを要求する必要があります。

成果物への影響: 未批准 `dE` が受理集合へ入り、台帳 bytes も canonical LF JSONL でない状態へ変わる一方、レポートは正常な 1 行追記として扱います。

3. `must-fix` — merge 規則が証明するのは「親に行が存在したこと」だけで、人間批准ではありません。

共通の正規台帳 `[d1]` から二枝を作り、一方を人間批准 `[d1,d2]`、他方を未批准 `[d1,dE]`、merge を `[d1,d2,dE]` とすれば、新規則はすべて受理します。独立導入を 1 件へ制限しても、この反例は残ります。任意個の枝を使えば、一つの octopus merge で任意個の行を受理集合へ加えられます。

これは各枝の 1 行追記が認証済みである場合だけ安全です。しかし D905 は成りすませない実行主体が未着地であるとしています。各追加 commit を認証済み受領証へ束縛するか、その前提が成立するまで並行 merge を批准として扱わない必要があります。

成果物への影響: 攻撃枝の `dE` が台帳と批准集合へ残り、`enforcement-source-closure-unratified` で落ちるはずの certified 選択が成功します。

4. `should-fix` — shallow と graft の存在確認は check-then-use であり、検査中の変更に弱いままです。

実履歴 `p:[d1] -> c:[dE]` は置換として拒否されます。しかし開始時検査後に `c` を shallow root または graft root にすると、履歴走査と `_real_parents()` は `c` を親なし導入として扱い、1 行の `dE` を受理できます。`refs/replace` は全 `_git` 呼出しで無効化されるため同じ経路にはなりませんが、graft には対応する無効化がありません。安定 checkout だけを脅威モデルにするなら、その限定を成果物に明記すべきです。

成果物への影響: 検査中に履歴境界を書き換えられる環境では、置換後の `dE` が唯一の批准行として返り、certified 選択が開きます。

5. `should-fix` — `--full-history` の完全性が未証明のまま安全性の根に置かれています。

M4 の「blob がどれかの親と異なる commit」という一般化は、段 2 自身の mode-only 反例で既に破れています。同一 blob OID の `100644 -> 100755` が path history に列挙されるためです。正しい候補述語は blob 差ではなく tree entry の存在、mode、type、OID の差です。

また Git の版は固定されず、local config の `log.follow` なども全て無効化されてはいません。rename、directory 移動、octopus merge は M4 で未測定です。空 commit の省略は安全ですが、悪い遷移が 1 件でも `C` から抜けると、その node は検査されず HEAD の行だけが返ります。安全側なら全 reachable commit を列挙し、実親との tree entry 差をコード側で選別すべきです。

Git 文書は指定された射影に含まれず、Web 検索も禁止されているため、`--full-history` が必要な完全性を仕様として保証するかは未確認です。

成果物への影響: 列挙漏れ commit で加えた digest が HEAD の受理集合へ入り、台帳レポートに検査済みとして現れます。

6. `should-fix` — batch 化後の読み込み量は DAG に線形ではなく、ピークメモリが二次量になり得ます。

N commit が一行ずつ正しく追記すると、各 blob の大きさは 1 から N 行です。全 blob を一つの `cat-file --batch` の `stdout=PIPE` に集める設計では、保持量は `1+2+...+N`、つまり O(N²) です。巨大な初回 blobも、行数違反を判定する前に全体を読み、全行を解析します。現行実装も総読込量は大きくなりますが、全 blob を同時に保持する退行はありません。

成果物への影響: 大きな履歴では批准集合を返す前に timeout またはメモリ枯渇となり、certified 選択とレポート生成が一律停止します。

7. `nit` — 既存の `match=` は受理への退行を直接は隠しませんが、例外の優先順位が未規定です。

既存テストは `pytest.raises` を使うため、履歴が受理された場合はメッセージを更新しても失敗します。一方、mode 変更と複数行追加など複合違反では、判定順により従来の `added more than one row` が `mode changed` に変わり得ます。既存メッセージを維持するなら、削除、行遷移、mode の判定優先順位も契約化し、複合違反を追加すべきです。

成果物への影響: 受理集合は変わりませんが、失敗レポートの理由と、それを参照するテスト及び障害分類が変わります。

8. `nit` — 「両親が台帳を持つ merge は必ず実運用で発火する」という親の推論は成立していません。

ff-only の ref 更新でも、incoming range 内に merge commit を含めることはできます。逆に rebase または cherry-pick で並行追記を直列化する運用なら、両親が台帳を持つ規則は一度も発火しません。段 2 の synthetic `commit-tree` テストは規則自体を試しますが、実 land 経路で発火する証拠にはなりません。

成果物への影響: ff-only かつ直列化された運用では certified 選択値は変わらず、T-1742 を実運用で解いたというレポート上の参照だけが過大になります。

## 構成した反例履歴

以下で `d1 = "1"*64`、`d2 = "2"*64`、`dE = "e"*64`、`R(d)` はその digest の canonical JSON row、mode は全て `100644` とします。

### 反例 1: 独立導入の merge

```text
o: parent=なし、ledger=なし
├─ a: parent=o、ledger=[d1]       人間が批准
└─ e: parent=o、ledger=[dE]       人間は未批准
   \ /
    m: parents=(a,e)、ledger=[d1,dE]、HEAD
```

現行規則は `a` と `e` のうち後に列挙された方で strict prefix 違反になります。新規則は `a` と `e` を別々の正当な導入、`m` を正確な親集合の和として受理し、`{d1,dE}` を返します。

### 反例 2: 共通台帳からの未批准枝

```text
o: ledger=なし
b: parent=o、ledger=[d1]
├─ l: parent=b、ledger=[d1,d2]       人間が批准
└─ r: parent=b、ledger=[d1,dE]       人間は未批准
   \ /
    m: parents=(l,r)、ledger=[d1,d2,dE]、HEAD
```

新規則では両枝が 1 行追記、`m` は両親の行順を保存した完全な和集合です。現行規則は兄弟 blob 間の前置比較で拒否します。導入 commit を一意にしても防げない反例です。

### 反例 3: CRLF による byte 前置検査の消失

```text
o: ledger=なし
p: parent=o、bytes=R(d1) + LF
c: parent=p、bytes=R(d1) + CRLF + R(dE) + LF、HEAD
```

`_load_rows(c)` は `(d1,dE)` を返すため新規則は受理します。現行規則では `c` の bytes が `p` の bytes から始まらず拒否されます。

削除、空 blob への置換、親に存在する行の欠落、親内での行順変更については、安定した完全履歴が `C` に入るという前提下では回避経路を見つけていません。到達不能 commit と replace ref も、その前提下では受理集合へ直接影響しません。

## 親 brief への反論

- 不変条件 4 は CRLF 反例により偽です。
- 「新規則は現行より強い」は偽です。独立導入と並行枝の二経路で、現行が拒否する digest 集合を受理します。
- 「不一致は正直に unratified で落ちる」は、攻撃側の `dE` が変更後 closure digest なら成立しません。台帳自体は closure 外なので、`dE` の追加で closure digest は動きません。
- M4 の blob 差との完全一致は mode-only commit で一般化不能です。
- M5 の「wave branch 側で必ず merge」は運用規則から導かれていません。
- shallow、graft、replace のうち、replace は静的に無効化されていますが、shallow と graft は検査中不変という未記載の前提を必要とします。

## 総括

直接の拒否から受理への退行は三つあります。複数の台帳導入、未認証枝の merge、CRまたはCRLFを畳み込む `_load_rows()` です。特に最初の二つは、変更後 closure digest を未批准枝へ置くだけで certified 選択を開けます。

実装前に最低限、reachable DAG 全体で導入 commit を一意にし、LF bytes と行 tuple の単射を実際に成立させ、各枝の追記が人間批准済みであることを機械的前提へ加える必要があります。静的検査のみで、pytest と実測は実行していません。