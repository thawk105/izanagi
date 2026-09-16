## 3 件の対応表

**3件とも closed です。** 重大度は前巡の分類です。

| 対象 | 判定・重大度 | 照合結果／放置時の影響の解消 |
|---|---|---|
| §1.2 identity 実値 | **closed**／重大度: should-fix | 7行すべて一次資料と一致。job body digest の欠落と、事前登録の2束縛を混同する問題は解消。 |
| §1.4 field 不存在 | **closed**／重大度: should-fix | 不存在を `result.json` に限定。WAL の `payload.src_token` は baseline が `stock`、target が source digest と一致し、直後の説明と矛盾しない。誤った参照先への誘導は解消。 |
| §4.2 hash 照合範囲 | **closed**／重大度: should-fix | A-2／A-6 の manifest 照合と、T-1998 の `result.wal_sha256` 照合を分離。T-1998にも raw manifest があると読める問題は解消。 |

T-1998 の成果物 root 配下を再帰列挙し、23ファイルに `raw-manifest.json` が無いことを確認しました。WAL の実計算 SHA-256 は `154ab894a9955885036fcaff03478001153ba015c50f395cbb59b3e20dcf594e` で、`result.json` と§4.3に一致します。

A-2／A-6 の両 manifest には、§4.3の raw JSON 6件・WAL 3件の path と hash が一致して掲載されています。前巡で閉じた現物9件の再監査は行っていません。

## identity 表の照合

**全7行一致です。** 下表では値を短縮表示していますが、照合は全桁で行いました。

| 行 | 掲載値 | 照合した一次資料 |
|---|---|---|
| repository commit | `a551cdd3…c21137` | `result.repository_commit`、`reservation.source_binding.repository_commit` |
| CCBench gitlink | `511c9538…b706ec` | `result.ccbench_commit`、`reservation.source_binding.ccbench_gitlink_commit` |
| 環境契約 digest | `e576e9cd…42c01` | 是正記録§1・着地後再解析§2。事前登録§4・§5とも一致 |
| job body script digest | `dff913cb…7aecd8` | `reservation.binding.script_sha256` |
| arm別 source digest | baseline `2d691b45…239a2c6`／target `678b7203…580b12` | 登録2 arm の WAL `build_start.payload.build_admission.source.source_bytes_sha256`。本文§1.4の全桁とも一致 |
| baseline 性能 binary digest | `66054364…565d9` | 同 arm の WAL `build_done.payload.perf_bin_sha256`、両解析記録 |
| target 性能 binary digest | `6c89ebd9…dfec4` | 同 arm の WAL `build_done.payload.perf_bin_sha256`、両解析記録 |

2定数の説明も事前登録§1・§8に収まっています。成果物側は記録された commit の blob、解析規則側は渡された作業木の bytes に対する独立した束縛です。投入記録と両解析記録は、双方の値を `464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` と記録しています。今回の事前登録ファイルの実計算値も一致しました。

## 新しく壊れた箇所

**無いです。** 指定された修正に伴う範囲では、次を確認しました。

- §1.2・§1.3・§1.4の重複掲載値は一致し、出所の説明にも矛盾がありません。
- field 不存在と3走行一括の manifest 照合について、旧説明の消し残しはありません。
- §4.2の9件と§4.3の6件＋3件は一致しています。
- §3の限定は **1〜20の20件**で、欠番・重複なし。入口 README の対象行も **限定20件**です。
- 追加表による節番号・関連参照のずれはありません。

## 総括

**対象3件はすべて閉鎖、新規所見は0件です。** 指定資料による静的照合のみを行い、ファイル変更・測定・テストは行っていません。