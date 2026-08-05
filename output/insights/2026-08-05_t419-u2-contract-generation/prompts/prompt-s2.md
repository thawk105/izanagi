あなたは izanagi の開発 wave の**プラン起草者**である。読み取り専用で、実装も編集もしない。
出力は日本語の Markdown 1 本。file:line 粒度の実装プランを書く。

## 必読 (読めなければ即停止し、その旨だけを出力する)

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/t419-u2-contract-generation/brief.md`
- 設計正本: `output/insights/2026-08-05_t478-calibration-contract-generation/README.md`
  (特に §4 案 A′、§4.2 旧 artifact の扱い、§5 三状態、§7 変異候補)
- `orchestrator/campaign/env_contract.py` 全文
- `orchestrator/tests/test_env_contract.py` 全文
- `orchestrator/campaign/env_attestation.py` の `load_verified_calibration` 周辺

cwd は wave の worktree である。上記の相対 path はそこからの相対である。

## この wave の scope

親 brief の「scope」5 項目だけ。「scope 外」に挙がったものは**プランに入れてはならない**。
特に activation record / activation receipt / campaign identity / versioned predicate dispatch /
wrapper 結線 / probe の方式変更 / 較正の再取得は**すべて対象外**である。

## 出力に必ず含めるもの

1. **`env_contract.py` の改造プラン** — 世代列 `GENERATIONS`、`resolve_by_contract_sha256()`、
   transition predicate、`HistoricalContract` / `CurrentContract`、`require_current()` の
   シグネチャと配置を file:line で示す。既存 `lookup()` をどう扱うか (残す / 削る / 意味を変える)
   を明示し、残すなら誰が呼んでよいかを型で書く。
2. **`contract_sha256` 不変の論証** — 提案する構造で g1 の `contract_sha256` が現行と
   byte 単位で同一になる理由を、`_canonical_obj()` / `asdict` の挙動に即して書く。
   同一でなくなる提案は却下せよ。
3. **consumer 移行表** — `lookup()` を呼ぶ production 箇所を全列挙し (テストを除く)、
   各行に file:line と「`require_current()` へ移す / 据え置く / 別扱い」の別と理由を書く。
   据え置きが 1 件でもあるなら、それが型分離の抜け穴にならない理由を書く。
4. **env-literal AST 検査への影響** — `test_env_contract.py` の `V2_ENV_NEUTRAL_MODULES` は
   `env_contract.py` の免除 region を `_build_registry` と指定している。世代列を導入した後も
   免除が広がらないことを、免除 region の名前と範囲で具体的に示す。
5. **既存テストへの影響** — `test_env_contract.py` の既存 assert のうち壊れるものを列挙し、
   「期待を書き換えてよいもの (構造変更に伴う機械的追随)」と
   「書き換えてはいけないもの (防壁の弱体化になる)」に分けよ。
6. **新規テストの提案** — 性質で書く。既存テストが既に同じ性質を覆っているものは提案から外し、
   「純増の検出力」だけを残す。各テストについて、それが落ちる具体的な壊し方を 1 行で書く。
7. **親 provisional 裁定への意見** — brief の (P1) (P2) (P3) それぞれについて、
   賛成 / 反対と理由。反対なら代案を file:line で示す。

## 制約

- テストの実走は不要である。書込可能な tmp が無いので pytest 緑を要求されない。
  静的検査だけでよい。緑だと書いてはならない。
- 受理集合・凍結 bytes・calibration pin・`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` を
  変えるプランは書かない。
- 推測で file:line を書かない。実際に読んだ行だけを引く。

## 総括

出力の末尾に `## 総括` 節を置き、プランの骨子を 10 行以内でまとめる。
