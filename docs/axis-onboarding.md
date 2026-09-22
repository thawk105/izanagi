# 軸オンボーディング手順書 — 新しい変異軸を探索ループに載せるまで

**位置づけ:** 段 8a (軸提案のループ内化、`docs/phase3.md` 後続段) の前提作業として、
D41→D43 + D46 で sort-strategy 軸に 1 回実施した手順を再利用可能な形に固めたもの
(worklog 2026-07-10 (10) の決着)。軸あたり固定費 (実測 ~5 セッション、下記 §6) を下げ、
軸提案をループ内化しても回る水準にすることが目的。

**この文書は戦術層 (自由に更新可)。ただし手順が課すゲート (設計敵対レビュー・positive
control・偵察 firewall・auditor gate) は絶対規律 2/3/5/6 の実装であり、「手順の簡略化」を
理由にゲートを省略してはいけない。このテンプレが削るのは再発見コスト (何をすべきかを
毎回ゼロから思い出す・設計をゼロから組み直す) であって、検証そのものではない。**

先行実施の正本: D41 (設計再評価)・D42 (機構実装)・D43 (driver + auditor 機械 gate)・
D46 (機械 sweep 偵察)。前例 = backoff 軸 (段 4、D39)・sort 軸 (段 5)。

---

## §1. 全体フロー — 順序が本体

sort 軸の授業料: 偵察 (D46) が LLM ループ実走 (iteration 1) の**後手に回り**、死んでいる
可能性のある軸に driver 実装 + E2E の固定費を先払いした。以後の標準手順は**偵察を LLM
ループより先に**置く (worklog 2026-07-10 (10) 決着 3 点目)。

| 段階 | 内容 | 型 (先行実施) | 出口 gate |
|---|---|---|---|
| A | 軸候補の特定 | critic 機序帰属 (P2-4) → 段 8a 本体で LLM 役新設 | 人間承認 |
| B | 軸定義シート記入 + 設計敵対レビュー | D41 | 3 レンズ全員 adopt (条件付き可)。必須条件リストを D 番号で凍結 |
| C | 機構実装 (偵察の前提まで) | D42 | positive control all_pass + identity 実証 |
| D | 機械 sweep 偵察 | D46 | 軸の生死 (floor 超地形の有無) → 人間判断 |
| E | LLM ループ実装 | D43 | 実装前 3 レンズレビュー + テスト緑 |
| F | 実 LLM iteration 1 E2E | worklog 2026-07-10 (2) | outcome=certified |

- **D で死んだ軸は E に進まない** — 固定費削減の核。E/F (driver・coder 定義・runbook・E2E)
  は生きている軸にだけ払う。**この順序が成り立つには、偵察 (D) が依存する軸定数
  (MARKER_ID/SOURCE_REL/TEMPLATE_PATCH/`_BASE`/PIN) を E でなく C の出口で確定させる必要が
  ある** — sort 軸の現物 `s6_sort_sweep.py` は歴史的経緯 (偵察が driver 実装の後手に回った)
  により E 段成果物 `p3_s4_loop_sort.py` を import しているが、これは踏襲しない。新軸では
  軸定数ブロックを C 段成果物 (coverage driver が自前 `_BASE` を持つ `s5_permutation_coverage.py`
  の形) または軸定数だけの共有モジュールとして先に置き、偵察器はそこから import する
  (敵対レビュー 2026-07-10 must-fix)。
- 各段階は**別タスク (別セッション可) に分割する** (規律 5。D40〜D43 の分割が前例)。設計と
  実装を 1 手に束ねない。
- B の敵対レビューは省略不可。C の positive control は**新たな正しさ不変条件を導入する軸で
  省略不可** (verifier 死角を閉じる assert を足すなら、その assert に歯があることの実走証明が
  必須)。sort/lock がこの型。backoff のような「正しさを原理的に壊せない (性能/liveness にのみ
  影響する) 値軸」には対応する positive control driver が存在せず、標準 verify ゲートで足りる —
  ただし「壊せない」という主張自体を B の敵対レビューで裏取ること。「小さい軸だから」は省略の
  理由にならない — sort 軸では設計者自身の安全論拠 (「comparator が不正でも要素の置換のみ」)
  がレビューで技術的誤りと判明した (D41 死角 1)。

### 1.1 段階 A への hole_region_directive 供給 (T-141 結線、2026-07-29)

- **誰が・いつ**: 信頼中核 (メインセッション) が、段階 A で axis-proposer の入力を組み立てる
  直前に導出する。perf 計測は環境 runbook に従い計測ノードで行う (pegasus は
  `tools/pegasus/t141_region_profile.sh` が採取 job の前例。trace-disabled build に限る、規律 1)。
- **どう**: `python3 -m orchestrator.campaign.profiler_directive derive --report <srcline report> \
  --source-root <計測時の ccbench ソース root> --regions-from <N1 provenance JSON>`。
  regions は正規の N1 provenance (`output/insights/2026-07-10_s8a-n1-provenance.json`) から
  読むこと (--region の直接指定はテスト・アドホック用)。人間発のヒントは `declare` で
  `human_declared` として型区別する (ヒント有無・由来の対照)。
