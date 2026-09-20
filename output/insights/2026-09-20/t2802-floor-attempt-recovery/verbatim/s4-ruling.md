# 段 4 裁定 — [T-2802] per-call memo による attempt ledger 回復の二乗構造の局所修正

裁定時刻: 2026-09-20 07:35 JST (この file の mtime を正とする)。入力: `s1-brief.md`、`codex/s2-plan.md`、`codex/s3-consult-A.md` (正しさ境界)、`codex/s3-consult-B.md` (実効性・測定設計)。裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox`) に T-2802 関連の更新なし。local main は `b7f970dfa` のまま。

## 1. 所見の裁定 (real / refuted、採否、scope)

| # | 所見 | 裁定 | 採否 | 反映先 |
|---|---|---|---|---|
| A-N1 | 受理集合の対応表は「一呼出し中、読取対象・読取結果が安定」の条件下で成立。無条件の実行履歴同値と書くのは過大 | real | 採用 | I1 の文言を訂正 (§3) |
| A-N2 / B-M2 | P5 (main ledger 生読取の呼び出し内共有) は既存の main 読取位置 (H:4737 / H:4946) での遅延初期化なら受理集合不変。eager (先読み) は例外順序を変えるので不可。target claim の coverage 失敗時は main 読取 0 回 | real | 採用 (遅延形のみ) | plan v2 §2、test の回数期待 §4 |
| A-S1 / B-S4 | plan の参照実装 (test 内に走査を写し変更後 helper を呼ぶ) は旧実装との独立比較にならない | real | 採用 | 差分 probe は base module (`b7f970dfa` 逐語) を別名 module で load する **wave 時 probe** (repo へ入れない)。repo の恒久 test は固定 literal の期待文書・message で書く (§4) |
| A-S2 | 変異台帳は「KILL」「狙った理由での KILL (最初の拒否位置)」「新規検出力 (新 test だけが検出)」を分ける。T:2729 / T:2750 が既に検出する変異を新規検出力に数えない | real | 採用 | 変異事前登録 §5 に 3 欄 |
| A-S3 | test 5 群だけでは I1〜I5 の全項目を実証したと書けない。unsafe entry、reader の各 message、filter 順序、main ledger reader の各例外、呼び出し間の main 改竄、`__all__`/signature の差分確認を台帳化 | real | 採用 | §4 の被覆台帳を author に書かせる。静的到達不能 (A≠marker、target≠canonical_target、marker identity 重複) は理由を記録し負例で埋めない |
| A-N3 | lock 契約外 (advisory lock 無視・一過性 I/O) の差は既存契約の限界として insight に記録。新 gate・再読は不要。lock なしで候補関数へ到達する production 経路なし (validate は H:5082 入口・H:5094 lock、registry trigger H:5676 は単文書 wrapper) | real | 採用 | insight §限界 |
| A-N4 | A≠marker (H:5296)、target≠canonical_target (H:5304)、marker identity 重複 (H:5276) は静的 root で到達不能 (同 identity は同じ canonical 文書 F(identity) に再導出される) | real | 採用 | 変異に含めない。production の防御は残す。理由を insight と test の docstring に記録 |
| A-N5 | legacy (v1) fixture は現行 producer の経路ではないが、変更対象 H:4670 の legacy branch の同値性検証に要る。「legacy 読取互換性の unit fixture」と明記して維持 | real | 採用 | §4 |
| A-N6 | brief の訂正 6 点 (P3 の「最初の marker」→「target を含む最初の利用」、main writer 4 箇所に R33 H:3168 は含まれ不足は claim 公開 H:3171〜3173 の説明、`floor_attempt_requires_cut6_replay` は H:5330 / validate は H:5082、P2 の v1 digest 費用は代表 node の説明にならず「1 s 未満」は未測定、P4 は同一 SHA 比較でない、fixture scope の趣旨、launcher は別 author) | real | 採用 | §3 |
| B-M1 | 本 wave の must-fix 基準に「A/B 対表・判定・insight・裁定内容を変える欠陥」を含める (性能の速度予想やコードの好みは除く) | real | 採用 | §3、段 6 レビューの基準 |
| B-M3 | 200 s はノイズから導いた閾値でなく実用上求める削減量。T-2766 (同一 code の A/B) の floor 対差は 22 / −211 / 60 s (中央値 22 s) で、無変更時の対差の幅は ±200 s 級。一次指標は 523 node 全体を維持し、事後の部分集合選別は不可。補助は測定前に凍結した部分集合 | real | 採用 | §6 (凍結済み `floor-subset-frozen.json`) |
| B-M4 | A (base tree) / B (実装 tree) の比較は D2068 の「同一 tree 内で方式を交互」条件を満たさない。完全 SHA・実 path・tracked 差分を固定・保存し、docs/output の無関係な変更を測定 tip に混ぜない。裁定パッケージに測定契約の差を明記 | real | 採用 | §6、insight の裁定パッケージ節。**測定 tip B = 実装 commit (production + test) だけ**。記録 commit は測定後 |
| B-M5 | 無効対と B 実装起因の赤を同じ再試行規則に入れない。原因未分類の赤は系列停止。B 実装起因なら測定終了 → 修正 → 新系列 (旧系列と合算しない)。インフラ起因と確認できた対だけ同順序で取り直す。全投入 12 走上限、片走は流用しない | real | 採用 | §6 |
| B-M6 | 「523 件」だけでは同一性を保証しない。完全 nodeid 集合を凍結し、各 node ちょうど 1 件・同一実行状態・有限非負 time を検算。top-level junit は合算しない。B の追加 admission test は所属 file で除外 (間接効果は残ると明記) | real | 採用 | §6 (`S_all` 凍結済み)、集計器の要件 |
| B-S1 | 両 tree の bytecode 条件を対称にする (固定 SHA 確定後に両 tree で同じ計算ノード collect-only 1 走、pyc 書込設定・件数を記録)。受入 launcher の恒久 warm-up 義務化ではない | real | 採用 | §6 手順 |
| B-S2 | 親の一般化の分類: 「4〜12 s 帯 = 二乗 node」は誤り (時間帯は経路分類でない)、「48w では比例しない」は妥当、「400〜500 秒削減」は未実測の条件付き予想 | real | 採用 | §3、insight で 12w profile / 48w A/B を別列に |
| B-S3 | 3 対は限定的な実用判定には足りるが位置効果の相殺・因果確定には足りない。AB/BA/AB 固定、有効 3 対で固定終了、`W_max = max(W_0, W_1, W_2)` | real | 採用 | §6 |
| B-N1 | helper の粒度は成果物を変えない。optional な呼び出し内 context 1 個でも可。既存 wrapper 維持 | real | 採用 (author の裁量、上限 §5) | plan v2 |
| B-N2 | scope 外候補の扱い: 残る二乗性・claim 数増加・snapshot/clone の限界と cross-call cache 不採用は insight で十分。`floor_attempt_requires_cut6_replay` の意味変更、snapshot 共有等は別裁定。別 tree 比較と D2068 の測定契約の差は今回の裁定パッケージに明記 | real | 採用 | insight |
| plan 「1 s 未満」の brief 記述 | 未測定の仮説。plan の候補部分 1〜3 s / node 全体 2〜4 s も暫定仮説 (実測範囲でない) | real | 採用 | 段 6 の焦点走 (計算ノード) と A/B で確認。受入条件にしない |
| plan 変異 M2 (exact-key 省略 + extra key 破棄) | 二つの防御を同時に弱める複合変異で、T:2729 が既に検出 | real | **不採用** (変異から外す。extra-key の test は残す) | §5 |

scope 外の real 所見で裁定パッケージにするもの: 「別 tree 比較は D2068 の同一 tree 条件を満たさない」という測定契約の差 (insight の裁定パッケージ節で採否の射程として明記)。他は insight 記録。

## 2. plan v2 (設計、file:line は `b7f970dfa` の現物)

- 候補関数 `_floor_attempt_recovery_candidate_locked` (H:5230) の**ローカル**に呼び出し内 context (projection memo + main ledger 行列の遅延 slot) を 1 個作り、H:5236 (target)、H:5270 (各 marker)、H:5287 (各 A 行) の 3 箇所だけ memo 対応 helper を通す。module 変数・呼び出し跨ぎの保持は禁止。
- memo key は `(attempt_schema, claim_digest)`。**成功済み (marker equality まで通った) projection だけ**格納。失敗・部分結果は保存しない。
- hit でも毎回: marker の exact shape・schema・role・digest・attempt_id 検査 (H:4675〜4689 / 4801〜4816 と同順)、`attempt_id in projection.attempt_ids` (同 message)、既存 constructor (H:4613 / H:4564) で期待文書を組み、marker 全体との equality (MUT-A2)。
- miss: schema 別 projection helper が既存位置・既存順序で claim 読取 → claim 検査 → (v1: coverage → entry/seams; generation: entry/seams → coverage) → main 行選択・検査 → expected_main 比較を行う。**P5**: main ledger の `_read_ledger` は H:4737 / H:4946 相当に初めて到達したときだけ呼び、その生行列を同一呼び出し内で共有する (未読 sentinel で空リストと区別、行列は変更しない)。v1 の全 floor 行 shape/key/digest 検査 (H:4738〜4753) は miss ごとに従来どおり全行へ掛ける (検査対象行の集合を変えない。generation 経路へ追加しない)。
- 既存 signature `_canonical_floor_attempt_ledger_row(root=, marker=)` / `_canonical_measurement_generation_floor_attempt_ledger_row` / `_measurement_generation_main_ledger_row` は wrapper として維持 (memo なし、毎回完全再導出)。他の呼び出し元 (H:5052、H:5676、T:2197) は変えない。
- 走査順・filter・path 検査 (H:5271)・identity 重複 (H:5276、5291)・A 行の marker 不在/不一致 (H:5293〜5297)・最終判定 (H:5300〜5311) は変更なし。早期 `None` 不可。
- helper の粒度は author の裁量 (plan の 5 関数 + データ型、または context 1 個 + 分割最小)。検査順の移動と重複 code を最小にする。
- 規模上限: production の差分 +300 / −150 行以内、test の差分 +900 行以内 (超過は所見が閉じても差し戻し)。

## 3. brief の訂正 (erratum、brief 本文は書き換えない)

- I1: 「任意の root 状態」→「一呼出し中に読取対象・読取結果が安定した root 状態」に対する (戻り値、例外型、message 全文) の一致。lock 契約外の実行履歴同値は主張しない。
- P2: 代表 node は measurement-generation 経路で、v1 の main 行ごとの `_claim_digest` は代表 node の直接の律速ではない。主要項は marker / A 行ごとの claim 読取 + main ledger 全読 (+ v1 では行ごとの digest)。「1 s 未満」は取り下げ、効果は未測定 (作業仮説: 候補部分 1〜3 s、node 全体 2〜4 s)。残る二乗成分 (marker 読取 k 件/呼、A ledger 全読、constructor・比較 q 回、sort) により全体は線形化しない。claim 数が attempt 数と共に増える条件では projection 部分にも二乗性が残る。
- P3: 「最初の marker」→「target を含む最初の利用」。
- P1: main ledger の append 4 箇所 (H:1909 / 2169 / 3168 / 3797) は全て lock 内 (R33 H:3168 を含む)。claim の公開は各 reservation の lock 内 (H:1760 / 2158 / 3786) と R33 の `_r33_publish_exact` (H:3171〜3173、lock 内)。「claim は reservation の `_write_exclusive` だけで書く」は不十分だった。
- 行番号: `floor_attempt_requires_cut6_replay` の定義は H:5330 (H:5327 は前関数の末尾)、`validate_floor_attempt_consumption_marker` の定義は H:5082 (H:5040 は内部 helper)。
- P4 / 成果物 4: A = base `b7f970dfa`、B = 実装 tip で**同一 SHA 比較ではない**。条件内では全反復同一 SHA。
- 「fixture 側の変更は scope 外」= 既存 fixture の高速化を除外する趣旨。新規 regression fixture (複数 cell、legacy 読取互換) は許す。
- launcher / 集計器 / 差分 probe は別 author (unit-probe worktree) の所有物。production author の編集対象に混ぜない。
- 「4〜12 s 帯 (65〜68 node) ≈ 二乗 node」は同一視しない。「400〜500 worker 秒削減」は未実測の条件付き予想 (90 × 5.8 s = 旧 node 全体 522 s の全量は削減不能)。
- must-fix 基準 (DW-G05): 受理集合に加え、A/B 対表・判定・insight・裁定内容を変える欠陥も must-fix。

## 4. test 計画 v2 (unit-impl author、`orchestrator/tests/test_s8b_holdout_admission.py`、既存期待値は不変)

恒久 test (repo に入れる):
1. 複数 cell (≥ 2 claim)・各 cell ≥ 2 planned attempt の消費列で、各段階の marker 不在 / M+A− / M+A+ が固定の期待文書・固定 message どおりになる正例 (target 以外の claim と同 claim の既存 marker が同時に存在する状態を含む)。
2. 2 件目以降 (名前順でも後段) の非 target marker の負例: `claim-mismatch` (campaign_run_id 改竄)、`extra-key`、`noncanonical-filename` (改名、複製でない)、`attempt-not-covered` (未登録だが文字列として妥当な attempt_id、file 名もそれに合わせる) → 各 message 全文の固定 literal。
3. 2 件目以降の A 行の負例: `campaign_run_id` 改竄 (期待 message は H:5287 の完全再導出の `…marker differs from claim and ledger`)、marker 不在 (`…no consume marker`)、canonical A 行の二重化 (`…duplicate identity`)。
4. 例外順序: 未登録 attempt + main 不正の併置で coverage が先 (v1: coverage → entry/seams、generation: entry/seams → coverage)。target の claim/coverage 失敗時は main 読取 0 回。
5. main 検査の射程: v1 は別 claim の floor 行 shape 不正も拒否、generation は無関係行の意味的 shape 不正を新たに拒否しない、非 canonical ledger bytes は双方で拒否。legacy (v1、claim v1/v2) fixture は「legacy 読取互換性の unit fixture」と docstring に明記。
6. memo の寿命・回数: 実物へ委譲する観測 wrapper (monkeypatch で `_read_ledger` / `_read_canonical_document` を包む) で、候補 1 呼び出しにつき claim 読取 = claim ごと 1 回、main ledger 生読取 = 呼び出し全体で 1 回 (target の claim 失敗時は 0 回)、marker 読取 = 全件。2 回目の呼び出しでは再読され、呼び出し間に改竄した claim / main が拒否される。
7. 被覆台帳 (author の報告に表で): I1〜I5 の各検査項目 × {新規 test / 既存 test (T:2581/2633/2668/2685/2699/2714/2729/2750/2676) / 静的到達不能 (理由)}。unsafe entry・directory 不在 (H:5258/5262)、reader の各 message (H:1351/1353/1355/1358、`_strict_json`)、filter 順序 (対象外 schema の正常文書は無視・不正 bytes は拒否、A ledger も同様)、main ledger reader の各例外 (byte 上限・末尾 LF・空行・JSON・非 regular・読取不能) と claim エラーとの優先順位、`__all__` / 公開 signature の差分確認を含める。

wave 時 probe (unit-probe author、`probe-t2802/`、repo に入れない): 差分 probe `t2802_diff_probe.py` — base module (`verbatim/base-module/s8b_holdout_admission_base.py`、sha256 `de03d253…`) を `orchestrator.campaign._t2802_base_admission` の別名で `spec_from_file_location` により load (exec 前に `sys.modules` へ登録、現行 module は置換しない、repo root を import 可能に)、同一 root 状態の系列 (正例列 + 改竄の系統的列挙) に対し新旧候補関数の (戻り値 / 例外型の module 対応 / message 全文) の一致を検算する。例外型は module ごとの対応表で比較。親が段 6 で計算ノード (または login、admission-only で軽い) で 1 回実走し、DW-O19 の一時変異 (M1 形) で probe が差を検出することの正例も 1 回取る。

## 5. 変異 matrix の事前登録 (DW-M01、実装後に単一理由性を確認して spec 化)

経路: 独立 clone (D1009、T-2766 の `make-mutation-source.sh` + `init-mutation-source-submodules.sh` の型、main = 実装 tip)、`tools/mutation_worktree.py --runner-mode dispatch --detached`、runner argv = `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_s8b_holdout_admission.py -q -rf` (消費 test の parametrize 完全集合を静的に確定できなければ probe 走 (全件 SURVIVED 期待、node 空) → final 走の 2 段、DW-M08)。等価変異 1 件は `positive` で SURVIVED 期待。

| ID | 変異 (production の位置、実装後に anchor 確定) | category | 期待 | KILL する test (旧 / 新) | 狙った最初の拒否位置 |
|---|---|---|---|---|---|
| M1 | memo hit 時に marker の `campaign_run_id` で期待文書を上書き | negative | KILLED | 新: 2 件目 marker `[claim-mismatch]` (非 target・A 不在)。旧: T:2729 も message 不一致で落ちうる (台帳に「旧でも赤」を記す) | marker ≠ expected (MUT-A2) |
| M3 | memo hit 時の `attempt_id in attempt_ids` 検査を省く | negative | KILLED | 新: `[attempt-not-covered]` | coverage |
| M4 | canonical filename 比較 (H:5271) を省く | negative | KILLED | 新: `[noncanonical-filename]` (改名) | filename |
| M5 | A identity 重複検査 (H:5291) を省く | negative | KILLED | 新: A 行二重化 | A duplicate identity |
| M6g | generation 経路の `main != expected_main` (H:4917) を省く | negative | KILLED | 新: `records` だけ claim と異なる main 行 (shape・identity・manifest・marker は正常) | main ≠ expected_main |
| M6v | v1 経路の `main != expected_main` (H:4780) を省く | negative | KILLED | 新: legacy fixture の同型 | 同上 (v1) |
| M7 | completed 拒否 (H:5308) を省く | negative | KILLED | 旧: T:2750 (新規検出力に数えない) | MUT-A6 |
| M8 | memo を module 変数に昇格 (呼び出しを跨いで保持) | negative | KILLED | 新: memo 寿命 test (2 回目の呼び出しで改竄 claim/main が拒否される) | I4 |
| P0 | A 行 identity の `str(...)` を外す (H:5289) | positive | SURVIVED | — | 等価 |

不採用: plan M2 (複合変異)。到達不能 (変異にしない): A≠marker (H:5296)、target≠canonical_target (H:5304)、marker identity 重複 (H:5276)。各 KILL は 3 欄 (KILLED / 最初の拒否位置が狙いどおり / 新規検出力) で台帳化する。

## 6. A/B 対比較の事前登録 (凍結、結果を見て変えない)

- **条件:** A = `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-base-a` (HEAD `b7f970dfa507558f7fb669a5ab38958d6c76b57c`、clean)。B = wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2802-floor-attempt-recovery` (HEAD = **実装 commit だけ**を含む measurement tip、完全 SHA を系列開始前に `runs/measurement-tips.json` へ固定、clean)。B の SHA が変われば旧系列は破棄し新系列 (合算しない)。各条件内では全反復同一 SHA。両 tree の tracked 差分 (`git diff --stat b7f970dfa <B>`) を保存。
- **投入形:** 各 worktree から `IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` を直接投入 (待ち手・lease・merge・receipt なし)。`PYTHONDONTWRITEBYTECODE` は unset。門番 = T-2766 と同じ (他 session の受入待ち手 ≤ 1 かつ load1 < 30 を 100〜140 秒周期で 2 回連続 + 0〜45 秒乱数 → 再判定)。job dir の flock で直列化。投入直前と終了後に HEAD == 条件別 SHA と clean (`--untracked-files=all --ignore-submodules=none` = 0 行、`output/pegasus-dispatch/` は除外) を照合。
- **warm-up:** 系列開始前に両 tree で同じ計算ノード collect-only を 1 走ずつ (`PYTHONDONTWRITEBYTECODE=` を allowlist 経由で渡す T-2766 `run-warm2.sh` 型)、pyc 件数を記録。page cache・fixture の warm は主張しない。
- **順序:** slot 1 = A,B / slot 2 = B,A / slot 3 = A,B。有効 3 対で固定終了。全投入 12 走上限 (超えたら効果未確立)。
- **無効条件 (走):** 子 rc ≠ 0、3 shard のいずれかに failed/error > 0、成果物 (3 shard の junit.xml / report.json) の欠落・sha 不一致、floor nodeid 集合が `S_all` と不一致 (各 node ちょうど 1 件・有限非負 time)、HEAD/clean の投入前後不一致、投入時刻の単調性違反。**無効走を含む対は無効。**
- **赤の扱い:** 原因未分類の赤 → 系列停止 (親が本文で分類、5 分超は悩まない DW-O18)。B 実装起因 → 測定終了 (修正 → 新系列)。インフラ起因 (dispatch-infrastructure、memo publication timeout 等、本文で確認) → その対全体を同順序で取り直す。片走は次の対へ流用しない。
- **一次指標:** `F` = 3 shard の junit `testcase` のうち `S_all` (凍結 523 nodeid、`floor-subset-frozen.json` sha256 `2bc360b9b1e524506cfa152ec53f2b720df726a6b1a6e9b2f245314e1df4e5d4`) の `time` 合計 (各 node 1 回、top-level junit は合算しない、B の追加 admission test は所属 file で除外)。対差 `ΔF = F_A − F_B`。**判定:** (i) 有効 3 対とも `ΔF > 0` かつ対差の中央値 ≥ 200 s → 「方向一致・実用閾値以上」、(ii) 3 対とも `ΔF > 0` だが中央値 < 200 s → 「方向一致・閾値未満」、(iii) それ以外 → 「効果未確立」。200 s は実用上求める削減量で、ノイズ (T-2766 同一 code の floor 対差 22 / −211 / 60 s) から導いた閾値でも有意差判定でもない。
- **補助指標:** `ΔF_mid` = `S_mid` (中央値 4〜12 s の 65 node、同 json、`sum_mid_median` 400.6 s) の合計対差、nodeid 単位の対差の分布 (中央値、`Δ ≥ 3 s` の node 数とその合計)、`W_max = max(W_0, W_1, W_2)` と `W_0`、最忙 worker の占有 (記述的)。補助指標は一次の代替にしない。
- **主張範囲:** 二つの固定 tree の差の測定であり、memo 単独の因果効果・D2068 の同一 tree 条件の充足・有意差は主張しない。48w A/B と 12w profile (旧 5.8 s/node) は別列で示し比率換算しない。

