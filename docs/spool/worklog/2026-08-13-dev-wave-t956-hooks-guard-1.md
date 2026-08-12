---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-t956-hooks-guard
seq: 1
title: hooks/ を guard 自身の判定対象へ加え、直接 3 経路を閉じた (コード + テスト、branch worktree-dev-wave-t956-hooks-guard)
---

## 本文

- **ユーザー裁定 (2026-08-13 第 7 束)**: 「[T-956] = 採用 (hooks/ を保護対象へ、Codex author +
  敵対検証)」。控えは rulings-inbox `2026-08-13-rulings8-batch.md` の「防壁 3 件」。
  [T-955] = 据置 / [T-957] = 終端は本 wave の scope 外として一切触れていない。
- **成果の限界を先に書く。** 本 wave が閉じたのは **信頼済み PreToolUse が観測した、事前登録済みの
  直接 payload 3 形 (Edit 1 / apply_patch 1 / Bash 1) を実測で 3/3 拒否**したところまでである。
  「worker の guard 書換えを封じた」「fully closed」とは書けない。残余は下記のとおり。
- **wave 前の実測 (親)**: 3 経路すべてが hooks/ への書き込みを rc=0 で受理していた。
  `codex_worker_launch.py` は hook 検証の直後に排他なく `Popen` し、worker 存続中の再検証も無い。
  guard bytes の pin は HEAD blob との動的照合であって凍結 literal ではない (よって凍結族の
  手順は不成立)。
- **敵対検証は独立コンテキストで 3 本 + 焦点 1 本**。段 3 の 2 レンズ、段 6 のレビュー 2 本、
  焦点再レビュー 1 本。段 6 の 2 本は**独立に同じ単調性の反例**へ到達した。
- **親の暫定裁定 3 件が反証された** ((P1) 拡張子列挙で足りる / (P2) leaf 判定で足りる /
  (P3) 1 patch で足りる)。さらに**親の追補裁定 §4.5 (共通 canonical の raw 化は単調)
  も反証された** — 反例があり、legacy と raw の 2 系統を保持して deny union にする形へ改めた。
- **既存欠陥を 1 件発見 (本 wave の産物ではない)**: `_is_read_only` の allowlist に残る実 writer
  6 形 (`awk` の出力 redirection・`sed -n 'w'`・`git diff --output=`・`sort -T`・`find -fls`・
  `xxd -r`) が、**現行実装で既存保護対象 (WAL) を書ける**ことを親が実測した (対照の `echo >>`・
  `rm` は正しく拒否)。hooks/ とは独立に成立するため別起票とし、本 wave では直していない。
- **変異検査 6/6 KILLED** (SURVIVED 0 / MISMATCH 0)。裁定が要求した 2 形 (wave 前への revert、
  保護を謳うだけで発火しない恒真形) を両方含み、受理集合を縮める wave なので過剰拒否を検出する
  正例も 2 件登録した。初回は期待 node の完全集合が未確定のため probe とし、実測集合で再登録して
  本走した (spec sha256 = 6fd41293…)。
- **段 5 第 1 attempt は自分の変更で締め出されて停止した** ({{F:guard-self-lockout}})。
  実装子は正しく fail-closed で止まり、回避しなかった。回収と再投入の手順は
  {{D:guard-self-edit-protocol}} に記録した。
- **エージェント工数**: codex 子 8 本 (plan 1 / consult 2 (1 本は上流分類器に拒否され再投入) /
  author 2 / fix 2 / review 3 / focus 1)。段 3 レンズ A の初回は 22 分・出力 token 約 4.1 万を
  消費して output_bytes=0 で終わった ({{F:codex-cyber-classifier-refusal}})。
- **受入**: (実測前。受入全走の結果は同 commit に追記する)

## 次の一手差分

### 完了

- [T-956] 裁定が採用した「hooks/ を保護対象へ加える」を実装し、直接 3 経路の拒否を実測した。
  裁定 scope 外だった 2 つの時間窓は {{T:guard-verification-windows}} へ切り出した。
  remaining: none
  base: ab813bb09599aef25e6e85ab90fe8868a1e6f5813065c0c95884b4f2bfc67f29

### 新規

- {{T:guard-verification-windows}} **P3・新規 ([T-956] の残余、裁定 scope 外)**:
  [T-956] の起票が指した 2 つの時間窓は未着手のまま残る。(1) `codex_worker_launch.py` の
  起動前検証 (`_require_attempt_hook_installation`) から `subprocess.Popen` までの間に排他が無い。
  (2) worker 存続中の再検証が無い (`check_codex_hooks` の参照は launcher 内 3 箇所のみで、
  attempt 開始時にしか走らない)。[T-956] は**この窓を閉じたのではなく、窓の間に in-band で
  書き換えられる経路を受理集合から外した**だけである。窓そのものを閉じるには、
  検証と spawn の間を不可分にするか、worker 存続中に周期再検証を入れるかの設計判断が要る。
  費用と得られる保証の見合いから、粗い provenance 基準では既定で見送り側。
  起票資料 = archive worklog `worklog-phase3-0812-495.md` の [T-956] 項と、
  本 wave の `hooks/README.md`「既知の限界」。
- {{T:allowlist-real-writers}} **P1・新規**: `hooks/guard_bash.py` の `_is_read_only`
  allowlist に残る実 writer を閉じる。`awk 'BEGIN {print > "…"}'`・`sed -n 'w …'`・
  `git diff --output=…`・`sort -T …`・`find -fls …`・`xxd -r … …` の 6 形が、
  **現行実装で WAL 等の既存保護対象を書ける**ことを実測済み (2026-08-13、
  `probe_allowlist.py`、対照の `echo >>`・`rm` は拒否)。[T-956] land 後は同じ 6 形を
  `hooks/guard_write.py` へ向ければ guard source の上書きにも到達する。scope は hooks 特例では
  なく**全既存保護対象**に対する reader mode の実 writer 判別。受入条件 = 6 形を hooks と
  WAL の双方で拒否し、対応する純読み形 (`awk '{print}' file`・`sed -n p`・`git diff -- path`・
  `sort file`・`find -print`・`xxd file`) は維持。flag/env の逃がし道を置かない。
- {{T:guard-bash-docstring-drift}} **P3・新規**: `hooks/guard_bash.py` の docstring
  (39-45 行付近) が現状と 2 点食い違う。(1)「Codex subprocess には hook が未配線」—
  `.codex/hooks.json` で配線済み ([T-983] が 2026-08-13 に land 済み)。
  (2) 限界の列挙に hooks subtree 保護 ([T-956]) が反映されていない。実装面ファイル内の記述
  なので Codex author が要り、hooks/ を触るため {{D:guard-self-edit-protocol}} の手順に従う
  (docstring 1 箇所のために有効化前 base からの作り直しが要るので、hooks/ を触る次の wave へ
  相乗りさせるのが安い)。
