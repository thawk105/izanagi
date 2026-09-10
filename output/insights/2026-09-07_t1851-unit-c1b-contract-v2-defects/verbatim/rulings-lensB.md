## (0)

**判定:** [推測] **機構は必要**。ただし必要なのは「v2 terminal の値を launcher が保持する実測事実から再導出し、試行 proof chain の虚偽を防ぐこと」であり、契約 v2 の full record 複製や E2 と分類理由の混同ではない。現時点では certified 到達性は 0 なので、C1b 単独では land せず、result v5・C2・D2 と同じ変更単位で初めて有効化する。

**根拠:**

- [実測] consumer は次で全数である。

  1. core replay は v2 terminal の exact 25 keyを読み、chain、slot、binding、分類 receipt、`terminal_status`、3 digest、`primary_value`、`failure_reason`、分類 echo、observation-start、時刻、schedule、process identity を検査する。[attempt_registry_core.py:1008](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1008)、[attempt_registry_core.py:1361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1361)

  2. adapter には terminal を含み得る replay が exact 8 箇所ある。予算横断、atomic old/candidate、公開 read、reserve、observation、resume、prefix replay である。[s8b_attempt_registry.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:857)、[s8b_attempt_registry.py:1623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1623)、[s8b_attempt_registry.py:1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1666)、[s8b_attempt_registry.py:1862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1862)、[s8b_attempt_registry.py:2388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2388)、[s8b_attempt_registry.py:2734](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2734)

  3. prefix consumer は terminal field を直接読まず、exact 7 keyの `freeze_sha256`、`protocol_sha256`、`schedule_sha256`、`row_count`、`chain_head_sha256`、schema 2 種だけを使う。[実測] 直接評価は `prefix_proof_keys 7`。`capture_attempt_registry_prefix()` の production caller は 0 件、`inspect_attempt_registry_prefix()` は live floor verifier からの 1 件だった。[attempt_registry_core.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:284)、[s8b_floor_stats.py:1133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:1133)

  4. `s8b_floor_stats` は result v5 の prefix proof と独立 inspector の結果だけを等値比較し、terminal の `primary_value` や理由を result session と突き合わせない。[s8b_floor_stats.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:683)

  5. holdout freeze と ratified freeze は live verifier を間接利用するが、床値自体は journal/result の session から再計算する。[s8b_holdout_freeze.py:1586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_holdout_freeze.py:1586)、[s8b_ratified_freeze.py:3261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_ratified_freeze.py:3261)

- [実測] 現行 `assemble_result()` は v4 を生成し `attempt_registry` を持たない。holdout/ratified の top-level 検査も既定 v4 を要求するため、v2 terminal から certified 成果物への現行経路は 0 件である。[s8b_floor_campaign.py:6703](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:6703)、[s8b_holdout_freeze.py:1431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_holdout_freeze.py:1431)、[s8b_ratified_freeze.py:2352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_ratified_freeze.py:2352)

- [推測] 封印なしの具体的偽装手順は、正当な reservation、classification、observation-start までは通常経路で作り、terminal builder だけが任意の出力 bytes、status、report/observation digest、primary、測り直し理由を返す、というものになる。core は形と相互整合しか見ないため、弱い validator ならその行を hash chain に追加できる。`capture_attempt_registry_prefix()` がその行を含む chain head を result v5 に載せ、live verifier、holdout freeze、ratified freeze が同じ prefix を受理する。床値の数値は journal から再計算されるので変わらないが、certified 成果物に付く「この attempt はこの理由・結果だった」という proof chain が偽装される。

- [実測] classification receipt は観測前理由と authority を固定するが観測後の実測を持たない。[s8b_attempt_registry.py:2059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2059) observation-start は phase 順と classification event を束縛するだけで、測定内容を証明しない。[attempt_registry_core.py:1341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1341)

- [実測] deferred reader は `raw_output_sha256` を再計算するが、hash 対象 bytes 自体は terminal builder が供給する。[s8b_floor_attempt_launcher.py:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:830)、[s8b_attempt_registry.py:2379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:2379) admission claim は generation、slot、attempt、campaign、manifest、run、cell、consumption を閉じるが、terminal outcome は閉じない。[s8b_attempt_registry.py:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_registry.py:1450)

