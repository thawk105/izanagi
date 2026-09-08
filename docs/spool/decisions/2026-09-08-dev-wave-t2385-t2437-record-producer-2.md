---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t2385-t2437-record-producer
seq: 2
---

## {{D:result-evidence-producer-core-api}}. result-evidence record の producer は core API として置き、terminal WAL projection の bytes へ束縛する — production issuer への配線は含めない

**決定:** `orchestrator/campaign/reflux_result_evidence.py` に record 層の producer を新設する。
形は次の 3 関数と 1 型に閉じる。

- `derive_physical_result(*, ordered_wal_projection_bytes, build_attempt_id, ordered_verifiers, verify_result=None)`
  が `physical_result` を **3 方向**に導く。accepted = projection の terminal が `commit` で
  `verify_configs` が verifier policy の順序付き集合と exact 一致。rejected = terminal が `abort` で
  `reason == verify_result.verdict == "non-serializable"`、`verify_result` は exact `VerifyResult` で
  `integrity.clean()` が真、`total_cycles == len(anomalies) == 1`、terminal の `verify` が
  `result_to_dict()` から `trace_dir` を除いた wire snapshot と canonical bytes で同値。
  それ以外は `ResultEvidenceIssuanceRefused` で**発行を拒否する** (indeterminate、dirty integrity、
  切詰め、複数 class、空 anomaly、非 production 構造、terminal の外枠が production の 5 key
  `{variant, stage, env_tag, ts, payload}` でない root shadow、別 attempt)。**複数 class から 1 件を
  選ばない。**
- `DerivedPhysicalResult` は `ordered_wal_sha256` (projection bytes の content-addressed digest) を
  持ち、`assemble_result_evidence_record()` は record の `ordered_wal_ref.sha256` との一致を要求する。
  導出に使った projection と record が参照する projection は同じ bytes である。
- `issue_result_evidence_record()` は `ordered_wal_ref` と `execution_provenance_ref` の両参照先を
  解決してから既存の create-only writer を呼ぶ。
- witness の構造検査と class digest は `validate_witness_anomaly()` / `witness_class_sha256()` として
  同 module に置き、8c formal consumer はそれを wrapper で呼ぶ。`ArtifactError -> FC07` の変換は
  wrapper に残す。consumer の判定式・reason code・受理集合は変えない。

**production issuer への配線は本決定に含めない。** `EvalResult` は `VerifyResult` を保持せず、
設計 (`docs/phase3-8c-wiring-design.md` §3.3) が issuer と定める `run_campaign()` の最終化点、
ordered WAL projection を `wal.jsonl` から作る producer、`run_origin_trial` の production 呼び手は
いずれも存在しない。成果物は **producer core API** であり、「本番 projection が端から端まで通る」とは
主張しない。

**理由:**
- record 層で consumer を合わせる余地が無い。`constraint_sha256` は FC04 (record と ledger member)、
  FC07 (record と WAL の witness class)、FC09 (class 集合) の 3 つの等式で束縛され、ledger 自体が
  rejected に digest を必須とする。producer を書く以外に不整合を閉じる方法が無い。
- typed `VerifyResult` 単独の導出では、consumer が FC07 で落とす record を発行できる (段 3 の
  敵対相談が反例を示した)。accepted は単一 pass の結果でなく全 pass 通過後の commit で成立し、
  rejected は WAL に凍結された snapshot と同じ bytes でなければ class が一致しない。だから producer は
  terminal WAL projection を第一入力にし、typed 結果は rejected の証拠として bytes 同値を要求する。
- 導出結果と record が参照する projection を digest で束縛しないと、同じ attempt の別 projection を
  参照する record を正常発行できる (段 6 の 2 レンズが独立に指摘)。
- consumer の `_wal_field()` は同名 top-level field を payload より優先する (D1715/D1768 で維持)。
  producer が payload だけを読むと root shadow で両者が乖離する。production writer は 5 key の外枠
  しか書かないので、producer は外枠を exact に要求して乖離の入口を閉じる。consumer 側の外枠 gate は
  D1730 の別項のままにする。
- 構造検査と digest を共有するのは、式の複製が drift の温床になるためである。共有単位を digest だけ
  にすると、構造検査を経ない値に対して同じ digest が出る経路が残る。
- production 配線を含めないのは、発火条件を満たす既存の artifact path が無く (DW-G04)、
  設計 §9 が「3 条件のいずれも成立していない」と明記しているためである。無い呼び手のために
  API の形を推測で決めない。

**却下した選択肢:**
- **abort payload の dict を producer の入力にする** — 自己申告の `integrity.clean` を producer が
  再認証できず、typed 経路より受理集合が広がる。typed 経路は `Integrity.clean()` の proof surface と
  commit witness まで見る。
- **ordered WAL projection の producer (`wal.jsonl` の 1 attempt 区間からの逆関数) を同じ wave で
  書く** — source WAL 全体の digest を採ってから追記されないという保証が issuer の最終化点に依存し、
  本 wave 単独では production 実効性を確定できない。issuer 配線と同じ束で送る。
- **共有 module を新設する** — consumer の source 検査が 15 file の閉集合を pin しており、
  record 契約の所有 module に置けば足りる。
- **typed 層と wire 層の重複検査を 1 つの policy 関数へ統合する** — typed 層は proof surface まで
  見る強い条件、wire 層は consumer parity であり、役割が違う。変異の帰属は両層同時の複合変異で取る。
- **witness class の uniqueness を producer で証明する** — `total_cycles` は SCC 数であり、
  1 SCC 内の複数 simple cycle は verifier が代表 1 件へ縮約する。class の定義は D1768 のまま
  「verifier が SCC ごとに報告する代表 witness の digest」であり、uniqueness の再定義は
  ユーザー裁定へ返す。

**限界:**
- 閉じたのは record 層の producer core API までである。production issuer への配線が無い限り、
  rejected の本番 projection は端から端まで通らない。
- fixture の到達性 (accepted / rejected / 発行拒否の 3 方向) は `test_verifier.py` と同型の
  synthetic Silo source 束縛の下での値である。production の verifier 呼び出しは build に封印された
  source snapshot と commit witness を検証するため、同じ trace でも `integrity.clean()` が変わりうる。
  production 到達性は主張しない。
- class = SCC ごとの代表 witness。1 SCC に複数 simple cycle があっても 1 class として扱われる。
