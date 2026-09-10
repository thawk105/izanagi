# 段 6 での裁定修正 (2026-08-26 05:05 JST)

`s4-adjudication.md` の修正である。両方あわせて段 4 裁定の正本とする。

## A-1. hook 変更を本 wave の scope から外す (§1 の一部を撤回)

**事実:** `hooks/guard_write.py` は hooks/ subtree 自身への書き込みを拒否し、例外は
`hooks/README.md` だけである。この guard は `.claude/settings.json` 経由で Claude 側にも
配線されているため、**codex 子も親も `hooks/guard_bash.py` を編集できない**。
実装子 C の `apply_patch` は実際にこれで拒否された。
`hooks/README.md` が定める正規手順は「防護有効化前の commit から作り直し、統合 commit を
作ってから次の子を起動する」であり、本 wave の変更単位を超える履歴操作である。**迂回しない。**

**裁定:** §1 のうち「hook が dispatch gateway の exact CLI 形を認識する」変更を scope 外とし、
裁定パッケージへ返す。汎用 task 自体は実装済みで動く。`-- pytest` / `-- cmake` / `-- perf` は
hook を通る。通らないのは `-- python -m pytest` の綴りだけである。

**実測で判明した重要な訂正:** 焦点走で、実装子 C が書いた**否定**テスト
(`unknown-task` / `lookalike-path` / `dot-path` など) も赤だった。つまり**現行 hook は
`dispatch_compute.py --task <任意> -- <重量コマンド>` を既に許している**。
この穴は本 wave 以前から存在し、汎用 task が作ったものではない。
未知 task を実際に止めているのは dispatcher の閉集合 (親と `_job_run` の二層) である。

したがって hook 変更を見送っても、**受理集合は本 wave 以前と同じであり、新しい露出は生じない**。
汎用 task の安全性は hook ではなく dispatcher の compute 限定 gate が担う。
段 4 §1 に書いた「hook を広げる」は、実際には「既に広い hook をむしろ狭める」変更だった。
この認識の誤りを記録に残す。

## A-2. 事前登録の修正

段 4 §12 の変異表から hook 由来の登録を外す。M7 (`check_docs.py` の alias/unpack 拒否) は
hooks とは別 file であり **そのまま残す**。他の M1〜M6 も不変。

## A-3. 段 6 fix 子へ出す指示 (親の裁定であることを明記する)

未実装の hook 変更を pin する `test_hooks.py` の 11 node は「実装を追い越した事前登録」であり、
**親の裁定として削除を指示する**。これは fix 子が自分の判断でテストを弱めることを
許すものではない (`DW-S06-B` の禁止は維持する)。

削除の代わりに、**現行 hook の実挙動 (gateway 内側 argv が hook では境界づけられないこと) を
明示的に pin する回帰テストを 1 本残す**。これは願望でなく現状を固定するものであり、
将来 hook を直したときに必ず赤になって気付ける。

## A-4. 実装子 A の欠陥 1 件

`orchestrator/tests/test_pegasus_dispatch_compute.py` に `import hashlib` が無い。
同 file の 81 赤の大半がこの `NameError` の連鎖である。fix 子が直す。
