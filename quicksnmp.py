import pysnmp
from pysnmp import hlapi

RETRY_LIMIT = 3

def construct_object_types(list_of_oids):
    object_types = []
    for oid in list_of_oids:
        object_types.append(hlapi.ObjectType(hlapi.ObjectIdentity(oid)))
    return object_types


def construct_value_pairs(list_of_pairs):
    pairs = []
    for key, value in list_of_pairs.items():
        pairs.append(hlapi.ObjectType(hlapi.ObjectIdentity(key), value))
    return pairs


def get(target, oids, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.getCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_object_types(oids)
    )
    return fetch(handler, 1)[0]


def set(target, value_pairs, credentials, port=161, engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.setCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        *construct_value_pairs(value_pairs)
    )
    return fetch(handler, 1)[0]


def get_bulk(target, oids, credentials, count, start_from=0, port=161,
             engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    handler = hlapi.bulkCmd(
        engine,
        credentials,
        hlapi.UdpTransportTarget((target, port)),
        context,
        start_from, count,
        *construct_object_types(oids)
    )
    return fetch(handler, count)


def get_bulk_auto(target, oids, credentials, count_oid, start_from=0, port=161,
                  engine=hlapi.SnmpEngine(), context=hlapi.ContextData()):
    count = get(target, [count_oid], credentials, port, engine, context)[count_oid]
    return get_bulk(target, oids, credentials, count, start_from, port, engine, context)


def cast(value):
    if type(value) == pysnmp.proto.rfc1902.OctetString or type(value) == str:
        return str(value)
    elif type(value) == pysnmp.proto.rfc1902.TimeTicks or type(value) == float:
        return float(value)
    elif type(value) == pysnmp.proto.rfc1902.Integer or type(value) == pysnmp.proto.rfc1902.Integer32 or type(value) == pysnmp.proto.rfc1902.Unsigned32 or type(value) == pysnmp.proto.rfc1902.Gauge32 or type(value) == pysnmp.proto.rfc1902.Counter32 or type(value) == int:
        return int(value)
    else:
        raise Exception("Type '{}' not implemented yet!".format(type(value)))


def fetch(handler, count):
    result = []
    for i in range(count):
        retry_counter = 0
        while(1):
            # get message
            error_indication, error_status, error_index, var_binds = next(handler)
            # no error
            if not error_indication and not error_status:
                items = {}
                for var_bind in var_binds:
                    items[str(var_bind[0])] = cast(var_bind[1])
                result.append(items)
                break
            # no error
            else:
                retry_counter += 1
                if retry_counter >= RETRY_LIMIT:
                    raise RuntimeError('Got SNMP error: {} , {}, {}'.format(error_indication, error_status, error_index))
                else:
                    print("Init retry cause of SNMP error: {} , {}, {} ".format(error_indication, error_status, error_index))
    return result
