# -*- coding: utf-8 -*-
"""S-1 known-axes / measurement freeze の test-local 外部固定 golden ([T-066] 継続 wave、D82)。

このファイルは test 専用の独立 golden 台帳である。production
(orchestrator/campaign/**) から import してはならず、値を canonical freeze や
現行コードから実行時に導出してもいけない (恒真化するため)。literal は
output/s1-freeze/known_axes_freeze.json と measurement_freeze.json の記録値と
機械照合した上で凍結した (照合手順・変異台帳は D82 と本 wave の insights を参照)。

意図的に pin しない値 (裁定 P2、正当編集で false red になる揮発値):
- 編集可能ファイル (orchestrator/campaign/*.py, docs/*, output/insights/*) の sha256
  (64hex 形状のみ検査。bytes の歴史的 pin は canonical freeze + FROZEN_MANIFEST 側が担う)
- external/ccbench 配下の sha256 (ccbench_pin 検査が別途ある。lines は literal 固定 —
  pin bump 時だけ裁定つきで更新する)
- 各 entry の note 文 (散文。key の存在は key-set で固定、値は pin しない)

更新契約: 値の変更は「上流の選定・実装が正当に変わった」ことを worklog/decisions で
裁定してから行う。テストを緑にするための書き換えは規律 2 違反。
"""
from __future__ import annotations

WORKLOADS = ("balanced", "write-heavy", "read-heavy")
CONFIGURATIONS = (
    "system_gate", "ident_all", "p2_2_flag_opt", "backoff_fixed_best",
    "sort_best", "stock_common",
)

_ABSENT = object()

# backoff sweep の静的 grid (semantic slice golden — 事後の候補集合縮小を検出する)
EXPECTED_SWEEP_US = (2, 5, 10, 25, 50, 100)

EXPECTED_STOCK_COMMON = {'BACK_OFF': 1, 'NO_WAIT_LOCKING_IN_VALIDATION': 1, 'NO_WAIT_OF_TICTOC': 0, 'WAL': 0}

EXPECTED_TRIGGER_FLAGS = {'BACKOFF_TRIGGER_GATING': 1,
 'BACK_OFF': 1,
 'NO_WAIT_LOCKING_IN_VALIDATION': 1,
 'NO_WAIT_OF_TICTOC': 0,
 'WAL': 0}

EXPECTED_P2 = {'balanced': {'flags': {'BACK_OFF': 0,
                        'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                        'NO_WAIT_OF_TICTOC': 0,
                        'WAL': 0},
              'label': 'B0-L-W0',
              'reference_fitness_tps': 2752621.0,
              'variant': '5185ee5e6094'},
 'read-heavy': {'flags': {'BACK_OFF': 0,
                          'NO_WAIT_LOCKING_IN_VALIDATION': 0,
                          'NO_WAIT_OF_TICTOC': 1,
                          'WAL': 0},
                'label': 'B0-T-W0',
                'reference_fitness_tps': 8487844.0,
                'variant': 'b971a1d9f80a'},
 'write-heavy': {'flags': {'BACK_OFF': 0,
                           'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                           'NO_WAIT_OF_TICTOC': 0,
                           'WAL': 0},
                 'label': 'B0-L-W0',
                 'reference_fitness_tps': 1872376.0,
                 'variant': '5185ee5e6094'}}