- [推測] したがって封印が追加で塞ぐものは、正当に予約された attempt の terminal outcome を呼び手が差し替え、その虚偽を正しい chain headとして流す経路だけである。数値選択の防壁を二重実装するものではない。

- [実測] `rulings` の既存防壁優先基準に従って別系統モデルへ A/B を分離照会したが、それぞれ 180 秒、120 秒で timeoutし、回答は得られなかった。採用票や緑には数えていない。pytest は 0 件で、worktree は clean だった。

**却下した案:**

- [推測] 「機構は全面的に過剰」— 数値選択は既存 verifier が守るが、proof chain に虚偽の terminal fact が入る穴は残る。
- [推測] 「C1b だけ先に land」— 現行 certified consumer は 0 件であり、D1114・D1341どおり死んだ gate になる。
- [推測] 「契約 v2 の full record をそのまま複製」— 既存 holdout-safe writerと衝突し、再導出に不要な raw carrierまで新しい権威へ持ち込む。

## (1)

**決定:** [推測] E2 の 4 語は測り直し理由の構造化シグナルとして台帳に残すが、`failure_reason` には載せない。`failure_reason` は観測前 classification の exact echo、別の v2-only field `measurement_retry_reason` は封印証拠から再導出した E2 または null とする。証拠文書の outer field は exact 23 のままにし、E2 は raw facts から再導出する。v2 terminal 行だけ `measurement_retry_reason` と `terminal_evidence_sha256` を追加する。

**根拠:**

- [実測] 現在の順序は classification echo、`failure_reason` 等値、null matrix、validator である。[attempt_registry_core.py:1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/attempt_registry_core.py:1410) 観測後にしか分からない理由を `failure_reason` へ入れる限り、validator 到達前に拒否される。

- [推測] core の変更後は次とする。

```python
@dataclass(frozen=True, slots=True)
class DomainProfile(...):
    ...
    retryable_reason_field: str = field(
        default="failure_reason", kw_only=True
    )

def _assert_null_matrix(
    row: Mapping[str, Any],
    *,
    retryable_reasons: frozenset[str],
    retryable_reason_field: str,
    label: str,
) -> None: ...

def record_attempt_terminal(
    rows: Sequence[Mapping[str, Any]],
    *,
    profile: DomainProfile[SlotT, BindingT],
    freeze_id: str,
    slot_id: Hashable,
    binding: BindingT,
    terminal_status: str,
    raw_output_sha256: str,
    report_sha256: str | None,
    observation_sha256: str | None,
    primary_value: Any,
    finished_at: str,
    failure_reason: str | None = None,
    measurement_retry_reason: str | None = None,
    terminal_evidence_sha256: str | None = None,
) -> RegistryRows: ...
```

- [推測] v2 profile は `retryable_reason_field="measurement_retry_reason"`、v1 は既定の `failure_reason` とする。validator を null matrix より前へ移し、sealed evidence から再導出した値と row の `measurement_retry_reason` を等値確認してから、E2 集合への所属を検査する。

- [推測] adapter 側の入口は `record_sealed_attempt_terminal(observation: CapturedObservation, evidence: SealedTerminalEvidenceDraft) -> None` とし、reason や primary を引数にしない。durable replay は adapter が検証済み evidence 集合を閉じ込めた `_require_sealed_s8b_v2_terminal(row, *, evidence_by_digest) -> None` を構成し、core の全公開 load APIへ capability keywordを伝播させない。

- [実測] 直接評価で現行 v1 terminal は exact 24 key、v2 は exact 25 key、v1/v2 の retryable 集合はいずれも 0 件だった。[s8b_attempt_profile.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:403)、[s8b_attempt_profile.py:490](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:490)、[s8b_attempt_profile.py:532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:532)

- [推測] v1 の受理集合は変わらない。v1 event key、空 retryable 集合、`failure_reason` 等値、旧 adapter APIを維持し、新しい引数が非 nullなら v1では従来の未知引数と同じく拒否する。変更後に増えるのは、sealed evidenceを伴う official v2 terminalだけである。

