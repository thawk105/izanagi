## (1)

**決定:** [推測] 「観測前分類」と「観測後導出」を別軸のまま保持し、official v2 の row-bound evidence capability が検証された場合だけ、後者を terminal `failure_reason` として認める。既存の `pre_observation_failure_reason_echo` が前者、`failure_reason` が後者なので、新しい理由 field は増やさない。core の通常経路、v1、capability なしの v2 は従来どおり分類理由との等値を要求する。

[推測] `attempt_registry_core.py` の型と関数は次へ変更する。

```python
@dataclass(frozen=True, slots=True)
class TransitionPolicy(Generic[SlotT]):
    ...
    require_terminal_reason_equals_classification: bool
    ...
    allow_terminal_reason_from_validated_evidence: bool = field(
        default=False, kw_only=True,
    )

@dataclass(frozen=True, slots=True)
class DomainProfile(Generic[SlotT, BindingT]):
    ...
    terminal_row_validator: Callable[[Mapping[str, Any]], None] | None = ...
    validated_terminal_row_validator: (
        Callable[[Mapping[str, Any], object], None] | None
    ) = field(default=None, kw_only=True)

def _assert_registry_rows_with_budget_counts(
    rows: Sequence[Mapping[str, Any]], *,
    profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT | None = None,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
    validated_terminal_evidence: object | None = None,
) -> tuple[RegistryRows, BudgetCounts]: ...

def load_attempt_registry_with_validated_terminal_evidence(
    data: bytes, *,
    profile: DomainProfile[SlotT, BindingT],
    expected_binding: BindingT,
    validated_terminal_evidence: object,
    initial_started_budget_counts: Mapping[Hashable, int] | None = None,
) -> tuple[RegistryRows, BudgetCounts]: ...

def record_attempt_terminal(
    rows: Sequence[Mapping[str, Any]], *,
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
    terminal_evidence_sha256: str | None = None,
    validated_terminal_evidence: object | None = None,
) -> RegistryRows: ...
```

[推測] 現行 `attempt_registry_core.py:1413` の echo 等値は常時維持する。`:1419` の直接理由等値は、差があり新 policy が false なら現在と同じ位置で拒否する。新 policy が true のときだけ `:1431` の null matrix、続いて validated hook を実行し、hook 成功後にだけ差を許す。capability が無い、hook が無い、hook が拒否した場合は必ず拒否する。既存 `load_attempt_registry*` の signature は変えず、capability を渡せる入口は上記 1 本に限定する。

[推測] `s8b_attempt_profile.py` では次へ置換する。

```python
def _require_sealed_s8b_v2_terminal(
    row: Mapping[str, Any],
    validated_terminal_evidence: object,
) -> None: ...
```

[推測] `make_s8b_v2_domain_profile()` は E2 の閉じた 4 語、`allow_terminal_reason_from_validated_evidence=True`、上記 validated hook を設定する。v1 factory は新 field の既定 `False` と両 validator の `None` を使う。

[推測] launcher は `seal_terminal_evidence(reservation, opened, terminal)` から未完成の `SealedTerminalEvidenceDraft` だけを得る。observation-start 後、`record_sealed_attempt_terminal(observation, draft)` を adapter へ渡し、adapter が exact `CapturedObservation` の 3 digest を補って `ValidatedTerminalEvidenceSet` を発行する。launcher は core capability を受け取らない。

**根拠:** [実測] 現 HEAD `68573078e` では echo、理由等値、null matrix、hook の順序が `attempt_registry_core.py:1413,1419,1431,1436` にある。`record_attempt_terminal()` は `:2000` で、最後に全行を再 replay するのは `:2080` である。

[実測] `s8b_attempt_profile.py:403` の v1 terminal key は 24 個、`:490` の現 v2 terminal key は 25 個で、直接評価した差集合は `measurement_ordinal` だけだった。変更後は v1 を 24 個のまま保ち、v2 terminal を 26 個として `terminal_evidence_sha256` だけを追加する。terminal 証拠文書は欠けていた `failure_reason` を加え、23 field から exact 24 field とする。

