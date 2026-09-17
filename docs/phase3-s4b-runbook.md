# Phase 3 段 4b Runbook — coder 自律ループの実走手順 (Model Y 駆動)

**位置づけ:** 段 4b = 実 LLM (planner-v4 / coder-v4-autonomous / critic) をメインセッションが
spawn し、機械部分 (`orchestrator/campaign/p3_s4_loop.py`) に proposal を引数で渡す実ループ。
設計の正典は D39 (decisions.md) と phase3.md 後続段 4。設計経緯の詳細は
`docs/phase3-s4-design-v1.md` (段 4 完了で凍結、矛盾があれば正典が勝つ)。本書は**運用手順**だけを持つ
(設計判断・完了状況は書かない — 正本は worklog 末尾と phase3.md)。矛盾があれば正典が勝つ。

段 4 の機械部分 (挿入→検疫→評価→WAL→digest→whiteboard→停止判定) と cross-process 永続化
(checkpoint) は実装・test 済み。本書が埋めるのは「メインセッションが LLM を回してその機械部分を
駆動する」手順。

---

## 0. 実走前ゲート (すべて満たすまで駆動を始めない)

1. **fresh session である** — `planner-v4` / `coder-v4-autonomous` はエージェント登録が
   **セッション開始時**に読まれる。frontmatter を足した commit より後に**新しく開いた session**
   でないと spawn できない (セッション途中の .md 追加は反映されない、2026-07-08 実証)。
   確認 = Agent の利用可能型に `planner-v4` と `coder-v4-autonomous` が並ぶこと。
2. **計測層が single-tenant** — `pgrep -a -f 'ccbench|silo|bench'` で他ユーザー/孤児ベンチが
   無いこと (load avg は EMA ゆえ遅延しがちで pgrep が正、規律4)。段 4b は各 iteration で
   build/verify/bench を実走するため、他者の計測と相互汚染しない窓を要する。
3. **submodule が pinned-clean** — `git -C external/ccbench rev-parse HEAD` が `p3_s4_loop.PIN`
   (D1936項1で固定した完全SHA)、`git -C external/ccbench status --porcelain` が空。
4. **test 緑** — `python3 -m pytest orchestrator/tests/ -q` が all pass。
5. **calibration の確認** — 段 4 の `default_perf` は配線規模 (records=100k/threads=4/extime=1/reps=2、
   有意性を主張しない、D39 残存リスク c)。**headline 性能主張はしない段** — headline は段 6。
   実 fitness 比較に上げるときは calibrator が決めた records/threads/reps に差し替える。

---

## 1. 1 iteration の駆動プロトコル (メインセッションが回す)

ループ主導権はメインセッション (Model Y、D39 決定7)。harness は LLM を spawn しない。
proposal は `load_proposal_file` の受理検査 (closed key set + ability-probe 射影 tripwire、
`patches/ledger.json` の projection_policy を執行 — [T-139]) を通ったものだけが評価される。
ledger 不在・禁止字面混入は fail-closed。sort (`phase3-s5-sort-runbook.md`) と
trigger-gating (`phase3-s8a-trigger-runbook.md`) の loader も同一の検査を持つ。1 周:

**K2 宣言アーム (`coder-v4-autonomous-k2`) を回すとき**、driver へ渡す `--knowledge-manifest` の
知識源は `docs/agent-architecture.md` の `coder-v4-autonomous-k2` 節にある
「知識源の選定 (送り手側の義務、D1936 項 2)」項に従って選ぶ。本書には規律本文を複製しない。
driver で `--emit-planner-context` を指定せず `--run-iteration` を実行する場合、manifest の `sources` が
非空なら `--coder-role coder-v4-autonomous-k2` が必須で、妥当な空取得 manifest (`sources: []`) では
従来どおり role 省略を許す (D1878)。

### (a) planner-v4 を spawn (方向提案・値なし)
`Agent(subagent_type='planner-v4')`。入力 (メインセッションが**射影して**渡す。JSON):

