## 総括

**NO-GO**。blocker は **4件**です。

実装本体は D1198 の supply/meaning 分離、`driver_integration="none"`、production caller 0、BACKOFF_FIXED だけの限定、fixture byte anchor を満たしています。

阻害要因は mutation/test 証拠です。事前登録8変異には、生存候補、別防護による mask、診断文字列だけの赤、expected node 完全集合の不足があり、DW-M02/M03/M04/M08 に従う有効な kill として数えられません。

pytest/build は指示どおり実行していません。緑とは判定していません。

## 数え上げ

| 項目 | 静的結果 |
|---|---:|
| author patch の file | 13、全て段4所有集合内 |
| author patch と dirty 実装 | `git apply --check --reverse` rc=0、完全一致 |
| gate production caller | 0 |
| supply/meaning 公開 arm | 各1、別 function・別 evidence |
| shared extractor production consumer | 2: meaning gate、sort wrapper |
| sort public wrapper production consumer | 1、さらに oracle の production caller は2 |
| source_digest adapter production caller | 1 |
| source_digest adapter test call site | 3 |
| 事前登録 expected node | 8/8実在、positive control も実在 |
| 意味上単一箇所へ対応する mutation anchor | 6/8 |
| 複合 anchor | M06、M08 |
| 新規収集 node | 23 |
| duration ledger 登録 | 0/23 |
| fixture 差分 | Options mapping 1行だけ |
| 既存 test 期待値変更・削除・skip追加 | 0 |
| driver/patch/ledger/grid/encoding変更 | 0 |
| 残り7 macroの対応済み主張 | 0 |

## Findings

1. **real / severity=high / scope内 / blocker**

   - file:line: [mutation spec:13](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/mutation-spec-preregistered.json:13)、[condition_meaning_gate.py:315](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:315)、[condition_meaning_gate.py:321](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:321)
   - 反例: M01で membership 判定だけを外しても `cache_name is None` が拒否する。missing guard 全体を外しても次の cache identity 判定が `supply-value-mismatch` で拒否し、受理集合は変わらない。M02で effective-value equality だけを外しても、wrong-RHS fixture は `cache_name != MACRO` で拒否され続ける。
   - 成果物影響: M01は SURVIVED または診断理由だけの赤、M02は現adapter下で equivalent/SURVIVED になる。D1198 supply arm の mutation 証拠を確定できない。
   - 最小fix: 原事前登録を残した erratum として、missing mapping の二層変異を登録する。route identity と value equality を別変異にし、後者には「正しい cache name、誤った effective value」の resolution を supply 公開predicateへ注入する独立testを設ける。
   - 対応mutation node: M01、M02。

2. **real / severity=high / scope内 / blocker**

   - file:line: [mutation spec:26](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/mutation-spec-preregistered.json:26)、[evolve_block.py:38](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/evolve_block.py:38)、[condition_meaning_gate.py:456](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:456)、[condition_meaning_gate.py:470](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:470)
   - 反例:
     - M03で複数markerを許して先頭を選ぶと、comment decoy testは次の directive 検査で同じ理由のまま拒否され得る。一方、sort wrapperの重複marker parameterだけが赤になる。
     - M04でcaptured holeを無視すると、登録node以外に F718、comment付き変更式、nonfinite nodeも赤になる。
     - M05の比較 bypass は F718、uniform shift、comment付き変更式を同時に赤にする。`invert` はpositive nodeまで赤にする別変異である。
     - M06のduplicate検査とmissing検査は2箇所に分かれている。
   - 成果物影響: DW-M08の完全 expected-node 集合と一致せず、実走しても KILLED でなく MISMATCH または SURVIVED になる。
   - 最小fix: 各変異をexact source replacementへ落とし、M06をduplicateとmissingへ分割する。M03からM05は全失敗nodeを登録するか、fixtureを単一理由へ再照準する。
   - 対応mutation node: M03、M04、M05、M06。

3. **real / severity=high / scope内 / blocker**

   - file:line: [mutation spec:54](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/output/insights/2026-08-27_t2018-condition-meaning-gate/mutation-spec-preregistered.json:54)、[condition_meaning_gate.py:418](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:418)、[condition_meaning_gate.py:422](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:422)、[condition_meaning_gate.py:461](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:461)
   - 反例:
     - M07のfinite checkを外しても、有限expectedとのbits比較が nonfinite を `decoded-meaning-mismatch` で拒否する。現testの赤はreason code変更だけである。
     - M08でcompile rc検査だけを外しても、binary不在により後段が `decoder-run-failed` で拒否する。公開受理集合は変わらず、別の直接helper testが追加で赤になる。timeout、rc、stderrも別anchorである。
   - 成果物影響: DW-M03/M08上、M07は diagnostic sensitivity pin、M08はmaskされた診断赤であり、behavioral killとして記録できない。
   - 最小fix: M07はdiagnostic pinへ降格するか、pointwise比較も外す二層変異を事前登録する。M08は非zero compileでも正しい実行物を生成するfixtureで「rcを無視すると受理」させ、compile/run/timeout/stderrを別変異・完全node集合に分ける。
   - 対応mutation node: M07、M08。