[実測] 台帳 terminal 行には既に `failure_reason` と `pre_observation_failure_reason_echo` がある (`s8b_attempt_profile.py:445`)。したがって crash 後も terminal 行から両値を区別でき、先行 classification 行との echo 等値を再検査できる。ただし観測後理由の正しさは行だけでは証明できず、`terminal_evidence_sha256` が指す canonical bytes を再読し、E1、digest、attempt binding を再導出して初めて確定する。

[実測] 直接評価では v1 profile は retryable 集合が空、理由等値が true、validator が `None` だった。現行 test source は v1 の同理由受理と異理由拒否を `test_attempt_registry_core_s8b_profile.py:2253`、validator より先の拒否を `:2322`、adapter の v1 正例を `test_s8b_attempt_registry.py:3136` で固定している。pytest は本相談では実行しておらず、緑とは数えない。

[推測] v1 では新 policy が常に false なので、`:1419` の既存条件、検査順、row bytes、旧 API が完全に同じである。したがって v1 の受理集合は 1 bit も変わらない。

**却下した案:** [推測] launcher の分類語彙を E2 全語へ変える案は、観測後にしか判明しない理由を観測前分類へ置けないため却下する。

**却下した案:** [推測] v2 で理由等値 flag を単純に false にする案は、capability なしの core 直呼びまで広げるため却下する。

**却下した案:** [推測] 全 core load API へ capability keyword を伝播する案は、adapter の中央 replay 境界 1 本で足りるため却下する。

**規律 2 の反証:** [推測] 新しく受理される status と「前理由、後理由」の組は、次の 7 組だけである。

1. [推測] `observed`: `(None, None)`
2. [推測] `retryable-failure`: `(competing_process, measurement_environment_conflict)`
3. [推測] `retryable-failure`: `(None, measurement_execution_unavailable)`
4. [推測] `retryable-failure`: `(launch_failure, measurement_execution_unavailable)`
5. [推測] `retryable-failure`: `(None, measurement_sample_incomplete)`
6. [推測] `retryable-failure`: `(launch_failure, measurement_sample_incomplete)`
7. [推測] `retryable-failure`: `(None, measurement_dispersion_exceeded)`

[推測] 全組で exact official v2 profile、E2 閉集合、null matrix、canonical evidence、row digest、attempt binding、E1 再導出が必要である。`terminal-failure`、`not-consumed`、echo 改変、E1 と違う後理由、primary や digest の不一致は増加集合に入らない。capability のない呼び手は既存 loader か `validated_terminal_evidence=None` の writer にしか到達できず拒否される。custom profile は generic core では作れても、adapter の exact profile 比較 `s8b_attempt_registry.py:319` を通らない。

## (2)

**決定:** [推測] (2-b) を採る。契約の `exec_failures` を「私有 sink が証明する実行失敗数」から「現行 campaign が `ScalePoint.notes` から導出した集約値」へ追記訂正する。実際の rep 実行成否は `repetition_evidence`、`rep_integrity_failures`、qualified throughput 列が証明するものとし、`exec_failures` に二重の役割を持たせない。

**根拠:** [実測] `_project_scalepoint()` は `s8b_floor_campaign.py:1893` で rep 証跡を検査する一方、`:1965` で `exec_failures` だけを notes regex から得る。直接評価では returncode が非 zero の 2 rep、notes 空に対して `exec_failures=0`、`rep_integrity_failures=2`、qualified throughput は空だった。

[実測] returncode 非 zero は complete 条件 `s8b_floor_campaign.py:1946` を破り、`assess_session()` は本数不足を `nonfinite_or_partial_output` にする (`s8b_floor_stats.py:127`)。campaign の precedence は `s8b_floor_campaign.py:6311`、`_finish_session()` は reason 非 nullまたは `exec_failures` 非 zeroなら median を nullにして `valid=False` とする (`:6346`)。