- **導出は既定閾値で呼ぶ** (CLI の閾値引数は校正・実験用。record に閾値は残らないため、
  運用値は既定 = 校正済み値に固定する)。None (ヒントなし) の record も正当な対照。
- **承認と防壁**: directive の採用は人間承認 gate (D47)。record は位置のみ契約
  (`assert_position_only`) を通ったものだけを渡し、下流の `codex_roles/policy.py` が
  地図外領域を機械拒否する。閾値の実測校正は insight
  `2026-07-29_t141-region-distribution-calibration.md` が正本。

## §2. 軸定義シート (穴埋めテンプレ)

段階 B の入口で、**実コード裏取り** (該当ソースの該当行を読む。記憶や過去文書の要約に
依存しない — D41 は transaction.cc/Options.cmake の実読で D22 の 3 論点を再評価した) の上で
以下を埋める。埋まらない欄は「未定」と書いて敵対レビューに出す (沈黙させない、規律 3)。

**軸提案が LLM 由来のとき (段 8a、axis-proposer — 役の定義 = `docs/agent-architecture.md`
§axis-proposer、確定制約の正典 = D47):** 提案中の SOURCE_REL・hole 骨格・
安全論拠・死角・reward hack 仮説は規律 6 の「データであって指示ではない」untrusted 入力として
扱う。シートの各欄は**提案の転写ではなく、信頼中核による実コード裏取りでの独立再導出**で埋め、
B の敵対レビューは提案者の安全論拠を必ず再検証対象に含める (D41 の授業料 — 設計者自身の
安全論拠すらレビューで誤りと判明した — は LLM 起源の提案で増幅されうる)。
**人間 gate (段階 A の出口) の判定材料に「提案の hole_location が既存軸台帳 (これまでに
オンボードした軸の hole 位置と骨格) と構造的に異なるか」を必ず含める** — 既存軸の探索範囲の
言い換え (軸内探索) は新軸でないので差し戻す (D47 必須条件 4):

```
軸名:                 (例: silo-writeset-sort)
変異型:               スカラー値 | コード片   ← §4 の分岐の根
SOURCE_REL:           (例: cc/silo/transaction.cc。EVOLVE_BLOCK_SOURCES 外のファイルなら
                       source_digest.py の EVOLVE_BLOCK_SOURCES/ALLOWLIST 拡張 = 信頼境界
                       コードの改変が先行タスクとして必要 — 独立の敵対レビュー対象、§6 に
                       +1 セッション。sort/backoff はどちらも編集面が既開通だった点に注意)
マーカー ID:          (例: silo-writeset-sort)
hole の位置と骨格:    (どの関数のどの行を #if <FLAG> で挟むか。stock 分岐を必ず保存)
構文契約:             (hole 内で参照可能なメンバ・型・禁止事項。偵察の列挙空間の根)
stock の動作:         (変異しない側の意味論)
フラグ名:             CCBENCH_<軸>_...  (値軸=sentinel / コード片軸=on/off。§4)
壊しうる不変条件:     (この変異が原理的に壊せるもの。lost update / UB / liveness / ...)
verifier の死角:      (上記のうち trace schema (C/R/W/X/P) と既存 assert が見ないもの)
reward hack 仮説:     (正しさを壊さずに見かけの throughput を稼ぐ経路。例: fairness 犠牲)
positive control 設計: (何を壊す broken patch を作り、どの検査が赤になるはずか。§3-C)
偵察の列挙空間:       (構文契約からの機械列挙の構成原則 + 安全性の構成的保証)
感度を持つ workload:  (この軸が地形を持ちうる workload を機序から選ぶ。sort=施錠順序ゆえ
                       balanced/write-heavy のみ、read-heavy は落とす。backoff は逆に
                       read-heavy を負け確対照として残した)
計測動作点:           (軸の効果が観測可能になる contention/規模。sort は配線規模 t4/100k
                       では競合が弱く p2_2 確定動作点 t48/1M を採った。floor は同スケールで
                       較正済みか)
```

「壊しうる不変条件 / verifier の死角 / reward hack 仮説」の 3 欄が敵対レビューの主戦場。
sort 軸ではこの 3 欄に相当する検討から死角 2 件 (非 SWO comparator の UB・fairness reward
hack) が出た (D41)。**コード片軸では言語契約違反 (UB) を必ず問診に含める。**

## §3. 各段階の完了定義と成果物

### B. 設計敵対レビュー (D41 型)
- 3 レンズ (auditor 1 + 独立懐疑者 2、workflow 経由・全員が独立コンテキスト)。過去に同じ軸を
  撤回した経緯があれば (sort 軸の D22)、その論点の再評価を必ず含める。
