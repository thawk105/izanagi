# [T-276] 段 1 親 brief — 計算ノードでの role 実行を解禁する

base commit: `3c924bb` (local main tip)。worktree: `.claude/worktrees/dev-wave-t276-compute-role`。

## 確定済みユーザー裁定 (worklog (102))

択 (b) 採用 = 計算ノードでの role 実行を解禁する。解禁の前に次の 3 件を閉じる。
① 攻撃者制御 proxy の MITM / injection (規律 6)、② proxy 値の同一性 provenance
(key 名だけでは別値が同一台帳へ混載)、③ 実装と同じ env から期待値を作る恒真な受入検査。
受理集合の変更なので D96 手続 (新 D + 境界テストを同一変更単位) を通す。

## 段 1 前提実測 (本 wave、request `877155` / bnode009 / 2026-08-01T20:57+09:00)

1. 計算ノードの proxy は **lowercase 2 key のみ** — `http_proxy` / `https_proxy` = `http://10.120.96.1:8080`。
   `HTTP_PROXY` / `HTTPS_PROXY` / `NO_PROXY` / `ALL_PROXY` / `FTP_PROXY` はすべて未設定。
2. TLS trust root を変える env (`SSL_CERT_FILE` / `SSL_CERT_DIR` / `REQUESTS_CA_BUNDLE` /
   `CURL_CA_BUNDLE` / `NODE_EXTRA_CA_CERTS` / `NODE_TLS_REJECT_UNAUTHORIZED` / `SSLKEYLOGFILE`)
   は 1 つも設定されていない。
3. allowlist 5 key + lowercase proxy 2 key で `claude -p` が **rc=0 / API 2.6 秒**で応答 (裁定の前提は生きている)。
4. **ログインノード (pegasus02) には proxy env が 1 つも無い** (本 wave 実測)。
   つまり transport は site ごとに非同型であり、②「同一台帳へ混載」は仮想でなく実在する差である。
5. 禁止は **prose のみ**で、`claude -p` を計算ノードで拒否する機械 gate は repo に存在しない
   (D108 決定 (1) と `docs/pegasus-runbook.md` §8 の 2 箇所)。
6. `CLAUDE_ENV_ALLOWLIST` は `s8b_prediction_runner.py:71` の 1 箇所で、
   `claude_projected_provider.py:23` が import して**共有**している。

## scope

- **in:** role provider の transport 受理集合 (planner/coder/auditor/critic = D108 の 4 役が通る
  `ClaudeProjectedRoleProvider`)、新 leaf の transport 受理判定、Pegasus policy への宣言、
  境界テスト、新 D、D108 決定 (1) の supersede 注記、runbook §8 の該当行是正、worklog。
- **out:** `dispatch_compute.py` への campaign task 新設 (= T-236、凍結裁定済み)、
  `_site_admits_measurement` の Pegasus 拒否 (= T-277)、build identity 拡張 (= D108 決定 (5) / T-277)、
  `s6_proposal_rounds.py` の env 非対称 (= T-278)。

## 不変条件

- `CLAUDE_ENV_ALLOWLIST` の中身は変えない。s8b ratified 経路 (`ClaudeHeadlessProvider`) へ
  transport を波及させない。理由: その `agent_provenance` は `s8b_selector_freeze.py:88` で
  **exact 8 key** に凍結されており、transport identity を足せば凍結 schema が割れる。
  s8b が login 専用に留まるのは**意図的な境界**であって取り残しではない。
- 既定挙動は現行と同一 (proxy を落とす)。admission は明示 opt-in でのみ成立する。
- 凍結 bytes・`FROZEN_MANIFEST`・既存 cache・certified 選択・proof chain を変えない。

## provisional 裁定 (親の暫定。攻撃対象)

- **(P1)** 受理は lowercase `http_proxy` / `https_proxy` の 2 key だけ。実測が支持しない
  uppercase / `no_proxy` / `all_proxy` へ一般化しない ((96) の敵対レビューが同じ過大一般化を訂正済み)。
- **(P2)** 値は policy file の宣言と exact 一致でなければ拒否する。**期待値を実行時 env から作らない** (③)。
- **(P3)** TLS trust root を変える env が source env に 1 つでも在れば fail-closed で拒否する (①)。
  admission した 2 key 以外は子へ渡らないため trust root は既定のまま = proxy は CONNECT の
  metadata しか見えない。この構造的性質を receipt に書き、恒真にならない形で検査する。
- **(P4)** admission は `site_policy.current_site() == PEGASUS_COMPUTE` のときだけ許す。
  login / SUSPECT / OTHER では宣言があっても拒否する。
- **(P5)** receipt (mode / 受理 key 集合 / endpoint 値 / 値の sha256 / policy 宣言 sha256) を
  projected provenance へ足す (②)。同 provenance に exact-key gate が無いことは実測済み
  (`capability_lowering` の consumer は test 1 本のみ)。

## 成果物影響 (DW-G05)

実装しない場合、live pilot は transport 断のまま走り、台帳には「LLM が schema を破った」と
読める `planner-invalid` だけが残る (実体は transport 断。規律 3 が network 境界で片肺)。
実装した場合、試行台帳の各 role 行が transport identity を持ち、
login 直結で作られた行と compute proxy で作られた行が**値で**識別できるようになる。

## 成果物の形

1. `orchestrator/campaign/claude_transport.py` (stdlib-only leaf)
2. `orchestrator/campaign/claude_projected_provider.py` の opt-in 配線 + provenance 追記
3. `tools/pegasus/policies/transport_v1.json` + `registry_v1.json` への登録
4. `orchestrator/tests/test_claude_transport.py` (D96 の境界テスト)
5. docs: 新 D、D108 決定 (1) supersede 注記、runbook §8、worklog (親が書く)

## 分割方針

実装子 1 本 (leaf + 配線 + policy + 境界テスト、docs と commit は禁止)。
敵対レビュー 2 本 (レンズ A = 信頼境界 / MITM / 規律 6、レンズ B = 恒真性・consumer 取り残し・
凍結波及)。受理集合が変わるため `DW-C00` により段 2・3 と段 6 の review 子は省略しない。
