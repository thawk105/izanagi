## 所見

### F-B1

対象 file:line: `s8b_floor_campaign.py:1493, 3670-3698`、`s8b_ratified_freeze.py:1654, 3252-3260`、`s2-plan.md:152-170`

主張: 旧 portable artifact は全て拒否される設計であり、resume と公開済み freeze の再検証が継続できない。

根拠: exact-key 集合へ `admission_receipt` を追加する一方、互換 loader、schema 移行、遡及再取得を実装しないと明記されている。tracked `output/s8b-freeze` には active v2 artifact が無いが、外部 durable store や過去 resume artifact の不存在は確認できない。

成果物影響: receiptless manifest/result の受理集合が空になる。既存の `floor_source.sha256` や trust root の bytes は変わらなくても、report、judge、resume がその成果物を読めなくなる。

重大度: blocker

### F-B2

対象 file:line: `s8b_materialization.py:73-95`、`build_admission.py:533-560, 647-747`、`source_digest.py:119-153`、`s2-plan.md:37-53`

主張: root 非依存 descendant receipt は、発行済み receipt であることを durable artifact 上で証明していない。

根拠: `source_root` を除いた body に新しい SHA を付けても、元の sealed `BuildAdmission` や元 receipt との連鎖が残らない。既存の review receipt も構造と一致性だけを検証し、人間の真正性は認証しない。発行時検証だけでは、後続 consumer が自己生成された同形 receipt と区別できない。

成果物影響: `receipt_sha256`、policy、source、subject が自己整合するだけの未発行 record が受理集合へ入る。保証を「発行済み admission の連続性」とするなら、元 receipt の安定した digest、issuer chain、または同等の信頼根が必要である。root-neutral テストも、現在は bytes 一致しか検証していない。

重大度: must-fix

### F-B3

対象 file:line: `s8b_ratified_freeze.py:3242-3260`、`s8b_oracle_report.py:1760`、`s8b_oracle_judge.py:371`、`build_admission.py:438-446`

主張: current policy を必須化すると、historical contract を使う read-only 再検証と衝突する。

根拠: `launch_validate()` は current contract、`reverify_published_freeze()` は記録済み historical contract を使う。後者は report と judge の公式入力経路である。policy は current pin と registry から再生成されるため、過去 artifact の policy と現在の policy が一致する保証はない。段2プランの consumer 一覧にも report、judge がない。

成果物影響: 過去 freeze の再検証、official report、judge が receipt 検査で拒否される可能性がある。逆に historical reverify だけ policy 検査を省くと、同じ portable record が経路によって異なる受理集合になる。

重大度: blocker

### F-B4

対象 file:line: `s2-plan.md:113, 131`、`s8b_floor_campaign.py:1493`

主張: 提案された mutation (a) は実際の弱体化を検出しない。

根拠: 負例テストは `admission_receipt` key 自体を削除する。しかし production の exact-key 検査が `admission_receipt is None` の検査より先に走るため、null receipt を受理するよう mutation しても、key 欠落でテストは赤いままである。

成果物影響: receipt 値が `None`、空 object、malformed body でも受理する欠陥が mutation test を通過する。key 欠落検査と、key はあるが無効な receipt の検査を分離する必要がある。

重大度: must-fix

### F-B5

対象 file:line: `s8b_v2_freeze_fixture.py:197-208`、`test_s8b_floor_campaign.py:5190-5201, 6261-6274, 2807-2811`

主張: 共有 fixture と直接 `_Runner` fixture は、production issuer と実 binary の束縛を検証していない。

根拠: v2 fixture は `binary_sha256` を持つ5項目程度の hash-only record で、binary path、store、binding、receipt、実 bytes がない。別の `_Runner` テストも receiptless の最小 record を直接構築している。ここへ現行 hash と合成 receipt を差し込むだけでは、receipt 発行器の正当経路を通らない。

成果物影響: holdout、ratified、oracle の正例が receipt の形だけを検証する。`test_binary_receipt_mismatch_aborts` も、意図した実測直前 hash 不一致ではなく receipt 欠落で失敗する可能性がある。なお `test_s8b_materialization.py:558-563` の golden SHA は literal なので、ここを production serializer から動的生成する変更は避けるべきである。

重大度: must-fix

### F-B6

対象 file:line: `s8b_floor_stats.py:591-619, 880-929`、`test_s8b_floor_stats.py:43-50`、`test_s8b_floor_campaign.py:3681-3700, 6343-6366`

主張: `verify_floor_artifact` の API 変更に対する既存 consumer がプランから漏れている。

根拠: 計画は current policy の追加を production caller 4箇所に限定しているが、test wrapper は旧3引数のままである。また `test_s8b_floor_campaign.py` は binaries を持つ実結果を policy なしで直接検証している。binaries 無しの formula fixture は後方互換対象だが、binaries 有りの直接呼出しは別扱いが必要である。

成果物影響: policy を必須引数にすれば既存テストが引数不足で停止する。任意引数にすれば、holdout や直接 verifier 経由で receipt 検査を回避でき、受理集合が呼出し元依存になる。