- **(LLM 由来の軸提案のとき) 必須検査 3 点** (D47 必須条件 3・決定 3): (1) 提案軸名・hole
  骨格が axis-proposer への入力射影に既出でないこと (転写の事後検出)、(2) シートに載る機序
  閾値リテラルが critic recommend から転記されていないこと、(3) stock 抜粋の選定 provenance
  (全 mapped 領域との機械的一致で、裁量選定になっていないこと)。照合対象 = 信頼中核が凍結
  する provenance 三点セット (raw critic 出力 / 射影版入力 / 落とした対応表、D47 決定 3)。
- 出口 = decisions.md に D 番号で「条件付き採用 + 実装着手前の必須条件リスト」を凍結。
  却下された安全論拠も「却下」節に残す (同じ誤りを次の軸で繰り返さない)。
- 一次資料 (workflow journal) のパスを D エントリに記録。

### C. 機構実装 (D42 型) — 偵察の前提まで
1. **骨格 patch** (`patches/<軸名>-variant.patch`): EVOLVE-BLOCK マーカー + `#if <FLAG> ...
   #else (stock) ... #endif` + fails-closed ガード (`#ifndef <FLAG>` → `#error`)。pin には
   焼かない (backoff/sort の template patch と同型)。
2. **フラグ配線**: `cmake/Options.cmake` のみで完結させる (`ccbench_universal_definitions()`
   相乗り — protocol 固有 OPTIONS への配線は ALLOWLIST 外改変になる、D42 条件 5)。**この
   相乗りが成立するのは silo hole かつ他 protocol に無害なマクロで表せる場合に限る** —
   protocol 跨ぎ・非 silo の軸では ALLOWLIST 拡張 (信頼境界改変、§2 SOURCE_REL 欄と同じ
   先行タスク) が不可避。identity 実証: stock 側 → `source_digest.resolve()` が
   `src_token="stock"`、variant 側 → 別 digest (cache-miss 相当)。honest-digest (D23/D24)
   との整合を確認。
3. **verifier 死角を閉じる assert** (軸定義シートの死角欄に対応): `#if TRACE` 内・
   **EVOLVE_BLOCK_SOURCES 内で完結させる** (trace.hh 等への波及は guard_write が正当に
   拒否する。既存の `izanagi_trace::stream()` 直呼びで足りる — D42 の学び。hook の拒否を
   迂回しない)。verifier 4 層 (parse/model/core/report) への配線 + pytest fixture。
   assert が submodule ソースに及ぶ場合、**submodule に Co-Authored-By 付き local commit を
   作成し (push は人間、ユーザー承認済み運用 — worklog 2026-07-09 (8))、`pin.py` の
   CURRENT_PIN を前進させる**。この新 PIN が §3-E の worktree 隔離既定を決める因果の起点
   (PIN が既存 driver と異なれば隔離既定 ON、D43)。
4. **positive control**: broken patch を検査点ごとに作り (「N 検査点が別々に歯を持つ」実証、
   D42 の erase/swap が型)、coverage driver (`s3_lock_coverage.py`/`s5_permutation_coverage.py`
   様式 — checks 辞書 + stock control (assert 沈黙) + all_pass 判定) で実走確認。結果 JSON を
   `output/env/<tag>/calibration/` に凍結。characterization の型 = 単一スレッド
   (`SINGLE_FLAGS`) で `total_cycles==0` (verifier は構造的に certify) かつ新 assert の
   violation>0 → indeterminate、で「新 assert だけが赤にできる」ことを決定的に判定する。
   **この型が効くのは単一スレッド決定的実行で観測可能な不変条件に限る** — fairness/liveness/
   統計的にしか顕在化しない死角 (sort 死角 2 = fairness が実例) には characterization を
   作れない。その種の死角は positive control でなく規律 3 の見送り扱い (項 6、指標・発火
   条件の明記) で沈黙させない。
   broken patch の裸マクロは意図的に `CCBENCH_` 名前空間外 (`IZANAGI_BREAK_*`) に置き、
   pipeline から定義不能 = coverage driver + 手動 `-D` でのみビルド可能にする (壊した CC を
   baseline に混ぜない、規律 2)。この非対称性を新軸でも必ず保つ。
5. **auditor ギャラリー型の追加** (軸固有の reward hack / 侵食パターン): `.claude/agents/`
   の変更はユーザー明示承認が必要 (自己変更保護、D42 条件 4 の経緯)。
6. **規律 5 で見送る対策**は指標・発火条件を phase3.md 残存リスク節に明記して沈黙させない
   (sort 軸の fairness 観測点が型)。

### D. 機械 sweep 偵察 (D46 型)
- **入口の前提 = C 段で確定済みの軸定数** (§1 の脚注)。偵察器が E 段 driver を import する
  現状の `s6_sort_sweep.py` の形は踏襲しない。
