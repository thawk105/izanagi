# 段 1 brief — 並行セッション開発の無駄なチェック削減 (parallel-dev)

- wave: `/dev-wave parallel-dev`、branch `worktree-dev-wave-parallel-dev`、基準 `5544794`
- 環境: `pegasus02` = `PEGASUS_LOGIN`。受入・変異・重い処理は計算ノードへ dispatch する
  (docs 検査・静的検査・編集はログインノードで可)

## 確定済みユーザー裁定

- 2026-08-01「codex はレートリミットが近いので使わないでください。claude を代わりに使ってください」。
  D95 の Codex author 契約に抵触するため、D105 決定 (1) の
  `AI-Agent-Waiver: reason=codex_rate_limit; ratified=2026-08-01` を統合 commit に付す。
  実装子・レビュー子はすべて Claude、`role=author` は Claude 側に立つ

## scope (実装する 4 件)

- **S1 — land が他セッションの handoff 形式不備で全体拒否するのをやめ、代わりに保護を広げる。**
  `tools/dev_wave_land.py`。現状 `_handoff_snapshot` (593-634) が `docs/handoff/` 配下の全ファイルを
  `_validate_handoff_at` (538-590) で内容検証し、1 本でも不正なら land 全体を `RC_CONTROL_PLANE` で拒否する。
  一方 `protected` (909) に入るのは**検証を通った handoff だけ**なので、形式不備の handoff は
  「拒否させるのに保護もされない」二重の欠陥にある。
  **成果物影響**: 放置すると wave の成果が main へ着地せず branch に留まり、worklog 台帳と main の状態が
  乖離する (実績: (73) の wave は着地しないまま終了、(77) は 1 回拒否)
- **S2 — 他セッションの 48h 稼働中 handoff が、無関係なセッションの必須 commit gate を落とすのをやめる。**
  `tools/check_docs.py:2185-2188`。所有者を見ずに findings を出し rc=1 になる。
  `check_docs.py` はクラス 2/3 の完了 commit で必須 (CLAUDE.md 作業の進め方 6(c))。
  **成果物影響**: 放置すると main checkout で作業するセッションが自分と無関係な理由で commit できず、
  台帳更新が滞る。**2026-08-01 10:15 頃に自然発火する** (実測済み)
- **S3 — repo に pytest 設定を新設し、collection 範囲を checkout 非依存にする (F41 射程拡大 / T-129、P1・未解決)。**
  repo に `pytest.ini` / `pyproject.toml` / `setup.cfg` が 1 つも無く、`testpaths` / `norecursedirs` /
  `collect_ignore` の指定もゼロ。main checkout で範囲指定なしの素の `pytest` は ignored な
  `output/s1-build-cache/` (36,158 件・1.8GB) の googletest 由来 `*test*.py` を収集し **1253 errors**。
  worktree では 0 件で緑。**成果物影響**: 放置すると「赤の有無が checkout に依存」し続け、
  受入結果を実装差分へ誤帰属する (F41 に実績)
- **S4 — worktree 置き場の除外を tracked `.gitignore` へ移す。**
  `.claude/worktrees/` の除外はマシンローカル・未追跡の `.git/info/exclude:11` にしかなく、
  repo に入っていない。`.codex/worktrees/` は無視すらされず main checkout で `?? ` として見える。
  **成果物影響**: 放置すると clone / 別マシン / exclude 消失で全 `git status` 系 gate が
  他セッションの worktree を dirt として拾う

## 不変条件 (緩めない)

- 正しさ防壁は緩めない。S1 は land が**保護する**範囲を広げ、**拒否する**範囲だけを狭める。
  ff-only・lock・stale 判定・audited closure・postcondition・identity/hash による mid-flight 変化検知は不変
- 他セッション所有物 (handoff・worktree・job・process) を変更しない。rebase / force / remote / push をしない
- 受理集合を変えるため D96 の手続に従い、decision 記録と境界テストを同じ変更単位で更新する
- 実装面は親が直接編集しない (D95 / D105 waiver 経路)

## 攻撃対象の provisional 裁定 (親の暫定であり段 3 で攻撃させる)

- **(P1)** S1 で内容 schema 検証を land から外しても安全である。根拠は
  「land の docstring が自ら *協調する manager 間の事故防止用であり sandbox ではない* と宣言している」
  「隣の handoff の**内容**は自分の ff-only merge の安全性に因果を持たない」。
  代わりに name-shape (`_SAFE_HANDOFF_RE`)・regular file・one link・size 上限・identity/hash snapshot は維持し、
  `protected` を**全直下 `.md`** へ広げる
- **(P2)** S2 は検出を捨てず「他人の commit を止めない形」へ移す。死んだセッションの検出という
  価値は残す必要がある (どこへ移すかは段 2/3 で詰める)
- **(P3)** S3 の設定新設は `run_tests.py` の既存起動形・`_is_acceptance_run` 判定・rootdir 解決・
  conftest 探索を壊さない。**未確認なので段 2 で file:line 粒度の確認を要求する**
- **(P4)** S4 は land の `_ignored_paths_for_target` / `_existing_ignored_target_or_ancestor` の
  受理集合を変えない (wave は `.claude/` `.codex/` 配下へ commit しないため)。**未確認**

## scope 外 → 裁定パッケージ

- **R1 — B 軸: main 進行に伴う再検査ループそのもの。** land は ff-only、stale なら拒否し、
  `DW-O23`/`D102` が fresh context での新 main 監査・固定 SHA merge・**受入再走**を義務づける。
  受入は D104 が約 200 秒の床を実測済み (in-scope の施策では動かない、T-201 が裁定待ち)。
  lock は `LOCK_NB` で待機なし、かつ設計上受入中は保持しない。D102 却下案 (c) が
  「同一 context での自動 merge / 再試行」を明示的に却下している。
  **既存の設計判断に正面から当たるので実装せず裁定へ返す。** ただし実発生分の相当部分は
  S1 の解消で消える (land 阻害起因の受入再走は実績 4 回 × 約 200 秒)
- **R2 — (72) の 12 回連続 rc=20**: 2 セッションが同じ `output/insights/` 配下を真に奪い合った衝突であり、
  land の判定は正しかった。ディレクトリ命名規約の側の課題として起票する

## 成果物の形と並列分割

- 成果物: 上記 4 件の実装 + 境界テスト + decision 1 本 + failures 追記 + worklog + 裁定パッケージ
- 分割 (編集ファイル所有が素集合): **U1** = `tools/dev_wave_land.py` + その境界テスト /
  **U2** = `tools/check_docs.py` + その境界テスト / **U3** = pytest 設定 + `.gitignore` + 収集境界テスト。
  U3 は S3 と S4 がともに「collection / ignore 面」で相互作用するため 1 単位に寄せる