[実測] 現行 test source も nonzero rc を `rep_integrity_failures=1`、`valid=False`、`exclusion_class=rep_integrity_failure` として固定している (`test_s8b_floor_campaign.py:9240`)。legacy retry は最終的に session の `valid is False` を根拠に許可される (`s8b_holdout_admission.py:5734,5802`)。したがって notes 算出を維持しても、非 zero rc が valid 測定へ昇格する穴は開かない。

[推測] 証拠が弱める主張は明確である。`exec_failures` 単独では「何 rep が実際に失敗したか」を証明せず、「campaign が notes から何件と数えたか」だけを証明する。実際の失敗 rep と理由は構造化 `repetition_evidence` から再導出する。

[推測] D1113 は維持できる。issuer は exact `OpenedFloorAttempt.measurement.notes` から regex 値を再計算し、terminal builder の `campaign_record.exec_failures` と比較する。rep 成否は launcher 私有 sink と exact observation handleから独立に再導出するため、呼び手がどちらの値も選べない。

[推測] 過去の journal の意味、`excluded_reason` precedence、`valid`、retry 判定を変更せず、既存測定を書き換えない。契約 v2 の誤った強い主張だけを追記訂正するので規律 7 と整合する。

**却下した案:** [推測] (2-a) の sink 由来への変更は、同じ campaign record field の意味と一部 `excluded_reason` を過去と異なるものにし、journal schema・全 consumer・再検証規則まで改訂しなければならない一方、正しさの無効化は既存 rep integrity gate で既に達成されているため却下する。

## (3)

**決定:** [推測] 同一 Python process 内での任意コード実行、private API 呼出し、module 改変は脅威モデルに含めない。ただしその除外を保証文へ明記し、production seal の最終発行を adapter の exact observation handle 消費に限定する。test launcher は production finalizer を呼ばない別 call graph にする。

[推測] 信頼境界には次を逐語で採用する。

> 本封印は、campaign、terminal builder、計測 subprocess 出力、および crash 後に再読する台帳・receipt bytes を非信頼データとして扱い、公開 production API から与えられる値の改変、別 attempt 証拠の差替え、欠落、非 canonical 化、digest 不一致を検出する。orchestrator の Python process 内で任意コードを実行できる主体、すなわち module global の読書き、underscore API の直接呼出し、発行表への直接 insert、monkeypatch、import hook、関数または code object の置換、`object.__new__`、`object.__setattr__`、`__reduce_ex__` を実行できる主体は保証対象外である。その能力を得た時点で信頼中核そのものが侵害されたと扱い、本封印は防御を主張しない。

[推測] launcher は共通準備と production finalization を分離する。`_launch_floor_attempt()` は observation、opened、terminal を保持する私有 prepared 型までを返す。`launch_floor_attempt()` だけが固定 adapter を直接呼び、draft と exact `attempt_registry.CapturedObservation` から validated capability を発行する。`_launch_floor_attempt_for_test()` は fake recorder のみを呼び、production finalizer を参照せず、production registry object の注入も identity で拒否する。fake observation を production finalizerへ渡しても adapter の exact type、issued identity、state fingerprint 検査で落ちる。

**根拠:** [実測] 現行同型 capability は可変 table と `_new_handle()` を権威にする (`s8b_attempt_registry.py:42,258`)。現 launcher は production と test が同じ `_launch_floor_attempt()` を呼び、test 側が registry、capture、probe、authority、terminal builder を注入できる (`s8b_floor_attempt_launcher.py:723,855,879`)。現行 production wrapperも mutable `_PRODUCTION_DEPENDENCIES` を実行時に読む (`:181,875`)。

[実測] adapter には exact handle type、元 object identity、state fingerprint、attempt phase key の検査が既にある (`s8b_attempt_registry.py:280`)。また exact `CapturedObservation` は observation-start と raw output digest の確定後にだけ発行される (`:2388`)。これを最終 seal の入力にすれば、test seam の fake 型は production capability を取得できない。