適用版 (D2104 項 4): 2026-09-17 の [T-2703] / [T-2717] / [T-2705] 改訂以降に開始する走行には、改訂した
役割入力文書 (`.claude/agents/planner-v4.md` / `coder-v4-autonomous-trigger-gating.md` / `critic.md` /
`critic-experiment.md` と `src/coder-leakproof-context.md`) と下の射影形を適用する。凍結済みアーム (K0 / K1 /
B-4) と、それ以前に開始した走行 (T-2588 の K2 走行を含む) には遡及適用せず、記録は当時の文書・射影
(`last_delta_pct: null` を含む) のまま保持する。
```json
{
  "current_perf": {"throughput_tps": <baseline>, "abort_rate_pct": <baseline>},
  "leading_indicators": {"cache_miss_rate_pct": <baseline>, "contention_level": "<...>", "IPC_overall": <baseline>},
  "whiteboard": <loop_state.json の whiteboard (抽象・機序なし)>
}
```
- whiteboard は checkpoint (`output/exploration/campaigns/<id>/loop_state.json`) の whiteboard フィールド、
  または `whiteboard_for_planner(state)` の射影。**機序・勝ち筋値を足さない**。
- **単位の換算 (D118)**: `abort_rate_pct` と `cache_miss_rate_pct` は **percent (0..100)** である。
  WAL / calibrator が持つ `abort_rate` と `llc_miss_rate` は **0..1 の率**なので、
  射影時に **×100 する**。換算を忘れると role は 7.9% を 0.079% と読む (100 倍の意味ずれ)。
- 出力 = `{proposal: {axis, direction, magnitude, justification, uncertainty}}` (値なし)。

### (b) coder-v4-autonomous を spawn (値 + hole コード合成)
`Agent(subagent_type='coder-v4-autonomous')` (tools=[] = ファイルシステム走査経路なし、リーク制御)。
入力 (メインセッションが射影):
```json
{
  "leakproof_context": "<src/coder-leakproof-context.md の内容を inline で>",
  "planner_direction": <(a) の proposal>,
  "baseline": {"throughput_tps": <baseline>, "abort_rate_pct": <baseline>},
  "whiteboard": <抽象 whiteboard>
}
```
- **リーク制御 (規律2/6, D39 決定7):** coder には**勝ち筋値・性能利得・機序を渡さない**。渡すのは
  `src/coder-leakproof-context.md` (勝ち筋 literal を物理削除した curated 版) + planner の抽象方向のみ。
  `src/coder-spec.md` は sweet-spot 漏れリスクありゆえ coder に直接渡さない (leakproof 版を使う)。
- coder は tools=[] ゆえ prompt に無い情報を読めない = 構造的リーク閉。
- 出力 = `{proposal: {axis, value(1-1000), implementation, justification, confidence}}`。
  `implementation` は `double now_backoff = <数値 literal 1 個>;` の**ちょうど 1 文**。
  literal は接尾辞を持たず、value と数値が一致すること (D836 / D901 条項 1)。
  計算式・呼び出し・括弧・三項・後続の文は受理文法が拒否する。値の不一致は harness の
  `assert_value_literal_consistent` が AttributionMismatch で弾く (決定7)。

### (c) proposal ファイルを書く
`<scratch>/prop.json`:
```json
{
  "planner": <(a) の proposal>,
  "coder":   <(b) の proposal>,
  "prior_critic_reverse": <前 iteration の critic が逆方向を推奨したか true|false、iteration 1 は null>
}
```

### (d) harness で 1 iteration を実走 (single-tenant!)
```
python3 -m orchestrator.campaign.p3_s4_loop --run-iteration <scratch>/prop.json \
    --allow-coder-derived-build
```
- **`--allow-coder-derived-build` は必須** — coder 由来 source の build は既定拒否であり、
  この明示 opt-in が無ければ `BuildAdmissionError` で止まる (D125)。`--no-build` の
  配線リハーサルでは build へ進まないため不要。
- checkpoint を復元 (無ければ start_wall 付き初期化) → critic feedback 畳込み → **入口 check_stop**
  (停止すべきなら run せず終了) → iteration++ → 挿入→diff 検疫→(pass なら)build×2/verify/bench →
  checkpoint 保存 (atomic) → digest 書き出し → 末尾 check_stop。
