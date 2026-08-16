判定は **NO-GO**。案 3 の根拠そのものを崩す blocker がある。

## 所見

### 1. AI が pin を前進させるたび、測定用の一回性 key も再生成される

- `重大度`: blocker
- `根拠`: 裁定は AI に `ccbench_pin` 更新を許している [裁定控え:24](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-floor-reseal-ai-authority.md:24)。plan は HEAD gitlink をそのまま使い [s2-plan.md:66](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:66)、片側だけ変わる組も受理する [s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:170)。実測の一回性 key は `ccbench_pin` を含む一方、`contract_sha256` と `protocol_sha256` を含まない [s8b_holdout_admission.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_holdout_admission.py:406)。静的 probe でも pin を変えると claim digest が変わり、両 SHA field が key に無いことを確認した。
- `再現の筋道`: 計測意味が同じでも commit OID だけ異なる CCBench pin `p1` を作る。`(c,p1)` を発行して測定する。次に別 OID `p2` へ前進し、未使用の `(c,p2)` を発行する。一回性 key も変わるため再測定できる。各 exact pair は一度しか使っておらず、組 index は常に緑である。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: 異なる pin ごとに `floors` を複数生成し、低い観測を選べる。保証は「AI が動かせる文字列上の exact pair ごとに、現行 namespace 内の protocol が最大 1 件」まで縮み、「同じ実験条件で測り直せない」ではない。案 2 を不要とした [裁定控え:39](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-floor-reseal-ai-authority.md:39) の前提も崩れる。

### 2. Q3 の片側交代を、plan が明示的に受理している

- `重大度`: blocker
- `根拠`: 裁定は「両成分がともに交代する」と逐語で要求する [裁定控え:49](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-16-floor-reseal-ai-authority.md:49)。既存正本も `both-components-change` である [calibration-freeze-authority-bundle-design.md:841](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/docs/calibration-freeze-authority-bundle-design.md:841)。対して plan は一方だけ変わる組を受理し、現在でも `(g1, HEAD pin)` を発行可能と認める [s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:170)、[s2-plan.md:174](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:174)。
- `再現の筋道`: 現在の active contract は g1、legacy pin は `d706650…`、HEAD pin は `511c9538…`。零引数 issuer を現在状態で呼ぶだけで `(g1,511c9538…)` が未使用組として受理される。P6 は「呼ばない」という運用規律だけで、issuer の拒否条件ではない。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: `contract_sha256` を据え置いた pin-only protocol が新規受理される。上位束の承認・発効参照を持たない片側世代が namespace に残り、Q3 と受理集合が食い違う。上位 lockstep receipt が未定義なら段 5 へ進めない。

### 3. legacy anchor の真正性が新 index 自身に束縛されていない

- `重大度`: major
- `根拠`: plan は working-tree の legacy を parse・通常 validate して anchor にする [s2-plan.md:25](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:25)、[s2-plan.md:51](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:51)。通常 validator は `master_seed` と `stock_configuration` を非空文字列としてしか検査せず [s8b_floor_contract.py:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_contract.py:154)、`wired_min_rel_floor` も範囲検査だけである [s8b_floor_contract.py:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_contract.py:194)。現行 manifest の legacy bytes 検査は hold 中に走査対象から外れる [test_frozen_artifacts.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_frozen_artifacts.py:165)。
- `再現の筋道`: read-only probe で legacy document の `master_seed` を `adversarial-seed`、`wired_min_rel_floor` を `0.000001` にしたところ、歴史 validator と current validator の双方が受理した。新 index はそれを anchor として、変更値を全 successor へ正確に継承する。既存の literal E2E pin はあるが [test_s8b_floor_campaign.py:6279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_floor_campaign.py:6279)、fixture は committed HEAD を clone する [test_s8b_floor_campaign.py:1185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_s8b_floor_campaign.py:1185) ため、issuer が読む dirty working-tree anchor と同じ bytes の検査ではない。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: `master_seed`、`wired_min_rel_floor`、`stock_configuration`、`freeze` など本来不変の値と successor の `protocol_sha256` が変わる。P2 は「可変な承認定数」から「真正性を同時に確立しない working-tree anchor」へ authority を移しただけになる。

