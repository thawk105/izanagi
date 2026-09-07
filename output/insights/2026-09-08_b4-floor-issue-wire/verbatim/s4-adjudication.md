# 段 4 裁定とプラン v2 — B-4 権威 floor 成果物の発行と配線

親が両レンズを real / refuted と scope 内 / 外へ裁定した結果。段 5 実装子はこの文書をプランの正本とする。

## A. 裁定の要点 (先に読む)

- **丸めをやめる。** `math.nextafter` を使わない。floor は採用された `candidate_floor` の値を
  **1 bit も変えず** `as_integer_ratio()` で exact ratio にする。
- **信頼せず再導出する。** summary の `derivation[].samples[].session_medians` から producer と
  **同じ float 演算で** D と層別 upper と最終 upper を再計算し、記録値と **bit 完全一致**を要求する。
  一致しなければ発行しない。
- **採用記録 (adoption record) を新設しない。** 権威の出所は事前登録 §5 の floor 行だけとする。
- **identity は caller に申告させない。** summary が sha256 で束縛した spec から導出する。
  導出できない要素があれば発行を拒否し、欠けている要素名を返す。
- **A と B は 1 commit にまとめる。** 分割着地を不可能にする。

## B. レンズ所見の裁定

|#|所見|判定|扱い|
|---|---|---|---|
|A-1 / B-1|現行 v2 の D 意味は D1699 に不適合|**real**|**scope 外**。版 pin を単一定数にし、非保証へ明記して裁定パッケージへ返す (下記 §E-1)|
|A-2|1 ULP 切上げでも exact D を覆わない|**real (親が数値で追試して確認)**|**採用 (向きを変えて)**。丸め自体を廃止する。exact 再導出への差し替えは採らない (§E-2)|
|A-3|`candidate_floor` と derivation を照合していない|**real**|**採用・must-fix**。再導出 bit 一致を要求する|
|A-4 / B-2|採用記録が実在の D へ束縛されていない|**real**|**採用**。採用記録という入力そのものを廃止する|
|A-5|不在時 bytes の oracle が変更後コード自身で変異帰属が立たない|**real**|**採用・must-fix**。変更前の固定 golden を使う|
|A-6|権威あり × assembly 拒否 の意味が未定義|**real**|**採用・must-fix**。下記 §D-4 の射影で固定する|
|A-7|brief の行番号 `:243` は `:242` の誤り。「verdict は 1 種類」は assembly 成功経路に限る|**real (nit)**|**採用**。記録時に訂正する|
|B-3|A/B 分割は分割着地を許し未接続 interface を再現する|**real**|**採用**。1 commit にまとめる|
|B-4|`nextafter` は未裁定の値改変であり `as_integer_ratio` で足りる|**real**|**採用**。A-2 と併せて丸め廃止|
|B-5|§5 の grammar はコード側の新規発明|**real**|**採用 (限定)**。表内の既存記法に合わせ、裁定パッケージで §5 記入者へ渡す|

**refuted はゼロ。** 両レンズが「反証できなかった点」に挙げた項目 (closure tuple 不変、
批准節 pin 不変、caller floor 注入口なし、schema の閉集合性、A/B の textual 非重複) は親も追認した。

## C. 変更しない面 (段 2 プランから継承)

`p3_b4_analysis_contract.py` 全体、`p3_b4_analysis_path.py` の `_SOURCE_CLOSURE_PATHS`、
`p3_b4_analysis_prereg_consumer.py` の `_CLOSURE_PATHS`、事前登録 doc 全体、
`floor_pair_driver.py` 全体、`p3_b4_material_report.py:48-49` の既存 `SCHEMA_VERSION` と
`GENERATOR_IDENTITY`。新 module を分析 5 module の closure へ足さない。

## D. プラン v2 (段 2 プランからの差分だけを書く。書いていない部分は段 2 プランのまま)

### D-1. exact 化 — 丸めを廃止する

段 2 プランの `ROUNDING_ID` と `math.nextafter` を **削除**する。代わりに:

- `floor_exact = Fraction(*candidate_floor.as_integer_ratio())` とし、値を変えない。
- 値域検査は `0 <= floor_exact < 1` を exact に行う (`candidate_floor == 0.0` は正規に受理する。
  現行 producer は 0.0 を生成しうる)。
