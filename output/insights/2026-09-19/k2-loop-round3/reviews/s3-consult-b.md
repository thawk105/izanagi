## 1. submit-tree と投入 (P5)

参照略号: `R` = 指定 repo、`J3` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-round3`、`J2` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2746-k2-loop-round2`、`L` = `R/orchestrator/campaign/p3_s4_loop.py`、`S` = `R/tools/pegasus/p3_s4_loop_pegasus.sh`。以下は読取監査であり、投入・編集・テストは実施していない。

**B#1 — refuted: 既定 staging が clean 判定を壊すという疑い。**

`R/.gitignore:25` が既定 `job-staging/` 全体を除外する。`--staging-root` は必須ではない。渡す値は `hydrate` 出力 JSON の `.source_root` であり、cache root ではない (`tools/pegasus/README.md:315`、`fetch_third_party.py:758`)。hydrate は既存 staging にも ignored 生成物を拒否する検査を行う (`fetch_third_party.py:632`)。

成果物影響: 既定 staging の使用だけでは投入前 clean 判定も評価集合も変わらない。

**B#2 — refuted: plan の配置・投入形に既知の preflight 衝突が残るという疑い。**

`J3/plan.md:164` の `J3/submit-tree` は AI worktree container 外であり、`S:116` の拒否条件を避ける。1 回で通すための必要条件は次のとおり。

- 計算ノード `bnode*` と scheduler の必須環境、必須 4 変数、proposal、K2 4 変数が揃う (`S:17`、`S:54`)。
- HEAD は完全 SHA `a99425b66258911973785b11fd7d194884aeec64`。superproject tracked clean、CCBench は `PIN` 完全一致かつ clean (`S:214`、`S:228`)。再帰 submodule 初期化の失敗を表示だけで済ませない。
- evidence は repository 外の新規 attempt。親は mkdir だけ行い、qstat・reservation・receipt を先置きしない (`S:125`、`S:263`、`S:322`、`S:503`)。
- third-party は hydrate 成功後の pristine source。gflags/glog は policy pin と一致し、untracked を含め clean (`S:409`、`S:436`)。残り 3 source は参照可能な Git checkout、tracked clean、masstree に既存 `config.h` がない (`S:471`、`S:499`)。
- 計算ノードで Python 3.10、compiler/CMake、fresh scratch、解釈可能な qstat reservation が得られる (`S:159`、`S:188`、`S:269`)。

これらは必要条件であり、queue・ノード・build 成功の事前保証ではない。拒否されても再投入しない。`J2/setup-submit-tree.sh:32` 以降のように rc を表示するだけの glue を、そのまま成功判定として写してはいけない。plan は `:165` でこれを補っている。

成果物影響: 条件違反時は唯一の attempt を消費し、評価 0 件・場合によっては campaign 未生成となる。

## 2. campaign identity と WAL (N2)

**B#3 — refuted: 同じ campaign ID だから旧 WAL を継続・skip するという疑い。**

identity は `spec_content / ccbench_commit / search_tag / search_config / trial` の 5 key (`ident.py:212`)。round 2 原本 `campaign.lock:1` の `identity_preimage` は、pin `511c9538…`、Pegasus、K2 digest `396cd559…`、reflux on、records 100000、threads 4、grammar 1、build admission を含む。superproject HEAD・proposal 値・tree の絶対 path はこの 5 key に入らない。

新 tree の出力先はその tree の module 位置から決まる (`layout.py:42`)。旧 campaign をコピーせず、新 WAL/checkpoint が不在なら、旧 terminal 集合は読まれない。skip は当該 WAL 由来の `done` に対して行う (`loop.py:610`、`:695`)。checkpoint 不在なら `start_wall=time.time()` (`L:2553`)。`--isolate-worktree` は CCBench の変異作業木を隔離するだけで、campaign/WAL を新しくする機能ではない (`L:3046`)。

`409e13f8` 維持は静的根拠と整合する。ただし本監査では現行 builder の再計算完了を主張しない。親は短縮 ID に加え `identity_preimage` 全体を照合する。