**却下した案:** [推測] issuer を別 process に隔離する案は、任意同一 process コード実行を脅威に含める場合には必要だが、IPC、鍵または fd capability、crash protocol、別 process test harness を新設する規模になり、今回明示した信頼境界には不要なので却下する。

**却下した案:** [推測] immutable bytes と module-private issuer tableだけで「同一 process 攻撃も防ぐ」と主張する案は、既に直接評価で反証されているため却下する。

**規律 2 の反証:** [推測] threat scope 内の呼び手は terminal builder の status、reason、primary、campaign record を選べても、それらは比較専用であり、adapter が exact observation と canonical bytes から再導出した値だけを core へ渡す。test seam は production capability を発行できない。scope 外の任意 Python コード実行なら防壁を破れるが、そこを防いだとは主張しないため、恒真な封印保証にもならない。

## (4)

**決定:** [推測] 次 wave は leaf、launcher production finalizer、v2 profile、core の capability 専用 lower path、adapter の evidence publish/replay を縦に 1 単位で実装する。1 wave に収め、`leaf + launcher` では切らない。C2 campaign 配線と D2 consumer 束縛は含めず、D1341 に従い C1b 単独では land しない。

**根拠:** [実測] 現在の対象は core 2,160 行、profile 684 行、launcher 909 行、adapter 3,122 行である。旧 plan の見積りは production +1,228〜1,717、test +1,775〜2,465 (`s2-plan.md:423`)。同 plan は claim v4、state mode、全 load API 伝播を含んでいた (`:264,287`)。

[実測] durable measurement-generation claim は既に `mode` を保持し、reader も等値検査する (`s8b_holdout_admission.py:1703,6393`)。adapter の terminal を含みうる core load は 8 箇所だが、genesis-only load は別に特定できる (`s8b_attempt_registry.py:1841`)。したがって中央 evidence-aware loader 1 本へ束ねられる。

[推測] 3 件を落とし、(2-b) により campaign を触らない再見積りは次である。

| 面 | production | test |
|---|---:|---:|
| evidence leaf | +500〜680 | +550〜750 |
| launcher | +70〜110 | +150〜220 |
| profile + core | +85〜135 | +150〜230 |
| adapter | +220〜340 | +350〜550 |
| perf closure | 0 | +15〜25 |
| 合計 | **+875〜1,265** | **+1,215〜1,775** |

[推測] 合算は +2,090〜3,040 行で、C1a 実績 827 行の約 2.5〜3.7 倍である。規模は大きいが、旧 plan より production 上限を約 450 行、test 上限を約 690 行削り、機能境界が leaf、発行、検証、永続 replay の 4 面に閉じるため 1 wave とする。

[推測] 受入条件は public launcher を通した genuine v2 の 7 outcome 正例、capability なし直呼び拒否、全 durable replay 面の evidence 欠落・swap 拒否、v1 bytes/受理集合不変である。上限を超えた場合も半開きコードは land せず、同じ wave の未完として返す。

**却下した案:** [推測] leaf + launcher で切る案は v2 terminal が 1 行も増えず、D1114 の死んだ gate に当たるため却下する。

**却下した案:** [推測] 契約文書だけを次 wave に置く案は今回の目的である「terminal 行を書ける道」を開かないため却下する。

**却下した案:** [推測] C2/D2 まで同じ waveへ入れる案は D1341 の最終 land 単位ではあるが、今回の C1b 実装上限を越えるため却下する。

## 総括

- [推測] (1) 前分類 echo と後導出 reason を分離し、official v2 の validated evidence 専用経路だけを開く。
- [推測] (2) `exec_failures` は現行 notes 射影へ契約を狭め、実行成否は構造化 rep 証跡に担わせる。
- [推測] (3) 任意同一 process コード実行を明示的に範囲外とし、test launcher と production finalizer を分離する。
- [推測] (4) +875〜1,265 production、+1,215〜1,775 test の縦一式を次の 1 wave で作る。
- [推測] 実装可能。ただし C1b 単独では land せず、C2/D2 と同じ最終変更単位まで保持する。