## 対応表

| 段6の所見 | 状態 | 根拠 |
|---|---|---|
| F1 H-line の対象選択 | **closed** | [run_probe.py:776](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:776) は source で選び、9件の展開不一致、他12件と全21件の include 活性一致、21件の重複なしを要求する。[selftest.py:217](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/selftest.py:217) の組は原データと順序まで一致し、旧 filter を拒否する検査もある。 |
| F2 裁定済み OID への固定 | **closed（親の投入経路）** | [run-compute.sh:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/run-compute.sh:8) は C・C1′・C3 を定数で渡す。[同:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/run-compute.sh:11) の裁定済み C2′ と `C2p.oid`、bundle の指定 ref を照合し、不一致なら [投入命令:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/run-compute.sh:26) より前に終了する。probe 単体は値を固定しないが、[段6裁定:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/s6-ruling.md:11) が指定した修正範囲に合う。 |
| F3 C4 の表示名 | **closed** | 両 run の `passed` が真の場合だけ pass 名を付け、それ以外は `fail`。[run_probe.py:705](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:705) |
| F4 不要な診断計数 | **closed** | 修正前からの差分で定数と stderr 計数だけを削除。[s6-fix-1.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/out/s6-fix-1.md:12) |
| F5 selftest の説明 | **closed** | 単位11の4変異を明記。[selftest.py:1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/selftest.py:1) |
| F6 anchor の表示 | **closed** | 確定済みと記載し、4件の照合ログがある。[mutation-spec.json:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/spec/mutation-spec.json:3)、[check_anchors.log:4](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/check_anchors.log:4) |
| 表末尾: gzip fallback 削除 | **closed（不採用裁定どおり）** | zstd がない場合はエラーになる実装のまま。偽緑にはならない。[run_probe.py:541](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:541)、[段6裁定:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/s6-ruling.md:16) |
| 表末尾: reasons／first_reason 照合 | **closed** | H-set は protocol 別、それ以外は入力との一致を selftest で照合する。[selftest.py:265](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/selftest.py:265) |

**F1 の原データ検算:** [C1-preprocess.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/compute-1/C1-preprocess.json:3) の `(source, target)` を独立に数えると、計21組・重複なし、`cc/<p>/tpcc_<p>.cc` が9組、その他が12組。旧 target 選択は12組で、余分な3組は mocc・si・silo の `transaction.cc` から `tpcc_<p>.exe` への entry（例: [mocc:183](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/compute-1/C1-preprocess.json:183)、[si:435](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/compute-1/C1-preprocess.json:435)、[silo:615](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-mocc-v3-emitter/evidence/compute-1/C1-preprocess.json:615)）。新判定の対象集合は[段6 §3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/s6-ruling.md:29)どおり。

## 新しい所見

**must-fix / should / nit: なし。** 修正による selftest 照合の弱化、C4 合否の回帰、他の3変異の判定回帰、起点からの検査弱化という攻撃は**不成立**。H-set は両 protocol の失敗と先頭 `schema`、S-table／M-type は単独の指定理由を要求し、例外は `ERROR` で kill に数えない。[run_probe.py:618](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:618)、[同:762](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:762)。C0 の親・raw diff・tree/blob 照合と C1 の両木21件比較も残る。[同:229](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:229)、[同:377](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:377)。`v3check.py` は修正前と同一だった。

## 総括

**GO（静的再レビュー）。** 指定資料の読み取りと原データの計数で、段6の修正条件は満たされている。probe は指示どおり走らせていないため、C4 の実際の合格と4変異の実際の kill は未判定。親の自己試験記録は [185/185 passed](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/evidence/parent-selftest-2.txt:3)。