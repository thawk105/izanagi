## 総括

**NO-GO。** S1 は run 不変の digest を使う点は正しいが、同一 root では pilot や失敗 run が protocol を永久占有し、別 root では排他できない。  
S2 の host は caller 支配外ではない。Pegasus ログインノードでは非特権 UTS namespace から hostname と FQDN を変更でき、boot ID は不変だった。  
script SHA の実 bytes と nonce の scheduler 束縛は wrapper に既存経路があり、「authority 不在」を理由に host だけへ縮小するプランは採れない。  
静的検査と非書込 probe のみ。pytest は未実走。

## 所見

### 1. 排他の lifetime と root が未裁定

- severity: high
- 根拠: `s2-plan.md:12-22,43-52` は mode・時刻を除外する一方、`orchestrator/campaign/campaign_claim.py:167-174` は release・stale 回収を持たない永久 one-shot である。claim は perf preflight より前に取られる (`orchestrator/campaign/s8b_floor_campaign.py:4720-4742,4780-4787`)。production wrapper は常に pilot (`tools/pegasus/floor_campaign.sh:962-965`) で、claim root は repo ごとの `output/claims` (`orchestrator/campaign/layout.py:40-46`) に限定される。
- **成果物影響:** 未修正なら同一 root では pilot・crash・preflight 失敗が将来の official 受理集合を永久に空にし得る一方、別 clone/root では同一 protocol が二重受理され、材料レポートと proof chain の `single_process` が一貫した意味を持たない。
- 提案する修正: 「active process 排他」か「protocol 生涯一回」かを段 4 で明示裁定する。前者なら安全な active/terminal 二相 lifecycle、後者なら pilot・失敗・将来 official の扱いを固定する。併せて canonical shared claim root と、旧時刻 identity の active job がない cutover 条件を設ける。

### 2. host 照合は scheduler authority にならず、caller が再現できる

- severity: high
- 根拠: binding と `PBS_JOBID` は同じ caller 提供 Mapping から読む (`orchestrator/campaign/reservation.py:120-175,218-251`)。プランの現実側は `socket.gethostname()` / `socket.getfqdn()` (`s2-plan.md:85-100`) だが、Pegasus ログインノードでは `/proc/sys/kernel/unprivileged_userns_clone:1` が `1`、`/proc/sys/user/max_user_namespaces:1` が `2147483647` であり、read-only probe で非特権 UTS namespace 内の両値を変更できた。その際 `/proc/sys/kernel/random/boot_id:1` は親と同一だった。計算ノードでは未実測である。
- **成果物影響:** 未修正なら direct Python caller は namespace hostname・boot ID・binding を一致させて受理され、claim と材料レポートの host 値を選べるため、proof chain は「scheduler が割り当てた host」を証明しない。
- 提案する修正: host は local drift 検査とだけ呼び、authority には live `qstat` の assigned host など scheduler 所有 source を使う。計算ノードで user/UTS namespace 可否も確認し、production API から任意 reader seam を外す。

### 3. script SHA の authority は既に存在し、nonce にも scheduler 錨がある

- severity: high
- 根拠: floor wrapper は receipt の nonce と `PBS_JOBID` を照合 (`tools/pegasus/floor_campaign.sh:406-463`)、実行中 `$0`・receipt・commit blob の SHA-256 を三者照合 (`:508-555`) してから Python を起動する (`:962-965`)。T126 にも同型検査がある (`tools/pegasus/t126_qualification.sh:658-717`)。静的 admission も receipt の nonce・job ID・script blob を検査する (`orchestrator/campaign/certified_writer_admission.py:177-204,297-381`)。
- **成果物影響:** host だけへ縮小すると wrapper 経路の受理集合は変わらない一方、wrapper を通らない reservation consumer では script/nonce が形状検査だけのまま残り、proof chain は Python leaf の照合として参照できない。
- 提案する修正: ユーザーの三項同一 wave 裁定を維持するなら wrapper、両 caller、編集面を拡張する。script は wrapper が開いた `$0` または検証済み receipt の read-only FD を必須入力にする。nonce は submitter-owned receiptだけで十分とは数えず、`qstat` の変数表示や scheduler API が実在するか確認し、無ければ明示的な再裁定で停止する。

### 4. 専用 leaf の「再検算」は caller 入力同士の一致に留まる

- severity: medium
- 根拠: `acquire_protocol_claim` 案は caller が渡す `protocol_sha256` と `freeze_sha256` から identity を再生成するだけである (`s2-plan.md:28-52`)。64 桁 hex は意味を証明せず、record と両引数を同じ run 由来 digest に同期変更すれば一致する。計画テストは record だけを timestamp identity に変えるため、この同期変異を撃たない (`s2-plan.md:156-166`)。
- **成果物影響:** 未修正なら専用 leaf を独立防壁として proof chain に引用できず、将来 caller が同期した偽 digest を渡した場合は run 単位 claim が受理され、二重計測が材料レポートや certified 選択へ到達し得る。
- 提案する修正: leaf に full-validated protocol と verified freeze、またはそれらからしか発行できない capability を渡し、内部で canonical digest と freeze の cross-field 照合まで行う。record と digest 引数を同時に run 由来へ変える変異、および floor caller が専用 leaf を実際に呼ぶことを固定するテストを追加する。