**却下した案:**

- [推測] E2 を `failure_reason` に載せ、capability 時だけ等値を代替する — 観測前分類と測り直し理由を一 field に重ね、core に例外的な受理穴を作る。
- [推測] `require_terminal_reason_equals_classification` を観測前失敗だけへ緩める — 適用条件が row の自己申告に依存し、通常 core 直呼びの受理集合まで広げる。
- [推測] E2 を廃止する — proof chainから「なぜ測り直し対象になったか」が消え、規律3とD1113の構造化理由を満たさない。

## (2)

**決定:** [推測] **契約の「非 zero rc または起動失敗をすべて `exec_failures` と数える」が誤り**である。campaign が意図する `exec_failures` は runner が rep の open 時に捕捉した実行例外数、`rep_integrity_failures` は return code、counter、schema、欠損を含む証跡不完備数で、別量だが同じ rep で重なってよい。ただし notes regex は証拠の権威にせず、runner の私有 rep sinkへ構造化 `execution_failure` を追加し、campaign と封印 validatorの双方がそこから数える。

**根拠:**

- [実測] runner は `captured.open()` の例外時に `n_exec_fail` を増やし、最後に自然文 notes へ集約する。[runner.py:953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/calibrator/runner.py:953) campaign はその自然文を regex で読み戻している。[s8b_floor_campaign.py:1879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_campaign.py:1879)

- [実測] `rep_integrity_failures` は exact 6-keyの rep observationについて、return code、counter状態、missing event、index、型、throughputを独立検査して数える。[s8b_floor_stats.py:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:64)、[s8b_floor_stats.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_stats.py:471)

- [実測] 直接評価では、2 repの return code が非 zero、notes が空の入力に対し、現 campaign は `exec_failures=0`、`rep_integrity_failures=2` を返した。これは両 field が同じ量ではないことと、notes が欠ければ aggregate を復元できないことを示す。

- [推測] rep observation を exact 7-keyにし、`execution_failure` を nullまたは構造化理由として runner が書く。`exec_failures` は非 null件数、`rep_integrity_failures` は従来の完全性導出とする。notes は診断表示だけに残す。この変更は genuine runner 出力の意味を変えず、syntheticまたは破損した「return codeとnotesが不一致」の入力を fail-closedにする。

- [推測] 証拠が証明するのは「campaign が記録した aggregate が runner-owned sink の各 rep outcomeから再導出できること」であり、任意のOS履歴そのものではない。

**却下した案:**

- [推測] 契約を現行 notes regexへ合わせる — 自然文の存在を証明するだけで、実行失敗の構造化事実を証明しない。
- [推測] `exec_failures` と `rep_integrity_failures` を統合する — 実行例外とcounter・schema不完備の診断を失い、規律3に反する。
- [推測] return codeだけから `exec_failures` を数える — return codeが得られない例外や、return code正常後のparse/open失敗を落とす。

## (3)

**決定:** [推測] 封印の脅威境界は、外部 CCBench/生成 variantが返す悪意ある bytes・return code・出力と、通常のPython操作による capability内容変更、誤ったproduction callerまでを含める。一方、任意の同一process module改変、private issuerの意図的直呼び、反射操作、同一Unix uidによるregistryとvalidatorの同時改変は範囲外と明記する。issuerを別processにはせず、immutable canonical bytes、adapter再導出、test capabilityとの型分離で閉じる。

**根拠:**

- [実測] variant coder の編集面は designated C++領域へ限定され、variantは隔離 worktreeでpatch適用、build、実行される。通常経路では Python orchestrator moduleを同一processで実行しない。[agent-architecture.md:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/docs/agent-architecture.md:95)、[roadmap.md:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/docs/roadmap.md:409)

- [実測] 一方、repository実装とCCBench sourceはAIが編集・commitでき、上流pushだけが人間に残る。[ai-provenance.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/docs/ai-provenance.md:44)、[decisions.md:28469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/docs/decisions.md:28469) したがって、repo内のissuerとvalidatorを「AIから独立した権威」とは主張できない。

