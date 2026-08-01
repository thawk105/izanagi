判定は **NO-GO**。親実測の「request `877172`、161 passed」は事実として受領した。こちらでは pytest・実走を行っていない。

### 所見 1 — 従量経路 5 key の deny が完全に欠落している

深刻度: **BLOCKER**

根拠: 段 6 must-fix は 5 key を空文字でも拒否し、M16/P3 を追加するよう要求している。[adjudication.md:116](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/adjudication.md:116) しかし実装の deny 集合は proxy と TLS override だけで、[claude_transport.py:30](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:30)、実際の検査も PBS/TLS/proxy だけである。[claude_transport.py:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:181) staged tree 全体にも指定 5 key は 0 hit だった。

現 provider は allowlist 再構築により 5 key 自体を子へ forward しない。だが裁定が要求したのは「forward しない」だけでなく、`source_env` に存在する run を拒否することだ。

放置した場合の成果物影響: `ANTHROPIC_API_KEY` 等を持つ run が、本来の `transport-admission-error`／`report.status=partial` ではなく role attempt へ進む。試行台帳の受理集合、report の cells/status、T-277 後の proposal・certified 候補が変わる。

推奨対応: `claude_transport.py` に 5 key の exact 集合を追加し、値の真偽ではなく `key in source_env` で拒否する。wrapper でも policy read 前に検査し、M16 と、5 key 不在時の P3 を追加する。各 key は空文字・sentinel の双方を検査し、error、`fatal_error`、journal に値が出ないことまで固定する。

### 所見 2 — `PATH` と `HOME` が実行体・認証・課金経路の未束縛 trust root のまま

深刻度: **MAJOR**

根拠: 子へ渡す共有 allowlist は `PATH/HOME/LANG/LC_ALL/TERM` のままである。[s8b_prediction_runner.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:71) provider は `source_env` を読む前に ambient `PATH` で `claude` を解決し、[claude_projected_provider.py:128](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:128)、digest は記録するだけで承認値と比較しない。[claude_projected_provider.py:131](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:131) `HOME` は存在しか見ず、空・symlink・owner・auth mode を検査しない。[claude_projected_provider.py:178](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:178)

したがって、直接 API caller が渡した `environ` と実行体解決用 PATH は一致すら保証されない。4 provider の構築中に ambient PATH または実体が変われば、同じ transport receipt で異なる executable を使える。`HOME` の差替えは subscription account、credential store、CLI 設定の差替えになる。`LANG/LC_ALL/TERM` は主に挙動・診断の drift 面で、従量経路の直接 root ではない。

放置した場合の成果物影響: 同一 receipt の planner/coder/auditor/critic が別実行体・別認証 home を使い、role 応答、proposal、report、将来の certified 選択が変わる。receipt からその差を復元できない。

推奨対応: T-242 を残余として明記するだけでは「subscription-only」を保証できない。承認済み executable digest、固定 child PATH、起動直前再照合、認証専用 HOME の canonical path/owner/mode/auth-mode witness を admission に束縛する。`LANG/LC_ALL/TERM` は probe 済み literal に正規化する。

### 所見 3 — `PBS_JOBID` は偽装可能で、adversarial witness としては無効

深刻度: **MAJOR**

根拠: `PBS_JOBID` は単に `source_env.get()` し、非空かだけを見る。[claude_transport.py:181](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:181) 空白、任意文字列、別 job ID も通る。production の `source_env` も user-controlled な `os.environ` の copy にすぎない。[p3_autonomous_workload_trial.py:1234](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1234) 一方、site 分類は `bnode[0-9]+` hostname だけで COMPUTE とし、scheduler 証拠を使わない。[site_policy.py:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/site_policy.py:29)

意味があるのは、通常運用で「偶然 bnode 名になった環境」や PBS 外の誤起動を減らす cheap witness としてだけである。hostname/env を操作できる攻撃者への attestation ではない。

放置した場合の成果物影響: UTS hostname と env を偽装した非 allocation run が `site=PEGASUS_COMPUTE` として受理され、試行台帳・report の site/job 帰属が偽になる。T-277 後は別環境の測定・certified 候補へ波及する。

推奨対応: 現実的には、PBS prologue が作る root-owned または署名済み receipt に job ID、uid、hostlist、期限を束縛し、現在 PID の scheduler cgroup と照合する。次善策は pin した `qstat` で running job・owner・exec host を検査し、kernel hostname/cgroup と結合すること。`/proc/self/environ` の再読だけでは偽装不能にならない。

### 所見 4 — redaction を実装しながら、同じ proxy 実値と job ID を receipt で平文出力する

深刻度: **MAJOR**