## 7. 実装の分割 (段 5、並列 2 本)

- **unit-impl** (`/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-impl`、所有: `orchestrator/campaign/s8b_holdout_admission.py`、`orchestrator/tests/test_s8b_holdout_admission.py`): plan v2 + test 計画 v2。
- **unit-probe** (`/work/1/SFC/tanab/izanagi/.codex/worktrees/t2802-unit-probe`、所有: `probe-t2802/run-measure.sh`、`probe-t2802/run-series.sh`、`probe-t2802/t2802_ab_analyze.py`、`probe-t2802/t2802_diff_probe.py`): §6 の launcher (T-2766 `run-measure.sh` の改変: 条件別 worktree/SHA、pairing env 削除、run.json に条件別 SHA・path・tracked diff の sha)、系列 script、集計器 (§6 の指標・無効条件・判定を実装、`--selftest` 付き)、差分 probe (§4)。親が実行後 job dir へ退避、repo へ入れない。
- 統合: 親が unit-impl の所有 path 限定 patch を wave worktree へ `git apply` → 実装 commit (AI-Agent trailer、Codex author) = measurement tip 候補。段 6 レビュー 2 本 (過剰・削除レンズ固定 1 本 + 正しさ境界 1 本) → fix (同 unit worktree、branch 切替) → 焦点走 (計算ノード: 変更 test file 単独 + consumer `test_s8b_floor_campaign.py`、`test_s8b_oracle_n_pilot.py`、`test_s8b_oracle_driver.py` 等は参照関係で列挙) → 変異 (§5) → A/B (§6) → 段 7。