### 4. 削除すると「未発行」に戻るため、追加専用でも履歴不変でもない

- `重大度`: blocker
- `根拠`: 新 directory の不存在は正常扱い [s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:28)。将来 artifact は manifest に登録しない [s2-plan.md:178](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:178)。create-only writer が検査するのは書込時点の同一 path の存在だけ [s8b_floor_campaign.py:704](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:704)。既裁定の履歴不変条件は全 `rev-list(HEAD)` の OID を検査する式である [calibration-freeze-authority-bundle-design.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/docs/calibration-freeze-authority-bundle-design.md:84)。
- `再現の筋道`: pair `q` の file を発行して commit する。その file、または directory 全体を削除する。scan は `q` の過去の存在を知らず、directory 不在も正常とする。issuer は同じ `q` を再び受理する。所見 3 と組み合わせれば、同じ path・同じ pair に異なる 16-field bytes を再発行できる。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: pair の状態が `occupied → absent → accepted` と戻る。過去 proof chain の path 参照は欠落し、同一 path の OID が履歴中で複数になり得る。「2 件目拒否」と「既存 bytes は追加のみ」の双方が current-tree 限定の保証へ縮む。

### 5. issuer/index が consumer authority に到達せず、「全 protocol」の index にもなっていない

- `重大度`: blocker
- `根拠`: consumer 切替は scope 外 [s1-brief.md:51](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s1-brief.md:51)。通常 campaign CLI は任意の `--protocol` path を受け取る [s8b_floor_campaign.py:5663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_floor_campaign.py:5663) 一方、測定直前の holdout authority は固定 legacy HEAD blobだけを読み、異なる document を拒否する [s8b_holdout_admission.py:376](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/s8b_holdout_admission.py:376)。さらに M-13 が列挙した `s8b_holdout_freeze.py` [s1-brief.md:31](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s1-brief.md:31) は scope 外 consumer 一覧から脱落している。
- `再現の筋道`: 新しい versioned protocol を正常発行して campaign に渡す。入口 validator は通っても、holdout authority が固定 legacy との document 不一致で拒否する。逆に legacy と同値の別 path は入口で受理されるが、組 index はその path を走査しない。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: 新 artifact は certified 測定・holdout refreeze・prediction/proof chain から到達不能な候補に留まる。現行参照値はすべて legacy のままであり、「AI が束縛を発効できる」という裁定は未実装である。候補 producer だけを land するなら、案 3 完了とは記録できない。

### 6. publish 直前の active contract 再照合は production では恒真になる

- `重大度`: major
- `根拠`: plan は `_env_contract.lookup()` を二度呼べば drift を検出できるとする [s2-plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:68)。しかし authority snapshot は PID ごとに一度 load され、その後 cache される [env_contract.py:576](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/campaign/env_contract.py:576)。既存テストも authority file を削除した後の `lookup()` が同じ object を返すことを固定している [test_env_contract_activation.py:1978](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-floor-reseal-authority/orchestrator/tests/test_env_contract_activation.py:1978)。
- `再現の筋道`: issuer process が最初に g1 を lookup する。別工程が activation を g2 へ進める。同じ process の publish 前 lookup は cache の g1 を返すため一致判定が通り、g1 pair を発行する。post-index の歴史 resolver も ever-active g1 を正当とする。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: path と document の `contract_sha256` が発行時点の active contract ではなく古い snapshot を記録する。Q3 chain と live authority の参照がずれた artifact が受理される。fresh authority receipt、安定した HEAD、または別 process による再読が必要である。

### 7. 事前登録テストは post-write と source drift の検出力を証明しない

