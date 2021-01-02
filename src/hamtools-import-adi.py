import sys
import adif_io
import redis

redis = redis.Redis(host='localhost',
                    port=6380,
                    db=0,
                    charset="utf-8",
                    decode_responses=True)

qsos_raw, adif_header = adif_io.read_from_file(sys.argv[1])
for qso in qsos_raw:
    call = qso['CALL']
    cleanCall = call.split("/", maxsplit=2)
    redis.sadd('qrzCALLS', cleanCall[0])
