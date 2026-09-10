# 段 6 裁定 — レビュー A / B の所見

親が両レビューを real / refuted と scope 内 / 外へ裁定した結果。fix 子はこの文書を正本とする。

## 裁定表

|#|所見|判定|扱い|
|---|---|---|---|
|A-1|`-0.0` が値域検査と bit 一致比較をすり抜ける|**real (親が数値で追試)**|**must-fix**|
|A-2|summary が束縛した spec を producer の閉 schema で検証していない|**real**|**must-fix**|
|A-3|public loader に caller 自己申告経路が残る (digest 省略可)|**real**|**must-fix (限定)**|
|A-4|exact 化 test の oracle が issuer 自身の出力。M1 の帰属が別層へ落ちる|**real**|**must-fix**|
|A-5|到達不能な assert|**real (nit)**|**採用 (削除)**|
|B-1|source の非保証を捨てたまま `checked` へ昇格している|**real**|**must-fix**|
|B-2|未裁定 wire token `not_fixed_by_floor_presence` を新設した|**real**|**must-fix (別解で)**|
|B-3|段 4 が明示しない一般 hardening 群|**real な指摘だが scope 内と裁定**|**変更しない (理由は下記)**|

**refuted はゼロ。**

## 親が数値で追試した点 (A-1)

`-0.0 < 0.0` は `False`、`-0.0 == 0.0` は `True`。したがって値域検査も bit 一致比較も通る。
producer は `abs(gain_1 - gain_2)` を通すので必ず `+0.0` を出し、`-0.0` は **producer が生成し得ない**。
`math.copysign(1.0, x) < 0` で判別できる。

## fix (すべて must-fix)

### F-1. `-0.0` を拒否する (A-1)

`candidate_floor`、`upper`、層別 `upper`、`difference`、`gain_1`、`gain_2`、`values` の各 float に対し、
**値が 0 で符号が負のものを拒否する**。判別は `math.copysign(1.0, x) < 0` で行う。
再導出比較は `==` に加えて**符号 bit の一致**も要求する (`math.copysign` の一致で足りる。
`struct` で bit を取り出す必要はない)。

### F-2. spec を producer の閉 schema で検証する (A-2)

identity の導出元 spec を、`.get()` の拾い読みでなく **`floor_pair_driver` の既存 spec loader で
parse する**。producer が受理しない spec からは発行しない。**新しい validator を書かない** —
producer の loader を呼ぶ。test fixture の spec も producer が受理する形へ直す。

`floor_pair_driver` を import することで
`orchestrator/tests/test_official_perf_closure.py` の exact inventory 2 本
(`test_official_perf_surface_inventory_is_exact`、
`test_outer_perf_file_and_added_guard_inventory_is_exact`) が赤になる可能性がある。
**新 module に perf の tracked call 名を書かないこと。** この 2 本を必ず確認して報告する。

### F-3. loader の digest を必須にする (A-3)

`load_authoritative_floor()` の `expected_sha256` の既定値 `None` を**削除し必須引数にする**。
digest なしで権威成果物を読める経路を無くす。

`source_summary` の参照先の実在照合は**しない** (D1696 が人手責任に残した面へ踏み込むため)。
代わりに F-4 で「照合していない」ことを正直に書く。

### F-4. `checked` の主張を実態へ狭める (B-1)

- 材料レポートの `checked` から `authoritative_floor_artifact` を**外すか**、
  実際に検査している内容 (§5 の grammar・file の実在・内容 sha256・schema・exact ratio の整合) だけを
  指す名前へ**狭める**。どちらでもよいが、**検査していないことを検査済みと読める表現を残さない**。
- 権威成果物の非保証欄へ、**source summary の参照先を実在照合していない**ことを逐語で足す。
- summary が持つ `proof_limitations` の items を、権威成果物の非保証欄へ**そのまま転記する**
  (要約・省略をしない)。upstream の非保証を捨てない。

### F-5. 未裁定 token をやめる (B-2)

