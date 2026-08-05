# [T-327] 段 1 brief (v1) — 8c 事前登録の自動発効 + 条件文の凍結

**裁定正本**: archive worklog (115)。推奨 (a) 都度承認を蹴って **択 (b) 自動発効**。
「条件充足を機械が確認した時点で発効させ、都度の明示承認は求めない」(ユーザー理由 = 定型
コマンドを打つ手間の排除)。実装要件として**条件文自体の凍結** (条件文の変更は事前登録の
改訂扱い) を伴わせる。これは都度承認でなく一度きりの設計性質なので裁定理由と衝突しない。

## scope (T-327 の面 = 発効 authority の機構)

1. **発効判定器**: 任意の checkout に対し「`docs/phase3-8c-preregistration.md` は発効しているか」を
   fail-closed で導出する純関数 + CLI。入力 = §5 の記入欄・§6 の 12 条件・条件文凍結の一致。
2. **条件文の凍結**: §5 の欄名集合と §6 の 12 条件文の**正規化 hash** を tracked freeze artifact に
   pin し、改訂は前 hash を含む chain 付き ledger で記録する。pin 不一致かつ改訂記録なしは赤。
3. **文書改訂 (親が実施)**: §6 末尾「発効の判定は誰が行うか (未解決)」を裁定結果 (自動発効 +
   条件文凍結 + 改訂手続き) に置き換える。
4. **常時発火する invariant test**: 凍結一致・chain 妥当性・各述語の negative control。

## scope 外

- 前提条件 1〜12 の**中身**の実装 (3/8 = [T-325] 稼働中、7 = [T-088]/[T-296]、11 = [T-244]/[T-324]、
  9/10 = [T-318]〜[T-321] 系)。本 wave は「充足したかを判定する層」だけを持つ。
- §5 の数値実記入と実際の発効 ([T-295])。8b 設計とその §8 再凍結手続きの変更。
- **launcher / acceptance への gate 結線** — 同じ入口 (`p3_autonomous_workload_trial.py`) を
  [T-325] が改修中 (branch `worktree-dev-wave-t325-trial-registry`、2 commit、未 land)。衝突面。
- `layer3_report` 本体 ([T-326])、既存成果物の遡及判定。

## provisional 裁定 (攻撃対象)

- **(P1)** 発効は**導出値**であり宣言物ではない。commit C における 発効(C) =
  (凍結一致) ∧ (§5 全欄記入済み) ∧ (12 条件すべて green)。承認 commit / approval record を
  新設しない。8b §8 の approval record 方式は 8b 系列に留め、8c 発効へ流用しない (裁定の理由に反する)。
- **(P2)** 発効版 commit = 事前登録文書を最後に変更した commit (`git log -1 -- <path>`)。
  実走成果物への記録と祖先検査の**実装**は [T-325] の面。本 wave は定義と判定だけを持つ。
- **(P3)** 凍結は本文の複製でなく**正規化 hash の pin**とする。理由は **compact な canonical
  contract** であること (複製した本文が正本と二重化して将来ずれるのを防ぐ)。
  なお「本文複製が未既知性検査を汚染する」は一般には成立しない — 現文書は §0 の規約により三軸の
  canonical 綴りを持たないため、その bytes を複製しても conjunction hit にはならない
  (段 3 レンズ A-12 の指摘を採用して訂正)。汚染の有無は**実 artifact を repo scan にかける
  テスト**で実測する。
- **(P4)** 述語は fail-closed。機械証拠を定義できない条件は SATISFIED を返さず「証拠未定義」で
  未充足へ倒す。名前や CLI の存在だけで green にする恒真述語を作らない。
- **(P5)** 新規 module を `orchestrator/campaign/` に新設し、`p3_autonomous_workload_trial.py` と
  `trial_registry.py` を**編集しない** ([T-325] 稼働面との衝突回避)。読取・import は可。
- **(P6)** 本 wave の consumer は CLI + 常時走る invariant test までとし、launcher 結線は
  [T-325] land 後の後続タスクとして起票する。

## 不変条件

