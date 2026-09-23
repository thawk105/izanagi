## 総括

**GO。7所見すべて closed。** 指定範囲で新たな誤り・後退や、§0・§4・§5 の不整合は認めない。
現物から判定取得済み90走・未完走4走、SIGKILL／timeout の区別、patch・verifier の hash、A-1 の4 file の同一性を確認した。編集・テスト・再判定・保全データ全量の再ハッシュは実施していない。

## 対応表

行番号はレビュー対象の [README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-repro-package-rest/output/insights/2026-09-23/t2853-repro-package-archive/README.md) を指す。

| ID | 状態 | 根拠（README の行） |
|---|---|---|
| M1 | closed | 192、218–219行。template patch 後の gate 条件式書込みと `source_before` 照合を明記。runner 637–645行の処理順と一致し、両 patch の記録 hash も一致。 |
| M2 | closed | 194、204–222行。現物は D2160 が64走中60走完了、B-8 が30走全完了。残る4走は0 B。balanced は `timed_out=false`・SIGKILL、write-heavy は `timed_out=true`・約3,601秒。改修版の資源値と旧版を区別し、`reverify` の非汎用性も正しく限定している。 |
| M3 | closed | 16–22、93、154、166、178、237–238行。確認できた範囲と標準経路からの判断を区別し、別コピーの不在を断定していない。 |
| S1 | closed | 77–78行。別実装による manifest 照合とし、cache 排除の証拠ではないと明記。 |
| S2 | closed | 87–88行。未追跡971 file と全体1,389 file を区別。A-1 の4 file は現物の完全な SHA-256 が現行追跡 file とすべて一致。 |
| S3 | closed | 49–52行。終了コードと照合成功を区別。script の実装および `copy.log` の12組すべて `ok=True`・不一致0・extra/missing空と整合。件数・bytes の再集計も本文と一致。 |
| N1 | closed | 116、216行。両方の `git worktree add --detach` に保存先と commit の引数がある。 |

## 新規所見

- **must-fix:** なし。
- **should:** なし。
- **nit:** なし。