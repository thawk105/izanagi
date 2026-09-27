# Phase 3 silo-function-policy Runbook — 関数方策の自律ループの実走手順 (planner なし、Model Y 駆動)

**位置づけ:** 軸 `silo-function-policy` (D2214) の段階 F 以降で、実 LLM (`coder-v4-autonomous-policy` または
`coder-v4-autonomous-policy-ir` / `auditor` / `critic`) をメインセッションが spawn し、機械部分
(`orchestrator/campaign/p3_s4_loop_policy.py`) に proposal を file で渡す実ループ。
`docs/phase3-s5-sort-runbook.md` (sort 軸) の兄弟文書だが、**planner を使わない** (D2214 決定 8、
手順書 `docs/axis-onboarding.md` §3 E の例外)。設計の正本は D2214 と
`output/insights/2026-09-21/silo-function-synthesis-space/README.md`。本書は運用手順だけを持つ
(設計判断・完了状況は書かない — 正本は worklog 末尾と phase3.md)。矛盾があれば正典が勝つ。

---

## 0. 実走前ゲート (すべて満たすまで駆動を始めない)

1. **fresh session である** — 新しい role はセッション開始時にだけ登録される。Agent の利用可能型に
   `coder-v4-autonomous-policy` (C++ 形) または `coder-v4-autonomous-policy-ir` (IR 形)、`auditor`、`critic`
   が並ぶこと。
2. **計算ノードの投入経路** — `tools/pegasus/p3_s4_loop_pegasus.sh` の方策 mode
   (`IZANAGI_S4_POLICY_MODE=stock|pair|replay`、段階 F で追加) を親が `qsub` する。qsub の例と env は
   `tools/pegasus/README.md` の §7 (方策 mode) が正本。build・verify・bench は計算ノードだけで行い、
   login node では build しない。
   **submit checkout を 1 本だけ使う。** AI worktree 容器 (`.claude/worktrees/`・`.codex/worktrees/`) の外に
   detach checkout を 1 本作り (submodule 初期化・third-party の hydrate・`git worktree lock`)、stock job・
   login 側の (a)〜(e)・pair job をすべてその checkout で**直列に**行う。campaign dir はその checkout の
   `output/` 配下にでき、login と計算ノードが同じ campaign を指す。同じ campaign の操作を並行させない。
3. **submodule が pinned-clean** — `external/ccbench` の HEAD が `p3_s4_loop_policy` の参照する
   `axis_silo_function_policy.PIN` (= `pin.CURRENT_PIN`) と一致し、tracked clean。値は `pin.py` が正本で、
   ここに literal を書かない。
4. **test 緑** — 本 driver と role 登録簿の test (`orchestrator/tests/test_p3_s4_loop_policy.py`・
   `test_silo_policy_ir.py`・`test_codex_agents.py`) を含む受入が緑。
5. **計算の見積りと確認** — 1 iteration は build・legacy verify・性能構成 verify (較正 write-heavy 動作点)・
   bench を含む。投入前に job Elapse の実測単価で見積もり、図 1 枚あたりの node 時間を示し、検査込みの
   タスク合計が 2 node 時間以上ならユーザー確認 (D2212 項 4)。
6. **形を 1 つに決める** — 1 系列は C++ 形 (`--form cpp`) か IR 形 (`--form ir`) のどちらかだけで回す。
   形は search_config に焼かれ、形ごとに別 campaign になる。

---

## 1. 1 iteration の駆動プロトコル (メインセッションが回す)

ループ主導権はメインセッション。driver は LLM を spawn しない。planner 段は無い。

**共通引数:** 計算ノードで回す系列では、login 側の (a)・(c)・record-reject にも `--campaign-env pegasus` を付ける
(計算ノードの job body は同じ値で呼ぶ)。付けないと login の履歴と計算ノードの評価が別 campaign に割れる。
計測する操作 (stock・run・replay) は、実行 site の契約と `--campaign-env` が食い違えば実行前に拒否される。

### (0) 初回だけ: stock の baseline を測る
job body の `IZANAGI_S4_POLICY_MODE=stock` を 1 job 投げる (driver は `--stock-baseline`)。stock は
CCBench 原型 source (方策 patch なし) と方策 flag を除いた genome で、性能動作点・verify 構成は loop と同じ。
結果は loop とは別の campaign (`evaluation_purpose=bootstrap`) に入る — 同じ campaign に入れると、pair で
測る同じ stock variant が terminal skip になるため。job stdout の JSON の `fitness_tps` と `abort_rate_pct`
(同じ attempt の bench の abort 率 × 100) を (a) の 2 scalar にする。2 回目以降の iteration は直前の
pair の stock の値を使う。

