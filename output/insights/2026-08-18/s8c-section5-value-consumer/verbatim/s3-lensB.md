# 所見

静的検査のみ。pytest は実走していない。

## C07 の実体を値セル validator と同一視している

- 深刻度: must-fix
- file:line: `brief.md:59`、`docs/phase3-8c-preregistration.md:231`、`orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:268`
- 具体例: C07 は現在 `machine_checkable: false`、`s8c_result_judge.py` は未存在で、evaluator も `FLOOR_JUDGE_CONSUMER_UNDEFINED` を返す (`s8c_preregistration_evidence.py:1846`)。値セルを正しく受理しても、完全 block、n exact 一致、3 表、judge は実装されない。
- 成果物影響: production の `effective` は false のままで、certified 選択・公式 report・試行台帳への受理は増えない。
- 代案: 本 wave は parser 層だけの必要条件と明記し、C07 contract、judge、manifest/observations を別の裁定パッケージへ送る。

## DECIDER_VERSION と generation record の scope 外指定が矛盾する

- 深刻度: must-fix
- file:line: `brief.md:42`、`s2-plan.md:274`、`docs/phase3-8c-preregistration.md:292`、`orchestrator/campaign/s8c_preregistration.py:50`
- 具体例: `{"n":"two"}` 等を従来 `FILLED` から `INVALID` へ変えるのは受理集合と拒否理由の変更である。現行は `s8c-decider/v3` と g7 record に束縛されている。
- 成果物影響: v4 と新 generation record を発行しないまま land すると、旧 v3 契約のまま新しい受理意味を使うことになり、発効判定・effective 参照が不正になる。
- 代案: 段4で「v4 + 新 record を追加」か「明示的な人間裁定で bug fix の版扱いを定義」のどちらかを選ぶ。無裁定の v3 維持は不可。

## `sd_max=-0.0` は 8b 制約上は受理可能

- 深刻度: must-fix
- file:line: `s2-plan.md:63`、`s2-plan.md:112`、`docs/phase3-8b-descriptor-design.md:472`
- 具体例: `sd_max` は有限の非負値なので、canonical JSON の `-0.0` は数値的に 0 であり非負。計画は negative zero を拒否する。
- 成果物影響: 正当な閾値が `INVALID` となり、§5 field の受理集合と `effective` が不必要に縮小する。
- 代案: `delta_min` の `-0.0` は正値違反として拒否し、`sd_max` の `-0.0` は 0 として受理する。

## unit / direction の意味を非空文字列だけでは検証できない

- 深刻度: must-fix
- file:line: `s2-plan.md:50`、`s2-plan.md:53`、`docs/phase3-8b-descriptor-design.md:469`
- 具体例: `direction:"banana"`、`unit:"?"`、または `" on-minus-off "` は非空文字列として通るが、どちらの構成を引くか、観測値の単位かを固定していない。
- 成果物影響: `FILLED` として発効し、judge が差の向きを逆に解釈すると official_status、certified 選択、report の結論が反転し得る。
- 代案: 固定語彙を validator で検査するか、値セルは構文だけに留め、judge が result の単位と subtraction direction を exact 照合して不一致を判定不能にする。

## P4 の「fail-open」は本文と逆

- 深刻度: must-fix
- file:line: `brief.md:74`、`brief.md:75`、`s2-plan.md:100`
- 具体例: 見出しは fail-open だが、本文と計画は対象欄消失時に `section5-validator-field-missing` で fail-closed としている。現行 activation は parser error を握り潰して空 findings にする (`s8c_preregistration.py:1676`)。
- 成果物影響: fail-open と解釈して未登録欄を generic `FILLED` にすると、再凍結後に未検証値が `effective=True` となり得る。
- 代案: 見出しを fail-closed に直し、欄消失を production report 上で構造化された invalid finding または専用 error として保持する。

## 欄消失の reason_code が ActivationReport から消える

- 深刻度: should-fix
- file:line: `s2-plan.md:14`、`s2-plan.md:66`、`orchestrator/campaign/s8c_preregistration.py:1680`、`orchestrator/campaign/s8c_preregistration.py:1727`
- 具体例: `PreregistrationError` は `activation_report_at` で破棄され、`section5_findings=()`、`freeze_reason_code="valid"` のまま `effective=False` になり得る。
- 成果物影響: effective は止まるが、report・台帳に「validator field missing」の参照が残らず、原因追跡の reason が欠落する。
- 代案: `ActivationReport` に parser reason を保持する専用欄を追加するか、対象名の synthetic `INVALID` finding を返す。