- 列挙空間 = 構文契約からの機械列挙 + 退化点 + stock。**安全性を構成的に保証**し (sort 軸では
  全点 SWO)、機械検査 (有限モデル総当たり等) で実走前に裏取る — コード片軸でランダム生成を
  使わない理由 (非 SWO ハングを機械検査なしで踏む、D46 決定 4)。**構文契約から有限列挙 +
  構成的安全保証ができない軸では、この段は実施不能** — その場合は偵察を省いて E に進むのでは
  なく、「列挙可能な部分空間の獲得」を設計課題として B に差し戻す (E への無審査昇格の禁止)。
- 動作点 = p2_2 確定動作点 (配線規模 t4/100k は contention が弱く却下済み、D46)。全点
  verify 付き (legacy+s2)。工数の目安: 16 点 ≈ 40〜80 分 (worklog 2026-07-10 (10))。
- **報告カテゴリは「偵察 (preliminary)」** — 事前登録 (phase3-main-experiment.md) のどの構成
  でもないことを明記し、(c) 判定は出さない。firewall: 段 6 正式 grid はこの結果を材料流用せず
  ゼロから再導出、偵察を見た事実を情報源として記録する (D46 決定 1・残存リスク (a))。
- **偵察 → LLM ループの firewall (本テンプレで新設)**: 偵察を LLM ループより先に置く再配置は、
  D46 が想定しなかった漏洩隣接を作る — 偵察 insight には勝ち点の具体実装・順位が逐語で載る
  (D46 の sk_ad が実例) が、それを読んだ人間が E/F で coder 入力 (leakproof_context) や
  planner direction を起草する。**ループへ消費させるのは二値 (floor 超地形の有無 = 軸の生死)
  のみ**とし、偵察の具体勝ち点・実装・順位を coder/planner の入力に流さない。偵察 insight を
  見た事実は campaign provenance に情報源として記録する (D46 残存リスク (a) のループ版)。
- LLM 由来でない機械生成候補には auditor 目視を課さない。ただし AuditorVerdict の自己生成
  (self-attest) はしない — 段そのものを省く (D46 決定 3)。
- 出口 = 「floor 超地形が見えるか」を insight に凍結し、**継続/軸見直しは人間判断**。

### E. LLM ループ実装 (D43 型)
- **兄弟 driver** (`p3_s4_loop_<軸>.py`): 汎用ヘルパ (`quarantine`/`record_diff_reject`/
  `make_critic_digest`/`check_stop`/`LoopState` 永続化) は `campaign.p3_s4_loop` から import
  再利用。`diff_quarantine.py` は marker_id/source_rel パラメータ化済みで変更不要 (D41 却下案)。
  軸固有部分 = genome 構築・proposal スキーマ・pre-build 整合チェック (§4)・PIN。
- **PIN が backoff driver と異なる場合は worktree 隔離を既定 ON** (`--no-isolate-worktree` で
  opt-out) — 共有 tree での `assert_pinned_clean` 衝突を避ける (D43)。`_resolve_duplicate` 系の
  ヘルパに `ccbench_dir` を明示的に渡す (worktree 隔離下の tree 取り違え、D43 必須修正)。
- `_BASE` に依存フラグ (`BACK_OFF: 1` 等) を明示 — Options.cmake の CACHE 既定への暗黙依存を
  避ける (D43)。`search_config["verify"]="legacy+s2"` を default_cfg に明記 (設計採用の根拠が
  S2 の競合再現にあるなら、driver 自身がそれを満たす構成でないと採用の土台が崩れる、D43)。
- **coder 定義** (`.claude/agents/coder-v4-autonomous-<軸>.md`): fresh subagent・tools なし
  (D39 決定 7 の構造遮断)・構造化出力のみ。**出力スキーマに具体戦略の例示を書かない** (例示
  経由のリーク、D43 必須修正)。planner-v4 は無改変で再利用し、direction の意味論を軸ごとに
  機序含みの言葉で具体化しない (reward hack 誘発、D43)。
  **例外: §4 第 3 列の軸 (関数群・複数 hook・状態) では planner を外す** (D2214 決定 8)。
  planner-v4 の方向契約 (増加 / 低下 / 両探索 + magnitude) が、複数 hook・補助関数・状態型に
  合わないためである。この型では兄弟 driver と tool なしの coder role を、C++ 版と IR 版の
  2 つの出力形で新設する。`.claude/agents/` の変更はユーザー明示承認を条件にする。
- **runbook 兄弟文書** (`docs/phase3-s5-sort-runbook.md` が型): 実走前ゲート + iteration
  プロトコル + 停止条件。
- 実装前に 3 レンズ敵対レビュー (リーク制御/fails-closed/regression)。fails-closed の検査
  (フィールド欠落・未知 verdict で例外) をテストに含める。
- テストは既存駆動 (`orchestrator/tests/test_p3_s4_loop_sort.py` が型) に倣う。

### F. 実 LLM iteration 1 E2E
- **新設エージェント定義は同一セッションで spawn できない** (登録はセッション開始時のみ、
  2026-07-08 実証) — E とは必ず別セッション。runbook の実走前ゲート (single-tenant 確認・
  pin clean・テスト緑・calibration) に従う。