### (a) coder の入力を driver に作らせる
```
python3 -m orchestrator.campaign.p3_s4_loop_policy --form <cpp|ir> --campaign-env pegasus --emit-coder-input \
    --baseline-throughput-tps <stock の値> --baseline-abort-rate-pct <stock の値 (percent 0..100)>
```
出力 JSON (5 key: `leakproof_context`・`policy_spec`・`baseline`・`recon_projection`・`self_history`) を
**そのまま** coder に渡す。メインセッションが key を足したり、値を書き換えたり、説明を付け足したりしない。
前 iteration の critic 診断を渡すときだけ、同じ command に `--critic-output <critic の出力 file>` を足す。
driver が 6 文字列 field の閉じた形 (`critic_diagnosis`) に変換して載せる。

### (b) coder を spawn
`Agent(subagent_type='coder-v4-autonomous-policy')` (C++ 形) または `'coder-v4-autonomous-policy-ir'` (IR 形)。
出力 = `{"proposal": {"axis", "implementation" | "ir", "justification", "confidence"}}`。

### (c) diff プレビューを取る
`<scratch>/coder.json` = `{"coder": <(b) の proposal>}` (top key は `coder` だけ) を書き、preview を取る:
```
python3 -m orchestrator.campaign.p3_s4_loop_policy --form <cpp|ir> --preview-diff <scratch>/coder.json
```
出力 = `{passed, working_diff, diff_digest, subtype, rule_id}`。preview は検疫・構文検査・単独 TU compile までを
build 無しで通す (auditor 判定はしない。auditor の deny-only veto と digest 照合は (f) の run で掛かる)。`passed=false` なら auditor を呼ばず、同じ file で拒否を記録してから (a) に戻る (iteration を 1 消費する):
```
python3 -m orchestrator.campaign.p3_s4_loop_policy --form <cpp|ir> --campaign-env pegasus --record-reject <scratch>/coder.json
```
driver が同じ gate を掛け直し、拒否なら WAL と履歴 (`policy_history.jsonl`) に subtype・rule id を記録する
(gate を通る候補は拒否して何も書かない)。メインセッションは拒否理由を言い換えて coder に渡さない —
次の (a) の `self_history` に driver が載せる。

### (d) auditor を spawn (LLM 由来の候補すべてに必須)
`Agent(subagent_type='auditor')`。入力は sort runbook §1(d) と同じ形 (`working_diff`・`diff_digest`・
`designated_sources`・`abort_digest`)。`designated_sources` には `orchestrator/campaign/silo_function_policy_api.hh`
と `orchestrator/campaign/silo_function_policy_coder_spec.md` を含める。返却 `diff_digest` は (c) の値の echo
であり、caller が補正しない。本軸の違反型は 1〜26。
spawn の prompt には、driver の auditor gate (`auditor_gate.parse_auditor_dict`) が受理する閉じた出力形を明記する:
`violations` は `{type (整数), location, correctness_impact, verifier_blind_spot}` の配列、`nits` は `{"finding": 文字列}`
か `{"note": 文字列}` の配列、`proposed_tests` はちょうど `{mutation, expected_gate, machine_judgment}` (文字列) の配列、
`uncertainty` は文字列 1 つ。auditor role の出力節は型を定めておらず、明記しないと (e) の読込みで
`AuditorGateFailure` になる (段階 F の初回で観測)。返却が gate に拒否されたら値を直さず、同じ入力で再審査させる。

### (e) proposal file を確定
`{"coder": <(b) の proposal>, "auditor": <(d) の返却>}`。top key はこの 2 つだけ
(`planner`・`value`・`prior_critic_reverse` を書くと driver が拒否する)。

### (f) 1 iteration を実走 (計算ノード、single-tenant)
job body の `IZANAGI_S4_POLICY_MODE=pair` (`IZANAGI_S4_POLICY_PROPOSAL_PATH=<scratch>/prop.json`) を qsub する。
job body は前処理 (gflags・glog・masstree) の後に次を 1 回呼ぶ:
```
python3 -m orchestrator.campaign.p3_s4_loop_policy --form <cpp|ir> --campaign-env pegasus \
    --fetchcontent-prebuild-receipt <job が作る receipt> \
    --allow-coder-derived-build --run-iteration <scratch>/prop.json --stock-control
```
- 候補を評価した後、同じ authorization session で stock を 1 評価する (同じ job・同じ動作点の対照)。
  候補が例外で終わっても stock は試み、最後に候補の例外で rc≠0 になる (履歴には `eval-exception` の行が残る)。
  pair の成立は job rc ではなく、両 attempt の WAL で確かめる。
