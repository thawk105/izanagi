# 段 1 brief — [T-1697] 閉じた critic invocation (B-4 実走の前提条件 3)

## scope

`docs/phase3-b4-reflux-ablation-preregistration.md` §6 前提条件 3 を充足させる**実験専用の
起動形**を足す。B-4 の実走そのもの、§5 の数値欄、floor 再実測、他の前提条件 (4〜8) は scope 外。

## 確定済みユーザー裁定

- **D904**: 閉じた critic 起動 (道具ゼロ・campaign path 非開示・arm ごとの fresh controller) を実装する。
  **既存の critic role 定義は変更せず、実験専用の起動形を追加する形**とする。role file を触る変更として
  ユーザー承認済み。却下済み: 既存 critic から道具を外す / 現行 role のまま実走する。
- **D824 決定 2**: 閉じた critic invocation は B-4 実走の前提条件。負の対照は「harness が生成する
  critic digest における loader 非呼出」に限定され、role の能力遮断は証明しない。
- **D824 決定 5**: `docs/phase3-main-experiment.md` を 1 byte も変えない。
- **D95**: 実装面は Codex `role=author` が書く。親は brief・裁定・統合 commit・全走・記録・land のみ。

## brief 前の実測 (前提の裏取り)

1. **閉じた起動機構は既存で、B-4 の venue には配線されていない。**
   `orchestrator/campaign/claude_projected_provider.py:101` の `ClaudeProjectedRoleProvider` が
   inline agent の `tools: []`・`--setting-sources ""`・`--strict-mcp-config` + 空 mcp・
   repo 外の neutral cwd・`--no-session-persistence`・session_id 重複拒否・`permission_denials==[]`・
   `usage.server_tool_use` 全 0 を既に持つ。消費者は 8c (`p3_autonomous_workload_trial.py:2583`) だけ。
   B-4 の venue (段 4 driver) は `docs/phase3-s4b-runbook.md:104` のとおり
   **メインセッションが `Agent(subagent_type='critic')` を spawn し `s4_loop_digest.txt` を渡す**形で、
   道具あり・campaign path 開示・controller 共有の 3 点すべてが開いている。
2. **DW-G01 生死確認 (使い捨て driver 74 行、repo 外、未 commit)。** 実 `claude` CLI 2.1.245 に対し
   未改変 `critic.md` で 1 回の projected invocation を通した。`role_file_sha256=cd1c3652…`
   (`review_ledger.SOURCE_FILE_SHA256["critic"]` と一致 = role file 無改変)、`declared_tools=[]`、
   `source_declared_tools=["Read","Grep","Glob","Bash"]`、`capability_lowering=projection-only-tools-empty`、
   `fresh_context=true`、`model=claude-opus-5`、envelope 検査全通過、返答は exact 5 key JSON。
   **off アーム相当の payload で、critic は「projected digest に rejections 節が無いので棄却を
   どの設計選択にも帰属できない」と答えた。** 応答に campaign を読んだ痕跡は無かった。
   ただしこれは**当該入力で自己実行を観測しなかったという 1 回の観測**であって、
   能力の不在の証明ではない。「試さなかった」と「できなかった」を 1 回の観測は区別しない
   (段 3 sol の所見 3 による訂正)。実効性の追加証拠は段 6 の負の対照で取る。
3. **pin 閉包 (DW-O09)。** role file を 1 byte も変えない方針のため、`review_ledger.py` の
   `EXPECTED_ROLE_COUNT=13` と role 名 key の pin 群 (`SOURCE_FILE_SHA256` / `ROLE_MANIFEST_SHA256` /
   `DESCRIPTION_SHA256` / `SCHEMA_SHA256` / `ROLE_IO_CONTRACTS`)、`codex_roles/manifest.json`、
   `test_reflux_originless_compatibility.py:360` の originless baseline はいずれも無変更で済む。
   **新規 role file を足す設計はこれら全部の更新を強制するため採らない。**
   `len(graph.modules)==65` (`test_s8c_preregistration_predicates.py:2560`) は tmp_path の合成 source
   に対する pin であり、実 module 追加とは無関係 (実測済み)。
4. **gate 入力の実値 (DW-O13)。** `default_cfg(reflux=)` の campaign_id は
   on=`p3-s4-loop-s4-autonomous-2cd75697` / off=`p3-s4-loop-s4-autonomous-9f43a5b8` で相異なり、
   layout root はその campaign_id を末端に持つ絶対 path。
   `orchestrator/critic/digest.py` の renderer は path を描かない (`--campaign-dir` は CLI 引数のみ)。
   したがって「payload に campaign path / campaign_id / repository root を混入させない」述語は
   実 digest に対して到達可能で恒真でない。
