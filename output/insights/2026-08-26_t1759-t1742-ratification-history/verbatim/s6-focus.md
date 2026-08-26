## 所見ごとの closed / partial / regressed 判定

| # | 採用所見 | 判定 | 静的根拠 |
|---:|---|---|---|
| 1 | batch 成功応答の query 束縛 | closed | 成功形は4 fieldで解析し、`rest` を期待 commit と完全比較する。台帳と directory の両 query が同じ parser を通る。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:387) |
| 2 | blob byte 数と batch size の照合 | closed | OIDごとの size を保持し、同一 OID の矛盾も拒否した上で、取得した `raw` の `len` と照合する。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:476) |
| 3 | `_load_rows` の線形重複検査 | closed | 判定だけを `seen_digests` に移し、返却順と `enumerate(..., start=1)` は維持されている。重複行番号と `repeats a closure digest` の文言は変わらない。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:107) |
| 4 | 台帳親1 + 非台帳親1の拒否例 | closed | bearing 親の行を replacement に置換する2親 mergeを構成しており、「非台帳親があれば検査を飛ばす」誤実装を殺す。[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:483) |
| 5 | octopus の拒否例 | closed | 3番目の親だけが持つ digest を merge 結果から落としているため、最初の2親しか見ない誤実装を殺す。[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:613) |
| 6 | 不正中間遷移テストの深化 | closed | 不正 commit の後に正常な append、carry、carry の3 commitがあり、不正遷移は `HEAD~3` にある。HEAD近傍だけを見る実装では期待する拒否に到達しない。[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:780) |
| 7 | graft と replace ref の分離 | closed | 空 graft と unrelated replace ref は独立した2 testになっている。[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:896) |
| 8 | batch 異常系の負例 | closed | query比較を除去すれば query mismatch testが、size比較を除去すれば size mismatch testが失敗する構造。対象 helper は production から実際に呼ばれており、test専用の死んだ関数ではない。[テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:232) |

`partial` 0件、`regressed` 0件。severityを付ける新規所見はない。

## 新しい破れ

新規所見なし。

- missing 応答は、確定契約どおり `<commit>:<path> missing` を4 field解析より先に処理する。成功応答は `<oid> <type> <size> <commit>` として別に処理される。`%(rest)` 導入による両形の混同はない。
- query は `<commit>:<path>` と後置 commitを1個のASCII空白で分離している。pathとcommitに空白はなく、object指定と `%(rest)` の境界は壊れていない。
- 空 blobは size 0として保持され、`len(b"")==0` を通って空行列になる。台帳不在 commitは `None` のまま blob取得対象から除外されるため、size台帳の不在参照は起きない。
- 重複 digest の行番号は従来どおり入力上の行番号である。
- batch負例は内部関数を直接呼ぶが、削除対象の比較そのものを通る単一理由のテストであり、production call siteも同じ関数を使用している。

## 規則の不変性

段4の評価順、受理集合、拒否集合に fix 差分による変更はない。

- `_validated_root`、shallow、graft、HEAD、DAG列挙、batch取得、blob取得、各 commit検査、導入一意性、HEAD集合返却の順を維持している。
- 削除、置換・並べ替え、複数行追加、複数行導入の既存4メッセージは逐語で維持されている。[遷移検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:568)
- query不一致とsize不一致は既存の新設メッセージ `ratification ledger is not a blob in committed history` を使い、新しい第5メッセージを増やしていない。
- broaderな性能再設計は入っていない。採用された重複判定のset化だけで、全世代保持、OID単位取得、process構成は維持されている。
- mode allowlistの緩和も入っていない。`100644` / `100755` のexact allowlistを維持している。[mode検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:510)
- mode allowlistは段4の素の文言より強いが、これは段6裁定が明示的に「実装を維持」とした既存差であり、fixが持ち込んだ規則変更ではない。

## 総括

静的再レビューでは、採用8件はすべて closed。新しい偽赤、誤受理、メッセージ変更、棄却事項の混入は見つからなかった。

pytestその他の実測は行っていない。以上は指定された8ファイルだけによる静的判定である。