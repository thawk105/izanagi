## 所見

1. **must-fix — `-0.0` が bit 完全一致をすり抜け、producer 不可能な summary が受理される。**  
   `p3_b4_floor_artifact_issuer.py:283-288` は `-0.0 < 0.0` が偽なので負ゼロを受理し、再導出比較も `:538-543`、`:572-580`、`:631-634` の `==` 相当で正負ゼロを区別しない。次の fragment を通常のゼロ差 fixture に入れると全比較を通る。

   ```json
   {
     "upper": -0.0,
     "candidate_floor": -0.0,
     "derivation": [{
       "samples": [{
         "window_id": "window-synthetic",
         "pair_id": "pair-synthetic",
         "sample_index": 0,
         "session_medians": {
           "candidate_1": 100.0,
           "candidate_2": 100.0,
           "reference": 100.0
         },
         "gain_1": -0.0,
         "gain_2": -0.0,
         "difference": -0.0
       }],
       "strata": [{
         "window_id": "window-synthetic",
         "pair_id": "pair-synthetic",
         "values": [-0.0],
         "upper_function": "sample_max/v1",
         "upper": -0.0
       }]
     }]
   }
   ```

   producer は `floor_pair_driver.py:1358-1363` の演算と `abs` から `+0.0` を生成する。一方 issuer は `p3_b4_floor_artifact_issuer.py:753-759` でこれを `Fraction(0, 1)` に畳み、`source_float_hex` だけを負ゼロにする。NaN は拒否されるため、有限 float で `==` と bit 一致が違う実例はこれである。  
   **放置時:** 数値 floor は `[0,1]` のままだが、producer 不可能な入力が受理集合へ加わり、採用 float の符号 bit と evaluator に渡る値の表現が一致しなくなる。

2. **must-fix — issuer は summary-bound spec が producer に受理可能かを検証せず、caller が作った自己整合 JSON を発行できる。**  
   producer は `floor_pair_driver.py:1141-1161` で spec の完全な閉 schema を要求するが、issuer は `p3_b4_floor_artifact_issuer.py:788-798` で object と `schema` しか確認せず、identity 用 field を `.get()` で拾うだけである。実際、test fixture の spec (`test_p3_b4_floor_artifact_issuer.py:61-74`) は必須の `provenance`、`pairs`、`windows`、`statistics` 等を欠き、未知の `fixture_kind` を持つため producer には絶対に受理されない。それでも同 fixture から発行と load が成功する前提になっている (`:375-397`)。  
   **放置時:** caller が選んだ medians、env、protocol、campaign から任意の自己整合 floor と参照を「authoritative」artifact として生成でき、受理集合・成果物値・identity が producer の実出力から離れる。

3. **must-fix — public loader に caller 自己申告経路が残っている。**  
   `load_authoritative_floor()` は caller 指定の `artifact_path` を受け、digest は既定値 `None` で省略できる (`p3_b4_floor_artifact_issuer.py:966-985`)。さらに `source_summary` は文字列と hash の形だけを検査し、参照先の存在・bytes・再導出を確認しない (`:1073-1124`)。材料レポート test 自身が、存在しない source と `"1"*64` 等の架空 hash を持つ artifact を手書きし、loader に受理させている (`test_p3_b4_material_report.py:97-136`)。材料レポートの正規 CLI は固定 resolver を使うため直接の fallback はないが、public API としては再侵入している。  
   **放置時:** public caller は floor 値・artifact path・架空の source 参照を選んだ `B4AuthoritativeFloor` を取得できる。正規 material-report 出力への影響には §5 pin が必要だが、API が返す権威参照自体は caller 選択になる。

