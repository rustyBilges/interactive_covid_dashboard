INSERT INTO user (username, password)
VALUES
  ('test', 'pbkdf2:sha256:50000$TCI4GzcX$0de171a4f4dac32e3364c7ddc7c14f3e2fa61f2d17574483f7ffbb431b4acb2f'),
  ('other', 'pbkdf2:sha256:50000$kJPKsz6N$d2d4784f1b030a9761f5ccaeeaca413f27f2ecb76d6168407af962ddce849f79');

INSERT INTO response (author_id, created, number_patients)
VALUES
  (1, '2018-01-01 00:00:00', 15);

INSERT INTO rank (response_id, author_id, rank_number, name, bed_number, t_number, encounter_id)
VALUES
  (1, 1, -1, 'Eduardo Galeano', 10, 'T01', 2);