EXPECTED_BACKOFF = {'balanced': {'backoff_us': 5,
              'flags': {'BACKOFF_FIXED': 5,
                        'BACK_OFF': 1,
                        'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                        'NO_WAIT_OF_TICTOC': 0,
                        'WAL': 0},
              'reference_fitness_tps': 3106342.0,
              'reference_points': {'no_backoff': {'flags': {'BACKOFF_FIXED': -1,
                                                            'BACK_OFF': 0,
                                                            'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                                                            'NO_WAIT_OF_TICTOC': 0,
                                                            'WAL': 0},
                                                  'reference_fitness_tps': 2791760.0},
                                   'stock_adaptive': {'flags': {'BACKOFF_FIXED': -1,
                                                                'BACK_OFF': 1,
                                                                'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                                                                'NO_WAIT_OF_TICTOC': 0,
                                                                'WAL': 0},
                                                      'reference_fitness_tps': 916149.0}}},
 'read-heavy': {'backoff_us': 2,
                'flags': {'BACKOFF_FIXED': 2,
                          'BACK_OFF': 1,
                          'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                          'NO_WAIT_OF_TICTOC': 0,
                          'WAL': 0},
                'reference_fitness_tps': 7889420.0,
                'reference_points': {'no_backoff': {'flags': {'BACKOFF_FIXED': -1,
                                                              'BACK_OFF': 0,
                                                              'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                                                              'NO_WAIT_OF_TICTOC': 0,
                                                              'WAL': 0},
                                                    'reference_fitness_tps': 8450806.0},
                                     'stock_adaptive': {'flags': {'BACKOFF_FIXED': -1,
                                                                  'BACK_OFF': 1,
                                                                  'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                                                                  'NO_WAIT_OF_TICTOC': 0,
                                                                  'WAL': 0},
                                                        'reference_fitness_tps': 1919103.0}}},
 'write-heavy': {'backoff_us': 10,
                 'flags': {'BACKOFF_FIXED': 10,
                           'BACK_OFF': 1,
                           'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                           'NO_WAIT_OF_TICTOC': 0,
                           'WAL': 0},
                 'reference_fitness_tps': 2603521.0,
                 'reference_points': {'no_backoff': {'flags': {'BACKOFF_FIXED': -1,
                                                               'BACK_OFF': 0,
                                                               'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                                                               'NO_WAIT_OF_TICTOC': 0,
                                                               'WAL': 0},
                                                     'reference_fitness_tps': 1882125.0},
                                      'stock_adaptive': {'flags': {'BACKOFF_FIXED': -1,
                                                                   'BACK_OFF': 1,
                                                                   'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                                                                   'NO_WAIT_OF_TICTOC': 0,
                                                                   'WAL': 0},
                                                         'reference_fitness_tps': 1052528.0}}}}

# 欠落 key (read-heavy の reference_fitness_tps / remeasure_reference) は literal にも無い。
# 対応する実 doc の key 欠落は EXPECTED_CONFIG_KEYS が固定する。
EXPECTED_SORT = {'balanced': {'comparator': '  sort(write_set_.begin(), write_set_.end(),\n'
                            '       [](const WriteElement<Tuple>& a, const '
                            'WriteElement<Tuple>& b) -> bool {\n'
                            '         return a.storage_ != b.storage_ ? b.storage_ < '
                            'a.storage_\n'
                            '                                         : b.rcdptr_ < '
                            'a.rcdptr_;\n'
                            '       });',
              'flags': {'BACK_OFF': 1,
                        'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                        'NO_WAIT_OF_TICTOC': 0,
                        'SORT_VARIANT': 1,
                        'WAL': 0},
              'name': 'sp_dd',
              'remeasure_reference': {'argmax_name': 'sk_aa',
                                      'reference_fitness_tps': 921457.0}},
 'read-heavy': {'comparator': '  sort(write_set_.begin(), write_set_.end(),\n'
                              '       [](const WriteElement<Tuple>& a, const '
                              'WriteElement<Tuple>& b) -> bool {\n'
                              '         return a.storage_ != b.storage_ ? a.storage_ < '
                              'b.storage_\n'
                              '                                         : b.key_ < a.key_;\n'
                              '       });',
                'flags': {'BACK_OFF': 1,
                          'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                          'NO_WAIT_OF_TICTOC': 0,
                          'SORT_VARIANT': 1,
                          'WAL': 0},
                'name': 'sk_ad'},
 'write-heavy': {'comparator': '  sort(write_set_.begin(), write_set_.end(),\n'
                               '       [](const WriteElement<Tuple>& a, const '
                               'WriteElement<Tuple>& b) -> bool {\n'
                               '         return a.storage_ != b.storage_ ? a.storage_ < '
                               'b.storage_\n'
                               '                                         : b.key_ < a.key_;\n'
                               '       });',
                 'flags': {'BACK_OFF': 1,
                           'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                           'NO_WAIT_OF_TICTOC': 0,
                           'SORT_VARIANT': 1,
                           'WAL': 0},
                 'name': 'sk_ad',
                 'remeasure_reference': {'argmax_name': 'sk_ad',
                                         'reference_fitness_tps': 1098674.0}}}

