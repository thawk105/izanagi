# Phase 3 段 5 Runbook — sort-strategy 自律ループの実走手順 (Model Y 駆動)

**位置づけ:** 段 5 sort-strategy = 実 LLM (`planner-v4` / `coder-v4-autonomous-sort` /
`auditor` / `critic`) をメインセッションが spawn し、機械部分
(`orchestrator/campaign/p3_s4_loop_sort.py`) に proposal を引数で渡す実ループ。
`docs/phase3-s4b-runbook.md` (backoff 軸) の兄弟文書 — 構造は同じだが **auditor が
per-iteration 必須の機械 gate として追加**されている点が異なる (D41 条件4、敵対レビュー
2026-07-10)。設計正本は D41/D42/D43 (decisions.md) と `orchestrator/campaign/p3_s4_loop_sort.py`
の docstring。本書は**運用手順**だけを持つ (設計判断・完了状況は書かない — 正本は
worklog 末尾と phase3.md)。矛盾があれば正典が勝つ。

---

## 0. 実走前ゲート (すべて満たすまで駆動を始めない)

1. **fresh session である** — `planner-v4` / `coder-v4-autonomous-sort` / `auditor` は
   エージェント登録が**セッション開始時**に読まれる。`coder-v4-autonomous-sort.md` を
   追加した commit より後に**新しく開いた session** でないと spawn できない (セッション途中
   の `.md` 追加は反映されない、2026-07-08 実証・段4b runbook と同じ制約)。確認 = Agent
   の利用可能型に `planner-v4` / `coder-v4-autonomous-sort` / `auditor` が並ぶこと。
2. **計測層が single-tenant** — `pgrep -a -f 'ccbench|silo|bench'` で他ユーザー/孤児
   ベンチが無いこと (load avg は EMA ゆえ遅延しがちで pgrep が正、規律4)。**この機で他ユーザー
   (leon 等) の claude セッションが並行稼働していることがある — バイナリ実行 (`ycsb_*.exe` 等)
   のプロセスが実際に走っているかを見分ける** (daemon/vscode-server 等の常駐プロセス名に
   `ccbench`/`bench` が偶然含まれるだけの場合は競合ではない)。
3. **submodule が pinned-clean** — `git -C external/ccbench rev-parse --short HEAD` が
   `p3_s4_loop_sort.PIN` (= `pin.CURRENT_PIN`) と一致し、
   `git -C external/ccbench status --porcelain` が空。pin の値は `pin.py` が正本 —
   ここに literal を書かない (pin 前進で腐るため、2026-07-12 監査)。
4. **test 緑** — `python3 -m pytest orchestrator/tests/ -q` が all pass。
5. **calibration の確認** — 段 5 の `default_perf` は配線規模 (records=100k/threads=4/
   extime=1/reps=2、有意性を主張しない)。**headline 性能主張はしない段** — headline は段 6。

---

## 1. 1 iteration の駆動プロトコル (メインセッションが回す)

ループ主導権はメインセッション。harness は LLM を spawn しない。1 周:

### (a) planner-v4 を spawn (方向提案・値なし、backoff 軸と無改変で共用)
`Agent(subagent_type='planner-v4')`。入力は段4b runbook と同型 (JSON):
```json
{
  "current_perf": {"throughput_tps": <baseline>, "abort_rate_pct": <baseline>, "last_delta_pct": null},
  "leading_indicators": {"cache_miss_rate_pct": <baseline>, "contention_level": "<...>", "IPC_overall": <baseline>},
  "whiteboard": <loop_state.json の whiteboard (抽象・機序なし)>
}
```
axis は `"silo-writeset-sort"` (段4b は `"silo-backoff-magnitude"`)。**direction/magnitude
の意味論をメインセッション側で具体的に解釈・注入しない** — 「乖離度を上げる」「積極的に
再順序化する」等の言い回しは coder への戦略ヒントの経路になりうるため使わない (敵対
レビュー 2026-07-10)。planner-v4 は sort 専用 fork を作らず段4b と共通の
`.claude/agents/planner-v4.md` を使う (D45 で tools:[] 化済み — 軸間で共通のまま)。
- **単位の換算 (D118)**: `abort_rate_pct` と `cache_miss_rate_pct` は **percent (0..100)** である。
  WAL / calibrator が持つ `abort_rate` と `llc_miss_rate` は **0..1 の率**なので、
  射影時に **×100 する**。換算を忘れると role は 7.9% を 0.079% と読む (100 倍の意味ずれ)。
