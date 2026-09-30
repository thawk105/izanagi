## 直したこと (file:line)

- [確認 job](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:410): M3 を fix2 だけ逆適用した Release TRACE=0 の TPC-C M に変更。修理後 tip の初回 M 走行と交互に実行し、`insert order failed` が逆適用版 `> 5 ×` 修理後 tip なら `reached`、それ以外は `not_reached` と記録する。`not_reached` は全体 fail に含めない。計器 patch は使わない。
- [入力検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:100): 正式 tip の OID・bundle SHA-256、4 patch、fix2 の逆適用可能性を確認する。壊し patch は `--broken-patch` で渡す。
- [修理後の失敗記録](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:348): 修理後 ASan 走行も `fixed_tip_failures` の対象にした。
- [README](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/README.md:5): M3 の条件、数え上げ、見積り、予測を追補 3 に合わせた。

## 各 part の dry-run の argv と結果

次のシェル記述で展開される各コマンドを実行した。`--scratch-root /tmp` と各 `--out-dir` はログインノードでの dry-run 用である。

```bash
J=/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30
X=/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x
W=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-cicada-promotion-uaf-fix
COMMON=(
  --dry-run
  --base-bundle "$J/base.bundle"
  --tip-bundle "$J/tip.bundle"
  --tip-oid 9da7016438839ebcedd7b1094ce4ffad4d1f0dc3
  --fix4-patch "$J/fix/fix4-inline-insert-init.patch"
  --broken-patch "$X/patches/broken-cicada-promotion-ronly-stale-recheck.patch"
  --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache
  --scratch-root /tmp
  --promotion-diag-patch /work/1/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/instr-cicada-trace-promotion-diag.patch
  --ci-sif /work/SFC/tanab/tmp/t2854-ccbench-format-ci-20260929/images/ccbench-devcontainer-ci.sif
  --ci-build-script "$X/md32-scratch/run_ci_image.sh"
  --dependency-prefix /work/1/SFC/tanab/izanagi-a2-deps
  --verifier-head 4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037
)

/usr/bin/python3.10 "$X/md32-scratch/launch_promo_confirm.py" \
  --part ycsb --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-m1 \
  --out-dir /tmp/md32promo-x-dry-ycsb "${COMMON[@]}"

/usr/bin/python3.10 "$X/md32-scratch/launch_promo_confirm.py" \
  --part tpcc --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-m2 \
  --out-dir /tmp/md32promo-x-dry-tpcc "${COMMON[@]}"

/usr/bin/python3.10 "$X/md32-scratch/launch_promo_confirm.py" \
  --part ci --repo-root "$W" \
  --out-dir /tmp/md32promo-x-dry-ci "${COMMON[@]}"
```

**結果:** ycsb・tpcc・ci はすべて rc=0、`dry-run-inputs-valid`。Python 構文検査、`check_codex_agents.py`、`check_docs.py`、`git diff --check` も rc=0。build・TPC-C 走行・判定器・ASan・CI の実走は未実施。

## 数え上げと見積り

YCSB は **10 build・35～38 走行**、TPC-C は **15 build・30 走行**、別に CI 全 protocol build 1 回。合計 **25 build＋CI、65～68 走行**。M3 は以前の計器 YCSB 1 build・1 走行を Release TPC-C 1 build・1 走行へ置換したため、総数は変わらない。計算ノード上の概算は **1,800～3,600 秒（0.5～1.0 node 時間）**。

## 総括

追補 3 の M3 感度 pin と正式 tip の入力確認を反映した。全 part の dry-run は通過したが、M1～M3 と修理後 tip の実走結果は未確定。