- **投入前に walltime を確かめる。** loop の walltime 予算 (`MAX_WALLTIME_S`) は `loop_state.json` の作成時刻から
  数える。login の record-reject が先に loop_state を作った系列では、queue 待ちも予算に入る。残りが足りなければ
  投入せず、予算停止として記録する。
- `--allow-coder-derived-build` が無ければ build は拒否される。配線確認だけなら login で `--no-build`
  (検査を通れば `dry-pass` を返すが、WAL・履歴・critic digest には載らない)。
- driver は検疫 → 構文検査 → 単独 TU → auditor digest 照合 → 書込 → digest 再照合 → build → legacy verify →
  性能構成 verify → bench の順に進め、履歴 (`policy_history.jsonl`) と critic digest
  (`silo_policy_loop_digest.txt`) を campaign dir に書く。
- `AuditorGateFailure` は手順ミスか監査帰属の破れ。値を転記し直さず (c) からやり直す。

### (g) 停止判定を読み、続けるなら critic を spawn
停止は予算 (iteration 数・walltime) だけ (planner が無いので収束判定と逆方向枯渇は使わない)。
critic の出力は次の (a) で `critic_diagnosis` として渡す。

---

## 2. リーク制御チェックリスト (毎 iteration、メインセッションが自己監査)

- coder 入力は (a) の driver 出力だけ。段階 D の偵察結果 (projection.json の `binary`・`scope` 以外)、
  既知最良との小比較 (D2240) の点 ID・因子・比・順位、段階 C の手書き方策の名前・値・性能を渡さない
  (手順書 §3 D の firewall、D2243 項 1)。
- `justification` は履歴 file に残るが、coder 入力と critic には渡らない。メインセッションも転写しない。
- 他系列・他の形の campaign の結果を coder に見せない。
- 偵察・小比較の insight を読んだ事実は campaign の provenance に情報源として記録する。

---

## 3. 停止と継承

`L.check_stop` の予算 (`MAX_ITER` / `MAX_WALLTIME_S`) に委譲する。checkpoint は campaign dir の
`loop_state.json`、自系列の本文と結果は `policy_history.jsonl`。stock baseline (bootstrap campaign) と
R2 (r2 campaign) は loop の checkpoint・履歴を動かさない。

---

## 3.1 R2 — 保存候補の LLM なし再評価

再現パッケージの R2 (保存した候補を LLM なしで新しく評価し直す、見積り稿
`output/insights/2026-09-22/t2853-repro-package-estimate/README.md` §8) の入口。入力は (e) の proposal file
(`{coder, auditor}`) そのもので、job body の `IZANAGI_S4_POLICY_MODE=replay` が
`--replay-proposal <proposal>` で driver を呼ぶ。検疫・構文検査・単独 TU・auditor の digest 照合と deny-only veto・
書込後の digest 再照合を実走と同じ gate で掛け直し、loop とは別の campaign (`evaluation_purpose=r2`) で 1 評価する。
結果は新しい有限履歴についての新しい判定であり、元の判定の再確認ではない。同じ候補を同じ checkout で 2 回 R2 すると
同じ variant が terminal skip になる (反復が要るときに識別子を足す)。

## 3.2 trace の保全

方策 mode の job は `IZANAGI_TRACE_ARCHIVE_ROOT` (絶対 path、repo の外) を必須にする (欠けると driver の前に rc=2)。
保全の実体は pipeline の既存 opt-in (D2233・D2247、qsub の env で渡す運用は D2261 項 3)。write-heavy 1 評価で
約 0.75 GiB (見積り稿 §7)。保全先は `/work/1/SFC/tanab/izanagi-repro-archive/<日付付きの dir>/`。

---

## 4. 既知の限界

- certified は有限の観測履歴についての判定。verify と perf で同じ分岐を踏んだとは言えない (設計 §3.1)。
- 公平性 (worker の駐車・偏り) の機械観測は無い。endpoint 候補と勝ち候補に auditor の目視を課す (設計 §3.4)。
- lock 方策は既定で「verify 中の発火証拠なし」と扱う (候補ごとの hook 計数は v1 に無い、設計 §3.4)。
- 候補ごとの sanitizer は置かない。UB の型は受理契約 policy-C++ v1 と単独 TU compile で構造的に除く。
- IR 形は有限 IR の部分空間、C++ 形は policy-C++ v1 の空間で、両者の差は表現と探索法を合わせた差。
- 段階 C の上限 (abort 後 1000 µs・lock 1 回 50 µs・32 周回) は試走設計値で、最適値ではない。
