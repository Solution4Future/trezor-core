# Automatically generated by pb2py
from protobuf import protobuf as p
t = p.MessageType('Ping')
t.wire_type = 1
t.add_field(1, 'message', p.UnicodeType)
t.add_field(2, 'button_protection', p.BoolType)
t.add_field(3, 'pin_protection', p.BoolType)
t.add_field(4, 'passphrase_protection', p.BoolType)
Ping = t