- `DW-O09` 実測 (query と分類を明示。段 3 レンズ B-10 の指摘を採用して追補):
  - **path 検索** `grep -rn "phase3-8c-preregistration" --include=*.py` → **hit 0**。
  - **bytes 検索** 文書の git blob ID (`7db6983`) と sha256 (`4efc92b1…`) を repo 全体
    (`.git` / `external` 除く) で検索 → **hit 0** = bytes を pin する台帳・test・trust root なし。
  - **key/role 側検索** `prereg` / `s8c` を key にする pin → hit は insights の変異台帳 field と
    review lens 名のみで、いずれも**この文書を pin していない** (分類: 歴史記録)。
  - **FROZEN_MANIFEST** 23 path に不在。`output/` に `s8c` namespace は未存在。
  - docs 側の言及 (`docs/README.md` / `decisions.md` / runbook) は**参照**であり pin ではない。
  → 本 wave の freeze が新規 durable manifest の発行にあたる。既存凍結 bytes は不変。
- `DW-O10`: 新設 producer (freeze 生成器) の書き出しは新規 artifact のみ。既存 producer の
  出力 bytes を変えない。
- 新設 tracked artifact に三軸 canonical 綴りを持ち込まない (§0 の自爆回避と同じ理由)。
- 自己 hash 自己参照を作らない (F36)。受理集合は狭まる方向にだけ動かす。

## 成果物影響 (DW-G05)

未実装なら「発効」が誰の権限でいつ成立したか不定のままであり、§1 が自認する穴 (数値欄が空の版を
祖先に持つだけで ancestry 条件を満たす) が開いたまま。certified 選択・材料レポートに
「事前登録された実験である」と書く根拠が無い。さらに条件文が凍結されないと、条件の書き換えで
判定基準を実質的に動かせる (ユーザーが (b) 採用時に残した留保)。実装後は発効が機械の導出値になり、
条件文の無記録変更が赤になる = 正式系列として受理される試行の集合が縮小する。

## 既存被覆と純増検出力

- 既存 (性質で検索): 8b 系列の ratified freeze + approval record (8b 専用、8c 発効は対象外)、
  trial 内側の journal↔report 完全性、(未 land) trial registry の manifest↔registry 照合。
- **純増**: ① 実走前提の充足を単一の機械判定へまとめる層 (現在ゼロ、文書が「未定」と自認)、
  ② 事前登録の条件文自体の改竄検出 (現在ゼロ — 文書は bytes を pin されていない)。

## 軽量判定・生死確認

- 受理集合が変わり proof chain の authority に触るため**軽量版にしない**。段 2・3 と段 6 敵対
  レビュー 2 本を実施する。
- `DW-G01`: 新探索軸でなく機構。生死確認 = §5/§6 の機械パース安定性で、親が実測済み
  (§5 = 9 行の markdown 表、§6 = 1〜12 の番号付きリスト + 太字宣言文)。専用 driver 不要。
- `DW-G04`: 発火条件を満たす既存 artifact path = `docs/phase3-8c-preregistration.md` (実在)。
  判定の consumer = 本 wave の CLI と常時走る invariant test。

## 実測済みの周辺事実 (段 2/3 で攻撃対象)

- `DW-O13` gate 入力の実在: §5 の 9 欄はすべて値 `未記入`、§6 は 1〜12 と
  「現時点で 1〜12 はいずれも未充足である」の宣言文を持つ。judge の入力はこの 2 節のみ。
- **docs の誤参照**: `D124` 決定 (5) は発効 authority を「[T-321] へ送る」と書くが、T-321 は
  `guard_bash` の話であり、実体は [T-327] (worklog (113) 起票 / (115) 裁定)。段 7 の erratum 候補。
- `MAX_APPROVED_GENERATIONS = 1` (`p3_autonomous_workload_trial.py:134`)、`WORKLOADS` は同 :162。

## 分割方針

単位 A = parse + freeze/chain core + 述語 framework + 専用 test。単位 B = 12 述語の実装と
negative control test。A→B 直列 (同一 worktree)。単位 C = 文書改訂は親 (docs)。
最終分割は段 2 プランに委ねる。

## 受入・実測環境

pytest 全走は `tools/run_tests.py` の自動 dispatch (Pegasus 計算ノード)。既知赤は `DW-O18` の
単独再走で本 wave 差分と切り分ける。
