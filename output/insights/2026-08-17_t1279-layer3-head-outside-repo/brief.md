# 段 1 brief — [T-1279] repo 外 campaign で layer3 レポート生成が必ず失敗する件

wave: dev-wave-t1279-layer3-head-outside-repo / branch: worktree-dev-wave-t1279-layer3-head-outside-repo
親: izanagi dev-wave manager / 2026-08-17 08:55 JST

## scope

`orchestrator/campaign/layer3_report.py` の `generated_from_head` fallback が repo 外 campaign で
`Layer3ReportError` を投げる件だけを直す。schema 側の `perf_observation` 穴 (worklog 618 で land 済み)
は scope 外。版の権威をどこに置くかの敵対検証も scope 外 (裁定で不要と確定)。

## 確定済みユーザー裁定 (2026-08-17 /rulings 全件 第 5 回、worklog 622)

- **repo 外 campaign でも失敗しない形にすること**だけを要求する。
- 値は呼び手が渡す既存経路 (campaign.lock が束縛する pin) をそのまま使ってよい。
- 理由: commit ID がだいたい分かれば同じコードを再現でき、それもだいたいでよい。論文は版と性能の
  厳密な結び付けを求めない。
- 不変: official 経路の受理集合を緩める向きへは進めない (規律 2)。

## brief 前の実測 (親が本 worktree で実施、2026-08-17 08:46-08:55 JST)

1. `orchestrator/campaign/layout.py:271-332` — `_resolve_exploration_output_root` は
   `_has_git_ancestor(resolved)` が真なら `ValueError("... は repository 外でなければならない")`。
   **探索 campaign は機械的に repo 外に置かれる**ことが仕様として強制されている。
2. `git -C <repo 外 dir> rev-parse HEAD` の rc=128 を実測 (fatal: not a git repository)。
   したがって `layer3_report._git_head(campaign_dir)` は探索経路で必ず送出側に回る。
3. `orchestrator/campaign/p3_autonomous_workload_trial.py:1762` — 8c は
   `layer3_report.render(campaign_root, persisted, output_root=...)` を
   `generated_from_head` 無しで呼ぶ。`build_report` (layer3_report.py:511) の fallback に必ず入る。
4. `orchestrator/campaign/autonomous_trial_completeness.py:2091-2098` — persisted の
   `generated_from_head` が `_GIT_OBJECT_ID_RE` (hex40 または hex64) でなければ campaign-chain が
   fail する。**代替値は git object ID 形でなければならない。**
   同 2139 行は比較射影から同 field を pop するので、決定論比較には影響しない。
5. `orchestrator/campaign/layer3_schema.json:9` — `generated_from_head` は minLength 1 の string
   としか縛られていない。schema 変更は不要。
6. `orchestrator/campaign/campaign_lock.py:60-70,197-199` — v2 lock の
   `authority.contract_loader_commit` は hex40 で検証済み。`layer3_report.py:444` の
   `_read_campaign_lock` は既に `DecodedCampaignLock` を得ており、`authority` (v1 では None) へ
   到達できる。**新しい読み取り経路も新しい引数も要らない。**
7. `orchestrator/campaign/ident.py:469-484` — v2 authority は
   `require_environment_contract=True` の lock 作成時にだけ書かれる。既定は True
   (`ident.py:334`)、`guided.py:179,205` だけが False。**8c 探索 lock が v1 になる経路が
   残っていないかは段 2 で file:line 実証すること (P1)。**
8. 既存 consumer: `orchestrator/tests/test_p3_autonomous_workload_trial.py:2368` が
   `monkeypatch.setattr(A.layer3_report, "_git_head", lambda _root: "a" * 40)` で
   **位置引数 1 本**の signature に依存している。signature を変えるならこの test も同時に直す
   (親の no-touch 対象ではない — 通常の consumer)。

## 不変条件

- official (repo 内) campaign の `generated_from_head` の値は、変更前後で**同一**でなければならない。
  受理集合を緩める向きの変更を入れない (規律 2)。
- 結果値は常に hex40 または hex64 (上記 4 の consumer 要求) を満たす。満たせない場合は
  黙って placeholder を入れず fail-closed で送出する。
- `generated_from_head` は provenance 専用であり、決定論比較の対象外という既存の宣言
  (layer3_report.py:23, layer3_schema.json の description) を変えない。
- 新しい gate・新しい検証機構を作らない (裁定: 厳密化しない)。

## provisional 裁定 (親の暫定判断であり攻撃対象)

- **(P1)** fallback 順序は「明示引数 → campaign.lock v2 の `authority.contract_loader_commit`
  → 生成器自身が居る repo の HEAD → fail-closed」とする。campaign_dir に対する
  `git rev-parse` は**意味的に誤り**であり (問うべきは生成器の版であって campaign 置き場の版ではない)、
  順序から落としてよいと親は見ている。ただし official 経路の値が変わらないことの実証が要る。
- **(P2)** v1 lock (authority 無し) で repo 外という組み合わせは、pin が存在しないので
  fail-closed のままでよい。8c がその組み合わせに落ちないことを段 2 で file:line 実証する。
  落ちうるなら P1 を再設計する。
- **(P3)** 8c 呼び手 (`_finalize_build_cell_admission`) は変更しない。layer3_report 側だけで閉じる。
  呼び手へ引数を足す案は、同じ穴を持つ他の呼び手を取り残すので採らない。

## 成果物影響 (DW-G05)

- 直さない場合: 8c 探索 campaign の build cell が `AutonomousTrialError` で必ず倒れ、
  **certified 選択も層 3 材料レポートも 1 件も生成されない**。8c 探索は 0 試行で終わる。
- 直した場合に変わる値: 探索 campaign の `reports/layer3_report.json` の
  `meta.generated_from_head` が「存在しない」から「lock が束縛する hex40 pin」になる。
  official campaign の同 field は不変 (不変条件で束縛)。

## 成果物の形

- production: `orchestrator/campaign/layer3_report.py` の fallback 1 箇所 (+ 必要なら signature)。
- test: repo 外 campaign で `build_report`/`render` が成功し、`meta.generated_from_head` が
  lock pin と一致することを示す回帰テスト。official 経路の値不変も同時に pin する。
- 既存 consumer (`test_p3_autonomous_workload_trial.py:2368`) の追随。
- docs: worklog fragment (spool)、必要なら decisions fragment。

## 分割方針

実装面は単一 file に閉じるので実装子は 1 本。段 2 のプラン子 1 本 (read-only) を回して
P1/P2 を file:line で実証させる。段 3 の敵対相談は裁定が明示的に不要と述べたため省く (軽量版)。
段 6 は敵対レビュー 1 本 + 変異 matrix + 受入全走。

## 環境

- 受入・テスト実行環境: 本 worktree
  (`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1279-layer3-head-outside-repo`)。
- 実測は login ノードで完結する範囲 (pytest の焦点走と受入全走)。計算ノードは要らない。
