# Automatically generated by pb2py
from protobuf import protobuf as p
t = p.MessageType('DecryptedMessage')
t.wire_type = 52
t.add_field(1, 'message', p.BytesType)
t.add_field(2, 'address', p.UnicodeType)
DecryptedMessage = t