- 権威成果物には `source_float_hex = candidate_floor.hex()` と `floor_exact = [num, den]` を両方置く。

**この向きが規律 2 に反しない理由。** 値を変えていないので、緩めても厳しくもしていない。
A-2 が示した「binary64 の中間丸めにより、記録された float D が同じ入力の exact D より小さいことがある」
という限界は**残る**。これは producer の演算の性質であり、consumer 側で別の統計量へ差し替えると
D1383 (AI が値を既成事実にしない) と D1699 (D の式は実走前に凍結する) の両方に触れる。
したがって**差し替えず、権威成果物の非保証欄へ逐語で明記し、裁定パッケージへ返す**。

### D-2. 自己整合の再導出 (A-3)

issuer は `derivation[0]["samples"]` の各 `session_medians` から、`floor_pair_driver` と
**同じ float 演算順序**で `gain_1` / `gain_2` / `difference` を再計算し、記録値と `==` で一致することを要求する。
続いて層別 `upper` (層内 max)、最終 `upper` (層間 max) も再計算し一致を要求する。
最後に top-level `upper` と `candidate_floor` の一致、および `type(upper) is float` を要求する
(`False == 0.0` を通さないため、bool を明示的に拒否する)。1 つでも外れたら発行しない。

これは**新しい統計量の追加ではなく、記録された計算の再導出**である (D1531 が既に採る形)。

### D-3. identity の導出 (A-4 / B-2)

`--adoption-record` を **廃止**する。CLI 入力は `--repo-root` と `--summary` だけとする。
identity は次の連鎖から導出する。caller の申告を一切受けない。

1. summary の `spec_relpath` / `spec_sha256` で spec を解決し、bytes の sha256 を照合する。
2. spec から `environment.env_tag`、`cells[].perf_config.threads`、`cells[].perf_config.workload` を取る。
3. `campaign 識別子` は summary の `campaigns[]` から取る。
4. `protocol` は spec の `artifacts[].build_receipt` が指す受領証から取る。

**親が実測した事実: `protocol` という field は spec の dataclass 群に存在しない**
(`floor_pair_driver.py:150-200`)。したがって 4 が導出できない可能性が高い。
その場合 issuer は **発行を拒否し、欠けている要素名を返す**。既定値で埋めない。caller に聞かない。
実装子はこの連鎖を実測し、`protocol` がどこから導出できるか / できないかを結論として報告する。
**導出できないことが確定したら、それは欠陥ではなく裁定パッケージ項目である** (§E-3)。

### D-4. 権威あり × assembly 拒否 の射影 (A-6)

resolver は evaluator 呼出しより**前**に走らせる。射影は次で固定する。

|状態|`floor.availability`|`analysis.status`|`analysis.floor_argument`|
|---|---|---|---|
|権威なし・assembly 成功|`absent`|`evaluated`|`null`|
|権威なし・assembly 拒否|`absent`|`not_evaluated`|`null`|
|権威あり・assembly 成功|`present`|`evaluated`|`[num, den]`|
|権威あり・assembly 拒否|`present`|`not_evaluated`|**`null`**|

最後の行が要点である。**評価器を呼んでいない以上「渡した引数」を書いてはならない。**
floor は present だが引数は渡っていない、という状態を正直に射影する。この 4 状態すべてに test を置く。

### D-5. 不在時 bytes の独立 golden (A-5)

`_build_report_value()` / `_render_markdown()` を oracle にしない。段 5 実装子は、**変更を入れる前の
現行コード**で正規の JSON bytes と Markdown bytes を 1 度生成し、その **sha256 を test 内の定数**として
焼き込む。変更後の public 経路が同じ digest を出すことを検査する。両辺に同じ変異を入れても
定数は動かないので変異帰属が成立する。

### D-6. §5 の grammar (B-5)

floor 行の non-sentinel 値の grammar は、**同じ表の既記入行と同じ `<key>=<value>; ` 形式**に合わせる。

`artifact_path=<repo 相対 path>; sha256=<64 桁小文字 hex>`

sentinel は逐語 `未記入` の完全一致だけとする。sentinel なら不在。それ以外で grammar に合わない、
file が無い、hash が合わない、schema が合わない場合は **fail-closed** とし、不在へ読み替えない。
この grammar は §5 記入者への interface なので、裁定パッケージで明示して返す (§E-4)。

### D-7. 版 pin (A-1 / B-1)

