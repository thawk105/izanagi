静的レビュー所見（pytest・変異の実走は未実施）。

1. **real / blocker — caller の探索根配線が実効化されていない**

   `.claude/commands/cleanup-branches.md:17-18` は `--offrepo-root <runbook §7.2 の dir>` というプレースホルダを渡す一方、`tools/audit_dangling_commits.py:680-684` は CLI 指定時に env を完全に無視する。runbook の env 記載 (`docs/pegasus-runbook.md:739-749`) が caller では使われない。

   放置すると探索根が実体化されず、実 repo の抑止 2 対・注記 11 対が得られず、残り 6 commit / 26 対のままになる。

2. **real / blocker — B-4 の env 名誤記変異をテストが検出できない**

   実装は `tools/audit_dangling_commits.py:25,683` の `OFFREPO_ROOT_ENV` を読む。環境 default テストは `orchestrator/tests/test_audit_dangling_commits.py:477-492` で `ADC.OFFREPO_ROOT_ENV` を設定しており、定数を誤記しても同じ誤った名前へ設定するため緑になる。M05 の literal (`:391`) は CLI root 指定時であり env を読まない。

   放置すると `IZANAGI_DEV_WAVE_JOBS_DIR` の実運用誤記が検出されず、env 経由の外部コピー抑止が全件失われる。

3. **real / blocker — command 編集が `check_docs` の consumer pin と未同期**

   現在の command は 3987 bytes で 4000-byte cap 内だが、実体 hash は `2f97cc…`、`tools/check_docs.py:403-405` の期待値は `757d46…` のまま。`tools/check_docs.py:4132-4140` が不一致を検出し、`orchestrator/tests/test_check_docs.py:5856-5863` は実 repo の rc=0 を要求している。

   放置すると command の変更を含む land は docs 検査で停止する。

4. **real / blocker — M06・M07・M09 は受理集合の kill ではなく diagnostic pin**

   - M06: `orchestrator/tests/test_audit_dangling_commits.py:411-434`
   - M07: `:277-295`
   - M09: `:459-475`

   いずれも変異で最終 `findings`/rc が変わらず、出力文字列（抑止節、探索未実施、fold-tree の表示）だけが変わる。DW-M03 上は acceptance kill ではなく diagnostic sensitivity pin として別枠にすべきである。

   放置すると変異 matrix が 10/10 の受理集合被覆を誤って主張し、抑止数・探索未実施の開示が消えても意味的 kill として扱われる。

既存8テストは、`monkeypatch.delenv` の追加以外に期待値の反転・緩和・skip・削除は確認できない。B-3/B-5/B-6/B-7 の実装逐語と対応 control は存在する。ack 台帳・prune・T-593 項目・hardlink/root-symlink防護の scope 外実装も確認されない。

## 総括

1. blocker は **4件**。
2. 受理集合の kill としては **M06・M07・M09 が緑のまま**（raw test は診断文字列で失敗し得るが、意味的 kill ではない）。
3. **NO-GO**。