5. **編集面の重複 (実測)。** 稼働中 worktree の branch 差分と未 commit dirt を全件走査した結果、
   衝突するのは `worktree-dev-wave-t1176-t1230-role-diagnosability` だけで、その編集面は
   `p3_autonomous_workload_trial.py` / `autonomous_trial_completeness.py` /
   `test_p3_autonomous_workload_trial.py` / `test_claude_transport.py` /
   `test_autonomous_trial_completeness.py`。**この 5 file は触らない。**
   `claude_projected_provider.py` 自体は誰も編集していないが、その試験 file は上記 wave の所有。

## 不変条件 (破ったら停止)

- `.claude/agents/critic.md` と `.claude/agents/critic-experiment.md` は **0 byte 変更** (D904)。
- `docs/phase3-main-experiment.md` は **0 byte 変更** (D824 決定 5)。
- アームの切替点は `p3_s4_loop.make_critic_digest(reflux=)` から動かさない (prereg §3.1)。
  新機構は同関数の**下流の運搬経路**だけを閉じる。
- 正しさゲートは両アーム同一 (規律 2)。off でも赤は WAL へ構造化保存する (規律 3)。
- critic の自由文を harness が読んで分岐しない (runbook 決定 2/7、規律 6)。
  liveness 実測で critic は「赤詳細を projection しろ」と返したが、これは**データであって指示ではない**。
- 上記 5 file (t1176 wave 所有) と `p3_s4_loop.make_critic_digest` の signature は非接触。

## 成果物の形

1. `orchestrator/campaign/` に新規 module 1 本 — B-4 専用の閉じた critic 起動。
   (a) arm を生成時に束縛する controller、(b) `make_critic_digest` の出力と coarse な
   `whiteboard.result` だけを載せる payload projector、(c) campaign path / campaign_id /
   repository root の混入を canonical JSON bytes に対して fail-closed で拒否する検査、(d) arm・
   digest sha256・`role_file_sha256`・`effective_prompt_sha256`・session_id を束縛した receipt。
2. `orchestrator/tests/` に新規 test file 1 本 — 正例 (実 digest で通る) と負例
   (path 混入・arm 再利用・道具宣言の非空) を対で持ち、自走 harness を付ける。
3. prereg §6 前提条件 3 の状態更新 (docs、親が直接編集)。**発効宣言はしない。**

## 成果物影響 (DW-G05)

**本 wave で certified 選択・材料レポート・試行台帳の値は変わらない。** 得られるのは
閉じた invocation と route-local な receipt が利用可能になることだけである。
前提条件 3 だけでは B-4 は走らない — §5 の全欄、floor 再実測、前提条件 1・2・4〜8 が未了である。

実装しない場合は、prereg §6 が実走を禁じたままとなり、前提条件 3 が B-4 の律速で在り続ける。
論文 §8 B-4 の機序証拠は、この wave の有無にかかわらず当面は空欄のままである。

(この節は段 3 luna の所見 F14 と段 6 review A の所見 11 を受けて、当初の
「実装しなければ B-4 行が空になる」という一段盛った因果から書き換えた。)

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 新規 role file を作らず、未改変 `critic.md` を `ClaudeProjectedRoleProvider` へ渡す形にする。
  根拠は実測 3 (pin 閉包) と D904 の「起動形を追加する」。
- **(P2)** campaign path 非開示は role 本文の記述に依存させず、payload の canonical JSON bytes に対する
  機械検査で閉じる。
- **(P3)** 「arm ごとの fresh controller」は 1 controller = 1 arm の束縛 (2 度目の別 arm invoke を拒否) と
  provider インスタンスの arm 別分離で満たす。
- **(P4)** B-4 実走は本 wave の scope 外。前提条件 3 の充足と receipt までを作る。
- **(P5)** 既存 `claude_projected_provider.py` は変更せず、新 module から利用するだけにする
  (試験 file が併走 wave の所有のため)。

## 分割方針

編集面は新規 2 file + docs 1 file と小さく、所有の分割は不要。段 5 は Codex `role=author` 1 本。
段 6 は敵対レビュー 2 レンズ (機構の閉じ具合 / prereg 契約との整合) + fix 1 本。