根拠: receipt は proxy 実値と生の `PBS_JOBID` を返す。[claude_transport.py:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:75) それが成功 provenance、[claude_projected_provider.py:347](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:347)、admission/invalid/init journal、[p3_autonomous_workload_trial.py:661](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:661)、terminal report に複製される。[p3_autonomous_workload_trial.py:929](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:929)

error redactor は同じ値を置換するが、[p3_autonomous_workload_trial.py:640](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:640)、receipt 自身が平文 sink なので秘密保護にはならない。journal は `0600` だが、report writer は明示 mode なしで作成する。[p3_autonomous_workload_trial.py:555](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:555)

正直に区別すると、committed proxy 値は既に repository 内にあり、policy URI の userinfo/query/fragment は拒否される。ただし URI path は拒否条件に無く、[claude_transport.py:147](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:147)、`PBS_JOBID` は任意文字列なので credential sentinel を入れて report へ運べる。

放置した場合の成果物影響: `attempts.jsonl`、各 role provenance、`report.json` に内部 endpoint と allocation identity が増殖する。report の配布・収集範囲が source checkout より広ければ漏洩面が拡大する。

推奨対応: report/provenance は endpoint digest、policy path/SHA、scheduler receipt digest に限定する。生値が監査上必要なら `0600` の restricted artifact 一箇所へ分離する。`PBS_JOBID` は syntax/length を制限し、report では hash 化する。policy URI は path も空固定にする。

### 所見 5 — opt-out/custom provider から receipt exact gate を迂回できる

深刻度: **MAJOR**

根拠: `_invoke()` は run-level `transport_receipt` が非 `None` の場合だけ nested receipt を検査する。[p3_autonomous_workload_trial.py:702](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:702) opt-out では provider provenance 内の `transport_receipt` を禁止せず、そのまま valid event へ複製する。[p3_autonomous_workload_trial.py:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:733) custom providers が禁止されるのも opt-in 時だけである。[p3_autonomous_workload_trial.py:1209](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1209)

さらに `_validate_transport_receipt()` は `policy_sha256` の 64hex 形状しか検査せず、実 policy bytes との一致を再検証しない。[p3_autonomous_workload_trial.py:606](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:606) journal writer 自体は generic で schema gate を持たない。[p3_autonomous_workload_trial.py:415](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:415)

放置した場合の成果物影響: flag 省略 run の `attempts.jsonl` と `report.cells[*].roles[*].provenance` に、missing/extra/偽 hash を含む forged receipt を `status=valid` で入れられる。top-level report には receipt が無く、同一 report 内で transport 帰属が矛盾する。

推奨対応: sentinel を用い、opt-out 時に provenance 内の `transport_receipt` が存在したら拒否する。event type ごとの write-side schema gateを `AttemptJournal` の前に置き、serialized journal/report の read-side validatorも用意する。policy SHA は run-level admission が読んだ bytes の digestへ束縛する。

### 所見 6 — error 診断中の例外で role attempt 行と receipt が消える

深刻度: **MAJOR**

根拠: provider 例外を捕捉した後、artifact の `is_file()`／`read_bytes()` を保護なしで実行する。[p3_autonomous_workload_trial.py:711](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:711) 同一 UID による file swap・permission drift・I/O error がここで起きると invalid event の append 前に脱出する。外側は `supervisor-error` を記録するが、その journal event には receipt がない。[p3_autonomous_workload_trial.py:873](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:873)

放置した場合の成果物影響: 本来 `role-invalid` と receipt を持つべき行が消え、`report.status=partial`、`stop_reason=supervisor-error` に変わる。certified 選択へは進まないため選択自体は fail-closed だが、再現可能な試行台帳という成果物が欠落する。

推奨対応: invalid attempt の最小行を先に確定し、artifact 診断は別の狭い `try/except OSError` で best-effort にする。`supervisor-error` にも run-level receipt を付け、診断失敗を元の role failure と置換しない。

### 所見 7 — flag 省略時の「不変」は object shape と例外分類まで含めると反証できる

深刻度: **MINOR**

根拠: opt-out provider にも常に `self.transport_receipt = None` が増えるため、`vars(provider)`・pickle・introspection の shape は変わる。[claude_projected_provider.py:186](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:186) また `dict(response.provenance)` が新たに `_invoke()` の `try` 内へ移ったため、壊れた Mapping は従来の supervisor-error ではなく role-invalid に分類される。[p3_autonomous_workload_trial.py:698](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:698)

新 import graph は増えたが、現 `claude_transport`／`site_policy` に import-time site/policy I/O は見つからなかった。公式 provider の通常成功経路については、flag off 時の child argv/env と 17-key provenance に transport field を足さない条件分岐になっている。