EXPECTED_GATES = {'balanced': {'flags': {'BACKOFF_TRIGGER_GATING': 1,
                        'BACK_OFF': 1,
                        'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                        'NO_WAIT_OF_TICTOC': 0,
                        'WAL': 0},
              'gate_predicate': 'izanagi_gate_pass = izanagi_abort_reason_ == '
                                'IzanagiAbortReason::kUnset || izanagi_abort_reason_ == '
                                'IzanagiAbortReason::kReadValiLocked;',
              'name': 'g_rl'},
 'read-heavy': {'flags': {'BACKOFF_TRIGGER_GATING': 1,
                          'BACK_OFF': 1,
                          'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                          'NO_WAIT_OF_TICTOC': 0,
                          'WAL': 0},
                'gate_predicate': 'izanagi_gate_pass = izanagi_abort_reason_ == '
                                  'IzanagiAbortReason::kUnset || izanagi_abort_reason_ == '
                                  'IzanagiAbortReason::kReadValiLocked;',
                'name': 'g_rl'},
 'write-heavy': {'flags': {'BACKOFF_TRIGGER_GATING': 1,
                           'BACK_OFF': 1,
                           'NO_WAIT_LOCKING_IN_VALIDATION': 1,
                           'NO_WAIT_OF_TICTOC': 0,
                           'WAL': 0},
                 'gate_predicate': 'izanagi_gate_pass = izanagi_abort_reason_ == '
                                   'IzanagiAbortReason::kUnset || izanagi_abort_reason_ == '
                                   'IzanagiAbortReason::kReadValiTid;',
                 'name': 'g_rt'}}

EXPECTED_IDENT_ALL_PREDICATE = 'izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict || izanagi_abort_reason_ == IzanagiAbortReason::kUpdateAbsent || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid || izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked || izanagi_abort_reason_ == IzanagiAbortReason::kNodeVali;'

# workload×configuration ごとの entry key 集合 (None と欠落を同一視しない防壁)。
EXPECTED_CONFIG_KEYS = {('balanced', 'backoff_fixed_best'): frozenset({'backoff_us',
                                                'flags',
                                                'reference_fitness_tps',
                                                'reference_points',
                                                'sources'}),
 ('balanced', 'ident_all'): frozenset({'name', 'sources', 'gate_predicate', 'flags'}),
 ('balanced', 'p2_2_flag_opt'): frozenset({'flags',
                                           'label',
                                           'reference_fitness_tps',
                                           'sources',
                                           'variant'}),
 ('balanced', 'sort_best'): frozenset({'comparator',
                                       'flags',
                                       'name',
                                       'note',
                                       'remeasure_reference',
                                       'sources'}),
 ('balanced', 'stock_common'): frozenset({'sources', 'flags'}),
 ('balanced', 'system_gate'): frozenset({'name', 'sources', 'gate_predicate', 'flags'}),
 ('read-heavy', 'backoff_fixed_best'): frozenset({'backoff_us',
                                                  'flags',
                                                  'reference_fitness_tps',
                                                  'reference_points',
                                                  'sources'}),
 ('read-heavy', 'ident_all'): frozenset({'name', 'sources', 'gate_predicate', 'flags'}),
 ('read-heavy', 'p2_2_flag_opt'): frozenset({'flags',
                                             'label',
                                             'reference_fitness_tps',
                                             'sources',
                                             'variant'}),
 ('read-heavy', 'sort_best'): frozenset({'note', 'flags', 'comparator', 'name', 'sources'}),
 ('read-heavy', 'stock_common'): frozenset({'sources', 'flags'}),
 ('read-heavy', 'system_gate'): frozenset({'name', 'sources', 'gate_predicate', 'flags'}),
 ('write-heavy', 'backoff_fixed_best'): frozenset({'backoff_us',
                                                   'flags',
                                                   'reference_fitness_tps',
                                                   'reference_points',
                                                   'sources'}),
 ('write-heavy', 'ident_all'): frozenset({'name', 'sources', 'gate_predicate', 'flags'}),
 ('write-heavy', 'p2_2_flag_opt'): frozenset({'flags',
                                              'label',
                                              'reference_fitness_tps',
                                              'sources',
                                              'variant'}),
 ('write-heavy', 'sort_best'): frozenset({'comparator',
                                          'flags',
                                          'name',
                                          'note',
                                          'remeasure_reference',
                                          'sources'}),
 ('write-heavy', 'stock_common'): frozenset({'sources', 'flags'}),
 ('write-heavy', 'system_gate'): frozenset({'name', 'sources', 'gate_predicate', 'flags'})}

