## 判定 (GO / NO-GO)

**GO：実装なしで段 4 へ進める。ただし、不在証明と pin 閉包の説明は訂正が必要。**

授権済みの production 撤去漏れは確認できませんでした。一方、親 brief の repo 全体に及ぶ件数断定は誤りです。以下の **real / refuted は親への疑義の判定**です。

静的検査のみ実施。編集・テスト実走はしておらず、緑は主張しません。

## 不在の主張の再測定

### 1. 「`perf_sha_by_cell` は 0 件」の範囲が不明 — **real**

`git grep -n -I perf_sha_by_cell` では、追跡ファイルに **6 行**あります。

- `docs/decisions.md:59973`
- 前 wave の `s4-adjudication.md:18,92,93,97`
- 同 `verbatim/s5-u2.md:3`

ただし、production 撤去漏れという疑義は **refuted**。別 key の `binary_sha256`・`binaries_by_cell` から追うと、driver:1007–1058 は receipt/store 検査に使い、:1748–1793 の評価引数へ過去 binary hash を渡していません。`_V2Plan`:884 と返却箇所も照合しました。

**影響：** 記録上の検索範囲の誤表示。現行の値・受理集合・参照への影響はなく、件数表現自体は nit。

### 2. 「旧 snapshot key は負例 1 件だけ」 — **real**

同じく追跡ファイルの検索では **17 行**です。

| 分類 | 一致行数 |
|---|---:|
| docs・archive | 4 |
| Python 負例テスト | 1 |
| insight の Markdown | 8 |
| insight の JSON に格納したテスト出力 | 4 |

具体的反例は `output/insights/2026-08-11_t750-freeze-v2-manifest/verbatim/s6-review-1.md:71`、前 wave の `README.md:101` などです。現 wave の未追跡 brief・段 2 記録は、この件数に含めていません。

JSON の一致ファイル 2 件を `json.loads` して辞書 key を再帰走査すると、**実 key としての一致は 0 件**。一致はテスト出力の文字列でした。また `output/s8b-freeze` の JSON 12 件、`output/s8b-freeze-budget-approvals` の 1 件にも当該文字列はありません。

manifest の key 集合:55–60、生成:719–737、拒否:965–966 と負例:797–819 は整合しています。

**影響：** production 残存の反例ではありません。「全 repo で 1 件」を根拠にした成果物調査の説明が不正確です。件数訂正は nit。

### 3. 間接供給元を取り残した可能性 — **refuted（確認した静的経路内）**

test 以外の `pipeline.evaluate` caller は次の **5 箇所**です。

| caller | 転送引数の構築元 |
|---|---|
| `campaign/loop.py:782` | `evaluate_options`:710–766 |
| `campaign/screening_driver.py:639` | :600–638 |
| `campaign/s1_direct_comparison.py:1233` | :1037–1043、:1214–1231 |
| `campaign/s8b_oracle_driver.py:1783` | :1558–1579、:1748–1781 |
| `qualification/t126_driver.py:543` | `_member_pipeline_perf_kwargs`:697–708 |

いずれも具体的な期待 hash を供給しません。設定値を渡す経路も、key はこれらの構築箇所で決まっています。

さらに内部経路を追いました。

- `evaluate` → `_prepare_evaluation_core`：pipeline:2675、:2682。
- loop:768 → `_prepare_evaluation` → core：pipeline:2723–2725。

後者には `**kwargs` 転送が実在しますが、入口の `evaluate_options` に旧期待値はありません。読んだ経路に改名・部分適用による供給は見つかりませんでした。これは任意の動的 Python 呼出しまで排除する全称証明ではありません。

**影響：** generic gate は残る API として有効ですが、確認した production caller では既定値 `None` により発火しません。

### 4. approved spec 不在と fail-closed — **refuted**

現物は `s8b_oracle_spec.py`：

- :19 — `SPEC_REL = "output/s8b-oracle-spec/reviewed_spec.json"`
- :23 — `APPROVED_SPEC_SHA256 = None`
- :182–199 — pin 不在を先に拒否し、その後で固定パスを読む。
- :259–261 — public loader からこの経路へ入る。

実測：

```text
固定パス exists=False、is_symlink=False
git ls-tree -r HEAD -- output/s8b-oracle-spec/reviewed_spec.json
rc=0、stdout=''
```

**rc=0 ではなく stdout が空であること**を確認しました。

