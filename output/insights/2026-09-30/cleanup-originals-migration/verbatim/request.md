md_1: 原本を抱えて消せない古い worktree・branch を「回収 → 記録の付け替え → 撤去」で片付ける

/dev-wave (軽量版) で実施する。依頼者はユーザー (2026-09-30 01:0x JST)。

■ ユーザーの言葉 (逐語)
- 「ワークツリーとブランチの数が異常に感じるけど、まだ掃除できるのでは？」
- 「じゃぁ、それらのワークツリーやブランチを安全に消すために必要だったりする回収用かつそして消す用dev-waveの投げ文をくれ」
- 「回収する価値があるならね。適当なテストや計測だったらいらねぇ」
- 前日の方針:「mainに取り込むものがないやつ、取り込む価値が小さいやつ、そして古いやつはどんどん消しちゃってよ」
  「削除で失われていいコミットもあるからね？hello worldとかさ」「研究に取り込む価値のないちょっとした検証やお試しコードとかね」
  「私がやらなければいけない仕事を増やさないで。cleanup-branchesというスキルでやりなさい、今後も」

■ 背景
2026-09-29 の /cleanup-branches 3 回で worktree 223→153 本・branch 209→76 本まで減らした。残りの大半は、Codex 2 役 (決定役・攻撃役) が
「insight・docs が計測原本や再現手順の置き場として path を名指ししているので、tar 写しが SHA 一致でも消さない」
「git 登録だけ外す案は Git を使う再現手順と submodule を壊すので不可」と判断して残したもの。
本 wave は、その**名指しを外せる状態を作ってから消す**。

■ 対象 (2026-09-30 01:0x の棚卸し /work/1/SFC/tanab/tmp/cleanup-branches-20260929b/plan4.json と summarize4.out)
A. 計測原本を抱える投入木 80 本 (すべて施錠、occupied 0、数日前に完了した系列)
   dev-wave-jobs/ の dev-wave-t1505-a1-sized-submit・t2489-a2-nodes5-probe・t2792-a1-sized-attempt2・t2795-k2-pair・t2795-k2-pair-resubmit (2)・
   t2797-b5-contrast・t2797-b5-main-run/submit-trees (16)・t2847-verifier-capacity (2)・t2849-mocc (2)・t2849-mocc-conn/trees (22)・
   t2850-trace-concurrent-verify (2)・同 trial-v2/trees (19)・t2850-trial-run (+vprobe)・t2865-iter2/series-c/stage-f の trees (3)・t2871-policy-loop-iter/trees、
   tmp/t2868-mocc-g2-20260927/trees (4)。
B. 研究記録が path を名指しする個別の木と branch
   .claude/worktrees/t2797-b5-effect + branch worktree-dev-wave-t2797-b5-main-run (B-5 発効 commit 6fce61d6e の唯一の ref)、
   .claude/worktrees/t2868-probe-author + branch t2868-probe-author、.codex/worktrees/t2724-chain-scratch・t2724-g1-gen + branch 2、
   .codex/worktrees/t2853-r2-plot-author/fix1/fix2・t2853-r2-fig6-author + branch 4、.claude/worktrees/vhb-mw9・vhb-mw10、
   tmp/vhash-readonly-share-2026-09-29/mutation/scratch2 の変異木、branch probe/t2489-a2-nodes5-submit・md2-pack-hint-fix、
   branch worktree-t2273-shard0-local-copy (D2242「branch は残す」— 消すなら D2242 を改める裁定が要る)。
稼働中の wave の木・branch (occupied>0、または数時間以内に動いたもの) は対象外。段 1 で棚卸しを取り直し、対象を確定する。

■ やること
**既定は「回収せずに消す」。** 回収するのは、価値が一次資料で示せた系列だけにする。適当なテスト・試走・生死確認・閉じた系列の計測は回収しない。
1. 段 1 で、A・B の各系列について「どの insight・docs・decisions が、どの path・ref を、何の目的 (原本・再現・固定 checkout・発効版) で名指ししているか」を全数表にする。
   その系列が今の研究 (論文ストーリーが数値・図として使う・phase3 の次の一手・有効な事前登録が入力に取る) にまだ要るかを判定する。
   **要ると示せたものだけ「回収」、それ以外は「回収せず消す」。** 名指しされているだけ (経緯の記述) は回収の理由にならない。
