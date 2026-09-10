genome: silo|BACKOFF_FIXED=10,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0
jobid: ['0_940170.nqsv', '0_944884.nqsv', '0_945229.nqsv', '0_952615.nqsv', '0_952631.nqsv']

admission の leaf ごとの値の種類数 (job をまたいだ全 completion)
  authority_kind                                               一致           1
  class                                                        一致           1
  generator_id                                                 一致           1
  generator_receipt                                            一致           1
  input_sha256                                                 一致           1
  policy_sha256                                                一致           1
  receipt_sha256                                               **不一致**      5
      "03805d51d85ac097a941eeb1ad733830dbff6c412bb1ebcc5336fe40ea449317"
      "63ae37c0617b9263e8f708b58fbec3576d25cd7ba33823ea07fac835c342365c"
      "97333a64c2c3a9643e96a6cf10eb85dddd23c41a7bbd86fea12f7a868859513a"
  review_id                                                    一致           1
  review_receipt.input_sha256                                  一致           1
  review_receipt.receipt_sha256                                **不一致**      5
      "18161f47d6dc70111de38cfcb4c6d0bf5560cae06a2169022f624bbb60e927c1"
      "37be8b5a1dedab7e4d4b75e7cadfc69538031c694a9447c48f1b93c28b9abeef"
      "93d2573ef600ef1a150684e05a364361c1be207caa88b8c76a81e96b1bd443e3"
  review_receipt.review_id                                     一致           1
  review_receipt.schema                                        一致           1
  review_receipt.source.ccbench_commit                         一致           1
  review_receipt.source.genome_sha256                          一致           1
  review_receipt.source.schema                                 一致           1
  review_receipt.source.source_bytes_sha256                    **不一致**      2
      "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9"
      "fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620"
  review_receipt.source.source_root                            **不一致**      5
      "/scr/0_940170.nqsv/izanagi_wt_32nwzd2t/wt"
      "/scr/0_944884.nqsv/izanagi_wt_kgrsghud/wt"
      "/scr/0_945229.nqsv/izanagi_wt_y8m0i91h/wt"
  review_receipt.source.src_token                              **不一致**      2
      "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9"
      "fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620"
  review_receipt.source.tracked_clean                          一致           1
  review_receipt.source.tracked_diff_sha256                    **不一致**      2
      "a41c7d155f7e60cf71b19069836be917374b43c60da398f3a1e15030f4ef4d69"
      "b7b4c79aa2ebd0f7c09761099f716f18f7c8e8b031f61be8ef48a93d4958e4ba"
  review_receipt.source.tracked_paths[0]                       一致           1
  review_receipt.source.tracked_paths[1]                       一致           1
  schema                                                       一致           1
  source.ccbench_commit                                        一致           1
  source.genome_sha256                                         一致           1
  source.schema                                                一致           1
  source.source_bytes_sha256                                   **不一致**      2
      "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9"
      "fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620"
  source.source_root                                           **不一致**      5
      "/scr/0_940170.nqsv/izanagi_wt_32nwzd2t/wt"
      "/scr/0_944884.nqsv/izanagi_wt_kgrsghud/wt"
      "/scr/0_945229.nqsv/izanagi_wt_y8m0i91h/wt"
  source.src_token                                             **不一致**      2
      "955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9"
      "fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620"
  source.tracked_clean                                         一致           1
  source.tracked_diff_sha256                                   **不一致**      2
      "a41c7d155f7e60cf71b19069836be917374b43c60da398f3a1e15030f4ef4d69"
      "b7b4c79aa2ebd0f7c09761099f716f18f7c8e8b031f61be8ef48a93d4958e4ba"
  source.tracked_paths[0]                                      一致           1
  source.tracked_paths[1]                                      一致           1

src_token / source_snapshot_sha256 を jobid ごとに並べる
  0_940170.nqsv  src_token=fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620  snapshot=None  policy=None
  0_944884.nqsv  src_token=fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620  snapshot=None  policy=None
  0_945229.nqsv  src_token=fdab3432e593a84cce746d17568c1dea5a474dce9b870a7f9552ed28b0c00620  snapshot=None  policy=None
  0_952615.nqsv  src_token=955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9  snapshot=6f9615dc586b0025bf5be12a252f1def4df1f261ccb91aa517e1e6a72f22b1c4  policy=snapshot-and-external-hashes/v1
  0_952631.nqsv  src_token=955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9  snapshot=6f9615dc586b0025bf5be12a252f1def4df1f261ccb91aa517e1e6a72f22b1c4  policy=snapshot-and-external-hashes/v1