- 出力 = `{proposal: {axis, direction, magnitude, justification, uncertainty}}` (値なし)。

### (b) coder-v4-autonomous-sort を spawn (comparator コード合成)
`Agent(subagent_type='coder-v4-autonomous-sort')` (tools=[] = ファイルシステム走査経路
なし、リーク制御)。入力:
```json
{
  "leakproof_context": "<src/coder-leakproof-context.md の内容を inline で>",
  "sort_spec": "<coder-v4-autonomous-sort.md の「合成対象と制約」節を inline で>",
  "planner_direction": <(a) の proposal>,
  "baseline": {"throughput_tps": <baseline>, "abort_rate_pct": <baseline>},
  "whiteboard": <抽象 whiteboard>
}
```
- リーク制御 (規律2/6, D39 決定7 を継承): coder には**勝ち筋の comparator 設計・性能利得・
  機序を渡さない**。
- 出力 = `{proposal: {axis, implementation, justification, confidence}}`。`value` は無い
  (backoff 軸との違い)。`implementation` は EVOLVE-BLOCK hole 全体 (`sort(...)` 文一式) を
  置換する複数行コード。

### (c) diff プレビューを取得 (auditor に渡す実 diff + digest を得る、段4b には無い新ステップ)
`coder.implementation` をファイルに書き、harness の `--preview-diff` を呼ぶ (build 不要・
single-tenant 不要、read-only に近い):
```
echo "$IMPLEMENTATION" > <scratch>/impl.txt
python3 -m orchestrator.campaign.p3_s4_loop_sort --preview-diff <scratch>/impl.txt
```
出力 JSON = `{"passed": bool, "working_diff": "...", "diff_digest": "<sha256>", "subtype": ..., "reason": ...}`。
- `passed=false` (フレーム/hole 逸脱) なら auditor を呼ばず、この時点で `<scratch>/prop.json`
  の `auditor` は省略できない仕様なので、`auditor: {"verdict": "reject", "diff_digest": "<空文字列は不可>"}`
  のような回避を試みない — **`passed=false` は diff 検疫 reject として直接 `--run-iteration`
  に渡す** (auditor に見せる価値のある diff にすらなっていないため)。この場合 (b) に戻り
  coder に再提案させる (メインセッションの判断)。
- `passed=true` なら trusted caller であるメインセッションが事前計算済みの `diff_digest` と
  `working_diff` を組にして auditor へ渡す。proposal に採用する digest は auditor が実際の監査後に
  echo した返却値であり、(c) の値を caller が後付けしない。

### (d) auditor を spawn (per-iteration 必須の機械 gate、D41 条件4)
`Agent(subagent_type='auditor')`。入力 (メインセッションが射影、auditor.md の入力隔離
規約どおり fitness/WAL 生ファイルは渡さない):
```json
{
  "working_diff": "<(c) の working_diff>",
  "diff_digest": "<(c) で事前計算した sha256>",
  "designated_sources": ["<patches/silo-sort-variant.patch の骨格 + WriteElement 定義等、必要な API 抜粋>"],
  "abort_digest": {}
}
```
`abort_digest` がある場合は、直近 iteration の赤 digest から verdict/liveness の形状だけを入れ、
性能数値は含めない。`designated_sources` には
`.claude/agents/coder-v4-autonomous-sort.md` の「利用可能な API」節 (`storage_`/`key_`/
`rcdptr_` の宣言) を必ず含める ([T-1356])。closed-region 契約のうち「新しい型/関数の追加」残余
(auditor ギャラリー参照) は、宣言済み API 範囲を auditor 自身が知らなければ判定できない。
欠落させたまま spawn しない。
- 出力 (`auditor.md` の出力節どおり) =
  `{verdict, diff_digest, violations, nits, proposed_tests, uncertainty}`。`diff_digest` は auditor が
  `working_diff` を監査した後、入力で受けた事前計算値を変更せずに echo する。
  `verdict` は `pass`/`reject`/`uncertain` のいずれか。
