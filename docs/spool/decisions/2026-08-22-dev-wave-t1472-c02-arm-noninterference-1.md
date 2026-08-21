---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-22
wave: dev-wave-t1472-c02-arm-noninterference
seq: 1
---

## {{D:provider-audit-id-split}}. off arm の invocation ID を provider-facing と audit-only へ分離する

**決定:** off arm の trial 実行で、provider (LLM role) へ実際に渡す invocation ID
(`_invoke()` の `invocation_id` 引数) と、journal event・run-start・terminal report・
provider artifact metadata が記録する audit 用 invocation ID を別々に構成する。
provider-facing ID は holdout に依存しない `content_digest_sha256` と中立workload定数
`OFF_NEUTRAL_PAYLOAD_WORKLOAD` から作り、audit-only ID は従来どおり実 holdout 由来の
`arm_binding_digest_sha256` と実workloadを保持する。on/swapped arm は変更しない。

**理由:**
- 8c事前登録 §4 の非干渉性は「role へ渡す payload」と「provider へ実際に送る bytes」の
  両方が真の holdout を跨いで byte 同一であることを要求する。2026-08-18の単位A/B (arm
  execution digestの導入wave) が導入した invocation ID 形式
  (`arm-{arm}.exec-{arm_binding_digest}.{workload}.g{n}.{role}`)
  はholdoutを直接埋め込んでおり、これがそのままprovider呼び出しへ渡ると、payload本体を
  中立化しても非干渉性が成立しない。段3敵対相談2レンズが独立にこの漏洩を指摘した。
- digest/workloadを単純に空文字へ置換する案は、既存の「provider payloadがinvocationの
  digestに束縛されている」という anti-tamper 検査 (単位A/Bが実装) を弱める。
  audit-only IDへ実digest/実workloadを退避し、journal/report/provider artifact metadata
  側でこれを検証し続けることで、非干渉性とanti-tamperの両方を維持する。
- off armのcontent_digest_sha256は既にholdout不変であることが実測済み (s8c_arm_inputs.py
  の凍結neutral artifactに由来) であり、provider-facing IDの構成要素として再利用でき、
  新しい概念を持ち込まずに済む。

**却下した選択肢:**
- invocation ID を「監査専用」と扱いprovider呼び出しには渡さない前提で無視する
  (段2 plan の当初案) — 実際には`_invoke()`がinvocation_idをそのままproviderへ渡しており、
  未検証の前提のまま非干渉性を主張することになる。段3敵対レンズが指摘し段4で修正した。
- provider-facing IDを完全な固定文字列にする — content_digest由来の情報を落とすと、
  off descriptorの改竄検知 (anti-tamper) が弱まる。

## {{D:c02-scope-excludes-generation2-results}}. C02非干渉性の主張をgeneration 1相当の共通payload構成に限定する

**決定:** 本waveのoff arm非干渉性実装は、`_common_payload()`が構成するworkload・
descriptor_binding・provider-facing invocation IDのholdout非依存性だけを対象とし、
generation≥2でrole payloadへ混入する実測結果依存の値 (`harness_result`のmetrics/outcome/
stop_reason、`critic_feedback`) は中立化しない。worklog・decisions・新規テストの
docstringは「非干渉性が完全に成立した」と書かず、この限定を明記する。

**理由:**
- これらの値は真のH1(rr80)/H2(rr20)ワークロードに対する実測ベンチ結果そのものであり、
  値が異なること自体は正当な現象であって実装バグではない。中立化するには適応的合成の
  機能そのものを止めるか、値を加工する必要があり、これはC02のpayload配線バグ修正の
  scopeを超える実験設計判断である。段3敵対相談 (Lens A所見1、Lens B所見3) が独立に
  この残存チャネルを指摘した。
- 8c事前登録 §4の「世代間で運んでよいものの閉じた集合」節は、この種の結果依存チャネルが
  存在すること自体は認めており (「還流を遮断したとは主張しない」)、非干渉性節とは
  別の独立した規範として扱われている。両者を混同して「非干渉性が全世代で完全に成立する」
  と主張することは、規律2/3 (正しさシグナルの誠実な報告) に抵触するリスクがある。

**却下した選択肢:**
- generation≥2の結果チャネルも本waveで中立化する — 適応的合成の機能を損なう可能性があり、
  かつT-1434の前例 (17領域を1waveに詰め込み段3で規模超過指摘、Wave A+Bへnarrow) と同型の
  scope拡大になる。ユーザー裁定を経ずに実験設計を変更しない。
- 残存チャネルの存在に触れず「非干渉性達成」とだけ記録する — 過大な主張であり、
  後続waveが誤って本系列を起動する根拠に使うリスクがある。
