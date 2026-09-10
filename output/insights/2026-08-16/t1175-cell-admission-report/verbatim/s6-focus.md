## 総括

- **NO-GO**。R1・R2・R4 は closed だが、R3 は `pending_critic_disposition.count == 1` の campaignless fallback を Layer 3 chain 単体が受理するため partial。
- producer の実 fallback は構造上 `count == 0` だが、verifier の exact fallback 述語は `0` と `1` の両方を許しており、「producer exact shape」と一致しない。
- 走 a・走 b は、現在も静的追跡上 `_write_json_atomic` へ到達する。今回テストは実走しておらず、319 passed は親の実測を事実として採用した。
- R4 正例の `_git_head` 固定は provenance seam の補完だけで、renderer、campaign admission、fresh rebuild、Layer 3 chain は実処理のまま。
- 既存テストの skip・xfail・削除や、裁定外の期待値緩和は見つからなかった。一方、M4 と再照準後の M6 は現在も他 gate に遮蔽される。

## 所見対応表

| 所見 | 判定 | 独立判定と根拠 |
|---|---|---|
| R1 | **closed** | completeness 共通 artifact-admission gate が failure の唯一性と最終配置を要求する。`orchestrator/campaign/autonomous_trial_completeness.py:2031-2046`。full coverage の `[failed, admitted]` 拒否テストも存在する。`orchestrator/tests/test_autonomous_trial_completeness.py:2757-2804`。failure がゼロなら `if failure_indices` に入らないため、正常系を巻き込まない。 |
| R2 | **closed** | disposition の `count == 1` を最終 generation の `partial-generation` event に束縛している。`orchestrator/campaign/autonomous_trial_completeness.py:1903-1919`。許容集合内だった他二状態を個別に拒否するテストがある。`orchestrator/tests/test_autonomous_trial_completeness.py:1091-1114`。 |
| R3 | **partial** | top-level の六キー、identity key 不在、空 generations、stop reason、error shape は producer と一致する。`orchestrator/campaign/autonomous_trial_completeness.py:166-189`。ただし disposition 共通述語が `count in {0, 1}` を許す。`同:151-163`。producer の fallback は `_pending_critics` を持たないため `discarded == 0` となる。`orchestrator/campaign/p3_autonomous_workload_trial.py:2141-2146,1781-1790,1826-1834`。したがって `generations=[]` かつ `count=1` という producer 不可能形が chain 単体を通る。 |
| R4 | **closed** | 正例は三 workload、build 有効、全 decision positive、disk report 実在を固定する。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2361-2465`。wrapper は保存した実関数を先に呼ぶ。`同:2379-2387`。production は実 renderer を呼び、`orchestrator/campaign/p3_autonomous_workload_trial.py:1740-1755`、chain は独立 admission と fresh Layer 3 rebuild を実行する。`orchestrator/campaign/autonomous_trial_completeness.py:2346-2401`。 |

## 走 a / 走 b の到達確認

### 走 a

**到達する。**

- coder の JSON parse 失敗は `_invoke` 内で invalid role event へ変換される。`orchestrator/campaign/p3_autonomous_workload_trial.py:1499-1528`
- cell は `outcome="coder-invalid"`、`stop_reason="role-invalid"` となる。`同:2658-2665`
- harness 前なので pending critic は作られず、active accounting は `finally` で一度だけ既存の `partial-generation` として確定する。`同:2768-2780,2785-2791`
- 正常復帰側 finalizer は `AutonomousTrialError` だけを failure decision と disposition `count=0` へ変換する。`同:1770-1846,2182-2188`
- `admission_succeeded == False` で workload loop を終了し、status は partial になる。`同:2240-2260`
- run-finish 投影、completeness、実 Layer 3 chain、journal hash 再検査の後、writer に到達する。`同:2332-2376`

### 走 b

**到達する。**

- planner/coder/auditor 後、drive 呼び出しで `KeyError('build_start')` が送出される位置は `orchestrator/campaign/p3_autonomous_workload_trial.py:2736-2752`。
- pending critic の登録前なので pending は空で、active accounting は `finally` で一度だけ確定する。`同:2768-2791`
- `_finish_trial` が supervisor-error event を追加し、既に `_partial` に置かれた cell/generation を回収する。`同:2114-2147,2485-2486`
- supervisor-error 側 finalizer が failure decision を付ける。`同:2148-2153`
- terminal event は run-finish の直前となり、completeness、chain、hash 再検査後に writer へ到達する。`同:2332-2376`

走 b は空の fallback cell ではなく、`_partial["cell"]` に保存済みの campaign identity 付き cell を使うため、今回見つけた R3 の `count=1` campaignless 穴には依存しない。

## fix による新たな破れ

新しい既存挙動 regression は確認できなかった。ただし、次の R3 残存穴は land を止める must-fix である。

- **主張:** campaignless fallback が、producer 不可能な disposition `count=1` を受理する。
- **根拠:** verifier は disposition の count を `{0, 1}` とする。`orchestrator/campaign/autonomous_trial_completeness.py:151-163`。fallback 述語はそれをそのまま利用し、`count == 0` を追加要求しない。`同:166-189`。producer fallback は空 cell から始まり pending がないため必ず `count=0`。`orchestrator/campaign/p3_autonomous_workload_trial.py:2141-2146,1781-1790,1826-1834`
- **成果物への影響:** producer が生成できない「空 generations なのに critic を一件破棄した」identity-less cell が standalone Layer 3 chain の受理集合へ入る。
- **直し方:** `_is_exact_campaignless_failure_fallback_cell` で `pending_critic_disposition.count == 0` を明示要求し、fixture の count を `1` へ変える拒否テストを追加する。

削除行はすべて確認した。既存テストで反転されたのは、裁定済みの「finalizer failure は例外送出・report 不在」から「partial report を公開」への変更だけ。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2932-3040`。production の catch は `AutonomousTrialError` 限定で、`KeyError` は伝播する。`orchestrator/campaign/p3_autonomous_workload_trial.py:1770-1775`、境界テストは `orchestrator/tests/test_p3_autonomous_workload_trial.py:3043-3063`。

