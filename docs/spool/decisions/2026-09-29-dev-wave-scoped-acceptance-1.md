---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-scoped-acceptance
seq: 1
---

## {{D:scoped-acceptance}}. 知識面だけの wave は、機械分類と land の再検証を条件に縮小受入で land してよい

**ユーザー裁定 (2026-09-29 夜、逐語):** 「あなたとやっている仕事ってさ、これまで昔からあった izanagi のテストを回さなくても問題ない話だよね？なぜなら izanagi システムとあまり関係ないじゃん？
あなたと私と dev-wave で試行錯誤して知識を izanagi に蓄積させてるだけでしょ？つまり、特定スタイルの開発であったら main land めっちゃ早く終わらせられるよね？
そういうことがすでに dev-wave スキル定義でわかっていそうなのか、わかっていそうでなければわからせてやりたい」

**決定:**

1. 受入全走の免除は、変更面が知識面の許可差分に閉じると `tools/scoped_acceptance.py` が機械で判定し、その縮小受入の受領証
   (`dev-wave-scoped-acceptance-receipt/v1`) を `tools/dev_wave_land.py` が lock 内で再検証した wave だけに認める。wave の自己申告では免除しない。
   それ以外の wave (実装面が 1 byte でもある wave、分類不能な差分を持つ wave) は従来どおり受入全走 (v5 受領証) を要する。
2. 許可差分は閉じた列挙で最小に始める: `docs/spool/{worklog,decisions,failures}/` の fragment の新規追加、`output/insights/**` のテキスト
   (md/txt/csv/tsv/json/jsonl)、`docs/**/*.md`。いずれも通常 file の追加・内容変更だけを許し、削除・rename・mode 変更・symlink・gitlink・非 UTF-8 path・
   2 MiB 超は全受入。手順書 (`docs/dev-wave/**`、`docs/skill-self-improvement.md`)、台帳正本、`docs/archive/**`、`docs/handoff/**`、
   `docs/ai-provenance.md`、名前に preregistration・erratum・freeze を含む文書は全受入。
3. 正しさの門の入力は全受入に倒す。変更 path ごとの鍵 (full path、汎用名 README.md・index.md と日付以外の basename、
   `docs/<x>` 以下と `output/insights/<日付>/<slug>` 以下の祖先 path と汎用名以外の dir 名) のいずれかを、production code
   (docs/・output/・external/・Markdown・test・直接実行する検査 2 本を除く tracked file) の本文が部分文字列として持てば全受入とする。
   引用符やコメントを区別せず file 全体で照合し、過大除外側に倒す。`docs/spool/*`・`output/insights`・`output/insights/<日付>`・`docs` のような
   入れ物 dir は鍵にしない (入れ物を列挙する reader は fold・直接実行の検査・land の fold gate が担う)。この入れ物 reader を鍵で拾えないことは限界である。
4. 縮小受入で回す集合は、実 repo を読む test の一覧 (`_REAL_REPO_NODE_INVENTORY`)、docs・spool・provenance・inventory 系の固定 test file、
   変更 path と同じ鍵を文字列で持つ test file、insight を変えるときは `"insights"` を持つ test file、直接実行
   `python3 tools/check_docs.py` と `python3 tools/spool_fold.py --dry-run` とする。恒久除外と growth hold は受入全走と同じ意味で効く。
5. 取り込んだ main で runner・分類選択器・縮小 launcher・直接実行の検査 2 本・`orchestrator/tests/conftest.py` のいずれかの blob が
   tested main と違えば、縮小受領証を再利用せず再受入とする (D987 の拡張)。test file の追加・変更だけでは再受入しない (D662 と同じ割り切り)。

**D747 との関係:** D747 は受入を速くする手段として test の削除を採らないと決めた。本決定は test を 1 件も削らず、hold も足さない。
変更面に応じて回す集合を選ぶだけで、実装面を含む wave は引き続き全 test を回す。削除 (全 wave から検出力を奪う) と選択
(知識面だけの wave に対し、その変更が到達しうる検査を回す) は別の操作である。

**D237・D301 との関係:** D237 は「docs のみの wave も check_docs・spool fold を実 repo に対して走らせる test があるので受入全走を免除しない」とし、
機械 gate 化は範囲外としてユーザー裁定へ返していた。本決定はその裁定にあたり、D237 が挙げた検査を縮小集合と直接実行に必ず含めることで
その理由を保つ。D237・D301 の本文は遡及改変しない。`DW-S04` の受入の文だけを前向きに「縮小受入を land が再検証した wave 以外は免除せず」へ改めた
(変異 matrix の免除文は変えていない)。

**効果の限界 (実測は insight):** 縮小受入も計算ノードへ dispatch される。login の実効メモリ天井を同じ user の他 session が使い切っている
時間帯が多く、queue 待ちそのものは残る。短縮は走る test の量と、無関係な赤に当たる面 (再投入回数) から出る。

**budget:** `DW-S04` の追記は L1 予算 (余白 6 bytes) に入らず、D782 に従い既存記述の意味等価な削減で収容した
(`DW-S07` の括弧書き「insights は従来どおり直接書く」は直前の文が 3 台帳だけを縛ることと等価、`DW-S04` の「wave 開始後」を「開始後」)。
上限は引き上げていない。

**却下した選択肢:**
- `docs/**`・`output/insights/**` を一括許可する — 事前登録・凍結・論文の束縛が path で読む文書や、実 repo の insight を glob で読む test が実在し、
  縮小受入で見逃す (段 3 相談)。
- production reader を AST で全走査する — 初回工数が大きく、動的連結・glob・subprocess を追えず完全にならない。文字列一致で過大除外に倒す方が安く安全。
- 引用符で囲まれた文字列の中だけで照合する — コメント中のアポストロフィで引用の対応がずれ、後続の path 文字列を見逃す (段 6 レビュー)。
- basename と入れ物 dir を常に鍵にする — 直近の知識面だけの land 10 件が 10/10 全受入になり効果が消えた (段 6 の親の実測)。
- spool fragment と新規 insight の追加だけに絞る — 直近 80 land のうち知識面だけの 31 件中 11 件しか対象にならない。
- 受領証に分類結果を書かせて land がそれを信じる — 自己申告と同じ。land が固定 SHA から再導出する。
- 受入全走の v5 受領証を拡張する — 既存の全 wave の land 経路を変える。別 schema に隔離した。