ただし「official は必ず `no-approved-spec` を返す」は広すぎます。driver:1391 や report:2552 に達する前に、別の前提条件で拒否される場合があります。

**影響：** 通常の承認 pin の下では official 成功へ進めません。不在だけから個々の実行の最初の拒否理由は断定できません。

## 行番号・アンカーの照合

行番号ずれの疑義は **refuted**。brief の実アンカー表は一致しています。

| 対象 | 現物 |
|---|---|
| R1 | driver:524–527 |
| R2 | budget:96–118、driver の呼出し:1433 |
| R3 の assertion | report:2548 |
| 旧 key 負例 | `test_s8b_oracle_manifest.py:803` |
| generic gate | pipeline:1565、:2091 |

**R3 の範囲不足は real。** 「解決経路」は report:2547–2560、consumer 引渡しまで含めれば :2563 です。assertion 1 行と経路全体の撤去を同一視できません。

**影響：** 撤去対象の解釈次第で、選択検査だけでなく再検証・manifest 検証・consumer 入力まで変わります。

## 凍結 pin 閉包の再検査

**「実装なしなら変更対象なし」は支持。「撤去しても影響先なし」への拡張は real な誤りです。**

| 軸 | 現物と仮想撤去の影響 |
|---|---|
| file 全体 SHA-256 | R3 は `generator_versions.report` の対象。manifest:67、:458–496 が source bytes を照合する。現 report hash は `30fe2b1bcad143f5a85ca32250744522d6049f4c71e9b853618e3af2dd0091c7`。 |
| 行番号 | `test_ccbench_spawn_sites.py:2959–2964` が driver の評価行 **1783** を pin。R1 やその前の R2 呼出しを行ごと消せば参照がずれる。 |
| 正規表現・文字列アンカー | budget の null 拒否は `test_s8b_budget.py:72` の `match="null"`。driver 側は `test_s8b_oracle_driver.py:1609` の prefix と :2330–2331 の literal。source 行を照合する正規表現 pinとは別物。 |
| 派生 digest | `test_s8b_oracle_manifest.py:92–93` の golden spec に report hash が埋まり、:63–65 の `PIN_GATE_SPEC_SHA256` に波及する。fixture は現 source bytes をコピーする（同:219、`s8b_oracle_spec_fixture.py:92–99`）。 |

R3 変更時に golden spec の report hash を更新すれば、**golden bytes と spec digest も変わります**。放置すれば generator hash 照合が拒否します。

再生成する manifest では、さらに `generator_versions` → `manifest_id`（manifest:661–662、:736）→ manifest digest（:1083）へ波及します。budget ledger は driver:1581–1586 でその manifest digest に束縛されています。これは**新規生成時の依存鎖**であり、既存の凍結 JSON が source 編集だけで書き換わる意味ではありません。

今回確認した固定成果物に、変更必須の live approved spec はありません。広域 JSON 全件の再帰走査は完遂しておらず、上記を repo 全体の完全な pin 閉包とは主張しません。

## 親の一般化しすぎ

**測定範囲を越えた断定**

- brief:45–46：Python 内の残存件数を repo 全体の件数として読める形に拡張している。
- brief:66–68：approved spec 不在は、fixture の hash pin・行番号 pin の不在を意味しない。

**提示された証拠では未立証の断定**

- brief:51：「R1〜R3 の撤去はいずれも受理集合を広げる」。
  - R1 の null 拒否は manifest:603–606 にも残る。
  - R2 は loader 呼出しだけ消すと `limits` の供給を壊す。
  - R3 は撤去範囲自体が一意でない。

**影響：** 局所述語の削除、経路の破損、最終受理集合の拡大を混同すると、段 4 の撤去判断と成果物影響の説明を誤ります。

## nit

- docs・過去 insight に旧識別子があること自体は撤去漏れではありません。消す必要はありません。
- アンカーの行番号訂正は不要です。R3 の範囲だけ区別が必要です。
- generic gate の引数位置は public API の pipeline:2595 も併記すると正確です。

## 総括

**「今回必要な授権済み実装は確認できない」は維持できます。「不在を repo 全体で証明した」は維持できません。**

親へ返す訂正点は、検索母集団の明示、R3 の範囲、仮想撤去時の pin 依存、局所削除と最終受理集合の区別です。新しい gate・検査・台帳・一般化の追加は提案しません。