- `--preview-diff` → auditor spawn → proposal JSON → `--run-iteration`。digest 転写は
  スクラッチファイル経由の改行混入で `AuditorGateFailure` になった前例あり (worklog
  2026-07-10 (2)) — implementation 文字列は JSON から直接抽出する。
  (trigger-gating 軸は [T-428] で wire-only 化し、CLI も `--preview-wire` — 同軸の現行手順は
  `docs/phase3-s8a-trigger-runbook.md` が正本。本節の `--preview-diff` 記述はコード片軸の型)
- `--no-build` での配線リハーサル (dry-pass) は実走と campaign identity (内容ハッシュ決定論、
  D13) を共有するため **iteration カウンタを 1 消費する** (whiteboard には載らないため整合性は
  保たれる。guard_bash が campaign dir の改変を拒否するので放置してよい)。iteration 番号の
  ずれを想定しておく (worklog 2026-07-10 (2))。
- 出口 = outcome=certified (verify legacy+s2 とも anomaly 0)。

## §4. 変異型による分岐 — スカラー値軸・コード片軸・関数群軸

**最初の二型は「これまでに実施した 2 軸」の分類であり、全変異軸の網羅ではない。** どの列にも
綺麗に当てはまらない軸 (複数 hole にまたがる軸・値とコード片の複合軸・データ構造/型選択の軸
など) が来たら、手順を無理に当てはめるのではなく**本テンプレ自体を改訂し (この表に列を
追加)、その改訂を D41 水準の敵対レビューにかける**。
(注: trigger-gating 軸は [T-428] で「固定 5-bit wire 軸」へ移行しコード片二型のどちらでも
なくなった。第 3 列の追補は本注記のみとし、テンプレ本体の改訂は D41 水準レビューを伴う
独立の変更単位で行う — 現行手順の正本は `docs/phase3-s8a-trigger-runbook.md`)既存機構の単一 hole 前提
(`diff_quarantine.parse_template_file` は marker_id 単数) もその際に見直し対象になる。

**第 3 列 (関数群・複数 hook・状態の軸) は、この規定に従って足した列である。** 軸
`silo-function-policy` の段階 B (D2214) で起草し、同軸の設計 wave の 3 レンズ (codex 2 本 +
auditor role) と焦点再レビュー 3 巡で攻撃した (案と逐語は
`output/insights/2026-09-21/silo-function-synthesis-space/README.md` の §8・§11)。**先の 2 列は
実施済みの軸から起こしたが、第 3 列は段階 B の設計の採用に基づき、段階 C 以降の実施ではまだ
裏付けられていない。** 段階 C〜F の実測と食い違ったら、この列を改訂する。

| 論点 | スカラー値軸 (backoff が型) | コード片軸 (sort が型) | 関数群・複数 hook・状態の軸 (silo-function-policy が型、D2214) |
|---|---|---|---|
| フラグ設計 | 数値 sentinel (`BACKOFF_FIXED`) | on/off (`SORT_VARIANT`) | on/off (`SILO_POLICY_VARIANT`)。型・状態・呼出し点・要因記録を全て軸 OFF で消す。軸 ON が前提とする他 flag (`BACK_OFF` と no-wait 系) は `#error` で固定する |
| coder 出力スキーマ | `value` + 実装 literal | 実装のみ (`value` なし) | C++ 版は単一領域の implementation (`value` なし)、IR 版は IR JSON。どちらも justification は台帳に残すが、critic と次の coder には渡さない |
| pre-build 整合チェック | `assert_value_literal_consistent` (値と literal の機械照合) | **auditor 機械 gate** — `auditor.diff_digest` (sha256) を proposal 必須フィールドにし、driver が実 diff の digest と機械照合。不一致 = `AuditorGateFailure` で即停止。「宣言止まり」(照合なしの verdict 参照) は fail-open であり不可 (D43) | 単一領域の検疫 + effect gate + 型付きの構文検査 + 単独 TU compile + 実 diff に束縛した auditor gate (LLM 由来の候補)。構文検査が閉じた領域制約に代わるのはこの型だけで、先の 2 型の受理集合は変えない |
| 安全性の問診 | 値域・オーバーフロー | **言語契約 (UB) を必ず含める** — 非 SWO で introsort が OOB/ハング (write_set 16 要素 = insertion-sort 閾値、D42 条件 1)。「クラッシュしない」は恒真化した安全に見える罠 | UB (式の型・初期化・shift・除算)・状態の寿命・停止・呼出し graph・外部参照・代替綴り・lock 保持時間・公平性。IR の保証を自由 C++ に拡張しない |
| 偵察の列挙 | 値グリッド | 構文契約からの構成的列挙 + 安全性の機械検査。ランダム生成は不可 (D46 決定 4) | 構成的に安全な型付き IR の部分空間。部分空間の結果と全空間の生死を区別する |
| auditor の役 | 目視 (段 4 では未配線) | pre-build 機械 gate + ギャラリー型目視 | 関数・状態と固定骨格の境界、代理、公平性、検証条件への依存を監査。非 LLM の機械 IR 候補は auditor 段を省くが、endpoint 候補と勝ち候補の公平性目視は課す |
| marker と呼出し点 | — (第 3 列で足した論点) | — (同左) | marker は 1、呼出し点は複数。呼出し点と namespace の外枠を hole にしない |
| 状態 | — (第 3 列で足した論点) | — (同左) | 骨格が所有する 1 個を参照で渡す。hole は書換え可能な持続状態 (静的・thread 記憶域の可変変数) を定義しない (namespace の constexpr 定数は可) |
| 実験主張 | — (第 3 列で足した論点) | — (同左) | IR 内の探索法比較と C++ 空間拡張の比較を分けて報告する |

