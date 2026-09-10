## 所見 1: pair 単位の発行前拒否まで消える

深刻度: blocker

file:line: [s2-plan.md:18](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:18)、[s8b_floor_campaign.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:748)、[s8b_floor_campaign.py:966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:966)、[s8b_floor_campaign.py:1009](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:1009)、[s8b_floor_campaign.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:1060)

具体的な失敗筋:

- plan は `occupied_contract_paths` を全削除するが、この分岐は contract 封鎖だけでなく、target pair が既に index にある場合の発行前拒否も偶然担っている。
- `HEAD gitlink == legacy anchor の pin` の状態では、target pair は legacy path ですでに index 済みだが、導出される versioned path は別なので create-only writer は成功する。
- その後の full-index scan で初めて duplicate pair が検出され、無効 artifact が残る。組単位一意性は発行後に破られる。
- versioned 側に同一 pair が既存の場合も、writer の拒否が [s8b_floor_campaign.py:935](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:935) の「作成済み artifact を取り除け」という message に変換される。今回作成していない正規 artifact の削除を誘導する。
- plan の同一 pair 再発行テスト [s2-plan.md:111](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:111) は versioned destination の存在で writer が拒否する形しか踏まず、legacy pair 衝突を検出しない。

提案する修正:

`occupied_contract_paths` を丸ごと消さず、`target_pair in index` の狭い発行前拒否へ置換する。同一 pair の既存 record path を示し、writer を呼ばず、削除指示も出さないこと。legacy pair 衝突と versioned pair 再発行の双方で、destination 不生成・writer 未呼出し・先行 bytes 不変を検査する。

## 所見 2: P1 の先行投入で admission と実行 protocol が分裂する

深刻度: blocker

file:line: [s1-brief.md:51](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s1-brief.md:51)、[s2-plan.md:23](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:23)、[s2-plan.md:69](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:69)、[certified_writer_admission.py:201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/certified_writer_admission.py:201)、[floor_campaign.sh:954](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/tools/pegasus/floor_campaign.sh:954)

具体的な失敗筋:

- 現在値は contract `e576e9cd…`、legacy pin `d706650c…`、HEAD pin `511c9538…`。contract 拒否撤去後、公開 CLI [s8b_floor_campaign.py:6706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:6706) は現在の組で versioned artifact を直ちに発行できる。
- index は versioned namespace を HEAD tree ではなく working tree から読む [s8b_floor_campaign.py:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:829)。したがって未 commit artifact でも P1 は HEAD-pin exact として選ぶ。
- `submit_floor.sh` は `output/` 配下の untracked file を許す [submit_floor.sh:213](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/tools/pegasus/submit_floor.sh:213)。job 側の清浄性検査も `output` を除外する [floor_campaign.sh:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/tools/pegasus/floor_campaign.sh:565)。
- `_admit_floor` は versioned record を authority として PASS する一方、実 driver は固定 legacy path を `--protocol` に渡す [floor_campaign.sh:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/tools/pegasus/floor_campaign.sh:968)。admission は pin `511c…` を見て、実測は legacy pin `d706…` で走る。
- versioned path は chain record として launch scan に受理される [s8b_floor_campaign.py:3860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:3860) ため、未知 file 拒否も止めない。
- resolver の repo 内 direct production call が `_admit_floor` の 1 件だけなのは正しい。しかし protocol authority の consumer は唯一ではない。固定 path consumer は [test_s8b_protocol_builder.py:998](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/tests/test_s8b_protocol_builder.py:998) が列挙する 6 面に残る。この meta test は不要な contract gate ではなく、現存する分裂の sentinel である。

提案する修正:

P1 を T-1214 の全 consumer 結線・実発行と同じ atomic wave まで延期するか、この wave の scope を明示的に広げて全 consumer を同時に index resolution へ移す。新しい禁止 gate を足さないという裁定を守るなら、延期または atomic 統合が妥当。meta test だけを削除してはならない。

## 所見 3: P1 は旧 singleton 受理へ新しい gitlink 前提を混ぜる

深刻度: major

file:line: [s2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:26)、[s8b_floor_campaign.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:883)、[s8b_floor_campaign.py:914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/s8b_floor_campaign.py:914)

具体的な失敗筋:

有効な HEAD anchor と current-contract record が 1 件あるが `external/ccbench` gitlink が欠落・不正、またはその追加 Git read だけが失敗する repository を考える。現 resolver は singleton を受理するが、P1 は fallback 判定前に `_ccbench_gitlink` を必ず呼ぶため拒否へ反転する。これは裁定された拡大に未裁定の縮小を混ぜる。

