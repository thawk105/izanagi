結論は **NO-GO** です。実装本体と registry invariant、golden vector は概ね段 4 裁定どおりですが、CLI の新テストが実 probe と異なる tolerance・標本数・呼出系列を使っており、取得時 gate の重要な配線欠陥を検出できません。pytest は実走しておらず、以下は静的検査です。

## Registry 全走査 invariant

| 攻撃 | 判定 | 根拠 |
|---|---|---|
| 新しい自己不整合 `required` entry を追加 | **refuted** | 非既知 `(path, sha)` の `passes=False` は即座に赤になります。[test_env_contract.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:442)、[test_env_contract.py:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:459) |
| Pegasus 既知例外が直ったのに pin を消し忘れる | **refuted** | pass に反転すると `self_failures` から既知 pair が消え、exact equality が赤になります。[test_env_contract.py:456](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:456)、[test_env_contract.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:463) |
| `none` entry が後日 `required` へ変わっても検査を漏れる | **refuted** | `continue` は現在の mode が `none` の間だけです。`required` 化後は canonical 述語へ入り、さらに legacy 集合の exact 検査も反転忘れを赤にします。[test_env_contract.py:445](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:445)、[test_env_contract.py:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:466) |
| path だけ／SHA だけ一致する詐称 | **refuted** | 既知判定は pair 完全一致で、先行検査も実 bytes の SHA を照合します。[test_env_contract.py:404](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:404)、[test_env_contract.py:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:455) |
| 現 Pegasus entry の削除／registry 空集合 | **refuted** | `self_failures != KNOWN...` になり、Pegasus lookup golden も赤です。[test_env_contract.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:239)、[test_env_contract.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:463) |
| 現 linux-baremetal entry の削除 | **refuted（全 suite）／real（新 invariant 単独）** | 新 invariant 単独では緑ですが、legacy exact 集合と lookup golden が赤にします。[test_env_contract.py:223](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:223)、[test_env_contract.py:466](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:466) |

**real / nit:** `visited == set(ec.REGISTRY)` は同じ反復元から作った集合同士の比較なので恒真です。また `self_failures` は entry でなく `(path, sha)` の set であり、局所的には「exactly 1 entry」の件数を証明しません。[test_env_contract.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:439)、[test_env_contract.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:462)

現行 registry では canonical path と key-specific semantic test が alias を別途拒否するため、現在の unsafe な緑経路にはなりません。ただし、将来追加された自己整合 `required` entry の削除は、個別 inventory pin を置かなければこの全走査では検出できません。削除は fail-closed な受理集合縮小なので land blocker ではなく backlog とします。

## Golden vector の識別力

**refuted:** 段 4 S3 の未充足項目はありません。

- 奇数長、偶数長、inclusive 境界は [test_execution_guard.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:363) と [test_execution_guard.py:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:369)。
- Mapping/list/数値型不正と空列は [test_execution_guard.py:394](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:394)〜440。
- near-zero、zero、100% の tolerance 極値は [test_execution_guard.py:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:442)〜470。
- 全行に明示的 `want` があり、canonical 関数と consumer wrapper の双方を照合しています。[test_execution_guard.py:474](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:474)

平均 drift は実際に判定を分けます。[test_execution_guard.py:388](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_execution_guard.py:388) の `[100,100,130]` / 20% は、

- median 中心: 100、帯 `[80,120]` → 130 が帯外、`False`
- mean 中心の mutant: 110、帯 `[88,132]` → 100/100/130 が全て帯内、`True`

となります。直前の `[100,100,119]` は両方式とも `True` で単独では識別しませんが、130 の行が mean 置換を kill します。

## Must-fix: CLI テストの producer 代表性

**real / must-fix:** 新 CLI テストは、実 probe で load-bearing な二つの配線を検査できません。

実 probe は `cores.logical == len(samples_mhz)` の dataclass を返し、観測側 tolerance は policy 値ではないため常に `100.0` です。[env_attestation.py:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:423)、[env_attestation.py:426](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:426)、[env_attestation.py:433](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/env_attestation.py:433)。CLI はこれを指定 tolerance へ上書きする必要があります。[cli.py:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:549)

一方、テスト fixture は `logical=2` に対して 3 標本を持ち、最初から tolerance 5% です。[test_calibrator_certify.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:202)、[test_calibrator_certify.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:217)。CLI 引数も同じ 5% で、3 回の probe 呼出しすべてに同一 profile を返します。[test_calibrator_certify.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:323)、[test_calibrator_certify.py:330](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:330)

したがって次の欠陥が新テストを生存します。

1. `cli.py:551` の tolerance 上書きを削除・固定値化する。
2. gate 対象を candidate の `profile` から `static_pre`／`static_post` へ誤配線する。

実 probe 由来の placeholder 100% を使うと、現 Pegasus の中央値 2101、最大 3080.935 は帯 `[0,4202]` に入り、2% なら `[2058.98,2143.02]` で拒否される profile が受理されます。[registered artifact:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440)、[registered artifact:1484](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1484)

修正テストは、期待結果を変えずに以下を満たす必要があります。