2. 回収 (価値ありと判定したものだけ): 名指しされた中身を repo 外の恒久置き場へ写す (案: /work/1/SFC/tanab/archive/<日付>/<系列>/)。未追跡原本は tar ではなく展開した形で置き、
   全 file の sha256 manifest を置いて照合する (F1034 の空 tar 事故を踏まえ、件数と hash の両方)。固定 checkout は HEAD sha と bundle を置く
   (submodule の HEAD も)。B-5 発効 commit のように ref が要るものは、tag (例 archive/t2797-b5-effect) で残すか bundle で足りるかを段 4 で決める。
3. 記録の付け替え: 回収したものは insight・docs の名指しを新しい置き場へ、回収せず消したものは「撤去済み (日付・理由)」を、追記で訂正する (append-only の規則に従う。過去の記述は書き換えず、「所在の移動」節や erratum を足す)。
   D2242 など decisions の「残す」を改めるなら、新しい D で理由を書く。land まで通す。
4. 撤去: land 後に /cleanup-branches の手順で消す。worktree は同一 file system 上のゴミ置き場へ mv (rename で数秒/本) → 最後に 1 回 prune
   (land 調整役の PRUNE OK と、dry-run 候補 = 自分が移した集合の完全一致が条件) → 実体は背景で 2 並列削除 (Lustre では多並列にしない)。
   branch は bundle 退避後に名前と期待 tip の表で一括削除。施錠は unlock してから。
5. 回収に値しないと判定した系列 (適当なテスト・試走・お試し・閉じた系列で論文にも次の一手にも使わないもの) は、回収せずに消す。
   前日の退避 (20260929c/d の bundle・tar) がある分はそれで足り、新たな退避は要らない。損失ゼロは要件ではない。

■ 判断の仕方
- 残す・回収する・回収せず消す、の判定は Codex 2 役 (決定役 sol・攻撃役 luna、`tools/dev_wave_codex.py --stage consult --reasoning high --sandbox read-only`) に掛けて AI が決める。
  ユーザーへ確認・実行を回さない。攻撃役には「成立しない攻撃は不成立と書け」と明示する。
- auto mode 分類器に撤去 script を拒否されたら、対象を script 本文に名指しした形にし、ユーザーの明示指示の下で自分で再実行する (実行をユーザーへ渡さない)。
- land 調整役 session (manager: parallel land) がいれば、撤去・prune の前に CLEANUP-READY → OK、後に CLEANUP-DONE / PRUNE-DONE を送る。受入中は登録を消す操作を控える。

■ 材料
- 前日の作業物: /work/1/SFC/tanab/tmp/cleanup-branches-20260929b/ (plan3.py・backup2/3.py・exec5.sh (mv 方式)・trash-rm.sh・prune3.sh・consult3-*.md・codex/ 以下の相談記録)。
- 前日の退避: /work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-20260929c/ (A 群を含む 119 本分の diff・tar・bundle) と 20260929d/。
  A 群の多くは 20260929c の trees/ に tar と record.json がある (流用できるか段 1 で確かめる)。
- Codex の前回判断: consult-sol-out.md、consult3-sol-out.md、codex/cleanup-branches-20260929/*consult-luna*/attempt-0001.output.md。
- 記憶: cleanup-delete-stale-garbage-not-just-report、cleanup-discipline、worktree-removal-on-lustre-is-slow-dont-parallelize、k2-loop-originals-provenance-facts、b5-effect-bundle-facts。
- 参考 insight: output/insights/2026-09-23/t2853-repro-package-archive/、2026-09-27/t2853-repro-rest/ (原本の写しと正本の区別をした前例)。

■ 完了条件
A・B の対象が、回収済み (manifest 照合済み) かつ記録が付け替え済みで撤去されたか、回収に値しないと判定されて退避後に撤去されたか、のどちらかになっている。
残したものは、残す理由 (稼働中・裁定待ち等) を一覧で返す。事後の worktree・branch の本数と、prune 候補 0 を報告する。