## erratum 1 (2026-09-20 07:55 JST、測定前、§6 無効条件の訂正)

probe author の報告 (`codex/s5-author-probe.md`) で、凍結 `S_all` 523 node のうち 3 件 (`test_real_floor_prepare_material_oracle_and_capability_series_when_configured`、`test_slow_real_prepare_cell_to_buildcache_canary_one_configuration`、`test_slow_real_prepare_cell_to_buildcache_v2_canary_one_configuration`、実環境が未設定のとき skip する real/slow 系) が T-2766 の 6 走すべてで skipped と判明した。§6 の「各 node … skipped/failed/error でない」を次に訂正する (結果を見る前の訂正、判定式・閾値は不変):

- 走の無効条件: `S_all` の各 node がちょうど 1 件、`time` 有限非負、failed/error が 0。**skipped は許す**が、走ごとに skipped の nodeid 集合を記録する。
- 対の無効条件に追加: 対内 2 走の skipped nodeid 集合が一致しない対は無効 (状態が同一でない node の対差は定義しない)。
- 集計器 `t2802_ab_analyze.py` の本走 parser (`parse_junit` の `allow_historical_skips=False` 経路) をこの規則に合わせて fix する (Codex fix、unit-probe)。selftest は T-2766 の 6 走で「skipped 3 件・両走一致」を通し、skipped 集合が対内で異なる合成例を無効対にする負例を足す。

