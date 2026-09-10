# 段6 review 裁定

## in-scope real

1. floor配線テストは2構成だけで、fake manifestもsnapshot-onlyだった。全6構成で実在current rootを消費するv2 manifestを使い、compiler-input rootは全cell、oracle/build専用引数はsort_bestだけであることを固定する。
2. M1はidentity helperの再計算だけで、旧v1 completionを選ばずfresh v2 buildへ進む実cache挙動を固定していない。旧v1 entry配置→v2 request→fresh1回→v2 publishを検査する。

## scope外 real

1. completion manifestとそのdigestを同時改竄できる主体によるroot retag。v1もrelative/absolute pathとdigestを同時改竄すれば同型であり、本waveのroot-relative化が新設する受理拡大ではない。completion authenticityの独立authorityは別設計。
2. root component検査後のrename/symlink交換TOCTOU。v1 absolute external validationもresolve後にpathnameを再openする同型で、本waveの最小修理へfd lifetimeの全面改訂を混ぜない。

両項とも成果物を偽受理しうる限界なのでnitではなく専用scope-out handoffへ送るが、本waveのmust-fixにはしない。

## refuted

- non-sortへ渡すのはcompiler-input current rootだけで、post-oracle capabilityはsort_best限定のまま。
- v1/v2はschema pinで別identity。v1暗黙migrationは無い。
- selected hitのvalidation失敗からfresh buildへのfallbackは無い。

## fix分割

- fix-floor-tests: `orchestrator/tests/test_s8b_floor_campaign.py` のみ。
- fix-cache-tests: `orchestrator/tests/test_buildcache_v2.py` のみ。
- 既存期待値の反転・緩和・skip・削除は禁止。正例は「同じrelative path/hashのcurrent rootなら通る」、拒否は「欠落・差分なら通らない」を分離する。
