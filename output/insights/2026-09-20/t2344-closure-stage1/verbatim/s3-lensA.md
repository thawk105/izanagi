## 所見 1: subset 変異は、受理拡大ではなく KeyError で赤くなる

**判定: real。plan の変異設計の欠陥。**

**根拠:** [s2-plan.md:479](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/s2-plan.md:479) は、63 validator を subset 許容へ変える候補を挙げています。しかし複製元の [campaign_lock.py:511](orchestrator/campaign/campaign_lock.py:511) は、比較後も宣言 tuple 全体について `blob_sha256s[path]` を参照します。

比較条件だけを緩めた場合、`env_contract.py` 欠落はここで `KeyError` になります。先例の [test_campaign_lock_codec.py:628](orchestrator/tests/test_campaign_lock_codec.py:628) は `CampaignLockCodecError` を期待するため赤くなりますが、subset を誤受理したことを検出した赤ではありません。

**直し方:** 変異差分と期待失敗箇所を具体化する。`KeyError`・fixture 構築失敗・import error は、狙った受理境界を検証した成功として数えない。

## 所見 2: 「63 を現行分岐へ流すと拒否 test が赤」は逆

**判定: real。親 brief の欠陥。plan は修正できています。**

**根拠:** [brief.md:50](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/brief.md:50) は、この変異で「拒否 test が赤」としています。しかし現行分岐は [campaign_lock.py:707](orchestrator/campaign/campaign_lock.py:707) で通常 decoder を呼び、その `_validate_authority` が85以外を拒否します。

したがって、通常 decoder／certified の63拒否 test は引き続き通ります。落ちるのは63の**歴史読取り成功 test**です。[s2-plan.md:481](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/s2-plan.md:481) の説明が正しいです。

**直し方:** P5 のこの候補を「歴史互換性の正例が赤」へ修正する。certified 受理拡大を検出する変異とは分ける。

## 所見 3: 親の「bytes が変わる commit は受理を変えない」は条件不足

**判定: real。親の measured-facts の一般化に欠陥。plan §7 は影響を適切に限定しています。**

**根拠:** [measured-facts.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/measured-facts.md:92) の主張からコードで確認できるのは、**記録 epoch と現在 epoch の差そのものを拒否理由にしない**ことまでです。[artifact_admission.py:1168](orchestrator/campaign/artifact_admission.py:1168) は現在の capture 成功を要求し、その他の受理述語も実行します。bytes の変更一般について、受理不変とは言えません。

新22本の dirty による影響は実在する呼出し経路に届きます。[test_p3_s4_loop.py:1007](orchestrator/tests/test_p3_s4_loop.py:1007) と [test_p3_b4_closed_critic.py:282](orchestrator/tests/test_p3_b4_closed_critic.py:282) は実 certified admission を呼びます。共有 fixture が HEAD blob を使っても、後続 capture は省略されません。これらの driver を編集した checkout では新たに拒否されます。

A-2 の submit-tree 運用も全 consumer の保証にはできません。[paper_story_a2_certification.py:3300](orchestrator/campaign/paper_story_a2_certification.py:3300) は実行中の通常 decoder を直接呼び、[同:5045](orchestrator/campaign/paper_story_a2_certification.py:5045) の collect 入口に記録 commit のコードへ切り替える処理はありません。policy の絶対 path 束縛だけでは、import 元 checkout まで同一とは証明できません。

対象 driver 自体を意図的に dirty にして certified 成功を期待する現行 test は、確認範囲では見つかりませんでした。外部運用の全件確認はしていません。探索中、`orchestrator/tests/test_qualification_identity.py` は存在せず、`docs/*a2*` に一致する path もありませんでした。

**直し方:** 親の説明を「current capture と他の検査が成功する限り、epoch 差だけでは拒否しない」へ限定する。submit-tree は確認済み運用だけの記述にし、plan §7 の dirty 影響を引き継ぐ。

## 所見 4: exact-63 から certified への抜け道は壊せなかった

**判定: refuted。提示された plan に受理拡大の欠陥は確認できません。**

**根拠:**

- [campaign_lock.py:402](orchestrator/campaign/campaign_lock.py:402) の通常 authority 検査は現行 tuple と完全一致を要求します。85化後の63は拒否されます。
- [artifact_admission.py:1022](orchestrator/campaign/artifact_admission.py:1022) は exact enum を確認してから decoder を選びます。歴史 decoder への certified fallback はありません。
- `_historical_decoded_from_current` は通常型から歴史型への変換です。[campaign_lock.py:663](orchestrator/campaign/campaign_lock.py:663)
- plan は歴史 authority、committed blob 照合、歴史 scope、`_RecordedCampaignVerifierEpoch` の各分岐に63を追加します。[s2-plan.md:224](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/s2-plan.md:224)
- 最後にも歴史 epoch の certified 流入を拒否する型検査があります。[artifact_admission.py:1164](orchestrator/campaign/artifact_admission.py:1164)

なお、brief の「通常 decoder は exact-85 のみ」は **v2 authority grammar に限る**表現に直すべきです。v1 decode は残り、certified 側で E0 が拒否されます。plan 冒頭はこの限定を明記しています。

**直し方:** 境界変更は不要。brief の v2 限定を明記し、plan の63専用分岐を漏れなく実装する。

## 所見 5: wire 順と宣言順の二段検査は成立するが、同一 literal の自己照合には限界がある

**判定: refuted。入力 grammar の曖昧受理は壊せなかった。**

