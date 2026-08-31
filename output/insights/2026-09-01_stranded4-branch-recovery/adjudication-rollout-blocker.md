# 裁定 — 消えた T-181 原本 rollout に束縛された検査の扱い

- authority: none (裁定の正本は decisions、本書は根拠の集約)
- 判定日: 2026-09-01
- base main: `24014bdb2` / wave tip: `66ca22483`
- 逐語: `verbatim/s3-consult-a-sol.md` (レンズ A)、`verbatim/s3-consult-b-luna.md` (レンズ B)

ユーザー指示「codex と相談して決めて」に従い、read-only codex 2 レンズへ並列で相談した。
両レンズとも `check_codex_output.py` rc=0。

## 結論

**案 1 を採る。** T-181 の凍結 provenance literal は 1 bit も変えず、失われたのは
「原本を読んで golden を裏取りする」検査の**実行可能性だけ**である、という形にする。
素の skip にはせず、既存の明示 hold と同じ形で `unavailable` を機械可読に記録する。

## 親が段 1 で書いた推奨は誤りだった

親は当初「案 B: 現存する rollout へ pin を張り替える」を推奨した。**これは撤回する。**
両レンズが独立に不採用とし、親自身の調査も同じ結論に達した。

- レンズ A: 「規律 7 の第一 bullet 単独では案 3 を禁じないが、案 3 の in-place 上書きは
  規律 7 全体に反する」。親が「再現不能でも事実は変わらない」だけを禁止根拠にしたのは
  **拡大解釈**であり、実際に効くのは「記録はやめない」と「過去の判定は追記でのみ訂正する」の
  2 条である。親の結論は正しく、親の理由づけは部分的に誤っていた。
- レンズ B: POS hash を変えると manifest 全体の SHA が変わり、33 production 関数の既定 manifest と
  prompt / launch / collect / schedule / material / packet / verdict / aggregate の
  `task_manifest_sha256` が連鎖して変わる。既存 digest を持つ成果物は
  `_require_task_manifest_sha256` に拒否される。さらに `snapshot.numstat` は rollout から
  導出されない別の frozen literal である。**張り替えは局所修正ではなく別測定である。**

## 実測で確定した被害範囲 (レンズ B の推測を上書きする)

レンズ B は「session root の依存閉包は 24 test 関数」を BLOCKER として挙げ、fixture 経由の
21 関数も壊れうると**推測**した。親が実測して確かめた結果、**これは起きない。**

- 受入全走の failure digest は `failures=5 failed=4 errors=1 selected=5 omitted_failures=0`。
  切り捨てゼロで 5 件が全数である。
- fixture `benchmark_snapshots` を使う代表 1 本 (`test_parent_numstat_controls_remain_pinned`) を
  焦点走したところ **skipped** だった。skip の理由は原本の不在ではなく、
  既存の `IZANAGI_GROWTH_HOLD_V1` (`hold_axis=output_artifacts`、
  `ruling=2026-08-12 rulings 第 3 束`、`release_condition=explicit-user-command-only`) である。
- したがって被害は **2 関数 4 item** (`test_prompt_replacement_count_zero_expected_and_excess`
  の 3 parametrize と `test_real_rollout_collector_golden_is_source_bound`) に限られる。
  この 2 関数だけが、held の兄弟と違って不在時の guard を持たない。

依存閉包が 2 関数より広いというレンズ B の指摘自体は正しく、将来 hold が解除されれば
fixture 側も同じ原本を要求する。この点は案 1 の設計に織り込む。

## 実測で見つかった先例 (レンズ B の「先例なし」を上書きする)

レンズ B は「案 1 にそのまま使える既存の環境依存 hold は存在しない」を BLOCKER とした。
**契約の批判としては正しいが、形の先例は同じ file 内で現に動いていた。**

上記の skip reason は、次をすべて備えた機械可読 JSON として stderr へ出る。

