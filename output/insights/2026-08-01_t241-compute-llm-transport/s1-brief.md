# 段 1 brief — [T-241] A/B/C live pilot: 計算ノードの LLM transport を通す

wave: `t241-compute-llm-transport` / branch `worktree-dev-wave-t241-abc-pilot` / 2026-08-01

## 前提の実測 (DW-S01) — T-241 の前提 2 件が覆った

計算ノード bnode002 で実測 (request `876527` / `876528` / `876529` / `876729`)。

1. **計算ノードから LLM に到達できる。** `docs/pegasus-runbook.md` §7.1 の「計算ノードは外部
   network 不可」は direct DNS / socket については真 (`getent hosts api.anthropic.com` rc=2、
   `/dev/tcp` 名前解決不能) だが、計算ノードの shell profile が `http_proxy` / `https_proxy`
   (`10.120.96.1:8080`) を設定しており、Claude CLI はこの proxy 経由で通る。算術 nonce 3 問
   (7311+2088 / 8123+4517 / 4011+2044) を rc=0・3 秒で正答した。
2. **`numactl` は計算ノードに在る** (`/bin/numactl`)。login (pegasus02) には無い。T-241 が
   「login に numactl が無く停止した」と書いた経路は、計算ノードでは numactl 起因では塞がらない。
   なお pegasus env_contract は `numactl=()` なので、そもそも要求もしない。
3. **真の blocker は driver 側の env allowlist だった。**
   `orchestrator/campaign/s8b_prediction_runner.py:70`
   `CLAUDE_ENV_ALLOWLIST = {PATH, HOME, LANG, LC_ALL, TERM}` が proxy 変数を落とす。同 allowlist は
   `claude_projected_provider.py:155` (= 8c が使う provider) が共有する。実測の対照:
   full env → 正答 rc=0 / allowlist そのもの → `API Error: Unable to connect to API (ENOTIMP)`
   rc=1 **172 秒** / allowlist + proxy 2 変数 → 正答 rc=0。
4. **campaign build は Pegasus では未踏。** `buildcache.DEFAULT_CC/CXX = gcc-13/g++-13` は
   login にも計算ノードにも無い (`g++-12` のみ)。CCBench は `find_package(gflags/glog REQUIRED)`
   だが計算ノードに両者は無い (pinned source は `~/github/{gflags,glog}` に在る)。
   ただし `tools/pegasus/certify_calibration.sh` は計算ノードで staged gflags/glog + 解決済み
   compiler により CCBench を build 済みで、**recipe は実証済み**。未対応なのは Python の
   `buildcache` 経路だけである。

→ T-241 の見出し (live build → legacy+S2 → bench) は本 wave では完了できない。3 が塞がるまで
LLM が 1 本も通らないので、まず 3 を塞ぐのが最安の生死確認である (DW-G01)。

## scope

**やる:**
- (S1) transport env (proxy) を role 呼び出しへ通す。allowlist を意図的に拡げ、通した key を
  provenance へ記録する。`s8b_prediction_runner` / `claude_projected_provider` の共有点 1 箇所。
- (S2) 受入 = 8c の実 Claude **no-build** 全 cell を Pegasus 計算ノードで走らせ、
  12/12 role attempt valid・3/3 dry-pass を実測する (`--workloads ycsb-a,ycsb-b,ycsb-c
  --max-generations 1 --no-build`)。fix 前は同一経路が role-invalid になることを対照として残す。
- (S3) runbook §7.1 の「外部 network 不可」を実測どおりに訂正する (DNS/直結は不可、
  HTTP(S) proxy は在る)。この誤った前提は [T-236] の裁定根拠にも引かれている。
- (S4) 記録と再スコープ。T-241 の残りを「campaign build の Pegasus 対応」として起票する。

**やらない (裁定パッケージへ回す):**
- buildcache の compiler / 依存 prefix を env_contract 解決へ寄せる作業。compiler が
  gcc-13→gcc-12 に変わると生成コードが変わり、既存 `linux-baremetal` 数値との比較可能性に
  関わる = 設計択一。契約 schema の拡張も伴う。
- 任意 bnode での env attestation 通過確認、live build/bench 本走。

## 不変条件

- allowlist を拡げるのは **transport のみ**。role へ渡る文脈・能力は 1 bit も増やさない
  (tools=[]、空 MCP、setting-sources 無効、`--no-session-persistence` は不変)。
- 拡張後も非 allowlist の env が漏れないことを exact 一致で検査し続ける (受理集合を
  「proxy 分だけ」広げたことを機械で示す)。
- 実測は計算ノードのみ。login では build/bench/test を走らせない。
- 実装面は Codex `role=author` が書く。親は brief・裁定・統合・全走・記録・commit のみ。

## 成果物影響 (DW-G05)

- (S1) 未実施なら: 計算ノードで 8c/8b を回すと **全 role attempt が `role-invalid`** になり、
  台帳には「LLM が schema を破った」と読める記録だけが残る (実体は transport 断)。
  失敗理由の誤帰属であり、規律 3 の「なぜ壊れたか」を最初から誤らせる。加えて 1 attempt あたり
  最大 `CLAUDE_TIMEOUT_S=1200` 秒を焼く。
- (S3) 未実施なら: 「計算ノードから LLM を呼べない」という誤事実が裁定根拠に残り続ける
  ([T-236] の裁定文が現に引いている)。

## 攻撃対象の provisional 裁定

- **(P1)** proxy 変数の通し方は「`http_proxy`/`https_proxy`/`no_proxy` (+大文字) を存在時のみ
  素通し」を既定案とする。site 条件付き (Pegasus のときだけ) にはしない — 環境差を driver に
  焼き込まない (93) の方針に反するため。
- **(P2)** 通した transport key を envelope/journal の provenance へ記録する。値そのものは
  記録しない (proxy URL に資格情報が入りうる)。key 名と、値の SHA-256 までを候補とする。
- **(P3)** 既存 exact 一致テスト (`test_s8b_prediction_runner.py:544-556`) は allowlist を
  ぴったり固定しているので、拡張は必ずこのテストを意図的に更新する形になる。純増検出力は
  「proxy が在れば通る」「proxy が無ければ key を作らない」「非 allowlist は依然落ちる」
  「provenance に key が載る」の 4 vector。
- **(P4)** 本 wave は正しさ防壁 (role 隔離契約) に触るため軽量版にしない。段 2/3 の
  codex plan + 敵対相談、段 6 の敵対レビュー 2 本を省かない。

## 分割方針

実装面は 1 ファイル群 (provider 2 本 + そのテスト) に収まるため実装子は 1 本。
敵対レビューは「隔離契約の緩みを探すレンズ」と「provenance/秘匿と受入検査の恒真性を探すレンズ」の 2 本。
