## 受領証の検証結果と `artifact_refs` が同じ bytes に束縛されない

- 所見の主張: 受領証を検証してから `artifact_refs` が再読するまでに差し替えると、異なる受領証 A/B を一つの材料レポートが受理する。
- 根拠: [wal.py:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:765) は raw bytes を読むが digest を返さず、[layer3_report.py:760](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:760) で検証後、[layer3_report.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:197) と [layer3_report.py:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:829) が全 artifact を再読する一方、lock/WAL にある再 hash 検査 [layer3_report.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:753) に相当する受領証検査はない。
- 成果物への影響: `knowledge_provenance` は受領証 A の source 集合、`artifact_refs` は受領証 B の SHA-256 という自己矛盾した材料レポートが生成・受理され、proof chain の参照先が変わる。
- **must-fix:** 受領証を検証した同一 read の raw SHA-256 を新 helper 内部から返し、`artifact_refs` の同 path の digest と一致しなければ停止する。既存 `_knowledge_provenance_from_receipt` の戻り値、受領証、WAL 形は変えなくてよい。

## 新 schema は WAL/受領証 validator が拒否する source を受理する

- 所見の主張: `knowledge_source` の schema は source identity・manifest digest・2 配列の関係を十分に拘束せず、producer が生成不能な provenance を schema-valid とする。
- 根拠: [layer3_schema.json:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:38) の `uniqueItems` は object 全体の重複しか拒否せず、[layer3_schema.json:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_schema.json:290) の `path` は `minLength: 1` だけである。したがって `../x`、同一 commit/path に異なる SHA を付けた二 source、digest と無関係な配列、互いに異なる declared/injected が通るが、WAL 側は canonical path を [wal.py:690](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:690)、identity 重複と digest を [wal.py:705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:705)、両 receipt field の一致を [wal.py:871](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:871) で拒否する。
- 成果物への影響: schema-only の材料レポート受理集合が広がり、repo 外や競合 identityを指す source、または manifest digest に束縛されない source 集合を正当な provenance と扱える。
- **must-fix:** 非 `null` 欄に対し、既存 WAL source 正規化と digest 導出を再利用する semantic validation を `_validate_schema` 後に加え、両配列が同じ manifest digest に束縛されることを確認する。`../`、同一 identity・異 SHA、digest 不一致、配列不一致を負入力にする。

## legacy 正規化は knowledge-aware v3 の欄欠落を補正できない

- 所見の主張: `setdefault("knowledge_provenance", None)` は fresh 側も `null` の非対応 campaign にしか効かず、欄追加前と同形の knowledge-aware v3 を拒否する。
- 根拠: [autonomous_trial_completeness.py:4702](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/autonomous_trial_completeness.py:4702) は欠落を `None` にするが、knowledge-aware fresh report は [layer3_report.py:761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:761) と [layer3_report.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/layer3_report.py:822) により object を持つため、全体比較 [autonomous_trial_completeness.py:5016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/autonomous_trial_completeness.py:5016) は不一致になる。追加テストも `pop()` した値が `None` の非対応 fixture に限定されている [test_autonomous_trial_completeness.py:4733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/tests/test_autonomous_trial_completeness.py:4733)。
- 成果物への影響: schema 上は許される provenance 欠落 v3 のうち knowledge-aware report だけが完全性検査で落ち、材料レポートと試行台帳の受理集合が裁定 4 の意図より狭くなる。
- **must-fix:** persisted 側に欄が無い場合は比較時に両側から欄を除外し、存在する場合だけ exact 比較する。knowledge-aware fresh object／persisted 欠落の fixture を追加する。

## 2 段の値は正しいが出所は独立に射影されていない

- 所見の主張: 現在の equality 不変条件下では出力値は正しいものの、実装は二つの receipt field を個別に射影せず、正規化済み canonical 配列を二度コピーしている。
- 根拠: receipt reader は verified source を別に構築して equality を確認する [wal.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:842) が、戻り値には canonical source だけを残す [wal.py:894](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:894)。新 helper はその同じ配列から両欄を作る [wal.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2183-knowledge-provenance/orchestrator/campaign/wal.py:965)。一方、等価変異としての許容は [mutation-prereg.md:22](/home/SFC/tanab/.claude/jobs/848c23d0/tmp/wave-t2183/mutation-prereg.md:22) に明記されている。
- 成果物への影響: 現在の材料レポート値・受理集合は変わらないが、各欄が receipt のどちらの field 由来かを実装から独立監査できず、将来 equality を変えた際に alias が残る。
- **nit:** 既存関数の戻り値は維持しつつ、共通の内部 validator が検証後の canonical/verified 両配列を返し、新 helper が各 origin から別々にコピーすると契約が明瞭になる。

## 総括

must-fix は重い順に次の 3 件です。

1. 検証した受領証と `artifact_refs` の受領証が同じ bytes に束縛されない。
2. schema が canonical path・identity 一意性・digest／2 配列の整合を強制しない。
3. legacy 欠落補正が knowledge-aware report では機能しない。

それ以外は、既存の verified/canonical equality、`repo_artifact` 制限、部分 lock 拒否に弱体化はなく、WAL・受領証・campaign identity・`SCHEMA_VERSION`・top-level `required` も差分上不変です。`WalRecord` は定義済みの全5 fieldを型変換せず順序どおり再構築しており、例外捕捉も knowledge helper の `AttemptTopologyError` に限定されています。非対応 campaign は WAL 検査後 `None` を返して受領証を読まず、`minItems: 1` は manifest/WAL 双方の非空制約と一致します。

pytest と provenance 検査は再実行せず、以上は静的レビューです。