## erratum 2 (2026-09-20 08:36 JST、変異 probe 走は 08:26 に起動済み・結果は未読、§5 の probe 先行の理由)

DW-M08 の「期待 node は完全集合。確定できない場合に限り初回を probe」に対し、本 wave が probe 走を先行させる理由を記す (焦点再レビューの指摘)。

- 対象 test file は fix 後 110 case を含む 293 node。各変異で赤になる node の**完全集合**を静的に確定できない理由: (a) M1 / M7 は新規負例だけでなく既存 test (`test_cut6_recovery_requires_exact_marker_rederived_from_claim[claim-mismatch]`、`test_cut6_completed_session_forbids_reissue_of_same_attempt` 等) も別 message や別経路で赤になりうる (レビュー B §変異、author 報告) が、その全列挙は memo hit の発生する呼び出し列に依存する。(b) M8 (root key の呼び出し跨ぎ保持) は「同一 root で候補関数を 2 回以上呼ぶ既存 test」すべてに影響しうる (consume → 再 consume、`floor_attempt_requires_cut6_replay` → consume 等) が、その集合は fixture の呼び出し列を全 test について追わないと確定しない。(c) M3 / M4 / M5 / M6g / M6v は新規負例 1〜2 node への帰属を想定するが、同 fixture を使う正例側 (110 case) への波及は静的には否定しきれない。
- よって初回は全件 SURVIVED 期待 (node 空) の probe で観測集合を採り、その完全集合を final spec の KILLED 期待に登録する (T-2766、T-2710 と同じ型)。probe の結果は final 走の期待に使うだけで kill には数えない。
- P0 は両走とも SURVIVED 期待。