成果物影響: fresh tree なら新評価となり、旧 state を再利用すると walltime 停止、旧 terminal WAL を移すと skip になりうる。

**B#4 — refuted: 現行 harness の差が round 2 の数値意味論を一律に変えるという疑い。**

`d2ebef7a4..a99425b66` の実差分を確認した。

- AO live 追記は `agent_record` 指定時だけ (`L:2566`)。本 job body は `--agent-inputs` を渡さない (`S:580`)。
- T-2783 は生成入力への診断追加であり、本走の停止・測定集約処理の変更ではない (`L:1237`、`:1270`)。提案値が変わる可能性は今回の観測対象。
- T-2702 の集約は round 2 に適用済み (`round2 README:46`)。今回との差分で calibrator・pipeline・critic 集約処理は変更されていない。
- T-2484 の dispatch timeout は、本走の直接 qsub → `S` → driver の経路外。`S` 自体も両 SHA 間で差分なし。

WAL の時刻・path・実測値・provenance hash の一致までは意味しない。insight には両 HEAD と実行時刻を残し、「round 2 と今回で集約規則が違う」と誤記しない。

成果物影響: round 2 の記録は有効なまま。非同時刻の差を改善・退行へ読み替える根拠にはならない。

## 3. 既知値の分岐 (P2)

**B#5 — refuted: 20 分岐でも通常の AO 取込み・材料レポートを生成できるという前提。**

取込み口は実在する `campaign.lock` と非空・非 truncated・単一 env の WAL を要求する (`L:2704`)。variant null はこの条件を免除しない。

したがって、20 で投入しない場合は次が妥当。

- `J3/materials/proposal-4.json` と入力・prompt・逐語を保存し、未評価と記録。
- C2 への AO 追記は旧 campaign 原本の変更になるので行わない。
- 空 C3 を用意しても取込み条件は満たせない。新 gate や人工 WAL を作らない。
- 通常の材料レポートは生成せず、insight に AO 未取込み・report 未生成を明記する。

これは `J3/plan.md:291` ですでに扱われている。20 以外でも AO 3 件は certified かつ continue の分岐だけ。順序は planner-4 → coder-4 → critic-3 (`plan.md:232`) であり、round 2 の planner-2 → critic-2 → planner-3 → coder-3 と同一ではない。

成果物影響: 20 分岐の正式 AO/report は 0 件。旧 campaign へ追記すれば旧 report の参照集合を変えてしまう。

## 4. AO 取込みと材料レポート (P7)

**B#6 — refuted: plan の正常分岐では受領証・digest・ref が必然的に不足するという疑い。**

検査位置は以下のとおり。

| 検査 | 実装 |
|---|---|
| stage と output-key の一致、critic の key 禁止 | `L:2710` |
| planner wrapper・役割 schema | `L:2719` |
| 入力必須 key | `L:2733` |
| knowledge digest と campaign receipt | `L:2740` |
| variant の当該 WAL 実在 | `L:2750` |
| WAL ref の当該 WAL 実在 | `L:2757` |
| critic 入力・指定 digest・campaign digest の一致 | `L:2767` |

knowledge receipt は job body が呼ぶ driver の `_prepare_knowledge_campaign` が評価前に発行する (`L:3038`、`:1622`)。正常完走後なら存在する経路である。ただし job 終了だけで存在を推定せず、取込み前に現物を見る。

旧 `wal-refs.json` や旧 critic digest をコピーすると拒否される。新 WAL から ref を再計算し、critic 入力は C3 の `s4_loop_digest.txt` の SHA を用いる。各取込みの rc を個別に確認すること。`J2/run-ingest.sh:19` 以降は失敗しても後続へ進み、末尾の成功で `.done` が成功風になるため、そのまま成功判定に使わない。

成果物影響: 誤った入力では AO が欠け、3 件前提の材料レポートと実際の参照集合が食い違う。