今日の実 repo と admission fixture はともに有効な gitlink を持つため、legacy PASS 自体は落ちない。しかし plan の「受理 bit は変わらない」は今日の一状態にしか成立しない。

提案する修正:

current candidates を先に数え、0 件は従来どおり拒否、1 件は gitlink を読まずそのまま返す。2 件以上の旧 resolver が拒否していた状態だけで HEAD pin を読み、exact 1 件を選ぶ。singleton 時に `_ccbench_gitlink` が呼ばれない回帰テストを追加する。

## 所見 4: D460 の現行決定が未 supersede のまま残る

深刻度: major

file:line: [decisions.md:19198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:19198)、[decisions.md:19209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/docs/decisions.md:19209)、[s2-plan.md:73](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:73)

具体的な失敗筋:

D460 は resolver を「current contract に一致する exact 1 件」と定め、さらに「選択条件に ccbench pin を入れてはならない」と明記する。plan は decision fragment で「D444 決定 5 だけ」を限定 supersede するとしており、P1 を書いても D460 の規範が生き残る。land 後は code と canonical decision が正面衝突する。

提案する修正:

新 decision fragment で D460 の「exact 1 件」と「pin を選択条件にしない」の部分も限定 supersede する。root-only API、caller 非選択、indexed SHA 再照合は維持対象として明記する。

## 所見 5: stale-contract と HEAD-pin の交差変異がテスト計画にない

深刻度: major

file:line: [s2-plan.md:27](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:27)、[s2-plan.md:114](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:114)、[s2-plan.md:125](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:125)

具体的な失敗筋:

current contract の old-pin record と、stale contract の HEAD-pin record を同時に置く。実装が contract filter より先に全 index から HEAD-pin exact を選ぶ誤りでも、列挙済みの exact、fallback、zero、ambiguous テストを通過し得る。`_admit_floor` の current-contract 再検証で最終的には拒否されるが、本来受理できる current singleton が stale record のため全面停止する。

提案する修正:

この交差入力で current record へ fallback する負例と、pin filter を contract filter の外へ移す変異を事前登録する。

## 所見 6: 「同じ commit OID」の照合だけでは二重 HEAD 読みを殺せない

深刻度: minor

file:line: [s2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:26)、[s2-plan.md:115](/work/1/SFC/tanab/dev-wave-jobs/2026-08-17_t1218-floor-reseal-rulings/s2-plan.md:115)

具体的な失敗筋:

実装が `_head_commit_oid` を scan 用と gitlink 用に 2 回呼んでも、テスト中に HEAD が静止していれば両 helper の受領 OID は等しく、提案された比較は常に通る。実運用で 2 呼出し間に HEAD が動いた場合だけ authority が分裂する。

提案する修正:

`_head_commit_oid` の call count を exact 1 に固定し、2 回目は異なる値または例外を返す side effect を使う。単なる受領値の等値だけを防壁として数えない。

## 独立検算

- worktree は clean、HEAD は `5a19b8ab`。
- versioned directory は不在で artifact は 0 件。
- legacy は contract `e576e9cd…e242c01`、pin `d706650c…40969`、SHA-256 `261cec1c…e74aac`。current contract は同じで、HEAD gitlink は `511c9538…706ec`。
- 現 resolver の read-only 実行は legacy path を返した。P1 の現 repo 分岐も exact 0、current 1 なので fallback PASS になる。
- `FROZEN_MANIFEST` は 23 key、held 4・keep 19で、versioned path は 0 件。named hold 2 件も [freeze_verification_hold.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1218-floor-reseal-rulings/orchestrator/campaign/freeze_verification_hold.py:20) に残る。計画された編集から既存 frozen bytes や hold 状態を動かす直接経路は見つからなかった。
- contract 単位拒否の live code/test pin は、plan が列挙した source 2 箇所と test 3箇所で全件だった。ただし D460 と固定-path meta sentinel は別問題として残る。
- pytest は未実行。read-only の静的検査と非書込 probe のみで、終了時も worktree は clean。

判定: **NO-GO**

blocker:

1. contract gate 全削除により同一 pair の発行前拒否まで失われる。
2. P1 を consumer 結線より先に入れると、admission が versioned protocol、実 driver が legacy protocol を使う分裂状態を即時に作れる。

## 総括

NO-GO。裁定対象外の pair 防壁が issuer の発行前経路から落ちる。  
P1 は今日の legacy PASSを維持するが、公開 issuer と固定-path consumer の間に実行時の authority 分裂を作る。  
既存 frozen bytes、23-key manifest、保留中 2 check への直接波及は確認されなかった。  
pair precheck を狭く残し、resolver 変更は全 consumer 結線と atomic に扱うまで land を止めるべきである。