## 変異登録の妥当性

| ID | 判定 | 理由・再照準 |
|---|---|---|
| M0 | 成立 | catch を戻すと report 作成前に例外送出する。一つの境界変更。 |
| M1 | 成立 | persisted report 存在と独立 admission 成功を別 fixture が撃つ。chain 直接呼び出しなので前段遮蔽なし。 |
| M2 | 条件付きで成立 | exact helper `:133-148` 自体を置換対象にするなら単一理由。completeness の呼び出し箇所だけを緩める曖昧な anchor は避けるべき。 |
| M3 | 成立 | run-finish と report の不一致は `:1272-1282` だけで拒否される。 |
| M4 | **遮蔽・等価** | coverage の最終配置条件 `:1739-1750` を外しても、先行する共通 gate `:2033-2044` が同じ非最終 failure を拒否する。M9 と統合して共通 gate へ再照準するか、M4 を「正当な最終 failure suffix allowance を削除する過剰拒否変異」へ変更する。 |
| M5 | 成立 | producer だけ complete にすると先行 artifact gate `:2045-2046` が一理由で拒否する。 |
| M6 | **なお遮蔽・等価** | producer と `_check_status_projection` の二層を同時に外しても、artifact gate `:2045-2046` が failure＋complete を先に拒否する。producer `:2251-2259`、artifact gate `:2045-2046`、status projection `:1791-1799` の三箇所同時変異へ再照準する。 |
| M7 | 成立 | direct finalizer test が `KeyError` の伝播だけを固定する。 |
| M8 | 成立 | disposition を残さなければ exact disposition gate `:2017-2024` で拒否される。 |
| M9 | 成立 | full coverage の completeness 単体入力なので、共通最終配置 gate だけが拒否理由になる。 |
| M10 | 成立 | `generation-complete` は一般 state 閉集合には含まれ、R2 の exact 束縛だけで落ちる。 |
| M11 | 成立 | `pending-pre-invoke-failure` も同様に R2 の exact 束縛だけで落ちる。 |
| M12 | 成立だが不足 | null key と余剰 descriptor は exact fallback gate 一理由で落ちる。ただし `count=1` の生存変異が未登録。新しい M14 として追加すべき。 |
| M13 | 成立 | admitted cell の残存 metadata により exact fallback gate 一理由で拒否される。 |
| P1 | 正例として成立 | `_git_head` 以外は実 renderer・実 admission・実 fresh rebuild・実 chain。正常三 workload を過剰拒否しないことを固定する。 |

## 反証された懸念

- R1 の最終配置 gate が failure ゼロの正常系を拒否する懸念は成立しない。配置検査は `failure_indices` が非空の場合だけ発火する。`orchestrator/campaign/autonomous_trial_completeness.py:2033-2046`
- R4 が chain を no-op 化した恒真正例という懸念は成立しない。wrapper は実関数の成功後にだけ記録する。`orchestrator/tests/test_p3_autonomous_workload_trial.py:2379-2387`
- `_git_head` 固定は renderer の他検査を飛ばさない。renderer は実 campaign admission から report を構築して書き、chain は別途 fresh rebuild と完全比較を行う。`orchestrator/campaign/layer3_report.py:416-532,624-645`、`orchestrator/campaign/autonomous_trial_completeness.py:2085-2140,2389-2401`
- production が `Exception` 全般を admission failure へ倒す懸念は成立しない。catch は `AutonomousTrialError` 限定。
- 走 a・走 b の accounting 二重確定も成立しない。どちらも pending 登録前に止まるため、finalizer 内の pending loop は回らない。