# workload×configuration ごとの source record 並び (path, key, lines の有無)。
EXPECTED_SOURCE_LAYOUT = {('balanced', 'backoff_fixed_best'): (('output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl',
                                       'stage=commit/build_start',
                                       False),
                                      ('orchestrator/campaign/backoff_sweep.py',
                                       '_BASE and SWEEP_US',
                                       False)),
 ('balanced', 'ident_all'): (('output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2/reports/s8a_trigger_sweep_provenance.json',
                              'entries.ident_all.implementation',
                              False),
                             ('output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/s8a_trigger_sweep_provenance.json',
                              'entries.ident_all.implementation equality assertion',
                              False),
                             ('orchestrator/campaign/axis_trigger_gating.py', '_BASE', False),
                             ('orchestrator/campaign/s8a_trigger_sweep.py',
                              '_genome(1)',
                              False)),
 ('balanced', 'p2_2_flag_opt'): (('output/campaigns/p2-2-silo-balanced-enumerate-f1588056/runs/wal.jsonl',
                                  'stage=commit/build_start',
                                  False),
                                 ('orchestrator/campaign/genome.py',
                                  'SILO_SPACE fallback definition',
                                  False)),
 ('balanced', 'sort_best'): (('output/campaigns/p3-s6-sort-sweep-balanced-sweep-dd25aa8c/runs/wal.jsonl',
                              'stage=commit argmax',
                              False),
                             ('output/campaigns/p3-s6-sort-sweep-balanced-sweep-dd25aa8c/reports/s6_sort_sweep_provenance.json',
                              'entries.sp_dd.implementation',
                              False),
                             ('output/campaigns/p3-s6-sort-sweep-balanced-sweep-1b39095e/runs/wal.jsonl',
                              'remeasure stage=commit reference',
                              False),
                             ('output/campaigns/p3-s6-sort-sweep-balanced-sweep-1b39095e/reports/s6_sort_sweep_provenance.json',
                              'remeasure name mapping',
                              False),
                             ('output/insights/2026-07-10_s6-sort-sweep-preliminary.md',
                              'D46 main/remeasure interpretation',
                              False),
                             ('orchestrator/campaign/s6_sort_sweep.py',
                              '_genome(1) and candidate space',
                              False),
                             ('orchestrator/campaign/p3_s4_loop_sort.py',
                              '_BASE used by _genome(1)',
                              False)),
 ('balanced', 'stock_common'): (('external/ccbench/cmake/Options.cmake',
                                 'four CACHE defaults and BACK_OFF universal mapping',
                                 True),
                                ('external/ccbench/cc/silo/CMakeLists.txt',
                                 'silo target mappings for three protocol flags',
                                 True)),
 ('balanced', 'system_gate'): (('output/insights/2026-07-11_s8a-trigger-gating-recon.md',
                                'floor超地形 best gate table: balanced',
                                False),
                               ('output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2/reports/s8a_trigger_sweep_provenance.json',
                                'entries.g_rl.implementation',
                                False),
                               ('output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/s8a_trigger_sweep_provenance.json',
                                'entries.g_rl.implementation equality assertion',
                                False),
                               ('orchestrator/campaign/axis_trigger_gating.py', '_BASE', False),
                               ('orchestrator/campaign/s8a_trigger_sweep.py',
                                '_genome(1)',
                                False)),
 ('read-heavy', 'backoff_fixed_best'): (('output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl',
                                         'stage=commit/build_start',
                                         False),
                                        ('orchestrator/campaign/backoff_sweep.py',
                                         '_BASE and SWEEP_US',
                                         False)),
 ('read-heavy', 'ident_all'): (('output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7/reports/s8a_trigger_sweep_provenance.json',
                                'entries.ident_all.implementation',
                                False),
                               ('output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c/reports/s8a_trigger_sweep_provenance.json',
                                'entries.ident_all.implementation equality assertion',
                                False),
                               ('orchestrator/campaign/axis_trigger_gating.py', '_BASE', False),
                               ('orchestrator/campaign/s8a_trigger_sweep.py',
                                '_genome(1)',
                                False)),
 ('read-heavy', 'p2_2_flag_opt'): (('output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad/runs/wal.jsonl',
                                    'stage=commit/build_start',
                                    False),
                                   ('orchestrator/campaign/genome.py',
                                    'SILO_SPACE fallback definition',
                                    False)),
 ('read-heavy', 'sort_best'): (('docs/phase3-main-experiment.md',
                                'D52 2026-07-12追記: read-heavy sk_ad事前固定',
                                False),
                               ('output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef/reports/s6_sort_sweep_provenance.json',
                                'entries.sk_ad.implementation',
                                False),
                               ('orchestrator/campaign/s6_sort_sweep.py',
                                '_genome(1) and candidate space',
                                False),
                               ('orchestrator/campaign/p3_s4_loop_sort.py',
                                '_BASE used by _genome(1)',
                                False)),
 ('read-heavy', 'stock_common'): (('external/ccbench/cmake/Options.cmake',
                                   'four CACHE defaults and BACK_OFF universal mapping',
                                   True),
                                  ('external/ccbench/cc/silo/CMakeLists.txt',
                                   'silo target mappings for three protocol flags',
                                   True)),
 ('read-heavy', 'system_gate'): (('output/insights/2026-07-11_s8a-trigger-gating-recon.md',
                                  'floor超地形 best gate table: read-heavy',
                                  False),
                                 ('output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7/reports/s8a_trigger_sweep_provenance.json',
                                  'entries.g_rl.implementation',
                                  False),
                                 ('output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c/reports/s8a_trigger_sweep_provenance.json',
                                  'entries.g_rl.implementation equality assertion',
                                  False),
                                 ('orchestrator/campaign/axis_trigger_gating.py',
                                  '_BASE',
                                  False),
                                 ('orchestrator/campaign/s8a_trigger_sweep.py',
                                  '_genome(1)',
                                  False)),
 ('write-heavy', 'backoff_fixed_best'): (('output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl',
                                          'stage=commit/build_start',
                                          False),
                                         ('orchestrator/campaign/backoff_sweep.py',
                                          '_BASE and SWEEP_US',
                                          False)),
 ('write-heavy', 'ident_all'): (('output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb/reports/s8a_trigger_sweep_provenance.json',
                                 'entries.ident_all.implementation',
                                 False),
                                ('output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8/reports/s8a_trigger_sweep_provenance.json',
                                 'entries.ident_all.implementation equality assertion',
                                 False),
                                ('orchestrator/campaign/axis_trigger_gating.py',
                                 '_BASE',
                                 False),
                                ('orchestrator/campaign/s8a_trigger_sweep.py',
                                 '_genome(1)',
                                 False)),
 ('write-heavy', 'p2_2_flag_opt'): (('output/campaigns/p2-2-silo-write-heavy-enumerate-8967bed6/runs/wal.jsonl',
                                     'stage=commit/build_start',
                                     False),
                                    ('orchestrator/campaign/genome.py',
                                     'SILO_SPACE fallback definition',
                                     False)),
 ('write-heavy', 'sort_best'): (('output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef/runs/wal.jsonl',
                                 'stage=commit argmax',
                                 False),
                                ('output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef/reports/s6_sort_sweep_provenance.json',
                                 'entries.sk_ad.implementation',
                                 False),
                                ('output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-d4552403/runs/wal.jsonl',
                                 'remeasure stage=commit reference',
                                 False),
                                ('output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-d4552403/reports/s6_sort_sweep_provenance.json',
                                 'remeasure name mapping',
                                 False),
                                ('output/insights/2026-07-10_s6-sort-sweep-preliminary.md',
                                 'D46 main/remeasure interpretation',
                                 False),
                                ('orchestrator/campaign/s6_sort_sweep.py',
                                 '_genome(1) and candidate space',
                                 False),
                                ('orchestrator/campaign/p3_s4_loop_sort.py',
                                 '_BASE used by _genome(1)',
                                 False)),
 ('write-heavy', 'stock_common'): (('external/ccbench/cmake/Options.cmake',
                                    'four CACHE defaults and BACK_OFF universal mapping',
                                    True),
                                   ('external/ccbench/cc/silo/CMakeLists.txt',
                                    'silo target mappings for three protocol flags',
                                    True)),
 ('write-heavy', 'system_gate'): (('output/insights/2026-07-11_s8a-trigger-gating-recon.md',
                                   'floor超地形 best gate table: write-heavy',
                                   False),
                                  ('output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb/reports/s8a_trigger_sweep_provenance.json',
                                   'entries.g_rt.implementation',
                                   False),
                                  ('output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8/reports/s8a_trigger_sweep_provenance.json',
                                   'entries.g_rt.implementation equality assertion',
                                   False),
                                  ('orchestrator/campaign/axis_trigger_gating.py',
                                   '_BASE',
                                   False),
                                  ('orchestrator/campaign/s8a_trigger_sweep.py',
                                   '_genome(1)',
                                   False))}