- producer-reachable な標本数または実 `AttestationProfile` を使う。
- probe 側 tolerance を 100%、CLI 引数を別値にする。
- static-pre／dynamic-pre／static-post の clock 列を区別し、dynamic-pre だけを self-fail にする。
- 正例 publish 後に artifact の tolerance が CLI 値であることも直接 assert する。

**成果物影響:** このテスト欠落を放置して上記 regression が入ると、otherwise-qualified attempt が `accepted` となって新しい registered path/SHA を発行し、pin 更新後の `calibration_ref`／`contract_sha256`、execution receipt の受理集合、certified 選択・材料レポート・試行台帳の環境参照が 100% tolerance 側へ変わります。

なお「新テストがすべて合成入力だけ」という攻撃自体は **refuted** です。registry test は実 probe 由来の 48 標本 artifact を canonical 述語へ通しています。[test_env_contract.py:452](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:452)。不足しているのは、その実形を CLI gate の配線テストまで通す部分です。

## 主張の射程と受理集合

**refuted:** 現実装報告と新 docstring/reason code は、概ね CLI 限定を正しく表しています。

- gate は `_certify_main` の quality 判定から publish 前だけにあります。[cli.py:607](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:607)、[cli.py:629](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:629)
- 実装報告も「CLI publish のみ」と明記しています。[s5-impl.md:31](/work/1/SFC/tanab/dev-wave-jobs/t419-attestation-clock/s5-impl.md:31)
- reason `effective-clock-self-comparison-failed` は candidate 自身の失敗だけを述べ、任意の registered file admission を示唆しません。[cli.py:608](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:608)

ただし、段 1 brief の「S1 は registered/ の受理集合を狭める」は歴史的な過大主張なので、段 7 worklog へコピーしてはいけません。[brief.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/insights/2026-08-04_t419-attestation-clock/brief.md:60)。段 4 は既にこれを CLI publish 限定へ縮めています。[s4-adjudication.md:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/output/insights/2026-08-04_t419-attestation-clock/s4-adjudication.md:25)

**refuted:** 意図しない accepted→rejected 波及は静的には見つかりませんでした。

- CLI 成功 fixture は median 2400、5% 帯 `[2280,2520]` に 2390/2400/2410 が入り、従来どおり pass です。[test_calibrator_certify.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:217)
- `_valid_document()` も同じ列・tolerance で self-pass です。[test_schema_v2.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_schema_v2.py:74)
- runtime consumer の抽出前後は同じ Mapping/list/type/median/all-inclusive 実装であり、受理集合変更はありません。[execution_guard.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/campaign/execution_guard.py:182)
- `test_s8b_floor_campaign` の required fixture は CLI certify を通らず、既存のクランプ観測を consumer に渡すため従来どおり受理されます。[test_s8b_floor_campaign.py:3446](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_s8b_floor_campaign.py:3446)

accepted→rejected へ移るのは、意図された self-fail CLI candidate だけです。既に別理由で rejected だった self-fail attempt には reason が追加され、attempt JSON bytes が変わり得ますが、accepted 集合の副作用ではありません。

## 総括

- **(a) must-fix**
  - **real:** CLI の新正負例が、実 probe の `tolerance_pct=100`、標本数、3 回の profile 差を表現せず、tolerance 上書き削除または gate 対象誤配線を検出できません。[test_calibrator_certify.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_calibrator_certify.py:195)、[cli.py:551](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/calibrator/cli.py:551)。**成果物影響:** 誤配線時には self-fail candidate が accepted/published となり、pin 後の certified 選択受理集合、材料レポートの環境根拠、試行台帳の `contract_sha256`／calibration 参照が変わります。

- **(b) nit / backlog**
  - **real / nit:** `visited == set(REGISTRY)` は恒真で、削除検知を担いません。[test_env_contract.py:462](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:462)
  - **real / backlog:** self-failure を pair の set で集めるため、exactly-one-entry の件数は局所的に固定されません。現行 alias は他テストが拒否しますが、将来 entry の inventory 保存をこの invariant の保証に含めてはいけません。[test_env_contract.py:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t419-attestation-clock/orchestrator/tests/test_env_contract.py:455)

- **(c) refuted にした攻撃**
  - 新しい自己不整合 required entry、既知例外の修正忘れ、none→required、path-only／SHA-only 詐称、現 registry の空集合はすべて赤になります。
  - golden vector は段 4 S3 の全カテゴリを満たし、`[100,100,130]` が median→mean drift を実際に識別します。
  - canonical comparator 抽出による既存 runtime consumer の受理集合変化、既存 certify 正例や `_valid_document()`、S8B fixture の意図しない reject は静的にはありません。
  - 「新テストがすべて合成入力」という絶対命題は、実 48 標本 artifact を使う registry test があるため refuted です。

- **(d) 主張を縮めるべき文言**
  - 使用可: 「現行 `_certify_main` の CLI publish 候補に自己比較 gate を課す。`env_contract.REGISTRY` の参照済み entry は land 時のテストで全走査する。」
  - 使用不可: 「registered/ を守る」「registered/ への全投入を admission する」「登録済み artifact を runtime で常時検査する」。
  - tolerance の権威束縛 U-3 が閉じるまでは、「強い環境同一性 gate」ではなく「artifact 内 tolerance に対する自己整合 gate」と限定すべきです。