補足: ASan/UBSan での positive control (D41 条件 1) は実機で「UBSan は masstree の既存無関係
UB (`kpermuter.hh` shift exponent) でノイズになる」と判明済み — driver 化する場合は UBSan を
外すか既知 UB を許容リストする (D42)。第 3 列の軸は候補ごとの sanitizer を置かない。型付きの
部分言語が UB の型を構造的に除き、検査器の誤りは段階 C の UBSan 付き単独 TU harness 1 回
(CC ヘッダと masstree を含めない) と検査段ごとの自己試験で見る (D2214)。

## §5. 規律チェックリスト (各段階の出口で確認)

- [ ] 正しさゲートを緩める方向の簡略化をしていない (規律 2)。verdict/整合チェックは
      fails-closed か (欠落・未知値で例外に落ちるか)
- [ ] 見送った対策に指標・発火条件を明記した (規律 3)
- [ ] 段階を 1 手に束ねていない。1 作業単位 ~15 分粒度 + handoff 更新 (規律 5、作業の進め方 8)
- [ ] リーク制御: coder に勝ち筋の値・具体戦略が届く経路 (出力スキーマの例示・planner
      direction の具体化・文書経由 = D45 の文書地雷) を作っていない (D39 決定 7/D45)
- [ ] 偵察 insight の具体勝ち点・実装・順位を coder/planner 入力に流していない — ループへ
      渡すのは軸の生死の二値のみ (§3-D の新設 firewall)
- [ ] (LLM 由来の軸提案のとき) シートの各欄を提案の転写でなく独立再導出で埋めた (規律 6、§2)
- [ ] `.claude/agents/` の変更はユーザー明示承認を得た
- [ ] hook (guard_write/guard_bash) の拒否を迂回していない (D42 の学び — 拒否は仕様)
- [ ] 偵察結果と正式実験の間に firewall を明文化した (D46 決定 1)
- [ ] 性能数値は計測層のみ・env タグ付き・単一テナント確認済み (絶対規律 4 は本手順でも不変)

## §6. 工数予算 (テンプレ化前の実測、sort 軸)

B 設計レビュー 1 セッション (3 レンズ ≈ 38 万 token、D41/worklog 2026-07-09 (7)) /
C 機構実装 1 セッション (Explore×5 併用、worklog 2026-07-09 (8)) / E driver 1 セッション
(3 レンズ ≈ 37 万 token、worklog 2026-07-10) / F E2E 1 セッション / D 偵察 1 セッション
(設計 3 + 実装 2 レンズ + 実測 40〜80 分)。**計 ~5 セッション/軸。**

この実測は sort 軸の好条件 — 編集面 (transaction.cc) が D38 で既開通・verifier 死角が実質
1 個 (permutation)・計測動作点 (p2_2) の floor 既測 — の下の値。C の工数は死角数 (各々
assert + broken patch + coverage 検査点) に比例し、編集面未開通なら信頼境界改変 + 再レビューで
+1 セッション、floor 未較正なら較正が別途要る。

**テンプレが削るのは B〜C の再発見コスト (何をすべきかをゼロから思い出す) と E の新規設計
労力であり、生存軸のゲート実行 (B レビュー・C positive control・D 偵察・E 実装前レビュー・
F certify) はどれも削減対象ではない** — 生存軸は今後も 5 段ぶんのゲートを全部通る。
「2〜3 セッション/軸」に短縮できるのは D で早期死する軸 (~3 セッションで打ち切り) と、
各セッションの中身が薄くなる (再発見ゼロで写経中心になる) ことによる実時間短縮であって、
段の統合・ゲートの省略 (規律 5 違反) によってではない。

## §7. 資材対応表 — 何を再利用し、何を軸ごとに作るか

