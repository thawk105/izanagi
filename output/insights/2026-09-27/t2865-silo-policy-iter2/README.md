# silo-function-policy 軸の 2 iteration 目以降 — 骨格の乱数 seed をスレッドごとに直し、新系列 B で critic 診断を挟んで回したが、Pegasus 契約の one-shot claim で 2 本目の pair job が通らず評価済み 1 iteration で止めた (2026-09-27、[T-2865])

- 位置づけ: 段階 F (D2270、記録 `output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md`) の続き。手順は `docs/phase3-silo-policy-runbook.md`。本 wave の設計判断は同じ wave の decisions fragment。可変状態の正本 (worklog 末尾) にはしない。
- wave: branch `worktree-dev-wave-t2865-iter2`、起点 local main `339d7c188` (開始 gate rc=0)。submodule pin `6810666` (方策軸の pin、不変)。
- 逐語 (`verbatim/`): 依頼 `request.md`、段 1 brief、段 2 plan、段 3 相談 A・B、段 4 裁定、段 5 実装子の報告、段 6 のレビュー A・B・裁定・fix-1 の報告、claim の扱いの相談 2 本 (決定側 `claim-consult-decide.md`・攻撃側 `claim-consult-attack.md`)、系列 B の LLM 入出力 (`verbatim/llm/`)。変異の spec と結果は `mutation/`。codex の prompt と受領証は wave の job dir (repo 外)。
- **firewall の記録:** coder に渡したのは driver の `--emit-coder-input` の出力 (iteration 3 は `--critic-output` 付き) そのもので、親は key を足さず値も書き換えていない (固定 field が iteration 1・2・3 で bytes 一致することを `cmp` で確かめた)。critic に渡したのは同じ系列の digest 本文・当該候補の実装 (justification を除く)・同じ job の stock の値だけ (`verbatim/llm/critic-prompt-2.md`)。偵察・小比較・再測の点 ID・因子・比・順位は coder・critic・auditor のどの入力にも入っていない。critic の出力に含まれる数値は自系列の値と role 文書由来の noise floor だけ。codex 子の prompt でも段階 D の §2.1 以降・偵察 file・小比較と再測の insight を読むなと指示した。

## 0. 要約

1. **骨格の乱数 seed を直した (段 3 の裁定):** 骨格 patch `patches/silo-function-policy-variant.patch` の方策用乱数は全スレッドで同じ初期値だった。`TxExecutor::begin()` の既存の `SILO_POLICY_VARIANT` 分岐で、初回だけ worker の `thid_` から splitmix64 で混合した値 (`| 1` で非 0) を seed する (10 行、Codex author)。hole・API・hook 呼出し点・上限・patch の touch set・stock 側の行は不変。stock の variant ID は修正前後とも `db4764543546` で、stock build の同一性が保たれたことを直接確かめた。焦点 test 1 本と変異 M1〜M3 (3 / 3 KILLED)。
2. **旧系列 A は予算で閉じていた:** 段階 F の loop campaign は 16:32 JST 開始で、walltime 予算 3,600 秒を超えていた。driver は iteration を進める前に `stopped-before / budget-walltime` を返すので、2 iteration 目は新系列で回すしかなかった。
3. **新系列 B (修正後の骨格、新 submit checkout):** iteration 1 は preview で拒否 (接尾辞なしの shift 量 `>> 1`、`lex.literal-suffix`)。iteration 2 は coder が履歴の拒否理由から自分で直し、auditor pass、計算ノードで certified。同じ job の stock 比 3.19 (1 回の観測、主張ではない)。critic は「待ちが短いことが効いた」を第一仮説とし、変更を 1 か所に絞る切り分けを推奨した。iteration 3 の coder はその推奨どおり abort 後の待ちだけを 0 にした候補を出し、auditor pass。
4. **iteration 3 の pair job は build 前に `ClaimError` で止まった:** Pegasus 契約では campaign claim が identity ごとに一度きり (one-shot) で、release も stale 判定も無い (D464・D553)。同じ job の中の候補→stock は D2205 で 1 process の認可 session に束ねて解決済みだが、**job をまたぐ同じ loop campaign の 2 本目**は同じ path の `O_EXCL` で必ず拒否される。段階 F は pair を 1 本しか実走しておらず、この制約は表に出ていなかった。
5. **claim を手で退避して再投入する案は採らなかった:** codex の 2 レンズ (決定側・攻撃側) に相談した。決定側は「止める」、攻撃側も「明文の禁止とまでは言えないが、2 本目以降の常用手順にすると one-shot の拒否を運用で繰り返し解除し、未修復の driver 設計を置き換える」として止める側を推した。系列 B は評価済み 1 iteration (iteration 2) と、critic 診断を受けた未評価の iteration 3 proposal で確定する。
6. **次の一手:** 方策 loop を Pegasus で複数 iteration 回すには、job をまたぐ同じ campaign の claim の扱いを driver 設計で解く必要がある (one-shot の防壁は変えない)。新しい持ち越し項に起票した。