- 出力 = `ran / outcome (rejected|certified|aborted|dry-pass|stopped-before) / iteration / 停止判定 /
  checkpoint パス / digest パス`。
- **配線リハーサルは `--no-build`** (single-tenant 不要。ただし diff 検疫 pass の clean 提案は
  dry-pass = whiteboard に載らない → 実 feedback は build を要する。dry は配線確認専用)。

### (e) 停止判定を読み、続けるなら critic を spawn
- `停止判定` が `continue` 以外 (converged / reverse-exhausted / budget-*) → ループ終了 (§3 へ)。
- `continue` なら `Agent(subagent_type='critic')` に digest (`s4_loop_digest.txt`) を渡し、帰属 +
  次方向を得る。**メインセッションが critic 出力を解釈**し「逆方向を推奨したか」を判定 →
  次 iteration の `prior_critic_reverse` に反映 (harness は critic の自然文を読まない、決定2/7)。
- **この legacy 手順は B-4 還流 ablation の標本として非適格である。** 同 role は `Bash` を持ち
  digest の自己生成を明示許可するため、off アームとして数えられない
  (`docs/phase3-b4-reflux-ablation-preregistration.md` §6 前提条件 3)。B-4 の標本を採る走行は
  `orchestrator/campaign/p3_b4_closed_critic.py` の閉じた起動形を使う。
  本節の手順は B-4 以外の段 4b 走行のためのものである。
- (a) に戻る。

---

## 2. リーク制御チェックリスト (毎 iteration、メインセッションが自己監査)

段 4b の主実験妥当性 (baseline 4 の帰無仮説 = LLM 固有価値) は「coder が勝ち筋値を見ずに
合成したか」に懸かる。メインセッションが射影する入力から次を排除する:
- decisions.md の sweet-spot literal・機序・利得
- output/insights の P2 backoff case-study の値
- backoff-sweep campaign の WAL/reports/profile
- main-experiment の勝ち筋 VALUE 節
- whiteboard に機序 (critic attribution) を転写しない (checkpoint の型が 5 フィールドに制限
  = state_from_dict が未知フィールドを拒否するが、**入力構築時の自己規律が一次防壁**)

---

## 3. 停止と継承 (D39 決定2)

- **停止条件:** 収束 (同一方向・magnitude=small が 3 連続) / 逆方向枯渇 (critic 逆方向推奨 2 回 +
  改善なし) / 予算 (10 iteration or wall 3600s)。
- **checkpoint は段 6 へ継承:** 予算枯渇時の whiteboard は「未査証 (partial)」として段 6 が拾う
  (final certified finding ではない)。checkpoint = `output/exploration/campaigns/<id>/loop_state.json`。
- **reflux (還流 on/off) = LLM ablation の対照:** `--reflux off` で critic への赤節を落とす別
  campaign (別 output dir、混ざらない)。on/off を別 campaign で走らせ比較 (段 6 の LLM ablation)。
  **ただし digest 生成を off にするだけでは B-4 の off アームにならない** — 上記 (e) のとおり
  legacy の critic spawn は道具を持つ。B-4 として報告する走行は閉じた起動形を要する。

---

## 4. 既知の限界 (実走前に承知しておく)

- 段 4 は `delta_pct` 常に None (統計的 delta/検証相は段 6 予約) → whiteboard の性能率は空。
- dry-pass (clean 提案 × `--no-build`) は whiteboard に載らない (配線専用)。実 feedback は
  build 必須。
- 段 4 の 1 iteration 実走は「配線が E2E で通る」の機械実証 — kickoff CorrectnessWorkload は
  同一キー競合をほぼ踏まず n も小さいため**有意性を主張しない** (D39 残存リスク c)。
- 並行 driver は想定しない (メインセッション単独駆動)。checkpoint は atomic 書き込みだが
  read-modify-write の相互排他は張らない — 同一 campaign に複数 driver を当てない。