# output/campaigns 配下 (防護ツリー・不変成果物) のみ bytes hash を pin する。
PINNED_CAMPAIGN_SHA256 = {'output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/runs/wal.jsonl': '8ac3f47e55274fada20e6518eea9cbb0e822170eeda1b424df99e76e11fd789c',
 'output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9/runs/wal.jsonl': 'c74d5837a4facd071704a515f905d1d638463878850661cf217b96cd694774dc',
 'output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7/runs/wal.jsonl': '9c179331a7171969ac6f4ed2b1d09e4afbf52378cfbac7bd133696a6589fe926',
 'output/campaigns/p2-2-silo-balanced-enumerate-f1588056/runs/wal.jsonl': 'd6e98161d8cc3a011688316c3a180a532c0374c87fbbcc30934106f51f95f34c',
 'output/campaigns/p2-2-silo-read-heavy-enumerate-5ffcabad/runs/wal.jsonl': '50f772772fc5c2cd527338c54a43bd9b7b29dc4e2637f73df2cbecb05e0ea76d',
 'output/campaigns/p2-2-silo-write-heavy-enumerate-8967bed6/runs/wal.jsonl': '14b43988f228c573fa1a0b1e7d7fcdc51e8e34c42f4c6b39ff5c27808ff399a5',
 'output/campaigns/p3-s6-sort-sweep-balanced-sweep-1b39095e/reports/s6_sort_sweep_provenance.json': 'fa862099c1637b9bd36ea627d824153864b77006cd6dd341bca2a5dd426f0f70',
 'output/campaigns/p3-s6-sort-sweep-balanced-sweep-1b39095e/runs/wal.jsonl': '542681e3c246317b1e5c08ea7c1cbb7dd16ebba85029fdb3e574a52e4a68f785',
 'output/campaigns/p3-s6-sort-sweep-balanced-sweep-dd25aa8c/reports/s6_sort_sweep_provenance.json': '8c8e0b2270046fdcc0486858946e95b0e6c5d39ab6872a643aee366f31dd9863',
 'output/campaigns/p3-s6-sort-sweep-balanced-sweep-dd25aa8c/runs/wal.jsonl': 'e003d8668e481e224d5b5160c1be593c5169c5ef6f560eddb12eea811c3cb585',
 'output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef/reports/s6_sort_sweep_provenance.json': '42aad55fd9fc57360ec3beff429ccebee1ba0f41288a10e52d12a71c547fcdc7',
 'output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-0484feef/runs/wal.jsonl': '8ad315afd66c1d0e97dbb4b7c82e16e93dc778ad5f50b263716a3d406efdc6a6',
 'output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-d4552403/reports/s6_sort_sweep_provenance.json': '99f5f243371413ca989785b4f53acaf4b91dca0efce47dc28f9329d9fdaeaea6',
 'output/campaigns/p3-s6-sort-sweep-write-heavy-sweep-d4552403/runs/wal.jsonl': '108091b7136bdf94facd0ebb680ac26c5a4de74163254e34a3e4243ac27101ff',
 'output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-b8f4a4e2/reports/s8a_trigger_sweep_provenance.json': '4b7ad441f5e3d1eabffd0ce8f2d7c67caa43bc4bd8c21435dcc725991465ba7c',
 'output/campaigns/p3-s8a-trigger-sweep-balanced-sweep-c2d838b8/reports/s8a_trigger_sweep_provenance.json': '87a6e5640c96f5d5d26cb889538b347c8dfd32fcb7a800f8b423b65405070cf3',
 'output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-654d5cd7/reports/s8a_trigger_sweep_provenance.json': '4466f6c28f735854a331b57dcb9ebd750ff42fcc6db0458cc5c775134608656c',
 'output/campaigns/p3-s8a-trigger-sweep-read-heavy-sweep-8a237e8c/reports/s8a_trigger_sweep_provenance.json': 'bfe345564d6c57be00741ec2a9b0c340a6515b72f5f336f0b53c8a0d592b688a',
 'output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-a81ec3d8/reports/s8a_trigger_sweep_provenance.json': '4518376a154d1fe290eee05803168dd6ed107a0e3dbeca74aca962d47ab7b71f',
 'output/campaigns/p3-s8a-trigger-sweep-write-heavy-sweep-dcd2bbfb/reports/s8a_trigger_sweep_provenance.json': '3b0bdf7735ef292281c575d71cf8699fcb071aadc6dcb6ed394eed9a5cd2d441'}