present 時の `report_scope.expected_analysis_verdict` と `expected_analysis_reason` は、
新しい文字列語彙を発明せず **`null`** にする。exact contract の test はそのまま残す。
理由: floor が present なら verdict は floor の不在で固定されず、データに依存する。
「固定されない」を表すのに新しい語彙は要らない。**schema version は v1 のまま据え置く。**

### F-6. exact 化 test の oracle を独立させる (A-4)

expected な ratio と hex を、issuer の戻り値からでなく **fixture の JSON に書いた元の値から**
独立に計算する。issuer が値を 1 ULP 動かして 3 つの field へ同じ値を入れても落ちる形にする。

### F-7. 到達不能 assert を消す (A-5)

`assert summary.identity is not None` は直前の呼出しが同じ否定条件で必ず例外にするため、
偽で到達する入力が無い。**削除する。** 恒真な保証を残さない (規律 7)。

## B-3 を変更しない理由

段 4 が明示していない hardening が入っているのは事実だが、次の理由で scope 内と裁定する。

- **canonical JSON・duplicate key・非有限の拒否**: 再導出による自己整合検査 (§D-2) が意味を持つ前提。
  非 canonical JSON の重複 key は、検査した値と採用する値を別にできる。
- **summary 全体の閉 schema**: producer 自身が `_exact_object` で同じ形を採る。producer の形を写しており、
  新しい判定基準を持ち込んでいない。
- **path の canonical 化・symlink 拒否・regular file 要求**: create-only 発行に必要。
  同型の拒否は D1378 が材料レポートの writer について既に採っている。
- **tempfile + fsync + hard-link**: create-only の発行そのもの。
- **材料レポートの二重 projection 検査**: §D-4 が exact な射影を要求している。ただし F-7 の
  到達不能 assert だけは削る。

いずれも **D1696 が人手責任に残した 9 項目 (exact 2 window・n・24 時間・校正・セル集合・journal・
JSONL・finalize 束縛・成果物名の意味的一致) には踏み込んでいない。** 実際、レビュー A/B とも
「9 項目そのものは検査していない」と確認している。

## 変異事前登録の更新 (DW-M01、fix 前)

段 4 §F の M1〜M11 に加え、fix 対象へ次を足す。M1 は帰属が別層へ落ちるため**登録から外す**
(段 4 §F の単一理由性の注記どおり。F-6 の独立 oracle が代わりに値改変を捕まえる)。

|ID|位置|変異|期待|
|---|---|---|---|
|M12|issuer の `-0.0` 拒否|符号検査を落とす|KILLED (`-0.0` summary の拒否 test)|
|M13|issuer の spec 検証|producer loader 呼出しを `.get()` の拾い読みへ戻す|KILLED (producer 不受理 spec の拒否 test)|
|M14|issuer の loader|`expected_sha256` に既定値 `None` を戻す|KILLED (digest 必須 test)|
|M15|issuer の非保証|source summary の未照合の逐語を消す|KILLED (非保証逐語 test)|
|M16|issuer の非保証|summary の `proof_limitations` の転記を落とす|KILLED (転記 test)|
|M17|material report|present 時の `expected_analysis_*` を `null` 以外にする|KILLED (exact contract test)|
|M18|issuer の exact 化|`candidate_floor` を 1 ULP 動かして 3 field へ同じ値を入れる|KILLED (F-6 の独立 oracle test)|

## 裁定パッケージへの追加 (ユーザーへ返す)

段 4 §E の 5 件に次を足す。

6. **事前登録 §11 の事実記述が本 commit 後に偽になる。** §11 は「材料レポートの生成器は本書を読まず、
   評価器へ無条件に floor 不在を渡す」と書くが、本 commit 以降は §5 を読んで floor を渡す。
   段 4 §C が doc 非改変を裁定しているため本 wave では直さない。
   **推奨: §5 記入 wave ([T-2140]) が §11 を追記で訂正する。**
7. **summary の関係検査の穴。** `window_artifacts` の重複、campaign strata の重複、
   `planned` と `retained_sample_count` の不整合は検査していない。これは D1696 が人手責任に
   残した面であり、本 wave では足さない。**再訪条件 = 人手の確認が実際に見落としたとき (D1696 の逐語)。**
