読めた completion: 20 件

==============================================================================
genome: silo|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
completion 数: 5  別 jobid の数: 5 ['0_940170.nqsv', '0_944884.nqsv', '0_945229.nqsv', '0_952615.nqsv', '0_952631.nqsv']

field                                          job またぎで一致       値の種類数
admission                                      **不一致**          5
cc                                             一致               1
ccbench_commit                                 一致               1
compiler_input_policy                          **不一致**          2
cxx                                            一致               1
dependency_prefix                              **不一致**          5
genome_canonical                               一致               1
site                                           一致               1
source_snapshot_sha256                         **不一致**          2
src_token                                      **不一致**          2
toolchain_manifest_sha256                      一致               1
trace                                          一致               1

不一致 field の値 (先頭 2 件ずつ):
  admission:
    {"authority_kind": null, "class": "human-reviewed", "generator_id": null, "generator_receipt": null, "input_sha256": "e6d002d8177afb0f234129b714350ffcccf4a6a0a5b3e6b86c7c47c86182f4ea", "policy_sha256": "949ddcc2951935405
    {"authority_kind": null, "class": "human-reviewed", "generator_id": null, "generator_receipt": null, "input_sha256": "e6d002d8177afb0f234129b714350ffcccf4a6a0a5b3e6b86c7c47c86182f4ea", "policy_sha256": "949ddcc2951935405
  compiler_input_policy:
    "snapshot-and-external-hashes/v1"
    null
  dependency_prefix:
    ["/scr/0_940170.nqsv/gflags-install", "/scr/0_940170.nqsv/glog-install"]
    ["/scr/0_944884.nqsv/gflags-install", "/scr/0_944884.nqsv/glog-install"]
  source_snapshot_sha256:
    "6f9615dc586b0025bf5be12a252f1def4df1f261ccb91aa517e1e6a72f22b1c4"
    null
  src_token:
    "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9"
    "fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620"

==============================================================================
genome: silo|BACKOFF_FIXED=2,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
completion 数: 1  別 jobid の数: 1 ['0_945229.nqsv']
→ job をまたいだ比較にならないので skip

==============================================================================
genome: silo|BACKOFF_TRIGGER_GATING=1,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
completion 数: 6  別 jobid の数: 3 ['0_940170.nqsv', '0_944884.nqsv', '0_945229.nqsv']

field                                          job またぎで一致       値の種類数
admission                                      **不一致**          6
cc                                             一致               1
ccbench_commit                                 一致               1
cxx                                            一致               1
dependency_prefix                              **不一致**          3
genome_canonical                               一致               1
site                                           一致               1
src_token                                      **不一致**          3
toolchain_manifest_sha256                      一致               1
trace                                          一致               1

不一致 field の値 (先頭 2 件ずつ):
  admission:
    {"authority_kind": null, "class": "human-reviewed", "generator_id": null, "generator_receipt": null, "input_sha256": "6b174daaade66de4113fa71267b4a1954bb2009e9dc54aa21c066402023f8a53", "policy_sha256": "949ddcc2951935405
    {"authority_kind": null, "class": "human-reviewed", "generator_id": null, "generator_receipt": null, "input_sha256": "7eba49e7e1b87a262a9229ecabb41b90b01506b2b656e0c0c1f0d5502d30b365", "policy_sha256": "949ddcc2951935405
  dependency_prefix:
    ["/scr/0_940170.nqsv/gflags-install", "/scr/0_940170.nqsv/glog-install"]
    ["/scr/0_944884.nqsv/gflags-install", "/scr/0_944884.nqsv/glog-install"]
  src_token:
    "8ac2a15d7853ec07d892844603852e1bd3f2d4f88331e7701070731d3b0cdc48"
    "a0219ce0b258e339ac6489cb5b17b3acb4158ce0d6087ca6098d1e408862f833"

==============================================================================
genome: silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=0,NO_WAIT_OF_TICTOC=1,WAL=0
completion 数: 1  別 jobid の数: 1 ['0_945229.nqsv']
→ job をまたいだ比較にならないので skip

==============================================================================
genome: silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
completion 数: 3  別 jobid の数: 3 ['0_940170.nqsv', '0_944884.nqsv', '0_945229.nqsv']

field                                          job またぎで一致       値の種類数
admission                                      **不一致**          3
cc                                             一致               1
ccbench_commit                                 一致               1
cxx                                            一致               1
dependency_prefix                              **不一致**          3
genome_canonical                               一致               1
site                                           一致               1
src_token                                      一致               1
toolchain_manifest_sha256                      一致               1
trace                                          一致               1

不一致 field の値 (先頭 2 件ずつ):
  admission:
    {"authority_kind": null, "class": "human-reviewed", "generator_id": null, "generator_receipt": null, "input_sha256": "fc6e41b98d541d311c6c4fb35be25cfe88aa2759324ccdd1878494d6fa7c14e5", "policy_sha256": "949ddcc2951935405
    {"authority_kind": null, "class": "human-reviewed", "generator_id": null, "generator_receipt": null, "input_sha256": "fc6e41b98d541d311c6c4fb35be25cfe88aa2759324ccdd1878494d6fa7c14e5", "policy_sha256": "949ddcc2951935405
  dependency_prefix:
    ["/scr/0_940170.nqsv/gflags-install", "/scr/0_940170.nqsv/glog-install"]
    ["/scr/0_944884.nqsv/gflags-install", "/scr/0_944884.nqsv/glog-install"]

==============================================================================
genome: silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,SORT_VARIANT=1,WAL=0
completion 数: 2  別 jobid の数: 1 ['0_945229.nqsv']
→ job をまたいだ比較にならないので skip

==============================================================================
genome: silo|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
completion 数: 2  別 jobid の数: 1 ['0_945229.nqsv']
→ job をまたいだ比較にならないので skip
