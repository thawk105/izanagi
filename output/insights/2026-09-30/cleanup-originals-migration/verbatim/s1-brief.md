# 段 1 brief — cleanup-originals-migration (2026-09-30)

- 依頼: /work/1/SFC/tanab/tmp/cleanup-originals-migration-2026-09-30/md_1.txt (ユーザー、2026-09-30 01:0x JST)
- 起点: local main f0869d953、wave branch worktree-dev-wave-cleanup-originals-migration、job dir 本 dir
- 研究前進 (土台): worktree 156 本・branch 77 本の重さが研究 wave の検査を止めている。2026-09-29 の実測では、`git worktree list` が 7.2 秒で
  rescue gate (git 1 呼出し 8 秒上限) が完走できず、全 worktree の status は 15 分超だった。A・B の 91 本を撤去すると登録 worktree は 156 本から約 6 割減る。
  完了判定: A・B の全対象が「回収済み+記録付け替え済み+撤去」か「回収不要と判定+退避済み+撤去」になり、prune 候補 0。
- 確定済みユーザー裁定 (逐語は md_1): 既定は「回収せずに消す」、回収は価値を一次資料で示せた系列だけ、損失ゼロは要件でない、
  判定は Codex 2 役に掛けて AI が決める、実行をユーザーへ回さない、D2242 の「残す」を改めるなら新しい D で理由を書く、land まで通す、撤去は land 後。

## 棚卸し (段 1 実測)
- 対象: A 群 80 本 (targets-t0.json)、B 群の木 11 本 (t2853-r2-plot-fix1/fix2 を含む) と branch 11 本。
- 名指しの全数表: s1-survey-1.md (K2・B-5・A-1/A-2・T-2273)、s1-survey-2.md (T-2847/2849/2850/2865/2871/2868)、s1-survey-3.md (T-2724・T-2853 図・vhb-mw・scratch2・md2)。
  3 本とも、コード・テストが木の path を読む consumer は 0 件。(a) 論文の数値・図が原本からしか得られない、(b) 次の一手・phase3 が入力に取る、
  (c) 有効な事前登録が入力に取る、のいずれにも当たる系列は 0 件。論文が使う数値はすべて repo 内の派生物 (insight・結果稿) にある。
- 既存の写し: `/work/1/SFC/tanab/izanagi-repro-archive/` に K2 3 組・B-5 試走・A-1・mocc-conn 21 本・T-2850 試走 v2 18 本・T-2865 段階 F の campaign 原本が
  sha256 照合つきで写し済み (T-2853)。前日退避 (cleanup-branches-20260929c/d) は A 群の 56 本と B の一部を持つ (targets-t0-backup.json)。

## provisional 裁定 (攻撃対象)
- (P1) A・B の全系列を「回収せず消す」とする。ただし P2・P3 を除く。名指しは経緯・所在の記録であって回収理由にならない。
- (P2) 回収 1 件: T-2871 `trees/live` の campaign 2 本 (`…-c4efe427`・`…-4e8009c5`)。`gen-opt-evolution-design/README.md:43` が §6.1 の新事実
  (評価 1 回の約 9 割が検査) の生データとして WAL を名指しし、その事実が gen-opt 設計の前提。小さいので campaign dir ごと展開して写す。
  置き場は `izanagi-repro-archive/cleanup-originals-20260930/` (既存規約: README・manifests/<item>.{json,sha256}・data/)。
- (P3) B-5 発効 commit `6fce61d6e` (唯一の ref が branch `worktree-dev-wave-t2797-b5-main-run`): tag `archive/t2797-b5-effect` で残し、branch は削除。
  論文稿 (paper-story 2026-09-29 版・paper-methods-ja・comsys 原稿) が SHA を名指しするので、SHA が解決できる状態を 0 費用で保つ。bundle も併せて取る。
- (P4) branch `worktree-t2273-shard0-local-copy`: bundle 退避後に `-D`。D2242 決定 1「branch は残す」を新しい D で改める
  (D2243 項 2 が候補 (c) = この実装の中立 land を不採用、この branch を入力に取るタスク無し、実装は insight §2 が記述し bundle で復元可)。
- (P5) main 非祖先の branch (scratch-t2724-chain-check、t2853-r2-plot-author/fix1/fix2、codex/t2853-r2-fig6-author、t2868-probe-author、
  probe/t2489-a2-nodes5-submit、md2-pack-hint-fix、worktree-dev-wave-t2797-b5-main-run、worktree-t2273-shard0-local-copy) は 1 本の bundle に退避・verify・list-heads 一致を確かめてから `-D`。
  main 祖先の freeze-g1-gen-t2724 は `-d`。
- (P6) 前日退避の無い木 (t2849-mocc 2・mocc-conn 22・t2868 sb1-4・t2868-probe-author・vhb-mw9/10・scratch2 repo・t2853 4 本) は、撤去前に未追跡物
  (`ls-files -o --exclude-standard` + `output/` の ignored) を tar で job dir へ退避し、list 数と tar の非 dir entry 数を照合する (F1034)。前日退避がある木は HEAD 不変と未追跡件数の不変を確かめて流用。
- (P7) 記録の付け替え: 集約 insight `output/insights/2026-09-30/cleanup-originals-migration/` (対象表・判定・退避と回収の所在・名指しの逆引き表) を正本とし、
  原本の所在・固定 checkout・発効版として path を名指す insight README (pin されていないもの) の末尾に「所在の移動・撤去 (2026-09-30 追記)」節を足す。
  結果稿・版・claim-evidence (append-only の凍結物) は書き換えず、`docs/paper-story/README.md` に C14a 前例と同形の所在注記を足す。
  `izanagi-repro-archive/README.md` の表に行を足し、T-2853 の写しが元の木の撤去後の唯一の控えになったことを書く。decisions fragment 1 本 (P1・P3・P4 の方針)、worklog fragment 1 本。
- (P8) 撤去は land 後、land 調整役の CLEANUP OK の窓で: unlock → (branch 付きは detach) → 同一 FS のゴミ置き場 `/work/1/SFC/tanab/tmp/cleanup-trash-20260930/` へ mv →
  prune は dry-run 候補 (admin 名) が自分の移した集合と完全一致で PRUNE OK のときだけ 1 回 → 実体は背景で 2 並列削除。
  job dir 内の木以外の file (例 `dev-wave-t2850-trial-run/vprobe/runs/`・`consult-option/`) は動かさない。
- (P9) 段構成: 軽量版。設計択一 (P2・P3・P4) は Codex 2 役 (決定役 sol・攻撃役 luna、consult / high / read-only) で段 3 として攻める。
  repo の実装面の変更は無い (docs・insight のみ) ので段 5 は無し。一次資料から事実を書き起こす docs wave なので段 6 の read-only review 1 本は残す。
  repo 外の退避・写し・撤去 script は cleanup-branches 手順の実行物で repo に入れない。受入全走は land 前に行う。

## 不変条件
- 正しさゲート・規律 1〜3 に触れない (verifier・gate・テストのコードを変えない)。
- 凍結物 (結果稿・版・claim-evidence・receipt・MANIFEST・verbatim・raw) を書き換えない。追記は README 末尾の新節だけ。
- F26: `git worktree remove`・`git submodule deinit` を使わない。F1034: tar は `-C` を `-T` の前、list 数 ≤ 非 dir entry 数を撤去の前提にする。
- 稼働中 wave の木・branch、数時間以内に動いたもの、占有されたものは対象外。撤去直前に占有・HEAD 不変・施錠状態を再確認。
- push しない。prune は自分が移した集合と候補が完全一致のときだけ。