4. **real / severity=medium / scope内 / blocker**

   - file:line: [test_condition_meaning_gate.py:110](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:110)
   - 反例: `test_f707_missing_mapping_rejected_before_compiler` はreasonだけを確認する。supply armへcompiler解決や実行を先に追加し、その後同じ `macro-not-supplied` を返してもtestは通る。
   - 成果物影響: F707の「compiler解決より前に拒否」という必須署名がtestで保護されず、M01 evidenceにも含められない。
   - 最小fix: 同nodeで `_resolve_compiler` と `_run_process` を呼ばれたら即失敗するよう差し替え、呼出し0を固定する。
   - 対応mutation node: M01。

5. **nit / severity=low / scope内 / non-blocker**

   - file:line: [source_digest.py:1899](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/source_digest.py:1899)
   - 反例: adapterはownerをregistryから導出するが、渡された `protocol_cmake_text` がそのownerのfile由来かは検証しない。
   - 成果物影響: 現production callerは固定された silo pathをcaptureする1件だけなので、現wave evidenceへの影響はない。将来の一般consumerが `owner_protocol` をprovenance保証と誤読する余地だけがある。
   - 最小fix: docstringでcaller preconditionと明記するか、将来一般化時にowner path captureと一体化する。
   - 対応mutation node: なし。

## Refuted

- **refuted / severity=none / scope内**: D1198のAPI分離不足。
  file:line: [condition_meaning_gate.py:293](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:293)、[condition_meaning_gate.py:478](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:478)。
  反例確認: F707でsupply赤・meaning緑、F718でsupply緑・meaning赤を別公開functionで通す。
  成果物影響: 欠陥なし。最小fix: なし。対応mutation: M01、M05。

- **refuted / severity=none / scope内**: consumer refactor破壊。
  file:line: [sort_swo_oracle.py:41](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/sort_swo_oracle.py:41)、[sort_swo_oracle.py:498](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/sort_swo_oracle.py:498)、[sort_swo_oracle.py:2135](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/sort_swo_oracle.py:2135)。
  反例確認: 旧wrapperのhole bytesと3種の公開例外文言は保存され、absolute-path broker importにも sibling fallbackがある。
  成果物影響: 静的差分上は互換。未実走なので緑とはしない。最小fix: なし。対応mutation: M03。

- **refuted / severity=none / scope内**: fixture漂流。
  file:line: [test_condition_meaning_gate.py:333](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:333)。
  反例確認: supplied/F707はOptions mapping 1行だけが異なり、headerとprotocolはbyte一致。両conditionalはauthority patch targetと一致する。
  成果物影響: fixture同時変更はscope外patch anchorまたは既存B10 anchorで落ちる。最小fix: なし。対応mutation: M01、M04。

- **refuted / severity=none / scope内**: scope違反と7 macro過大主張。
  file:line: [condition_meaning_gate.py:33](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/campaign/condition_meaning_gate.py:33)、[test_condition_meaning_gate.py:347](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:347)。
  反例確認: `SUPPORTED_MACROS` はBACKOFF_FIXEDのみ、残り7を差集合で固定。production caller 0、driver integration none。author patchは所有13 fileだけ。
  成果物影響: driver、patch、ledger、grid、encoding、既存期待値への変更なし。最小fix: なし。対応mutation: なし。

- **refuted / severity=none / scope内**: test discovery閉包欠落。
  file:line: [test_condition_meaning_gate.py:380](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2018-condition-meaning-gate-codex-resume/orchestrator/tests/test_condition_meaning_gate.py:380)。
  反例確認: plain-runner signalと`__main__`があり、acceptanceはdirectory収集する。
  成果物影響: 新23 nodeのledger登録は0だが、段4が親の実走時記録としているためauthor blockerではない。coverage meta-testは未実走。最小fix: 親実走後に実測値を記録。対応mutation: なし。

## Mutation評価

| Mutation | 静的評価 |
|---|---|
| M01 | **SURVIVAL候補**。cache-name guardでmask、または診断理由だけ変化 |
| M02 | **SURVIVAL/equivalent候補**。正しいrouteではeffective equalityがadapter構成上成立し、wrong-RHSはroute guardが拒否 |
| M03 | **SURVIVAL/MISMATCH候補**。comment fixtureは後段guardで拒否継続、sort wrapper nodeが別に赤 |
| M04 | behavioral kill候補だが、少なくとも4 nodeへ波及してexpected集合不完全 |
| M05 | behavioral kill候補だが、bypassとinvertが別変異。少なくとも3 nodeへ波及 |
| M06 | duplicateとmissingが2 anchor。変異を一意に注入できない |
| M07 | **diagnostic sensitivityのみ**。公開受理集合は点比較で拒否継続 |
| M08 | **mask/diagnostic/MISMATCH候補**。timeout、rc、stderrが複合し、registered nodeだけでは閉じない |

静的結論は、現事前登録のまま有効な `KILLED` として確定可能なものは **0/8** です。変異自体は実行していません。

## GO-NO-GO

**NO-GO**

- blocker: **4**
- nit: **1**
- 実装本体のD1198/scope blocker: **0**
- mutation/test evidence blocker: **4**
- pytest/build: **未実走**