## P5 の nonfinite reason は現行順序では到達しない

- 深刻度: should-fix
- file:line: `s2-plan.md:62`、`s2-plan.md:109`、`orchestrator/campaign/s8c_preregistration.py:815`
- 具体例: `delta_min:1e309` は `_canonical_bytes(... allow_nan=False)` で先に失敗し、`section5-params-delta-min-nonfinite` ではなく `invalid-json` になる。`NaN` も同様に field validator へ届かない。
- 成果物影響: status は INVALID のままだが、report の拒否理由が field-specific でなく generic になる。
- 代案: generic `invalid-json` を正式仕様にするか、非有限数だけは field path を保持して専用 reason を返す。

## M9 の mutation literal が現コードと不一致

- 深刻度: nit
- file:line: `s2-plan.md:260`、`orchestrator/campaign/s8c_preregistration.py:1728`
- 具体例: 計画は旧式を `any(...)` としているが、現コードは `all(...)`。その mutation は適用不能である。
- 成果物影響: certified 値は変わらないが、INVALID finding が effective を止めるという防壁の mutation 証拠を偽って記録できる。
- 代案: 現行逐語に合わせて mutation を登録し直す。

## 並行 wave の merge 面が実際に衝突する

- 深刻度: should-fix
- file:line: `brief.md:6`、`brief.md:16`、`s2-plan.md:7`、`s2-plan.md:72`
- 具体例: 本 wave は `_parse_section5`、`_classify_section5_value`、validator table を編集し、t1363 も §5 別欄の consumer を追加する設計である。t1352 は同じ parameter semantics を judge で再利用する必要がある。現時点の両 sibling worktree は同じ HEAD で clean だが、設計上の衝突面は同じである。
- 成果物影響: merge で一方の table entry や schema が落ちると、予算欄または判定欄が誤って `FILLED` となり、effective と certified 受理集合が変わる。
- 代案: parser/router の所有者を一 wave に固定し、各欄 wave は独立 validator module と test だけを追加する。共有 schema は judge と parser が同じものを読む形にし、table assembly は親が一度だけ統合する。

## 親の実測値の一般化には境界がある

- 深刻度: should-fix
- file:line: `brief.md:36`、`brief.md:34`、`brief.md:56`
- 具体例: 実行可能な `_classify_section5_value` の pin は現状定義・呼出しだけで、過去 insight の記述 (`output/insights/2026-08-05_t327-prereg-activation/s6-rev1.md:115`) は executable pin ではない。fixture は `_markdown` 一箇所 (`test_s8c_preregistration_core.py:66`) に集約されている。
- 成果物影響: 現在の8c結果 bytes は変わらないが、v3 pin と future activation semantics まで「pin 無し」「値不変」と一般化すると、版更新漏れと将来の effective 判定差を見逃す。
- 代案: 「現行 executable pin は無い」「filled fixture の変更点は一箇所」「現存する8c測定成果物は無い」と限定して記録する。

# 層の棚卸し (scope 内 / scope 外 / 裁定パッケージ候補)

### scope 内

- 値セル parser: canonical JSON の後段で対象欄だけを検証する (`s8c_preregistration.py:759`)。
- 欄名 dispatch と validator key の meta-test。
- 既存 activation consumer の回帰確認 (`s8c_preregistration.py:1727-1758`)。conjunction 本体の新設ではない。
- fixture の target 欄だけの正例化。`_markdown` 一箇所で足りるという実測は狭い意味では real。

### scope 外

- evidence contract C07 の `machine_checkable` と evaluator registry。現状 C07 は未検査 (`s8c_preregistration_evidence_contract.v1.json:294-301`)。
- `s8c_result_judge.py` 本体、完全 block、対差の平均・標本 SD、3 表、`official_status`。
- manifest schedule row と observations schedule index の完全対応、および全 cell の n exact 一致。
- 累積 bench 秒 consumer、trial registry、結果から certified selector へ至る acceptance。
- docs、evidence contract、generation record の再凍結。

