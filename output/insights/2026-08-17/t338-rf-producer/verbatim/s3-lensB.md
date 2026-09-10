## 所見

LB-01 / blocker / 根拠: `s2-plan.md:35-52`、`s1-brief.md:64-71`、D163(1)、D229(6)、D481(6)(7) / S2 は永続 writer なしの byte assembler であり、`t139-receipt/v1` を一枚も produce しないため、raw producer 数は 0 のまま、validator は fixture しか読めず、D162(ii)(iii) は発火しない。

LB-02 / blocker / 根拠: `s2-plan.md:8-20`、`record-items-v2.md:29-53,573-585` / registry snapshot と `seal_stage()` に `study_id`、`study_stage`、campaign 境界がなく、pilot と main の stage-local slot や検証 allocation を分離できないため、attempt の双射が混在または欠落し、受理集合が変わる。

LB-03 / blocker / 根拠: `s2-plan.md:40-45,168-172`、`record-items-v2.md:719-726,801-827`、D162(2)(3)、D481(2) / `fields_without_attempts`、qsub 結果、marker、環境観測を外部 binding なしで受け取るため、schema-valid だが偽の pin・fileRecord・qsub fact を持つ receipt を作れ、発火条件と受理集合を不正に広げる。

LB-04 / blocker / 根拠: `s2-plan.md:21-24,170-172`、`atomic_publish.py:24-30`、D229(8) / atomic な一枚の publish primitive はあるが、event ledger の永続 append/read と外部固定 tip がなく、末尾削除や registry と receipt の同時削除が replay と双射検査を通るため、失敗投入の除外 mutation を検出できない。

LB-05 / must-fix / 根拠: `s2-plan.md:141-164,166-173`、D229(8) / P4 は三 mutation を必須 kill とする一方、plan 自身が launch 側削除、alpha lineage 整合改ざん、anomaly clean 化を現 scope では kill 不能と認めており、未検出を kill 済みと記録すれば mutation coverage と受理集合を誤る。

LB-06 / must-fix / 根拠: `s1-brief.md:75-79`、`s8b_holdout_admission.py:1-11,681-744,855-883,2011-2041,2708-2738`、`qualification/series.py:66-109,243-289` / M1/M2 の二ファイルが非再利用なのは確認できるが、別所には worktree 共有の O_EXCL ledger、exact coverage、hash replay がある。RF へ直輸入できるとは限らないが、これを検討せず atomic_publish だけを再利用すると、既存の耐性と別の台帳を重複実装する。

LB-07 / must-fix / 根拠: `s2-plan.md:37-39,58`、`approval_payload.py:166-171`、`blobref.py:93-169`、D282 / plan は path・size・sha256 と書くが、実際の BlobRef は path・commit・sha256 であり、D282 payload は固定 commit の Git blob から読む。worktree path を読む実装を許すと schema の pin が外れ、構造受理集合が変わる。

LB-08 / must-fix / 根拠: `s2-plan.md:112-137,168-175`、`s1-brief.md:86-88` / probe は binding、実在 allocation、pointer、semantic minimum の全真を要求するが、それらを scope 外にしており、未実走かつ赤見込みである。schema_valid だけで stage 5 を進めれば、D147/D163 が禁じた fixture-only の緑になる。

LB-09 / must-fix / 根拠: `s1-brief.md:19-24,75-77`、`s2-plan.md:70,174`、D496(1)(2)(3)、D162(9) / floor field が 0 件なのは D496 との直接結線がない根拠にはなるが、同 campaign の構成集合固定と失敗時の全構成再測定は別の lifecycle 条件である。registry に campaign/config-set identity と全体再測定の扱いがなく、失敗 campaign を部分 terminal 化すれば比較対象集合が変わる。

LB-10 / must-fix / 根拠: `s1-brief.md:70-71`、`s2-plan.md:70,177-183`、D229(6)、D481(7) / plan の順序は probe→S1→S2→S3 という内部順序だけで、producer→pilot→validator/consumer→本走の handoff を作らない。S2/S3 の pass を producer land と記録しても次段 pilot が読む artifact はなく、依存辺が実質的に切れる。

## 親 brief への反証

- M1、M2 は対象箇所で確認でき、反証なし。
- M3 の D229 名指しは正しい。ただし「qualification だけが候補」という含意は未検証で、`s8b_holdout_admission.py`、`qualification/series.py`、T-810 coordinator に再利用候補がある。
- M4 の floor 0 件と三 arm の確認は正しい。ただし D496 との無関係という結論は過剰で、campaign lifecycle の影響を別途扱う必要がある。
- M5 の `declared_use_class` は pin schema と T-479 により確定している。
- M6 の digest 実測は正しいが、「pin 参照は test だけ」は不正確。実際の権威経路は `approval_payload.py` と `read_pinned_blob` である。
- M7 の producer 0 件は正しい。その事実が、永続 writer を実装しない S2 を producer と呼べないことを示す。
- M8、M9 は確認でき、M9 は投入なしの実 receipt が作れない根拠になる。
- P1 は s8b_floor_stats/campaign を外す判断は正しいが、他の durable ledger 機構を調査しておらず、再利用方針が未確定。
- P2 の dry による end-to-end receipt は誤り。dry は利用意図の enum であり、qsub・marker・verification allocation の免除ではない。plan の P2 後半がこの点を反証している。
- P3 は安全な停止条件として正しいが、probe は未実走であり、現 scope では緑にならない。段 5 へ進める根拠にはならない。
- P4 は mutation 候補の列挙としては正しいが、三本を必須 kill 済みとして扱うのは未検証である。
- P5 は本静的検査からの反証なし。本作業では pytest、probe、性能走行を実施していない。

## scope 外だが real な所見

SO-01 / `PreregBinding`、resolver、measurement head、fileRecord の存在・size・hash・単一 snapshot を検証する persistent writer。`record-items-v2.md:719-726` が要求するため、別 wave の裁定対象である。

SO-02 / 独立 semantic validator と consumer hook。D162(3)(10)(iii)、D481(6)(7)、D229(8) の raw 再読、alpha 全履歴、anomaly 再判定、RF 判定を担うが、D229 の順序上この wave では実装しない。

SO-03 / pilot の実 qsub fact、stage/campaign binding、D496 の全構成再測定。pilot submission は forbidden のままなので、実装ではなく次段の handoff と裁定 package にする。

## 総括

NO-GO。  
S2 は永続 receipt producer ではなく、S1 も外部 tip 付き durable authority ではない。  
stage-local receipt、binding、D229(8) mutation kill、D496 lifecycle の未結線が残る。  
M1/M2 の否定は正しいが、それだけでは P1 の再利用結論を支えない。  
pytest と probe は未実行で、緑の結果はない。