**B#7 — refuted: 正常分岐の source_refs は 10 件、または floor 値を補うべきという疑い。**

双射の期待側は WAL + whiteboard + AO (`layer3_report.py:327`)。今回は正常分岐で `N + 1 + 3`、WAL 5 件なら **9 件**。機序仮説 1 件を別 source として加算しない。critic 非起動なら AO は通常 2 件となる。

floor は `--output-root` 以下の `env/<env_tag>/calibration` を探索する (`layer3_report.py:938`)。対応記録がなければ within/between とも値 null、`no-matching-env-record` (`:730`)。fresh tree の実在内容を確認して報告し、旧 tree の較正値を黙って補わない。

成果物影響: 件数水増しと欠測の数値化を避け、report の参照双射と不確実性を維持できる。

**B#8 — real / should: 入力組立て script は plan が要求する補完照合を実装していない。**

`J3/plan.md:23` は receipt 正準 bytes 全体一致を求めるが、`build_round3_inputs.py:57` は digest だけを比較する。`:61` は JSON オブジェクト一致であり、docstring `:10` の「同 bytes」ではない。`:73` も短縮 campaign ID の比較だけである。production の既存 receipt 判定は bytes 全体一致 (`knowledge_manifest.py:609`)。

現物が不一致だという所見ではない。親が別途照合するか、検査済みという主張を実際の範囲へ限定する必要がある。

成果物影響: 放置すると、claim boundary を含む receipt 全体や identity 全体を検証済みと誤記し、次巡が未確認の束縛を根拠にする。

## 5. critic-3 (P6)

**B#9 — real / should: 過去 2 走の開示が、コピー手順では 1 走のまま残りうる。**

`J3/plan.md:263` は round 2 入力の各値を更新するが、過去走行の開示を 2 走へ増やす指示が明示されていない。`J2/materials/critic-input-2.json:17` は round 1 だけを開示している。

critic-3 には、少なくとも round 1 と round 2 が同じ ID の別 tree にあり、C3 の WAL/checkpoint はそれらを含まないことを明記する。両記録は `round1 README:105`、`:108` と `round2 README:33`、`:42` で確認できる。「2 走ある」を全履歴の網羅宣言にはしない。

成果物影響: 放置すると critic の履歴認識が 1 走不足し、attribution・avoid と次巡へ渡す診断が変わりうる。

**B#10 — refuted: continue だけで critic を無条件に起動し、B-4 適格と扱えるという疑い。**

今回の条件は certified かつ continue (`brief.md:68`)。`check_stop` 自体は certified を検査せず、iteration・walltime・収束・逆方向を判定する (`L:1319`)。親の certified 条件は追加の制限として記録する。critic 後の planner/coder 再起動は予算外。

`.claude/agents/critic.md:4` は Bash を持つ。入力 JSON の書込禁止文では tool 権限を除去できない。使用 role、実際の入力・prompt、非 B-4 を insight に残す。最大 1 回の終端 critic は plan の範囲だが、ユーザー逐語が critic を明示認可したとは書かない。

成果物影響: critic 非起動時は機序仮説が増えず、起動しても B-4 の受理集合には入らない。

## 6. 記録と主張限定

**B#11 — real / must-fix: critic の prompt 全文を保存する具体手順が欠ける。**

`J3/plan.md:239`、`:245` は planner/coder の prompt を指定する一方、critic の `:247` のコマンドには `--agent-prompt` がない。`:274` も入力と出力の保存だけである。AO 取込みでは prompt は任意なので、欠落しても成功する (`L:2763`)。

critic 起動前に実際の prompt 全文を固定・保存し、取込み時にもその path を指定する。新機構は不要。

成果物影響: 放置すると critic AO の prompt SHA と、次巡で診断を解釈するための親の指示全文が残らない。

**B#12 — refuted: round 2 の証拠一覧と正規化を無条件に複写すればよいという疑い。**

今回保存すべき一次資料は次のとおり (`round2 README:193`、`J3/brief.md:81`)。