backoff 軸 (段 4) と sort 軸 (段 5) の実装差分の機械的洗い出し (2026-07-10、5 並列読解) に
基づく。**兄弟ファイルを並べて diff を取ると、それがそのまま「新軸で埋める穴」の一覧になる**
— loop driver は `p3_s4_loop.py` ↔ `p3_s4_loop_sort.py`、coverage driver は
`s3_lock_coverage.py` ↔ `s5_permutation_coverage.py` が 1:1 の写経関係 (注意: s3 の対は
段 3/D38 の lock 被覆機構であり backoff 軸の対物ではない — backoff は正しさ不変条件を導入
しない値軸ゆえ coverage driver 自体を持たない、§1 の positive control 条件参照)。

### 7.1 無改変で再利用するもの (新軸で手を入れたら設計ミスを疑う)

| 資材 | 内容 |
|---|---|
| `p3_s4_loop.py` の `L.` ヘルパ群 | `quarantine` (marker_id/source_rel はパラメータ)・`record_diff_reject`・`make_critic_digest` (tag だけ差替)・`check_stop` (停止規約は軸非依存 — 独自の停止基準を作らない)・`LoopState` 永続化 (軸固有フィールドを足さない)・`project_whiteboard` (5 フィールド射影 = 構造的リーク防御。軸固有情報を whiteboard に足すのは禁止)・`_fold_critic_reverse`・`default_perf` |
| `diff_quarantine.py` | marker_id/source_rel パラメータ化済みの汎用実装 (D41 却下案で確認済み)。**単一 marker/source 前提** — 複数 hole 軸では `parse_template_file`/`quarantine` の複数マーカー対応が必要 (§4 冒頭のテンプレ改訂経路) |
| sweep の器 (`s6_sort_sweep.py` の骨格) | `run_sweep` 直列駆動 (WAL 追記・中断再開 replay skip・abort 隔離)・`_eval_one` 配線・`_replay_outcome` (replayed-certified/aborted の区別)・`_write_provenance` (merge + 逐次書き)・`config_for` の identity ハッシュ分離・`--remeasure` cross-run 裏取り・worktree 隔離 + build-variants キャッシュ・`report()` 記述統計骨格・floor 判定不能の fails-closed。**注意: 器そのものが sort (D46) 単独由来の n=1** — backoff に偵察の対物はなく、2 軸目の適用で初めて汎用性が実証される。また現物は E 段 driver を import しているため §1 脚注の張り替えが要る |
| `source_digest.resolve()` | Options.cmake HEAD 版から既定値を自動で読むため新 CACHE 変数を自動で拾う — 機構改変不要、新軸では検証 (stock→`src_token="stock"` / variant→別 digest) の実行のみ |
| `planner-v4.md` | 無改変 (D43 で確定、D45 で tools:[] 済み)。出力例の axis 名が backoff のままでも改変しない |
| `auditor.md` の骨格 | 役割定義・入力隔離・二層判定・出力スキーマ・規律。軸固有はギャラリー型とチェックリストの**追記のみ** |
| coder 定義の共通文言 | tools:[] / fresh subagent / 3 制約 / Model Y (D39 決定 7) の文言・「具体戦略の一言要約フィールドを出力スキーマに書かない」禁止 |
| runbook の骨格 | 5 節スケルトン (§0 実走前ゲート 5 点 / §1 駆動 / §2 リーク制御 / §3 停止と継承 / §4 既知の限界) + 「設計判断は書かない、矛盾は正典が勝つ」但し書き。§3 は backoff runbook への参照 1 文で済む |
| 偵察 firewall の政策 | D46 決定 1 が正本 (軸非依存)。コードへの文言複製は per-axis (7.2) |
| broken patch の隔離規約 | out-of-tree・裸マクロ `CCBENCH_` 外・既定 OFF inert (`patches/README.md`) |
| characterization 型 | `SINGLE_FLAGS` + 「cycles==0 かつ violation>0 → indeterminate」判定。単一スレッドで観測可能な不変条件に限る (§3-C の条件) |

### 7.2 軸ごとに写経・特殊化するもの (テンプレの「穴」)