- `重大度`: major
- `根拠`: plan は publish 前再照合と post-write full scan を防壁に数える [s2-plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:68)、[s2-plan.md:74](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:74)。しかし登録テストには、途中で source/index を変化させる例がない [s2-plan.md:132](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:132)。16-field 負例も helper 直呼びであり [s2-plan.md:148](/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/s2-plan.md:148)、production scanner がその helper を呼ぶことを証明しない。
- `再現の筋道`: (a) publish 前の二度目の source read を削除する、または (b) post-write scan を削除する。全入力を安定させた正例、pre-scan で落ちる duplicate 例、helper 直呼びの inheritance 例はそのまま緑になり得る。scanner 到達試験で `schema` 等を変えると既存 `validate_protocol` が先に拒否し、新 gate の検出力を偽装できる。
- `これを直さないと成果物のどの値・受理集合・参照がどう変わるか`: TOCTOU 後に生じた duplicate、source drift、dead inheritance call が受理される。既存 validator を通る `master_seed`、`wired_min_rel_floor`、`stock_configuration`、妥当形の `freeze` を public scan 経由で変異し、各新層の削除変異を殺す必要がある。

## 攻撃したが破れなかった点

- 零引数 public API と pair 由来 path は、呼び手が path・contract・pin・先行 protocol を直接指定する面を閉じている。
- predecessor を固定 legacy 1 本にしたため、mtime、辞書順、追加済み successor から都合のよい lineage を選ぶ自由はない。ただし legacy 自身の authority 問題は所見 3 のとおり。
- exact 18-key schema と v2 固定により、v1／未知 schema の交差受理は既存 validator が拒否する。
- 登録だけでは `contract_sha256` は動かない。`lookup()` が返すのは active activation の contract だけであり、g2 は登録済み・非活性のままでは target にならない。
- 同一 pair の並行 issuer は同じ導出 path を狙うため、atomic hard-link create-only により一方しか publish できない。
- 新 namespace 内の symlink、directory、未知 entry、誤命名を全件拒否する走査設計は閉じている。
- 既存 `write_protocol_document()` の凍結領域拒否と、人間用 `freeze_protocol()` の confirm／TTY／T-080 は変更しない限り維持される。ただし新 issuer は専用 private writer を使うため、これらは新経路の防壁には数えられない。
- `s8b_approved` から16 fieldを再導出しない判断は、承認定数を predecessor 選択器にする経路を閉じている。

## 親裁定が要る択一

1. 測り直し自由度をどう消すか。

   - 推奨: 上位 lockstep receipt を issuer の必須 authority とし、両 field の交代と bundle generation を一体で検証する。pin-only 発行は拒否する。
   - 代替: AI 可変 pair を維持するなら、案 2 相当の事前登録・全走行台帳を復活させる。
   - 現 plan の snapshot-local exact-pair 保証を採るには、「選択自由度が消える」という裁定自体の再裁定が必要。

2. anchor と追加履歴をどこで不変化するか。

   - 推奨: issuer は clean committed HEAD の anchor blob OID／SHA を上位 receipt へ束縛し、versioned path には `rev-list` 履歴不変検査と durable な issued-pair membership を課す。
   - hold がこの exact bytes 検査を禁止するなら、迂回実装せず、ユーザーの明示解除または新 authority の裁定まで issuer を停止する。

3. wave の完了範囲をどう呼ぶか。

   - 推奨: consumer resolution、holdout one-shot key、`s8b_holdout_freeze.py`、prediction seal／上位束まで含む後続設計が確定するまで public issuer を発効させない。
   - 候補 producer だけを land する場合は「dormant candidate issuer/index」であり、「案 1 + 案 3 実装完了」や「正しさ防壁が閉じた」と記録しない。

## 総括

判定は NO-GO。  
exact pair の構成要素である pin を AI が動かすたび、新しい測定一回性 key が得られる。  
したがって保証は「現行 namespace・現行 snapshot の同じ文字列 pair に最大1件」まで縮む。  
plan はさらに Q3 が禁じる pin-only pair を明示的に受理する。  
legacy anchor の worktree authority、削除後の再発行、PID cache による恒真再照合も未閉鎖である。  
versioned artifact は現行 consumer authorityへ到達せず、裁定の発効機能としては未完成である。  
post-write scan と source drift のテストには削除変異を殺す対照がない。  
上位 lockstep receipt、履歴不変 membership、consumer 結線のいずれかを scope 外にしたまま完了扱いにはできない。  
pytest・実測は行わず、静的検査と書込みなしの validator／claim-key probe のみを用いた。