## 1. 依頼と裁定

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `verbatim/request.md`): 2 iteration 目以降 (critic の spawn と `--critic-output`)。先に §3.4 の骨格乱数の所見を段 3 で直すか決め、直すなら変更前後を別条件として 1 iteration 目と混ぜない (骨格は Codex author、stock build の同一性は崩さない)。Elapse 単価で見積もり、検査込み 2 node 時間以上ならユーザー確認。firewall と auditor の閉じた出力形の明記を守る。[T-2870] の role 本文は触らない。
- 段 4 の主な裁定 (`verbatim/s4-ruling.md`、相談 A 7 件・B 6 件を採否):
  - 骨格の seed は直す (plan・相談 A・B が一致)。旧系列 A はどのみち予算で閉じており、2 iteration 目以降は新系列になるので、直す追加費用は小さい。
  - 修正の形は `begin()` の初回 seed (patch の 2 file に収まる。構築子で seed すると touch set が増える。thread_local の address や thread id の hash は実行ごとに非決定)。
  - 系列 B 専用の bootstrap stock を測る (runbook §1(0) の手順どおり。段階 F の値を再使用すると「条件が混ざる」という plan の理由は採らない — stock は骨格 patch を使わない)。
  - 条件の区別は campaign identity を変えず、submit checkout・HEAD・骨格 patch の SHA-256・campaign dir を記録して行う (identity は patch の bytes を含まない)。
  - critic には digest・当該候補の実装・同じ job の stock の値だけを親が抜き出して貼る。
- claim の扱いの裁定 (本 wave 中、§3.4): 止める。

## 2. 実装 (commit)

| commit | 内容 | 作者 |
|---|---|---|
| `361e094f7` | 骨格 patch の seed (10 行) と焦点 test `test_worker_seed_uses_thid_once_and_keeps_random_sequence` | Codex author |
| `0ff7645c4` | runbook §1(g) の critic 入力・出力形、§3 の骨格を変えたときの系列の分け方 | 親 (docs) |
| `61e38420a` | fix-1: 骨格の上に重ねる計器 patch `instr-silo-function-policy-probe.patch` の hunk 位置と文脈 1 行 (焦点走 1 回目で `test_silo_policy_coverage.py` の 3 件が `git apply` rc=1)。+/- 行の本文は不変、変異 patch 11 本は無変更で当たる | Codex fix |
| `3205dd93e` | runbook: critic 入力の抜き出し元、新 checkout の HEAD 確認 (段 6 レビュー B) | 親 (docs) |

焦点 test は、適用後 source の `begin()` 分岐が `seed_random(thid_)` を 1 回呼ぶ結線と、適用後 source から抜き出した実 seed 関数・`next_random()` を単独 TU で動かして「異なる thid → 初回値が異なる / 同じ thid → 一致 / 再 begin で系列が巻き戻らない」を確かめる。保証の範囲は現行 worker (1 thread に 1 executor) の寿命。

## 3. 系列 B の実走