放置した場合の成果物影響: 通常成功 run の visible schema は維持される一方、custom provider の異常系では journal の event 種別、report の cells/stop_reason が変わる。「全 flag-off journal/report bytes 不変」は成立しない。

推奨対応: 不変主張を「公式 provider の正常成功経路における argv/env、既存17-key provenance、transport field 不在」に限定する。object shape と異常系分類は変更として記録し、決定的 clock を使った HEAD 対比を追加する。

## Receipt consumer の全列挙

| consumer | 動作 | exact gate |
|---|---|---|
| `ClaudeTransportReceipt.as_dict()` | raw receipt producer | producer 側型 |
| `ClaudeProjectedRoleProvider` | admission を読み、成功 provenance へ複製 | admission 型のみ |
| `_validate_transport_receipt()` | shape・endpoint hash・expected 一致 | あり。ただし policy bytes の独立再検証なし |
| `_invoke()` | 成功/invalid role event へ複製 | opt-in のみ。opt-out bypass あり |
| `_append_provider_init_error()` | init failure へ複製 | あり |
| `AttemptJournal.append()` | JSONL 化 | generic、gate なし |
| `_run_workload()` | role event を report cells へ複製 | upstream 依存 |
| `_finish_trial()` | top-level receipt と journal byte hash | receipt gate あり、journal hash は意味検査なし |
| proposal / campaign | planner/coder/auditor 値だけ複製 | receipt 自体が到達しない |
| tests | helper、invoke、report を検査 | production reader ではない |

proposal は receipt を落として書かれ、[p3_autonomous_workload_trial.py:1111](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1111)、campaign provenance entry も proposal path・auditor digest・variant・outcome だけである。[p3_s4_loop_trigger_gating.py:503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_s4_loop_trigger_gating.py:503) これは親が明示的に scope 外裁定した既知残余だが、T-277 後も certified outcome の proof chain に transport identity が束縛されないことは変わらない。

## 凍結波及の独立再検査

この面への到達は確認できなかった。

- `CLAUDE_ENV_ALLOWLIST` は exact 5 key のまま。[s8b_prediction_runner.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:71)
- s8b provider の env projection は同じ定数だけを使う。[s8b_prediction_runner.py:1153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:1153)
- s8b producer は従来の 8-key provenance のまま。[s8b_prediction_runner.py:1303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:1303)
- freeze consumer も exact 8 key を要求する。[s8b_selector_freeze.py:223](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_selector_freeze.py:223)
- `FROZEN_MANIFEST` は既存 output 23 件だけで、新 provider/policy/registry を含まない。[test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_frozen_artifacts.py:38)
- staged 6 file に既存 output/journal/report file は無く、既発行 bytes への直接変更はない。

したがって既発行 s8b bytes への波及はない。ただし、所見 7 のとおり「将来生成される全 flag-off journal/report bytes」まで一般化した不変性は成立しない。

## M1〜M15 の SURVIVE 予測

少なくとも次は SURVIVE 扱いにすべきである。これは静的な検出力評価で、変異実走結果ではない。

- **M10**: 現 test は同じ admission object が factory に渡ったことしか確認しない。[test_claude_transport.py:720](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_claude_transport.py:720) 引数を受け取りながら provider 内で無視して再解決する mutant は、identity assert を維持できる。run 全体で `current_site`・policy open が各1回であることを counter で固定すべき。
- **M12（anchor 次第）**: static symlink/nonregular test は pre-open `lstat` 層で拒否されるため、`O_NOFOLLOW` や post-open inode/regular-file 検査だけを削除した mutant は生存し得る。[claude_transport.py:281](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_transport.py:281) `open_fd` が別 regular file の fd を返す controlled swap test が必要。
- **M14 の同値変異**: opt-in gate の逐語削除は既存 test が検出する見込みだが、opt-out provenance への forged receipt 注入はすでに通る。mutation 契約上は別層 mask とせず、M14′として再照準すべき。

M1〜M9、M11、M13、M15 の登録どおりの局所編集には直接 assert がある。ただし M13 は受理集合の kill ではなく、機密性に対する diagnostic-sensitivity pin として別枠で記録すべきである。

## 総括

**NO-GO**

最重要 3 件:

1. 段 6 must-fix の従量経路 5-key deny、M16、P3 が丸ごと未実装。
2. `PBS_JOBID` は偽装可能で、`PATH/HOME` も実行体・認証・課金 trust root として未束縛。
3. opt-out/custom provider が exact gate を通らず forged receipt を試行台帳・reportへ入れられる。