# lines を持つ source (external/ccbench の CMake 抜粋) の行内容 literal。
# 固定 ccbench pin (d706650) に対する値で、pin bump 時だけ裁定つきで更新する。
EXPECTED_SOURCE_LINES = {'external/ccbench/cc/silo/CMakeLists.txt': ['5:     '
                                             'NO_WAIT_LOCKING_IN_VALIDATION=${CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION}',
                                             '6:     '
                                             'NO_WAIT_OF_TICTOC=${CCBENCH_NO_WAIT_OF_TICTOC}',
                                             '10:     WAL=${CCBENCH_WAL}'],
 'external/ccbench/cmake/Options.cmake': ['20: set(CCBENCH_BACK_OFF      1 CACHE STRING '
                                          '"exponential backoff on abort")',
                                          '27: set(CCBENCH_NO_WAIT_LOCKING_IN_VALIDATION  1 '
                                          'CACHE STRING "")',
                                          '28: set(CCBENCH_NO_WAIT_OF_TICTOC              0 '
                                          'CACHE STRING "")',
                                          '47: set(CCBENCH_WAL                           0 '
                                          'CACHE STRING "silo")',
                                          '63:     BACK_OFF=${CCBENCH_BACK_OFF}']}

# ---- measurement freeze 側 golden (canonical measurement_freeze.json と機械照合済み) ----

