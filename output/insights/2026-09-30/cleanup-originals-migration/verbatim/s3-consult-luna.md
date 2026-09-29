## 総括

**現案のまま撤去するのは止めるべきです。** 回収基準を超える T-2871 の複製、重複する発効 tag、誤った控えの所在説明、退避本数の不一致が確認できました。  
一方、調べた範囲では、対象木を残さなければ論文の数値・図や有効な事前登録が失われるという反例は見つかりませんでした。修正後に対象と退避を再照合すれば、掃除自体は進められます。

## 成立した攻撃

- **P2 — T-2871 の回収理由が基準を満たさない。** [gen-opt 設計 README:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/gen-opt-evolution-design/README.md:3) は案の採用も本走の承認もないと明記する。WAL 由来の所要内訳は[同:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/gen-opt-evolution-design/README.md:224) に転記済みで、[T-2871 記録:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-29/t2871-policy-loop-iter/README.md:65) は生死確認を研究系列と合算しない。**成果物への影響:** 回収すると、未採用設計の生データまで恒久保全する基準になる。**修正:** 2 campaign の追加回収を外し、後続の確定した入力が要ると示された場合だけ回収する。

- **P3 — tag と bundle の二重保全。** [B-5 事前登録:598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/b5-generator-contrast-preregistration.md:598) は v1 を閉鎖済み。[論文ストーリー:4225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/paper-story/2026-09-29.md:4225) は SHA と当時の所在を記すが、常時解決できる tag を入力には指定しない。commit の中身は main にないため bundle 保全には根拠がある。**成果物への影響:** tag を足しても、論文中の「branch にある」という古い所在説明は直らず、管理する ref だけ増える。**修正:** 検証した bundle とその復元方法を所在注記に記し、tag は追加しない。

- **P7 —「撤去後の唯一の控え」は誤記になる。** [K2 記録:206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md:206) は job dir の `originals-copy-20260922/` を byte 複製と記し、現物も確認した。[brief:37](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:37) の撤去対象は木で、job dir の他の file は残す。archive 自体も[README:6](/work/1/SFC/tanab/izanagi-repro-archive/README.md:6) で「写し」と定義する。**成果物への影響:** 控えの台帳が残存箇所を過少申告し、写しを正本と誤読させる。**修正:** 系列ごとに残る job dir 複製・archive 写し・撤去される原本を区別して書く。

- **P6・brief — 退避本数が対応表と合わない。** [brief:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:17) は A 群 56 本とするが、[targets-t0-backup.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/targets-t0-backup.json) の A 群 80 行を集計すると `backup=c` は **52 本**、`backup_ok=true` は **47 本**、退避記載なしは **28 本**。**成果物への影響:** 56 本を退避済みとして扱うと、撤去判定と事後報告が誤る。**修正:** 木ごとの対応表を正とし、退避の有無と利用可能性を別々に判定してから撤去する。

- **P8 — prune の照合キーが admin 名だけ。** [brief:38](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:38) は dry-run 候補を admin 名で比較する。一方、対象の mutation 木の `.git` は共通 gitdir の汎用名 `worktrees/repo` を指し、[調査表:117](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/s1-survey-3.md:117) も他 wave による同名の再利用を未確認としている。**成果物への影響:** 並行更新時に名前だけでは候補が移動済みの対象木か証明できず、他 wave の登録を巻き込む余地が残る。**修正:** prune 直前に各 admin entry の gitdir・元の絶対 path・HEAD を対象表と再照合し、対応が崩れたら止める。

## 不成立だった攻撃

- **P1 の一律撤去で論文数値が直ちに再導出不能になる、という攻撃は不成立。** 調べた K2 の[結果稿:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/paper-story/results/2026-09-23-k2-manual-loop-four-rounds.md:174)には原本 path と SHA が残り、K2・B-5 試走・MOCC 疎通・T-2850 試走 v2 の archive manifest には件数と `verify.ok=true` が記録されていた。ただし現時点の全 file を再 hash したわけではない。
- **P4 の新しい D は過剰、という攻撃は不成立。** [D2242:72114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/decisions.md:72114) が「branch は残す」と明記し、[依頼:42](/work/1/SFC/tanab/tmp/cleanup-originals-migration-2026-09-30/md_1.txt:42) も覆すなら新しい D を求めている。
- **P6 の tar が F1034 と同じ空 tar を生む、という攻撃は不成立。** [F1034:28366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cleanup-originals-migration/docs/failures.md:28366) の原因だった `-C` の順序と空の退避を見逃す問題には、[brief:47](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:47) が対処を指定している。件数照合だけで全 byte の一致を証明するものではないが、不要判定した木の退避に損失ゼロは求められていない。
- **91 本の撤去で「約 6 割減」は不成立の攻撃。** 91 ÷ 156 は約 58.3% で、[brief:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-cleanup-originals-migration/brief.md:5) の概数として妥当。7.2 秒・15 分超の過去の実測値そのものは再測定していない。

## 確かめたこと

必読の依頼原文、brief、調査表 3 本、退避対応 JSON、archive README を開いた。加えて上記リンク先の repo 一次資料、K2 の job dir 複製の現物、代表的な archive manifest、発効 commit とその ref を読んだ。代表的な木の名前についてコード・テスト側も検索した。

全系列の consumer 0 件と全 archive file の現在の hash 一致は独立に全数再検査していない。前日退避 c/d の tar・bundle の現物内容も検証していないため、対応表の `backup_ok` を実物の完全性の証明とは扱っていない。