- [実測] hooksは直接書込みの一部だけを塞ぎ、script、別process、persistent shell、同一uidなどは開いている。[hooks/README.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/hooks/README.md:112)、[hooks/README.md:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/hooks/README.md:377) D387も同一Unix userによる意図的偽造を範囲外としている。[decisions.md:16451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/docs/decisions.md:16451)

- [推測] 別process化しても同一uid、同一repository、同じ検証codeを使う限り独立性は増えない。意図的な外部binaryのfilesystem改変まで防ぐなら、issuerだけでなくbenchmark実行を別principalまたはOS sandboxへ移す必要があり、本件の封印APIとは別設計になる。

- [推測] A-01のtable直接insertやprivate helper直呼びは「Python内で偽造不能」の根拠には使わない。ただし通常操作で発行後objectを書き換えられる穴はD406の範囲内なので、canonical bytesを唯一の実データにし、projectionを毎回再生成する。

**却下した案:**

- [推測] issuerだけを同一uidの別processへ移す — 攻撃者がmoduleとfilesystemを書ける前提では境界にならず、IPCとcrash状態だけが増える。
- [推測] 任意の同一process改変まで封印が守ると主張する — issuerとvalidatorを同じ主体が書き換えられるため成立しない。
- [推測] 外部 CCBench/variantの出力を信頼境界内とする — 規律6の本質的な未信頼入力を除外してしまう。

## (4)

**決定:** [推測] 契約 v3確定後のC1bは、leaf、launcher、profile、core、adapterを**縦の1実装単位**として作る。branch上のcheckpointにはできるが単独landはしない。result v5 producer、campaign配線、freeze/ratified consumerを完成させるC2/D2と同じland単位に置く。C1b改訂見積りはproduction約+1,000〜1,600行、test約+1,500〜2,400行とする。runnerの構造化 `execution_failure` とcampaign変更はC2側で別途見積もる。

**根拠:**

- [実測] 現行 launcher はv2を副作用前に拒否し、profileも全terminalを無条件拒否する。[s8b_floor_attempt_launcher.py:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_floor_attempt_launcher.py:508)、[s8b_attempt_profile.py:556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/orchestrator/campaign/s8b_attempt_profile.py:556) leafまたはlauncherだけではproduction terminalは1行も増えない。

- [実測] 元planの見積りはproduction +1,228〜1,717行、test +1,775〜2,465行だった。[s2-plan.md:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/verbatim/s2-plan.md:423)

- [推測] 新見積りはclaim v4、`_AttemptState.mode`、core公開API群へのevidence keyword伝播を削り、代わりにv2-only reason fieldとnull matrix分離を足した値である。設計確定前なので上限を狭く見積もらない。

- [実測] D1341は台帳writerとproof chain consumerを同一変更単位でlandすることを要求する。[decisions.md:42839](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a/docs/decisions.md:42839)

**却下した案:**

- [推測] leaf + launcherだけをC1b完了とする — moduleと早期拒否だけが増え、production効果がない。
- [推測] core/profile/adapterを別waveへ分ける — sealed APIの正例が無いまま片側の契約を固定し、再設計を招く。
- [推測] 契約文書だけで実装を無期限延期する — proof chainの既知の虚偽経路が残り、C2着手条件が決まらない。
- [推測] C1b単独をlandする — result v5 consumerが無いため、実効しない保証になる。

## 総括

- (0) [推測] 封印機構はproof chainの虚偽防止に必要だが、C1b単独では有効化しない。
- (1) [推測] `failure_reason` は観測前分類、E2は別の `measurement_retry_reason` に固定する。
- (2) [推測] `exec_failures` はrunner-owned構造化実行失敗、`rep_integrity_failures` は独立した証跡不完備数とする。
- (3) [推測] 外部出力と通常操作を脅威内、任意module改変と同一uid偽造を脅威外とし、別process issuerは作らない。
- (4) [推測] C1bは5 production面を縦1単位で実装し、C2/D2と同時landする。
- 全体の実装可否: [推測] **契約 v3への追記訂正後は実装可。literalな契約 v2のままは実装不可。**