### 裁定パッケージ候補

1. parser を必要条件として land し、C07 は未充足、実走・certified 受入は不可と明記する。
2. C07 を実装する別 wave として、contract の C07 更新、judge、manifest/observations binding、3 表、production acceptance を一体で裁定する。
3. 受理形を exact object に凍結するか、8b の意味制約だけを検査するかを明示裁定し、意味変更なら v4 generation record を発行する。

# (P1)〜(P5) の評価

## (P1) 受理形

- 判定: 部分的に real、exactness は未裁定
- 深刻度: should-fix
- file:line: `brief.md:67`、`s2-plan.md:46`、`docs/phase3-8b-descriptor-design.md:466`
- 具体例: H1/H2 ごとに n・delta・sd が異なる object は表現できるが、8b は root exact 2 key、block exact 5 key、追加 metadata の拒否までは凍結していない。H1/H2 を配列要素で表す canonical JSON は拒否される。
- 成果物影響: 将来の正当な値表現が `INVALID` となり、field の受理集合と effective が縮小する。
- 代案: exact schema を採るなら 8c 固有の versioned representation として裁定し、そうでなければ必須意味フィールドと非権威 metadata の境界を定義する。

## (P2) 制約

- 判定: refuted
- 深刻度: must-fix
- file:line: `brief.md:69`、`s2-plan.md:50`、`docs/phase3-8b-descriptor-design.md:469`
- 具体例: `n` の exact 一致を parser に混ぜていない点は正しい。反面、`sd_max=-0.0` を過剰拒否し、unit/direction は非空だけで意味を検証していない。
- 成果物影響: 正当な `sd_max` は拒否され、不正な direction/unit は発効し得るため、受理集合と公式判定の両方を誤らせる。
- 代案: zero の符号を8bどおり扱い、n exact は manifest/judge、unit/direction の実値整合は judge の責務として分離する。

## (P3) dispatch

- 判定: field isolation は real、並行拡張案は refuted
- 深刻度: should-fix
- file:line: `brief.md:72`、`brief.md:73`、`s2-plan.md:9`
- 具体例: exact field name で対象欄だけを選ぶ方針は妥当だが、「兄弟 wave が同じ table に entry を足す」は t1363 と同一編集面になる。
- 成果物影響: entry の欠落や重複で別欄の validator が未接続となり、effective と certified 受理集合が変わる。
- 代案: table の所有者を親側の統合 commit に限定し、各 wave は独立 validator と負例だけを提供する。

## (P4) 欄名消失

- 判定: fail-closed の本文は real、見出しの fail-open は refuted
- 深刻度: must-fix
- file:line: `brief.md:74`、`brief.md:75`、`s2-plan.md:100`
- 具体例: 欄名 hash の変更だけで旧 generation は無効化されるが、新 generation で欄名が認可された後に table key が古いままだと、fail-open 実装は generic `FILLED` を許す。
- 成果物影響: 未検証欄が `effective=True` となり、certified 選択・report・台帳に入る可能性がある。
- 代案: 用語を fail-closed に統一し、現行 doc の欄名集合との一致を parser と meta-test の両方で検査する。

## (P5) reason_code

- 判定: schema 違反については real、parser error と欄消失は不十分
- 深刻度: should-fix
- file:line: `brief.md:77`、`s2-plan.md:57`、`orchestrator/campaign/s8c_preregistration.py:821`
- 具体例: root、block、n、range の reason は分離できるが、nonfinite JSON は `invalid-json` に潰れ、field missing は ActivationReport に残らない。
- 成果物影響: 受理 status は fail-closed のままだが、report・台帳の原因参照が generic または空になる。
- 代案: parser-level error と field-level constraint error を明確に区別し、production report が常に追跡可能な reason を持つことをテストする。

## 総括

最大の危険は、値セル validator を前提条件7の充足と誤認することです。  
段4では「parserのみでC07未充足のまま進める」か「contract・judge・manifest・v4 recordまで含める」かを択一で裁定すべきです。  
同時に `sd_max=-0.0` の過剰拒否と unit/direction の意味不足を修正対象にしてください。  
並行 wave は共有 table の所有者を一つに固定し、親が統合面を解決すべきです。