**根拠:** 歴史 decoder は入力を sort して救済するのではなく、`tuple(blob_sha256s)` を sorted 期待列と比較します。[campaign_lock.py:705](orchestrator/campaign/campaign_lock.py:705)

未知 subset／superset／同数別集合は対応分岐に一致せず、最後の24 validator でも拒否されます。入力順違いも歴史 validator が拒否します。通常 decoder では集合検査の後に outer canonical JSON 検査が拒否します。[campaign_lock.py:639](orchestrator/campaign/campaign_lock.py:639)

同じ集合で順序だけ違う宣言 tuple を authority に渡すと、白名単との ordered tuple 比較が拒否します。正しい宣言 tuple に異なる map 順を渡した場合も拒否されます。[campaign_lock.py:279](orchestrator/campaign/campaign_lock.py:279)

ただし、**production の白名単 literal 自体を並べ替えれば**、wire 識別は変わらず、その変更済み literal で map を再構成して自己照合は通ります。これは入力 grammar の抜け道ではなく source 変更であり、独立 literal・固定 epoch test が検出する対象です。

**直し方:** plan の二種類の順序を維持する。「production literal の破損も runtime 白名単だけで検出する」とは説明しない。

## 所見 6: 末尾追加による歴史63 epoch の変化は壊せなかった

**判定: refuted。P3 と plan の固定値は整合します。**

**根拠:** [artifact_admission.py:1097](orchestrator/campaign/artifact_admission.py:1097) は歴史 authority の記録順を使い、hash preimage は domain＋各 `path\0`＋32-byte digest です。scope は含みません。

production を import せず、既存 test literal と plan の85 literal からメモリ内計算しました。先頭63本は順序込みで一致し、次の4値を再現しました。

| 対象 | ordered-path SHA-256 | E1 の SHA-256 部分 |
|---|---|---|
| 63 | `2247e5312a327caca9d0d4be081457eaf196513764010f64ccad1561409399ec` | `73f334f62ec13c394aae3d4787b80117562187984b6e0e372f2c0f7058b8ced2` |
| 85 | `bea3624661166dbe20df206ebd1e4f855f8c13e39721ab67e8b19d981bd6b5a1` | `bc8a6c8c6fd792ab6f21f22107f5313fb64ef0be1d6f8c97a15065998c423dc7` |

[test_artifact_admission.py:1578](orchestrator/tests/test_artifact_admission.py:1578) の ordered-path hash は **test 期待列**の順を検査します。production だけの並べ替えは独立 literal 比較と実 epoch 比較、production と期待列の同時並べ替えは固定 hash が検出します。固定 epoch assert が先に失敗すれば、同じ実走で後続 path-hash assert まで到達したとは数えられません。

**直し方:** 固定値は維持する。変異結果では最初に失敗した assert を記録し、複数の検査が発火したと一括報告しない。

## 所見 7: 否定側の棚卸しは、既知 grammar との衝突を回避している

**判定: refuted。plan §5 の恒真化・既知集合混入は壊せなかった。**

**根拠:** [test_campaign_lock_codec.py:610](orchestrator/tests/test_campaign_lock_codec.py:610) と [test_artifact_admission.py:3269](orchestrator/tests/test_artifact_admission.py:3269) の62 superset は、worker ではなく `unknown_t2483.py` を追加します。63本でも既知 exact-63 とは別集合です。

危険な具体例は **exact-63 の末尾 worker を削る操作**です。これは未知62ではなく既知 exact-62 になります。また現行63の missing-key test で worker を削った場合、通常 decoder の拒否は正しくても「歴史 decoder が未知 grammar を拒否した」証拠にはなりません。

[s2-plan.md:392](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage/s2-plan.md:392) はこれを認識し、新63 subset では `env_contract.py` を削除します。worker が残るため既知62には一致しません。更新後の現行85−1は84で、収載 grammar と衝突しません。

**直し方:** plan の具体的変形をそのまま採用する。先例の `paths[:-1]` を63用へ機械的に複製しない。

## 所見 8: 163／85／22 の計数規則のすり替えは見つからなかった

**判定: refuted。親の集合計測と plan の22本は再現できました。**

**根拠:** repository 内の [probe 原文:96](output/insights/2026-09-09/t2344-closure-reachability/verbatim/probe-closure.md:96) は `ast.walk` で関数内・条件分岐内 import も拾い、seed と import 先の package `__init__.py` を展開します。

この原文をメモリ内で用い、固定 commit `f94b61fc865af29ff3c7e1c8ef8b99fd8a1216ad` の Git blob に対して再計算しました。結果は **1段目85、全発見集合163、未解決参照0**。plan の85集合と一致し、追加22本は差集合の sorted 順と一致しました。今回、新規追加の `__init__.py` は0本でした。

package 初期化を含める規則は [docs/decisions.md:50607](docs/decisions.md:50607) の D1650 と一致します。T-733 の24→62を同規則で再現した記録もあります。[既存 insight:45](output/insights/2026-09-09/t2344-closure-reachability/README.md:45)

これは静的発見集合の再現であり、163本全部の production 実行到達を証明したものではありません。

**直し方:** 計数・追加集合の変更は不要。静的発見と実行到達の区別を維持する。

## 総括

最大の risk は、変異が `KeyError` や別の検査で赤くなったことを、狙った正しさ境界の検証成功と誤認することです。
親 brief の P5 と measured-facts の受理不変の説明には修正が必要です。
提示された plan から exact-63 が certified に流入する経路は壊せませんでした。
集合数・追加順・固定 hash は再計算で一致しました。pytest・変異実走・ファイル変更は行っていません。