# Phase 3 段 4b Runbook — coder 自律ループの実走手順 (Model Y 駆動)

**位置づけ:** 段 4b = 実 LLM (planner-v4 / coder-v4-autonomous / critic) をメインセッションが
spawn し、機械部分 (`orchestrator/campaign/p3_s4_loop.py`) に proposal を引数で渡す実ループ。
設計正本は D39 (decisions.md) と `docs/phase3-s4-design-v1.md`。本書は**運用手順**だけを持つ
(設計判断・完了状況は書かない — 正本は worklog 末尾と phase3.md)。矛盾があれば正典が勝つ。

段 4 の機械部分 (挿入→検疫→評価→WAL→digest→whiteboard→停止判定) と cross-process 永続化
(checkpoint) は実装・test 済み。本書が埋めるのは「メインセッションが LLM を回してその機械部分を
駆動する」手順。

---

## 0. 実走前ゲート (すべて満たすまで駆動を始めない)

1. **fresh session である** — `planner-v4` / `coder-v4-autonomous` はエージェント登録が
   **session 開始時**に読まれる。frontmatter を足した commit より後に**新しく開いた session**
   でないと spawn できない (mid-session の .md 追加は反映されない、2026-07-08 実証)。
   確認 = Agent の利用可能型に `planner-v4` と `coder-v4-autonomous` が並ぶこと。
2. **計測層が single-tenant** — `pgrep -a -f 'ccbench|silo|bench'` で他ユーザー/孤児ベンチが
   無いこと (load avg は EMA で laggy ゆえ pgrep が正、規律4)。段 4b は各 iteration で
   build/verify/bench を実走するため、他者の計測と相互汚染しない窓を要する。
3. **submodule が pinned-clean** — `git -C external/ccbench rev-parse --short HEAD` が `028f34d`
   (= `p3_s4_loop.PIN`)、`git -C external/ccbench status --porcelain` が空。
4. **test 緑** — `python3 -m pytest orchestrator/tests/ -q` が all pass。
5. **calibration の確認** — 段 4 の `default_perf` は配線規模 (records=100k/threads=4/extime=1/reps=2、
   有意性を主張しない、D39 残存リスク c)。**headline 性能主張はしない段** — headline は段 6。
   実 fitness 比較に上げるときは calibrator が決めた records/threads/reps に差し替える。

---

## 1. 1 iteration の駆動プロトコル (メインセッションが回す)

ループ主導権はメインセッション (Model Y、D39 決定7)。harness は LLM を spawn しない。1 周:

### (a) planner-v4 を spawn (方向提案・値なし)
`Agent(subagent_type='planner-v4')`。入力 (メインセッションが**射影して**渡す。JSON):
```json
{
  "current_perf": {"throughput_ops_sec": <baseline>, "abort_rate_pct": <baseline>, "last_delta_pct": null},
  "leading_indicators": {"cache_miss_rate_pct": <baseline>, "contention_level": "<...>", "IPC_overall": <baseline>},
  "whiteboard": <loop_state.json の whiteboard (抽象・機序なし)>
}
```
- whiteboard は checkpoint (`output/campaigns/<id>/loop_state.json`) の whiteboard フィールド、
  または `whiteboard_for_planner(state)` の射影。**機序・勝ち筋値を足さない**。
- 出力 = `{proposal: {axis, direction, magnitude, justification, uncertainty}}` (値なし)。

### (b) coder-v4-autonomous を spawn (値 + hole コード合成)
`Agent(subagent_type='coder-v4-autonomous')` (tools=[] = filesystem browse 経路なし、リーク制御)。
入力 (メインセッションが射影):
```json
{
  "leakproof_context": "<src/coder-leakproof-context.md の内容を inline で>",
  "planner_direction": <(a) の proposal>,
  "baseline": {"throughput_ops_sec": <baseline>, "abort_rate_pct": <baseline>},
  "whiteboard": <抽象 whiteboard>
}
```
- **リーク制御 (規律2/6, D39 決定7):** coder には**勝ち筋値・性能利得・機序を渡さない**。渡すのは
  `src/coder-leakproof-context.md` (物理削除済み) + planner の抽象方向のみ。`src/coder-spec.md`
  は sweet-spot 漏れリスクありゆえ coder に直接渡さない (leakproof 版を使う)。
- coder は tools=[] ゆえ prompt に無い情報を読めない = 構造的リーク閉。
- 出力 = `{proposal: {axis, value(1-1000), implementation, justification, confidence}}`。
  `implementation` は `double now_backoff = <値>;` 形。value と literal は一致させる
  (不一致は harness の `assert_value_literal_consistent` が AttributionMismatch で弾く、決定7)。

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
python3 -m campaign.p3_s4_loop --run-iteration <scratch>/prop.json
```
- checkpoint を復元 (無ければ start_wall 付き初期化) → critic feedback 畳込み → **入口 check_stop**
  (停止すべきなら run せず終了) → iteration++ → 挿入→diff 検疫→(pass なら)build×2/verify/bench →
  checkpoint 保存 (atomic) → digest 書き出し → 末尾 check_stop。
- 出力 = `ran / outcome (rejected|certified|aborted|dry-pass|stopped-before) / iteration / 停止判定 /
  checkpoint パス / digest パス`。
- **配線リハーサルは `--no-build`** (single-tenant 不要。ただし diff 検疫 pass の clean 提案は
  dry-pass = whiteboard に載らない → 実 feedback は build を要する。dry は wiring 確認専用)。

### (e) 停止判定を読み、続けるなら critic を spawn
- `停止判定` が `continue` 以外 (converged / reverse-exhausted / budget-*) → ループ終了 (§3 へ)。
- `continue` なら `Agent(subagent_type='critic')` に digest (`s4_loop_digest.txt`) を渡し、帰属 +
  次方向を得る。**メインセッションが critic 出力を解釈**し「逆方向を推奨したか」を判定 →
  次 iteration の `prior_critic_reverse` に反映 (harness は critic の自然文を読まない、決定2/7)。
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
- **checkpoint は段 6 へ inherit:** 予算枯渇時の whiteboard は「未査証 (partial)」として段 6 が拾う
  (final certified finding ではない)。checkpoint = `output/campaigns/<id>/loop_state.json`。
- **reflux (還流 on/off) = LLM ablation の対照:** `--reflux off` で critic への赤節を落とす別
  campaign (別 output dir、混ざらない)。on/off を別 campaign で走らせ比較 (段 6 の LLM ablation)。

---

## 4. 既知の限界 (実走前に承知しておく)

- 段 4 は `delta_pct` 常に None (統計的 delta/検証相は段 6 予約) → whiteboard の性能率は空。
- dry-pass (clean 提案 × `--no-build`) は whiteboard に載らない (wiring 専用)。実 feedback は
  build 必須。
- 段 4 の 1 iteration 実走は「配線が E2E で通る」の機械実証 — kickoff CorrectnessWorkload は
  同一キー競合をほぼ踏まず n も小さいため**有意性を主張しない** (D39 残存リスク c)。
- 並行 driver は想定しない (メインセッション単独駆動)。checkpoint は atomic 書き込みだが
  read-modify-write の相互排他は張らない — 同一 campaign に複数 driver を当てない。