4. **must-fix — exact 化 test は変更前の値を oracle にせず、M1 の変異帰属も別層に落ちる。**  
   `test_p3_b4_floor_artifact_issuer.py:228-239` は expected ratio と hex を、元の fixture JSON ではなく既に issuer が返した `accepted.candidate_floor` から再計算している。issuer が candidate を 1 ULP 動かしてから `candidate_floor`、`floor_exact`、`source_float_hex` の三つへ同じ値を入れる変異なら全 assert が通る。また登録 M1 の「Fraction を float のまま返す」は `:231-237` で別 module の `as_b4_exact_fraction()` が先に赤を出すため、issuer 単体への帰属になっていない。  
   **放置時:** 将来の 1-bit 値改変で成果物 floor と評価境界が変わっても test が通り得て、M1 の KILLED 帰属も過大申告になる。

5. **nit — 到達不能な assert がある。**  
   `p3_b4_floor_artifact_issuer.py:930` の `assert summary.identity is not None` は、直前の `_authority_value()` が同じ否定条件で必ず例外にする (`:827-833`) ため、偽のまま到達する入力が存在しない。`python -O` で消えても挙動は変わらない。  
   **放置時:** 成果物値・受理集合・参照は変わらないため nit。

## scope 外だが real

- `window_artifacts` は型しか検査せず重複を許す (`p3_b4_floor_artifact_issuer.py:362-374`)。campaign strata も重複を検査せず、`planned=1` に対して巨大な `retained_sample_count` を置ける (`:384-441`)。これは producer 不可能な summary を追加する real な穴だが、exact window・標本数および finalize 束縛の validator 拡張は D1696 で人手責任に残されたため、この wave の must-fix にはしない。
- pinned v2 の D1699 不適合と binary64 中間丸めによる過小評価は既裁定どおり real だが scope 外。コードは非保証を保持している (`p3_b4_floor_artifact_issuer.py:47-56`)。
- 現行の実 producer receipt から `protocol` を導出できず、正規 summary の発行が拒否されることは test でも確認されている (`test_p3_b4_floor_artifact_issuer.py:186-218`)。段 4 が裁定パッケージへ送った既知事項であり、本実装の欠陥には数えない。

## 反証できなかった点

- NaN・Infinity、bool の float 代用、空の `window_artifacts` / `campaigns` / samples / strata、重複 sample key、重複 derivation stratum、重複 campaign ID は拒否される。巨大 int は型として通るが、問題は上記 scope 外の関係検査不足である。
- `-0.0` を除く有限 binary64 では `as_integer_ratio()` による値改変を認めず、数値として `[0,1)` 外の値が通る経路も反証できなかった。
- resolver では逐語 `未記入` だけが `None` になり、grammar・file・hash・schema 異常を不在へ落とす経路は見つからなかった (`p3_b4_floor_artifact_issuer.py:1141-1174`)。material report も例外を握り潰さず失敗へ写す (`p3_b4_material_report.py:211-226`)。
- 4 状態射影は実装どおりで、権威あり × assembly 拒否は `floor_argument=null`、evaluator 未呼出しである (`p3_b4_material_report.py:244-278`, `:1001-1003`)。4 組すべてが parameterized test にある (`test_p3_b4_material_report.py:838-905`)。
- 不在時 golden は JSON/Markdown とも固定 digest 定数であり、変更後 renderer を expected 側に使っていない (`test_p3_b4_material_report.py:55-61`, `:827-832`)。
- M2〜M11では、M1以外に別の無関係な層が先に赤を出す変異帰属破れを反証できなかった。M9 の内部 projection assert は同じ D-4 性質の検査なので別理由とは数えない。
- material-report の CLI/public builder に floor 引数、環境変数、floor 既定値はない。例外は所見 3 の raw public loader である。
- pytest は指示どおり実行していない。

## 総括

- `-0.0` を拒否するか bit 比較を導入し、producer 不可能な signed-zero summary を閉じる。
- summary-bound spec を少なくとも既存 producer の閉 schemaへ束縛し、synthetic specからの権威発行を止める。
- caller 指定・digest 任意・source 未照合の public loader 面を権威経路から外す。
- exact test を元 summary の値に対する独立 oracleへ直し、M1を issuer 単体へ再照準する。