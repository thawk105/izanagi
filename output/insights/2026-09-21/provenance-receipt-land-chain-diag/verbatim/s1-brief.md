# 段 1 brief — T-2803 着地後の実 land 連鎖での全史 provenance 監査 warm / cold の実測 (診断のみ)

- 起点 local main `5efd69367b641b9bfbd6fb426478f66ae5762783` (fresh worktree、開始 gate rc 0 @ 07:35 JST、login pegasus02 load 6.8)
- 依頼逐語: job dir `verbatim/origin.md`。起点 entry 1769 (T-2803、`docs/archive/worklog-phase3-0921-1769.md`)、一次資料 `output/insights/2026-09-20/t2803-receipt-attributes-fingerprint/README.md` §8〜§11、D2045 / D2192。

## 研究前進
論文の主張・図表・実験には直接影響しない。**土台**: 全 wave の land が provenance 監査 (D254 の 480 秒予算、超過は rc=29 で main が進まない、F365 / D2045 の起点) で止まらないことの実測確認。最小差分の期待値 = **0 行** (T-2803 の warm 連鎖が実 land で成立しているなら追加実装不要、と裁定パッケージで示す)。完了判定 = 着地後の全 land / 受入監査について warm / cold と cold の原因が 1 件ずつ分類され、残る cold の主因に対する局所修正候補の効果見積り (または「候補なし」) が insight に書かれ、段 6 review 1 本が GO。

## scope
- 診断のみ。実装 0 行。gate・台帳・一般化の追加、監査の判定・受領証 schema・D2045 / D2192 の束縛の変更は scope 外 (依頼逐語)。規律 2 を緩めない。
- 成果物: `output/insights/2026-09-21/provenance-receipt-land-chain-diag/README.md` (時系列・分類表・実測・限界・裁定パッケージ・再現資料) + worklog fragment (`docs/spool/`)。decisions は裁定パッケージなので記録しない (採否はユーザー)。
- probe (受領証分類・land / 受入ログ突合・追加実測 launcher) は **Codex author が書き** (実行可能 script は所在不問で実装面、F75 / 記憶)、親が実行し job dir (repo 外) に置く。repo へ入れない。

## 確定済みユーザー裁定 (依頼逐語)
1. 実測対象 = T-2803 着地後に land した wave の受領証 (共有 store) と land-*.log。着手直前の local main から fresh worktree。
2. cold 件ごとに原因を 4 種で分類: checker sha 変更 / `.gitattributes` / attributes 以外の binding 失効 / partition 跨ぎ。
3. 局所修正候補 (§11 の候補列挙 memo 化・attr.tree 束縛・errno 正規化) は **その主因に当たる場合だけ**、効果見積り付きで裁定パッケージ。
4. 診断だけ。

## 親の前提実測 (仮説。確定値は Codex author の probe で再導出する)
script (親作、job tmp、read-only): `receipt_inventory.py` / `receipt_chain_classify.py` / `land_accept_wall.py`。生出力 `receipts-classified.txt` / `land-accept-wall.txt`。
- 共有 store `<common git-dir>/provenance-audit-receipts/`: 495 件 / 19 partition (07:4x)。現行 checker sha256 `e69764c1d885…` は 65966f4d8 (2026-09-20 23:41、T-2803 + T-2804 の merge) 以降不変。
- 現行 checker の partition は 2 つだけ: `c508d1de93e1` (34 件、継承 env に `GIT_EDITOR=true`、`git config --list` に ~/.gitconfig の lfs filter 4 行) = **受入 (`dev_wave_wait.py` の claim 前 / merge 後監査) + 対話 session の直打ち**、`4608b761416c` (11 件、`GIT_CONFIG_GLOBAL=/dev/null` … `LC_ALL=C`) = **land (`dev_wave_land.py` の `_git_env()` override)**。受入は checker 起動に `_GIT_ENV_OVERRIDES` を適用せず親 env を継承する (`_run_subprocess` の `git_discovery_stage`、行 651〜659)。
- 分類 (同 partition に mtime が前・tip が祖先・bindings 完全一致の受領証があれば warm 推定、無ければ cold + 原因): 09-20 21:00 以降 81 件 = 旧 checker `7c02fb2d` の attributes 差 cold 26 (起点どおり) / checker 変更 6 / partition 跨ぎ 2 / warm 推定 47。**現行 checker 45 件 = cold 2 (各 partition の初回: 受入側 65966f4d8 = checker 変更、land 側 c383bac07 = partition 跨ぎ) + warm 推定 43。attributes / registry / cab_hits / policy / epoch 差の cold = 0。**
- wall 上限 (log の開始時刻 → 受領証 mtime、混雑 load1 は受入 chain.log の gate 行): 受入 claim 前 warm 17 / 17 / 19 / 21 / 23 / 18 秒 (load1 1.4〜4.7)、merge 後 warm 17 / 18 秒、受入 cold 初回 36 秒 (load1 3.5)。land warm 27 / 40 / 51 秒 (前処理 = preflight・turn・lock 待ち込み)、land cold 初回 81 秒。land_total 190〜335 秒のうち監査は小さい。
- 旧 checker 期の cold (参考、混雑 load1 7〜26): 42〜126 秒 (T-2656 batch 化後)。
- **「混雑時・計算ノード」の本番経路** (`tools/check_ai_provenance.py` main、行 3610〜3730): login では `orchestrator/campaign/login_headroom.py` の admission (memory cgroup の余力。load ではない) を評価し、余力があれば bounded local (cgroup 制限の子) で走り、`headroom_short` で queue が使えれば `tools/pegasus/dispatch_compute.py --task provenance` (env_mode=inherit) で **計算ノードへ自動 dispatch** する。`--force-dispatch` で強制できる。dispatch されると継承 env が変わるので**別 partition** に落ちる (= 混雑時の cold の経路)。継承 env が `LC_CTYPE=C.UTF-8` だけの partition 3 つ (旧 checker `5cb709cb` 64 件 / `7c02fb2d` 11 件 / `65476daf` 1 件) がその受領証と推定 (未確定、実測で確定する)。**現行 checker `e69764c1` では計算ノード partition が無い** = 09-20 23:41 以降の受入 / land 監査は 1 件も dispatch されていない (深夜、load1 1.4〜4.7)。混雑時 (headroom_short) の現行 checker の観測は無い。