- request ID、job stdout/stderr、存在する compute-result・reservation・prebuild receipt、投入・hydrate の記録。
- proposal、knowledge/診断、各役割の実入力 JSON・prompt 全文・逐語出力。
- WAL の必要射影・新 canonical refs、verdict・停止理由、AO 件数と SHA、原本の絶対 path。
- knowledge receipt・campaign lock・state・digest の原本参照と SHA、材料レポートと生成元 HEAD。
- ユーザー逐語、失敗・未投入・未取込みの分岐。

WAL/lock/digest/AO 原本は repo に複製しない。round 2 の行末正規化は実際の 2 行に対する処置だった (`README:204`)。今回も必要な場合だけ行い、原文を保持して原文/正規化後の SHA・変換内容を残す。

記録文は「**同 job の stock 対照は未実走。同時刻対照なし。非同時刻値を対照にしない**」とする。`delta_pct=null`、certified は改善の意味ではない。

成果物影響: 原本との対応と未達事項が追跡可能になり、非同時刻比較による性能主張を防げる。

## 7. 過剰と欠落

**B#13 — real / must-fix・裁定パッケージ候補: stock 未実走を完了条件から落としている。**

ユーザー逐語は同 job stock 1 本を含む (`J3/rulings/user-decision-2026-09-19.md:3`)。しかし `brief.md:12` の完了判定には stock がなく、`:57` で未実走へ変更している。`S:580` は候補 driver 1 起動だけであり、plan も原依頼未充足を認める (`plan.md:222`)。

親の provisional 裁定だけで stock 要求を履行済みにできない。候補のみの結果を部分成果として記録し、既存結線の不在と残る要求を裁定パッケージ候補へ返す。ここで launcher 設計・実装はしない。

成果物影響: 放置すると stock の観測値がない成果を、認可された pair 評価の完了として台帳・results 系列へ渡してしまう。

**B#14 — real / should: N3 の新規性と runbook 改修の扱いが広すぎる。**

`brief.md:42` の login emit 制約は新発見ではない。round 1 原本 `README:54` に CLI 拒否と production 関数直呼びが明記されている。したがって `brief.md:93` の failures 新型候補は、この事実だけでは成立しない。

また `brief.md:94`、`:106` の runbook 変更は、実走・材料記録とは別の変更面である。今回の経路差を insight に残すことで足りる。runbook 側の修正が必要なら候補として分離し、新 gate や経路改修へ広げない。

成果物影響: 放置すると既知の運用制約を新型障害として重複計上し、実走記録に不要な変更面を混ぜる。

**B#15 — refuted: plan が追加評価・再投入を要求し、AO/report を一律に落としているという疑い。**

`plan.md:191` は失敗時も再投入なし、`:289` は停止・reject・20 分岐を区別している。正常分岐の AO/report は含まれる。rulings-inbox の stock 候補も `brief.md:93` にある。

ただし `plan.md:214` 以降の stock 設計メモを、本 wave の実装許可と扱わない。20 分岐の AO/report 不在を埋める新台帳も不要。

成果物影響: 分岐どおりに実行すれば予算は増えず、未生成の成果物を捏造しない。

## 総括

- **must-fix:** B#11 critic prompt 全文の保存手順。B#13 stock 未達を含む完了判定・主張の修正。
- **should:** B#8 補完照合と検証済み主張の一致。B#9 過去 2 走の開示。B#14 N3 の新規性訂正と runbook 改修の切り離し。
- **nit:** B#5 の「round 2 と同じ順序」は不正確だが、plan の具体コマンド順は妥当。順序の呼称だけなら成果物影響なし。
- **裁定パッケージ候補:** B#13 同 job stock 対照の未充足と既存結線の不在。実装済み・認可変更済みとは扱わない。

identity/receipt の Python 再計算は PreToolUse `guard_bash` が「防護 path と不透明構文の同居は分類不能」として拒否した。原本の読取りは許可された `cat` / `jq` で行ったが、再計算成功やテスト緑は報告していない。