- 返却 `diff_digest` が入力値と異なる、空、欠落のいずれかなら caller が値を補正してはならない。
  同じ `working_diff` / `diff_digest` の組で auditor に再審査させ、矛盾が解消しなければ iteration を停止する。

### (e) proposal ファイルを書く
`<scratch>/prop.json`:
```json
{
  "planner": <(a) の proposal>,
  "coder":   <(b) の proposal>,
  "auditor": {
    "verdict": "<(d) の verdict>",
    "diff_digest": "<(d) で auditor が echo した diff_digest>",
    "violations": <(d) の violations>,
    "nits": <(d) の nits>,
    "proposed_tests": <(d) の proposed_tests>,
    "uncertainty": "<(d) の uncertainty>"
  },
  "prior_critic_reverse": <前 iteration の critic が逆方向を推奨したか true|false、iteration 1 は null>
}
```
**`auditor.diff_digest` には (d) の返却値を採用する**。digest 自体は trusted caller が (c) で
事前計算し、auditor は同じ digest と組になった `working_diff` を監査してその値を echo する。
次の (f) で driver が build/検疫対象から再計算した実 digest と照合するため、別 diff や古い
iteration の返却値を使い回すと `AuditorGateFailure` で駆動が止まる。

### (f) harness で 1 iteration を実走 (single-tenant!)
```
python3 -m orchestrator.campaign.p3_s4_loop_sort --run-iteration <scratch>/prop.json \
    --allow-coder-derived-build
```
- **`--allow-coder-derived-build` は必須** — coder 由来 source の build は既定拒否であり、
  この明示 opt-in が無ければ `BuildAdmissionError` で止まる (D125)。`--no-build` では不要。
- checkpoint 復元 → critic feedback 畳込み → 入口 check_stop → iteration++ → 挿入→diff
  検疫→**auditor gate (digest 突合 + verdict 判定)**→(pass なら)build×2/verify(legacy+S2)/bench
  → checkpoint 保存 (atomic) → digest 書き出し → 末尾 check_stop。
- `AuditorGateFailure` が飛んだら (digest 不一致・auditor フィールド欠落・verdict と violations の
  矛盾等) **メインセッションの手順ミスまたは監査帰属の破れ** — 値だけを転記し直さず、(c) で
  現在の diff/digest を再取得して auditor に再審査させる。再審査でも矛盾が解消しなければ停止する。
- 出力 = `ran / outcome (rejected|certified|aborted|dry-pass|stopped-before) / iteration /
  停止判定 / checkpoint パス / digest パス`。`rejected` の内訳は WAL の
  `diff_quarantine.subtype` (`frame-altered`/`hole-escape`/`outside-region`/`malformed`
  = 検疫型、`auditor-violation`/`auditor-uncertain` = auditor 型) で読み分けられる。
- **配線リハーサルは `--no-build`** (single-tenant 不要。diff 検疫 + auditor gate の配線
  確認のみ、dry-pass は whiteboard に載らない)。

### (g) 停止判定を読み、続けるなら critic を spawn
段4b runbook §1(e) と同じ (harness は critic の自然文を読まない、メインセッションが
「逆方向を推奨したか」を判定して次 iteration の `prior_critic_reverse` に反映)。

---

## 2. リーク制御チェックリスト (毎 iteration、メインセッションが自己監査)

段4b runbook §2 と同じ排除対象 (sweet-spot literal・機序・利得・WAL/reports/profile・
勝ち筋 VALUE 節) に加え、sort 軸固有の追加項目:
- **planner_direction の解釈をメインセッション側で具体化しない** — "increase" 等の言葉に
  「積極的な再順序化」「乖離度」のような機序含みの説明を足して coder に渡さない (§1(a))。
- **auditor の violations/uncertainty をそのまま whiteboard に転写しない** — whiteboard
  entry は `L.project_whiteboard` が既存の 5 フィールド (機序なし) しか書けない設計なので
  構造的に防がれているが、critic への digest (`s5_sort_loop_digest.txt`) には auditor の
  violations 文が载る (これは critic までの経路であり whiteboard へは流れない、設計通り)。