| 資材 | 埋める穴 |
|---|---|
| 軸定数ブロック (**C 段の出口で確定**) | MARKER_ID/SOURCE_REL/TEMPLATE_PATCH/`_BASE`/PIN (新 driver は `pin.CURRENT_PIN`、歴史的 driver は literal 保持)。§1 脚注のとおり E 段 driver でなく C 段成果物または共有モジュールに置き、偵察器 (D) と loop driver (E) の両方がそこから import する |
| 兄弟 loop driver (E 段) | `run_one_iteration`/`drive_iteration`/`default_cfg` (verify 配線含む)/`load_proposal_file`/`main` CLI + fixture・`_resolve_duplicate` (worktree 隔離既定に合わせ `ccbench_dir` 明示)・digest ファイル名/critic tag (campaign 出力の分離) |
| worktree 隔離の既定値 | 自軸 PIN が現行共有 tree と一致するかで決める (不一致なら既定 ON)。非対称は runbook §4 に明記 |
| 骨格 patch (`patches/<protocol>-<軸>-variant.patch`) | EVOLVE-BLOCK マーカー対 (id は driver の MARKER_ID と一致)・`#if`/`#else` (stock 逐語温存)/`#endif` 二枝・fails-closed `#error` ガード・閉領域制約の定型文 (D23 道 Y — 冒頭の変異内容 1 文だけ軸固有)・cmake universal 相乗り配線 (`CCBENCH_<軸>` の CACHE 行 + 定義関数 1 行) |
| positive control patch + coverage driver | 検査点ごとの相補的な broken patch・checks 辞書 (stock control は不変、mutation 側は検査点数ぶん)・trace 行パース (行 prefix・reason の列位置は軸固有 — X 行は parts[3]/txid あり、P 行は parts[1]/txid なし)・verifier 4 層への Integrity フィールド配線 + pytest fixture |
| variant patch 3 役 | identity 後方互換 (`variant-noop-else-copy` 型 = 合成枝が #else の逐語複写 → cache-hit 実証)・certified 緑 1 周 (sweep 済み非勝者点でリーク制御)・(任意) red consumer。**注意: 3 役とも kickoff/backoff の資産で sort 軸では未作成** — 実施済み手順でなく踏襲推奨の型として読む |
| coder 定義 (`coder-v4-autonomous-<軸>.md`) | frontmatter (段番号/name/description)・合成対象と制約 (骨格提示・利用可能 API・型シグネチャ・正しさ契約)・出力スキーマ (§4 の軸型分岐) |
| auditor ギャラリー型 | 軸固有 reward hack 型を連番で末尾追記 + 「何を見るか」チェックリスト対応項目 (**ユーザー明示承認が必要**) |
| runbook 兄弟文書 | §0 ゲート 1 の agent 名列挙・ゲート 3 の PIN 記号参照 (`<driver>.PIN` = `pin.CURRENT_PIN` の形で書く — **値の literal を runbook に書かない**。pin 前進で腐る、2026-07-12 監査)・§1 の軸固有段・§2 の軸固有リーク経路追記・§4 の軸固有 failure mode + 機械 backstop の有無 (未実装なら発火条件を明記) |
| 偵察 sweep | 列挙生成器 + CANDIDATES・構文契約・退化点/対照点の選定・WORKLOADS (感度で絞る)・動作点・firewall 文言のコード内 4 箇所 (docstring/spec_content/report 冒頭/floor fails-closed)・偵察報告書 (insight) の定型節立て (位置づけ→実験→結果→示唆 (判断しない)→還元判断) |
| 台帳更新 | decisions.md (D 番号)・worklog 末尾・phase3.md への記録・(submodule assert を足した場合) `pin.py` の CURRENT_PIN/PREVIOUS_PIN。driver docstring と runbook は設計を書かず正典を指す |

### 7.3 変異型で設計自体が分岐するもの

§4 の表が正本 (表のどの列にも収まらない軸はテンプレ改訂 + 再レビュー、§4 冒頭)。存在自体が分岐する
資材: `--preview-diff` CLI・auditor spawn 段・`diff_digest` 照合 (コード片軸のみ) /
`assert_value_literal_consistent` (スカラー値軸のみ) / mutation-red (**言語契約 = UB** の
positive control、コード片軸のみ) / 列挙生成器 vs 数値グリッド。positive control の二種を
混同しないこと — 「新 assert に歯があることを証明する broken patch + coverage driver」は
新しい正しさ不変条件を導入する全軸で省略不可 (§1)、「UB 用の mutation-red」はコード片軸のみ。
**新軸オンボードの最初の分岐点は変異型の判定** — この一点から出力スキーマ・pre-build gate・
runbook の段数 ((a)-(e) 5 段 vs (a)-(g) 7 段) がすべて派生する。どの型でも
「build 前に coder 出力が hole 契約を破っていないかを機械で弾く fails-closed な一次防壁」の
軸版を必ず設計する — 無いと正しさゲートを緩める変異が採用されうる (規律 2、D41 残存リスク)。

### 7.4 テスト複製の最小集合 (共有機構は再テストしない)

`test_p3_s4_loop_sort.py` の方針 (docstring に明記) を踏襲: 共有機構 (`L.` ヘルパ・検疫・
LoopState) は backoff 側テストが済ませており再検証しない。新軸で複製するのは —
1. **gate fails-closed**: digest/literal 不一致で例外・構造検疫が意味 gate に先行・
   verdict subtype の区別
2. **proposal schema fails-closed**: 必須キー欠落 = KeyError・未知 verdict 拒否・
   空 digest 拒否・スカラー軸なら「value がある」/コード片軸なら「value が存在しない」
3. **default_cfg 配線**: 自軸の verify 相・axis・PIN が cfg に載ること
4. **drive_iteration 入口停止 + checkpoint 継続** (pinned-clean skip ガード付き)
5. (コード片軸のみ) digest ヘルパ決定性・列挙空間の安全性有限モデル検査・言語/生成形式の
   落とし穴 (sort では無名引数 (-Werror)・コメント禁止 (preprocess 後ハッシュ)・
   参照メンバ契約) の機械番人
