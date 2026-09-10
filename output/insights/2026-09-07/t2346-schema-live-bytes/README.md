# [T-2346] qualification schema の live bytes を記録 blob へ結ぶ

D1512 の裁定を実装した wave の一次資料。

## 何が問題だったか

qualification の受理判定は、2 か所で schema を disk から読んでいた。

- `orchestrator/qualification/artifacts.py` の `validate_json_schema`
- `orchestrator/qualification/collector.py` の `_schema_validate`

どちらも `Path(__file__).resolve().parent / <name>` で package directory から読む。
一方、身元検証 `orchestrator/qualification/identity.py` の
`verify_recorded_series_identity` は、記録された commit の blob hash と preimage の
`code_identity` が一致することしか見ていなかった。

つまり **判定が実際に読んだ bytes と、記録された blob との等値は、どこでも確かめられていなかった。**
同じ campaign epoch・同じ記録 code identity のまま、disk 上の schema を緩めるだけで
qualification receipt の受理集合が広がる経路が開いていた。これは provenance の粒度の問題ではなく
受理境界の問題であり、規律 2 の側に入る (D1512)。

## 何をしたか

1. `artifacts.py` に `qualification_schema_bytes(schema_name) -> bytes` を足した。
   - 入力検査は既存 `validate_json_schema` の 3 条件をそのまま移した。新しい拒否条件も
     6 名の allowlist も足していない (allowlist は受理集合を不要に狭めるので段 3 で却下した)。
   - 呼ばれるたびに disk を読み、schema 名ごとの memo と比較する。一致すれば memo の
     bytes object を返し、不一致は `QualificationArtifactError` で拒否する。
2. `validate_json_schema` と `collector._schema_validate` をこの helper 経由へ変えた。
   collector と identity からの参照は module-qualified にした。
3. `identity.verify_recorded_series_identity` で、記録 commit の blob 検証の直後に
   6 schema の live bytes の sha256 と記録 digest を照合し、不一致を
   `IdentityVerificationError` で拒否するようにした。

## なぜ bytes を返す helper なのか (段 3・段 6 の所見)

段 3 のレンズ A が「path だけを共有して読み手と検査が別々に read すると、
`collector.py` の schema 検証 (受理) と身元検証の間で bytes を差し替えられる」ことを指摘した。
D1512 の文言は「**実際に使われた** schema の live bytes」なので、path の共有では文言を満たさない。

同一 FD を validation stack へ通す案は、全 validator の署名変更を伴い、D1512 が却下した
bytes 級 provenance 側へ寄るため採らなかった。代わりに helper が bytes を返して memo することで、
読み手と検査が同じ bytes object を使う形にした。

段 6 のレンズ C が、その memo が process 途中の schema 変更を見逃す穴を作ることを指摘した。
memo は親が段 4 で足したものなので、性質を保ったまま穴だけ塞いだ —
毎回 disk を読んで memo と比べ、不一致は fail-closed で拒否する。差分前と同じ I/O 回数に戻る。

## この検査が保証しないこと

- 記録 commit 自体に緩い schema が入っている場合の意味的な厳格さ。
- 6 schema 以外の code identity path、schema 以外の読み手、bytes 級の provenance。
- schema の変更履歴、read 時刻、FD・inode の provenance。

守るのは「受理判定が読んだ bytes が、記録された blob と同じであること」だけである。
D1417 と同じく、列挙した closure の bytes 一致以上を主張しない。

## fixture を実 schema へ変えた理由

`_attempt()` は識別 path の中身を `f"fixture {relative}\n"` というダミー文字列で埋めていた。
live の validator は実 package の schema を読むので、fixture repo の記録 blob と live bytes が
最初から食い違う。6 schema だけを実 file の copy に変え、fixture が現実と一致するようにした。
validator・期待 digest・拒否条件はいずれも差し替えていない。

## 変異台帳

| file | 内容 |
|---|---|
| `mutation-spec-final.json` | 本走 spec (M12 / M13) |
| `mutation-ledger-final.json` | 本走の結果。baseline PASSED、M12 KILLED、M13 KILLED、いずれも単一 node |
| `mutation-spec-probe.json` | 帰属 probe spec (既存 35 変異、全件 SURVIVED 期待で観測 node を集める) |
| `mutation-ledger-probe.json` | probe の結果。35 件完走、M12 / M13 の node はどの失敗集合にも現れない |
| `mutation-ledger-erratum-run1.json` | 本走の初回 (erratum)。下記の冗長 gate で MISMATCH になった |

### 本走の期待と結果

- `M12-t126-registry`: `identity.py` の live bytes 等値条件を恒偽化 → KILLED。
  失敗 node は `test_m12_relaxed_live_schema_cannot_expand_receipt_acceptance` の 1 件だけ。
- `M13-t126-registry`: `artifacts.py` の memo/disk 一致条件を恒偽化 → KILLED。
  失敗 node は `test_m13_qualification_schema_memo_drift_fails_closed` の 1 件だけ。

### erratum — 初回走行の冗長 gate

初回 (`mutation-ledger-erratum-run1.json`) は M12 / M13 とも自分の node に加えて
`test_fr3_mutation_node_registry_is_exact_and_complete` を落とし、MISMATCH になった。
この meta-test は変異登録簿の anchor 逐語が source に 1 回だけ現れることを検査するので、
**登録簿に anchor を持つ変異ならどれでも落ちる**。機構についての信号ではなく冗長 gate である。
`DW-M03` に従い、本走ではこの 1 件を `--deselect` して単一理由へ差し替えた。
初回結果は消さずここに残す。当該 meta-test は焦点走と受入では通常どおり走っている。

### 帰属

既存 35 変異の probe を回し、M12 / M13 の期待 node がどの変異の失敗集合にも現れないことを
実測した。M12 / M13 の kill は自分の変異に固有である。

なお `T126_MUTATION_REGISTRY` は parametrize された test の node を bare 名で持つため、
登録簿から機械生成した spec を全件そのまま走らせると collection 照合で止まる。
これは今回の変更とは無関係な既存の性質で、この wave では扱っていない。