---

## 3. 停止と継承

段4b runbook §3 と同じ規約 (収束/逆方向枯渇/予算、checkpoint は段6へ継承、reflux on/off
は LLM ablation の対照)。`MAX_ITER`/`MAX_WALLTIME_S` も同じ値 (`L.check_stop` に完全委譲)。

---

## 4. 既知の限界 (実走前に承知しておく)

- 段4b runbook §4 と同じ限界 (delta_pct 常に None・dry-pass は whiteboard に載らない・
  有意性を主張しない・並行 driver は想定しない) に加えて:
- **型14 (非 SWO comparator) は独立 oracle が build 前に閉じた IR への membership で塞ぐ**
  ([T-316] R2-b、[T-2145]、`orchestrator/campaign/sort_swo_oracle.py`)。順序は hole 挿入 →
  diff 検疫 → auditor deny-only veto → **独立 SWO oracle** → build。gate は
  `PASS` / `REJECT` / `UNAVAILABLE` の閉じた結果を返す。
  受理は**閉じた 79 値 sort IR の正準 token 列と完全一致すること**だけで、受理後は正準形へ
  正準化して材へ再 materialize する。関係行列は trusted evaluator が出し、実
  ``WriteElement<Tuple>`` TU の観測行列と byte exact で照合する。
  `REJECT` は admission が候補テキストを受理しなかった場合に出る。
  **IR が確定した評価経路では、compile 失敗・run 失敗・timeout・観測された非決定性・
  実 TU と trusted evaluator の不一致は候補の finding にせず `UNAVAILABLE` へ帰属させる** —
  compile するのは admitted IR から trusted renderer が作った正準形なので、その失敗は
  候補の欠陥ではない。判定不能を `PASS` へ倒す経路は無い (規律 2)。
  環境故障も同じく `UNAVAILABLE` として attempt を止める — 固定長 protocol の異常と
  compiler の起動・signal・wall timeout はこちらである。
  **これは「有限 corpus 上で SWO 公理の反例を探す gate」ではない。** 保証の種類は
  **構成的 SWO + 実 TU conformance** であり、79 値は構成上すべて SWO を満たすので
  `check_relation_matrix` は候補由来では発火しない (恒真化した)。provenance 面では強くなり、
  任意 C++ に対する動的な反例探索能力は失っている。任意 C++ の全入力に対する SWO の証明でもない。
  対象は coder 自律ループが合成する comparator で、s6 sweep の列挙候補
  (SWO-by-construction) は対象外 (s6 からは呼ばれない)。
  **この受理言語の縮小は D39 の raw C++ 独立合成の実証点を別実験へ移す。** D344 が却下理由に
  挙げた実験同一性の論点は supersede されていない (D1451)。
  同一 process 内で任意 native comparator が観測経路へ干渉しうる残余は本 gate では閉じない
  (脅威 α 側の課題で、lexical 効果 gate と sandbox 系統が担当。扱いはユーザー裁定へ返した)。
  既存 timeout (`TRACE_TIMEOUT_S=120`/perf run の `timeout_s=120`) は defense-in-depth として残る。
  write_set_ サイズが小さい探索 (規律4の最小レコード数) では非 SWO comparator でもハングが
  顕在化しない (D42 条件1の実機知見) — 現行 gate はハングの有無によらず、非 IR の候補テキストを
  admission で拒否する。
- **oracle 導入で campaign identity が変わった。** 旧 campaign
  `p3-s5-sort-loop-s5-sort-autonomous-3be89e0d` は**歴史成果物であり再開不可**。
- **型15 (fairness reward hack) の機械観測点も未実装** (規律5、D41 決定3・D42 条件3)。
  現状は auditor 静的目視のみが防壁。発火条件・指標 (Gini係数/max-min比) は phase3.md
  残存リスク節を参照。
- `--isolate-worktree` は**既定 ON** (backoff driver とは非対称、PIN が異なるため)。
  `--no-isolate-worktree` で無効化できるが、共有 tree で backoff driver と交互に走らせる
  場合は `assert_pinned_clean` の PIN 不一致で止まりうる (意図通りの fails-closed)。