EXPECTED_MASTER_SEED = 20260715

EXPECTED_SCHEDULE_HASH = 'b76333da5db1945908641679773bf7ef307ac2dc2bb3462a171b15be235ae150'

EXPECTED_COMPARISONS = [{'alternative': 'greater',
  'comparison_id': 'S-1a:balanced:p2_2_flag_opt',
  'family': 'S-1a',
  'left_cell': 'balanced:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'balanced:p2_2_flag_opt',
  'workload': 'balanced'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:balanced:backoff_fixed_best',
  'family': 'S-1a',
  'left_cell': 'balanced:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'balanced:backoff_fixed_best',
  'workload': 'balanced'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:balanced:sort_best',
  'family': 'S-1a',
  'left_cell': 'balanced:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'balanced:sort_best',
  'workload': 'balanced'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:write-heavy:p2_2_flag_opt',
  'family': 'S-1a',
  'left_cell': 'write-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'write-heavy:p2_2_flag_opt',
  'workload': 'write-heavy'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:write-heavy:backoff_fixed_best',
  'family': 'S-1a',
  'left_cell': 'write-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'write-heavy:backoff_fixed_best',
  'workload': 'write-heavy'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:write-heavy:sort_best',
  'family': 'S-1a',
  'left_cell': 'write-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'write-heavy:sort_best',
  'workload': 'write-heavy'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:read-heavy:p2_2_flag_opt',
  'family': 'S-1a',
  'left_cell': 'read-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'read-heavy:p2_2_flag_opt',
  'workload': 'read-heavy'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:read-heavy:backoff_fixed_best',
  'family': 'S-1a',
  'left_cell': 'read-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'read-heavy:backoff_fixed_best',
  'workload': 'read-heavy'},
 {'alternative': 'greater',
  'comparison_id': 'S-1a:read-heavy:sort_best',
  'family': 'S-1a',
  'left_cell': 'read-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'read-heavy:sort_best',
  'workload': 'read-heavy'},
 {'alternative': 'greater',
  'comparison_id': 'S-1b:balanced:gate_on_vs_gate_off',
  'family': 'S-1b',
  'left_cell': 'balanced:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'balanced:ident_all',
  'workload': 'balanced'},
 {'alternative': 'greater',
  'comparison_id': 'S-1b:write-heavy:gate_on_vs_gate_off',
  'family': 'S-1b',
  'left_cell': 'write-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'write-heavy:ident_all',
  'workload': 'write-heavy'},
 {'alternative': 'greater',
  'comparison_id': 'S-1b:read-heavy:gate_on_vs_gate_off',
  'family': 'S-1b',
  'left_cell': 'read-heavy:system_gate',
  'note': 'stock_common は併記用の文脈セルであり、検定比較対には含めない。',
  'right_cell': 'read-heavy:ident_all',
  'workload': 'read-heavy'}]

_HEX = set("0123456789abcdef")

# 内部整合の import 時検査: gates の flags は共通 trigger flags と一致していなければ
# 台帳自体が矛盾している (dead literal 化の防止)。
for _wl in WORKLOADS:
    assert EXPECTED_GATES[_wl]["flags"] == EXPECTED_TRIGGER_FLAGS, _wl
# pin 集合と layout 参照集合の完全一致 (campaign path の pin 漏れ/余剰の防止)。
assert set(PINNED_CAMPAIGN_SHA256) == {
    p for layout in EXPECTED_SOURCE_LAYOUT.values()
    for (p, _k, _l) in layout if p.startswith("output/campaigns/")
}
assert set(EXPECTED_SOURCE_LINES) == {
    p for layout in EXPECTED_SOURCE_LAYOUT.values()
    for (p, _k, has_lines) in layout if has_lines
}


def assert_json_exact(actual, expected, label):
    """型厳密 (bool≠int≠float)・dict key-set・list 順序込みの再帰完全一致。"""
    assert type(actual) is type(expected), (label, type(actual), type(expected), actual, expected)
    if isinstance(expected, dict):
        assert set(actual) == set(expected), (label, sorted(actual), sorted(expected))
        for key in expected:
            assert_json_exact(actual[key], expected[key], f"{label}.{key}")
    elif isinstance(expected, list):
        assert len(actual) == len(expected), (label, len(actual), len(expected))
        for i, (a, x) in enumerate(zip(actual, expected)):
            assert_json_exact(a, x, f"{label}[{i}]")
    else:
        assert actual == expected, (label, actual, expected)