submit checkout: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-iter2/trees/b` (HEAD `3205dd93e`、骨格 patch SHA-256 `9cb545520fe6d27a852ccb406f321924ee61d17ff86bf1b74eeafc54b9db2904`、locked)。loop campaign `p3-silo-policy-loop-silo-policy-autonomous-877344a7` (段階 F の旧系列と同じ ID で別 checkout の別 dir。ID 単独で結合しない)、bootstrap campaign `…-a84dd632`。trace 保全先 `/work/1/SFC/tanab/izanagi-repro-archive/t2865-iter2-20260927/`。全操作をこの checkout で直列に行った。

旧系列 A (比較のための記録): submit checkout `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-stage-f/trees/e2e` (HEAD `b815183af`)、骨格 patch SHA-256 `35524d7558fc596dac24557538d1bccd8c0112a9069023a48fec9eb9229b6249`、iteration 1 で予算停止。A と B の値は合算しない。

### 3.1 経過

| iteration | 段 | 結果 |
|---|---|---|
| (0) | bootstrap stock `31833.nqsv` (Elapse 309 秒) | `certified-stock`、variant `db4764543546` (段階 F と同じ ID)、5 rep 中央値 1,355,352 txn/s、abort 11.84% |
| 1 | coder (C++ 形、`verbatim/llm/coder-1.json`) → preview | `passed=false`、policy-grammar / `lex.literal-suffix` (`window >> 1` の接尾辞なし)。auditor は呼ばず `--record-reject` (loop_state がここで作られ、walltime 予算の起点 = 20:25:06 JST) |
| 2 | coder (self_history に拒否 1 行) → preview → auditor → pair `31855.nqsv` (Elapse 786 秒) | coder は「前回は `>> 1` の接尾辞なしで拒否された」と読み `>> 1u` に直した (方策は据え置き)。preview 通過 (digest `b0171a7d…`)、auditor pass (違反 0)。候補 `145e3d73315a` certified (serializable)、同じ job の stock `certified-stock` |
| (g) | critic (`verbatim/llm/critic-prompt-2.md` → `critic-output-2.md`) | 4 見出しで返却。driver が `critic_diagnosis` (6 field、`source_sha256` `af09edd0…`) に変換 |
| 3 | coder (`--critic-output` 付き) → preview → auditor → pair `31899.nqsv` (Elapse 36 秒) | coder は critic の推奨 A どおり abort 後の待ちだけを 0 にした (lock 方策は据え置き)。preview 通過 (digest `37a17d1d…`)、auditor pass (違反 0、liveness の nit)。**job は build 前に `ClaimError: campaign claim は既に 3235201 が所有している` で rc=1** (§3.4)。履歴に `eval-exception` の行 |

### 3.2 値 (5 rep、txn/s)

| attempt | job | 中央値 | 5 rep | abort 率 |
|---|---|---|---|---|
| stock (bootstrap campaign) | 31833 | 1,355,352 | 1,355,352・1,367,130・1,337,455・1,353,460・1,384,208 | 11.84% |
| 候補 iteration 2 (loop campaign) | 31855 | 4,351,478 | 4,455,545・4,429,819・4,290,171・4,351,478・4,302,727 | 18.68% |
| stock (loop campaign、同じ job) | 31855 | 1,366,231 | 1,417,285・1,364,633・1,366,231・1,330,855・1,371,362 | 12.63% |

- 同じ job の比 (候補 ÷ stock の 5 rep 中央値) = 4,351,478 ÷ 1,366,231 = 3.19。**1 回の観測・1 候補であり、性能主張ではない。** 段階 F (旧骨格、別の候補) の 2.80 とは骨格も候補も違う別条件なので並べて比べない。
- 候補の verify 中の abort 率は 23.33% (critic digest の verify 統計)。lock 方策が verify 中に発火した証拠は v1 に無い (runbook §4)。
- trace 保全: stock 340 MB、pair 1.1 GB (inventory complete)。iteration 3 は build 前に止まったので保全物は空。

### 3.3 critic の診断と iteration 3 の候補

critic は「abort が増えたのに throughput が 3.2 倍に上がった」ことから「abort 後や施錠競合時の待ちが短いことが効いた」を第一仮説とし、窓が低位に張り付いて待ちは実質 1 単位程度と推定した。推奨 A は「abort 後の待ちを常に 0 にし、lock 方策は据え置く」単一変数の切り分け、B は「lock 方策を即 abort に戻す」。欠測 (llc_miss_rate・ipc、lock hook の発火証拠、abort 要因別の内訳、待ちの単位) は uncertainty に書いた。iteration 3 の coder はこの推奨 A をそのまま候補にした (`verbatim/llm/coder-3.json`)。critic 診断が次の候補の形を決める経路は実際に働いた。その候補の評価は §3.4 のため得られていない。

### 3.4 job をまたぐ同じ loop campaign の claim (one-shot)

- 事実: Pegasus 契約 (reservation 必須) では `loop._authorize_measurement` が `campaign_claim.acquire_claim` を呼び、claim は campaign identity ごとに 1 file・`O_EXCL`・release も stale 判定も無い。D464 の生存判定は同じ protocol の**別 path** の競合だけを扱い、同じ path の既存 file は持ち主の生死を見ずに拒否する (D2187 が既に記録)。D2205 は同じ job の候補→stock を 1 process の認可 session で共有して解いたが、**次の job へ認可は持ち越さない**。したがって方策 loop の 2 本目の pair job (同じ loop campaign) は構造的に通らない。
- 実測: 残った claim は `trees/b/output/env/pegasus/claims/p3-silo-policy-loop-silo-policy-autonomous-877344a7.claim` (host `bnode009`、job `0:31855.nqsv`、pid 3235201、SHA-256 `382f48de9aae9b53083e479ff75e7e30f1b8620bca8bab23e076992073107308`)。31855 は qstat に無く、compute-result は driver_rc=0 (正常終了)。claim は動かしていない。
- 段階 F の記録 §7 の「runbook §1(g) の手順はそのまま使える」は、Pegasus では 1 campaign あたり pair 1 本までしか成り立たない (段階 F は pair を 1 本しか実走しておらず、2 本目を試していなかった)。段階 F の insight は書き換えず、ここに記録する。
- 判断: 手で claim を退避して再投入する案 (A) と止める案 (B) を codex の 2 レンズに相談した (`verbatim/claim-consult-decide.md`・`claim-consult-attack.md`)。決定側は B。攻撃側の最も強い反対理由は「(A) を 2 本目以降の常用手順にすると、D2187・D2205 が守った one-shot の拒否を運用で繰り返し解除し、未修復の driver 設計を事実上置き換える」。攻撃が成立しなかった項目 (規律 6 違反、退避だけで証拠改変と断定すること、D2187 の却下文の直接適用) も記録されている。B を採った。
- 修復は driver 設計の別 task (one-shot の claim leaf は変えない)。runbook §3 に「Pegasus では 1 loop campaign あたり pair job 1 本まで」を書いた。

## 4. 計算ノードの使用 (job Elapse)

| 用途 | request | Elapse |
|---|---|---|
| 焦点走 1・2 | 31814・31832 | 46・46 秒 |
| 変異 probe (3 本 + baseline) | (dispatch、使い捨て木) | harness 所要 573 秒 (待ち行列込みの上限) |
| 変異 final (3 本 + baseline) | (dispatch、使い捨て木) | harness 所要 171 秒 (同上) |
| bootstrap stock | 31833 | 309 秒 |
| pair iteration 2 | 31855 | 786 秒 |
| pair iteration 3 (ClaimError) | 31899 | 36 秒 |

受入を除く合計は 1,967 秒以下 (約 0.55 node 時間)。段 4 の見積り (検査込み ≤ 1.79 node 時間) の内側で、ユーザー確認の線 (2 node 時間) を下回るので確認なしで投入した。受入は §6。LLM: coder 3 回 (約 78・42・36 秒)、auditor 2 回 (約 103・96 秒)、critic 1 回 (約 99 秒)。

## 5. 変異 matrix (段 4 の事前登録)

runner `tools/run_tests.py --force-dispatch orchestrator/tests/test_silo_function_policy_template.py`。spec と結果は `mutation/`。

| id | 壊す箇所 (骨格 patch) | probe (main = `361e094f7`) の失敗 assert | final (main = `3205dd93e`) |
|---|---|---|---|
| M1 | seed 関数の `thid` を定数 0 | different thid | KILLED |
| M2 | 初回だけの印を外し毎回 seed | continued sequence | KILLED |
| M3 | `begin()` の seed 呼出しを削る | begin must seed (結線検査) | KILLED |

3 本とも新焦点 test 1 node だけを赤にし、失敗 assert が互いに別であることを probe で確かめた (単一理由)。fix-1 は patch の位置合わせだけで受理集合を変えないので変異を追加していない (焦点走 1 の赤 → 2 の緑が検出の実証)。

## 6. 受入

記録時点では未実施。

## 7. scope 外と次の一手

- 方策 loop を Pegasus で複数 iteration 回すための、job をまたぐ同じ loop campaign の claim の扱い (driver 設計、one-shot の claim leaf は不変)。これが解けるまで、Pegasus の方策系列は 1 campaign あたり評価 1 本。
- iteration 3 の proposal (`verbatim/llm/prop-3.json`、critic の推奨 A の切り分け候補) は未評価。R2 (別 campaign) で測ると同じ job の stock 対照が付かず loop も進まないので、本 wave では測っていない。
- [T-2870] (role・固定文面の改訂、ユーザー承認待ち) は触っていない。auditor の出力形は prompt の明記で 2 回とも 1 回目で gate を通った。

## 所在の移動・撤去 (2026-09-30 追記)

本 insight が投入元として名指す `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-iter2/trees/b` と `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-stage-f/trees/e2e` は、2026-09-30 の掃除 wave で回収せずに撤去する。値は本文に転記済み、`e2e` の campaign 原本の写しは `/work/1/SFC/tanab/izanagi-repro-archive/t2853-20260927/` (manifest `t2865-stage-f-originals`) にある。
判定の根拠・木ごとの退避の所在・残る写しの一覧は `output/insights/2026-09-30/cleanup-originals-migration/README.md` を正本とする。上の本文は当時の事実として書き換えない (記録された測定・判定は撤去を理由に無効にならない、規律 7)。撤去は同 wave の land の後に行う。
