import sys
import json
import adif_io
import redis

redis = redis.Redis(host='localhost',
                    port=6380,
                    db=0,
                    charset="utf-8",
                    decode_responses=True)

qsos_raw, adif_header = adif_io.read_from_file(sys.argv[1])
for qso in qsos_raw:
    if 'CALL' in qso:
        #print(qso)
        call = qso['CALL']
        cleanCall = call.split("/", maxsplit=2)
        redis.sadd('qrzCALLS', cleanCall[0].upper())
        if 'QSL_RCVD' in qso:
            qsl_rcvd = qso['QSL_RCVD']
        else:
            qsl_rcvd = 'N'
        if 'QSL_SEND' in qso:
            qsl_send = qso['QSL_SEND']
        else:
            qsl_send = 'N'
        if 'OPERATOR' in qso:
            operator = qso['OPERATOR']
        else:
            operator = 'UNKNOWN'
        data = {'station': qso['STATION_CALLSIGN'],
                'operator': operator,
                'band': qso['BAND'],
                'mode': qso['MODE'],
                'date': qso['QSO_DATE'],
                'time': qso['TIME_ON'],
                'qsl_rcvd': qsl_rcvd,
                'qsl_send': qsl_send}
        redis.set('qrzLASTCALL' + cleanCall[0].upper(), json.dumps(data, default=str))