受理する producer schema は **単一の定数 1 値**とし、集合や範囲や「以上」を作らない。
現時点の値は `floor-pair-summary/v2`。定数が 1 値であることを検査する test を置く。
権威成果物と材料レポートの非保証欄に、**その版が D1699 適合をまだ満たしていない**ことを明記する。

### D-8. 単一変更単位 (B-3)

段 5 は A (issuer) と B (配線) の 2 子で並列実装するが、**段 7 で 1 commit にまとめる**。
A だけ / B だけが main へ着地する経路を作らない。

## E. 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. **v2 の D 意味が D1699 に不適合。** 本 wave は版 pin を単一定数にして非保証へ明記したが、
   B-4 の床値を実際に発行する前に、pin を D1699 適合 producer の版へ進める必要がある。
   その producer は [T-2369] wave が実装中。**推奨: T-2369 着地後に pin を 1 行進める follow-up。**
2. **binary64 の中間丸めにより、記録された float D は同じ入力の exact D より小さいことがある。**
   親が数値で確認した実例: `candidate_1=0.10000000000000003, candidate_2=reference=0.1` のとき
   driver の D は `2.220446049250313e-16`、同じ入力を exact 有理数で計算した D は
   `2.7755575615628914e-16` で、差は `5.55e-17`。floor が真の D より小さいと、境界の block が
   tie から勝敗へ変わりうる。**択一: (a) 現状維持 + 非保証明記 (本 wave の採用)、
   (b) D の式を exact 有理数で凍結し直す (D1699 の凍結作業に含める)。推奨 (b) を T-2369 側で。**
   実効上の大きさは相対 1e-16 で、床値の典型値 (3% 級) の 14 桁下である。
3. **D1641 の命名 5 要素のうち `protocol` が producer の凍結 spec に存在しない。**
   親の実測では `floor_pair_driver.py` の spec dataclass 群に `protocol` field が無い。
   段 5 実装子が build receipt からの導出可否を確定して報告する。導出できない場合、
   **択一: (a) spec に `protocol` を足す (T-2369 の凍結作業に含める)、(b) D1641 の命名要素を
   4 要素へ訂正する追記。推奨 (a)。**
4. **§5 floor 行の記入 grammar** を D-6 で固定した。§5 記入者 ([T-2140] 側) はこの記法で書く必要がある。
5. [T-2289] の closure receipt 接続は D1530 どおり本 wave へ同梱しない。

## F. 変異事前登録 (DW-M01、実装前登録)

各変異は位置と、赤理由が 1 つに絞れることを実装後に確認する。絞れないものは登録から外す。

|ID|位置|変異|期待|
|---|---|---|---|
|M1|issuer の exact 化|`Fraction(*x.as_integer_ratio())` を `x` (float) のまま返す|KILLED (契約が float を拒否する経路まで到達する test)|
|M2|issuer の再導出|`difference` の再計算結果との比較を落とす|KILLED (自己矛盾 summary の拒否 test)|
|M3|issuer の再導出|`type(upper) is float` の bool 拒否を落とす|KILLED (`upper=False` の拒否 test)|
|M4|issuer の版 pin|pin 定数を別の値にする|KILLED (版 pin test)|
|M5|resolver|grammar 不一致を不在として返す|KILLED (fail-closed test)|
|M6|resolver|sha256 照合を落とす|KILLED (改竄 artifact の拒否 test)|
|M7|material report|権威解決の例外を握って `floor=None` へ落とす|KILLED (非 fallback test)|
|M8|material report|不在経路の射影を 1 field 変える|KILLED (固定 golden digest test)|
|M9|material report|権威あり × assembly 拒否 で `floor_argument` に ratio を書く|KILLED (D-4 の 4 状態 test)|
|M10|issuer の identity|caller 申告の identity を受理する経路を足す|KILLED (identity 導出 test)|
|M11|issuer の値域|`floor_exact < 1` を `<= 1` に緩める|KILLED (値域 test)|

**単一理由性の注意 (F820)。** M1 は契約側の `floor_domain_error` が先に出るため、issuer の型検査と
契約の拒否のどちらが赤にしたか区別がつかない恐れがある。実装後、issuer 単体の test で
赤理由が 1 つに絞れることを確認し、絞れなければ M1 を登録から外して実効 gate へ再照準する。
