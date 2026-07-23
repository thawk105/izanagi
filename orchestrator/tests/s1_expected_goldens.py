# -*- coding: utf-8 -*-
"""S-1 known-axes freeze の test-local 外部固定 golden (D82 / [T-066] 継続 wave)。

このファイルは test 専用の独立 golden 台帳である。production
(orchestrator/campaign/**) から import してはならず、値を canonical freeze や
現行コードから実行時に導出してもいけない (恒真化するため)。literal は
output/s1-freeze/known_axes_freeze.json の記録値と機械照合した上で凍結した
(照合手順は D82 / output/insights の変異台帳を参照)。

更新契約: 値の変更は「上流の選定・実装が正当に変わった」ことを worklog/decisions で
裁定してから行う。テストを緑にするための書き換えは規律 2 違反。
"""
from __future__ import annotations

WORKLOADS = ("balanced", "write-heavy", "read-heavy")
CONFIGURATIONS = (
    "system_gate", "ident_all", "p2_2_flag_opt", "backoff_fixed_best",
    "sort_best", "stock_common",
)

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
              'reference_fitness_tps': None,
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
                'name': 'sk_ad',
                'reference_fitness_tps': None,
                'remeasure_reference': None},
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
                 'reference_fitness_tps': None,
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
# 編集可能ファイル (orchestrator/campaign/*.py, docs/*, output/insights/*) と
# external/ccbench の sha256 は pin しない (正当編集/pin bump で false red になるため。
# 形式は 64hex のみ検査する)。
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

_HEX = set("0123456789abcdef")


def assert_exact_int_flags(actual, expected, label):
    """key 集合 + 値の型 (bool を int と誤認しない) + 値を厳密に固定する。"""
    assert isinstance(actual, dict) and set(actual) == set(expected), (label, actual, expected)
    for key, exp in expected.items():
        val = actual[key]
        assert type(val) is int and val == exp, (label, key, val, exp)


def _assert_sha256_shape(value, label):
    assert isinstance(value, str) and len(value) == 64 and set(value) <= _HEX, (label, value)


def assert_known_axes_semantic_goldens(doc):
    """entries の意味内容 (flags/name/label/variant/comparator/predicate/選定値) を
    外部固定 literal と完全一致で検査する。"""
    entries = doc["entries"]
    assert set(entries) == set(WORKLOADS), sorted(entries)
    for wl in WORKLOADS:
        entry = entries[wl]
        assert set(entry) == set(CONFIGURATIONS), (wl, sorted(entry))
        assert_exact_int_flags(entry["stock_common"]["flags"], EXPECTED_STOCK_COMMON,
                               f"stock_common.flags[{wl}]")
        gate = entry["system_gate"]
        assert gate["name"] == EXPECTED_GATES[wl]["name"], (wl, gate["name"])
        assert gate["gate_predicate"] == EXPECTED_GATES[wl]["gate_predicate"], (wl, gate["gate_predicate"])
        assert_exact_int_flags(gate["flags"], EXPECTED_TRIGGER_FLAGS, f"system_gate.flags[{wl}]")
        ident = entry["ident_all"]
        assert ident["name"] == "ident_all", (wl, ident["name"])
        assert ident["gate_predicate"] == EXPECTED_IDENT_ALL_PREDICATE, (wl, ident["gate_predicate"])
        assert_exact_int_flags(ident["flags"], EXPECTED_TRIGGER_FLAGS, f"ident_all.flags[{wl}]")
        p2 = entry["p2_2_flag_opt"]
        assert p2["variant"] == EXPECTED_P2[wl]["variant"], (wl, p2["variant"])
        assert p2["label"] == EXPECTED_P2[wl]["label"], (wl, p2["label"])
        assert p2["reference_fitness_tps"] == EXPECTED_P2[wl]["reference_fitness_tps"], (wl, p2)
        assert_exact_int_flags(p2["flags"], EXPECTED_P2[wl]["flags"], f"p2_2.flags[{wl}]")
        backoff = entry["backoff_fixed_best"]
        assert backoff["backoff_us"] == EXPECTED_BACKOFF[wl]["backoff_us"], (wl, backoff["backoff_us"])
        assert backoff["reference_fitness_tps"] == EXPECTED_BACKOFF[wl]["reference_fitness_tps"], (wl, backoff)
        assert_exact_int_flags(backoff["flags"], EXPECTED_BACKOFF[wl]["flags"], f"backoff.flags[{wl}]")
        expected_refs = EXPECTED_BACKOFF[wl]["reference_points"]
        assert set(backoff["reference_points"]) == set(expected_refs), (wl, backoff["reference_points"])
        for name, ref in backoff["reference_points"].items():
            assert_exact_int_flags(ref["flags"], expected_refs[name]["flags"],
                                   f"backoff.reference_points[{name}].flags[{wl}]")
            assert ref["reference_fitness_tps"] == expected_refs[name]["reference_fitness_tps"], (wl, name, ref)
        sort = entry["sort_best"]
        assert sort["name"] == EXPECTED_SORT[wl]["name"], (wl, sort["name"])
        assert sort["comparator"] == EXPECTED_SORT[wl]["comparator"], (wl, sort["comparator"])
        assert_exact_int_flags(sort["flags"], EXPECTED_SORT[wl]["flags"], f"sort.flags[{wl}]")
        assert sort.get("reference_fitness_tps") == EXPECTED_SORT[wl]["reference_fitness_tps"], (wl, sort)
        assert sort.get("remeasure_reference") == EXPECTED_SORT[wl]["remeasure_reference"], (wl, sort)


def assert_known_axes_source_goldens(doc):
    """source record の並び (path/key/lines 有無)・exact key-set・campaign sha pin を検査する。"""
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
                pinned = PINNED_CAMPAIGN_SHA256.get(s["path"])
                if s["path"].startswith("output/campaigns/"):
                    assert pinned is not None and s["sha256"] == pinned, (wl, cfg, s["path"], s["sha256"])


def assert_known_axes_goldens(doc):
    assert_known_axes_semantic_goldens(doc)
    assert_known_axes_source_goldens(doc)