重大度: must-fix

### F-B7

対象 file:line: `test_s8b_materialization.py:449-563`、`s8b_ratified_freeze.py:60-62, 146-185, 3132-3136`、`s8b_approved.py:39, 60-63`、`test_s8b_ratified_freeze.py:1343-1354`

主張: portable record の変更は既存の literal golden と、将来の freeze hash chain に波及する。

根拠: manifest golden の SHA が `test_s8b_materialization.py:561` に固定されている。`result.binaries == manifest.binaries`、`sha256(result.raw) == generation.floor_source.sha256` も ratified chain に含まれる。V1 trust root の path と SHA 自体は変更対象ではないが、そこから参照される過去 result が receiptless なら F-B1 の拒否対象になる。

成果物影響: future manifest bytes、`manifest_sha256`、floor source SHA、generation hash が変わる。raw `source_root` を保存すると root 間 deterministic assertion も壊れる。literal golden は新しい固定値へ更新し、V1 pin は書き換えない必要がある。

重大度: must-fix

### F-B8

対象 file:line: `s8b_floor_campaign.py:2172-2217`、`s2-plan.md:61`

主張: store 書込前の全件 preflight は、実装だけでなく遅い位置の不正 record で検証する必要がある。

根拠: 現行 `store_binaries` は record ごとに処理と書込を行う。計画は全 receipt の preflight を要求しているが、先行 record を書き込んだ後に後続 record の receipt が不正な場合のテストがない。

成果物影響: 一部 binary だけが durable store に残った状態で build が拒否される。後続 resume や再実行が stale store を観測し、store の受理集合と manifest の受理集合が一時的に分離する。

重大度: must-fix

## consumer 数え上げ

portable built record の値を直接読む箇所と、その受理経路の中継を含めると、production は19箇所である。

- `s8b_floor_campaign.py:1485, 1524, 1557, 2172, 2220, 2463, 2764, 3670, 3703`
- `s8b_floor_stats.py:880`
- `s8b_holdout_freeze.py:1275`
- `s8b_ratified_freeze.py:1643, 1726, 1814, 2156, 2295, 2322, 2848`
- `s8b_oracle_driver.py:844`

間接 consumer は2箇所ある。

- `s8b_oracle_report.py:1760`
- `s8b_oracle_judge.py:371`

特に未計画なのは report、judge、`test_s8b_floor_stats.py:43-50` である。

## 正当経路の回帰リスク

- `test_s8b_materialization.py:449-563`: hand-written portable record と literal manifest SHA。
- `test_s8b_floor_campaign.py:5062-5068`: exact-key 期待値。
- `test_s8b_floor_campaign.py:5168-5234`: receiptless、空 binding の手書き fixture。
- `test_s8b_floor_campaign.py:2807-2811, 6261-6274`: receiptless の直接 `_Runner` fixture。
- `test_s8b_floor_campaign.py:3681-3700, 6343-6366`: policy なしの直接 floor verifier。
- `s8b_v2_freeze_fixture.py:197-208`: hash-only binary record。`test_s8b_holdout_freeze.py:1272-1444` などへ波及。
- `test_s8b_ratified_verify.py:266-283`: 現行11項目 portable record。
- `test_s8b_ratified_freeze.py:1343-1354`: 異なる root 間の blob、tree、commit bytes 同一性。
- `test_s8b_oracle_report.py:1303-1351`: ratified freeze の再検証経路。
- `test_buildcache_v2.py:755-808`: production変更なしの回帰対象。ここは receipt の追加で buildcache 契約を変更しないことを確認する。

## 所有分割の評価

production file の所有は A、B、C、D で素集合になっている。

ただし test ownership は未確定である。C が共有 fixture を変更し、D がそれを消費する構造は順序で解決できる。一方、`test_s8b_floor_campaign.py` は B 所有でも C の `floor_stats` API を直接呼び、`test_s8b_floor_stats.py` と `test_s8b_oracle_report.py` は割当先が明記されていない。

一枚岩にする必要はないが、対応 test file を列挙し、report、floor stats wrapper、ratified verify の所有者を明示すべきである。

## 未確認

- tracked 外の過去 run directory、計算ノード上の durable store、手元の resume artifact の件数。
- pytest、build、mutation は read-only 制約により未実施。緑とは判定していない。
- 必読ファイルは全て読めた。Web 検索は行っていない。

## 総括

- fresh build から resume まで receipt を運ぶ構造自体は整合する。
- しかし旧 artifact の拒否は resume、report、judge の継続性を断つ。
- historical reverify と current policy の扱いが最大の経路不整合である。
- root-neutral descendant は発行済みであることの連鎖を追加で定義しないと、自己整合性しか証明しない。
- mutation (a) は exact-key 検査に隠れており、現状の候補では実効性がない。
- hash-only fixture、直接 `_Runner` fixture、floor stats wrapper が未更新である。
- literal golden と将来の hash chain は変わるが、V1 trust root の bytes は変更してはならない。
- production ownership は分割可能だが、test ownership は明示的な再分割が必要である。