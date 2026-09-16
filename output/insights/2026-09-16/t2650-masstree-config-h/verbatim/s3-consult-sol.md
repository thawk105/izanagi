## 規律 2 への抵触の有無

- **主張:** 提案の配線だけなら、規律 2 の緩和は認められない。ただし「red→green が起きない」という意味での受理集合不変は誤り。
  **根拠:** `condition_meaning_gate.py:2234–2248` は要求 macro・値・companion を照合し、`:2646–2661` は依存 closure 一致と前処理 bytes の差を要求する。無効値側は stock との一致等を要求する（`:2663–2704`）。依存引数は同じ captured input から configure へ入る（`:1697–1710`）。これらの判定式は変更されない。
  **成果物影響:** `config.h` 不在による検査不能から、実際に supply 判定を行える状態へ変わる。macro 不在・値違い・効果なしを無条件に green にする変更ではない。新規走行の台帳には従来得られなかった green が記録され得る。
  **重大度:** 中。「判定規則は不変、依存欠落による検査不能を解消」と記述すべき。

- **主張:** `config.h` 欠落と確認された red は、要求 define の供給失敗を証明していない。
  **根拠:** `external/ccbench/cmake/ThirdParty.cmake:66–85` は build 時に生成する `config.h` の所在を include path にする。一方 gate は configure 後に前処理する（`condition_meaning_gate.py:1703–1715`, `:2268–2271`）。
  **成果物影響:** この環境要因の解消は正当。ただし既存の `preprocess-failed` 全件を同じ原因と扱うことや、解消後の green を未実測で保証することはできない。
  **重大度:** 中、原因・完了主張の範囲に関する指摘。

## 負例が恒真になる危険

- **主張:** 床値の配置は罠の条件を満たす。ただし **plan の argv 一致テスト自体は、その罠に落ちない**。
  **根拠:** `s8b_floor_campaign.py:2629–2632` は source を `<base>/<name>-src` とする。採用予定 fixture も同形（`test_s8b_floor_campaign.py:3712–3715`）。しかし `plan.md:78–97` は configure を実行せず argv を捕捉し、token の値・本数・名前を比較する。override を一本削れば、この assert は失敗する。
  **成果物影響:** 配線欠落は検出できる。一方、このテストの成功から「CMake が override を実際に使用した」「前処理が成功した」とは主張できない。
  **重大度:** 中、検証が証明する範囲の限定。

- **主張:** 実 CMake の成功／失敗を使う負例なら、base と source の分離が必要。
  **根拠:** 同じ罠は `docs/decisions.md:57660` の D1920 に明記されている。
  **成果物影響:** 歯が立つ形は、既存案の argv 捕捉で **base・各 SOURCE_DIR を一本ずつ落とす変異**を落とすこと。実 CMake まで検証する場合は、テスト内で空の base と別 root の source を使い、ネットワーク取得へ逃げない条件で override 欠落を検出する。床値本体の配置変更は不要。
  **重大度:** 中。configure 成功だけを負例の証拠にすると配線欠落を見逃す。

## 凍結 bytes と受理集合への波及

- **主張:** argv の延長による構造検査・過去 record 互換の破壊は見つからない。
  **根拠:** `condition_meaning_gate.py:3555–3559` は argv と CMake path の束縛を検査し、固定 token 数を要求しない。`:3718–3726` の位置検査も維持される。ただしこれは **root-location-only 分岐限定**であり、brief は一般検査のように説明している。
  **成果物影響:** 過去 record に新 token を要求しないため、既存 record がこの変更だけで失効することはない。新 record の argv・証拠内容は変わり得る。
  **重大度:** 低、brief の根拠説明の訂正。

- **主張:** 提案どおりの二ファイル変更に、凍結成果物や既存 golden の更新は必要ない。
  **根拠:** `test_frozen_artifacts.py:41–89` の manifest に変更対象二ファイルや gate record はない。床値 golden は固定の計測入力から floor 値を検査する（`test_s8b_floor_campaign.py:11064–11101`）。schedule golden も別の検査である（`:7114`）。
  **成果物影響:** 凍結済み bytes・既存 floor 期待値はそのまま。将来の走行が先へ進むことで新しい材料が得られることと、既存成果物の書換えは区別される。
  **重大度:** 破壊所見なし。テストは未実行。

## 親 brief の (P1-a)〜(P1-d) の判定

