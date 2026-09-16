# 段 1 brief — [T-2588] K2 新提案 1 評価と次提案への還流

wave `dev-wave-t2588-k2-loop-roundtrip` / branch `worktree-dev-wave-t2588-k2-loop-roundtrip`
基点 local main `d97c423bdd14e0b416cb4f585d350e6c2b251287` (着手直前)。

## 研究前進

Phase 3 の主経路 (CC 自動合成) を 1 巡閉じる。進めるのは「段 4 合成ループが
**提案 → 評価 → 還流 → 次提案**を 1 周できる」という主張。完了判定は 3 点:
(a) **新しく生成した** proposal-1 が既存経路で terminal verdict を得る、
(b) その走の digest を critic が診断する、(c) その診断と実測を入力にした proposal-2 が保存される。

**止めている研究:** T-2581 (2026-09-10) は terminal verdict へ到達したが、**既存 proposal の値 20 を
再評価しただけ**で、role が新しく提案を作りその結果を次提案へ戻す往復は一度も閉じていない。
最小差分は「実装面ゼロ + 既存 role + 既存 job body の 1 投入」である。

## 依頼が指した blocker の実測 (覆った新事実)

依頼は「段 4 loop が literal 保持する CCBench 凍結 pin `028f34d` と現行 verifier の trace 形式が
食い違っている」を段 1 で現物確認せよと指示した。**現物では既に解消済みだった。**

| 対象 | 現物 | 値 |
|---|---|---|
| 段 4 loop の pin | `orchestrator/campaign/p3_s4_loop.py:112` | `PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"` |
| 前進 commit | `git log -L112,112` | `55d0f239945d34eaf39de500f076f332dc7e20b3` (2026-09-10 12:46:54 JST) |
| submodule gitlink | `git ls-tree HEAD external/ccbench` | 同一 `511c9538…` |
| 授権 | `docs/decisions.md` D1936 項 1 | 「項1はD38の段4固定pinを新規試行について改める。歴史的な028f34dの記録は保持する。」 |
| verifier | `orchestrator/verifier/parse.py:321-330` | v1 (5 field) 拒否 / v2 (7 field) 要求。**無変更** |

依頼の前提が覆ったので段 4 で再裁定する (`DW-S01`)。**blocker は無く、実走を止める理由は無い。**

## scope

`output/insights/2026-09-10_cc-next-precheck/run-card.md` (静的 precheck) の実行。同カードの
「最小の未充足事項」2 件は本 wave で満たされた — role 登録 (`planner-v4` /
`coder-v4-autonomous-k2` / `critic` が Agent 型一覧に実在) と実走指示 (D2044 項 9)。

1. planner-v4 → coder-v4-autonomous-k2 で `proposal-1.json` を生成
2. 固定 SHA の専用 submit-tree から既存 job body を qsub 1 本
3. critic 1 本で同走 digest を診断
4. planner-v4 → coder-v4-autonomous-k2 で `proposal-2.json` を生成 (**評価しない**)
5. 記録 (insight + spool fragment)

**scope 外:** 新機構・gate・検査・台帳・一般化の追加、比較 arm、再投入・再抽選、
B-4 正式実験 / 新 CC 構造合成への計上、legacy critic を使うため B-4 ablation への適格化。

## 確定済みユーザー裁定

`docs/decisions.md` D2044 項 9 (2026-09-16)。逐語「新しい機構は足さず、既存経路だけで行う」。
「D1936 項 1 の 1 本認可は別件で消費済みで今回へ自動的に広がらないため、本決定で新たに認可する」。

## 不変条件

1. **規律 2 を緩めない。** anomaly 検出は即 reject。verifier・K2 指示検出・帰属照合・検疫・
   文法 gate を 1 行も触らない。赤の性能を推定しない。
2. **実装面差分ゼロ。** コード・テスト・実行可能 script・機械設定を書かない。書く必要が生じたら
   本 wave を止めて D95 の Codex author 作業へ分ける。
3. **[T-304] の owned path を編集しない** — `.claude/agents/coder-v4-autonomous-k2.md`、
   `.codex/role-adapters/coder-v4-autonomous-k2.json` (稼働中、`throughput_ops_sec` →
   `throughput_tps` 改名)。読むだけとし、main 現物の `throughput_ops_sec` を使う。
4. **親の上限:** planner/coder 各 2 回、critic 1 回、評価 job 1 本。再投入・再抽選・比較 arm なし。
5. **主張しない:** K2 知識の性能への因果、LLM 固有優越、de novo、K2 を条件とする certified な最終選択、
   headline 性能、critic による改善の因果実証。
6. 既知値 (20/30/40) の再提案が出たら「既知値の再提案」と正直に記録し、未評価値生成の成功に数えない。
   **新しい値が出るまで再抽選する操作はしない。**
7. job rc=0 だけを成功としない。trace parse / build failure は terminal 取得としない。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

**(P1) `current_perf` / `leading_indicators` の出所。**
親の provisional 裁定: **run-card が固定した歴史測定をそのまま使う** —
`throughput_ops_sec=487088.5`、`abort_rate_pct=7.2`、`cache_miss_rate_pct=32.29014422247246`、
`IPC_overall=0.7387153219395488`、`last_delta_pct=null`、`contention_level="未判定"`、
初期 whiteboard は空。射影には「settled=false の歴史測定であり現 pin の baseline ではない」と明示する。
**攻撃点:** T-2581 が現行 pin・同一配線規模で実測値 (fitness 713068 tps、CV 0.0058189437641328196、
commits 466113 / aborts 81919 / anomalies 0) を出している。これを使わない方が還流の質を落とすのでは
ないか。run-card を事前登録として扱う根拠はどこにあるか。

**(P2) `proposal-2` の入力。**
親の provisional 裁定: 本 wave の評価結果 (verifier terminal + digest の leading indicators) を
`current_perf` と `whiteboard` へ入れ、親が critic を解釈した `prior_critic_reverse` を添える。
`prior_critic_reverse` の consumer は `_fold_critic_reverse` と停止判定であって planner/coder の
方向生成器ではない — 親の解釈を介した runbook 上の還流と、この bool の機械的消費を同一視しない。

## 成果物

- `output/insights/2026-09-16_t2588-k2-loop-roundtrip/README.md` (一次資料)
- 同 `verbatim/` に role 逐語、`materials/` に proposal-1 / proposal-2 と入力射影
- `docs/spool/` の worklog fragment (+ 必要なら decisions fragment)
- 証拠原本 (job stdout/stderr、compute-result、WAL) は repo 外 job root
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/`

## 並列分割

- 段 2: codex read-only plan 1 本 (実行順序・入力射影・記録の file:line 粒度)
- 段 3: codex 相談 2 本 (異なるレンズ — A=事前登録と還流の質、B=規律 2/6 と主張範囲)
- 段 5: **実装子なし** (実装面ゼロ)。段 6 の変異 matrix は `DW-S04` により免除、受入全走は免除しない。
