## 所見 (real 候補)

**B6-1 — stock の roundtrip 成功を、修正前後の pre-image byte 一致の証拠にはできない。**

- **根拠:** [s4-ruling.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md:17) は全文比較の観測手段に stock roundtrip を挙げ、[s5-impl.diff.txt:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-impl.diff.txt:12) は既存 pre-image の byte 一致を断定している。しかし [test_campaign.py:11236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py:11236) は、修正後の実装が返す `"stock"` と variant ID の一致を検査するだけで、修正前の bytes を比較しない。
- **real と主張する理由:** working-tree と baseline の正規化結果が同じように変化しても、両者の一致と `"stock"` は維持される。旧 variant token との比較も、stock 全8 genome の旧 pre-image 一致を代替しない。実際の byte 変化を発見したという所見ではなく、証拠から導ける結論の不一致である。
- **must-fix:** 放置すると、レポートが「stock token 維持」を「旧 pre-image artifact との互換性確認済み」へ過大評価する。
- **是正案（scope 内）:** 裁定・最終報告では token 維持と byte 一致を分け、旧 bytes との比較証拠がない範囲を未確認と記す。新 gate・検査機構の追加は不要。

**B6-2 — 焦点走の場所と compiler の証拠を、裁定の予定から引き継げない。**

- **根拠:** [s4-ruling.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s4-ruling.md:75) は login 走を予定するが、[s5-focus-run.log:2](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2731-cpp-normalize-dd/s5-focus-run.log:2) は計算ノードへの dispatch を記録する。同ログには個別 nodeid・compiler 版がない。unit test の選択関数は [test_campaign.py:11193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py:11193) の `_any_cxx()`。
- **real と主張する理由:** 計算ノードでも、このテストの compiler 選択が自動的に `compilers_for_current_site()` へ変わるわけではない。ログの集計値だけから、特定 node の実走や g++ 11.4 の使用は確認できない。
- **should:** 放置すると、レポートの実行環境・個別 node の検証済み範囲が証拠以上に広がる。製品の受理集合への直接影響はない。
- **是正案（scope 内）:** 実行場所は dispatch と記し、compiler 版・個別結果は既存の実記録を参照できる範囲だけ確定する。記録がなければ未確認とする。

## 報告と実体の一致

- commit `bd21bc501` の変更は申告された2ファイルのみ。両ファイルの現物は commit の blob と一致する。
- 追加は申告どおり8関数。変更前との AST 比較で、既存関数・クラスの変更や削除はなかった。差分にも既存期待値の変更・skip 追加はない。
- author は「pytest 実走0件・すべて未実走」と明記しており、実走済みへの偽装や申告漏れは認めない。
- 親のログから確認できる結果は **38 passed、3 skipped の集計**。author の未実走報告とは別の走行であり、矛盾しない。関連検査全件の完了証拠にはできない。

## 変異の帰属 (anchor の一意性・期待集合・単一理由)

**全 anchor の一意性を静的に確認した。** source-level 4変異と recipe 8変異について、各変異を独立に扱い、複数置換はメモリ上で累積適用した。各段階の `old` 出現数はすべて **1**。

新8 node に限定した source-level の期待集合は整合する。

| 変異 | 期待される失敗集合 | 帰属 |
|---|---|---|
| S0 | 空集合 | docstring のみ |
| S1 | A・B・F・H | 有効枝の指令が消え、identity の差が失われる |
| S2 | D・E | working-tree 側の追加供給が pre-image に残る |
| S3 | G | prefix 不一致でも正規化結果を返す |

A/B/H は include 列を変えず、F は既存供給の `BACK_OFF` を使う。別の拒否層による mask は静的には見当たらない。G は `_cpp_normalize` を直接呼び、診断文言ではなく例外の有無を検査する。

裁定どおり「8関数名の完全名を `or` 連結」した場合、AST 上の部分文字列照合で選択されるテスト関数は当該8件のみだった。ただし、**実際の runner argv と collection 結果の照合は未確認**。両 spec 自体には runner argv がない。

recipe の期待集合は裁定と一致する。今回確認したのは carrier の anchor と登録内容であり、probe 最終 checkout の結果や赤理由の実測ではない。DW-M08 の完全一致判定を通ったとは報告しない。

## consumer 整合と scope

- `_normalize_contexts` の文脈順序・タグ、canonical pre-image の連結方式は変更なし。有効指令が正規化内容へ加わる。
- `_trace_pair_diff` の比較式は維持されるが、指令差によって受理集合が変わる。author はこの波及を明記している。
- TRACE=0 checker も同じ正規化変更を受ける。consumer 自体の変更はない。
- `p3_s4_loop_trigger_gating.py:348` の既存 artifact との byte 不一致停止は維持され、author の波及列挙と一致する。
- spawn site 登録簿・静的 call 数登録簿は未変更。`_cpp_normalize` の `subprocess.run` は静的に1箇所のまま。
- cache・再帰 flag・prefix 不一致停止は裁定内。裁定外の helper・台帳・一般化は追加されていない。追加 docstring は include 相対位置と macro stack の限界を明記している。

## 総括

**実装の修正を要する矛盾は今回の静的検査では見つからなかった。報告上の must-fix は B6-1、証拠の整理は B6-2。**

anchor と source-level 期待集合は静的に支持できる。変異の実測成功、collection の完全一致、旧 pre-image の byte 互換性は未確認。ファイル変更・commit・テスト実行は行っていない。