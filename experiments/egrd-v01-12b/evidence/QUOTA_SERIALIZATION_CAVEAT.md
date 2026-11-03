# SDK duration serialization finding

The current authenticated Kaggle SDK returns total_time_allowed as datetime.timedelta(days=1, seconds=21600), which is108000 seconds. Its TimeDeltaSerializer._to_dict_value reads delta.seconds and omits delta.days, so response.to_dict() emits21600s. Three consecutive reads show the same mismatch. Correct available quota is computed with total_seconds():108000 -18006.232 -0 =89993.768 seconds. The initial interpretation of the serialized dict as a real quota reduction was corrected before any dispatch. No budget threshold was lowered.

Source: installed kagglesdk/kaggle_object.py, TimeDeltaSerializer lines167–174; local source SHA256: 17e37bfc533a0083fb91dd994d4ed35bc729e74c5a5e4a442f46eb45126032e5