## erratum 3 (2026-09-20 11:08 JST、A/B 系列の 02-B を無効走とし対 1 を取り直す。launcher の投入直前再判定を追加)

- 事実: 01-A (09:46〜10:12、rc=0、赤 0) は有効。02-B (10:35〜11:01、rc=0、赤 0、成果物複製 OK) は集計器の走無効条件 `gate metadata`
  (投入時に記録した他 leader 2 > 門番上限 1) に該当し無効。門番自体は 2 回連続 + 再判定で leaders ≤ 1 だったが、再判定から投入
  (HEAD/clean の `git status`、diff、RUN dir 作成) までの数秒〜十数秒に別 wave の受入待ち手が増えた。B の F / W は無効走のため未計算・未読。
- 分類: `runs/02-B/classification.json` = `infra` (他 wave の受入の同時性、B 実装に非帰属)。§6 の規則どおり対 1 (A,B) を同順序で取り直す:
  03-A / 04-B (slot 1) → 05-B / 06-A (slot 2) → 07-A / 08-B (slot 3)。総投入 8 走 (上限 12 内)。
- launcher の是正 (fix-probe4、Codex): RUN dir 作成の直前に門番をもう一度判定し、閉じていれば走番号を消費せず門番 loop へ戻す。判定式・
  指標・無効条件は不変 (集計器の `gate metadata` 検査は維持)。