## 割れうる前提 (親の provisional 裁定、攻撃対象)
- (P1) 「warm 推定」の妥当性: bindings 一致 + 祖先 + 発行順で再利用を推定した。`_receipt_prefix` の他条件 (selection digest / delta 一致 / correction candidate 0 / registry coverage) と lookup 時の並走 (受領証がまだ無い) を見ていない。裁定: Codex probe で `_receipt_prefix` を当時の受領証 pair に対して offline replay (bindings は受領証側の値を渡す) し、warm 推定 43 件の残り条件を機械判定する。wall (warm 17〜23 秒 vs cold 36〜126 秒) を第 2 の裏取りにする。
- (P2) 「開始 → 受領証 mtime」は監査 wall の**上限** (受入は attempt 開始直後に監査、land は preflight / lock 待ちを含む)。監査単独の wall は追加実測 (P4) で取る。
- (P3) 残る cold の主因 = 「checker 変更後の各 partition の初回」だけであり、§11 の 3 候補 (memo 化 = warm の候補列挙 2 回 → 1 回で 1.7〜3.5 秒、attr.tree = 該当経路なし、errno = 該当 0 件) はどれも主因に当たらない → 裁定パッケージは「局所修正なし (現状維持)」を第 1 案とし、参考として「受入 / land の checker 起動 env の統一 (partition 統一)」の効果見積り (checker 変更 1 回あたり land 1 本の cold 分 ≈ 30〜55 秒、D2045 の区画分離の改訂が要る) を添える。
- (P4) 追加実測 (本番経路そのもの、通常運用と同じ副作用 = 受領証が数件増える): (a) login 同時刻対照 — 本 worktree (HEAD = main、直近受領証 cf1c90e1f の子孫 Δ=1) で受入相当 env (親 env 継承) の warm 1 走、land 相当 env (`dev_wave_land._git_env()` 同値) の warm 1 走、新 `GIT_*` 変数 1 つで別 partition にした cold 1 走を直列で `/usr/bin/time -v`。(b) 計算ノード = **`python3 tools/check_ai_provenance.py --force-dispatch` を 2 回直列** (1 回目 = 計算ノード partition の初回 cold、2 回目 = warm。計算ノードでの継承 env / partition の実体・queue 待ち・cold wall が 480 秒に収まるかを確定)。「混雑時」の実測 = (b) と同じ経路 (headroom_short → dispatch) なので (b) で代表させ、login 混雑そのものは作らない。D1996 の「7 倍振れ」による login cold の試算は保証なしで併記。
- (P5) 親作 3 script の値は仮説。確定値と insight の数表は Codex author の probe の生 stdout (tee、逐語 file) から写す。

## 変更面 (実アンカー表)
| 種別 | path | 変更 |
|---|---|---|
| docs (新規) | `output/insights/2026-09-21/provenance-receipt-land-chain-diag/README.md` + `verbatim/` + `measurements/` | 親 |
| docs (新規) | `docs/spool/<worklog fragment>` | 親 |
| probe (repo 外) | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-provenance-cold-diag/probe/*.py`, launcher `*.sh` | Codex author 作、親実行 |
| 実装面 (repo 内) | なし | — |

## 条件表 (段 1 時点)
O08 / O09 / O10 非成立 (freeze・凍結 bytes・producer に触れない)。O13 非成立 (gate・検証を新設しない、依頼が scope 外と明示)。O11 非成立。O20 済 (external handoff、gate rc 0)。

## 段構成 (軽量版 + T-2243 型)
段 2 省略 (親 plan = 本 brief の P4)。段 3 相談 1 本 (codex read-only、brief と P1〜P5 を攻撃)。段 4 裁定。段 5 author 1 本 (probe)。親実走 (login 3 走 + 計算ノード 1 job)。段 6 review 1 本 (read-only、insight の数値・不在断定・限定文を生 stdout と照合) + 焦点再レビュー ≤ 3 巡。段 7 記録。段 8。段 9 受入 → land。

## 受入・実測環境
login pegasus02 (所在 = worklog)、計算ノード 1 job (機体固有 = `docs/pegasus-runbook.md`)。受入は `tools/dev_wave_wait.py acceptance` (docs-only でも land が receipt を要求、先例 T-2817)。
