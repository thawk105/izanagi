---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t720-import-unify
seq: 2
---

## 新規

### {{F:mutation-found-what-review-missed}}. 新設した静的検査が「実際に使われていた書き方での再発」を素通りしていた [恒真ゲート] [テスト代表性]

- 事象: [T-720] で新設した import 不変条件検査が、`orchestrator/campaign/**` への
  `<repo>/orchestrator` の `sys.path` 挿入を **`pathlib` の書き方でしか検出できなかった**。
  段 2 プラン、段 3 敵対相談 2 本、段 6 敵対レビュー 2 本、焦点再レビュー 1 本の**計 6 本の
  静的レビューを通っても検出されず**、変異 M11 を実際に注入して初めて生存として現れた。
  是正後も module 別名 (`import os as _o`) 経由が素通りし、2 巡目の変異でまた生存した。
- 根本原因: 検査が「禁止したい**効果**」ではなく「禁止したい**書き方**」を列挙していた。
  `sys.path.insert(0, str(Path(__file__).resolve().parents[1]))` は解釈できたが、
  **本 wave 以前に実コードが使っていた**
  `sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))` は
  解釈できなかった。レビューは「回避形がある」という一般的指摘はしたが、
  **最も起こりやすい再発の形が既に取り残されている**ことは指摘できなかった。
  レビューは設計を読む。変異は実際に注入する。この差が出た。
- 分離できた範囲: 統一そのもの (production の import 形) には欠陥が無く、
  欠陥は新設した検査側だけにあった。既存の受理集合は変わっていない。
- 恒久対応: `_path_expression_kind` を、`pathlib` と `os.path` の両慣用形について
  **深さを数えて解決先 path を決める**形へ変え、lexical scope を尊重した module alias 表で
  別名も解決する。`orchestrator/tests/test_campaign_import_invariant.py` に、
  5 つの正例 (素の `os.path` / module 別名 / `os.path` 自体の別名 / `from import` の別名 /
  `pathlib` 別名) と 2 つの負例 (repo root は許す) を逐語で固定した。
- 再発検知: 同型は「新設した検査を、その検査が禁止したい**実際の過去のコード**に対して
  走らせていない」ときに起きる。変異事前登録に
  **「wave 前の実コードと同型の形」を必ず 1 件入れる**ことで検出できる。
  本 wave の変異 M11 がその役を果たした。

### {{F:secondary-fanout-missed-in-scope}}. 横断 import 統一の scope を「対象 package を読む箇所」だけで数え、二次波及を落とした [手順漏れ] [テスト代表性]

- 事象: [T-720] の受入全走で 20 件が赤くなった。原因は
  `tools/pegasus/submit_t126_qualification.sh` の heredoc 3 箇所と
  `tools/pegasus/collect_t126_qualification.py` が、`<repo>/orchestrator` を `sys.path` へ入れて
  **top-level `qualification`** として読んでいたこと。本 wave が
  `orchestrator/qualification/**` を canonical 化したのでこの経路が壊れた。
  `:410` の heredoc は qsub の**前**に走るため script がそこで終了し、
  テストが待つ疑似 qsub に到達せず `assert entered.exists()` が 19 件落ちた。
- 根本原因: scope 列挙を **`campaign` を import する箇所**の grep で作った。
  統一のために `qualification` / `critic` / `calibrator` も canonical 化したのに、
  **それらを読む消費者は数え直さなかった。** 一次の対象 (campaign) だけを閉包と見なし、
  同じ wave が副次的に変えた package の消費者を落とした。
- 分離できた範囲: 親が同一 worktree で ref だけを切り替える 3 走
  (tip → main → tip) で帰属を確定した。修正前 tip 20 failed / main 0 failed / tip 20 failed、
  修正後は 3 走とも 347 passed / 0 failed。フレークとの区別を実測で付けた。
- 恒久対応: `orchestrator/tests/test_campaign_import_invariant.py` の R-A は
  repo 全体の legacy `campaign` namespace を機械検査するが、
  **`qualification` など他 package の旧形は検査対象外**である。
  横断的な import 統一を行う wave は、**統一した package ごとに消費者を数え直す**。
  memory `import-unification-count-consumers-per-package` に規律として残す。
- 再発検知: 同型は「複数 package を同時に canonical 化し、scope 表を 1 つの package の
  grep で作った」ときに起きる。統一対象の各 package について
  `grep -rn "sys.path.*orchestrator"` と `from <pkg>` を独立に数えれば検出できる。

### {{F:parent-ruling-broke-under-measurement}}. 親の裁定「既存テストを完全に無編集で残す」が実測で倒れた [手順漏れ]

- 事象: 段 4 で「二重 namespace を検査する既存テスト 2 本は期待値も import 形も一切変えない」と
  裁定したが、`test_campaign.py` の別名 pin テストについて成立しなかった。
  同テストは module 冒頭の legacy import と対で成立しており、実装子が指示どおり
  「関数本体だけ」を保護した結果、冒頭が canonical・関数が legacy という**分裂**が残った。
  テストが `layout_module._effective_uid` を差し替えてから canonical 側の関数を呼ぶため、
  差し替えが別 module object に当たって静かに空振りし、計算ノードで 2 件が赤になった。
- 根本原因: 親が保護範囲を「関数」の粒度で書いた。テストが依存するのは関数の外にある
  module-level import だった。**保護対象を「テストが成立するために必要な依存の閉包」で
  書かなかった**ことが原因である。
  さらに、統一後は `importlib.import_module("orchestrator.campaign.layout")` が
  同一 object を返すため、そのテストは元の書き方では意図を表現できなくなる。
  「完全に無編集」は原理的に不可能だった。
- 分離できた範囲: もう 1 本 (`test_reflux_ir.py` の D149(5) peer 受理) は
  連鎖が campaign 内に閉じるため無編集で成立し、計算ノードで緑を実測した。
  裁定が倒れたのは 1 本だけである。
- 恒久対応: 最終形は「module 冒頭は canonical、別名テストの中だけで実 legacy namespace を読む」。
  **assert は 1 つも変えていない。** 途中で採った合成 module への置換は、段 6 レビューが
  「実 topology の退行を検出しなくなる」と正しく指摘したので撤回した。
  規律としては、**保護対象を書くときは依存の閉包で書き、実測で倒れたら親が裁定を直す**に尽きる。
- 再発検知: 同型は「テストの一部だけを例外として保護し、残りを機械変換した」ときに起きる。
  保護した関数が参照する module-level の名前を列挙して、
  同じ例外に含まれているかを確認すれば検出できる。