- 系列 script の再開は、赤走なし・02-B の分類ありの状態で `run-series.sh "03 A 1" "04 B 1" "05 B 2" "06 A 2" "07 A 3" "08 B 3"`。

## erratum 4 (2026-09-20 11:40 JST、03-A を infra で無効とし対 1 を 04-A から再開)

- 事実: 03-A (11:25 投入) は child rc=16 (`acceptance shard gate failed: dispatch-infrastructure`)。shard-2 の計算ノード側で pytest-xdist の
  INTERNALERROR (`KeyError: <WorkerController gw30>`、loadscope.mark_test_complete) と timing 依存の 1 node (`test_pegasus_floor_tools.py::
  test_floor_checkpoint_filesystem_hang_has_a_wall_clock_bound[write]`) が出て child rc=16 → 受入 gate → 親が shard-0/1 の dispatcher を
  SIGTERM。A (未変更 base) の走なので B 実装に非帰属。`runs/03-A/classification.json` = infra。
- 残存: request 12235 / 12236 は scheduler に残り、base-a worktree に orphan hold 2 件。runbook §7.6 の順で、qstat で終端を確認 →
  base-a の HEAD/clean を確認 → hold file を手で削除 (qdel はしない)。
- 再開列 (集計器の文法「赤で止まった前半 1 走の後、同 slot の A から対全体をやり直す」に従う): 04 A 1 / 05 B 1 / 06 B 2 / 07 A 2 / 08 A 3 / 09 B 3。
  総投入 9 走 (上限 12 内)。判定式・指標・無効条件は不変。

## erratum 5 (2026-09-20 11:53 JST、04-A は root の orphan-hold latch 残存で未投入 → infra、05-A から再開)

- 事実: 04-A (11:49) は全 shard の dispatcher が `orphan-hold` で scheduler command を打たず child rc=16 (test は 1 つも走っていない)。
  原因は親の hold 解除漏れ: `orphan-holds/<request>.json` 2 件だけを消し、権威の latch `output/pegasus-dispatch/orphan-hold.json`
  (request 12235) を残していた (runbook §7.6 の「hold file」は root の latch を指す)。qstat で 12235/12236 不在・base-a HEAD/clean を確認済みの
  状態で root latch を削除 (写し `runs/03-A/orphan-hold-root.json`)。`runs/04-A/classification.json` = infra。
- 再開列: 05 A 1 / 06 B 1 / 07 B 2 / 08 A 2 / 09 A 3 / 10 B 3。総投入 10 走 (上限 12 内)。判定式・指標・無効条件は不変。