def assert_exact_int_flags(actual, expected, label):
    """key 集合 + 値の型 (bool を int と誤認しない) + 値を厳密に固定する。"""
    assert isinstance(actual, dict) and set(actual) == set(expected), (label, actual, expected)
    for key, exp in expected.items():
        val = actual[key]
        assert type(val) is int and val == exp, (label, key, val, exp)


def _assert_sha256_shape(value, label):
    assert isinstance(value, str) and len(value) == 64 and set(value) <= _HEX, (label, value)


def _expected_field(table, wl, key):
    return table[wl][key] if key in table[wl] else _ABSENT


def _assert_field(entry, table, wl, key, label):
    expected = _expected_field(table, wl, key)
    if expected is _ABSENT:
        assert key not in entry, (label, key, "expected absent")
    else:
        assert key in entry, (label, key, "expected present")
        assert_json_exact(entry[key], expected, f"{label}.{key}")


def assert_known_axes_semantic_goldens(doc):
    """entries の意味内容を外部固定 literal と型厳密・key-set 込みで検査する。"""
    entries = doc["entries"]
    assert set(entries) == set(WORKLOADS), sorted(entries)
    for wl in WORKLOADS:
        entry = entries[wl]
        assert set(entry) == set(CONFIGURATIONS), (wl, sorted(entry))
        for cfg in CONFIGURATIONS:
            assert set(entry[cfg]) == set(EXPECTED_CONFIG_KEYS[(wl, cfg)]), (
                wl, cfg, sorted(entry[cfg]), sorted(EXPECTED_CONFIG_KEYS[(wl, cfg)]))
        assert_json_exact(entry["stock_common"]["flags"], EXPECTED_STOCK_COMMON,
                          f"stock_common.flags[{wl}]")
        gate = entry["system_gate"]
        assert_json_exact(gate["name"], EXPECTED_GATES[wl]["name"], f"system_gate.name[{wl}]")
        assert_json_exact(gate["gate_predicate"], EXPECTED_GATES[wl]["gate_predicate"],
                          f"system_gate.gate_predicate[{wl}]")
        assert_json_exact(gate["flags"], EXPECTED_GATES[wl]["flags"], f"system_gate.flags[{wl}]")
        ident = entry["ident_all"]
        assert_json_exact(ident["name"], "ident_all", f"ident_all.name[{wl}]")
        assert_json_exact(ident["gate_predicate"], EXPECTED_IDENT_ALL_PREDICATE,
                          f"ident_all.gate_predicate[{wl}]")
        assert_json_exact(ident["flags"], EXPECTED_TRIGGER_FLAGS, f"ident_all.flags[{wl}]")
        p2 = entry["p2_2_flag_opt"]
        for key in ("variant", "label", "reference_fitness_tps", "flags"):
            _assert_field(p2, EXPECTED_P2, wl, key, f"p2_2[{wl}]")
        backoff = entry["backoff_fixed_best"]
        for key in ("backoff_us", "reference_fitness_tps", "flags", "reference_points"):
            _assert_field(backoff, EXPECTED_BACKOFF, wl, key, f"backoff[{wl}]")
        sort = entry["sort_best"]
        for key in ("name", "comparator", "flags", "reference_fitness_tps", "remeasure_reference"):
            _assert_field(sort, EXPECTED_SORT, wl, key, f"sort[{wl}]")


def assert_known_axes_source_goldens(doc):
    """source record の並び・exact key-set・campaign sha pin・lines literal を検査する。"""
    entries = doc["entries"]
    for wl in WORKLOADS:
        for cfg in CONFIGURATIONS:
            recs = entries[wl][cfg]["sources"]
            layout = tuple((s.get("path"), s.get("key"), "lines" in s) for s in recs)
            assert layout == EXPECTED_SOURCE_LAYOUT[(wl, cfg)], (wl, cfg, layout)
            for s in recs:
                expected_keys = {"path", "sha256", "key", "lines"} if "lines" in s \
                    else {"path", "sha256", "key"}
                assert set(s) == expected_keys, (wl, cfg, sorted(s))
                _assert_sha256_shape(s["sha256"], (wl, cfg, s["path"]))
                if s["path"].startswith("output/campaigns/"):
                    pinned = PINNED_CAMPAIGN_SHA256.get(s["path"])
                    assert pinned is not None and s["sha256"] == pinned, (
                        wl, cfg, s["path"], s["sha256"])
                if "lines" in s:
                    assert_json_exact(s["lines"], EXPECTED_SOURCE_LINES[s["path"]],
                                      f"lines[{s['path']}]")


def assert_known_axes_goldens(doc):
    assert_known_axes_semantic_goldens(doc)
    assert_known_axes_source_goldens(doc)