### 5. S2 の変異 kill は production の純増検出力ではない

- severity: medium
- 根拠: floor の host mismatch は wrapper が live qstat と hostname を比較して先に拒否する (`tools/pegasus/floor_campaign.sh:571-722`)。script/nonce も Python 前に拒否される (`:406-555`)。一方、計画テストは reader seam を直接供給する leaf test である (`s2-plan.md:130-190`)。
- **成果物影響:** 未修正なら変異報告が既存 wrapper の拒否を新設 Python gate の kill と誤帰属し、sanctioned floor/T126 の受理集合は不変なのに proof chain の参照だけが増える。
- 提案する修正: mutation matrix を「leaf 単体」「wrapper bypass consumer」「sanctioned end-to-end」に分ける。default hostname source を seam 無しで通すテストと、既存 wrapper を越えて初めて新 gate が拒否する実入力を事前登録する。

## 親 brief の誤り

- `brief.md:39-43`: probe が再現したのは同一 process・逐次実行・同一一時 root で異なる filename を二つ取得できることだけである。二つの PBS job や同時計測の再現ではない (`premise_probe.py:15-26`)。
- `brief.md:46-48`: binding field の存在は独立 authority の存在を意味せず、DW-O13 充足の根拠にならない。
- `brief.md:66-69`: 現行 required resume の直接拒否理由は既存 claim ではなく `allow_resume=False` (`orchestrator/campaign/s8b_floor_campaign.py:4658-4662`)。
- `brief.md:70-72`: script authority は wrapper 内に実在する。nonce も scheduler job ID に束縛された receipt chain はあり、「何も届かない」という二分法は誤り。
- `brief.md:75-78`: leaf は実 digest の authority を持たず、caller 引数間の一致しか強制しないため、「leaf が protocol 単位でない claim を拒否する」は過大表現。
- `brief.md:82-86`: 現時点では official が core と CLI で無条件拒否され (`orchestrator/campaign/s8b_floor_campaign.py:342-352,5585-5602`)、pilot は `eligible_for_refreeze=True` にできない (`:4198-4201`)。certified 選択への即時影響ではなく、pilot 材料と将来 official の防壁である。また sanctioned floor の host/script は wrapper で既に照合済みである。

## 親の実測への反証

- probe は `run_campaign`、protocol validation、reservation、wrapper、claim-root provisioning を通していない。
- 二つの claim は同じ PID・process starttime による逐次取得であり、二 job の競合や benchmark 同時実行を測っていない。
- `TemporaryDirectory` 上だけであり、Lustre/NFSv4 の `O_EXCL`、複数ノード、複数 clone/root を測っていない。
- synthetic な `"a" * 64` だけを使い、実 protocol/freeze field の安定性を測っていない。
- 旧時刻 identity と新 identity の混在、pilot が official を永久に塞ぐ lifecycle、claim 後の preflight failure を測っていない。
- 従って probe 単独から一般化できるのは「同一 root で異なる filename なら generic leaf は両方作る」までである。実 caller の欠陥自体は `s8b_floor_campaign.py:4715-4742` の静的追跡を合わせれば成立する。

## 退けた自分の疑い

- **protocol digest に run 可変 field が入る疑い:** 否定した。正規化 protocol は exact 18 key (`orchestrator/campaign/s8b_floor_contract.py:36-42,106-228`) で、時刻・PID・UUID・resume_dir・mode は無い。実 protocol の timestamp 形式 `master_seed` も凍結 field であり run clock ではない (`output/s8b-freeze/floor_protocol.json:1`)。
- **freeze digest が run ごとに変わる疑い:** 否定した。verified bytes の SHA-256 を protocol 内の SHA-256 と完全照合してから使う (`orchestrator/campaign/s8b_floor_campaign.py:4664-4679`)。
- **今日拒否される入力を受理へ広げる疑い:** 見つからなかった。S1 と host 検査は受理集合を狭め、`single_process=False` は `is_reservation_required` により従来どおり非発火 (`orchestrator/campaign/reservation.py:273-277`)。
- **現行 required contract に正当な resume がある疑い:** 否定した。登録済み組合せは `(single_process=True, allow_resume=False)` と `(False, True)` だけである (`orchestrator/campaign/env_contract.py:245-303`)。
- **Python の `sys.argv[0]` や `/proc/self/exe` から PBS script を直接取れる疑い:** 否定した。leaf は Python driver として起動される (`tools/pegasus/floor_campaign.sh:962-965`)。親 shell の FD は安定契約でなく、明示的な FD 継承が必要である。
- **live qstat が nonce を既に返す疑い:** 実在を確認できなかった。現行 parser は host・開始時刻・上限・残時間だけを抽出し (`tools/pegasus/floor_campaign.sh:593-643`)、実 qstat fixture にも nonce/Variable_List は無い (`orchestrator/tests/test_pegasus_floor_tools.py:1759-1781`)。現時点で scheduler nonce authority として数えるのは退けた。