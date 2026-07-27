| 所見 | 判定 | 根拠 |
|---|---|---|
| B2-1 | closed | `DW-C00` に変更面確定時の再評価義務が追加され、wave 開始時に同節を読む入口契約から継続的な実行義務として到達できる。 |
| B2-2 | partial | commit 前・後の両検査は明記されたが、記載コマンドは interpreter と必須の message-file 引数を欠き、そのままでは実行不能。 |
| B2-3 | partial | 本文任意への修正は実例と整合するが、`Co-Authored-By` との連続配置を規範化したまま checker は `AI-Agent` の Git 認識しか検査せず、受理集合の差が残る。 |
| B2-4 | partial | 無上限の間接 edge は残る。一方、`ai-provenance.md` への byte 上限追加は共有予算スキーマ変更であり、T-127 の裁定境界上、裁定パッケージ送りは妥当で本 wave の blocker ではない。 |
| B2-5 | closed | 旧「現行実体」を保存し、日付・タスク付きの「現行実体の更新」を追記しており、追記専用規則に適合する。 |
| B2-6 | closed | 「認識しない」という過度な断定が「認識は保証されない」へ修正され、Git の条件依存挙動を正確に表す。 |

## 新規所見

[must-fix] `docs/dev-wave/operations.md:95` commit 前検査の記載は、現物では実行不能なコマンド形である。

根拠: `tools/check_ai_provenance.py` は非 executable (`-rw-r--r--`) で、`--message-file` は [checker の argparse 定義](/home/SFC/tanab/github/izanagi/tools/check_ai_provenance.py:163)上、直後に `<path>` または `-` を要求する。正しい形は `python3 tools/check_ai_provenance.py --message-file <path>`。

成果物影響: 規則どおりでは記録 commit を作れず成果物参照の凍結が止まり、即興で省略すれば不正 trailer と旧 SHA 参照の再発余地が残る。

その他の横断検査では、C00 と入口の読み込み契約、F25 の追記形式に新規矛盾なし。byte は core `8,962/9,000`、4 reference 合計 `23,936/24,000` で、`REQUIRED_REFERENCE_SECTIONS` は全必須 H2 が一意かつ孤児なし。`check_docs rc=0` は親実測であり、本レビューでは再実走していない。

## 総括

**NO-GO。** B2-2 の実行不能な commit 前検査と、B2-3 の規範・checker 受理集合不一致が残る。  
pytest は指定どおり未実走。