- ユーザー裁定 ID (`ruling`)
- exact node id (`node_id`)
- 解除条件 (`release_condition: explicit-user-command-only`)
- 正しさ gate に触るかの明示 (`correctness_gate: true`)
- **barrier nodes の名指し** — hold されたものの代わりに何が走り続けるかを
  `test_snapshot_submodule_object_store_is_recursive` と
  `test_task_manifest_binds_frozen_provenance_to_literal_values` として書いている

レンズ B の指摘どおり `hold_axis` は repo growth の 5 種に限られ、`barrier_nodes` は
`reason` 内の advisory であって独立 field ではない。**新しい axis と field 契約の追加が要る。**
ただし機構をゼロから設計する必要はなく、この形を拡張すればよい。

## 実装すべき内容

1. **`TASK_MANIFEST` の T-181 literal は不変。** POS の session id、`rollout_sha256`、
   `prompt_source.sha256`、`snapshot.numstat` を 1 bit も変えない。
2. **原本を読む 2 関数を明示 hold にする。** 素の `pytest.skip` / `skipif` にしない
   (両レンズが案 4 として不採用、F9 / F697 の同型)。ユーザー裁定 ID、exact node id、
   `release_condition`、`correctness_gate`、barrier nodes を持つ機械可読 hold にする。
   失われた保証は「SHA `9b90d510...` の byte image の 16 行目が `_REAL_TOKEN_SLICE` だった」の
   **再検証可能性だけ**である、と明記する。受入成果物へは非成功として搬送し、
   「source-bound を再確認した」と主張しない。
3. **レンズ A の BLOCKER を同じ変更単位で閉じる。** `prompt_source` の dict 全体
   (`sha256` / `chars` / `bytes` / `replacements`) を literal 固定する。現状は prompt SHA しか
   固定されておらず、`replacements` を 8 など {0,9,10} の外へ変えると 3 case すべてが
   負例になって通る。hold を入れるだけではこの穴が残る。
4. **production の挙動保証は hermetic に残す。** 合成 rollout で `render_prompt` の
   replacement 検査を正例 9 / 負例 0・10 として走らせ続ける。原本が無くても
   受理集合の検査は止めない。
5. **案 2 を将来の移行先として残す。** SHA `9b90d510...` に byte 一致する原本を backup から
   回収できたら、repo 内へ固定して pin を repo 相対にし、hold を解除する。
   token slice から似た file を組み立てて新 hash へ期待値を変える形は F27 型なので採らない。

## 採らない案

- **案 2 (単独)**: 実施不能。working tree、通常 filesystem、到達可能 Git blob のいずれにも
  一致物が無い。親が `find /work/1/SFC/tanab /home/SFC/tanab` で 0 件を実測した。
- **案 3**: 不採用。上記のとおり別測定に相当する。別 rollout を使うなら新 task ID・新 manifest・
  新事前登録・新成果物を持つ successor 測定として追加し、その raw rollout は今度は repo 内へ
  同時保全する (retention 領域だけに置かない)。
- **案 4**: 不採用。F9 / F697 の直接の再発。現環境では恒久的に発火しない検査になり、
  pytest rc=0 を得ても source binding は一度も検査されない。絶対規律 2 に対して
  「赤い検査を走らなくして通す」変更である。

## 未解決 — ユーザー裁定が要る 1 点

hold 機構の `release_condition` は `explicit-user-command-only` であり、現に動いている先例も
`ruling: 2026-08-12 rulings 第 3 束` というユーザー裁定 ID を持つ。**正しさ検査を受入から
外す登録には裁定 ID が要る。** どの案を採るかは本書で決着したが、この ID だけは代行できない。

## 併記する事実 (本 wave の scope 外)

レンズ B が repo 外の生成物を読む他の箇所を棚卸しした。T-189 jobs tree、T-1434 science slice
(skip guard 無し)、B-10 measurement corpus (plot 1 node と provenance 16 node)。
いずれも現在は root が実在し赤は出ていないが、job tree の整理や測定 corpus の移動で
同じ型で壊れうる。**一般化 gate の追加は本 wave の scope 外**であり、
レンズ B 自身もそう述べている。記録だけ残す。
