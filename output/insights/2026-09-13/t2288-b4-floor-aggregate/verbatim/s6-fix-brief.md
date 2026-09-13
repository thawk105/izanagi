# 段 6 fix 裁定 — [T-2288]

親が段 6 の 2 レビューを裁定した結果である。ここに書いた 3 件だけを閉じよ。他は変更しない。

## must-fix 1 — 契約にない受理条件を除く (レビュー A 所見 1、real)

**判定: real。採用。**

現実装は、**異なる spec の間**でも window artifact path の非共有を要求している
(`aggregate_output_reuse_error`)。各 spec 内の出力 path 相異は `floor_pair_driver` の既存条件だが、
**spec をまたぐ非共有は追補 (b)(c) のどこにも無い要求**である。期待 spec 列と全 summary の閉包が
一致する入力でも発行と v2 読込を拒否するので、集約成果物の受理集合が契約より狭い。

**対応: spec をまたぐ出力 path 非共有 gate を除去せよ。**
維持するもの — 各 spec 内の相異検査 (既存 driver 側)、summary path の重複拒否、
期待 spec と summary の一対一対応、window 閉包の一致。

## must-fix 2 — 公開経路の正例と公開 API 負例を作る (レビュー A 所見 2 / B 所見 1、real)

**判定: real。採用。** 段 4 の変異事前登録が要求した正例そのものが未作成である。

現状の追加テストは、`FloorPairSpec` や検証済み summary オブジェクトを直接組み立てる**内部関数単位**に
留まる。そのため、期待 spec に対応する summary が欠落したときの検査や、再構成結果との比較を
**削除しても、追加テストはその変更点へ到達しない**。機構が実装された証拠になっていない。

**対応:**

1. **正例を 1 つ作る。** 3 spec (workload 別)・各 spec ちょうど 2 窓・全セル被覆・許容内の欠測を持つ
   合成入力を、**公開 API `issue_aggregate_authoritative_floor` で発行**し、
   **`load_authoritative_floor` と `resolve_preregistered_authoritative_floor` を通す**ところまでを
   1 本のテストで通せ。stub や monkeypatch で本体を迂回しない。
   既存の合成 helper (`orchestrator/tests/test_floor_pair_driver.py` の入力生成と
   本 file の既存 helper) を土台にしてよい。
   **材料レポートまで届ける経路**は、既存 test が使う組立経路でそのまま届くなら加えよ。
   合成 repo では届かせられないと判断したら、**その理由を報告に書いて、そこで止めよ。**
   作り話をしない。届かない部分を「届いた」と書かない。
2. **上の正例を土台に、公開 API を通る負例を作れ。** 最低限、次の 5 つ。
   いずれも無関係な hash・schema・自己整合は正しく更新し、狙った検査まで到達させよ。
   各テストで**停止した error code を assert** せよ。
   - 期待 spec 列を固定したまま、対応する summary を 1 件落とす。
   - 期待 spec 列と summary を同時に 1 組落とす (閉包の循環が無いことを示す)。
   - 発行済み成果物の `floor_exact` を非最大値へ替え、`source_float_hex` と外側 hash も整合させる。
   - 発行済み成果物から非最大入力の出所または非保証を 1 件落とし、外側 hash も整合させる。
   - 単体としては有効な入力のうち 1 件だけ identity (env_tag / protocol / threads のいずれか) を
     変え、公開 API が集約全体を拒否することを示す。
3. 正例が通ることを実走で確かめられない場合は、その旨を「未実走」と明記せよ。

## nit 1 — 恒真な分岐を残さない (レビュー A 所見 3)

`aggregate_empty_stratum_error` の `retain_count == 0` 分岐は、閉じた層集合の一致を通った後では
成立しない、と指摘されている。**まず自分で到達可能性を判定せよ。**

- 到達不能なら**除去せよ**。発火しない assert を保証として残さない。
- 到達可能なら、**その分岐へ実際に到達する負例を 1 つ足せ**。どの入力で到達するかを報告に書け。

どちらにするかは、コードを読んで自分で決めてよい。判定の根拠を報告に書くこと。

## refuted (対応不要)

- **レビュー A 所見 4 / B 所見 2 (規範追補が差分に無い)。** これは refuted である。
  追補は**親が wave 側 worktree に既に書いており**、この実装 worktree に無いのは設計どおりである
  (実装子は docs を編集しない)。追補の逐語は射影済みの file で読める。**docs を編集しないこと。**
- **レビュー A 所見 5。** 実装子の報告が限界を正しく限定していたので、対応不要。

## 変えてはならないもの

- `issue_authoritative_floor` / `load_floor_pair_summary` / `_authority_value` / publisher の本文、
  v1 定数、v1 成果物の bytes と命名。
- 既存テスト関数・fixture・decorator・期待値 (レビュー B が byte 単位で無変更を確認済み)。
- CLI の旧省略形と反復時の最終値採用 (レビュー B が受理集合の縮小ゼロを確認済み)。
- n = 62 と 24 時間分離を機械検査しないこと (追補 (f))。