- **P1-a — real。ただし「5定義」は床値では4本。**  
  **主張:** 既存生成器の再利用であり、新規の一般化ではない。  
  **根拠:** `p3_s4_loop.py:346–376` は prefix の有無を既に扱う。  
  **成果物影響:** 新たな schema・生成規則は不要。床値に5本を要求すると正しい配線を誤拒否する。  
  **重大度:** 低。

- **P1-b — real、今回の実装境界について。ただし gate の明文免除ではない。**  
  **主張:** D424 の理由は非 sort の cache identity・binary 参照の維持であり、今回の gate 引数追加はその境界を変更しない。  
  **根拠:** `docs/decisions.md:17628–17662`。現行 build の base/source 注入は `s8b_floor_campaign.py:4434–4473` で sort 限定。gate の引数搬送とは別経路である。  
  **成果物影響:** 非 sort build への追加注入は生じない。ただし「D424 に gate の例外が明記されている」とは書けない。  
  **重大度:** 低、裁定の引用精度。

- **P1-c — real。**  
  **主張:** repo 内の凍結 bytes を変更する必要はない。  
  **根拠:** 上記 manifest と validator。  
  **成果物影響:** 凍結成果物は維持されるが、新規 gate record の bytes まで不変という意味ではない。  
  **重大度:** 破壊所見なし。

- **P1-d — refuted、生死確認を既存実測だけで継承できるという部分。**  
  **主張:** 既存の失敗実測は修正後の成功を証明しない。また `find_package(... REQUIRED)` は login node に依存が無い証明ではない。  
  **根拠:** `brief.md:36–38`、`plan.md:78–81`。提案テストは configure 起動前で停止する。  
  **成果物影響:** 配線テスト合格だけで「cell build 段を越えた」と完了報告すると、未取得の床値材料を取得可能と誤認させる。実機再投入を scope 外とすること自体には異論なし。  
  **重大度:** 中、完了報告の証拠不足。

## 親の実測とその一般化への反証

- **主張:** 現行 worktree の「12 cell、sort_best 2件」だけから、過去三走行で prebuild が実行されたとは結論できない。
  **根拠:** 実行条件は `production_floor_path` と sort cell の存在（`s8b_floor_campaign.py:4259–4260`）。実行前には toolchain・staging 等の失敗点がある。現行コードには freeze と protocol の hash 照合（`:7393–7402`）、official の固定 freeze 照合（`:5238–5243`）があるが、過去走行が同じコード・入力でそこを通った証拠とは別。
  **成果物影響:** 一般化を誤ると、prebuild 自体が成立しなかった走行まで今回の配線だけで修復できると誤判定する。
  **重大度:** 中。

確認すべき既存証拠は、各走行の実行 revision、解決済み protocol の freeze path/hash、実際の freeze bytes、launch certificate、および `sort-swo-oracle-dependency.json`。最後のファイルは prebuild と依存検証後に発行される（`s8b_floor_campaign.py:4290–4318`）。これらの走行証拠は今回未照合。

## plan の事実誤認 (あれば)

- **主張:** 「明示 token は4本」は正しい。「prefix は供給されない」まで一般化すると誤り。
  **根拠:** 床値の `prepare_kwargs` に prefix はない（`s8b_floor_campaign.py:3414–3425`）。prebuild は明示 prefix がある場合だけ token を生成する（`buildcache.py:2051–2072`）。一方 official wrapper は `CMAKE_PREFIX_PATH` を export し、既存 receipt に記録する（`tools/pegasus/floor_campaign.sh:1148–1163`）。gate の subprocess は環境を継承する（`condition_meaning_gate.py:1588–1597`）。build 側も ambient prefix を読む（`buildcache.py:2618–2626`）。
  **成果物影響:** 4本の assert は維持してよい。ただしその一致は gflags/glog の実効環境まで検証しない。環境 prefix があっても、明示 argv が5本になるわけではない。
  **重大度:** 低、証明範囲の補足。

## 総括

二ファイルの配線案を止める正しさ・凍結互換上の欠陥は、静的検査では見つからなかった。修正が必要なのは、受理集合不変の表現、過去走行への一般化、配線テストを生死確認と扱う主張である。

argv 欠落の変異は既存案の assert で検出できる。実 CMake の負例を行う場合だけ base/source の分離が必要。実装・ファイル変更・テスト実行は行っていない。